"""Prepare and reproduce the reviewed November 2026 ETF evidence locally."""

import argparse
import calendar
import csv
from dataclasses import replace
from datetime import date, timedelta
from hashlib import sha256
import io
import json
import math
from pathlib import Path

import pandas as pd

from src.assumptions import ANNUAL_COST
from src.etf_portfolio import analyze_windows, snapshot_date
from src.historical import TICKERS, load_historical
from src.market_import import align, raw_path
from src.portfolio import Mandate

FORWARD = (.035, .0425, .050, .080)
SENSITIVITY_TARGET = .065
START = "2021-10"
END = "2026-10"
IDENTIFIERS = dict(zip(TICKERS, ("78468R663", "464287440", "464287242", "922042742")))
FORWARD_NOTE = ("Illustrative long-run assumptions after fund expenses: BIL 3.50%, IEF 4.25%, "
                "LQD 5.00%, VT 8.00%. Deduct 15 bp annually for investor costs.")


def audit(raw):
    stats = {}
    target_dates = None
    fields = ("open", "high", "low", "close", "adjusted_close", "volume", "dividend_amount")
    for ticker in TICKERS:
        path = raw_path(raw, ticker)
        content = path.read_bytes()
        reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")), strict=True)
        header = [x.strip().replace(" ", "_") for x in reader.fieldnames or []]
        if set(header) != {"timestamp", *fields} or len(header) != len(fields) + 1:
            raise ValueError(f"{ticker}: invalid provider schema.")
        reader.fieldnames = header
        dates, amounts = [], []
        for row in reader:
            session = date.fromisoformat(row["timestamp"])
            numbers = [float(row[field]) for field in fields]
            if (None in row or not all(math.isfinite(x) for x in numbers)
                or min(numbers[:5]) <= 0 or min(numbers[5:]) < 0
                or numbers[1] < max(numbers[0], numbers[2], numbers[3])
                or numbers[2] > min(numbers[0], numbers[3])):
                raise ValueError(f"{ticker}: invalid price, range, volume, or dividend on {session}.")
            dates.append(session)
            if START <= session.isoformat()[:7] <= END:
                amounts.append((session, numbers[-1]))
        if not dates or any(first <= second for first, second in zip(dates, dates[1:])):
            raise ValueError(f"{ticker}: expected unique, newest-first observations.")
        selected = tuple(sorted(day for day, _ in amounts))
        if target_dates is None:
            target_dates = selected
        if selected != target_dates or len(selected) != 61:
            raise ValueError(f"{ticker}: expected 61 aligned monthly dates.")
        for session in selected:
            expected = date(session.year, session.month, calendar.monthrange(session.year, session.month)[1])
            while expected.weekday() > 4 or expected == date(2024, 3, 29):
                expected -= timedelta(days=1)
            if session != expected:
                raise ValueError(f"{ticker}: unexpected month-end session {session}.")
        stats[ticker] = {"file": path.name, "sha256": sha256(content).hexdigest(), "raw_rows": len(dates),
                         "raw_first": str(dates[-1]), "raw_last": str(dates[0]), "selected_rows": len(selected),
                         "positive_distribution_months": sum(value > 0 for _, value in amounts),
                         "excluded_earlier_rows": sum(d.isoformat()[:7] < START for d in dates),
                         "excluded_partial_rows": sum(d.isoformat()[:7] > END for d in dates)}
    return stats


def prepare(root, captured_at):
    stats = audit(root / "raw")
    prices = "\n".join(align(root / "raw", END)) + "\n"
    metadata = {
        "provider": "Alpha Vantage", "endpoint": "TIME_SERIES_MONTHLY_ADJUSTED",
        "downloaded_at": captured_at,
        "capture_evidence": "Operator-supplied capture timestamp. Retain original acquisition evidence locally.",
        "currency": "USD", "frequency": "monthly",
        "adjusted_price_definition": "Provider monthly adjusted close in USD/share, using the final U.S. trading session.",
        "distribution_method": "Provider split and cash-distribution adjustment; dividend amount used for inspection only.",
        "usage_restrictions": "Private research. Public redistribution of raw, aligned and derived evidence not cleared.",
        "calendar_reference": "Final weekdays with March 29, 2024 Good Friday closure; matched across all four listings.",
        "source_urls": {ticker: "https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY_ADJUSTED"
                                f"&symbol={ticker}&datatype=csv" for ticker in TICKERS},
        "instrument_identifiers": IDENTIFIERS,
        "exclusions": ["Earlier rows outside October 2021–October 2026.",
                       "November 20, 2026 partial-month row in each raw export."],
        "raw_audit": stats,
        "reviewed_panel_sha256": sha256(prices.encode()).hexdigest(),
    }
    payload = json.dumps(metadata, indent=2) + "\n"
    sample = load_historical(prices.encode(), payload.encode())
    if sample.warnings:
        raise ValueError("The snapshot contains review flags: " + " ".join(sample.warnings))
    (root / "etf-prices.csv").write_bytes(prices.encode())
    (root / "etf-metadata.json").write_bytes(payload.encode())
    return sample


def pct(value):
    return f"{value:.2%}"


def matrix_lines(title, frame, precision):
    return ["", f"## {title}", "", "| Fund | " + " | ".join(TICKERS) + " |",
            "| --- | " + " | ".join(["---:"] * 4) + " |",
            *["| " + ticker + " | " + " | ".join(f"{value:.{precision}f}" for value in frame.loc[ticker]) + " |"
              for ticker in TICKERS]]


def render(sample):
    cutoff = snapshot_date(sample)
    base = Mandate()
    windows = analyze_windows(sample, base, cutoff, FORWARD, ANNUAL_COST, reviewed=True)
    sensitivity = analyze_windows(sample, replace(base, target=SENSITIVITY_TARGET), cutoff,
                                  FORWARD, ANNUAL_COST, reviewed=True)
    date_range = " to ".join(map(str, sample.sample_dates))
    lines = ["# ETF analysis results · Private research evidence", "", f"Captured {cutoff}. "
             f"61 monthly closes per ETF, {date_range}. 60 monthly returns per ETF.", "", FORWARD_NOTE, "",
             "| ETF | Arithmetic annual return | Geometric annual return | Annual volatility | Cumulative return | Max drawdown |",
             "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for ticker, stats in sample.statistics.iterrows():
        lines.append("| " + ticker + " | " + " | ".join(pct(value) for value in stats) + " |")
    lines += matrix_lines("60-month return correlation", sample.correlation, 3)
    lines += matrix_lines("60-month annual covariance (decimal squared)", sample.covariance, 6)
    lines += ["", "Monthly return rows are calculated locally as adjusted-close ratios minus one. "
              "The reproducible private CSV is generated alongside this report.", ""]
    window_lines = ["# Historical-window comparison · Private research evidence", "",
                    f"Decision date {cutoff}. " + FORWARD_NOTE, "",
                    "Base target 7.00%. A separate 6.50% diagnostic changes only the return target. "
                    "It does not amend the client mandate.", "",
                    "| Window | Price dates | Portfolio | BIL / IEF / LQD / VT | Expected net return | Volatility | Ceiling | Verdict |",
                    "| --- | --- | --- | --- | ---: | ---: | ---: | --- |"]
    for result, diagnostic in zip(windows, sensitivity):
        for name, case in result.portfolios.items():
            window_lines.append(f"| {result.months} | {result.first_price_date} to {result.last_price_date} | {name} | "
                                + " / ".join(map(pct, case.weights)) +
                                f" | {pct(case.net_return)} | {pct(case.volatility)} | {pct(result.max_net_return)} | {case.verdict} |")
        if "Constrained candidate" not in result.portfolios:
            window_lines.append(f"| {result.months} | Same sample | Constrained at 7.00% | — | — | — | "
                                f"{pct(result.max_net_return)} | Infeasible |")
        case = diagnostic.portfolios.get("Constrained candidate")
        if case is None:
            continue
        window_lines.append(f"| {result.months} | Same sample | 6.50% diagnostic candidate | "
                            + " / ".join(map(pct, case.weights)) +
                            f" | {pct(case.net_return)} | {pct(case.volatility)} | {pct(diagnostic.max_net_return)} | {case.verdict} |")
    window_lines += ["", "## Annualized risk by window", "",
                     "| ETF | 36-month volatility | 60-month volatility |", "| --- | ---: | ---: |"]
    for i, ticker in enumerate(TICKERS):
        risks = [pct(math.sqrt(window.annual_covariance[i][i])) for window in windows]
        window_lines.append(f"| {ticker} | {' | '.join(risks)} |")
    for result in windows:
        cov = pd.DataFrame(result.annual_covariance, index=TICKERS, columns=TICKERS)
        window_lines += matrix_lines(f"{result.months}-month annual covariance (decimal squared)", cov, 6)
        window_lines += matrix_lines(f"{result.months}-month return correlation",
                                    sample.returns.tail(result.months).corr(), 3)
    ceiling = windows[-1].max_net_return
    gap = f"{(ceiling - base.target) * 10000:+.1f} bp" if ceiling is not None else "Unavailable"
    window_lines += ["", f"Headroom against the default mandate: {gap} in both windows. "
                     f"{windows[-1].decision} Differences in covariance change risk and the diagnostic weights, "
                     "while feasibility depends on the shared forward returns, costs and constraints. "
                     "Security eligibility, issuer treatment, derivatives, leverage and five-day redemption remain "
                     "unverified. Client annual loss tolerance remains unresolved.", ""]
    return "\n".join(lines), "\n".join(window_lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true", help="Audit raw files and regenerate the paired local inputs.")
    parser.add_argument("--captured-at", help="Observed archive capture time with offset; required with --prepare.")
    args = parser.parse_args()
    if args.prepare and not args.captured_at:
        parser.error("--prepare requires --captured-at.")
    root = Path("data")
    sample = (prepare(root, args.captured_at) if args.prepare else
              load_historical((root / "etf-prices.csv").read_bytes(), (root / "etf-metadata.json").read_bytes()))
    historical, windows = render(sample)
    Path("outputs/etf-analysis-results.md").write_text(historical, encoding="utf-8")
    Path("outputs/historical-window-comparison.md").write_text(windows, encoding="utf-8")
    sample.returns.to_csv("outputs/etf-monthly-returns.csv")


if __name__ == "__main__":
    main()
