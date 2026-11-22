# Stress-testing methodology

BoilerPortfolio has two distinct stress workflows. **Training and validation** uses illustrative classroom assumptions and works without private data. **Reviewed ETF snapshot** evaluates BIL, IEF, LQD and VT using authorized historical covariance estimates and separate forward-return assumptions.

## Classroom comparisons

The active mandate and original classroom assumptions define the reference case. **Risk & Scenario Analysis → Lab analysis → Stress testing** offers the presets and **Custom stress**. A stress case challenges a copy of the active mandate and model.

- **Original weights under stress:** Revalue the active weights (the base optimized weights by default) with the stressed annual return, covariance, and expense assumptions. Retest those same weights under the challenged limits. The allocation makes no transition trades. An infeasible base has no original optimized allocation to hold.
- **Reoptimized under stress:** Use the classroom engine to find the lowest-volatility allocation meeting the stressed annual net target and enforceable limits. It uses full investment, long-only weights, the investment-grade bond and reserve floors, and the nonexempt issuer cap. Separately compute the highest modeled annual net return by maximizing over feasible vertices. The ceiling omits requirements that need outside evidence.
- **Return headroom:** Modeled maximum net return minus the challenged net target. Negative headroom is a shortfall and suppresses the reoptimized allocation. The table also gives changes in each portfolio's modeled return and volatility relative to the starting allocation, when available.

## Classroom inputs and costs

Custom return shifts are additive percentage points applied to every asset in the selected sleeve. Equities include global equity and the fictional company. Bonds include the Treasury note and IG bond fund. Treasury bills are the classroom cash proxy. Custom volatility multipliers apply to each asset in the selected sleeve. The global equity/IG bond fund, Treasury note/IG bond fund, and global equity/fictional stock correlations can be set separately. Other correlations retain the classroom values. The engine rebuilds annual covariance from the full matrix and rejects invalid correlations or covariance that is unsuitable for the positive-definite solver.

Expected annual net return subtracts recurring annual expenses from expected gross return. One-time transition cost uses the rate per dollar traded times gross buys plus sells, calculated as `sum(abs(new_weight - old_weight)) × starting portfolio value`. An equal-dollar buy and sell count separately under this convention. The estimate excludes taxes, market impact beyond the supplied rate, price moves, cash flows, and costs of future rebalancing. It is shown separately from the recurring return target. It does not change the annual target, the minimum-variance objective, or the modeled return ceiling.

## Classroom stress presets

These magnitudes are illustrative challenges. They have no estimated probability or predictive performance.

| Case | Assumptions and rationale |
| --- | --- |
| Base case | Active mandate and original classroom assumptions, including 15 bp annual expense and zero transition-cost rate. |
| Equity market deterioration | Reduce both equity expected returns by 2 pp and increase both equity volatilities by 25% to challenge the growth and uncertainty assumptions together. |
| Higher investment costs | Raise the annual expense to 25 bp and use 25 bp per gross dollar traded to distinguish ongoing expenses from implementation friction. |
| Rising stock/bond correlation | Increase global equity/IG fund correlation from 0.25 to 0.40 to test weaker diversification. Changing this one pair to 0.50 while leaving all other pairs fixed fails validation in the five-sleeve model. |
| Increased liquidity requirement | Add 5 pp to the reserve floor, capped at 100%, to test a larger liquidity buffer. The separate five-day redemption requirement and its evidence status remain unchanged. |
| Combined adverse scenario | Equity returns −2 pp, bond returns −0.5 pp, Treasury bill proxy −0.25 pp, equity volatility ×1.25, bond volatility ×1.15, global equity/IG fund correlation 0.40, annual expenses 35 bp, per-traded-dollar cost 25 bp, and reserve floor +5 pp capped at 100%. These jointly tighten growth, diversification, costs, and liquidity. |

## Reviewed ETF stress testing

Select **Reviewed ETF snapshot** under **Decision model** when the authorized, reviewed price and metadata pair is available.

| Dimension | Control and interpretation |
| --- | --- |
| Forward returns | **Risk & Scenario Analysis → Lab analysis → Stress testing → LQD and VT adverse return reduction (pp)** subtracts the same number of percentage points from both funds' forward annual returns. BIL and IEF return assumptions stay fixed. |
| Historical window | Use the sidebar **ETF risk window** to select 36 or 60 months. **Risk & Scenario Analysis → Lab analysis → Risk and allocation comparison** compares the windows, including volatility at fixed weights. |
| Recurring annual investor costs | In **Portfolio Builder → Builder view → Allocation**, select **Custom scenario** and set **ETF recurring cost (bp)**. The fee reduces expected annual net return and the return ceiling. The original case uses 15 bp. Fund expenses are already reflected in the forward assumptions. |
| Investment constraints | In the same custom scenario, open **Mandate limits** and change **Minimum investment-grade bonds (%)** or **Minimum liquid reserve (%)**. The ETF model provisionally counts IEF and LQD toward the bond floor and BIL toward reserve. The five-day redemption rule still requires separate evidence. |

At the default 7.00% net target, the reviewed ETF model has no feasible optimized allocation. Held-weight results that require those starting weights are therefore unavailable. Baselines can still be compared as references. A feasible hypothetical alternative is evaluated separately from the default mandate.

The ETF model uses the last 36 and 60 aligned monthly returns ending on the same session. Annualized volatility is monthly sample volatility × √12, annualized covariance is monthly sample covariance × 12, and correlation is monthly Pearson correlation. A window change can alter modeled risk and the minimum-volatility weights when a feasible allocation exists. The return ceiling stays fixed if forward returns, costs and enforceable constraints stay fixed and both covariance matrices are usable. The classroom optimizer is independent of these estimates.

One-time transition costs and direct volatility and correlation overrides are classroom controls. An ETF-specific transaction-cost stress is unimplemented. Reproducing the private `outputs/historical-window-comparison.md` requires [authorized ETF inputs](../data/README.md#reproduce-the-authorized-etf-capture). Keep that report and its underlying data private unless sharing is authorized. Synthetic panels exercise the workflow in tests.

## Decision rules

| Condition | Disposition |
| --- | --- |
| The evaluated proposal fails a required modeled check or no feasible allocation meets the target and enforceable limits | **REJECT** the proposal. Evaluate any feasible reoptimized alternative separately. An infeasible solve provides no candidate weights. |
| A reviewed ETF alternative meets the modeled checks | **HOLD** pending independent suitability and implementation verification, including security eligibility, liquidity, and client loss tolerance. |
| A classroom example meets the modeled checks | **ILLUSTRATIVE ONLY**, with $0 live authorization. |
| Financial inputs are invalid or the covariance or solution cannot be used | **STOP / INPUT ERROR**. Correct or review the inputs before relying on the result. |
| The historical panel is missing, rejected, insufficient or awaiting review | The historical-window comparison is **Unavailable**. Classroom sensitivities remain available. |

## Classroom report and experiment replay

From the project root with the project environment active:

```sh
python -m src.stress_report --as-of 2026-11-21 --output outputs/stress-test-results.md
python -m unittest discover -s tests -v
```

The [saved results](../outputs/stress-test-results.md) are calculated classroom cases and retain the original stress-report wording. The decision rules above describe the current committee policy. To replay an exported classroom experiment, use **Risk & Scenario Analysis → Lab analysis → Stress testing → Export before-and-after results**, then run:

```sh
python -m src.stress_report --experiment stress-experiment.json --output replayed-experiment.json
```

To replay in the app, select **Advanced Data Management → Optional import → Stress experiment** in the sidebar and upload the JSON. Then select **Committee Decision → Review area → Experiment replay**. The project-local CLI alternative is `.venv/bin/python -m src.stress_report --experiment stress-experiment.json`. Replay recalculates from the exported inputs and leaves the active scenario unchanged. The export contains the base and challenged mandates, model inputs, decision explanations and results. It is a calculation record. The official AI-off prediction and its GitHub commit are the student's separate work.
