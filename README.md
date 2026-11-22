# BoilerPortfolio

I used OpenAI ChatGPT and Codex to assist with planning, coding, testing, and documentation.

The analysis and decision are mine. This project is for educational use only and does not constitute investment advice.

BoilerPortfolio is an independent FIN 439 investment decision-support application. It evaluates whether a proposed allocation meets an investor’s objective and mandate, how sensitive it is to assumptions, and what evidence a committee needs before authorizing capital.


## Open BoilerPortfolio

**Live application:** https://boilerportfolio-fin439.streamlit.app/

**Source code:** [GitHub repository](https://github.com/alinam06/FIN439-Project2)

The public application opens in Training and validation mode.
The reviewed ETF analysis requires authorized historical market data,
which are not included in the public repository.


## Investment recommendation

**Reject deployment of BIL, IEF, LQD, and VT under the reviewed ETF assumptions. Authorize $0 in live capital.**

The public checkout can reproduce the classroom analysis and displays the previously documented ETF decision separately. Reproducing the ETF result requires an authorized local snapshot. Licensed inputs and private derived reports are excluded from the public repository. [ETF evidence status](outputs/etf-analysis-status.md)

### Key investment findings

| Finding | Reviewed ETF result | Investment significance |
| --- | --- | --- |
| Maximum feasible net return | **6.65% annually** | No modeled allocation satisfies both the return objective and the enforceable limits. |
| Return shortfall | **35 bp** below the **7.00%** objective | Eliminating the **15 bp** recurring investor fee would raise the ceiling to **6.80%**, still **20 bp short** with other assumptions fixed. |
| Adverse ETF return scenario | A **1 percentage point** reduction in the forward returns of both LQD and VT lowers the ceiling to **5.81%** | Weaker credit and equity assumptions deepen an already infeasible proposal. |
| Benchmark volatility, 36 vs 60 months | The same benchmark weights have higher estimated volatility in the 60-month window. Numerical estimates remain in the private report. | The window changes estimated risk. The return ceiling stays fixed when forward returns, costs and constraints are unchanged. |
| Proposed live allocation | **$0** | Paper-test the evaluation process. Reconsider deployment only if defensible assumptions or a separately approved universe change support a robust, suitable allocation. |

## Client mandate and investment universe

The fictional Lab 13 client is **45**, plans to retire at **60**, and has **$5 million** to invest over **15 years**. The annual net return objective is **7.00%**.

- **Portfolio rules:** Fully invested, long-only, with no borrowing, short selling or derivatives. Annual rebalancing.
- **Allocation limits:** At least **25%** investment-grade bonds and **10%** cash or highly liquid government securities. A single nonexempt company may account for up to **8%**. Diversified funds and U.S. Treasuries are exempt.
- **Benchmark and risk measure:** **60% VT / 40% LQD** for the reviewed ETF model. Risk is measured as annualized standard deviation of portfolio returns.
- **Implementation gates:** At least **90%** must be redeemable within five business days. Instrument eligibility, look-through exposure, redemption evidence and the client’s annual loss tolerance remain unresolved.

| ETF | Portfolio role |
| --- | --- |
| **BIL** | Short-term Treasury bills. Provisionally counts toward liquid reserves. |
| **IEF** | Intermediate U.S. Treasuries. Provisionally counts toward the bond floor. |
| **LQD** | Investment-grade U.S. corporate bonds. Provisionally counts toward the bond floor. |
| **VT** | Global equity exposure. |

## Run locally

Use CPython **3.14**. Validation used **3.14.7 on macOS arm64**. Run from the folder containing `app.py`. Package installation requires internet access. The public application runs offline afterward without credentials.

**macOS or Linux**

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

**Windows PowerShell**

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the URL Streamlit prints. See [launch troubleshooting](docs/rubric-alignment.md#launch-troubleshooting) for port and environment issues.

## Application workflow

| Page | Use |
| --- | --- |
| **Investment Overview** | Review the active model, decision, required return, feasible ceiling, margin and live capital. |
| **Portfolio Builder** | Compare equal weight, the benchmark and the constrained result. Toggle weight and dollar allocations, inspect risk contributions and run a hypothetical **Custom scenario**. **Research and data** contains fund and source evidence. |
| **Risk & Scenario Analysis** | Compare held and reoptimized outcomes. Review return shocks, estimation windows, costs and modeled limits under the applicable model. |
| **Committee Decision** | Review feasibility, approval gates and monitoring conditions. Download the active briefing as Markdown. |
| **Investment Assistant** | Ask focused questions about the active analysis. Answers use deterministic rules and calculated results offline. |

## Financial methodology

**Training and validation** is the credential-free public default. Its illustrative sleeves test the allocation process. The **7.11%** modeled ceiling and **7.00%** candidate at **12.10%** volatility are classroom results, with **$0 live authorization**. [Classroom results](outputs/version_1_results.md)

**Reviewed ETF snapshot** opens when the authorized panel is available.

- **Return and risk.** Expected net return is the weighted arithmetic forward return less the default **15 bp** annual investor cost. The ETF forward assumptions already reflect embedded fund expenses and are separate from historical sample means. Portfolio volatility is calculated from the covariance matrix. The ETF estimate annualizes sample covariance from monthly adjusted returns by multiplying by 12.
- **Portfolio comparison.** Compare equal weight and **60% VT / 40% LQD** with the constrained minimum-volatility candidate at the net return target. The reviewed ETF solve applies the modeled bond and reserve limits. Issuer treatment and five-day redemption require separate evidence. The classroom Treasury note can count toward both modeled minimums.
- **Stress and decision.** Reviewed ETF controls support an LQD/VT forward-return shock, **36- and 60-month** risk windows, and hypothetical investor fees and bond/reserve floors in Portfolio Builder. ETF-specific transaction-cost stress is unavailable. The classroom model separately supports one-time cost scenarios on gross trading. A failed or infeasible proposal is **REJECT**. A feasible reviewed alternative is **HOLD** pending suitability and implementation review.
- **Historical evidence.** Reconstructed ETF performance uses fixed weights rebalanced monthly and adjusted-price returns before investor fees, taxes and trading costs. On **November 21, 2026**, the [dated BAA10Y review](outputs/signal-decision-evidence.md) recorded **+12 bp** over **20 numeric observation steps**. This prompted a review of LQD credit-spread exposure and VT equity downside, with weights unchanged. Live BAA10Y is unavailable.

[ETF methodology](docs/data-methodology.md) · [Stress methodology and replay](docs/stress-testing-methodology.md) · [Investment judgment](docs/investment-judgment.md) · [Signal data card](docs/signal-data-card.md)

### Optional authorized data and online research

| Local files | Purpose |
| --- | --- |
| `data/etf-prices.csv` and `data/etf-metadata.json` | Reviewed monthly adjusted ETF closes and provenance. A reviewed pair enables the private ETF analysis. |
| `data/baa10y-archive.json` and `data/baa10y-manifest.json` | Authorized ALFRED vintages and provenance for date-level signal review. |

Redistribution rights for raw ETF histories and derived covariance evidence were not established. Keep licensed inputs, private outputs and credentials out of the public repository. See [private preparation, reproduction and session uploads](data/README.md) and [historical-window permissions](docs/rubric-alignment.md#historical-window-reproduction-and-permissions).

## Validation

From the project folder:

```sh
.venv/bin/python -m pip check
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m src.report --output outputs/reproduced.md
.venv/bin/python -m src.stress_report --as-of 2026-11-21
```

On Windows, substitute `.\.venv\Scripts\python.exe` for `.venv/bin/python`.

The recorded suite passed **102 tests**, and all five saved financial artifacts reproduced byte for byte. The public outputs are the [classroom results](outputs/version_1_results.md) and [classroom stress results](outputs/stress-test-results.md). Independent GitHub cold-run and visual browser evidence remain open. The official AI-off Locked Changed-Input Record is separate from these checks. [Executed validation evidence](outputs/validation-summary.md)

## Project deliverables

The [rubric alignment and submission checklist](docs/rubric-alignment.md#github-submission-checklist) records the available evidence and remaining submission items. The decision memo, validation and AI-use document, official Locked Changed-Input Record, submission manifest and video transcripts are not present in this checkout.
