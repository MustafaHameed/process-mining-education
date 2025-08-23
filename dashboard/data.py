from __future__ import annotations

from pathlib import Path
from typing import Tuple
import pandas as pd

try:
    # Prefer existing root-level processor if available
    from data_preprocessing import EPMDataProcessor  # type: ignore
except Exception:
    EPMDataProcessor = None  # type: ignore


def load_epm_dataset(repo_root: Path) -> Tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Load the bundled EPM dataset from the repo.

    Returns a tuple of (raw_df, event_log_df, stats_dict).
    """
    dataset_dir = repo_root / "EPM Dataset 2"
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset folder not found: {dataset_dir}")

    if EPMDataProcessor is None:
        # Minimal fallback: try any CSV within the dataset folder
        candidates = list(dataset_dir.rglob("*.csv"))
        if not candidates:
            raise ImportError(
                "EPMDataProcessor not available and no CSV found in the dataset folder."
            )
        df = pd.read_csv(candidates[0])
        event_log = df
        stats = {
            "total_events": len(df),
            "total_cases": df["case:concept:name"].nunique()
            if "case:concept:name" in df.columns
            else None,
        }
        return df, event_log, stats

    processor = EPMDataProcessor(str(dataset_dir))  # type: ignore
    raw = processor.load_all_data()
    if raw is None or raw.empty:
        raise ValueError(f"No data loaded from {dataset_dir}")
    event_log = processor.create_event_log(raw)
    stats = processor.get_basic_statistics(event_log)
    return raw, event_log, stats


def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)
