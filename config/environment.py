# config/environment.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Project root = one level above /config
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env from the project root, no matter where the script is run from
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
JWT_SECRET = os.getenv("JWT_SECRET")

if not DATABASE_URL:
    raise RuntimeError(
        f"DATABASE_URL is not set. Expected it in {BASE_DIR / '.env'}"
    )