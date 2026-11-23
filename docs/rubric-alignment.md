# FIN 439 Project 2 — Rubric Alignment and Evidence Map

**Project:** BoilerPortfolio — Investment Management Application

**GitHub repository:** https://github.com/alinam06/FIN439-Project2

**Live application:** https://boilerportfolio-fin439.streamlit.app/

## Project Status and Investment Conclusion

BoilerPortfolio is an investment decision-support application developed for FIN 439 Project 2.

The final investment recommendation is **REJECT** for the evaluated BIL, IEF, LQD and VT universe under the original client's mandate and reviewed financial assumptions. The proposed live capital authorization is **$0**.

The application separately demonstrates a reproducible illustrative classroom portfolio. A successful classroom optimization is not an investment recommendation. Paper-testing the evaluation process is a separate proposal that carries no trading authority.

This document maps the project's evidence to the eight base requirements and six grading categories. It is not a grade estimate.

## 1. Eight Base Requirements

| # | Requirement | Current status | Supporting evidence |
|---|---|---|---|
| 1 | Runnable application from README | **Implemented** | [README](../README.md), [application](../app.py), [dependencies](../requirements.txt), [automated tests](../outputs/validation-summary.md). Public Streamlit deployment is available, but a fresh independent checkout has not been established. |
| 2 | Original mandate, investment universe, benchmark and risk | **Complete** | [Client mandate](../README.md#client-mandate-and-investment-universe), [financial engine](../src/portfolio.py), [ETF methodology](data-methodology.md). |
| 3 | Two transparent baselines and constrained portfolio | **Complete** | [Classroom results](../outputs/version_1_results.md), Portfolio Builder, and [investment committee memo](decision-memo.md). The reviewed ETF model explicitly reports no feasible constrained portfolio at the original target. |
| 4 | Point-in-time signal and data card | **Complete for documented decision date** | [BAA10Y evidence](../outputs/signal-decision-evidence.md), [signal data card](signal-data-card.md), [economic signal module](../src/economic_signal.py). Historical-vintage reconstruction remains limited. |
| 5 | Estimate, historical-window, cost and constraint stresses | **Implemented; private ETF reproduction limited** | [Stress methodology](stress-testing-methodology.md), [classroom stress results](../outputs/stress-test-results.md), [ETF evidence status](../outputs/etf-analysis-status.md), and [validation report](validation-and-ai-use.md). |
| 6 | Locked Changed-Input Record | **Completed and documented** | [Locked record](locked-changed-input-record.md), [pre-run prediction commit](https://github.com/alinam06/FIN439-Project2/commit/61df82697e03946f6181c8537a712310f122650e), and [post-run results commit](https://github.com/alinam06/FIN439-Project2/commit/2d7831df74e5f8ae41fbccf7048c9ea5c3f78167). |
| 7 | Recommendation, range, monitoring and reversal triggers | **Complete in analysis and documentation** | [Decision memo](decision-memo.md), [investment judgment](investment-judgment.md), [committee logic](../src/committee.py). |
| 8 | Two opening disclosures in README, memo and videos | **Documented** | [README](../README.md), [decision memo](decision-memo.md), [validation and AI use](validation-and-ai-use.md), and video scripts. Confirm the actual recordings begin with both disclosures. |

**Evidence status note:** File links to newly drafted documents should be checked after those documents are committed to GitHub. A recorded or drafted deliverable is not automatically evidence of a successfully uploaded or accessible submission.

## 2. Original Client Mandate

The fictional Lab 13 investor is a 45-year-old executive with $5 million to invest over 15 years, intending to retire at age 60.

The investment objective is a **7.00% annual net return**.

| Requirement | Original policy |
|---|---|
| Portfolio construction | Fully invested and long-only |
| Borrowing, short selling and derivatives | Prohibited |
| Minimum investment-grade bonds | 25% |
| Minimum cash or highly liquid government securities | 10% |
| Nonexempt company concentration | Maximum 8% |
| Five-business-day redeemability | Minimum 90% |
| Benchmark | 60% global equities / 40% investment-grade bonds |
| Risk measure | Annualized portfolio standard deviation |
| Rebalancing | Annually |
| Acceptable annual loss | Unresolved |

The mandate is unchanged by hypothetical scenario analysis.

The model can verify certain numerical constraints, but instrument eligibility, look-through exposures, redemption evidence and the client's acceptable annual loss still require independent assessment.

## 3. Financial Reconciliation

### Classroom Training and Validation Model

The classroom model uses five illustrative sleeves, including a fictional individual company used to test concentration constraints.

| Portfolio | Expected annual net return | Annual volatility | Assessment |
|---|---:|---:|---|
| Equal weight across five sleeves | 5.81% | 8.67% | Fails the return objective and individual-company cap |
| 60% global equity / 40% IG bond fund | 6.65% | 10.46% | Fails return and reserve requirements |
| Constrained minimum-volatility candidate | 7.00% | 12.10% | Meets modeled numerical requirements; other investment evidence remains unverified |

The default illustrative constrained allocation is approximately:

- Treasury bills: 0%
- Treasury note: 10%
- Investment-grade bond fund: 16.98%
- Global equity: 70.10%
- Fictional company: 2.93%

The classroom return-maximizing feasible composition produces approximately **7.11% net** after the assumed 15 bp recurring investor fee.

These results demonstrate the model's calculation and constraint handling. They are not proposed live investments.

[Classroom calculations](../outputs/version_1_results.md) · [Investment judgment evidence](investment-judgment.md)

### Reviewed ETF Model

The actual Project 2 investment universe consists of BIL, IEF, LQD and VT.

| ETF | Annual forward-return assumption |
|---|---:|
| BIL | 3.50% |
| IEF | 4.25% |
| LQD | 5.00% |
| VT | 8.00% |

The assumptions are forward-looking scenarios after embedded fund expenses and before the recurring 15 bp investor charge. They are distinct from historical sample returns.

At the original 25% investment-grade bond minimum and 10% reserve requirement, the modeled maximum-return feasible composition is:

- BIL: 10%
- IEF: 0%
- LQD: 25%
- VT: 65%

This produces **6.80% gross** and **6.65% net**, a **35 bp shortfall** against the client's 7.00% objective.

The ceiling composition is a mathematical upper-bound calculation, not a proposed investment allocation. No target-meeting constrained portfolio is available.

The committee recommendation is therefore **REJECT, with $0 in live capital authorization**.

[ETF methodology](data-methodology.md) · [Decision memo](decision-memo.md)

## 4. Locked Changed-Input Record

The official experiment was conducted separately from routine automated and classroom stress tests.

**Changed input:** Minimum investment-grade bonds increased from 25% to 35%.

The reviewed ETF universe, forward-return assumptions, 60-month risk window, 10% reserve floor, 15 bp recurring fee, 7.00% target and other applicable modeled restrictions remained unchanged.

| Measure | Original result | Independent prediction | Observed result |
|---|---:|---:|---:|
| Maximum annual net return | 6.65% | 6.35% | 6.35% |
| Change in return ceiling | — | −30 bp | −30 bp |
| Return shortfall to objective | 35 bp | 65 bp implied | 65 bp |
| Target-meeting allocation | None | None predicted | None |
| Committee decision | REJECT | REJECT | REJECT |

The student-reported chronology records a pre-run prediction committed at approximately **11:12 a.m. Eastern on November 22, 2026**, followed by execution at approximately **11:23 a.m. Eastern**.

The observed return ceiling declined by 30 basis points, matching the locked numerical prediction at displayed precision. The recommendation remained REJECT.

This was a hypothetical constraint test. It did not permanently change the original Lab 13 mandate.

**Commit evidence:**

- [Original pre-run prediction](https://github.com/alinam06/FIN439-Project2/commit/61df82697e03946f6181c8537a712310f122650e)
- [Results and reconciliation](https://github.com/alinam06/FIN439-Project2/commit/2d7831df74e5f8ae41fbccf7048c9ea5c3f78167)
- [Complete experiment record](locked-changed-input-record.md)

Commit history preserves the recorded order. The reported AI-off condition is a student attestation rather than something independently established by the model tests.

## 5. Stress Testing and Financial Sensitivity

The application evaluates changes in investment assumptions across the four required dimensions.

| Dimension | Executed evidence | Investment significance |
|---|---|---|
| Forward-return estimates | Reducing LQD and VT assumed returns by 1 percentage point each lowers the original ETF return ceiling to approximately 5.81%. | The proposal becomes more infeasible under weaker credit and equity return assumptions. |
| Historical estimation window | Fixed-weight benchmark volatility was approximately 9.19% using 36 months and 12.23% using 60 months. | Modeled risk is sensitive to historical sampling. |
| Recurring costs | Removing the 15 bp investor fee raises the original ETF ceiling to 6.80%, still 20 bp below target. | Lower fees alone do not make the evaluated universe feasible. |
| Investment constraints | Increasing the bond floor to 35% reduces the modeled ceiling from 6.65% to 6.35%. | A tighter requirement increases the opportunity cost of holding higher-return equities. |

The adverse LQD/VT return shock under the separate 35% bond-floor scenario produces a ceiling of approximately **5.54%**. This is not the same scenario as the 5.81% original-mandate downside result.

The classroom model also provides illustrative correlation, volatility, reserve, combined-adverse and one-time transition-cost scenarios. ETF-specific transaction-cost stress is not implemented.

A return ceiling below the client's net objective is a stopping condition for the evaluated investment proposal.

[Stress-testing methodology](stress-testing-methodology.md) · [Classroom stress results](../outputs/stress-test-results.md)

## 6. Point-in-Time Economic Signal

BAA10Y measures the difference between Moody's seasoned Baa corporate bond yield and the 10-year Treasury yield.

The dated November 21, 2026 review used a FRED observation table, with November 19 as the latest observed date and November 20 as the reported update date.

The reviewed evidence showed a **12 bp widening** over 20 numeric observation steps, excluding the missing November 11 observation.

The signal prompted additional review of LQD credit exposure and VT equity downside. It did not automatically change portfolio weights, expected returns or covariance.

The evidence supports the stated November 21 monitoring decision. It does not establish a complete historical vintage backtest.

[FRED signal result](../outputs/signal-decision-evidence.md) · [Signal data card](signal-data-card.md)

## 7. Data Integrity and Reproduction Boundary

The reviewed ETF model uses four authorized Alpha Vantage monthly adjusted price exports.

The reviewed panel consists of 61 aligned monthly adjusted prices for each ETF, producing 60 monthly returns ending in October 2026.

The financial methodology documents:

- Instrument identity and source provenance.
- Exchange-session and month-end alignment.
- Adjusted-close return calculations.
- Missing, duplicate, invalid and excluded observations.
- Arithmetic and geometric return conventions.
- Monthly sample covariance multiplied by 12.
- Separate forward-looking return assumptions.
- Recurring fees and net-return calculations.
- Snapshot dates and limitations of historical point-in-time inference.

Public redistribution permission for the raw ETF histories, aligned dataset, covariance evidence and private derived reports was not established. These materials are therefore excluded from the public repository.

The public Streamlit application runs in **Training and validation** mode without private datasets or credentials.

The reviewed ETF decision and Locked Changed-Input experiment are documented through repository evidence and recorded presentations, but independent numerical reproduction of those specific ETF results requires authorized data.

A later authorized download may contain revisions and may not reproduce the original snapshot exactly.

[Data methodology](data-methodology.md) · [Private data preparation instructions](../data/README.md) · [ETF evidence status](../outputs/etf-analysis-status.md)

## 8. Six Official Grading Categories

| Category | Maximum points | Existing evidence | Remaining verification |
|---|---:|---|---|
| Problem definition and decision usefulness | 45 | Client mandate, benchmarks, investment recommendation, committee request and decision memo | Confirm final memo is uploaded and consistent with the app |
| Data integrity and traceability | 45 | ETF methodology, sample definitions, dated signal, source records and exclusions | Private-data permissions and independent ETF reproduction remain limited |
| Financial soundness and judgment | 60 | Return bridge, modeled ceiling, baselines, constraints, sensitivity, REJECT recommendation | Verify that presentation and memo distinguish original mandate from hypothetical experiment |
| Technical execution and usability | 45 | Streamlit application, public deployment, README and automated tests | Independently verify fresh checkout and browser functionality |
| Validation, sensitivity and reproducibility | 75 | Known-answer tests, recorded 102-test suite, regression evidence, stress analysis and completed locked record | Independent clean-run evidence remains unverified |
| Professional communication | 30 | README, decision memo draft, validation report draft, video scripts and submission manifest preparation | Verify actual uploaded documents, final video links, transcripts and disclosures |
| **Total** | **300** | Evidence map only | No grade estimate |

## 9. Validation and AI-Assisted Development

The recorded project validation suite passed **102 tests**, with zero reported failures, errors or skips. Five saved financial artifacts were reported to reproduce byte for byte.

Financial checks include Lab 14 known answers, portfolio arithmetic, covariance calculations, invalid inputs, mandate evaluation, historical-data processing, point-in-time filtering, stress testing and Streamlit application routing.

During application testing, the student encountered:

`TypeError: stress_view() takes 1 positional argument but 3 were given`

Codex-assisted investigation reproduced the routing failure through a regression test. The call interface was corrected, and subsequent recorded tests passed.

The original running process version could not be conclusively identified. The regression and correction are documented without claiming that the exact original execution environment was recovered.

These checks support software correctness under tested inputs but do not resolve financial suitability or guarantee future investment performance.

[Validation and AI-use report](validation-and-ai-use.md) · [Recorded test results](../outputs/validation-summary.md)

## 10. Project Development Evidence

The original Lab 13 mandate and Lab 14 known-answer calculations established the investment problem and core quantitative methods.

The subsequent integrated BoilerPortfolio application added the portfolio construction interface, ETF evidence handling, historical-window analysis, economic signal, stress testing, committee logic and deterministic investment explanations.

The earlier classroom calculation records and GitHub history are evidence of this development. Claims about specific Edition A and Edition B timestamps should be limited to dates that can be established from the actual course record or Git history.

[Original classroom results](../outputs/version_1_results.md) · [Validation chronology](../outputs/validation-summary.md)

## 11. GitHub Submission Checklist

| Deliverable | Status / location |
|---|---|
| Application, source code and dependencies | [GitHub repository](https://github.com/alinam06/FIN439-Project2) |
| README and launch instructions | [README](../README.md) |
| Public classroom results | [Executed public results](../outputs/version_1_results.md) |
| Stress methodology and public evidence | [Methodology](stress-testing-methodology.md) · [Results](../outputs/stress-test-results.md) |
| Data methodology | [Data methodology](data-methodology.md) |
| Economic signal evidence and card | [Data card](signal-data-card.md) · [Executed signal](../outputs/signal-decision-evidence.md) |
| Investment judgment | [Investment judgment evidence](investment-judgment.md) |
| Locked Changed-Input Record | [Completed record](locked-changed-input-record.md) |
| Investment committee decision memo | [Decision memo](decision-memo.md) — verify uploaded |
| Validation and AI-use report | [Validation report](validation-and-ai-use.md) — verify uploaded |
| Three recorded video presentations | Verify accessible YouTube links in submission manifest |
| Video transcripts | Verify uploaded scripts match actual spoken recordings |
| Submission manifest | Verify final manifest exists at the repository root and includes all links |
| Independent cold-run evidence | Not independently verified; do not claim completion without an actual test |

Do not upload restricted ETF histories, private monthly returns, private covariance matrices or reports, API credentials, virtual environments, Python caches or other unnecessary local files.

## 12. Independent Reproducibility Check

A reviewer can test the public application using the GitHub repository and the installation instructions in the README.

The expected public experience is the illustrative classroom model, without requiring private ETF files or API credentials.

Useful observable checks include:

| Check | Expected result |
|---|---|
| Application launches | Streamlit opens the public classroom experience |
| Investment Overview | Shows the 7.00% objective, approximately 7.11% classroom ceiling and $0 live authorization |
| Equal-weight classroom baseline | 5.81% net return, approximately 8.67% volatility |
| 60/40 classroom benchmark | 6.65% net return, approximately 10.46% volatility |
| Constrained classroom candidate | 7.00% modeled net return, approximately 12.10% volatility |
| Risk & Scenario Analysis | Classroom stress testing available without private ETF data |
| Committee Decision | Classroom result identified as illustrative, with no live capital authorized |
| Investment Assistant | Responds using deterministic calculation-based explanations |
| Committee briefing export | Downloads and reflects the active public scenario |

A hosted deployment or local automated test should not be described as a completed independent fresh-install test.

## 13. Outstanding Investment Approval Gates

Before any investment can be approved, the committee must establish:

1. A defensible expected net return meeting the client's original 7.00% objective under the applicable constraints.
2. Verified fund eligibility, issuer concentration treatment and permitted investment practices.
3. Evidence that at least 90% of the portfolio can become available cash within five business days.
4. An acceptable annual loss tolerance defined by the client.
5. Appropriate implementation cost estimates, downside resilience and monitoring arrangements.
6. A separate committee approval for the revised investment proposal.

Until these conditions are satisfied, the reviewed ETF investment decision remains **REJECT with $0 live authorization**.

Paper-testing BoilerPortfolio may continue without granting trading authority.
