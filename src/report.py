"""Regenerate the GitHub-readable baseline and sensitivity results."""

import argparse
from dataclasses import replace
from pathlib import Path

from src.assumptions import ASSETS, DATASET
from src.portfolio import Mandate, analyze


def render():
    default = Mandate()
    lines = [
        "# Version 1 portfolio results", "", f"Assumptions: {DATASET}.",
        "Reproduce with `python -m src.report` from the project root.", "",
    ]
    scenarios = (
        ("Lab 13 default client", default),
        ("Illustrative sensitivity · 7.50% net return target", replace(default, target=.075)),
    )
    for label, mandate in scenarios:
        result = analyze(mandate, frontier_points=0)
        maximum = "Unavailable" if result.max_net_return is None else f"{result.max_net_return:.2%}"
        lines.extend([
            f"## {label}", "",
            f"Portfolio ${mandate.portfolio_value:,.0f} over {mandate.horizon} years with "
            f"a {mandate.target:.2%} annual net target.",
            f"Bond minimum {mandate.min_bonds:.2%}, reserve minimum {mandate.min_reserve:.2%}, "
            f"company cap {mandate.max_company:.2%}, and five-day requirement {mandate.min_five_day:.2%}.",
            f"Maximum modeled net return **{maximum}**.", "", result.decision, "",
            "| Portfolio | Expected annual net return | Annual volatility | Overall verdict |",
            "| --- | ---: | ---: | --- |",
        ])
        for portfolio in result.portfolios:
            lines.append(f"| {portfolio.name} | {portfolio.net_return:.2%} | {portfolio.volatility:.2%} | {portfolio.verdict} |")

        names = " | ".join(p.name for p in result.portfolios)
        columns = " | ".join("---:" for _ in result.portfolios)
        lines.extend(["", f"| Asset | {names} |", f"| --- | {columns} |"])
        for index, asset in enumerate(ASSETS):
            weights = " | ".join(f"{p.weights[index]:.2%}" for p in result.portfolios)
            lines.append(f"| {asset.name} | {weights} |")

        lines.extend(["", "| Mandate rule | " + names + " |", f"| --- | {columns} |"])
        for checks in zip(*(p.rules for p in result.portfolios)):
            statuses = " | ".join(check.status for check in checks)
            lines.append(f"| {checks[0].name} | {statuses} |")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/version_1_results.md"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(), encoding="utf-8")
