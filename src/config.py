from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = ROOT / "data"
PROCESSED_DIR = ROOT / "processed"
OUTPUTS_DIR = ROOT / "outputs"
MODELS_DIR = ROOT / "models"

TAXI_FILE_GLOB = "Urban_Flow_Analytics_Taxi_Dataset_*.csv"
ZONE_FILE = RAW_DATA_DIR / "Urban_Flow_Analytics_Zone_Dataset.csv"

RANDOM_SEED = 42
CHUNK_SIZE = 500_000  # rows per chunk for the 500MB monthly files