"""Read-only local research data with explicit session overrides."""

import csv
from dataclasses import dataclass
from pathlib import Path

from src.economic_signal import Archive, load_archive
from src.historical import HistoricalSample, load_historical

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
ETF_FILES = ("etf-prices.csv", "etf-metadata.json")
SIGNAL_FILES = ("baa10y-archive.json", "baa10y-manifest.json")


@dataclass(frozen=True)
class DataWorkspace:
    etf: HistoricalSample | None
    archive: Archive | None
    etf_status: str
    signal_status: str


def load_pair(root, names, loader, override):
    source = "Session upload" if override is not None else "Repository data/"
    try:
        if override is None:
            paths = [root / name for name in names]
            if not all(path.is_file() for path in paths):
                missing = ", ".join(path.name for path in paths if not path.is_file())
                return None, f"Unavailable. Missing from data/: {missing}."
            override = tuple(path.read_bytes() for path in paths)
        return loader(*override), f"{source} · structural checks passed."
    except (OSError, ValueError, csv.Error, OverflowError, RecursionError) as error:
        return None, f"Unavailable. {source} rejected: {error}"


def load_workspace(root=None, *, etf_override=None, signal_override=None):
    root = DATA_DIR if root is None else root
    etf, etf_status = load_pair(root, ETF_FILES, load_historical, etf_override)
    archive, signal_status = load_pair(root, SIGNAL_FILES, load_archive, signal_override)
    return DataWorkspace(etf, archive, etf_status, signal_status)
