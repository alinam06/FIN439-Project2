"""Build the aligned upload from four authorized Alpha Vantage monthly CSV files."""

import argparse
import csv
from datetime import date
from pathlib import Path

from src.historical import TICKERS, PRICE_COUNT, read_prices


def raw_path(directory, ticker):
    ordinary = directory / f"{ticker}.csv"
    exported = directory / f"monthly_adjusted_{ticker}.csv"
    if ordinary.exists() and exported.exists():
        raise ValueError(f"{ticker}: multiple source exports. Keep one named input.")
    return ordinary if ordinary.exists() else exported


def align(directory, end_month):
    month = date.fromisoformat(f"{end_month}-01")
    last = month.year * 12 + month.month
    dates_by_ticker = {}
    for ticker in TICKERS:
        dates = {}
        with raw_path(directory, ticker).open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames:
                reader.fieldnames = [field.strip().replace(" ", "_") for field in reader.fieldnames]
            if not {"timestamp", "adjusted_close"}.issubset(reader.fieldnames or ()):
                raise ValueError(f"{ticker}: expected Alpha Vantage timestamp and adjusted_close columns.")
            seen = set()
            for row in reader:
                session = date.fromisoformat(row["timestamp"])
                number = session.year * 12 + session.month
                if last - PRICE_COUNT < number <= last:
                    if number in seen:
                        raise ValueError(f"{ticker}: duplicate session month {session:%Y-%m}.")
                    seen.add(number)
                    dates[session] = row["adjusted_close"]
        if len(dates) != PRICE_COUNT:
            raise ValueError(f"{ticker}: required {PRICE_COUNT} sessions, found {len(dates)} in requested range.")
        dates_by_ticker[ticker] = dates
    sessions = sorted(dates_by_ticker[TICKERS[0]])
    if any(set(sessions) != set(dates) for dates in dates_by_ticker.values()):
        raise ValueError("Fund session dates differ. Reconcile source files before aligning.")
    return ["date," + ",".join(TICKERS)] + [
        ",".join([session.isoformat(), *(dates_by_ticker[ticker][session] or "" for ticker in TICKERS)])
        for session in sessions
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--end-month", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        content = "\n".join(align(args.directory, args.end_month)) + "\n"
        read_prices(content.encode(), date.today())
        args.output.write_text(content, encoding="utf-8")
    except (ValueError, OSError, TypeError, csv.Error) as error:
        parser.exit(1, f"Import stopped. {error}\n")


if __name__ == "__main__":
    main()
