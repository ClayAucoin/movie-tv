"""
python3 "/mnt/c/_lib/data/_scripts_/py/_projects/Arr/Radarr/getFieldListFromAll.py"
"""

import requests
import json
import sys, os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # .../movie-tv
sys.path.append(PROJECT_ROOT)
from arr.config.config import RADARR_URL, RADARR_API_KEY, RADARR_API_URL

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define the file path in the same directory as the script
json_file_path = os.path.join(script_dir, "radarr_series_data.json")

# Include API key in headers
headers = {"X-Api-Key": RADARR_API_KEY}

# Make the API request
response = requests.get(RADARR_API_URL, headers=headers)

if response.status_code == 200:
    try:
        series_list = response.json()

        # Save the response data to the script's directory
        with open(json_file_path, "w") as outfile:
            json.dump(series_list, outfile, indent=4)  # Save with indentation for readability

        print(f"✅ Data saved to: {json_file_path}")
    except Exception as e:
        print(f"❌ Error parsing JSON: {e}")
else:
    print(f"❌ Error: Unable to fetch data. Status code: {response.status_code}")
