from dotenv import load_dotenv, find_dotenv
import os

# Load .env from the repo root (or nearest parent)
load_dotenv(find_dotenv())

# Read env vars (with safe defaults if you want)
SONARR_URL = os.getenv("SONARR_URL", "http://192.168.1.205:8989")
SONARR_API_KEY = os.getenv("SONARR_API_KEY", "e011965887634f9e8bd33536020dc1ed")

RADARR_URL = os.getenv("RADARR_URL", "http://192.168.1.205:7878")
RADARR_API_KEY = os.getenv("RADARR_API_KEY", "92315363a3c9466295befa6b7a7a197e")

# Build API endpoints
SONARR_API_URL = f"{SONARR_URL.rstrip('/')}/api/v3/series"
RADARR_API_URL = f"{RADARR_URL.rstrip('/')}/api/v3/movie"

# Optional: fail fast if secrets aren’t set (remove defaults above if you want this strict)
required = {
    "SONARR_URL": SONARR_URL,
    "SONARR_API_KEY": SONARR_API_KEY,
    "RADARR_URL": RADARR_URL,
    "RADARR_API_KEY": RADARR_API_KEY,
}
missing = [k for k, v in required.items() if not v]
if missing:
    raise RuntimeError(f"Missing required environment vars in .env: {', '.join(missing)}")
