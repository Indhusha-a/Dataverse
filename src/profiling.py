"""Phase 2: schema discovery. Run with `python -m src.profiling`.
Reads each raw file in chunks only -- never loads a full 500MB CSV at once."""
import json
import pandas as pd
from src.config import RAW_DATA_DIR, TAXI_FILE_GLOB, ZONE_FILE, OUTPUTS_DIR, CHUNK_SIZE

def profile_file(path, is_zone=False):
    sample = pd.read_csv(path, nrows=2000)
    info = {
        "file": path.name, "size_mb": round(path.stat().st_size / 1e6, 1),
        "columns": list(sample.columns), "dtypes_sample": sample.dtypes.astype(str).to_dict(),
    }
    if is_zone:
        full = pd.read_csv(path)
        info["n_rows"] = len(full)
        info["missing_pct"] = (full.isna().mean() * 100).round(2).to_dict()
        return info

    n_rows, missing_counts = 0, None
    for chunk in pd.read_csv(path, chunksize=CHUNK_SIZE):
        n_rows += len(chunk)
        m = chunk.isna().sum()
        missing_counts = m if missing_counts is None else missing_counts.add(m, fill_value=0)
    info["n_rows"] = n_rows
    info["missing_pct"] = (missing_counts / n_rows * 100).round(3).to_dict()
    return info

def main():
    OUTPUTS_DIR.joinpath("profiles").mkdir(parents=True, exist_ok=True)
    taxi_files = sorted(RAW_DATA_DIR.glob(TAXI_FILE_GLOB))
    inventory = [profile_file(f) for f in taxi_files]
    inventory.append(profile_file(ZONE_FILE, is_zone=True))

    (OUTPUTS_DIR / "profiles" / "dataset_inventory.json").write_text(json.dumps(inventory, indent=2, default=str))
    pd.json_normalize(inventory).to_csv(OUTPUTS_DIR / "profiles" / "dataset_inventory.csv", index=False)

    lines = ["# Schema Report\n"]
    for entry in inventory:
        lines.append(f"## {entry['file']} ({entry['size_mb']} MB, {entry['n_rows']:,} rows)\n")
        lines.append("| column | dtype | missing % |\n|---|---|---|\n")
        for col in entry["columns"]:
            dt = entry["dtypes_sample"].get(col, "?")
            mp = entry["missing_pct"].get(col, 0)
            lines.append(f"| {col} | {dt} | {mp} |\n")
        lines.append("\n")
    (OUTPUTS_DIR / "profiles" / "schema_report.md").write_text("".join(lines))
    print("Profiling complete ->", OUTPUTS_DIR / "profiles")

if __name__ == "__main__":
    main()