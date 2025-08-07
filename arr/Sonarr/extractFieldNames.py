"""
python3 "/mnt/c/_lib/data/_scripts_/py/_projects/Arr/Sonarr/extractFieldNames.py"
"""

import requests
import json
import os
import configSonarr  # Import the config module

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
fields_file_path = os.path.join(script_dir, "sonarr_available_fields.txt")  # Save in the same directory as the script

SONARR_URL = configSonarr.SONARR_URL
API_KEY = configSonarr.API_KEY
API_URL = f"{SONARR_URL}/api/v3/series"

# Include API key in headers
headers = {"X-Api-Key": API_KEY}

# Make the API request
response = requests.get(API_URL, headers=headers)

if response.status_code == 200:
    try:
        series_list = response.json()

        # Get first series entry to extract field names
        if series_list:
            first_series = series_list[0]

            def extract_keys(data, prefix=""):
                """ Recursively extract keys from JSON data. """
                fields = []
                if isinstance(data, dict):
                    for key, value in data.items():
                        new_prefix = f"{prefix}.{key}" if prefix else key
                        fields.append(new_prefix)
                        fields.extend(extract_keys(value, new_prefix))  # Recursion for nested fields
                elif isinstance(data, list) and data:  # If it's a list, process the first item
                    fields.extend(extract_keys(data[0], prefix + "[]"))
                return fields

            field_names = extract_keys(first_series)

            # Save field names to a file for easy reference
            with open(fields_file_path, "w", encoding="utf-8") as outfile:
                outfile.write("\n".join(field_names))

            print(f"✅ Available fields saved to: {fields_file_path}")  # Confirm file save
            # print("\n".join(field_names))  # Print field names to console for preview

    except Exception as e:
        print(f"❌ Error parsing JSON: {e}")
else:
    print(f"❌ Error: Unable to fetch data. Status code: {response.status_code}")
