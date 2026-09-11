"""Phase 8: chronological train/validation/test split. Run with `python -m src.splits`."""
import json
import pandas as pd
from src.config import PROCESSED_DIR, OUTPUTS_DIR

ALL_MONTHS = [f"{y}_{m:02d}" for y, mrange in [(2025, range(4, 13)), (2026, range(1, 4))] for m in mrange]
# 2025_04 .. 2025_12 (9 months) train | 2026_01, 2026_02 (2 months) validation | 2026_03 (1 month) test
SPLIT = {"train": ALL_MONTHS[:9], "validation": ALL_MONTHS[9:11], "test": ALL_MONTHS[11:]}

def save_split():
    OUTPUTS_DIR.joinpath("tables").mkdir(parents=True, exist_ok=True)
    (OUTPUTS_DIR / "tables" / "split_definition.json").write_text(json.dumps(SPLIT, indent=2))
    return SPLIT

def load_split_frames(columns=None):
    out = {}
    for split_name, months in SPLIT.items():
        frames = [pd.read_parquet(PROCESSED_DIR / f"taxi_{m}.parquet", columns=columns) for m in months]
        out[split_name] = pd.concat(frames, ignore_index=True)
    return out

def materialize_split_datasets(columns=None):
    """PDF Submission requirement #4: write the actual train/validation/test
    datasets to disk as separate files, not just a JSON month manifest."""
    out_dir = OUTPUTS_DIR / "tables" / "dataset_splits"
    out_dir.mkdir(parents=True, exist_ok=True)
    frames = load_split_frames(columns=columns)
    for split_name, df in frames.items():
        df.to_parquet(out_dir / f"{split_name}.parquet", index=False)
    return frames

if __name__ == "__main__":
    save_split()
    materialize_split_datasets()
    print("Saved outputs/tables/split_definition.json and outputs/tables/dataset_splits/*.parquet")