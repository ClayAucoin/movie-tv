"""
python3 "/mnt/c/_lib/data/_scripts_/py/_projects/Arr/Radarr/test/convertMovieExtract.py"
"""

import csv
import json
import os

# Get the script directory and JSON file path
script_dir = os.path.dirname(os.path.abspath(__file__))
json_file_path = os.path.join(script_dir, "radarr_series_data.json")
csv_file_path = os.path.join(script_dir, "radarr_movies.csv")

# Load the JSON data
with open(json_file_path, "r", encoding="utf-8") as infile:
    movies_list = json.load(infile)

# Validate that movies_list is a **list of dictionaries**
if not isinstance(movies_list, list) or not all(isinstance(movie, dict) for movie in movies_list):
    print("❌ Error: JSON data is not a valid list of dictionaries.")
    exit(1)

# Define CSV field order
fieldnames = [
    "title", "sortTitle", "cleanTitle", "year", "physicalRelease", "runtime",
    "movieFile.mediaInfo.runTime", "status", "inCinemas", "hasFile", "imdbId",
    "tmdbId", "movieFile.quality.name", "movieFile.quality.resolution",
    "movieFile.mediaInfo.resolution", "movieFile.mediaInfo.subtitles",
    "collection.title", "collection.tmdbId", "statistics.sizeOnDisk",
    "movieFile.size", "sizeOnDisk", "path", "movieFile.path",
    "youTubeTrailerId", "overview"
]

# Open CSV file for writing (fix encoding issue)
with open(csv_file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()

    for movie in movies_list:
        if not isinstance(movie, dict):
            print(f"⚠️ Skipping invalid entry (not a dictionary): {movie}")
            continue  # Skip any non-dictionary data

        try:
            # Extract data with safety checks for missing fields
            row = {
                "title": movie.get("title", ""),
                "sortTitle": movie.get("sortTitle", ""),
                "cleanTitle": movie.get("cleanTitle", ""),
                "year": movie.get("year", ""),
                "physicalRelease": movie.get("physicalRelease", ""),
                "runtime": movie.get("runtime", ""),
                "movieFile.mediaInfo.runTime": movie.get("movieFile", {}).get("mediaInfo", {}).get("runTime", ""),
                "status": movie.get("status", ""),
                "inCinemas": movie.get("inCinemas", ""),
                "hasFile": movie.get("hasFile", ""),
                "imdbId": movie.get("imdbId", ""),
                "tmdbId": movie.get("tmdbId", ""),
                "movieFile.quality.name": movie.get("movieFile", {}).get("quality", {}).get("quality", {}).get("name", ""),
                "movieFile.quality.resolution": movie.get("movieFile", {}).get("quality", {}).get("quality", {}).get("resolution", ""),
                "movieFile.mediaInfo.resolution": movie.get("movieFile", {}).get("mediaInfo", {}).get("resolution", ""),
                "movieFile.mediaInfo.subtitles": (
                    ", ".join(
                        [sub.get("language", "Unknown") for sub in movie.get("movieFile", {}).get("mediaInfo", {}).get("subtitles", [])]
                    ) if movie.get("movieFile", {}).get("mediaInfo", {}).get("subtitles") else "No subtitles"
                ),
                "collection.title": movie.get("collection", {}).get("title", ""),
                "collection.tmdbId": movie.get("collection", {}).get("tmdbId", ""),
                "statistics.sizeOnDisk": movie.get("statistics", {}).get("sizeOnDisk", ""),
                "movieFile.size": movie.get("movieFile", {}).get("size", ""),
                "sizeOnDisk": movie.get("sizeOnDisk", ""),
                "path": movie.get("path", ""),
                "movieFile.path": movie.get("movieFile", {}).get("path", ""),
                "youTubeTrailerId": movie.get("youTubeTrailerId", ""),
                "overview": movie.get("overview", ""),
            }
            writer.writerow(row)

        except Exception as e:
            print(f"⚠️ Error processing movie '{movie.get('title', 'Unknown')}': {e}")

print(f"✅ Data successfully saved to: {csv_file_path}")
