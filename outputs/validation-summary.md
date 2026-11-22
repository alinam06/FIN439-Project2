# Stage 1 financial and technical validation

**Result.** 18 automated tests passed in the existing course virtual environment. The Stage 1 changes preserve the Lab 13 client terms and the displayed Version 1 portfolio metrics. The optimized allocation has an overall **Unverified** verdict. Clean-environment installation remains unverified.

## Scope and files

Inspected `app.py`, `src/__init__.py`, `src/assumptions.py`, `src/portfolio.py`, `src/report.py`, `tests/test_app.py`, `tests/test_portfolio.py`, `requirements.txt`, `README.md`, `outputs/version_1_results.md`, and the parent-folder `lab13.md` and `LAB14.md`.

Changed `src/portfolio.py`, `app.py`, and `src/report.py`. Extended `tests/test_portfolio.py` and `tests/test_app.py`, added `tests/test_lab14.py`, updated `README.md`, regenerated `outputs/version_1_results.md`, and added this summary. The dependency pins, sample assumptions, and client terms stayed the same.

## Financial calculation audit

| Item | Calculation and audit finding |
| --- | --- |
| Expected annual portfolio return | Gross return is the weighted arithmetic mean of the individual expected annual returns, `wᵀμ`. Inputs are annual and illustrative. The dashboard shows the net version. An arithmetic expectation does not establish a realized compound growth rate. |
| Annual portfolio volatility | Compute `Σᵢⱼ = σᵢ σⱼ ρᵢⱼ`, then `√(wᵀΣw)`. The inputs are already annual, so the code applies no additional annualization multiplier. The earlier positive-definite-only rule rejected valid singular matrices even for risk measurement. Covariance construction now rejects material negative eigenvalues and accepts PSD input within numerical tolerance. Optimization still requires positive definiteness. |
| Weights and dollars | Equal weight uses `1/n` across the five demo sleeves. The fixed policy comparator uses 60% global equity and 40% U.S. IG bonds. The optimizer solves for weights. Dollar exposures equal unrounded weights times the scenario value. Presentation rounding can keep displayed totals from adding exactly to 100% or the portfolio value. Earlier code calculated metrics even for finite underfunded, overfunded, or negative allocations. The shared metrics function now rejects those inputs within a `1e-9` weight tolerance. |
| Net return | Subtract 15 basis points from the weighted gross return. The optimizer subtracts the same cost from every asset coefficient, which is equivalent under full investment. The fee is a demo assumption and excludes taxes, spreads and transaction costs. The default benchmark reconciles from 6.80% gross to 6.65% net. |
| Maximum modeled return | Enumerate vertices of the fully invested long-only feasible set defined by the modeled bond, reserve and company rules, then maximize the linear net return over those vertices. At default the max-return mix is 10% Treasury note, 15% IG fund, 67% equity fund and 8% fictional company stock, yielding 7.11% net. The ceiling excludes unverified rules. It cannot establish mandate-level achievability or a real investment opportunity. |
| 15-year compounded target value | Compute `$5,000,000 × 1.07^15 = $13,795,157.70` with no cash flows. The UI rounds to whole dollars. Changing the horizon affects this scenario value. The figure represents the target compounded at a constant rate. |
| Efficient frontier | Start with the modeled global minimum-variance mix and sample increasing return floors up to the ceiling. Each plotted point comes from a fresh constrained variance minimization. The default has 13 points, from about 1.56% volatility and 3.71% net return to 12.64% volatility and 7.11% net return. Lines join sampled points. The baseline markers can fall outside the modeled feasible set. |
| Constrained optimum | Minimize variance, equivalent to minimizing volatility, subject to modeled limits and a net return floor. The earlier face solve used a normal-equation system that can amplify conditioning problems. The revised solver transforms the objective with a Cholesky factor, solves by least squares, and checks equality residuals and all model inequalities. The default optimum matches a closed-form calculation on the binding face. It returns 7.00% net at 12.10% volatility. The 7.50% sensitivity has no optimized mix. |
| Mandate verdict | Compute budget, gross and net weight constraints, aggregate nonexempt issuer weights, bond and reserve shares, and the modeled return objective. Modeled failures take precedence. With passing model checks and missing evidence or policy, the overall verdict is Unverified. Rebalancing is specified annually and execution is unverified. The five-day rule is unverified at any positive requirement. A 0% scenario threshold is trivially met. |
| Committee recommendation | The app selects a written due-diligence recommendation when an optimized mix meets modeled checks and a defer message when the modeled target or constraints are infeasible. This is scenario-dependent wording for a fictional committee. No committee meeting, approval, or investment decision is recorded. |

No computed portfolio outcome is embedded in the app. Fixed values are the mandate and classroom/demo inputs, policy benchmark weights, age and retirement labels, and authored recommendation text. The saved results are generated. Tests intentionally hold independent known answers as assertions.

## Independent Lab 14 results

The fixtures duplicate the course-authored four-sleeve inputs independently of the five-sleeve demo. The fee is zero and inverse volatility uses normalized reciprocal volatilities. Tests allow half of 0.01 percentage point when comparing with the course's displayed precision.

| Case | Calculated return | Calculated volatility | Expected rounded return / volatility |
| --- | ---: | ---: | --- |
| 60/40 benchmark | 6.8000% | 10.4614% | 6.80% / 10.46% |
| Equal weight | 5.2000% | 5.2145% | 5.20% / 5.21% |
| Inverse volatility | 3.7721% | 1.0497% | 3.77% / 1.05% |
| Benchmark with IG/equity correlation of 0.50 | 6.8000% | 10.9982% | 6.80% / 11.00% |

Tests rejected 1.30 correlations, asymmetric correlations, a symmetric indefinite example, and invalid weights including negative, non-finite, and misfunded weights. The original covariance had a strictly positive minimum eigenvalue of about 0.00002463 in annual decimal variance units. A singular PSD control produced zero volatility for a perfectly offsetting portfolio.

## Lab 13 mandate reconciliation

The default uses $5 million, age 45, retirement at 60, a 15-year horizon, 7% annual net objective, an 8% nonexempt company cap, 25% minimum IG allocation, 10% minimum reserve, 90% minimum five-day redemption, and annual rebalancing. The sample applies a full-investment long-only budget, exempts its diversified funds and U.S. Treasuries from modeled issuer caps, and flags underlying fund leverage and derivatives for verification. Annual loss tolerance remains unresolved. The Meridian foundation terms do not enter the default or custom-mode starting values.

The reserve and bond eligibility flags are demo classifications. In particular, bills count toward reserve only and the Treasury note counts toward both tests. Actual security and fund classification, issuer and exemption documentation, fund leverage and derivatives exposure, liquidity terms and annual rebalancing execution require evidence. The modeled return pass concerns the 7% threshold under assumed inputs.

## Execution evidence

Existing environment ran Python 3.14.7, Altair 6.3.0, NumPy 2.5.4, pandas 3.0.6, and Streamlit 1.66.0. `pip check` found no broken requirements. Compilation and imports passed. The regenerated Markdown matched the checked-in results byte for byte.

The final suite ran **18 tests with zero failures or errors**. Three Streamlit AppTest cases covered custom input reruns, portfolio dollars and horizon, changed liquidity evidence, company and bond caps, restoration of default mode, and controlled error display. AppTest exercised Streamlit's script runner and emitted its bare-mode context warning. It did not verify browser rendering. Financial tests covered the independent Lab 14 cases, default policy, default optimizer and frontier, infeasibility, boundary cases, validation errors and result-file reproduction.

Commands executed from the project root:

```sh
../.venv/bin/python -m unittest discover -s tests -v
../.venv/bin/python -m pip check
../.venv/bin/python -c 'import sys, altair, numpy, pandas, streamlit, app, src.assumptions, src.portfolio, src.report; print(sys.version.split()[0], altair.__version__, numpy.__version__, pandas.__version__, streamlit.__version__)'
../.venv/bin/python -m compileall -q app.py src tests
../.venv/bin/python -m src.report
../.venv/bin/python -m src.report --output /tmp/fin439-stage1-results.md
cmp outputs/version_1_results.md /tmp/fin439-stage1-results.md
```

Two clean virtual environments were created. Both installs stopped at `streamlit==1.66.0` with pip reporting no matching distribution and no candidate versions. The existing course environment does have that version. Public package availability and clean launch were not established from this environment.

```sh
validation_env=$(mktemp -d /tmp/fin439-stage1.XXXXXX)
python3.14 -m venv "$validation_env"
"$validation_env/bin/python" -m pip --disable-pip-version-check install --no-cache-dir --retries 0 --timeout 8 -r requirements.txt

validation_env=$(mktemp -d /tmp/fin439-stage1-public.XXXXXX)
python3.14 -m venv "$validation_env"
"$validation_env/bin/python" -m pip --disable-pip-version-check install --index-url https://pypi.org/simple --no-cache-dir --retries 0 --timeout 8 -r requirements.txt
```

## Readiness and unresolved risks

Version 1 is validated as a demonstration and provides a regression baseline for designing real-data integration. Readiness to consume real data remains open. The current universe and return inputs are fixed, the face-enumeration solver is intended for a small universe and requires positive-definite risk, and there is no data ingestion, evidence feed, or point-in-time provenance check in this app. Real-data work needs documented return, covariance and cost methodology, treatment of singular and ill-conditioned samples, holdings/issuer and redemption evidence, and a reproducible installation and browser smoke test. Implementation readiness additionally requires client clarification of annual loss tolerance and a rebalancing workflow. Stage 1 creates no official Locked Changed-Input Record.

## Stage 2 reproducibility check

The existing course environment uses CPython 3.14.7 on arm64 macOS and the four direct pins in `requirements.txt`. Installed Streamlit metadata requires Altair >=5 and <7 (excluding 5.4.0 and 5.4.1), NumPy >=1.25 and <3, and pandas >=1.5.3 and <4. The current pins satisfy those ranges. The public Streamlit release includes a universal Python 3 wheel and requires Python 3.11 or newer. NumPy and pandas list CPython 3.14 macOS wheels. No version replacement was justified. [Streamlit 1.66.0](https://pypi.org/project/streamlit/1.66.0/), [Altair 6.3.0](https://pypi.org/project/altair/6.3.0/), [NumPy 2.5.4](https://pypi.org/project/numpy/2.5.4/), [pandas 3.0.6](https://pypi.org/project/pandas/3.0.6/)

| Check | Observed result |
| --- | --- |
| New virtual environment | Created successfully with Python 3.14.7 and pip 26.2.1. |
| Clean pip install | Failed. Verbose output showed a DNS failure resolving `pypi.org`, followed by zero candidate links and “No matching distribution found.” This reproduces the earlier symptom with a diagnosed index-access failure. It provides no fresh transitive resolution result. |
| Existing environment test suite | 18 passed, 0 failures, 0 errors. This includes the separate Lab 14 classroom fixtures and three Streamlit script-runner tests. No new automated tests were added because Stage 2 changes documentation only. |
| Existing environment pip check | No broken requirements found. |
| Financial reproduction | Byte-for-byte match to the saved Version 1 report. |
| Server launch from existing environment | Streamlit reached socket binding and received `PermissionError: [Errno 1] Operation not permitted` on loopback. No browser verification was performed in this session. |

```sh
validation_env=$(mktemp -d /tmp/fin439-stage2.XXXXXX)
python3.14 -m venv "$validation_env"
"$validation_env/bin/python" -m pip --isolated --disable-pip-version-check install --index-url https://pypi.org/simple --no-cache-dir --retries 0 --timeout 8 -vv -r requirements.txt

../.venv/bin/python -m unittest discover -s tests -v
../.venv/bin/python -m pip check
../.venv/bin/python -m src.report --output /tmp/fin439-stage2-results.md
cmp outputs/version_1_results.md /tmp/fin439-stage2-results.md
../.venv/bin/python -m streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 8752 --browser.gatherUsageStats false
```

Stage 2 updated the README and this record, and added [the proposed data methodology](../docs/data-methodology.md). No market prices were collected, and the application, model, tests and saved financial results were preserved. The setup still needs a network-enabled clean install and browser smoke test. The data methodology supports a separate pilot after provider access and rights are confirmed. Connecting historical data to the optimizer remains pending provenance, coverage, forward-looking assumptions, costs and mandate evidence.

## Stage 3 historical data pilot

Stage 3 was built and tested in a temporary copy because the project had moved from `project 2` to `project_2`, where the session could read files but could not write. The patch was checked against the original tree. The classroom assumptions, optimizer, Lab 13 mandate, 18 existing tests and saved financial report were preserved.

| Check | Observed result |
| --- | --- |
| Alpha Vantage adjusted monthly download | Terminal DNS resolution failed for `www.alphavantage.co`. Browser-tool probes of the four public demo queries yielded no accessible payload. No API key was available. |
| Real-market observations | Zero retrieved. No dates, returns, volatility, correlations, drawdown, or missing-observation counts are reported for the four real ETFs. |
| Existing tests | 18 passed. |
| New tests | 9 passed, covering chronology, data rejection, consecutive month alignment, total returns, annualization, covariance, correlation, drawdown, outlier retention and two Streamlit flows. During development one UI test failed first in the AppTest wrapper and then on its chart element identifier. Both assertions were corrected and the final run passed 27 of 27. |
| Classroom results | Regenerated report matched the Version 1 report byte for byte. |
| UI | Streamlit AppTest verified offline demonstration, the empty historical view, and four chart elements with synthetic uploads. Browser rendering was not tested. |

The synthetic fixture spans January 31, 2019 through January 31, 2024. Its IEF-labeled test column produced 1.00% annualized arithmetic return, 6.7585% annualized volatility, 3.95% cumulative performance, and a 10.00% monthly-close maximum drawdown. These are fixture values. Actual fund performance remains unavailable. The [data methodology](../docs/data-methodology.md#stage-3-import-workflow) documents source metadata, upload format, adjustments and data-quality gates. No redistribution permission or point-in-time coverage was established.

Commands run from the staged copy using the existing course interpreter:

```sh
python -m unittest discover -s tests -v
python -m src.report --output /tmp/fin439-stage3-results.md
cmp outputs/version_1_results.md /tmp/fin439-stage3-results.md
```

Ready for code and methodology review. Market-data and committee review require an authorized adjusted-close sample, provider/calendar and distribution reconciliation, and independent evidence on eligibility and liquidity. The point-in-time macroeconomic requirement and official Locked Changed-Input Record remain separate.

## Friday integration and stability check

The full sibling checkout under `project_2/FIN439-Project2` already contained Stage 3, confirmed by a successful reverse patch check. The original workspace under `project 2/FIN439-Project2` contained only `app.py` and had no importable project modules. Neither folder had Git metadata. The session could read the full sibling but could not write there. The writable workspace now contains the verified Stage 3 files and a merged app entry point that matched the sibling byte for byte before documentation edits. The Lab 13 mandate, financial engine, and saved results were preserved.

- Full sibling and repaired workspace each passed all 27 tests.
- The repaired workspace passed `pip check` and reproduced the saved financial report byte for byte.
- The integrated app reached server binding on localhost and received `PermissionError: [Errno 1] Operation not permitted` in the sandbox. Streamlit script-runner checks passed. A local browser smoke test remains open.
- Setup instructions now cover macOS, Linux and Windows PowerShell. Clean dependency installation and the Linux and Windows runs remain unverified.
- Historical upload is available. A real adjusted-price sample, point-in-time macroeconomic signal, and evidence for full mandate compliance remain open. The official Locked Changed-Input Record is a separate AI-off exercise.

Executed from the repaired workspace using the existing course virtual environment:

```sh
../../project_2/.venv/bin/python -B -m unittest discover -s tests -v
../../project_2/.venv/bin/python -B -m pip check
../../project_2/.venv/bin/python -B -m src.report --output /tmp/fin439-friday-results.md
cmp outputs/version_1_results.md /tmp/fin439-friday-results.md
../../project_2/.venv/bin/python -B -m streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 8752 --browser.gatherUsageStats false
```

## Stage 4 point-in-time economic signal

Implemented an offline BAA10Y ALFRED import and a read-only Economic Signals view in the authoritative `project 2/FIN439-Project2` workspace. Reviewed the official series, archive, real-time interval and observation API documentation. No machine-readable observations or authenticated BAA10Y archive were retrieved. The terminal request could not resolve the FRED API host, and no FRED API key was available. The view reports the signal unavailable until a valid archive is supplied. The [signal data card](../docs/signal-data-card.md) documents the import and restrictions.

| Check | Observed result |
| --- | --- |
| Git root | `git rev-parse --show-toplevel` found no Git repository in the folder or its parents. No repository was initialized. |
| Project-local environment | The README gives a self-contained Python 3.14 setup from `requirements.txt`. A fresh temporary virtual environment was created successfully. Pip found no candidate distributions in the sandbox, and a direct PyPI probe could not resolve the host. |
| Automated tests | 33 passed, zero failures and zero errors. This includes the existing 27 and six new tests with synthetic vintage inputs. |
| Vintage and decision validation | Tests covered a future publication, a future revision, an inclusive same-day vintage, missing and stale observations, invalid responses, monitor and review states, and a Streamlit chart from synthetic data. The tested signal flow does not invoke the allocation engine. |
| Report and scope | The saved Version 1 report reproduced byte for byte. The mandate and portfolio engine were preserved. The sibling `project_2` copy was used only as the source of the existing interpreter. |

```sh
git rev-parse --show-toplevel
../../project_2/.venv/bin/python -B -m unittest discover -s tests -v
../../project_2/.venv/bin/python -B -m pip check
../../project_2/.venv/bin/python -B -m src.report --output /tmp/fin439-stage4-results.md
cmp outputs/version_1_results.md /tmp/fin439-stage4-results.md
```

Real-archive compatibility and data coverage remain to be verified with an authorized export. The same-day cutoff is date-level and should be used after the day's releases. The widening rule is a committee review prompt without demonstrated predictive performance. The official AI-off Locked Changed-Input Record remains separate.

## Professional UI and model classification review

Redesigned the authoritative workspace with six sidebar sections, a navy and teal light theme, grouped scenario controls and a reset, an executive briefing with return headroom, and stacked allocations plus a mandate-aware efficient frontier. Existing historical and ALFRED uploads remain available. Stress testing is marked unfinished.

The full suite passed **35 tests with zero failures or errors**. This retains the prior 33 cases, including the original 27. One existing interface test now navigates to the dedicated Compliance and Portfolio Analysis pages before reading the same outputs. Two new tests check default and infeasible headroom, the reset control, chart rendering in AppTest and the unfinished stress-testing status. The saved report reproduced byte for byte. The portfolio engine and classroom assumptions matched the previous files.

```sh
../../project_2/.venv/bin/python -B -m unittest discover -s tests -q
../../project_2/.venv/bin/python -B -m src.report --output /tmp/fin439-ui-results.md
cmp outputs/version_1_results.md /tmp/fin439-ui-results.md
```

The default shows 7.00% expected annual net return, 12.10% annual volatility, 7.11% as the modeled ceiling, +11 bp headroom, and an Unverified overall verdict. The modeled ceiling excludes unverified rules. The issuer cap is exercised by a fictional stock in the classroom universe. It is absent from the ETF upload universe. The modeled 10-year Treasury note qualifies separately for the bond and reserve minimums, with a single weight in the portfolio budget. Its reserve classification is illustrative and does not establish five-day redeemability or the eligibility of an ETF wrapper.

AppTest exercised the interface and chart elements. Browser visual and responsive checks were not performed. Outstanding work includes stress calculations, actual ALFRED and ETF sample validation, and evidence for mandate rules marked Unverified.

## Stage 5 stress testing and decision intelligence

Implemented six hypothetical presets, a custom stress editor, original-weights and reoptimized comparisons, explicit stop/reject/defer/due-diligence decisions, and an experiment export with deterministic replay. The stress-only parameters reuse the existing portfolio engine. The default mandate, assumptions, historical ETF upload, and ALFRED signal remain in place.

- **43 tests passed, zero failures and zero errors.** The prior 35 cases remain. The existing stress-navigation test now verifies the implemented page and its missing-data state. Eight new tests cover costs, infeasibility, covariance validation, reserve/bond/issuer enforcement, due diligence, synthetic historical windows, export/replay, and Streamlit error and decision states.
- Both the original Version 1 report and the dated stress report reproduced byte for byte. `pip check` found no broken requirements in the existing course environment.
- Base net return and volatility were 7.00% and 12.10%. The equity deterioration and combined adverse cases reduced the modeled return ceiling to 5.61% and 5.25%, respectively. Both cases deferred without a reoptimized allocation. A higher reserve floor rejected the original weights; reoptimization met the 7.00% target with the 15% floor before unresolved checks.
- The stock/bond preset uses 0.40, because 0.50 with the other classroom pairs fixed is not positive semidefinite. Invalid settings stop the analysis without an export.
- Historical windows used a synthetic panel in tests. No real adjusted-price panel or ALFRED archive was supplied for this run. The interface was exercised with Streamlit AppTest. Browser rendering was not verified in this session. The official AI-off record remains separate.

```sh
../../project_2/.venv/bin/python -B -m unittest discover -s tests -v
../../project_2/.venv/bin/python -B -m src.report --output /tmp/fin439-stage5-v1.md
cmp outputs/version_1_results.md /tmp/fin439-stage5-v1.md
../../project_2/.venv/bin/python -B -m src.stress_report --as-of 2026-11-21 --output /tmp/fin439-stage5-stress.md
cmp outputs/stress-test-results.md /tmp/fin439-stage5-stress.md
../../project_2/.venv/bin/python -B -m pip check
```

## Stage 6 market data and decision evidence

The Alpha Vantage and FRED API terminal requests failed DNS resolution and neither API key was available. Browser-tool ALFRED archive requests did not return a usable response. The public official FRED table was accessible. The November 21, 2026 dated snapshot had 21 numeric observations and one explicit missing entry from October 21 through November 19. The 20-observation rule returned **+12 bp / Review**. This verifies a current decision-date example and leaves real ALFRED vintage/revision verification open. [Decision evidence](signal-decision-evidence.md)

No authorized ETF observations were retrieved. The actual 36/60-month windows, allocation, risk and feasibility remain **Unavailable**. The import workflow uses adjusted closes, strict alignment, a reviewed capture-date cutoff and dated forward-return inputs. Source restrictions, assumptions, and reproduction steps appear in the [ETF methodology](../docs/data-methodology.md#stage-6-etf-portfolio-analysis). [ETF evidence status](etf-analysis-status.md)

The full suite passed **48 tests, 0 failures, 0 errors**, including all 43 prior cases. The five new cases used synthetic ETF data and covered the shared endpoint and return ceiling, differing covariance/risk, conditional constraint checks, infeasibility, rejection of earlier snapshots and singular covariance, adjusted-column-only import and date matching, and Streamlit integration through export rendering. Both previous financial reports reproduced byte for byte. Browser visual testing was not performed. No raw vendor data or official AI-off prediction was added.

```sh
../../project_2/.venv/bin/python -B -m unittest discover -s tests -q
../../project_2/.venv/bin/python -B -m src.report --output /tmp/fin439-stage6-base.md
cmp /tmp/fin439-stage6-base.md outputs/version_1_results.md
../../project_2/.venv/bin/python -B -m src.stress_report --as-of 2026-11-21 --output /tmp/fin439-stage6-stress.md
cmp /tmp/fin439-stage6-stress.md outputs/stress-test-results.md
```

## Consolidation and clean-user checks

Audited the workflow for decision relevance. Prior ETF upload controls were repeated on two pages, the economic signal required a separate upload page, the committee briefing exposed feasibility without assignment action categories, and the project-local setup was buried in earlier validation detail. The app now centralizes optional files and session overrides, uses one active mandate, and keeps the forward-looking classroom inputs distinct from the optional ETF comparison and signal research. Signal flags add committee monitoring context without changing optimizer inputs. Experiment replay uses the recorded inputs and stays separate from the current scenario.

The default case advances to a paper **PILOT** with 0% live deployment. A 7.50% return target remains above the 7.11% modeled ceiling and produces **REJECT** for that allocation. ADOPT, ALLOCATE TO, and REBALANCE can be considered under the proposed-action control, and no execution is approved. Security evidence and annual loss tolerance remain unresolved.

**54 tests passed with zero failures or errors.** The prior 48 cases remain, with updated navigation for existing UI tests. Six added cases cover missing and partial files, local auto-loading, session override isolation, decision gates and ranges, offline startup and scenario consistency, and shared ETF data on risk and research pages. Both financial reports reproduced byte for byte. Testing used an existing interpreter. No external project path is used by the application or required by the README startup instructions. No real ETF prices or new ALFRED vintages were supplied, and no official AI-off prediction was written.

```sh
../../project_2/.venv/bin/python -B -m unittest discover -s tests -q
../../project_2/.venv/bin/python -B -m src.report --output /tmp/fin439-consolidated-base.md
cmp /tmp/fin439-consolidated-base.md outputs/version_1_results.md
../../project_2/.venv/bin/python -B -m src.stress_report --as-of 2026-11-21 --output /tmp/fin439-consolidated-stress.md
cmp /tmp/fin439-consolidated-stress.md outputs/stress-test-results.md
```

Streamlit AppTest covered application behavior. A direct launcher reached localhost port binding and received PermissionError. Browser rendering and a new dependency installation remain unverified.

## Actual ETF integration

Reviewed the four original Alpha Vantage monthly adjusted exports without modifying them. The import now accepts provider headers with spaces and either documented filename form. The raw counts were 234 BIL, 292 IEF, 292 LQD, and 221 VT. All four selected series contain 61 aligned month-end closes and 60 monthly returns. No duplicate dates, missing selected months, nonpositive prices, or outlier-screen flags remained. The incomplete November observation and earlier history were excluded. Sponsor identity and provider methodology were corroborated. Every issuer distribution was not independently reconciled.

The private, derived ETF reports were generated and reproduced in automated tests. The default 7.00% target was infeasible under the stated ETF assumptions in both windows. A separate lower-target diagnostic demonstrates the impact of window selection. The prepared, hash-matching pair automatically activates ETF results in the executive view. The classroom fallback remains selectable and retains its original outputs. Neither path approves live allocation with unverified checks.

**57 tests passed, zero failures and zero errors**, including all 54 prior cases and three licensed-snapshot cases. The classroom and stress reports also reproduced byte for byte. Streamlit AppTest exercised the executive model switch; no separate browser visual test was performed. A clean checkout without the private snapshot skips the three snapshot-specific tests. Actual ETF input files and derived reports are ignored by Git pending redistribution permission. No API credentials were needed or written. ALFRED revision data, mandate verification, and the official AI-off record remain separate.

```sh
../../project_2/.venv/bin/python -B -m src.etf_evidence --prepare --captured-at 2026-11-21T11:45:36-05:00
../../project_2/.venv/bin/python -B -m unittest discover -s tests -q
../../project_2/.venv/bin/python -B -m src.report --output /tmp/fin439-actual-v1.md
cmp /tmp/fin439-actual-v1.md outputs/version_1_results.md
../../project_2/.venv/bin/python -B -m src.stress_report --as-of 2026-11-21 --output /tmp/fin439-actual-stress.md
cmp /tmp/fin439-actual-stress.md outputs/stress-test-results.md
```

## Risk routing and full dashboard regression

The reported browser error was `TypeError: stress_view() takes 1 positional argument but 3 were given`. The authoritative file inspected at the start already accepted three arguments, so the original browser process or module version could not be confirmed. An AppTest using the one-argument renderer reproduced the exact TypeError at the prior `app.py` line 269. Its empty-exceptions assertion failed before the fix and passed afterward.

Classroom risk rendering now calls the classroom renderer with the mandate. The separate historical section retains the ETF panel and source-review status. ETF mode evaluates its own base and adverse forward returns against the same mandate, recurring cost and reviewed 36/60-month covariance. Classroom holdings and forecasts do not enter those calculations. The base ceiling stays at 6.65%. A 1.00 pp LQD/VT forward-return reduction lowers it to 5.81%. A 6.50% target produces a paper PILOT for the base and REJECT under the adverse scenario. Reset restores the Lab 13 target. Feasible modeled mixes remain Unverified.

**60 tests passed, zero failures and zero errors** on the final full suite. This preserves all 57 earlier tests and adds three tests for the signature regression, both-mode navigation, and missing-data fallback. The new navigation checks inspect `AppTest.exception` and unexpected `st.error` outputs across Executive Overview, Portfolio Builder, Portfolio Comparison, Risk and Scenario Analysis, and Research and Validation. They exercise default and custom scenarios, page switches, reset, an ETF downside input, classroom presets, allocation display, and research subtopics. A separate run repeated the both-mode navigation and scenario matrix with the actual private ETF files, with no unhandled exceptions.

Classroom, classroom stress and both private ETF Markdown reports, plus the ETF monthly return CSV, reproduced byte for byte. Browser startup was attempted. The sandbox refused localhost socket binding with PermissionError, so direct browser verification remains open. The Lab 13 mandate, licensing protections and official AI-off record were preserved.

```sh
../../project_2/.venv/bin/python -B -m unittest discover -s tests -p test_risk_routing.py -v
../../project_2/.venv/bin/python -B -m unittest discover -s tests -v
../../project_2/.venv/bin/python -B -m src.report --output /tmp/fin439-risk-fix-v1.md
cmp /tmp/fin439-risk-fix-v1.md outputs/version_1_results.md
../../project_2/.venv/bin/python -B -m src.stress_report --as-of 2026-11-21 --output /tmp/fin439-risk-fix-stress.md
cmp /tmp/fin439-risk-fix-stress.md outputs/stress-test-results.md
```

## BoilerPortfolio branding and organization

Reorganized the existing Streamlit app as BoilerPortfolio, an independent FIN 439 student project. The eight-section navigation retains all model workflows. Market Research provides existing historical ETF and economic-signal functions with a separate individual-stock research placeholder. AI Investment Analyst is explicitly in development. The dashboard links to custom scenario exploration, risk review and a dedicated committee page. The native Streamlit theme provides black, white, neutral gray and gold styling without new dependencies.

**62 tests passed, zero failures, zero errors.** The prior 60 tests remain, with navigation labels and coverage updated. Two new tests verify dashboard shortcuts, default reset and development placeholders. The suite exercised both models, and a separate AppTest run traversed all eight sections in both models with the private ETF snapshot installed. No unhandled exceptions were observed. The classroom, classroom stress and both ETF Markdown reports plus the ETF monthly return CSV reproduced byte for byte. The calculation engine, mandate and licensed-data protections were preserved.

```sh
../../project_2/.venv/bin/python -B -m unittest discover -s tests -q
../../project_2/.venv/bin/python -B -m src.report --output /tmp/boilerportfolio-classroom.md
cmp /tmp/boilerportfolio-classroom.md outputs/version_1_results.md
../../project_2/.venv/bin/python -B -m src.stress_report --as-of 2026-11-21 --output /tmp/boilerportfolio-stress.md
cmp /tmp/boilerportfolio-stress.md outputs/stress-test-results.md
```

Native theme settings and chart elements were checked through Streamlit. Browser appearance, contrast under rendering, and narrow-screen layout were not visually verified. The official AI-off record was not modified.

## Market Research Center

Added exact ticker search, curated issuer profiles, optional monthly Alpha Vantage retrieval, and an offline path for the reviewed ETF panel. Charts distinguish unadjusted market closes where supplied from adjusted histories used for growth, risk and drawdown. Comparisons use consecutive matched month-end observations. The active mandate supplies the company cap and allocation floors for explanatory notes. Research and the session watchlist leave the optimizer unchanged.

**70 tests passed, zero failures and zero errors**, including the previous 62 and eight new tests for validation, provider failures, missing credentials, adjusted-return calculations, missing observations, classifications and mandate notes, offline profile behavior and watchlist, and comparison rendering. The saved classroom, stress and private ETF reports and monthly-return CSV all matched byte for byte.

An independent AppTest run with the actual local ETF files displayed the VT/BIL comparison over 60 monthly returns and rendered five chart elements, with DNS calls disallowed and no unhandled exceptions. This used previously acquired observations. No new Alpha Vantage response was received. The session had no API key, and a public demo request failed DNS resolution. Provider response branches were tested with synthetic fixtures. Browser rendering and live entitlement remain unverified.

```sh
../../project_2/.venv/bin/python -B -m unittest discover -s tests -q
../../project_2/.venv/bin/python -B -m src.report --output /tmp/boiler-research-classroom.md
cmp /tmp/boiler-research-classroom.md outputs/version_1_results.md
../../project_2/.venv/bin/python -B -m src.stress_report --as-of 2026-11-21 --output /tmp/boiler-research-stress.md
cmp /tmp/boiler-research-stress.md outputs/stress-test-results.md
```

## Security Search reliability

The existing search read only `ALPHAVANTAGE_API_KEY` and left the provider option disabled by default even when configured. An AppTest regression with the alternate `ALPHA_VANTAGE_API_KEY` and an ordinary AAPL submit recorded zero provider calls before the change. The same test passed after both key names were accepted and online lookup became the default for configured processes. No credential values were printed. Neither key was present in this environment. A terminal demo request failed DNS resolution, and the browser-accessible official demo response contained only a demo-key access notice. No authorized online market history was retrieved.

Added offline demo charts using original, explicitly synthetic paths because public market-history redistribution permission was not established. Adjusted history can remain useful if the unadjusted close is unavailable. Stale successful online results can be refreshed on submit and are labeled if refresh fails. If two histories have no usable common window, the available primary history is displayed on its own with a warning.

**74 tests passed, zero failures and zero errors** in the final suite. The prior 70 remain. Four added tests cover the previously failing first submit with the alternate key, the offline demonstration without network access, retry and labeled cache behavior with canonical key precedence, and preservation of adjusted history with missing unadjusted data. A separate AppTest search loaded actual VT local data through October 30, 2026 and rendered four charts with networking disabled. Classroom and stress reports reproduced byte for byte. The portfolio engine and licensing protections were unchanged. Direct browser and authorized online checks remain open.

```sh
../../project_2/.venv/bin/python -B -m unittest discover -s tests -p test_security_search_regression.py -v
../../project_2/.venv/bin/python -B -m unittest discover -s tests -q
../../project_2/.venv/bin/python -B -m src.report --output /tmp/fin439-searchfix-classroom.md
cmp outputs/version_1_results.md /tmp/fin439-searchfix-classroom.md
../../project_2/.venv/bin/python -B -m src.stress_report --as-of 2026-11-21 --output /tmp/fin439-searchfix-stress.md
cmp outputs/stress-test-results.md /tmp/fin439-searchfix-stress.md
```

## Keyless security research

Reviewed yfinance and Yahoo's applicable data-access terms. The package license does not grant data rights. Yahoo requires prior permission for automated collection. The local app instead uses Market History's documented account-free U.S. stock and ETF bars endpoint. The default path uses the existing Python requirements. Alpha Vantage is optional. Private ETF source precedence, classroom models, mandate, and financial results were preserved.

The keyless path uses raw historical bars and separately labels price-only risk and performance. It does not treat raw prices as a distribution-adjusted history. Successes are cached by source and ticker in the browser session. Failures remain retryable, and new dated requests are spaced by the published limit. No online market data was bundled.

**78 tests passed, zero failures, zero errors**, including the existing 74 and four synthetic keyless tests for date handling, identification, stale/missing provider responses, HTTP status handling, no-key browser routing and cache reuse. All five financial artifacts reproduced byte for byte. The sandbox could not resolve the Yahoo or Market History hosts, and a new temporary environment could not install dependencies from PyPI. No live security request or visual browser result was verified. The README supplies a local five-symbol check and the classroom fallback.

```sh
../../project_2/.venv/bin/python -B -m unittest discover -s tests -q
../../project_2/.venv/bin/python -B -m src.report --output /tmp/boiler-keyless-classroom.md
cmp /tmp/boiler-keyless-classroom.md outputs/version_1_results.md
../../project_2/.venv/bin/python -B -m src.stress_report --as-of 2026-11-21 --output /tmp/boiler-keyless-stress.md
cmp /tmp/boiler-keyless-stress.md outputs/stress-test-results.md
```

## Integrated BoilerPortfolio workflow · November 21, 2026

The classroom case is now the default both with and without a reviewed local ETF panel. The optional ETF model is selected explicitly. Six pages use the shared mandate and, where applicable, the same active mix, model and risk window. The historical and economic research views retain a separate data provenance trail. The last Lab sensitivity evaluated against the active inputs is available in the analyst and committee recommendation record.

**81 tests passed, zero failures, zero errors and zero skips** in 28.244 seconds on CPython 3.14.7. The existing 78 tests remain, with navigation and default-model expectations adjusted to match the six sections. The three new regressions reconcile a 100% Treasury-bill allocation, validate stress replay with manual weights, walk the offline simulator-to-committee decision, and verify that the 36- and 60-month ETF windows use unchanged custom weights in a synthetic reviewed panel. The Treasury-bill calculation is 3.50% gross less 0.15% annual cost = 3.35% net, and 0.50% volatility. It fails the modeled bond and return rules. At 25 bp annual cost, the retained weighted portfolio gives 3.25% net.

An AppTest run with the actual private ETF snapshot traversed all six pages and all four Lab subviews with DNS calls disabled. A separate temporary public-source layout with no optional data and empty provider keys traversed all six pages under the installed course interpreter with DNS calls disabled. These were application-script tests. No new market observations were fetched and no visual browser run was performed.

All five saved financial artifacts compared byte for byte against fresh calculations using the existing inputs, including the private monthly return CSV. This procedure did not write the original reports. The classroom recommendation remains a paper-only PILOT at a 7.00% target and the reviewed ETF model still rejects the same target as infeasible. No licensed observations or derived risk dataset were added to the public project.

```sh
../../project_2/.venv/bin/python -B -m unittest discover -s tests -q
../../project_2/.venv/bin/python -m pip check
python3.14 -m venv /tmp/boilerportfolio-integrated-clean
/tmp/boilerportfolio-integrated-clean/bin/python -m pip install --disable-pip-version-check --retries 0 --timeout 5 -r requirements.txt
../../project_2/.venv/bin/python -B -m streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 8752 --browser.gatherUsageStats false
```

The installed environment passed `pip check`. The fresh temporary virtual environment was created successfully, but pip reported no candidate versions for the first Streamlit pin. The existing pinned versions have public releases. The local server launch reached the socket bind and returned `PermissionError: [Errno 1] Operation not permitted`. A clean dependency install, a browser walkthrough and an independent GitHub cold run remain unverified. The workspace provided no Git metadata. The README records the public setup and local verification steps. An authorized multi-vintage signal replay and the student's official AI-off changed-input record remain separate submission work.

## Final application validation · November 21, 2026

**84 tests passed, zero failures, zero errors and zero skips** in 31.026 seconds on CPython 3.14.7 (macOS arm64). The prior 81 tests were retained. The three new tests cover ordinary question phrasing, unsupported requests, suggestion buttons, transcript clearing, stale-context labels, mandate changes, signal interpretation, and both ETF covariance windows. The existing integrated journey now uses free text to verify that the Analyst reflects the active weights and the latest applicable stress. The initial run revealed that one assertion was reading a sidebar Markdown element instead of a reply. The existing navigation test also timed out at its three-second test-runner limit during concurrent probes. The corrected assertions and final full rerun passed.

A separate AppTest walkthrough traversed all six sections and four Lab subviews in both the classroom and actual local reviewed ETF modes, with DNS calls disallowed. The Analyst reported the respective 7.11% and 6.65% ceilings. Another AppTest walkthrough staged public source files in a temporary directory without the private ETF or ALFRED datasets, with empty provider credentials and DNS calls disallowed. All six pages and the Analyst's free-text answer passed. Both used the installed environment. These checks did not contact either market data provider.

The classroom and stress reports, both private ETF Markdown reports, and the private ETF monthly returns CSV reproduced byte for byte. No dependency pins changed. `pip check` reported no broken requirements. The direct release metadata sets a Python 3.12 floor through NumPy. CPython 3.14 remains the documented project environment and 3.14.7 is the version tested. [NumPy pin](https://pypi.org/project/numpy/2.5.4/) · [Streamlit pin](https://pypi.org/project/streamlit/1.66.0/)

```sh
../../project_2/.venv/bin/python -B -m unittest discover -s tests -q
../../project_2/.venv/bin/python -m pip check
python3.14 -m venv /tmp/boiler-final-clean
/tmp/boiler-final-clean/bin/python -m pip install --disable-pip-version-check --retries 0 --timeout 5 -r requirements.txt
../../project_2/.venv/bin/python -B -m streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 8753 --browser.gatherUsageStats false
```

The fresh virtual environment was created, but pip found no Streamlit candidate in this sandbox. The application server attempt failed at the socket bind with a permission error. A fresh dependency install, visual browser rendering and an independent GitHub cold run remain unverified. The official student AI-off record was not generated or run.

## Official rubric audit · November 21, 2026

The project-local `.venv/bin/python` reported CPython 3.14.7. `pip check` found no broken requirements. The audit reran **84 tests with no failures, errors or skips** in 30.449 seconds using `.venv/bin/python -B -m unittest discover -s tests -v`. All five existing financial artifacts matched the regenerated outputs byte for byte. A separate double-sum volatility and weighted-return calculation confirmed the three classroom results, including 12.09756% volatility for the constrained mix. Direct return-maximizer arithmetic confirmed the classroom 7.11% and ETF 6.65% annual net ceilings. The [official rubric map](../docs/rubric-alignment.md) records the calculations, signal and stress evidence boundaries, and missing submission artifacts.

A new temporary CPython 3.14 environment was created. Even with pip isolated and the public PyPI index specified, the sandbox returned no Streamlit candidates. The installed interpreter verified that the project configuration disables Streamlit usage reporting. No independent GitHub run or browser observation was recorded in this audit.

After the documentation, ignore-rule and Streamlit configuration changes, the complete suite passed again with **84 tests, zero failures, errors or skips**, in 31.471 seconds. The command was `.venv/bin/python -B -m unittest discover -s tests -q`.

## Investment judgment enhancement · November 21, 2026

The final full run used `.venv/bin/python -B -m unittest discover -s tests -q` on the existing project-local interpreter. **90 tests passed, zero failures, errors or skips.** The suite retains the prior 84 tests. Six new tests independently check signed risk attribution against an anti-correlated two-sleeve example and a finite-difference derivative, zero volatility and missing covariance, trading units and expenses, feasibility immediately on both sides of the reverse-stress boundaries, committee vetoes and missing or rejected signals, and scenario changes flowing through the interactive Lab, Analyst and Committee Review.

All five saved financial artifacts were regenerated in memory and matched byte for byte. A separate Streamlit AppTest using the actual private ETF snapshot with DNS blocked confirmed Committee Review and Risk Lab opened and displayed the original-target REJECT and the 36/60-month benchmark volatility comparison. No visual browser run, fresh installation, independent cold run, or official AI-off experiment was performed as part of this change. [Judgment methodology and worked results](../docs/investment-judgment.md)

## Committee-ready presentation · November 21, 2026

The final regression run used `.venv/bin/python -B -m unittest discover -s tests -q`. **93 tests passed, with zero failures, errors or skips.** All 90 earlier test cases were retained. Presentation assertions now locate figures in the screen that owns them. Three new tests reconcile the dashboard and stress findings to active financial inputs, check monitoring and missing-data states, confirm distinct navigation content, assert removal of the old stress narrative, and follow the same infeasible decision through Dashboard, Analyst and Committee Review.

All five previously saved financial artifacts matched regenerated output byte for byte. A separate AppTest traversed all six sections with the actual private ETF inputs and DNS blocked. It verified the 6.65% reference ceiling and 5.81% ceiling under the standard credit/equity shock. No visual browser test or independent GitHub cold run was performed. The official AI-off experiment was not used.

## Submission narrative freeze · November 21, 2026

The credential-free default demonstrates and validates the evaluation process with illustrative holdings. Its paper pilot authorizes testing that process. The separate reviewed ETF view makes the decision on BIL, IEF, LQD and VT explicit. Committee Review and its Markdown export now share one seven-section briefing. The single monitoring table separates current status from actions after a breach. Dated FRED evidence and unavailable live BAA10Y are labeled separately.

The final command was `.venv/bin/python -B -m unittest discover -s tests -q`. **95 tests passed, with zero failures, errors or skips.** The two new tests cover the public report scope and the reviewed ETF shortcut. An additional AppTest with the actual local authorized snapshot and DNS blocked checked that the shortcut changes the ceiling from 7.11% to 6.65%, the Committee Review shows REJECT and $0 live capital, the stress result is visible, and the export control is available. All five saved financial outputs reproduced byte for byte. No visual browser run or independent cold run was performed.

## Student investment-disposition policy correction · November 21, 2026

The student separated portfolio feasibility, investment disposition, and process use. A passing classroom case is ILLUSTRATIVE ONLY. A feasible reviewed alternative is HOLD pending robustness, suitability, and implementation review. A failed or infeasible modeled proposal is REJECT. Paper-testing the evaluation process is separate. Live deployment is zero.

The final run of `.venv/bin/python -B -m unittest discover -s tests -q` passed all **95 tests, with zero failures, errors or skips**. Recommendation assertions now verify the new policy rather than the superseded automatic PILOT. A separate AppTest with DNS blocked verified the documented-only public ETF disclosure and the 6.65% authorized local result, REJECT and $0 briefing. All five saved financial artifacts reproduced byte for byte. No visual browser test, independent GitHub cold run, or official AI-off experiment was performed.

## Stress findings first · November 21, 2026

Classroom, custom and reviewed ETF stress views now put calculated changes and committee responses before collapsed calculation tables. The presentation distinguishes a sensitivity with little decision significance from a held allocation that fails and an infeasible successor. Volatility changes are reported in percentage points, with relative context when return and feasibility stay unchanged. The financial calculations and decision policy are unchanged.

`.venv/bin/python -B -m unittest discover -s tests -q` passed **96 tests with zero failures, errors or skips**. The new regression reconciles the correlation, higher-cost and equity deterioration findings with their modeled consequences. An offline AppTest with the actual private ETF snapshot checked the adverse finding (5.81% ceiling, down 83.8 bp) and the unchanged zero-shock finding. All five saved financial artifacts reproduced byte for byte. No visual browser test was performed.

## Five-page presentation and model separation · November 21, 2026

The existing application was reorganized into Investment Overview, Portfolio Builder (including Research and data), Risk & Scenario Analysis, Committee Decision and Investment Assistant. An authorized reviewed snapshot is the first model in a new session. The public workspace starts in Training and validation, with the prior ETF decision in a separately labeled disclosure. The explicit model choice persists across navigation. Hypothetical controls are available on the Builder, and the original Lab 13 inputs remain available.

The final `.venv/bin/python -B -m unittest discover -s tests -q` run passed all **96 tests, with zero failures, errors or skips**. Existing UI assertions were relocated to the new pages and views. A separate AppTest with the actual authorized local snapshot and DNS blocked confirmed ETF-first startup, all five routes, and an explicit switch to training that persisted across navigation. All five saved financial artifacts matched generated output byte for byte. No visual browser verification, independent cold run, or official AI-off experiment was performed.

## Final chart and ETF stress coverage correction · November 21, 2026

Return ceiling charts now share horizontal bands, short labels and a labeled required-return marker. The Portfolio Builder retains a labeled horizontal required-return marker even when it lies outside the modeled return points. Comparison tables and the committee export show a constrained row when the solver finds no feasible solution. ETF stress coverage was audited from the code without running any new financial scenario. The ETF UI supports the LQD/VT return shock, 36/60-month windows, and manual modeled bond/reserve changes. ETF costs remain fixed at 15 bp and the ETF interface does not run recurring-cost or transaction-cost stress. Fund eligibility and five-day redemption remain evidence gates.

The final `.venv/bin/python -B -m unittest discover -s tests -q` run passed **98 tests, with zero failures, errors or skips**. Two new regression tests check the chart specifications. All five existing saved financial artifacts reproduced byte for byte. Browser rendering was not visually verified, and the official AI-off record was not used.

## Reviewed ETF recurring-cost control · November 21, 2026

Portfolio Builder now accepts a hypothetical recurring ETF investor fee in Custom scenario. The existing engine receives that fee for the active analysis, candidate evaluation, frontier, and ETF stress calculations. The existing custom bond and reserve controls remain available. Reset restores the original Lab 13 settings and the 15 bp default fee.

The final suite passed **100 tests, with zero failures, errors or skips**. The two added tests stub the solver for changed fees. They check input routing, navigation persistence and reset without computing any new financial outcome. All five existing financial artifacts matched byte for byte. ETF transaction costs and instrument-level eligibility remain outside the modeled stress controls. No official AI-off experiment was executed.

## Consolidated portfolio allocation comparison · November 21, 2026

The allocation chart now uses explicit horizontal segment start and end positions, fixed bar thickness, and one band per portfolio. Both units use the same holdings and an explicit full legend. The comparison table reports modeled margin, failed rules, and the largest contribution to annual volatility. Hover shows each holding's signed contribution. An infeasible constrained allocation has a status row and no chart bar.

The final `.venv/bin/python -B -m unittest discover -s tests -q` run passed **102 tests, with zero failures, errors or skips**. Two new tests verify geometry, both units, legend coverage, risk reconciliation, and the blank infeasibility row. Existing dollar checks now read the chart's serialized data. All five saved financial artifacts matched byte for byte. A Streamlit launch attempt was blocked at the local socket bind, so no visual browser verification was performed. The official Locked Changed-Input Record was not run.
