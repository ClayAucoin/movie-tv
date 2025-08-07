"""
python3 "/mnt/c/_lib/data/_scripts_/py/_projects/Arr/Radarr/test/firstFew.py"
"""

import requests
import csv
import os
import configRadarr  # Import Radarr config module

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_file_path = os.path.join(script_dir, "radarr_movies.csv")  # Save CSV in script directory

# Retrieve Radarr details from config file
RADARR_URL = configRadarr.RADARR_URL
API_KEY = configRadarr.API_KEY
API_URL = f"{RADARR_URL}/api/v3/movie"

# Include API key in headers
headers = {"X-Api-Key": API_KEY}

# Fetch movies directly from Radarr
def fetch_movies():
    response = requests.get(API_URL, headers=headers)
    try:
        movies_data = response.json()
        if isinstance(movies_data, list):
            print(f"✅ Retrieved {len(movies_data)} movies from Radarr.")
            return movies_data
        else:
            print(f"❌ Unexpected response type: {type(movies_data)}")
            return []
    except Exception as e:
        print(f"❌ Error parsing JSON response: {e}")
        return []

# Fetch movies
movies = fetch_movies()

# Exit early if no movies found
if not movies:
    print("❌ No movies found. Exiting script.")
    exit()

# Print first movie entry to confirm structure
print(f"✅ First movie entry: {movies[0]}")

# Define CSV field order
fieldnames = [
    "title", "sortTitle", "cleanTitle", "year", "physicalRelease", "runtime",
    "movieFile.mediaInfo.runTime", "status", "inCinemas", "hasFile", "imdbId",
    "tmdbId", "movieFile.quality.name", "movieFile.quality.resolution",
    "movieFile.mediaInfo.resolution", "movieFile.mediaInfo.subtitles",
    "statistics.sizeOnDisk", "movieFile.size", "sizeOnDisk", "path",
    "movieFile.path", "youTubeTrailerId", "overview"
]

# Open CSV file for writing
with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()

    for movie in movies:
        try:
            # Debug: Print movie title to ensure it's being processed
            print(f"🔹 Processing movie: {movie.get('title', 'Unknown')}")

            # Ensure movieFile exists
            movie_file = movie.get("movieFile", {})
            media_info = movie_file.get("mediaInfo", {})
            quality_info = movie_file.get("quality", {}).get("quality", {})

            # Ensure subtitles are in list format
            subtitles = media_info.get("subtitles", "")
            if isinstance(subtitles, list):
                subtitles = ", ".join([sub["language"] for sub in subtitles if isinstance(sub, dict)])

            row = {
                "title": movie.get("title", ""),
                "sortTitle": movie.get("sortTitle", ""),
                "cleanTitle": movie.get("cleanTitle", ""),
                "year": movie.get("year", ""),
                "physicalRelease": movie.get("physicalRelease", ""),
                "runtime": movie.get("runtime", ""),
                "movieFile.mediaInfo.runTime": media_info.get("runTime", ""),
                "status": movie.get("status", ""),
                "inCinemas": movie.get("inCinemas", ""),
                "hasFile": movie.get("hasFile", ""),
                "imdbId": movie.get("imdbId", ""),
                "tmdbId": movie.get("tmdbId", ""),
                "movieFile.quality.name": quality_info.get("name", ""),
                "movieFile.quality.resolution": quality_info.get("resolution", ""),
                "movieFile.mediaInfo.resolution": media_info.get("resolution", ""),
                "movieFile.mediaInfo.subtitles": subtitles,
                "statistics.sizeOnDisk": movie.get("statistics", {}).get("sizeOnDisk", ""),
                "movieFile.size": movie_file.get("size", ""),
                "sizeOnDisk": movie.get("sizeOnDisk", ""),
                "path": movie.get("path", ""),
                "movieFile.path": movie_file.get("path", ""),
                "youTubeTrailerId": movie.get("youTubeTrailerId", ""),
                "overview": movie.get("overview", ""),
            }

            writer.writerow(row)
            print(f"✅ Successfully written: {movie.get('title', 'Unknown')}")

        except Exception as e:
            print(f"⚠️ Error processing movie '{movie.get('title', 'Unknown')}': {e}")

print(f"✅ Data successfully saved to: {csv_file_path}")
