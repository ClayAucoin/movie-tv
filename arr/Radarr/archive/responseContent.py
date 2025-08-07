"""
python3 "/mnt/c/_lib/data/_scripts_/py/_projects/Arr/Radarr/responseContent.py"
"""

import requests
import configRadarr  # Import Radarr config module

RADARR_URL = configRadarr.RADARR_URL
API_KEY = configRadarr.API_KEY
API_URL = f"{RADARR_URL}/api/v3/movie"

headers = {"X-Api-Key": API_KEY}

response = requests.get(API_URL, headers=headers)

# Print debugging information
print(f"Status Code: {response.status_code}")
print(f"Response Content: {response.text[:500]}")  # Print first 500 chars of response

# Check if response is valid JSON before parsing
if response.status_code == 200:
    try:
        movies_list = response.json()
        print(f"✅ Retrieved {len(movies_list)} movies from Radarr.")
    except requests.exceptions.JSONDecodeError as e:
        print(f"❌ JSON Decode Error: {e}")
else:
    print(f"❌ Error: Unable to fetch data from Radarr. Status code: {response.status_code}")
