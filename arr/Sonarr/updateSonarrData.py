# python "C:/Users/Administrator/projects/movie-tv/arr/Sonarr/updateSonarrData.py"
# python3 "/mnt/c/_lib/data/_scripts_/py/_projects/Arr/Sonarr/updateSonarrData.py"

import requests
import csv
from datetime import datetime
import platform
import ctypes
#import configSonarr  # Import the config module

import os, sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # adds .../arr to path
from config.config import SONARR_URL, SONARR_API_KEY, RADARR_URL, RADARR_API_KEY

# 🔹 Update these values
SONARR_URL = config.config.SONARR_URL
SONARR_API_KEY = config.SONARR_API_KEY


# Determine file path based on the operating system
if platform.system() == "Windows":
    # CSV_FILE_PATH = "C:/Users/Administrator/Dropbox/arr/sonarr.csv"  # Dropbox Windows Path to save CSV file
    CSV_FILE_PATH = "E:/My Drive/_clay0aucoin@gmail.com/movies_on_m/arr/sonarr.csv"
else:
    CSV_FILE_PATH = "/mnt/c/Users/Administrator/Dropbox/arr/sonarr.csv"  # Dropbox Linux/WSL Path

print(f"Using CSV file path: {CSV_FILE_PATH}")

def notify(title, message):
    ctypes.windll.user32.MessageBoxW(0, message, title, 0x40)

def get_series_data():
    """Fetches series data from Sonarr API."""
    url = f"{SONARR_URL}/api/v3/series"
    headers = {"X-Api-Key": SONARR_API_KEY}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Error fetching data: {response.status_code}, {response.text}")

    print(f"✅ Retrieved {len(response.json())} series from Sonarr.")  # Debugging line
    return response.json()


def extract_airing_day(airing_time):
    """Extracts the airing day of the week from the provided airing time."""
    if airing_time:
        try:
            airing_datetime = datetime.strptime(airing_time, "%Y-%m-%dT%H:%M:%SZ")
            airing_day = airing_datetime.strftime("%A")  # Get full weekday name (e.g., "Monday")
            return airing_day
        except ValueError as e:
            print(f"Error extracting airing day: {e}")
            return "Unknown"
    else:
        return "Unknown"  # Return "Unknown" if airing_time is None or missing


def extract_airing_time(airing_time):
    """Extracts the airing day of the week from the provided airing time."""
    if airing_time:
        try:
            airing_datetime = datetime.strptime(airing_time, "%Y-%m-%dT%H:%M:%SZ")
            airing_day = airing_datetime.strftime("%H")  # Get full weekday name (e.g., "01, 23")
            return airing_day
        except ValueError as e:
            print(f"Error extracting airing time: {e}")
            return "Unknown"
    else:
        return "Unknown"  # Return "Unknown" if airing_time is None or missing


def get_season_data(series):
    """Retrieves the latest season data from a given series."""
    season_data = series.get("seasons", [])
    if not season_data:
        return []

    # Find the most recent season based on season number
    current_season = max(season_data, key=lambda x: x["seasonNumber"])
    print(f"Found current season for {series['title']}: Season {current_season['seasonNumber']}")

    # Extract episode statistics from the season
    statistics = current_season.get("statistics", {})
    total_episodes = statistics.get("episodeCount", 0)  # Default to 0 if not found
    print(f"Total episodes for {series['title']} Season {current_season['seasonNumber']}: {total_episodes}")

    return [current_season]  # Returning the most recent season data


def update_csv():
    """Fetches series data and writes it to a CSV file."""
    series_list = get_series_data()  # Fetch the series data from Sonarr

    with open(CSV_FILE_PATH, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Title', 'Sort Title', 'Year', 'Current Season', 'Latest Season Count',
                      'File Count', 'Last Aired', 'Next Airing', 'Next Airing Time',
                      'Previous Airing', 'Previous Airing Time', 'Status', 'Episode Count',
                      'Path', 'IMDB ID', 'titleSlug']
        writer = csv.writer(csvfile)
        writer.writerow(fieldnames)  # Write CSV header

        for series in series_list:
            title = series["title"]  # Extract series title
            sort_title = series["sortTitle"]  # Extract sort title
            year = series["year"]  # Extract series release year
            status = series["status"]  # Extract series status (continuing, ended, etc.)
            path = series["path"]  # Extract series status (continuing, ended, etc.)
            imdb_id = series.get("imdbId", "")  # Extract imdb id
            title_slug = series["titleSlug"]  # Extract title slug
            last_aired = series.get("lastAired")  # Use .get() to safely access the key
            next_airing = series.get("nextAiring")  # Use .get() to safely access the key
            previous_airing = series.get("previousAiring")  # Use .get() to safely access the key

            aired_last = extract_airing_day(last_aired)  # Extract the airing day if available
            next_airing_time = extract_airing_time(next_airing)  # Extract the airing day if available
            previous_airing_time = extract_airing_time(previous_airing)  # Extract the airing day if available

            # Get the latest season data
            latest_season = series["seasons"][-1]  # Get last item in the seasons list
            latest_season_count = latest_season["statistics"]["totalEpisodeCount"]  # Get episode count
            episode_count = latest_season["statistics"]["episodeCount"]  # Get episode count
            file_count = latest_season["statistics"]["episodeFileCount"]  # Get file count
            current_season = series["statistics"]["seasonCount"]  # Get total season count


            # Write the extracted data to the CSV file
            writer.writerow(
                [
                    title, sort_title, year, current_season, latest_season_count, file_count, aired_last,
                    next_airing, next_airing_time, previous_airing, previous_airing_time, status, episode_count,
                    path, imdb_id, title_slug
                ]
            )

    print("✅ CSV updated successfully.")
    # notify("Metadata Script", f"✅ Sonarr\n\nCSV updated successfully.")


# 🔹 Run the Script
if __name__ == "__main__":
    update_csv()
