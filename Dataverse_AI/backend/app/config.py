"""Paths back to the project root and .env loading. Read-only against the root
project; generated artifacts live under backend/data/."""
from pathlib import Path
from dotenv import load_dotenv
import os

BACKEND_DIR = Path(__file__).resolve().parent.parent          # Dataverse_AI/backend
DATAVERSE_AI_DIR = BACKEND_DIR.parent                          # Dataverse_AI
PROJECT_ROOT = DATAVERSE_AI_DIR.parent                          # Datathon

load_dotenv(DATAVERSE_AI_DIR / ".env")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")

# Root project (Parts 1-4) -- read-only from here
ROOT_OUTPUTS = PROJECT_ROOT / "outputs"
ROOT_MODELS = PROJECT_ROOT / "models"
ROOT_PROCESSED = PROJECT_ROOT / "processed"
ROOT_DATA = PROJECT_ROOT / "data"
ROOT_REPORTS = PROJECT_ROOT / "reports"

ZONE_FILE = ROOT_DATA / "Urban_Flow_Analytics_Zone_Dataset.csv"

# Generated Track 5/6 artifacts -- read/write from here only
DATA_DIR = BACKEND_DIR / "data"
EVIDENCE_DIR = DATA_DIR / "evidence"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
CONTRACT_PATH = DATA_DIR / "analytics_contract.json"
