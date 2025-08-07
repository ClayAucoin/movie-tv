"""
python "C:/_lib/data/_scripts_/py/_projects/ImportMetaData/importmetadata-4_working_b4_track_additions.py"

    TARGET_DIR = r"M:/Movie Test Dir 1/"

"""


import os
import csv
import platform
import time
import json
import sys
import ctypes
import subprocess
import concurrent.futures

def notify(title, message):
    ctypes.windll.user32.MessageBoxW(0, message, title, 0x40)

LOCK_FILE = 'script.lock'
if os.path.exists(LOCK_FILE):
    print("Another instance is already running. Exiting.")
    sys.exit()
with open(LOCK_FILE, 'w') as f:
    f.write(str(os.getpid()))

if platform.system() == "Windows":
    TARGET_DIR = r"M:/Movie Test Dir 1/"
    # TARGET_DIR = r"M:/Movies/"
    OUTPUT_CSV = r"E:/My Drive/_clay0aucoin@gmail.com/movies_on_m/movies_on_m.csv"
else:
    TARGET_DIR = r"/mnt/m/Movies/"
    OUTPUT_CSV = r"/mnt/c/Users/Administrator/Dropbox/movies_on_m"

VIDEO_EXTS = ('.mp4', '.mkv', '.avi', '.mov', '.flv')
FIELDS = [
    "Name of file", "Path of file", "Size Bytes", "Size KiB", "Size GiB", "File Type",
    "Movie BR", "Audio BR", "Audio Channels", "Audio Tracks", "Movie Name", "Collection",
    "Genre", "Edition", "Director", "IMDB ID", "Modified Time",
    "Video Track Titles", "Audio Track Titles"
]

#FIELDS = ["Name of file", "Path of file", "Size Bytes", "Size KiB", "Size GiB", "File Type","Movie BR", "Audio BR", "Audio Channels", "Audio Tracks", "Movie Name", "Collection","Genre", "Edition", "Director", "IMDB ID", "Modified Time"]

EXCLUDE_KEYWORDS = ["featurette", "trailer", "sample", "behind the scenes"]
EXCLUDE_DIR_KEYWORDS = ["Featurettes", "trailer", "sample", "behind the scenes"]
CACHE_FILE = OUTPUT_CSV.replace(".csv", "_cache.json")
TIMING_CSV = OUTPUT_CSV.replace(".csv", "_timing.csv")

file_cache = {}
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r') as f:
        file_cache = json.load(f)

verified_cache = {}
delCount = 0
for rel_path, sig in file_cache.items():
    full_path = os.path.join(TARGET_DIR, rel_path)
    if os.path.exists(full_path):
        verified_cache[rel_path] = sig
    else:
        delCount += 1
        print(f"[DELETED] [{delCount}] {rel_path} no longer exists")
file_cache = verified_cache

existing_rows = []
if os.path.exists(OUTPUT_CSV):
    with open(OUTPUT_CSV, 'r', encoding='utf8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing_rows.append(row)

def extract_metadata_cli(path, rel_path, stat, start_time):
    try:
        result = subprocess.run(
            ['mediainfo', '--Output=JSON', path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',  # ← Fix for UnicodeDecodeError
            timeout=10
        )
        data = json.loads(result.stdout)
        tracks = data.get("media", {}).get("track", [])

        row = {
            "Name of file": os.path.basename(path),
            "Path of file": os.path.dirname(path),
            "Size Bytes": stat.st_size,
            "Size KiB": round(stat.st_size / 1024, 2),
            "Size GiB": round(stat.st_size / (1024 ** 3), 4),
            "File Type": os.path.splitext(path)[1].lstrip('.'),
            "Movie BR": "", "Audio BR": "", "Audio Channels": "",
            "Audio Tracks": "", "Movie Name": "", "Collection": "",
            "Genre": "", "Edition": "", "Director": "", "IMDB ID": "",
            "Modified Time": float(stat.st_mtime)
        }

        channel_counts = []
        details = []

        for track in tracks:
            ttype = track.get('@type')
            if ttype == 'General':
                row["Movie Name"] = track.get("Movie", "")

                extra = track.get("extra", {})
                row["Collection"] = track.get("Law rating", "") or extra.get("LAW_RATING", "")
                row["Genre"] = track.get("Genre", "") or extra.get("GENRE", "")
                row["Edition"] = track.get("Composer", "") or extra.get("COMPOSER", "")
                row["Director"] = track.get("Director", "") or extra.get("DIRECTOR", "")
                row["IMDB ID"] = track.get("InternetMovieDatabase", "") or extra.get("IMDB_ID", "")

            elif ttype == 'Video':
                br = track.get("BitRate")
                if br:
                    row["Movie BR"] = round(int(br) / 1000, 2)
            elif ttype == 'Audio':
                ch = track.get("Channels", "")
                lang = track.get("Language", "")
                fmt = track.get("Format", "")
                br = track.get("BitRate")
                br_kbps = f"{int(float(br)) // 1000}kbps" if br else ""
                detail = ' '.join(filter(None, [lang, f"{ch}ch", fmt, br_kbps]))
                if ch:
                    channel_counts.append(str(ch))
                if detail:
                    details.append(detail)
                if not row["Audio BR"] and br:
                    row["Audio BR"] = round(float(br) / 1000, 2)

        row["Audio Channels"] = '+'.join(channel_counts)
        row["Audio Tracks"] = '; '.join(details)

        video_titles = []
        audio_titles = []

        for track in tracks:
            ttype = track.get("@type")
            title = track.get("Title", "")
            if title:
                if ttype == "Video":
                    video_titles.append(title)
                elif ttype == "Audio":
                    audio_titles.append(title)

        row["Video Track Titles"] = ", ".join(video_titles)
        row["Audio Track Titles"] = ", ".join(audio_titles)

        return rel_path, row, time.time() - start_time
    except Exception as e:
        print(f"[ERROR] {os.path.basename(path)} — {e}")
        return None, None, None

files_to_process = []
for root, _, files in os.walk(TARGET_DIR):
    if any(kw.lower() in root.lower() for kw in EXCLUDE_DIR_KEYWORDS):
        continue
    for fname in files:
        if any(kw.lower() in fname.lower() for kw in EXCLUDE_KEYWORDS):
            continue
        if not fname.lower().endswith(VIDEO_EXTS):
            continue
        path = os.path.join(root, fname)
        rel_path = os.path.relpath(path, TARGET_DIR)
        stat = os.stat(path)
        sig = {"size": stat.st_size, "mtime": stat.st_mtime}
        if rel_path in file_cache and file_cache[rel_path] == sig:
            continue
        files_to_process.append((path, rel_path, stat))

start_time = time.time()
updated_rows = []
with open(TIMING_CSV, 'w', newline='', encoding='utf8') as tf:
    time_writer = csv.DictWriter(tf, fieldnames=["Filename", "File Time (s)", "Total Elapsed (s)"])
    time_writer.writeheader()

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(extract_metadata_cli, p, r, s, time.time()): (p, r)
            for p, r, s in files_to_process
        }
        for future in concurrent.futures.as_completed(futures):
            rel_path, row, duration = future.result()
            if row:
                updated_rows.append(row)
                file_cache[rel_path] = {"size": row["Size Bytes"], "mtime": row["Modified Time"]}
                total_elapsed = time.time() - start_time
                time_writer.writerow({
                    "Filename": row["Name of file"],
                    "File Time (s)": f"{duration:.2f}",
                    "Total Elapsed (s)": f"{total_elapsed:.2f}"
                })
                print(f"[{len(updated_rows)}] {duration:.2f}s — {row['Name of file']}")

all_rows = existing_rows + updated_rows
final_rows = {}
for row in all_rows:
    rel_path = os.path.relpath(os.path.join(row["Path of file"], row["Name of file"]), TARGET_DIR)
    if os.path.exists(os.path.join(row["Path of file"], row["Name of file"])):
        final_rows[rel_path] = row

with open(OUTPUT_CSV, 'w', newline='', encoding='utf8') as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    writer.writeheader()
    for row in sorted(final_rows.values(), key=lambda r: r["Name of file"]):
        writer.writerow(row)

with open(CACHE_FILE, 'w') as f:
    json.dump(file_cache, f, indent=2)

total_time = time.time() - start_time
if delCount > 0:
    file_display = "file" if delCount == 1 else "files"
    print(f"🗑️ {delCount} {file_display} Deleted")

print(f"✅ Finished in {int(total_time)}s — {len(updated_rows)} updated, {len(file_cache)} total")
notify("Metadata Script", "✅ Script completed successfully.")
os.remove(LOCK_FILE)
