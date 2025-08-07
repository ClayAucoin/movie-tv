"""
python "C:/_lib/data/_scripts_/py/_projects/ImportMetaData/dump_mediainfo_json_full.py"
"""


import os
import json
import subprocess

# === Configuration ===
TARGET_DIR = r"M:\Movies"  # Change this to your target directory
OUTPUT_JSON = r"E:\My Drive\_clay0aucoin@gmail.com/movies_on_m\dump_media_metadata.json"  # Output location
# OUTPUT_CSV = r"E:/My Drive/_clay0aucoin@gmail.com/movies_on_m/movies_on_m.csv"

VIDEO_EXTS = ('.mp4', '.mkv', '.avi', '.mov', '.flv')
media_entries = []

# === Walk and process files ===
for root, _, files in os.walk(TARGET_DIR):
    for file in files:
        if not file.lower().endswith(VIDEO_EXTS):
            continue

        full_path = os.path.join(root, file)
        print(f"Processing: {file}")
        try:
            result = subprocess.run(
                ['mediainfo', '--Output=JSON', full_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                timeout=15
            )
            data = json.loads(result.stdout)
            data["source_file"] = full_path  # optionally add filename for reference
            media_entries.append(data)

        except Exception as e:
            print(f"[ERROR] {file} — {e}")

# === Write full dump to file ===
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(media_entries, f, indent=2)

print(f"\n✅ Done! Metadata for {len(media_entries)} files written to:\n{OUTPUT_JSON}")
