# FIN 439 Project 2 — Locked Changed-Input Record

## 1. Experiment identification

**Student:** Alina Mato

**Project:** BoilerPortfolio — Investment Management Application

**Date and time of independent prediction:** 2026-11-22, 10:30 Eastern Time

**AI use during prediction:** None. I completed the prediction and financial reasoning independently, before executing the changed-input experiment.

**Application model:** Reviewed ETF snapshot

**Investment universe:** BIL, IEF, LQD, VT

**Client objective:** 7.00% annual net return

**Portfolio value:** $5,000,000

## 2. Original model and changed input

The purpose of this experiment is to evaluate how tightening an investment constraint affects the portfolio's maximum feasible expected return and its ability to satisfy the client's mandate.

| Model input | Original value | Experimental value |
|---|---:|---:|
| Minimum investment-grade bond allocation | 25% | 35% |
| Required annual net return | 7.00% | 7.00% |
| Minimum liquid reserve | 10% | 10% |
| Annual recurring investor cost | 15 basis points | 15 basis points |
| Historical covariance window | 60 months | 60 months |
| Investment universe | BIL, IEF, LQD, VT | Unchanged |
| Forward-return assumptions | Existing reviewed ETF assumptions | Unchanged |

**Original financial result:** The evaluated ETF universe has a maximum modeled annual net return of 6.65%, which is 35 basis points below the client's required return. The model reports no feasible constrained portfolio at the original target.

**Location of experimental control:** Portfolio Builder → Allocation → Custom scenario → Mandate limits → Minimum investment-grade bonds (%).

## 3. LOCKED INDEPENDENT PREDICTION — COMPLETE BEFORE RUNNING

**Predicted maximum feasible annual net return:**

6.35%

**Predicted change from the original 6.65% ceiling:**

-30 bp

**My financial reasoning:**

To maximize expected return under the original constraints, the optimizer must hold the minimum 10% liquid reserve in BIL and the minimum 25% investment-grade bond floor in the highest-yielding 
bond ETF (LQD rather than IEF), leaving 65% for global equities (VT). Raising the minimum investment-grade bond floor from 25% to 35% forces a direct 10% reallocation out of VT and into lower-yielding 
LQD (or IEF), because the 10% BIL reserve is locked. Since investment-grade bonds carry materially lower forward return assumptions than equities—typically by 250 to 350 basis points—shifting 10% of 
the portfolio weight across that return spread reduces the maximum portfolio return ceiling by roughly 25 to 35 basis points. Meanwhile, the fixed 15 bps annual recurring investor cost continues to drag 
net performance identically across both scenarios.

**Predicted effect on portfolio construction:**

The tightened constraint shrinks the feasible allocation space and lowers the maximum-return corner portfolio from 10% BIL / 25% IG Bonds / 65% VT to 10% BIL / 35% IG Bonds / 55% VT. Because the 
portfolio already failed to reach the 7.00% net return target at the 6.65% ceiling, tightening a binding minimum constraint on a lower-returning asset class strictly reduces the upper bound of 
achievable return. Consequently, the model will continue to report no feasible constrained portfolio at the 7.00% target.

**Predicted committee decision:**

REJECT

**Why I predict that decision:**

The original proposal was already unviable because the reviewed ETF universe fell 35 basis points short of the client's 7.00% net return objective. Increasing the minimum investment-grade bond 
allocation worsens that exact deficit by pushing the maximum achievable net return even further below the hurdle rate, confirming that the mandate's return target and risk/asset-class constraints 
cannot be reconciled within this four-ETF universe.

**Other assumptions held constant:**

Only the minimum investment-grade bond allocation is changed. The investment universe, forward-return assumptions, historical window, net-return objective, recurring fees, reserve requirement and all other modeled restrictions remain unchanged.

## 4. PRE-RUN LOCK

**Prediction GitHub commit:** (https://github.com/alinam06/FIN439-Project2/commit/61df82697e03946f6181c8537a712310f122650e)

**Commit date and time:** 11:12 Eastern Time

I finalized and committed Section 3 before executing the changed-input experiment.

---

## 5. ACTUAL EXPERIMENT RESULTS — COMPLETE ONLY AFTER THE PREDICTION IS COMMITTED

**Experiment date and time:** [2026-11-22, 11:23 Eastern Time]

**Changed input actually applied:** Minimum investment-grade bonds increased from 25% to 35%.

**Actual maximum feasible annual net return:** 6.35%

**Actual change from baseline:** -30 bp

**Actual shortfall or headroom relative to the 7.00% objective:** 65 bp

**Did the optimizer produce a feasible allocation at the original target?** No

**Observed allocation or constraint effects:** ncreasing the minimum investment-grade bond allocation reduced the maximum feasible expected annual net return. The investment proposal remained infeasible under the client's original 7% objective.

**Actual committee decision:** REJECT

**Result evidence:** Investment Overview screenshot showing the custom scenario and 6.35% return ceiling.
<img width="732" height="669" alt="Screenshot 2026-11-22 at 11 26 09 AM" src="https://github.com/user-attachments/assets/a37b0464-e7ea-4649-b022-a46587a80473" />

## 6. Prediction-versus-actual reconciliation

| Question | My finding |
|---|---|
| Was my predicted direction correct? | Yes |
| How close was my numerical prediction? | It was accurate. |
| Did the decision change as predicted? | It was still reject. |
| What did I learn about the optimizer or mandate? | I learned that the optimizer cannot always find a feasible portfolio, even when assumptions improve. Meeting the mandate's constraints is more important than simply maximizing returns. |

**Final interpretation:**

The experiment showed that although the model responded to the changed assumptions as predicted, the investment proposal still failed to meet the client's mandate. The portfolio's expected return remained below the required target, so the investment decision stayed **REJECT**. This demonstrates that improving one financial assumption does not necessarily make a portfolio feasible when multiple constraints must be satisfied. The results also increased my confidence in the model because the actual changes closely matched my numerical prediction, suggesting the optimizer responded consistently to the inputs.

## 7. Evidence and chronology

**Pre-run prediction commit URL: https://github.com/alinam06/FIN439-Project2/commit/61df82697e03946f6181c8537a712310f122650e

**Post-run results commit URL: https://github.com/alinam06/FIN439-
Project2/commit/2d7831df74e5f8ae41fbccf7048c9ea5c3f78167

**Experiment evidence location:** Located in my Github repository.

The pre-run commit preserves the original prediction. The subsequent commit adds the actual results and reconciliation without modifying the original prediction.
