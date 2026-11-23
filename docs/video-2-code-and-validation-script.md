# Video 2 — Code and Validation

I used OpenAI ChatGPT and Codex to assist with planning, coding, testing, and documentation.

The analysis and decision are mine. This project is for educational use only and does not constitute investment advice.

**Maximum** 5:00 · **Target finish** 4:35

## 0:00–0:15

> **SHOW ON SCREEN**  
> Show the README and your webcam. Read both disclosures above.

**SAY**

Read both opening disclosures verbatim.

## 0:15–0:52

> **SHOW ON SCREEN**  
> Show README.md. In a prepared public checkout, show the launch command and open the URL Streamlit prints. Use the commands in the script notes.

**SAY**

Here's what someone gets from the public checkout. I create a Python 3.14 environment, install the requirements, and run Streamlit. The app opens in training mode without an API key. If I want to reproduce the ETF risk results, I need the authorized price file and its matching metadata. I'll keep those two models separate as I walk through the code.

## 0:52–1:46

> **SHOW ON SCREEN**  
> Open src/portfolio.py at portfolio_metrics, minimum_variance and analyze. Then open src/etf_portfolio.py at modeled_floors and fit_window. In Portfolio Builder → Allocation, with Reviewed ETF snapshot selected if authorized, show the comparison.

**SAY**

This function takes the assumed return on each holding, weights it by the allocation, and subtracts the annual investor fee. For risk, I use covariance because the way the funds move together matters just as much as the risk of each fund on its own. The optimizer asks which mix has the lowest volatility among those that meet the modeled rules and return target. I calculate the ceiling separately. If even the best possible return comes up short, I have no target-meeting mix to show. Equal weight and the 60/40 benchmark give me two references, even when they fail a client rule.

## 1:46–2:22

> **SHOW ON SCREEN**  
> Show src/economic_signal.py at eligible_vintages and evaluate_signal, then outputs/signal-decision-evidence.md.

**SAY**

The key question here is when I could have seen the number. An observation may be dated earlier than the day it became available. The vintage filter checks availability before letting it into the decision. My November 21 FRED snapshot showed a 12 basis point widening. I used it to flag credit and equity risk for review. Tests cover the revision logic using synthetic records. The snapshot alone can't tell me what was available on earlier dates.

## 2:22–3:10

> **SHOW ON SCREEN**  
> Show Risk & Scenario Analysis → Lab analysis → Stress testing and Risk and allocation comparison. In Portfolio Builder → Allocation point to the custom mandate and recurring fee controls. Show tests/test_lab14.py and outputs/validation-summary.md.

**SAY**

I used stress tests to see what could change the outcome. A different covariance window can change estimated volatility. Changing expected returns, recurring fees, or allocation floors can change whether the target is reachable. The classroom model also has a separate one-time trading cost test. For a check with a known answer, I used Lab 14. The benchmark comes back at 6.80 percent return and 10.46 percent volatility on those classroom inputs. The saved validation run records 102 passing tests.

## 3:10–4:35

> **SHOW ON SCREEN**  
> Show the [pre-run prediction commit](https://github.com/alinam06/FIN439-Project2/commit/61df82697e03946f6181c8537a712310f122650e) first. Point to the prediction and the recorded 11:12 a.m. Eastern commit time on November 22, 2026. Then open the [post-run results commit](https://github.com/alinam06/FIN439-Project2/commit/2d7831df74e5f8ae41fbccf7048c9ea5c3f78167) and show the 11:23 a.m. Eastern run and reconciliation. Show the Investment Overview screenshot only if cleared for sharing.

**SAY**

For my locked experiment, I changed one thing: the bond floor went from 25 to 35 percent. I held the same four funds, forward returns, 60-month window, reserve floor, fee, and target. My reasoning was that you'd have to move ten percentage points from VT into lower-returning LQD at the return ceiling. Their assumed returns are three percentage points apart, so I expected the portfolio ceiling to drop 30 basis points, from 6.65 to 6.35 percent. I committed that prediction at 11:12 Eastern and ran the experiment at 11:23. The result matched the direction and size of my prediction at the precision shown. I was now 65 basis points short of seven percent. The gap got bigger, but the decision was the same: REJECT, with zero dollars live.

## Screen reference commands

Use macOS commands below from a public checkout. On Windows use the README's PowerShell commands. The test command is an optional separately prepared screen reference. Allow for test runtime outside the narration.

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
.venv/bin/python -m unittest discover -s tests -v
```

See [executed validation](../outputs/validation-summary.md) and [Lab 14 fixtures](../tests/test_lab14.py). The Locked Record narration uses the student-supplied record. Confirm both GitHub links from a signed-out browser before recording.
