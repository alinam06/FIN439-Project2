# BAA10Y decision-date evidence

**Decision date:** November 21, 2026, New York end-of-day convention. The official FRED table was consulted on November 21 and displayed its last update as November 20, 2026 at 4:03 p.m. CST (5:03 p.m. Eastern). The analysis used the table already visible by 10:48 a.m. Eastern on November 21. This is contemporaneous snapshot evidence for that decision date. The source update timestamp does not establish individual release timestamps or earlier ALFRED vintages.

| Check | Observed result |
| --- | --- |
| Source | FRED BAA10Y, daily Moody’s seasoned Baa corporate yield minus the 10-year Treasury constant-maturity yield, in percentage points |
| Eligible comparison window | October 21 through November 19, 2026 |
| Numeric observations and missing data | 21 numeric observations, one explicit missing value on November 11 excluded without interpolation |
| Change over 20 numeric observations | **+12 basis points** |
| Decision | **Review**. Examine LQD credit-spread exposure and VT equity downside before considering an allocation change. Preserve all weights and mandate limits. |

The published table values were evaluated using the app’s 20-observation rule. Its snapshot date establishes availability for this example only. The ALFRED API archive was unavailable in this session, so revision handling has automated synthetic coverage and awaits comparison with a real archive. No raw series or row-level values are bundled. To reproduce while the dated snapshot is available, select the last 21 numeric observations through November 19, exclude missing entries, and subtract the oldest from the newest. For durable vintage evidence, use the authorized ALFRED workflow and compare against a single-date API request. [Official FRED table](https://fred.stlouisfed.org/data/BAA10Y) · [Signal data card](../docs/signal-data-card.md)
