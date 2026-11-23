I used OpenAI ChatGPT and Codex to assist with planning, coding, testing, and documentation.

The analysis and decision are mine. This project is for educational use only and does not constitute investment advice.

# BoilerPortfolio — Validation and AI-Use Report

**FIN 439 — Project 2**

## 1. AI Use, Responsibility and Review

I used OpenAI ChatGPT and Codex during project planning, software development, test development, troubleshooting and documentation.

The application's financial calculations are performed by Python code rather than by a generative AI response. The investment recommendation is based on the modeled return objective, constraints, stress evidence and unresolved implementation requirements.

My final investment recommendation is **REJECT the reviewed BIL, IEF, LQD and VT allocation under the original client mandate, with $0 in live capital authorization**. Paper-testing the evaluation process is a separate proposal that does not authorize trading.

AI-assisted output was subject to review rather than accepted as proof of correctness. The validation evidence below distinguishes code tests, executed calculations, observed failures and checks that remain incomplete.

## 2. Financial Known-Answer Tests

The project retains the original Lab 14 training fixtures to verify core portfolio-return and risk calculations independently of downloaded market data.

| Lab 14 portfolio | Expected annual return | Annualized volatility |
|---|---:|---:|
| 60/40 benchmark | 6.80% | 10.46% |
| Equal weight | 5.20% | 5.21% |
| Inverse volatility | 3.77% | 1.05% |

The documented correlation-change test raises benchmark volatility to approximately 11.00% while leaving expected return unchanged.

These known answers help establish that the code correctly applies expected-return weighting, covariance, volatility annualization and portfolio constraints under the defined fixture. Invalid weight and correlation inputs are also tested.

The classroom constrained example separately produces a 7.00% modeled net return, approximately 12.10% annual volatility, and a maximum net return ceiling of 7.11%. This is an illustrative calculation, not the reviewed ETF investment recommendation.

[Lab 14 tests](../tests/test_lab14.py) · [Executed classroom results](../outputs/version_1_results.md)

## 3. Automated Validation

The recorded November 21, 2026 validation run reports **102 tests passed**, with no failures, errors or skips, and five saved financial artifacts reproducing byte for byte in the existing environment.

The reported test command was:

```bash
.venv/bin/python -B -m unittest discover -s tests -q
```

The tests cover financial arithmetic, mandate evaluation, optimization logic, historical-data processing, economic-signal filtering, stress testing, application routing and deterministic explanations.

This constitutes recorded automated validation in the development environment. It is **not** proof that a stranger successfully installed the repository from a fresh checkout.

[Validation chronology and results](../outputs/validation-summary.md) · [Automated test files](../tests/)

## 4. An AI-Assisted Error That Was Caught and Corrected

While using the Streamlit application, I encountered the error:

`TypeError: stress_view() takes 1 positional argument but 3 were given`

The error showed that the stress-testing page was not being called with the correct interface.

Codex subsequently investigated the routing and reproduced the failure through a Streamlit AppTest regression. The application routing was corrected and regression tests were added. The relevant logged run passed 60 tests following the correction, and later recorded suites included broader application testing.

This was an important reminder that AI-assisted code generation does not guarantee working application behavior. Direct use of the interface exposed an error that automated development work had not prevented.

The original running process or module version was not conclusively identified, so the documented regression is evidence of the reproduced failure and correction rather than proof of the original process's exact configuration.

[Routing correction and test history](../outputs/validation-summary.md#risk-routing-and-full-dashboard-regression) · [Regression tests](../tests/test_risk_routing.py)

## 5. Locked Changed-Input Record

The official experiment tested a single hypothetical tightening of the investment-grade bond requirement in the reviewed ETF model.

The student-supplied record reports an independent AI-off prediction on November 22, 2026, a pre-run GitHub commit at approximately 11:12 a.m. Eastern, and a subsequent experiment at approximately 11:23 a.m. Eastern.

**Changed input:** Minimum investment-grade bonds increased from 25% to 35%.

**Held constant:** BIL, IEF, LQD and VT universe; $5 million portfolio; 7.00% annual net objective; 10% reserve floor; 15 bp recurring fee; reviewed forward-return assumptions; 60-month covariance window; and other modeled restrictions.

| Metric | Original | Independent prediction | Observed result |
|---|---:|---:|---:|
| Maximum modeled annual net return | 6.65% | 6.35% | 6.35% |
| Change in maximum return | — | −30 bp | −30 bp |
| Shortfall to 7.00% | 35 bp | — | 65 bp |
| Target-meeting allocation | None | None predicted | None |
| Investment decision | REJECT | REJECT | REJECT |

The reasoning recorded before the experiment concerned the trade-off between higher-expected-return VT exposure and the increased minimum allocation to lower-returning investment-grade bonds.

The actual result matched the predicted direction and magnitude at the precision displayed by the application. The tightened floor widened the return shortfall but did not change the investment recommendation.

The experiment did not modify the client's original 25% minimum bond requirement.

**Evidence of chronology:**

- [Pre-run prediction GitHub commit](https://github.com/alinam06/FIN439-Project2/commit/61df82697e03946f6181c8537a712310f122650e)
- [Post-run results and reconciliation GitHub commit](https://github.com/alinam06/FIN439-Project2/commit/2d7831df74e5f8ae41fbccf7048c9ea5c3f78167)
- [Complete Locked Changed-Input Record](locked-changed-input-record.md)

The earlier commit preserves the prediction as recorded before the later results commit. The independent AI-off condition and actual experiment sequence are documented as student-reported actions, not independently certified by automated tests.

## 6. Stress Testing and Robustness

The reviewed ETF analysis tests the sensitivity of modeled conclusions to:

| Dimension | Test and interpretation |
|---|---|
| Expected returns | A one-percentage-point reduction in LQD and VT forward returns lowers the original 25% bond-floor ceiling to approximately 5.81%. |
| Historical risk window | Benchmark volatility increases from 9.19% over 36 months to 12.23% over 60 months, with fixed benchmark weights. |
| Recurring investor expenses | Eliminating the original 15 bp fee raises the original return ceiling to 6.80%, still below the 7.00% target. |
| Allocation constraints | Raising the IG bond floor from 25% to 35% lowers the ceiling from 6.65% to 6.35%. |

The downside ceiling for the **separate 35% bond-floor custom scenario** is approximately 5.54%. This should not be confused with the 5.81% downside ceiling under the original mandate.

The classroom engine includes additional illustrative correlation, volatility, reserve and one-time trading-cost scenarios. ETF-specific transaction-cost stress remains unavailable.

A modeled failure is not resolved by automatically lowering the investor's objective or silently relaxing the original mandate.

[Stress methodology](stress-testing-methodology.md) · [Public classroom stress results](../outputs/stress-test-results.md)

## 7. Point-in-Time Economic Evidence

The BAA10Y signal was reviewed for November 21, 2026, using a dated FRED table. The reported result was a 12-basis-point widening over 20 numeric observation steps.

This observation prompted a review of corporate credit and equity downside exposure. It did not automatically modify return assumptions or portfolio weights.

The project's point-in-time filtering code is tested using synthetic availability and revision cases. However, a contemporary snapshot cannot independently reconstruct every earlier historical vintage without additional archival evidence.

[Signal data card](signal-data-card.md) · [Dated executed evidence](../outputs/signal-decision-evidence.md)

## 8. Public Reproducibility and Limitations

The public GitHub repository includes the Python application, dependency instructions, financial engine, tests, documentation and authorized public evidence.

A fresh checkout can run the **Training and validation** model without credentials or licensed market-data files.

The actual reviewed ETF analysis used a November 21, 2026 local Alpha Vantage snapshot containing 61 aligned monthly adjusted prices per ETF and 60 monthly return observations ending in October 2026.

Public redistribution permission for the raw ETF histories, prepared price panel and restricted derived reports has not been established. Accordingly, those files are excluded from the repository. Reproducing the reviewed ETF calculations requires access to authorized input data. A later download may contain revisions and therefore may not reproduce the original snapshot exactly.

The independent fresh-checkout cold run has not been established by the automated tests discussed above. Its status must be reported accurately rather than inferred from a successful local application launch or hosted deployment.

Other unresolved matters include ETF eligibility under the mandate, issuer treatment, derivative and leverage policies, actual five-day liquidity, realistic trading costs, the client's loss tolerance and the robustness of forward-return assumptions.

## 9. Final Validation Judgment

The recorded tests and financial reconciliations support the application's ability to calculate portfolio returns, risk, modeled constraints and the decision consequences of changed inputs.

The independent changed-input experiment demonstrates that a more restrictive bond requirement worsens the modeled return shortfall while leaving the decision unchanged.

However, numerical correctness and investment suitability are different questions. A portfolio should not receive capital merely because an optimizer can produce weights or a code test passes.

My investment recommendation remains **REJECT, with $0 in live capital**, until the financial objective, investment eligibility, liquidity requirements and client suitability conditions can be supported by defensible evidence.

## Supporting Documents

- [Investment Committee Memo](decision-memo.md)
- [Original mandate and README](../README.md)
- [Rubric evidence mapping](rubric-alignment.md)
- [ETF data methodology](data-methodology.md)
- [ETF evidence availability](../outputs/etf-analysis-status.md)
