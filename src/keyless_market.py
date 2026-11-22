"""Market History's documented free API, for local personal research."""

from datetime import datetime, timedelta
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import build_opener
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from src.security_research import History, NoRedirect, PROFILES, Profile, ResearchUnavailable, ticker_input

BASE_URL = "https://getmarkethistory.com/api/v1"
NY = ZoneInfo("America/New_York")
SOURCE = "Market History · Unadjusted daily bars"


def read_api(path):
    try:
        with build_opener(NoRedirect()).open(BASE_URL + path, timeout=8) as response:
            body = response.read(2_000_001)
            if response.headers.get("X-Next-Cursor"):
                raise ResearchUnavailable("Market History returned only part of the requested history.")
    except HTTPError as error:
        error.close()
        if error.code == 429:
            raise ResearchUnavailable("Market History rate limit. Wait 30 seconds and search again.") from None
        if error.code == 404:
            raise ResearchUnavailable("No Market History data was found for this U.S. ticker.") from None
        raise ResearchUnavailable("Market History returned an HTTP error. Try later.") from None
    except ResearchUnavailable:
        raise
    except (URLError, OSError, ValueError):
        raise ResearchUnavailable("Market History could not be reached. Check your connection and try again.") from None
    if len(body) > 2_000_000:
        raise ResearchUnavailable("Market History returned an oversized response.")
    return body


def parse_bars(body, ticker, captured):
    try:
        records = [json.loads(line) for line in body.splitlines() if line.strip()]
        if not records:
            raise ResearchUnavailable("No Market History observations were available for this ticker.")
        if any(not isinstance(row, dict) for row in records):
            raise ValueError("Invalid bar records")
        frame = pd.DataFrame.from_records(records)
        if (not frame["symbol"].eq(ticker).all() or frame["symbol_id"].isna().any()
            or frame["symbol_id"].nunique() != 1):
            raise ResearchUnavailable("Market History returned a mismatched or reused ticker.")
        dates = pd.DatetimeIndex(pd.to_datetime(frame["timestamp"], utc=True, format="ISO8601"))
        dates = dates.tz_convert(NY).tz_localize(None).normalize()
        close = pd.Series(pd.to_numeric(frame["close"]).to_numpy(dtype=float), index=dates).sort_index()
        if dates.hasnans or dates.has_duplicates or not np.isfinite(close).all() or (close <= 0).any():
            raise ValueError("Invalid close observations")
        # Sunday overnight bars are not regular weekday observations. Exclude the open day.
        close = close[(close.index.weekday < 5) & (close.index < pd.Timestamp(captured.date()))]
        if close.empty:
            raise ResearchUnavailable("No completed weekday bars were returned.")
        completed = close.loc[close.index < pd.Timestamp(captured.date()).replace(day=1)]
        month_end = completed.groupby(completed.index.to_period("M")).tail(1)
        return History(month_end, month_end, SOURCE, captured.isoformat(), "price", close)
    except ResearchUnavailable:
        raise
    except (KeyError, ValueError, TypeError, OverflowError, RecursionError):
        raise ResearchUnavailable("Market History returned missing or invalid price observations.") from None


def fetch_market_history(ticker):
    ticker = ticker_input(ticker)
    symbol = quote(ticker, safe="")
    captured = datetime.now(NY)
    query = urlencode({"start": (captured.date() - timedelta(days=729)).isoformat(),
                       "end": captured.date().isoformat(), "format": "jsonl", "tz": "exchange"})
    history = parse_bars(read_api(f"/bars/stocks/us/{symbol}/1d?{query}"), ticker, captured)
    if ticker in PROFILES:
        return PROFILES[ticker], history
    name = "Name unavailable"
    try:
        payload = json.loads(read_api(f"/stocks/us/{symbol}"))
        contract = payload.get("contract", {}) if isinstance(payload, dict) else {}
        if isinstance(contract, dict) and isinstance(contract.get("name"), str) and contract["name"].strip():
            name = contract["name"]
    except (ValueError, RecursionError):
        pass  # Catalogue outages should leave a usable series visible.
    return Profile(ticker, name, "U.S. listing · Classification unverified", "Unavailable",
                   "Exposure to investigate", "Confirm issuer, asset type and corporate actions.",
                   "https://getmarkethistory.com/docs/guides/historical-stock-market-data"), history
