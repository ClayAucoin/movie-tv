# arr/config/config.py
from dotenv import load_dotenv, find_dotenv
import os

# Finds movie-tv/.env by walking up directories
load_dotenv(find_dotenv())

SONARR_URL = os.getenv("SONARR_URL")
SONARR_API_KEY = os.getenv("SONARR_API_KEY")
RADARR_URL = os.getenv("RADARR_URL")
RADARR_API_KEY = os.getenv("RADARR_API_KEY")

SONARR_API_URL = f"{SONARR_URL.rstrip('/')}/api/v3/series"
RADARR_API_URL = f"{RADARR_URL.rstrip('/')}/api/v3/movie"

# Optional: fail fast if missing
missing = [k for k, v in {
    "SONARR_URL": SONARR_URL,
    "SONARR_API_KEY": SONARR_API_KEY,
    "RADARR_URL": RADARR_URL,
    "RADARR_API_KEY": RADARR_API_KEY,
}.items() if not v]
if missing:
    raise RuntimeError(f"Missing env vars: {', '.join(missing)}")
