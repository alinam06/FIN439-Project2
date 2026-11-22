# Historical ETF data methodology

**Status:** The November 21, 2026 Alpha Vantage snapshot was reviewed for BIL, IEF, LQD and VT. It contains 61 aligned monthly adjusted closes per fund from October 2021 through October 2026, yielding 60 monthly returns. The application can evaluate the reviewed ETF snapshot locally using authorized inputs. A public checkout runs the illustrative classroom model and can show the documented ETF conclusion. Independent reproduction of the ETF analysis requires authorized access to the original inputs. Redistribution rights, earlier price vintages, full issuer distribution reconciliation and mandate eligibility remain unresolved. [ETF evidence status](../outputs/etf-analysis-status.md) · [Private reproduction](../data/README.md#reproduce-the-authorized-etf-capture)

## Reviewed universe and sources

| Fund | Intended exposure | Evidence to review |
| --- | --- | --- |
| BIL | U.S. Treasury bills with one to three months to maturity | Assess reserve eligibility under the client's policy for fund wrappers, duration and access to cash. [State Street BIL](https://www.ssga.com/us/en/individual/etfs/state-street-spdr-bloomberg-1-3-month-t-bill-etf-bil) |
| IEF | U.S. Treasury bonds with seven to ten years to maturity | Assess bond-floor eligibility and interest-rate risk. Reserve eligibility needs explicit policy review. [iShares IEF](https://www.ishares.com/us/products/239456/ishares-7-10-year-treasury-bond-etf-ief) |
| LQD | U.S. dollar investment-grade corporate bonds | Check holdings, ratings methodology, unrated assets, downgrades, cash and permitted non-IG exposure before attributing eligible weight. [iShares LQD](https://www.ishares.com/us/products/239566/ishares-iboxx-investment-grade-corporate-bond-etf-lqd) |
| VT | Global equity | Confirm diversification, holdings and fund structure for any company-cap exemption. [Vanguard VT](https://investor.vanguard.com/investment-products/etfs/profile/vt) |

The reviewed price source is Alpha Vantage's `TIME_SERIES_MONTHLY_ADJUSTED` endpoint. It documents the last trading day, unadjusted close, adjusted close, volume and a dividend field. For future captures, confirm all four U.S. listings, USD currency, symbol and identifier mappings, adjustment coverage, access and rate limits, retention and redistribution terms, and the ability to archive snapshots. Keep credentials outside code, logs and manifests. A current response may contain revised history and a partial latest month. The endpoint documentation does not establish the publication time or vintage history of each observation. [Alpha Vantage API documentation](https://www.alphavantage.co/documentation/), [adjustment policy](https://www.alphavantage.co/support/api-key/)

Use issuer distribution histories and notices to reconcile ex-dates, amounts, splits and unusual distributions. Use sponsor total-return tables to investigate material differences on overlapping periods, logging differences among exchange close, issuer market-price convention, NAV, and reinvestment conventions. Treat filings and dated sponsor records as eligibility evidence. If vendor data fail coverage or adjustment checks, document the failure and select one comparable, licensed alternative for all four funds. Preserve the old snapshot and rerun the checks. Avoid stitching series across providers.

## Five-year USD return panel

For future captures, apply the following collection protocol. Completed checks for the November snapshot are listed under [Actual ETF evidence](#actual-etf-evidence).

1. Record the decision timestamp in UTC and its America/New_York trading-time equivalent. Define the terminal month as the latest full calendar month ended by that timestamp whose final trading session and required observations were available before the cutoff. Use the official U.S. listing calendar, including early closes and holidays. Exclude a vendor's partial current month.
2. Collect 61 consecutive month-end adjusted exchange closes spanning 60 monthly intervals for each fund. Store the calendar month and the actual last trading session date separately. For all funds retain the same monthly interval and confirm that closes correspond to the expected exchange sessions. Record UTC download time, provider, endpoint and parameters with secrets removed, fields, ticker, permanent identifier, listing and currency, and raw payload hash. Preserve raw close and dividend fields for reconciliation.
3. Compute the monthly simple USD total return as `r[t] = adjusted_close[t] / adjusted_close[t-1] - 1`. Confirm that adjustments capture splits and reinvestment of covered cash distributions. Apply an adjusted price series consistently and use distributions only for reconciliation to avoid double counting. Investigate special distributions, capital gains and returns of capital against dated issuer records. Report the return convention and any uncovered events. Shareholder taxes are excluded. VT's USD series already reflects foreign exchange effects on the fund.
4. Reject nonfinite or nonpositive prices, unexpected dates, stale values, identifier mismatches and conflicting duplicates pending review. Deduplicate exact records with an audit entry. Compute each return only between consecutive valid calendar months, then align the four return series by month. Forward fills, interpolation and gap-spanning monthly returns are prohibited. Publish the missing fund/date list and common sample size. The standard five-year report requires 60 contiguous common returns. Any approved shorter exploratory window needs its own date range, sample count and label. It cannot silently substitute for the five-year panel.

## Risk, return and costs

- Report realized annualized geometric total return as `prod(1 + r[t])^(12 / n) - 1`, with `n = 60` in the standard panel. Report `12 × mean(r)` separately if showing an annualized arithmetic statistic. The realized five-year rate and the arithmetic statistic are descriptive. The reviewed optimizer uses separate forward-looking arithmetic return assumptions, less annual investor costs. Historical returns are descriptive.
- Annualized sample volatility is `sqrt(12) × monthly sample SD` using `n - 1`. Estimate Pearson correlation and sample covariance on the same complete panel, with annual covariance equal to monthly covariance times 12. These scaling conventions abstract from serial dependence. Report dates and observation count. The ETF fit checks the covariance eigenvalues and stops for singular or ill-conditioned matrices. Reporting full rank and conditioning diagnostics is a proposed extension to the evidence protocol. Investigate outliers and regime dependence. For singular or unstable matrices, stop before optimization until an explicit estimator or regularization method has been reviewed, with original inputs and sensitivity recorded.
- Fund expenses are generally reflected in market-price and distribution performance. Document the relevant share class and expense schedule, and avoid deducting the expense ratio again from historical fund performance. Separately estimate investor-level advisory fees, commissions, half-spreads and order-size market impact on the buys and sells actually assumed in a future analysis. Use initial and annual rebalance trades as applicable, apply costs per traded notional with units stated, and show base and adverse sensitivities. Preserve a clear gross/net reconciliation. The Version 1 15 bp fee is illustrative. Taxable-account effects need their own assumptions.

## As-of availability, revisions and exclusions

For any future historical decision replay, maintain append-only raw snapshots and a row-level ledger keyed by source, instrument, field, observation period and vintage. Store effective session date, published or released timestamp when evidenced, source document or snapshot identifier, retrieval and first-seen timestamps, correction/revision timestamp, raw value, hash, and the normalization code version. For filings, preserve acceptance timestamps and reporting dates separately. For adjustments, date the relevant corporate actions and preserve the as-of adjusted series or reconstruct it from eligible raw closes and actions under a documented consistent convention.

Use provider publication timestamps or archived evidence of accessibility to establish when a value was available. A stored snapshot provides evidence by its capture time if earlier release is unknown. Exchange close time or observation date alone cannot establish when the provider published a particular value or its correction. Filter vintages for availability before or at the cutoff, then use the latest eligible vintage per key. A download made today cannot support a historical point-in-time claim without archived availability evidence. Flag a present-day revised series as a current-vintage retrospective study and keep it out of as-of decision replay. Fix the universe and eligibility evidence as of each historical decision date if replay is later added.

Log excluded fund/date/field/vintage, source, validation rule, reason, original payload reference and disposition. When a revision arrives, retain old and new values with timestamps and hashes. Produce a run manifest with decision cutoff, data snapshot IDs, date range, alignment counts, exclusions, code and dependency versions, and output hash. Publish derived evidence only within provider licensing terms.

## Mandate evidence and liquidity

Use effective prospectuses and SAIs, dated holdings and ratings, issuer legal identifiers, and SEC filings to document bond and reserve eligibility, legal issuers, fund diversification exemptions, derivatives and leverage. Track each rule's evidence date, period covered, source and reviewer. ETF wrappers can hold exposures or employ practices beyond the fund's headline category. Apply fund or holdings-level treatment only after the relevant interpretation is agreed, with unknown eligibility recorded as **Unverified**. Annual rebalancing remains the client policy and annual loss tolerance remains unresolved.

Clarify whether the client accepts secondary-market liquidation into available cash for the five-business-day redemption rule. Ordinary ETF sales and direct issuer-level creation-unit redemptions are distinct mechanisms. Obtain broker/custodian documentation on sale-to-available-cash timing, settlement, restrictions and any transfer delays. Assess intended trade sizes relative to daily dollar volume and market depth, spreads, stress assumptions, execution days, and settlement days. A listing or standard settlement cycle alone cannot establish the rule. Sum verified eligible weights as a lower bound. If that lower bound meets 90%, record Pass. If eligible plus unknown weight is below 90%, record Fail. Otherwise record Unverified. [SEC ETF investor bulletin](https://www.sec.gov/servlet/sec/investor/alerts/etfs.pdf)

## Stage 3 import workflow

Stage 3 established the retrospective import format before actual data were available. The November 19, 2026 terminal request failed DNS resolution and the public demo endpoint yielded no accessible fund data. The file format and validation gates below remain applicable to authorized captures. [Alpha Vantage terms](https://www.alphavantage.co/terms_of_service/)

1. Use an authorized account to request `function=TIME_SERIES_MONTHLY_ADJUSTED`, `symbol=<ticker>`, and `datatype=csv` for each listing from `https://www.alphavantage.co/query`. Preserve each raw response privately with its own UTC download timestamp and SHA-256. The metadata's `downloaded_at` records the latest capture in the batch. Archive the per-fund capture times separately.
2. Verify identities, USD units and distribution adjustments against the source and calendar as described above. Use the most recent eligible completed month and the preceding 60 months. Match the four provider exports by actual session date using an outer join or equivalent audit. Investigate every missing value, date mismatch and duplicate before creating the panel. Log window exclusions and any separately reviewed duplicate resolution. Sort the verified panel in ascending order.
3. Save the CSV with header `date,BIL,IEF,LQD,VT`. Use UTF-8, `YYYY-MM-DD` exchange session dates, and the provider's adjusted-close field in decimal USD per share. Do not include an extra index column, currency signs or thousands separators. The upload must contain exactly 61 rows and rejects duplicates rather than resolving them automatically. No data values are bundled.
4. Save a separate UTF-8 JSON document. Fill each placeholder with actual evidence. URLs must omit credentials. The following is a schema example and contains no observed data.

```json
{
  "provider": "Provider name",
  "downloaded_at": "<ISO 8601 timestamp with timezone>",
  "currency": "USD",
  "frequency": "monthly",
  "adjusted_price_definition": "<provider field and adjustment definition>",
  "distribution_method": "<coverage and reinvestment convention>",
  "usage_restrictions": "<entitlement and sharing restrictions>",
  "calendar_reference": "<exchange calendars and reconciliation record>",
  "source_urls": {
    "BIL": "https://example.com/bil",
    "IEF": "https://example.com/ief",
    "LQD": "https://example.com/lqd",
    "VT": "https://example.com/vt"
  },
  "instrument_identifiers": {
    "BIL": "<verified permanent identifier>",
    "IEF": "<verified permanent identifier>",
    "LQD": "<verified permanent identifier>",
    "VT": "<verified permanent identifier>"
  },
  "exclusions": []
}
```

5. Place both files in the optional local data directory or import the ETF pair in **Advanced Data Management**. Open **Portfolio Builder → Research and data → Historical Market Data**. The app checks structural alignment, finite and positive prices, dates, gaps and basic month-end plausibility. The `calendar_reference` must identify the external calendar reconciliation. The app does not independently check exchange holidays, source assertions, revisions, stale observations or distribution events. Keep both files and the input hashes shown in the app to reproduce the analysis. The files are processed locally when Streamlit is run on your Mac.

The historical loader flags absolute monthly returns above 2% for BIL, 15% for IEF and LQD, and 25% for VT, and checks for zero variance. These are source-review triggers. Flagged values remain in the sample and require review before statistics are displayed. Pearson correlation uses monthly returns and is unchanged by multiplying covariance by 12. Maximum drawdown is a positive loss magnitude from the running high of adjusted month-end closes and can miss intramonth losses. Cumulative performance is relative to the first adjusted close. The ETF import is retrospective. Point-in-time macroeconomic evidence is handled separately in the [signal data card](signal-data-card.md).

## Stage 6 ETF portfolio analysis

Stage 6 connected the import workflow to the ETF portfolio model. The November 21, 2026 user-supplied exports were reviewed and analyzed using that workflow. [ETF evidence status](../outputs/etf-analysis-status.md)

### Acquire and align the files

1. Register for an authorized [Alpha Vantage API key](https://www.alphavantage.co/support/#api-key) and review the provider’s terms. Keep prices, raw responses, tokens and data source files outside the project unless sharing is permitted. In a private folder, save each monthly adjusted CSV as `BIL.csv`, `IEF.csv`, `LQD.csv`, and `VT.csv`. Use the URL below four times, changing the symbol and supplying the key privately. Do not save the key in source metadata. Provider errors or quota notices are not CSV data. [Monthly adjusted endpoint](https://www.alphavantage.co/documentation/#monthlyadj) · [Terms](https://www.alphavantage.co/terms_of_service/)

   ```text
   https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY_ADJUSTED&symbol=BIL&datatype=csv&apikey=YOUR_KEY
   ```

2. Record each response’s download timestamp, symbol, source link without credentials, exchange session dates, adjustment and distribution coverage, and SHA-256. Check the provider fields against issuer records and the exchange calendar. Investigate exclusions and any missing or unmatched observations. Re-download or reconcile discrepancies and document the outcome. The compiler uses only `adjusted_close` and fails if dates disagree, a month is missing, or the usual Stage 3 validation fails.
3. From the project folder, with Python activated, run the following. `2026-10` is the latest completed month for a November 2026 capture. Change it for later captures. Keep both upload files private. Build the metadata JSON from the Stage 3 schema above with the actual capture date and exclusions.

   ```sh
   python -m src.market_import "/path/to/private-etf-files" --end-month 2026-10 --output "/path/to/private-etf-files/aligned.csv"
   ```

### Reproduce investment comparisons

1. Place the pair in `data/` as `etf-prices.csv` and `etf-metadata.json`, or import it in **Advanced Data Management**. Select **Portfolio Builder → Research and data → Historical Market Data**. Confirm the source, calendar and distribution review in **Advanced Data Management**, then open **Set up the 36- and 60-month analysis**. The app uses the capture day in New York for both windows and requires the latest completed month. A newly captured panel supports comparison on the capture day. It cannot establish point-in-time prices for an earlier decision. Keep the same upload and hash for later reproduction.
2. Enter four dated, forward-looking arithmetic total return assumptions after embedded fund expenses and before annual investor costs. Enter the rationale, sources and chosen annual investor cost. Use Treasury carry and reinvestment assumptions for BIL, Treasury carry and duration/rate scenarios for IEF, carry less credit losses and spreads/duration scenarios for LQD, and dividend yield, earnings growth and valuation assumptions for VT. The dashboard does not fill these values with historical returns. Use inputs available by the capture date and keep their citations. The default 15 bp investor fee and 1 pp LQD/VT downside reduction are illustrative settings.
3. Inspect equal weight, 60% VT / 40% LQD, and the constrained candidate for both windows. Compare the same forward inputs and fee against annual covariance computed from 36 or 60 aligned monthly returns. Ill-conditioned covariance stops the comparison. Changing covariance can change risk and the optimal feasible weights. Feasibility and the ceiling are unchanged across windows for identical returns, costs and constraints, provided both covariance matrices are usable. The downside case reduces only LQD and VT expected returns.
4. The optimization provisionally counts IEF and LQD toward the bond floor and BIL toward reserve, deliberately excluding IEF from the ETF reserve assumption until its eligibility is reviewed. Holdings are long-only and fully invested. Five-day redemption and issuer treatment are unverified and are excluded from the solve. A portfolio with passing modeled checks is **Unverified** overall and eligible only for due diligence. An actual compliance decision requires evidence for bond and reserve eligibility, diversification exemptions, derivatives and leverage exposure, and client loss tolerance.
5. Export **ETF analysis evidence**. It records input hashes, common decision date, sample ranges, forecast rationale, fees, mandate, covariance, weights and decisions. Reproduce the file by uploading the exact same files, choosing the saved scenario and entering the saved assumptions. Save or submit the derived result only when provider terms permit. The public project excludes the licensed inputs and restricted derived files. See Actual ETF evidence for local reproduction.

## Actual ETF evidence

On November 21, 2026, four user-downloaded Alpha Vantage `TIME_SERIES_MONTHLY_ADJUSTED` CSV exports were reviewed. The latest local save time, rounded to seconds, records the batch capture proxy. The files have no embedded ticker or download timestamp. Attribution uses the named downloads, their endpoint parameters, and sponsor ticker/CUSIP information. Sponsor listings and the provider convention support USD per share. [BIL sponsor](https://www.ssga.com/us/en/individual/etfs/state-street-spdr-bloomberg-1-3-month-t-bill-etf-bil) · [IEF sponsor](https://www.ishares.com/us/products/239456/ishares-7-10-year-treasury-bond-etf-ief) · [LQD sponsor](https://www.ishares.com/us/products/239566/ishares-iboxx-investment-grade-corporate-bond-etf-lqd) · [VT sponsor](https://investor.vanguard.com/investment-products/etfs/profile/vt)

**Completed automated checks.** The capture-specific audit checked the raw schema, finite numeric fields, positive prices, quote ranges, and unique newest-first dates. The compiler and loader confirmed exact alignment, 61 consecutive completed months and 60 returns per fund, with no missing or nonpositive selected prices and no outlier flags. Earlier history and each November 20 partial-month observation were excluded. The audit checked the final weekday of each month, with March 28, 2024 explicitly used for the Good Friday closure. This capture-specific rule is separate from the general upload's basic month-end plausibility check. The dividend field was checked and counted. Returns use adjusted closes, so distributions are not added a second time. [Validation evidence](../outputs/validation-summary.md#actual-etf-integration)

**Completed manual review.** The review corroborated fund identity and USD units against the named exports, endpoint parameters and sponsor references, and checked the provider's stated distribution and split adjustment convention. The latest local save time is a batch capture proxy. The exports do not establish provider publication timestamps or earlier vintages.

**Proposed checks and unresolved evidence.** For future captures, verify the calendar against the listed exchange and reconcile issuer cash events and unusual adjustments. The November review did not reconstruct every distribution from issuer records. Fund eligibility, issuer treatment, five-business-day redemption and the client's annual loss tolerance still require separate evidence or policy decisions. [Alpha Vantage monthly adjusted data](https://www.alphavantage.co/documentation/#monthlyadj) · [Provider's adjustment description](https://www.alphavantage.co/support/) · [NYSE holiday rules](https://www.nyse.com/publicdocs/nyse/regulation/nyse/NYSE_Rules.pdf)

| Fund | Raw rows | Selected prices | Selected months with positive distribution field |
| --- | ---: | ---: | ---: |
| BIL | 234 | 61 | 50 |
| IEF | 292 | 61 | 56 |
| LQD | 292 | 61 | 56 |
| VT | 221 | 61 | 20 |

The execution uses annual arithmetic assumptions of **3.50% BIL**, **4.25% IEF**, **5.00% LQD**, and **8.00% VT**, after embedded fund expenses and before a common **15 bp** annual investor charge. These are analyst scenarios: normalized short-rate carry, intermediate Treasury carry with duration exposure, a modest incremental credit premium, and an equity income-and-growth allowance. They are independent of historical sample means. The 6.50% target case is an explicitly labeled feasibility diagnostic; the actual 7.00% client objective stays in place. No new portfolio is produced when the applicable target is infeasible.

The 36- and 60-month matrices use the same terminal session. Their differing volatility and correlations affect risk and minimum-risk weights. The return ceiling depends on the return assumptions, costs, and enforceable model constraints. A reviewed local pair enables the executive briefing and still leaves mandate evidence outstanding. The panel is a capture-date snapshot and does not establish earlier vintages.

The standard API terms describe personal use and a nontransferable license. The project did not establish public redistribution rights for these exports or the derivative evidence. Keep the raw and aligned files, metadata, monthly returns, and both derived reports private unless your agreement or written permission covers sharing. Public GitHub can contain code, fixed scenario assumptions, directions, and synthetic tests. [Alpha Vantage terms](https://www.alphavantage.co/terms_of_service/) · [Private reproduction](../data/README.md#reproduce-the-authorized-etf-capture)
