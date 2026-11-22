"""Generate stress evidence or replay an exported experiment."""

import argparse
from datetime import date, datetime, timezone
import json
from pathlib import Path

from src.assumptions import ASSETS
from src.portfolio import Mandate
from src.stress import PRESETS, StressInputs, assess_stress, decision, experiment_record, held_decision, preset


def rate(value):
    return "Unavailable" if value is None else f"{value:.2%}"


def render(as_of):
    base = Mandate()
    lines = [
        "# Classroom stress test results", "",
        f"Report date {as_of.isoformat()} · Hypothetical assumptions · Lab 13 default client", "",
        "Annual net return includes recurring expenses. Transition costs are one-time and separate. "
        "All portfolios with passing modeled checks remain Unverified. No historical ETF panel was supplied.", "",
        "| Case | Held annual net return | Held volatility | Held verdict | Reoptimized annual net return | "
        "Reoptimized volatility | Reoptimized verdict | Modeled ceiling | Headroom / shortfall | Decision |",
        "| --- | ---: | ---: | --- | ---: | ---: | --- | ---: | ---: | --- |",
    ]
    allocations = []
    notes = []
    for name, description in PRESETS.items():
        inputs, stressed = preset(name, base)
        result = assess_stress(base, stressed, inputs)
        held, proposed = result.held, result.candidate
        maximum = result.stressed.max_net_return
        headroom = "Unavailable" if maximum is None else f"{(maximum - stressed.target) * 10000:+.1f} bp"
        proposed_return = rate(proposed.net_return if proposed else None)
        proposed_risk = rate(proposed.volatility if proposed else None)
        verdict = proposed.verdict if proposed else "Unavailable"
        state = decision(result.stressed)[0]
        lines.append(f"| {name} | {rate(held.net_return)} | {rate(held.volatility)} | {held.verdict} | "
                     f"{proposed_return} | {proposed_risk} | {verdict} | {rate(maximum)} | {headroom} | {state} |")
        weights = [rate(value) for value in proposed.weights] if proposed else ["Unavailable"] * len(ASSETS)
        transition = "Unavailable" if result.trade_drag is None else f"${base.portfolio_value * result.trade_drag:,.2f}"
        allocations.append("| " + " | ".join([name, *weights, transition]) + " |")
        notes.append(f"- **{name}.** {description} {decision(result.base)[0]} → {state}. "
                     f"{decision(result.stressed)[1]} {held_decision(held)}")
    lines.extend(["", "## Reoptimized weights and transition expense", "",
                  "| Case | " + " | ".join(asset.name for asset in ASSETS) + " | One-time expense |",
                  "| --- | " + " | ".join(["---:"] * (len(ASSETS) + 1)) + " |",
                  *allocations, "", "## Assumptions and decision effects", "", *notes, ""])
    return "\n".join(lines)


def replay(path):
    return replay_bytes(path.read_bytes())


def replay_bytes(content):
    data = json.loads(content)
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("Unsupported stress experiment schema.")
    base, stressed = Mandate(**data["base_mandate"]), Mandate(**data["stressed_mandate"])
    inputs = StressInputs(**data["inputs"])
    from src.investment_context import build_context

    weights = data.get("active_weights")
    active = build_context(base, weights=weights).active if weights is not None else None
    result = assess_stress(base, stressed, inputs, active=active)
    return experiment_record(data["scenario"], base, stressed, inputs, result, active=active)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", type=date.fromisoformat,
                        default=datetime.now(timezone.utc).date())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--experiment", type=Path)
    args = parser.parse_args()
    if args.experiment:
        text = json.dumps(replay(args.experiment), indent=2, allow_nan=False) + "\n"
    else:
        text = render(args.as_of)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
