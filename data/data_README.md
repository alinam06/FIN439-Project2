# Private local data

A clean checkout starts in classroom mode. Licensed inputs are optional and ignored by Git.

| Local path | Purpose |
| --- | --- |
| `raw/BIL.csv`, `raw/IEF.csv`, `raw/LQD.csv`, `raw/VT.csv` | Original Alpha Vantage monthly adjusted exports. The prefix `monthly_adjusted_` is accepted. |
| `etf-prices.csv` and `etf-metadata.json` | Generated aligned prices and provenance, including source raw file hashes and reviewed panel hash. A reviewed pair enables Reviewed ETF snapshot by default in a new session. |
| `baa10y-archive.json` and `baa10y-manifest.json` | Optional authorized ALFRED archive and metadata, unavailable in the verified ETF run. |

The preparation workflow below reads raw files without changing them. A reviewed, hash-matching pair enables the executive ETF comparison. An Advanced Data Management upload overrides only its matching source for the browser session. The app does not save uploads.

The raw exports, aligned prices, metadata and vendor-derived reports remain private pending authorization. Store no API keys here. [ETF methodology](../docs/data-methodology.md#actual-etf-evidence) · [ALFRED instructions](../docs/signal-data-card.md#reproduce-with-an-authorized-export)

## Reproduce the authorized ETF capture

1. Place the authorized source CSVs under `data/raw/` using the names above. See the [provider and alignment instructions](../docs/data-methodology.md#acquire-and-align-the-files).
2. For the original November 21, 2026 capture only, use its recorded timestamp from the repository root with the project environment active:

   ```sh
   python -m src.etf_evidence --prepare --captured-at 2026-11-21T11:45:36-05:00
   ```

3. With the prepared pair, run `python -m src.etf_evidence` to regenerate the private ETF reports and monthly returns. Later downloads require their true capture timestamp and may contain revisions. The fixed October 2026 panel must be the latest completed month for the capture. Exact replication needs authorized access to the original files. See the [historical-window evidence options](../docs/rubric-alignment.md#historical-window-reproduction-and-permissions).

## Optional research and session uploads

**Advanced Data Management** accepts authorized price, signal and experiment files for the current session. Set the signal date using the New York end-of-day convention. The app reports the archived signal as unavailable when evidence is missing.

For broader research, go to **Portfolio Builder → Research and data → Advanced · Security Search**. The search can use the local ETF panel, optional keyless price-only Market History, or optional Alpha Vantage access with `ALPHAVANTAGE_API_KEY` (alternate spelling `ALPHA_VANTAGE_API_KEY`). Availability depends on network access, provider entitlements, limits and data quality. Searches leave the active investment universe and decision unchanged.
