"""
python3 "/mnt/c/_lib/data/_scripts_/py/_projects/Arr/Radarr/test/extractFromJson.py"
"""

import json
import os

# Get the script directory and JSON file path
script_dir = os.path.dirname(os.path.abspath(__file__))
json_file_path = os.path.join(script_dir, "radarr_series_data.json")

# Load the JSON data
with open(json_file_path, "r", encoding="utf-8") as infile:
    data = json.load(infile)

# Print the structure of the first movie entry
if isinstance(data, list) and len(data) > 0:
    print(json.dumps(data[0], indent=4))  # Pretty-print the first movie
else:
    print("❌ JSON file is empty or not a list.")
