I used OpenAI ChatGPT and Codex to assist with planning, coding, testing, and documentation.

The analysis and decision are mine. This project is for educational use only and does not constitute investment advice.

# Investment committee memo

**Decision requested: REJECT the proposed four-ETF allocation under the reviewed assumptions. Authorize $0 in live capital, a live allocation range of 0%–0%.** The best modeled annual net return is **6.65%** against a **7.00%** requirement. The committee may separately authorize a paper test of the investment review process with zero trading authority.

## Client and mandate

The fictional Lab 13 client is 45, plans to retire at 60, and has $5 million over a 15-year horizon. The portfolio is fully invested and long-only, with no borrowing, short selling, or derivatives, and annual rebalancing. It must hold at least 25% investment-grade bonds and 10% cash or highly liquid government securities. Nonexempt individual company exposure is capped at 8%, with exemptions for diversified funds and U.S. Treasuries. At least 90% must be redeemable within five business days. The client has yet to specify an annual loss limit. [Mandate and methodology](../README.md#client-mandate-and-investment-universe) · [Original mandate in code](../src/portfolio.py)

## Investment case

BIL provides Treasury-bill exposure and provisionally counts toward reserves. IEF provides intermediate Treasury duration and LQD provides investment-grade corporate credit. Both provisionally count toward the bond floor. VT provides global equity exposure and has the highest forward-return assumption in the set. These are modeled fund roles pending eligibility review. [Fund and model methodology](data-methodology.md)

| Portfolio | Modeled annual net return | Assessment |
| --- | ---: | --- |
| Equal weight, 25% in each ETF | 5.04% | Meets the provisional bond and reserve floors. Misses the return objective. |
| Benchmark, 60% VT and 40% LQD | 6.65% | Misses the return objective and holds zero modeled reserves. |
| Constrained minimum-volatility candidate | Unavailable | No portfolio meets the modeled floors and the 7.00% net objective. |

The ceiling comes from using 10% BIL for reserves, 25% LQD for bonds and the remaining 65% in VT. LQD has the higher forward assumption of the two qualifying bond sleeves. At the documented forward assumptions, this ceiling mix earns 6.80% before the 15 bp recurring investor fee and 6.65% after it. It is a mathematical upper bound, with no proposed allocation at the required target. Removing the fee alone still leaves a 20 bp shortfall. Fund expenses are already reflected in the forward assumptions. ETF-specific transaction-cost stress is unavailable. [Return reconciliation](rubric-alignment.md#independent-financial-reconciliation) · [ETF model](../src/etf_portfolio.py) · [Stress methodology](stress-testing-methodology.md#reviewed-etf-stress-testing)

## Risk, evidence and reconsideration

- **Estimation window.** Annualized portfolio volatility uses sample covariance from monthly adjusted returns, scaled by 12. The fixed-weight benchmark had higher estimated volatility in the 60-month window than in the 36-month window, using the same endpoint. Neither window changed the 6.65% ceiling because forward returns, costs and modeled constraints were fixed. Volatility measures variability and leaves the client's acceptable loss unresolved. [ETF evidence status](../outputs/etf-analysis-status.md)
- **Downside and constraint sensitivity.** Cutting LQD and VT forward returns by 1 percentage point each lowered the original-case ceiling to 5.81%. The student's separate locked experiment raised only the bond floor from 25% to 35%. The ceiling fell by the predicted 30 bp to 6.35%, leaving a 65 bp shortfall and the same REJECT decision. The experimental floor was hypothetical. The original mandate remains at 25%. [Documented ETF findings](../README.md#key-investment-findings) · [Locked Record reconciliation](validation-and-ai-use.md#locked-changed-input-record)
- **Credit monitoring.** The dated November 21, 2026 BAA10Y review recorded 12 bp of widening over 20 numeric observation steps. Review LQD spread exposure and VT downside before reconsidering. The signal changes the review agenda, with weights unchanged. Live signal data are unavailable. [Dated signal evidence](../outputs/signal-decision-evidence.md) · [Signal data card](signal-data-card.md)

Reopen the proposal only when documented forward assumptions or a separately approved universe can support a modeled allocation at **7.00% net or above** within the applicable floors and hard limits. Stress that candidate before requesting approval. Verify fund eligibility, nonexempt issuer exposure and exemptions, derivatives and leverage policy, five-day access to cash for at least 90% of assets, and implementation costs and rebalancing. Obtain the client's annual loss tolerance and a separate committee vote. Stop if no mix meets the objective, a modeled hard rule fails, or the inputs are invalid. [Committee policy](../src/committee.py) · [Investment judgment methodology](investment-judgment.md)

A public checkout reproduces the illustrative classroom case. The reviewed ETF result requires an authorized local snapshot and the documented assumptions. Raw histories and restricted derived files remain private. [Public and private reproduction](../README.md#optional-authorized-data-and-online-research)
