"""
python "C:/Users/Administrator/projects/movie-tv/arr/Radarr/updateRadarrData.py"

python3 "C:/_lib/data/_scripts_/py/_projects/Arr/Radarr/updateRadarrData.py"
"""

import requests
import csv
import os
import platform  # Detect OS
import configRadarr  # Import configuration for Radarr API
from datetime import datetime

# ----------------------------------------
# Set base output directory based on OS
# ----------------------------------------
if platform.system() == "Windows":
    #output_dir = "C:\\Users\\Administrator\\Dropbox\\arr\\"  # Windows path for Dropbox
    output_dir = "E:\\My Drive\\_clay0aucoin@gmail.com\\movies_on_m\\arr"
else:
    output_dir = "/mnt/c/Users/Administrator/Dropbox/arr/"  # Linux/WSL path for Dropbox

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

# Define the CSV file path
csv_file_path = os.path.join(output_dir, "radarr.csv")

# ----------------------------------------
# Retrieve Radarr API details from config
# ----------------------------------------
RADARR_URL = configRadarr.RADARR_URL
API_KEY = configRadarr.API_KEY
API_URL = configRadarr.API_URL

# Include API key in headers for requests
headers = {"X-Api-Key": API_KEY}


# ----------------------------------------
# Function to fetch movies from Radarr
# ----------------------------------------
def fetch_movies():
    """Fetches movie data from Radarr API and returns a list of movies."""
    try:
        response = requests.get(API_URL, headers=headers)
        movies_data = response.json()

        if isinstance(movies_data, list):
            print(f"✅ Retrieved {len(movies_data)} movies from Radarr.")
            return movies_data
        else:
            print(f"❌ Unexpected response type: {type(movies_data)}")
            return []
    except Exception as e:
        print(f"❌ Error fetching data from Radarr: {e}")
        return []


# ----------------------------------------
# Function to format date fields
# ----------------------------------------
def format_date(date_string):
    """Formats date strings to 'YYYY-MM-DD' format, removing time if present."""
    return date_string.split("T")[0] if date_string and "T" in date_string else date_string


# ----------------------------------------
# Fetch movie data from Radarr
# ----------------------------------------
movies = fetch_movies()

# Exit early if no movies found
if not movies:
    print("❌ No movies found. Exiting script.")
    exit()

# ----------------------------------------
# Define CSV field order
# ----------------------------------------
fieldnames = [
    'imdbId', 'tmdbId', 'Title', 'SortTitle', 'Year', 'Physical Release', 'InCinemas', 'Status',
    'Length', 'RunTime', 'HasFile', 'Quality', 'Resolution', 'Aspect Ratio', 'Subtitles',
    'Collection Title', 'Collection tmdbId', 'SizeOnDisk', 'MovieFile Path', 'YT TrailerId',
    'Overview', 'Website', 'Monitored', 'Certification', 'Tags', 'Genres', 'Original Language'
]

movies_written = 0  # Track number of successfully written movies

# ----------------------------------------
# Write movie data to CSV file
# ----------------------------------------
with open(csv_file_path, 'w', newline='', encoding='utf-8', errors="replace") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()  # Write CSV header row

    for movie in movies:
        try:
            # Extract nested data safely
            movie_file = movie.get("movieFile", {})
            media_info = movie_file.get("mediaInfo", {})
            quality_info = movie_file.get("quality", {}).get("quality", {})

            # Format subtitles field
            subtitles = media_info.get("subtitles", "")
            if isinstance(subtitles, list):
                subtitles = ", ".join([sub["language"] for sub in subtitles if isinstance(sub, dict)])

            # Handle collection data correctly (dictionary, not list)
            collection = movie.get("collection", {})
            collection_title = collection.get("title", "")
            collection_tmdbId = collection.get("tmdbId", "")

            # Get original Language name
            originalLanguage = movie.get("originalLanguage", {})
            original_language = originalLanguage.get("name", "")

            # Construct row with formatted data
            row = {
                "imdbId": movie.get("imdbId", ""),
                "tmdbId": movie.get("tmdbId", ""),
                "Title": movie.get("title", ""),
                "SortTitle": movie.get("sortTitle", ""),
                "Year": movie.get("year", ""),
                "Physical Release": format_date(movie.get("physicalRelease", "")),
                "InCinemas": format_date(movie.get("inCinemas", "")),
                "Status": movie.get("status", ""),
                # remove length
                "Length": movie.get("runtime", ""),
                "RunTime": media_info.get("runTime", ""),
                "HasFile": movie.get("hasFile", ""),
                "Quality": quality_info.get("name", ""),
                "Resolution": quality_info.get("resolution", ""),
                "Aspect Ratio": media_info.get("resolution", ""),
                "Subtitles": subtitles,
                "Collection Title": collection_title,
                "Collection tmdbId": collection_tmdbId,
                "SizeOnDisk": movie.get("sizeOnDisk", ""),
                "MovieFile Path": movie_file.get("path", ""),
                "YT TrailerId": movie.get("youTubeTrailerId", ""),
                "Overview": movie.get("overview", ""),
                "Website": movie.get("website", ""),
                "Monitored": movie.get("monitored", ""),
                "Certification": movie.get("certification", ""),
                "Tags": movie.get("tags", ""),
                "Genres": movie.get("genres", ""),
                "Original Language": original_language,

            }

            # Write row to CSV
            writer.writerow(row)
            csvfile.flush()  # Ensure data is written immediately
            movies_written += 1

        except Exception as e:
            print(f"⚠️ Error processing movie '{movie.get('title', 'Unknown')}': {e}")

# ----------------------------------------
# Script Completion Message
# ----------------------------------------
print(f"✅ {movies_written}/{len(movies)} movies successfully saved to: {csv_file_path}")
