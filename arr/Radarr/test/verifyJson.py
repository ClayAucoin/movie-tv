"""
python3 "/mnt/c/_lib/data/_scripts_/py/_projects/Arr/Radarr/test/verifyJson.py"
"""

import json
import os

# Get the script directory and JSON file path
script_dir = os.path.dirname(os.path.abspath(__file__))
json_file_path = os.path.join(script_dir, "radarr_series_data.json")

# Load the JSON data
with open(json_file_path, "r", encoding="utf-8") as infile:
    data = json.load(infile)

# Print the first few entries to confirm format
if isinstance(data, list):
    print(f"✅ JSON is a list with {len(data)} movies.")
    print(json.dumps(data[:2], indent=4))  # Print first 2 movies
else:
    print(f"❌ JSON format issue! Expected a list but got {type(data)}.")
    print("First 500 characters of JSON:", json.dumps(data)[:500])
