"""Monthly security research. This module does not provide optimizer inputs."""

from dataclasses import dataclass
from datetime import datetime
import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, build_opener
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from src.assumptions import ASSETS
from src.historical import TICKERS

ENDPOINT = "https://www.alphavantage.co/query"
PERIODS = (12, 36, 60)
KEY_NAMES = ("ALPHAVANTAGE_API_KEY", "ALPHA_VANTAGE_API_KEY")


def configured_key():
    # Canonical spelling takes precedence. The key stays in local process memory.
    return next((value for name in KEY_NAMES if (value := os.getenv(name, "").strip())), "")


@dataclass(frozen=True)
class Profile:
    ticker: str
    name: str
    kind: str
    category: str
    role: str
    characteristic: str
    source: str


PROFILES = {
    "AAPL": Profile("AAPL", "Apple Inc.", "Individual company stock", "Devices and services",
                    "Single-company equity exposure", "Hardware demand and services revenue are relevant drivers.",
                    "https://investor.apple.com/investor-relations/"),
    "NVDA": Profile("NVDA", "NVIDIA Corporation", "Individual company stock", "Accelerated computing",
                    "Single-company equity exposure", "Data-center and accelerated computing demand are relevant drivers.",
                    "https://investor.nvidia.com/financial-info/annual-reports-and-proxies/default.aspx"),
    "MSFT": Profile("MSFT", "Microsoft Corporation", "Individual company stock", "Software and cloud",
                    "Single-company equity exposure", "Cloud and productivity businesses are relevant drivers.",
                    "https://www.microsoft.com/investor/reports/ar26/"),
    "TSLA": Profile("TSLA", "Tesla, Inc.", "Individual company stock", "Vehicles and energy",
                    "Single-company equity exposure", "Review automotive demand, margins and execution risk.",
                    "https://ir.tesla.com/"),
    "AMZN": Profile("AMZN", "Amazon.com, Inc.", "Individual company stock", "Commerce and cloud",
                    "Single-company equity exposure", "Review retail margins and cloud growth.",
                    "https://ir.aboutamazon.com/"),
    "GOOGL": Profile("GOOGL", "Alphabet Inc. Class A", "Individual company stock", "Internet services and cloud",
                     "Single-company equity exposure", "Review advertising exposure and cloud growth.",
                     "https://abc.xyz/investor/"),
    "SPY": Profile("SPY", "State Street SPDR S&P 500 ETF Trust", "ETF", "U.S. large-cap equity",
                   "Potential broad U.S. equity exposure", "Review index concentration and issuer overlap.",
                   "https://www.ssga.com/us/en/institutional/etfs/state-street-spdr-sp-500-etf-trust-spy"),
    "BIL": Profile("BIL", "State Street SPDR Bloomberg 1–3 Month T-Bill ETF", "ETF", "U.S. Treasury bills",
                   "Potential reserve sleeve", "Short Treasury maturity. Review fund-wrapper reserve and liquidity eligibility.",
                   "https://www.ssga.com/us/en/individual/etfs/state-street-spdr-bloomberg-1-3-month-t-bill-etf-bil"),
    "IEF": Profile("IEF", "iShares 7–10 Year Treasury Bond ETF", "ETF", "Intermediate U.S. Treasury bonds",
                   "Potential investment-grade bond sleeve", "Duration exposure can lead to losses when yields rise.",
                   "https://www.ishares.com/us/products/239456/ishares-7-10-year-treasury-bond-etf-ief"),
    "LQD": Profile("LQD", "iShares iBoxx $ Investment Grade Corporate Bond ETF", "ETF", "U.S. investment-grade credit",
                   "Potential investment-grade bond sleeve", "Exposed to interest-rate and credit-spread changes.",
                   "https://www.ishares.com/us/products/239566/LQD"),
    "VT": Profile("VT", "Vanguard Total World Stock ETF", "ETF", "Global equities",
                  "Potential diversified equity sleeve", "Review equity drawdown, currency exposure and issuer overlap.",
                  "https://investor.vanguard.com/investment-products/etfs/profile/vt"),
}
PROXIES = {ticker: ASSETS[index] for index, ticker in enumerate(TICKERS)}


class ResearchUnavailable(ValueError):
    """Display-safe data availability message."""


@dataclass(frozen=True)
class History:
    adjusted: pd.Series
    close: pd.Series | None
    source: str
    captured_at: str
    basis: str = "adjusted"
    daily_close: pd.Series | None = None


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def ticker_input(value):
    ticker = value.strip().upper()
    if len(ticker) > 12 or not re.fullmatch(r"[A-Z][A-Z0-9]*(?:[.-][A-Z0-9]+)?", ticker):
        raise ResearchUnavailable("Enter a valid ticker such as AAPL, VT or BRK.B.")
    return ticker


def provider_call(function, parameters, api_key):
    if not api_key.strip():
        raise ResearchUnavailable("Online history is unavailable. Set ALPHAVANTAGE_API_KEY and restart the app.")
    url = ENDPOINT + "?" + urlencode({"function": function, **parameters, "apikey": api_key.strip()})
    try:
        with build_opener(NoRedirect()).open(url, timeout=8) as response:
            body = response.read(2_000_001)
    except HTTPError as error:
        if error.code in (403, 429):
            raise ResearchUnavailable("Alpha Vantage access is restricted or rate-limited. Check your plan and quota.") from None
        raise ResearchUnavailable("Alpha Vantage returned an HTTP error. Try later.") from None
    except (URLError, OSError, ValueError):
        raise ResearchUnavailable("Alpha Vantage could not be reached. Check your connection and try later.") from None
    if len(body) > 2_000_000:
        raise ResearchUnavailable("Alpha Vantage returned an oversized response.")
    try:
        payload = json.loads(body)
    except (ValueError, RecursionError):
        raise ResearchUnavailable("Alpha Vantage did not return usable data.") from None
    if not isinstance(payload, dict):
        raise ResearchUnavailable("Alpha Vantage did not return usable data.")
    note = str(payload.get("Information", "")).lower()
    if "Note" in payload or any(reason in note for reason in ("rate limit", "requests per", "quota", "call frequency")):
        raise ResearchUnavailable("Alpha Vantage rate limit reached. Retry later or check your API plan.")
    if "Information" in payload:
        raise ResearchUnavailable("Alpha Vantage did not supply data. Check your key and monthly endpoint access.")
    if "Error Message" in payload:
        raise ResearchUnavailable("Alpha Vantage did not recognize the symbol or request.")
    return payload


def provider_profile(payload, ticker):
    matches = payload.get("bestMatches")
    if not isinstance(matches, list):
        raise ResearchUnavailable("Symbol metadata is unavailable.")
    match = next((row for row in matches if isinstance(row, dict) and row.get("1. symbol") == ticker), None)
    if match is None or match.get("4. region") != "United States" or match.get("8. currency") != "USD":
        raise ResearchUnavailable("No exact U.S.-listed USD match was found.")
    name = match.get("2. name")
    if not isinstance(name, str) or not name.strip():
        raise ResearchUnavailable("The matched symbol has no usable security name.")
    kind = {"equity": "Individual company stock", "etf": "ETF"}.get(str(match.get("3. type")).strip().lower())
    if kind is None:
        raise ResearchUnavailable("The matched instrument is outside the supported stock and ETF categories.")
    return Profile(ticker, name, kind, "Unavailable from symbol search",
                   "Single-company equity exposure" if kind.startswith("Individual") else "Fund exposure to investigate",
                   "Review issuer filings or fund documentation for financial characteristics.",
                   "https://www.alphavantage.co/documentation/#symbolsearch")


def assert_months(series):
    periods = series.index.to_period("M")
    if periods.has_duplicates or not periods.equals(pd.period_range(periods[0], periods[-1], freq="M")):
        raise ResearchUnavailable("Monthly observations contain a gap or duplicate month.")


def parse_history(payload, ticker, captured):
    meta = payload.get("Meta Data")
    values = payload.get("Monthly Adjusted Time Series")
    if not isinstance(meta, dict) or meta.get("2. Symbol") != ticker or not isinstance(values, dict):
        raise ResearchUnavailable("A matching monthly adjusted history is unavailable.")
    try:
        observations = sorted((pd.Timestamp(day), row) for day, row in values.items())
        rows = [(day, row) for day, row in observations
                if (day.year, day.month) < (captured.year, captured.month)][-61:]
        if len(rows) < 2:
            raise ValueError
        entries = [float(row["5. adjusted close"]) for _, row in rows]
        if not np.isfinite(entries).all() or np.any(np.asarray(entries) <= 0):
            raise ValueError
        index = pd.DatetimeIndex([day for day, _ in rows])
        adjusted = pd.Series(entries, index=index)
    except (ValueError, TypeError, KeyError, OverflowError):
        raise ResearchUnavailable("Monthly history has missing or invalid price observations.") from None
    assert_months(adjusted)
    close = None
    try:
        unadjusted = [float(row["4. close"]) for _, row in rows]
        if np.isfinite(unadjusted).all() and np.all(np.asarray(unadjusted) > 0):
            close = pd.Series(unadjusted, index=index)
    except (ValueError, TypeError, KeyError, OverflowError):
        pass
    return History(adjusted, close, "Alpha Vantage monthly adjusted endpoint", captured.isoformat())


def fetch_online(ticker, api_key):
    known = PROFILES.get(ticker)
    profile = known or provider_profile(provider_call("SYMBOL_SEARCH", {"keywords": ticker}, api_key), ticker)
    payload = provider_call("TIME_SERIES_MONTHLY_ADJUSTED", {"symbol": ticker}, api_key)
    return profile, parse_history(payload, ticker, datetime.now(ZoneInfo("America/New_York")))


def local_history(sample, ticker, reviewed=False):
    if sample is None or ticker not in TICKERS or (sample.warnings and not reviewed):
        return None
    return History(sample.prices[ticker], None, "Private reviewed ETF panel" if reviewed else "Private ETF panel",
                   sample.metadata["downloaded_at"])


def aligned_history(histories, months):
    if months not in (6, *PERIODS):
        raise ResearchUnavailable("Choose a supported historical period.")
    if any(item.adjusted.empty for item in histories.values()):
        raise ResearchUnavailable("A history has no completed month-end bars.")
    if len({item.basis for item in histories.values()}) != 1:
        raise ResearchUnavailable("Price-only and distribution-adjusted histories cannot be compared together.")
    merged = pd.concat({ticker: item.adjusted for ticker, item in histories.items()}, axis=1).sort_index()
    start = max(item.adjusted.index[0] for item in histories.values())
    end = min(item.adjusted.index[-1] for item in histories.values())
    aligned = merged.loc[start:end].tail(months + 1)
    if len(aligned) != months + 1 or aligned.isna().any().any():
        raise ResearchUnavailable(f"Need {months + 1} matched monthly closes for this comparison.")
    assert_months(aligned)
    return aligned


def historical_metrics(prices):
    returns = prices.pct_change(fill_method=None).iloc[1:]
    months = len(returns)
    growth = prices / prices.iloc[0] * 100
    drawdown = prices / prices.cummax() - 1
    return growth, drawdown, pd.DataFrame({
        "Annualized total return": (prices.iloc[-1] / prices.iloc[0]) ** (12 / months) - 1,
        "Annualized volatility": returns.std(ddof=1) * np.sqrt(12),
        "Maximum drawdown": -drawdown.min(),
    }), returns.corr()


def mandate_notes(profile, mandate):
    if profile.kind == "Individual company stock":
        return (f"The Lab 13 default single-company cap is 8%. The active cap is {mandate.max_company:.2%}. "
                "Verify total issuer exposure and any portfolio overlap. Ordinary equity does not satisfy the "
                "investment-grade bond or reserve floors.")
    if profile.kind != "ETF":
        return (f"Verify the issuer and asset type before applying the active {mandate.max_company:.2%} "
                "company cap, any fund exemption, or bond and reserve eligibility.")
    if profile.ticker == "BIL":
        role = f"Potential reserve exposure under the {mandate.min_reserve:.2%} active reserve floor."
    elif profile.ticker in ("IEF", "LQD"):
        role = f"Potential bond exposure under the {mandate.min_bonds:.2%} active investment-grade floor."
    else:
        role = "Verify the fund’s underlying assets before counting it toward any allocation floor or exemption."
    return (f"{role} Verify issuer exemptions, fund practices and whether the active "
            f"{mandate.min_five_day:.2%} five-day redemption requirement can be met at portfolio scale.")


def demo_histories():
    """Deterministic hypothetical paths with no mapped securities or source prices."""
    dates = pd.date_range("2020-12-31", periods=61, freq="BME")
    patterns = {
        "Hypothetical equity": (.025, .018, -.032, .035, -.013, .024),
        "Hypothetical bonds": (.008, -.004, .012, -.006, .011, .005),
    }
    return {label: History(pd.Series(100 * np.cumprod([1., *(pattern * 10)]), index=dates),
                           None, "Synthetic research example", "")
            for label, pattern in patterns.items()}
