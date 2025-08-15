"""
python "C:/Users/Administrator/projects/movie-tv/arr/Radarr/updateRadarrData.py"

python3 "/mnt/c/Users/Administrator/projects/movie-tv/arr/Radarr/updateRadarrData.py"
"""

import sys
import requests
import csv
import os
import platform
import ctypes
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # .../movie-tv
sys.path.append(PROJECT_ROOT)
from arr.config.config import RADARR_URL, RADARR_API_KEY, RADARR_API_URL

# Check if the script is running with the "/task_scheduler" argument
is_task_scheduler = '/task_scheduler' in sys.argv

def notify(title, message):
    try:
        if not is_task_scheduler:
            ctypes.windll.user32.MessageBoxW(0, message, title, 0x40)
    except Exception:
        # If not on Windows or GUI not available, ignore
        pass

# Output directory per OS
if platform.system() == "Windows":
    output_dir = r"E:\My Drive\__clay0aucoin@gmail.com\movies_on_m"
else:
    output_dir = "/mnt/E/MY DRIVE/__clay0aucoin@gmail.com/movies_on_m"

os.makedirs(output_dir, exist_ok=True)
csv_file_path = os.path.join(output_dir, "radarr.csv")

headers = {"X-Api-Key": RADARR_API_KEY}

def fetch_movies():
    try:
        r = requests.get(RADARR_API_URL, headers=headers)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list):
            print(f"❌ Unexpected response type: {type(data)}")
            return []
        print(f"✅ Retrieved {len(data)} movies from Radarr.")
        return data
    except Exception as e:
        print(f"❌ Error fetching data from Radarr: {e}")
        notify("Radarr Script", f"❌ Error fetching data from Radarr: {e}")
        return []

def format_date(s):
    return s.split("T")[0] if s and "T" in s else s

movies = fetch_movies()
if not movies:
    print("❌ No movies found. Exiting script.")
    raise SystemExit(1)

fieldnames = [
    'imdbId', 'tmdbId', 'Title', 'SortTitle', 'Year', 'Physical Release', 'InCinemas', 'Status',
    'Length', 'RunTime', 'HasFile', 'Quality', 'Resolution', 'Aspect Ratio', 'Subtitles',
    'Collection Title', 'Collection tmdbId', 'SizeOnDisk', 'MovieFile Path', 'YT TrailerId',
    'Overview', 'Website', 'Monitored', 'Certification', 'Tags', 'Genres', 'Original Language'
]

written = 0

with open(csv_file_path, 'w', newline='', encoding='utf-8', errors='replace') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    w.writeheader()

    for m in movies:
        try:
            mf = m.get("movieFile", {}) or {}
            mi = mf.get("mediaInfo", {}) or {}
            q = mf.get("quality", {}) or {}
            q_quality = q.get("quality", {}) or {}

            subs = mi.get("subtitles", "")
            if isinstance(subs, list):
                subs = ", ".join([s.get("language", "") for s in subs if isinstance(s, dict)])

            coll = m.get("collection", {}) or {}
            coll_title = coll.get("title", "")
            coll_tmdb = coll.get("tmdbId", "")

            lang = (m.get("originalLanguage") or {}).get("name", "")

            row = {
                "imdbId": m.get("imdbId", ""),
                "tmdbId": m.get("tmdbId", ""),
                "Title": m.get("title", ""),
                "SortTitle": m.get("sortTitle", ""),
                "Year": m.get("year", ""),
                "Physical Release": format_date(m.get("physicalRelease", "")),
                "InCinemas": format_date(m.get("inCinemas", "")),
                "Status": m.get("status", ""),
                "Length": m.get("runtime", ""),
                "RunTime": mi.get("runTime", ""),
                "HasFile": m.get("hasFile", ""),
                "Quality": q_quality.get("name", ""),
                "Resolution": q_quality.get("resolution", ""),
                "Aspect Ratio": mi.get("resolution", ""),
                "Subtitles": subs,
                "Collection Title": coll_title,
                "Collection tmdbId": coll_tmdb,
                "SizeOnDisk": m.get("sizeOnDisk", ""),
                "MovieFile Path": mf.get("path", ""),
                "YT TrailerId": m.get("youTubeTrailerId", ""),
                "Overview": m.get("overview", ""),
                "Website": m.get("website", ""),
                "Monitored": m.get("monitored", ""),
                "Certification": m.get("certification", ""),
                "Tags": ", ".join(m.get("tags", [])) if isinstance(m.get("tags"), list) else m.get("tags", ""),
                "Genres": ", ".join(m.get("genres", [])) if isinstance(m.get("genres"), list) else m.get("genres", ""),
                "Original Language": lang,
            }

            w.writerow(row)
            written += 1
        except Exception as e:
            print(f"⚠️ Error processing movie '{m.get('title', 'Unknown')}': {e}")

print(f"✅ {written}/{len(movies)} movies successfully saved to: {csv_file_path}")
notify("Radarr Script", f"✅ {len(movies)} movies successfully saved")
