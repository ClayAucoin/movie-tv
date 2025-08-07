"""
python3 "/mnt/c/_lib/data/_scripts_/py/_projects/Arr/Radarr/getFieldListFromAll.py"
"""

import requests
import json
import os
import configRadarr  # Import the config module

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define the file path in the same directory as the script
json_file_path = os.path.join(script_dir, "radarr_series_data.json")

RADARR_URL = configRadarr.RADARR_URL
API_KEY = configRadarr.API_KEY
API_URL = configRadarr.API_URL

# Include API key in headers
headers = {"X-Api-Key": API_KEY}

# Make the API request
response = requests.get(API_URL, headers=headers)

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
