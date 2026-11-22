# BAA10Y signal data card

## Series and timing

| Field | Definition |
| --- | --- |
| Source | Federal Reserve Bank of St. Louis, FRED series **BAA10Y**, Interest Rate Spreads release. ALFRED provides archived versions through the FRED API real-time-period interface. |
| Definition | Moody’s seasoned Baa corporate bond yield minus the 10-year U.S. Treasury constant-maturity yield. FRED notes a change in the Treasury input source with the June 21, 2019 update. |
| Units and frequency | FRED labels the series Percent. As a yield difference, one displayed unit equals one percentage point or 100 basis points. Daily, not seasonally adjusted. |
| Publication timing | The FRED page shows a series update timestamp and a separate observation date. Updates can follow the observation date, including across weekends and holidays. The series page does not establish a guaranteed row-level release time or publication lag. |
| Revision behavior | A historical value can have different ALFRED real-time intervals. ALFRED typically adds new or revised observations within one business day of release and can use provider release dates or first-availability dates when an official release date is unavailable. Archive coverage and precision can vary. |

[FRED series and copyright notes](https://fred.stlouisfed.org/series/BAA10Y) · [ALFRED archive](https://alfred.stlouisfed.org/series?seid=BAA10Y) · [ALFRED timing FAQ](https://alfred.stlouisfed.org/help) · [FRED real-time periods](https://fred.stlouisfed.org/docs/api/fred/realtime_period.html)

## Point-in-time filter and exclusions

- **Observation date** is the date of the spread measurement. **Publication date** is the date it was released, when independently documented. The import does not supply row-level publication dates or times, so the dashboard marks them unverified. **Vintage interval** is the inclusive real-time start and end date reported by ALFRED for a version. **Retrieval timestamp** records when the export was captured and bounds how far forward it can be used. It does not determine when older rows were originally published.
- The filter selects only an observation dated on or before the decision date whose vintage interval covers that date. If independent publication evidence is provided to the reusable filter, it also excludes observations published after the cutoff. A future vintage cannot replace a version that was available on the selected day. ALFRED boundaries can reflect the query range, so the displayed start is not a claim about first publication.
- The selected date is a U.S. end-of-day review. Same-day eligible versions are included. Use an earlier decision date for a decision made before that day’s releases. The app rejects dates outside the real-time query range or after the New York calendar date of capture. A same-day capture may omit releases that occur later that day. The historical chart is a single as-of view with each row selected using the same cutoff.
- Current-only FRED downloads, aggregated or transformed series, truncated responses, conflicting vintage intervals, invalid values, and manifest mismatches are rejected. ALFRED explicit missing values are counted and omitted, without filling or interpolation. Missing or stale history pauses reliance on the signal. The file hash detects changes relative to the manifest. It does not authenticate the uploader’s series and frequency declarations. Check the original query against the manifest.

## Financial interpretation and decision rule

A widening spread can indicate higher compensation for corporate default and liquidity risk. This is relevant to LQD’s corporate credit exposure and may coincide with tighter financial conditions for equities in VT. BAA10Y is a broad U.S. indicator with a nominal Treasury comparison. It can reflect Treasury rate moves and duration differences, and does not measure the ETFs’ own spreads, global equity risk, or the likelihood of a market loss.

Subtract the spread 20 eligible numeric observations earlier from the latest eligible spread and display the change in basis points. A positive change prompts **Review** of credit and equity downside before any proposed allocation change. A flat or negative change means **Monitor** through ordinary risk review. **Unavailable** pauses signal-based decisions if the latest numeric observation is more than seven calendar days old, there are fewer than 21 eligible numeric observations, or the comparison spans more than 45 calendar days. These are transparent operational choices without a validated forecast or calibrated threshold. Allocation decisions require a separate committee assessment. The optimizer inputs, portfolio weights and client policy do not change.

## Reproduce with an authorized export

Check Moody’s restrictions in the official series notes and confirm that your use is permitted. Keep the raw data outside the repository. Stage 4 did not retrieve a machine-readable BAA10Y archive, and the app opens with the signal unavailable. A live FRED graph is not an as-of input.

1. Using a registered FRED API key, request the [observations endpoint](https://fred.stlouisfed.org/docs/api/fred/series_observations.html) with the parameters below. Set `observation_start` early enough to cover the decision date and comparison window. The range below is an example. Omit the frequency aggregation parameter. Supply `api_key` in your client and keep it out of any files you share.

   ```text
   https://api.stlouisfed.org/fred/series/observations
   series_id=BAA10Y
   file_type=json
   output_type=1
   units=lin
   realtime_start=1776-07-04
   realtime_end=9999-12-31
   observation_start=2025-01-01
   offset=0
   limit=100000
   ```

2. Save the unchanged response as `baa10y-archive.json` in a private working folder. At download time, run the following in that folder with Python 3.14 or substitute the original capture timestamp if creating the manifest later.

   ```sh
   python3.14 -c 'import datetime, hashlib, json, pathlib; p = pathlib.Path("baa10y-archive.json"); m = dict(series_id="BAA10Y", endpoint="https://api.stlouisfed.org/fred/series/observations", frequency="daily", retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), sha256=hashlib.sha256(p.read_bytes()).hexdigest()); pathlib.Path("baa10y-manifest.json").write_text(json.dumps(m, indent=2), encoding="utf-8")'
   ```

3. Place both files in optional local `data/` or import them through **Advanced Data Management**. Set the decision date there and open **Portfolio Builder → Research and data → Economic Signals**. Record the decision date, original query parameters with credentials removed, archive hash, retrieval timestamp, and the displayed vintage information. The chart and calculations run offline after import. Synthetic fixtures in the test suite demonstrate the cutoff mechanics independently of provider access.

## Stage 6 decision-date check

The [November 21 decision evidence](../outputs/signal-decision-evidence.md) uses a contemporaneously available official FRED table with a November 20 update timestamp. Its 20-observation change was +12 basis points, triggering credit and equity downside review. No allocation inputs changed. The current-snapshot check establishes this example's availability; it does not verify earlier revision history. [Official FRED table](https://fred.stlouisfed.org/data/BAA10Y)

To verify the vintage workflow independently, obtain the full response and manifest using the request above, load them through local files or Advanced Data Management, and select **November 21, 2026**. Make a separate check request with both `realtime_start` and `realtime_end` set to `2026-11-21`, retaining the other parameters. Compare the latest observation, the comparison observation and the count of explicitly missing values for the same observation range. The single-date response is a check reference; upload the multi-date response for vintage filtering. To confirm a revision, compare the same observation date across consecutive eligible versions in the multi-date response. If no revisions appear in the selected interval, record that outcome. Use **Export signal decision evidence** to retain the cutoff, archive fingerprint, counts, dates, and decision effect without raw values. [FRED observations API](https://fred.stlouisfed.org/docs/api/fred/series_observations.html)
