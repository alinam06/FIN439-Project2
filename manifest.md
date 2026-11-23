# FIN 439 Project 2 — Submission Manifest

**Project:** BoilerPortfolio — Investment Management Application

**Student:** Alina Mato

**GitHub Repository:** [FIN439-Project2](https://github.com/alinam06/FIN439-Project2)

**Live Application:** [Launch BoilerPortfolio](https://boilerportfolio-fin439.streamlit.app/)

**Submission Snapshot Commit:** [View GitHub Commit](https://github.com/alinam06/FIN439-Project2/commit/87d5409f034a48b84a837feee2600d5f605eee7d)

## 1. Investment Recommendation

**Decision: REJECT — $0 live capital authorization.**

BoilerPortfolio evaluates whether an investment portfolio can satisfy a client's return objective, risk requirements, and investment constraints.

Under the original client mandate, the reviewed BIL, IEF, LQD, and VT universe produces a maximum modeled annual net return of **6.65%**, below the client's **7.00%** objective.

A hypothetical increase in the minimum investment-grade bond requirement from 25% to 35% reduces the return ceiling to **6.35%**, further supporting the decision not to deploy capital.

The public application operates in Training and validation mode. Reproducing the reviewed ETF analysis requires separately authorized historical data.

## 2. Application and Source Code

- [Application entry point](app.py)
- [README and installation instructions](README.md)
- [Python dependencies](requirements.txt)
- [Financial calculation and application modules](src/)
- [Automated validation tests](tests/)

## 3. Investment Analysis and Documentation

- [Final Investment Decision Memo](docs/decision-memo.md)
- [Validation and AI-Use Documentation](docs/validation-and-ai-use.md)
- [Investment Judgment Evidence](docs/investment-judgment.md)
- [Historical ETF Data Methodology](docs/data-methodology.md)
- [Stress-Testing Methodology](docs/stress-testing-methodology.md)
- [Economic Signal Data Card](docs/signal-data-card.md)
- [Rubric Alignment](docs/rubric-alignment.md)

## 4. Validation and Supporting Evidence

- [Locked Changed-Input Record](docs/locked-changed-input-record.md)
- [Automated Validation Results](outputs/validation-summary.md)
- [Public Financial Results](outputs/version_1_results.md)
- [Stress-Test Results](outputs/stress-test-results.md)
- [Dated FRED Signal Evidence](outputs/signal-decision-evidence.md)
- [ETF Evidence Availability](outputs/etf-analysis-status.md)

### Locked Changed-Input Chronology

**Pre-run prediction — November 22, 2026:**

[View Pre-run Prediction Commit](https://github.com/alinam06/FIN439-Project2/commit/61df82697e03946f6181c8537a712310f122650e)

**Post-run results and reconciliation — November 22, 2026:**

[View Post-run Results Commit](https://github.com/alinam06/FIN439-Project2/commit/2d7831df74e5f8ae41fbccf7048c9ea5c3f78167)

The experiment increased the hypothetical minimum investment-grade bond allocation from 25% to 35%. The predicted and observed modeled return ceiling declined from 6.65% to 6.35%, with the investment decision remaining REJECT.

The experiment did not change the client's original mandate.

## 5. Video Presentations

| Video | YouTube Recording | Transcript |
|---|---|---|
| Video 1 — Research Evolution | [Watch Video 1](https://youtu.be/iqptnKfU2So) | [Transcript](docs/transcript-video-1.txt) |
| Video 2 — Code and Validation | [Watch Video 2](https://youtu.be/iytTkM8ILd0) | [Transcript](docs/transcript-video-2.txt) |
| Video 3 — Committee Decision | [Watch Video 3](https://youtu.be/ti_W3A70xTc) | [Transcript](docs/transcript-video-3.txt) |

The three videos document the research process, code and validation, and final investment committee recommendation.
The three videos document the research process, code and validation, and final investment committee recommendation. The linked scripts serve as transcripts to the extent that they match the actual recordings.

## 6. AI Use and Educational Disclosure

I used OpenAI ChatGPT and Codex to assist with planning, coding, testing, and documentation.

The analysis and decision are mine. This project is for educational use only and does not constitute investment advice.

Additional details are documented in the [Validation and AI-Use Documentation](docs/validation-and-ai-use.md).

## 7. Reproducibility and Data Access

The public GitHub repository contains the application code, training-mode financial model, methodology documentation, and authorized public evidence.

The live Streamlit deployment allows reviewers to interact with BoilerPortfolio without installing Python or providing credentials.

The public classroom model is illustrative and does not constitute an investable portfolio recommendation.

The reviewed ETF investment analysis uses a November 21, 2026 local historical data snapshot. The underlying Alpha Vantage price histories, prepared datasets, and private derived reports are not publicly distributed because redistribution permission has not been established.

The reviewed ETF conclusions are documented in the decision memo, validation evidence, and video presentations. Independent numerical reproduction of those ETF calculations requires authorized source data.

An independent fresh-checkout installation test has not been verified.

**Final committee request:** Reject the evaluated ETF allocation, authorize $0 in live capital, and continue paper testing and investment research before reconsideration.
