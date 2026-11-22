"""Date-level ALFRED vintage selection and a review-only credit signal."""

from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256
import json
import math
from zoneinfo import ZoneInfo

SERIES = "BAA10Y"
ENDPOINT = "https://api.stlouisfed.org/fred/series/observations"
LOOKBACK = 20
MAX_AGE_DAYS = 7
MAX_LOOKBACK_DAYS = 45


@dataclass(frozen=True)
class Vintage:
    observation_date: date
    vintage_start: date
    vintage_end: date
    value: float | None
    publication_date: date | None = None


@dataclass(frozen=True)
class Archive:
    rows: tuple[Vintage, ...]
    start: date
    end: date
    retrieved_at: datetime
    fingerprint: str


@dataclass(frozen=True)
class Signal:
    status: str
    explanation: str
    history: tuple[Vintage, ...] = ()
    missing_count: int = 0
    change_pp: float | None = None


def iso_date(value):
    if not isinstance(value, str):
        raise ValueError("Dates must be YYYY-MM-DD.")
    result = date.fromisoformat(value)
    if result.isoformat() != value:
        raise ValueError("Dates must be YYYY-MM-DD.")
    return result


def load_archive(payload, manifest_bytes):
    """Read a complete ALFRED real-time-period response and its provenance manifest."""
    manifest = json.loads(manifest_bytes)
    data = json.loads(payload)
    if not isinstance(manifest, dict) or not isinstance(data, dict):
        raise ValueError("Both uploads must be JSON objects.")
    fingerprint = sha256(payload).hexdigest()
    if (manifest.get("series_id") != SERIES or manifest.get("endpoint") != ENDPOINT
        or manifest.get("frequency") != "daily" or manifest.get("sha256") != fingerprint):
        raise ValueError("Manifest must identify the daily BAA10Y response and match its SHA-256.")
    retrieved_raw = manifest.get("retrieved_at")
    if not isinstance(retrieved_raw, str):
        raise ValueError("Manifest must include the retrieval timestamp.")
    retrieved_at = datetime.fromisoformat(retrieved_raw)
    if retrieved_at.utcoffset() is None or retrieved_at > datetime.now(retrieved_at.tzinfo):
        raise ValueError("Retrieval timestamp must include a timezone and be in the past.")
    if data.get("output_type") != 1 or data.get("units") != "lin":
        raise ValueError("Use raw ALFRED levels and output_type=1, with no frequency aggregation.")
    start, end = iso_date(data.get("realtime_start")), iso_date(data.get("realtime_end"))
    if start >= end:
        raise ValueError("An explicit multi-date real-time range is required. Current-only FRED data is insufficient.")
    observations = data.get("observations")
    if (not isinstance(observations, list) or data.get("offset") != 0
        or data.get("count") != len(observations)):
        raise ValueError("Upload the complete first-page observations response.")
    rows = []
    for index, item in enumerate(observations, 1):
        if not isinstance(item, dict):
            raise ValueError(f"Observation row {index} must be an object.")
        observed, first, last = (iso_date(item.get(key))
                                 for key in ("date", "realtime_start", "realtime_end"))
        if first > last or observed > first:
            raise ValueError(f"Inconsistent observation/vintage dates in row {index}.")
        raw = item.get("value")
        if raw == ".":
            value = None
        else:
            try:
                value = float(raw) if isinstance(raw, (str, float, int)) and not isinstance(raw, bool) else math.nan
            except ValueError as error:
                raise ValueError(f"Invalid spread in row {index}.") from error
            if not math.isfinite(value) or abs(value) > 100:
                raise ValueError(f"Invalid spread in row {index}. Check the percentage-point units.")
        rows.append(Vintage(observed, first, last, value))
    rows.sort(key=lambda row: (row.observation_date, row.vintage_start))
    for before, after in zip(rows, rows[1:]):
        if before.observation_date == after.observation_date and before.vintage_end >= after.vintage_start:
            raise ValueError(f"Conflicting or duplicate vintage intervals for {after.observation_date}.")
    return Archive(tuple(rows), start, end, retrieved_at, fingerprint)


def eligible_vintages(rows, decision_date):
    """Select only versions available at the inclusive date-level cutoff."""
    eligible = {}
    for row in rows:
        if (row.observation_date <= decision_date
            and row.vintage_start <= decision_date <= row.vintage_end
            and (row.publication_date is None or row.publication_date <= decision_date)):
            if row.observation_date in eligible:
                raise ValueError(f"Multiple eligible versions for {row.observation_date}.")
            eligible[row.observation_date] = row
    return tuple(eligible[day] for day in sorted(eligible))


def evaluate_signal(archive, decision_date):
    capture_date = archive.retrieved_at.astimezone(ZoneInfo("America/New_York")).date()
    if not archive.start <= decision_date <= min(archive.end, capture_date):
        return Signal("Unavailable", "Decision date is outside the documented or retrieved archive coverage.")
    eligible = eligible_vintages(archive.rows, decision_date)
    history = tuple(row for row in eligible if row.value is not None)
    missing = len(eligible) - len(history)
    if not history or (decision_date - history[-1].observation_date).days > MAX_AGE_DAYS:
        return Signal("Unavailable", "No eligible numeric observation within seven calendar days.", history, missing)
    if (len(history) <= LOOKBACK
        or (history[-1].observation_date - history[-1 - LOOKBACK].observation_date).days > MAX_LOOKBACK_DAYS):
        return Signal("Unavailable", "Insufficient recent history for a 20-observation comparison.", history, missing)
    change = round(history[-1].value - history[-1 - LOOKBACK].value, 10)
    if change > 0:
        return Signal("Review", "Credit spread widened. Review credit and equity downside before any proposed allocation change.",
                      history, missing, change)
    return Signal("Monitor", "This comparison did not widen. Continue ordinary risk review before any allocation decision.",
                  history, missing, change)
