# Video 1 — Research Evolution

I used OpenAI ChatGPT and Codex to assist with planning, coding, testing, and documentation.

The analysis and decision are mine. This project is for educational use only and does not constitute investment advice.

**Maximum** 3:00 · **Target finish** 2:45

## 0:00–0:15

> **SHOW ON SCREEN**  
> Show the BoilerPortfolio title and keep your webcam visible. Read both disclosures above before starting the walkthrough.

**SAY**

Read both opening disclosures verbatim.

## 0:15–0:54

> **SHOW ON SCREEN**  
> Show the client mandate in README.md. Then show the four fund roles in Portfolio Builder → Research and data → Fund comparison.

**SAY**

The question I wanted to answer was simple: could I put this client's five million dollars to work and still meet their rules? They're 45, have 15 years until retirement, and need seven percent a year after costs. The original mandate calls for at least 25 percent in investment-grade bonds and 10 percent in reserves. It also sets an eight percent company cap, with exemptions, and requires 90 percent redeemable within five business days. The client's loss limit is still open.

## 0:54–1:32

> **SHOW ON SCREEN**  
> Show the fund roles, then switch to Portfolio Builder → Allocation and point to both baselines.

**SAY**

I gave each ETF a job. BIL is the reserve sleeve, IEF gives me Treasury duration, LQD adds corporate credit, and VT provides global equity exposure. Those are modeled roles that still need to be checked against the mandate. I started with equal weight and a 60 percent VT, 40 percent LQD benchmark. The benchmark helps me see the trade-off. It's a useful comparison, but it holds no reserve, so I couldn't recommend it for this client.

## 1:32–2:08

> **SHOW ON SCREEN**  
> Show the dated evidence in outputs/signal-decision-evidence.md and its data card. Keep private price files and tables off screen.

**SAY**

I used 60 months of ETF returns to estimate how the funds move together. For expected returns, I used separate forward assumptions. I also asked what I could actually have known on November 21. The dated FRED table showed Baa spreads had widened 12 basis points over 20 observation steps. That gave me a reason to look harder at LQD credit risk and VT downside. It didn't give me enough evidence to change the weights.

## 2:08–2:45

> **SHOW ON SCREEN**  
> Show the README's documented original ETF finding. End on the decision and public/private reproduction note.

**SAY**

The classroom example showed me the optimizer could find a mix at seven percent under illustrative inputs. With these four ETFs, the best net return at the original bond floor was 6.65 percent. That changed my recommendation. I'd reject the allocation and authorize zero dollars. I'd still test the review process on paper. A public checkout can reproduce the classroom case. Reproducing the ETF result takes authorized data.
