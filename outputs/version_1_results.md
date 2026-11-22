# Version 1 portfolio results

Assumptions: Lab 14 course assumptions plus Version 1 fictional company and fee.
Reproduce with `python -m src.report` from the project root.

## Lab 13 default client

Portfolio $5,000,000 over 15 years with a 7.00% annual net target.
Bond minimum 25.00%, reserve minimum 10.00%, company cap 8.00%, and five-day requirement 90.00%.
Maximum modeled net return **7.11%**.

Advance the optimized mix to due diligence. Confirm issuers, fund exemptions, bond and reserve eligibility, fund leverage and derivatives policies, verify five-day redemption, and clarify annual loss tolerance before seeking allocation approval.

| Portfolio | Expected annual net return | Annual volatility | Overall verdict |
| --- | ---: | ---: | --- |
| Equal weight | 5.81% | 8.67% | Fail |
| 60/40 global equity / IG bonds | 6.65% | 10.46% | Fail |
| Constrained minimum volatility | 7.00% | 12.10% | Unverified |

| Asset | Equal weight | 60/40 global equity / IG bonds | Constrained minimum volatility |
| --- | ---: | ---: | ---: |
| U.S. Treasury bills | 20.00% | 0.00% | 0.00% |
| U.S. Treasury 10-year note | 20.00% | 0.00% | 10.00% |
| U.S. investment-grade bond fund | 20.00% | 40.00% | 16.98% |
| Global equity index fund | 20.00% | 60.00% | 70.10% |
| Fictional company stock | 20.00% | 0.00% | 2.93% |

| Mandate rule | Equal weight | 60/40 global equity / IG bonds | Constrained minimum volatility |
| --- | ---: | ---: | ---: |
| Fully invested | Pass | Pass | Pass |
| Long-only / no borrowing / no shorting | Pass | Pass | Pass |
| No derivatives | Unverified | Unverified | Unverified |
| Underlying fund leverage | Unverified | Unverified | Unverified |
| Investment-grade bonds | Pass | Pass | Pass |
| Cash or liquid government reserve | Pass | Fail | Pass |
| Company concentration (model) | Fail | Pass | Pass |
| Issuer evidence | Unverified | Unverified | Unverified |
| Redeemable within five business days | Unverified | Unverified | Unverified |
| Expected net return objective | Fail | Fail | Pass |
| Annual rebalancing | Unverified | Unverified | Unverified |
| Annual loss tolerance | Unverified | Unverified | Unverified |

## Illustrative sensitivity · 7.50% net return target

Portfolio $5,000,000 over 15 years with a 7.50% annual net target.
Bond minimum 25.00%, reserve minimum 10.00%, company cap 8.00%, and five-day requirement 90.00%.
Maximum modeled net return **7.11%**.

Defer. The net return target exceeds the maximum under the modeled constraints. Review the objective and assumptions with the client.

| Portfolio | Expected annual net return | Annual volatility | Overall verdict |
| --- | ---: | ---: | --- |
| Equal weight | 5.81% | 8.67% | Fail |
| 60/40 global equity / IG bonds | 6.65% | 10.46% | Fail |

| Asset | Equal weight | 60/40 global equity / IG bonds |
| --- | ---: | ---: |
| U.S. Treasury bills | 20.00% | 0.00% |
| U.S. Treasury 10-year note | 20.00% | 0.00% |
| U.S. investment-grade bond fund | 20.00% | 40.00% |
| Global equity index fund | 20.00% | 60.00% |
| Fictional company stock | 20.00% | 0.00% |

| Mandate rule | Equal weight | 60/40 global equity / IG bonds |
| --- | ---: | ---: |
| Fully invested | Pass | Pass |
| Long-only / no borrowing / no shorting | Pass | Pass |
| No derivatives | Unverified | Unverified |
| Underlying fund leverage | Unverified | Unverified |
| Investment-grade bonds | Pass | Pass |
| Cash or liquid government reserve | Pass | Fail |
| Company concentration (model) | Fail | Pass |
| Issuer evidence | Unverified | Unverified |
| Redeemable within five business days | Unverified | Unverified |
| Expected net return objective | Fail | Fail |
| Annual rebalancing | Unverified | Unverified |
| Annual loss tolerance | Unverified | Unverified |
