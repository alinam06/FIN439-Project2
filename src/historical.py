"""Validated retrospective ETF analytics, independent of the portfolio engine."""

import calendar
import csv
from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256
import io
import json
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd


ROLES = {
    "BIL": "State Street SPDR Bloomberg 1–3 Month T-Bill ETF · Treasury bills",
    "IEF": "iShares 7–10 Year Treasury Bond ETF · Intermediate U.S. Treasuries",
    "LQD": "iShares iBoxx $ Investment Grade Corporate Bond ETF · Corporate bonds",
    "VT": "Vanguard Total World Stock ETF · Global equities",
}
TICKERS = tuple(ROLES)
PRICE_COUNT = 61
# Broad review triggers, in absolute monthly return. They never remove observations.
OUTLIER_LIMITS = dict(zip(TICKERS, (.02, .15, .15, .25)))


@dataclass
class HistoricalSample:
    prices: pd.DataFrame
    returns: pd.DataFrame
    cumulative: pd.DataFrame
    statistics: pd.DataFrame
    correlation: pd.DataFrame
    covariance: pd.DataFrame
    warnings: tuple[str, ...]
    metadata: dict
    csv_hash: str
    metadata_hash: str

    @property
    def sample_dates(self):
        return self.prices.index[0].date(), self.prices.index[-1].date()


def read_metadata(content):
    metadata = json.loads(content.decode("utf-8-sig"))
    if not isinstance(metadata, dict):
        raise ValueError("Source metadata must be a JSON object.")
    for field in ("provider", "downloaded_at", "adjusted_price_definition",
                  "distribution_method", "usage_restrictions", "calendar_reference"):
        value = metadata.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Provide source metadata for {field}.")
    if metadata.get("currency") != "USD" or metadata.get("frequency") != "monthly":
        raise ValueError("The pilot requires monthly prices in USD per share.")
    download = datetime.fromisoformat(metadata["downloaded_at"])
    if download.tzinfo is None or download.utcoffset() is None:
        raise ValueError("Download timestamp must include a timezone.")
    for field in ("source_urls", "instrument_identifiers"):
        values = metadata.get(field)
        if not isinstance(values, dict) or set(values) != set(TICKERS):
            raise ValueError(f"Provide {field} for all four tickers.")
        for ticker, value in values.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Provide {field} for {ticker}.")
            if field == "source_urls":
                parsed = urlsplit(value)
                if parsed.scheme != "https" or not parsed.hostname or parsed.username:
                    raise ValueError(f"{ticker} source URL must be a public HTTPS reference without credentials.")
                sensitive = ("apikey", "api_key", "token", "password", "secret")
                if any(key in parsed.query.lower() for key in sensitive):
                    raise ValueError(f"Remove credential parameters from the {ticker} source URL.")
    exclusions = metadata.get("exclusions")
    if not isinstance(exclusions, list) or any(
        not isinstance(item, str) or not item.strip() for item in exclusions
    ):
        raise ValueError("Supply an exclusions list, empty when none apply.")
    return metadata, download.astimezone(ZoneInfo("America/New_York")).date()


def read_prices(content, download_date):
    rows = list(csv.reader(io.StringIO(content.decode("utf-8-sig")), strict=True))
    if not rows or tuple(rows[0]) != ("date", *TICKERS):
        raise ValueError("Use the aligned adjusted-price CSV header date,BIL,IEF,LQD,VT.")
    dates, prices = [], []
    for line, row in enumerate(rows[1:], start=2):
        if len(row) != len(TICKERS) + 1:
            raise ValueError(f"Line {line} must have a date and four fund prices.")
        try:
            session = date.fromisoformat(row[0])
        except ValueError as error:
            raise ValueError(f"Line {line} date must use YYYY-MM-DD.") from error
        if row[0] != session.isoformat():
            raise ValueError(f"Line {line} date must use YYYY-MM-DD.")
        values = []
        for ticker, raw in zip(TICKERS, row[1:]):
            if not raw.strip():
                raise ValueError(f"Missing adjusted price for {ticker} on {session}.")
            try:
                price = float(raw)
            except ValueError as error:
                raise ValueError(f"Invalid adjusted price for {ticker} on {session}.") from error
            if not np.isfinite(price) or price <= 0:
                raise ValueError(f"Adjusted price for {ticker} on {session} must be finite and positive.")
            values.append(price)
        dates.append(session)
        prices.append(values)

    if len(set(dates)) != len(dates):
        raise ValueError("Duplicate observation dates detected. Review the provider records.")
    if dates != sorted(dates):
        raise ValueError("Observation dates must be strictly ascending.")
    months = [session.year * 12 + session.month for session in dates]
    for previous, current, start, end in zip(months, months[1:], dates, dates[1:]):
        if current != previous + 1:
            raise ValueError(f"Expected consecutive calendar months between {start} and {end}.")
    if len(dates) != PRICE_COUNT:
        raise ValueError(f"Expected {PRICE_COUNT} aligned price rows, found {len(dates)}.")
    for session in dates:
        last_day = calendar.monthrange(session.year, session.month)[1]
        if session.weekday() >= 5 or last_day - session.day > 6:
            raise ValueError(f"{session} is not a plausible final U.S. trading session for its month.")
    if months[-1] >= download_date.year * 12 + download_date.month:
        raise ValueError("Exclude incomplete or future calendar months relative to the download.")
    return pd.DataFrame(prices, index=pd.DatetimeIndex(dates, name="date"), columns=TICKERS)


def load_historical(prices_csv, source_json):
    """Check an aligned adjusted-price upload and calculate retrospective statistics."""
    metadata, download_date = read_metadata(source_json)
    prices = read_prices(prices_csv, download_date)
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        returns = prices.pct_change(fill_method=None).iloc[1:]
        cumulative = prices / prices.iloc[0] - 1
        drawdown = prices / prices.cummax() - 1
        covariance = returns.cov() * 12
    if not all(np.isfinite(frame.to_numpy()).all() for frame in (returns, cumulative, covariance)):
        raise ValueError("Price ratios produce nonfinite analytics. Review the price scale.")
    correlation = returns.corr()
    statistics = pd.DataFrame({
        "Annualized arithmetic return": 12 * returns.mean(),
        "Annualized geometric return": (prices.iloc[-1] / prices.iloc[0]) ** (12 / len(returns)) - 1,
        "Annualized volatility": np.sqrt(np.diag(covariance)),
        "Cumulative total return": cumulative.iloc[-1],
        "Maximum drawdown": -drawdown.min(),
    })
    if not np.isfinite(statistics.to_numpy()).all():
        raise ValueError("The historical statistics exceed the supported numeric range.")
    warnings = []
    for ticker in TICKERS:
        flagged = returns[ticker][returns[ticker].abs() >= OUTLIER_LIMITS[ticker]]
        warnings.extend(f"{ticker} {session.date()} return {value:+.2%} requires source review."
                        for session, value in flagged.items())
        if covariance.loc[ticker, ticker] == 0:
            warnings.append(f"{ticker} has zero return variance. Its correlations are undefined.")
    return HistoricalSample(prices, returns, cumulative, statistics, correlation, covariance,
                            tuple(warnings), metadata, sha256(prices_csv).hexdigest(),
                            sha256(source_json).hexdigest())
