"""
python "C:/_lib/data/_scripts_/py/_projects/ImportMetaData/dump_mediainfo_json_single.py" "M:\Movies\The Lord of the Rings The Fellowship of the Ring (2001)\The Lord of the Rings The Fellowship of the Ring (2001) [Extended Cut, Commentary, 2160p, 7.1].mkv"
"""


import subprocess
import json
import sys

# Replace with your file path or pass it as an argument
file_path = sys.argv[1] if len(sys.argv) > 1 else r"M:\Movies\Some Movie (2024).mkv"

try:
    result = subprocess.run(
        ['mediainfo', '--Output=JSON', file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding='utf-8',
        timeout=10
    )

    # Print STDERR if any (e.g., if file not found)
    if result.stderr:
        print("STDERR:", result.stderr.strip())

    # Try to parse and pretty print JSON
    data = json.loads(result.stdout)
    print(json.dumps(data, indent=2))

except Exception as e:
    print(f"Error running mediainfo: {e}")
