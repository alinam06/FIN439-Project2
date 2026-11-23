I used OpenAI ChatGPT and Codex to assist with planning, coding, testing, and documentation.

The analysis and decision are mine. This project is for educational use only and does not constitute investment advice.

# BoilerPortfolio — Investment Committee Decision Memo

**Course:** FIN 439 — Project 2  
**Investment universe:** BIL, IEF, LQD, VT  
**Decision:** REJECT  
**Proposed live capital authorization:** $0

## Executive Recommendation

I recommend **rejecting the proposed four-ETF allocation under the evaluated assumptions**, with no live capital authorized.

My client requires a 7.00% annual net return. Under the original investment mandate, the maximum modeled annual net return achievable within the evaluated ETF universe is 6.65%, a shortfall of 35 basis points. Because even the return-maximizing permitted allocation falls below the objective, the constrained minimum-volatility optimizer cannot produce a target-meeting portfolio.

I recommend separately paper-testing BoilerPortfolio's investment evaluation process. This is a recommendation to continue evaluating the process, not authorization to invest.

## Client Mandate

The fictional client is a 45-year-old executive with $5 million available for investment and a 15-year horizon until retirement at age 60.

The portfolio must satisfy the following requirements:

| Requirement | Original mandate |
|---|---|
| Annual net return objective | 7.00% |
| Minimum investment-grade bonds | 25% |
| Minimum liquid reserve | 10% |
| Individual nonexempt company concentration | Maximum 8% |
| Five-business-day redeemability | At least 90% |
| Investment restrictions | Long-only, fully invested; no borrowing, short sales or derivatives |
| Rebalancing | Annually |
| Benchmark | 60% global equities / 40% investment-grade bonds |
| Risk measure | Annualized portfolio volatility |
| Acceptable annual loss | Not yet defined by the client |

The model treats certain fund exposures as provisionally eligible for the bond and reserve requirements. Actual fund eligibility, issuer treatment and liquidity still require verification.

## Investment Universe and Portfolio Comparisons

I selected four ETFs with different investment roles:

- **BIL:** Short-term Treasury-bill exposure, provisionally representing liquid reserves.
- **IEF:** Intermediate-term U.S. Treasury exposure.
- **LQD:** Investment-grade corporate bond exposure.
- **VT:** Diversified global equity exposure.

The evaluated alternatives produce the following modeled results using the reviewed ETF assumptions:

| Portfolio | Expected annual net return | Mandate assessment |
|---|---:|---|
| Equal weight: 25% in each ETF | 5.04% | Misses return objective |
| Benchmark: 60% VT / 40% LQD | 6.65% | Misses return objective and reserve floor |
| Constrained minimum-volatility portfolio | No feasible solution | No candidate reaches 7.00% net |

The benchmark provides a useful return comparison, but it is not an acceptable investment merely because it has a higher expected return than equal weighting. Its lack of modeled reserves violates the client's liquidity allocation requirement.

## Why the Return Target Is Infeasible

The reviewed forward-looking arithmetic return assumptions, after embedded fund expenses and before the recurring investor charge, are:

| ETF | Assumed annual return |
|---|---:|
| BIL | 3.50% |
| IEF | 4.25% |
| LQD | 5.00% |
| VT | 8.00% |

Under the modeled rules, the maximum-return feasible composition places 10% in BIL, 25% in LQD, and 65% in VT. This is a **mathematical upper-bound calculation**, not an approved portfolio recommendation.

The corresponding modeled gross return is 6.80%. After subtracting 15 basis points of recurring annual investor expenses, the maximum net return is 6.65%.

Eliminating those expenses entirely would raise the ceiling to only 6.80%, still 20 basis points below the client's required 7.00%.

**The central problem is not that the optimizer selected the wrong weights. The evaluated universe and assumptions cannot meet the return objective while satisfying the modeled limits.**

## Risk, Sensitivity and Independent Experiment

Historical ETF price observations were used to estimate risk, while separate forward-looking assumptions were used for expected returns. The reviewed dataset contains 60 aligned monthly return observations through October 2026.

Benchmark volatility at unchanged weights was estimated at 9.19% using 36 months of returns and 12.23% using 60 months. This difference demonstrates sensitivity to the estimation period. Changing the covariance window affects modeled risk but does not raise the maximum expected return when return assumptions, costs and investment restrictions remain fixed.

In a downside scenario reducing the assumed returns of both LQD and VT by one percentage point, the original-mandate maximum net return falls to approximately 5.81%.

I also completed a separate Locked Changed-Input experiment. I increased the hypothetical minimum investment-grade bond allocation from the original 25% to 35%, holding the other selected inputs unchanged. My independent prediction was a 30-basis-point decline in the maximum net return.

The observed modeled ceiling declined from 6.65% to 6.35%, increasing the shortfall to 65 basis points. Under the 35% hypothetical scenario, the separate LQD/VT downside test lowers the ceiling to approximately 5.54%. The committee decision remains REJECT.

**The 35% requirement was an experiment, not an approved change to the client's original mandate.**

## Economic Monitoring Signal

I evaluated the BAA10Y corporate credit spread using a dated November 21, 2026 FRED evidence review. The reviewed observations indicated a 12-basis-point widening over 20 numeric observation steps.

This justified further examination of LQD credit risk and VT downside exposure. The signal was used for monitoring and risk review, not as a standalone trading instruction or an automatic change to portfolio weights.

## Implementation Risks and Evidence Limitations

Even a portfolio that passes the numerical optimizer would not automatically qualify for live investment. Outstanding questions include the client's acceptable annual loss, the actual eligibility of the ETF holdings under the mandate, concentration exemptions, leverage and derivatives exposure, five-business-day access to cash, and realistic implementation costs.

Additionally, the reviewed ETF results use a locally authorized historical data snapshot. The public GitHub application reproduces the separate illustrative classroom model; exact ETF reproduction requires access to the authorized underlying dataset. The private price history and restricted derived evidence are not redistributed publicly.

Expected returns are assumptions and are not guaranteed outcomes. Historical volatility does not establish the client's acceptable loss or the likelihood of a specific future drawdown.

## Committee Decision and Reconsideration Conditions

I request that the committee:

1. **Reject the evaluated ETF allocation and authorize $0 in live capital.**
2. Permit further research and paper testing of the portfolio evaluation process, without trading authority.
3. Reconsider an investment proposal only when defensible forward-return and expense assumptions, or a separately approved investment universe, support an allocation reaching at least 7.00% net within the applicable mandate.
4. Require verification of fund eligibility, concentration, redemption, client loss tolerance and implementation before any later approval.

The key lesson of this analysis is that **a mathematically optimized allocation is not necessarily an investable portfolio**. The investment decision must respect both the financial objective and the client's constraints.

## Supporting Evidence

- [README and investment summary](../README.md)
- [Historical ETF methodology](data-methodology.md)
- [Investment judgment evidence](investment-judgment.md)
- [Stress-testing methodology](stress-testing-methodology.md)
- [Dated economic signal evidence](../outputs/signal-decision-evidence.md)
- [ETF data and reproduction status](../outputs/etf-analysis-status.md)
- [Locked Changed-Input Record](locked-changed-input-record.md)
- [Validation and AI-Use Report](validation-and-ai-use.md)
