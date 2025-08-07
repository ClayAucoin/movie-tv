"""
python "C:/_lib/data/_scripts_/py/_projects/ImportMetaData/importmetadata-3_working_b4_optimization.py"

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


def extract_metadata(path):
    try:
        result = subprocess.run(['mediainfo', '--Output=JSON', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
        data = json.loads(result.stdout)
    except Exception as e:
        print(f"[ERROR] Failed to run mediainfo on {path} — {e}")
        return {}

    # Parse the JSON manually (just like you do now)
    # Extract only needed fields


def notify(title, message):
    ctypes.windll.user32.MessageBoxW(0, message, title, 0x40)

LOCK_FILE = 'script.lock'

if os.path.exists(LOCK_FILE):
    print("Another instance is already running. Exiting.")
    sys.exit()

with open(LOCK_FILE, 'w') as f:
    f.write(str(os.getpid()))

try:
    if platform.system() == "Windows":
        #TARGET_DIR = r"M:/Movie Test Dir 1/"
        TARGET_DIR = r"M:/Movies/"
        OUTPUT_CSV = r"E:/My Drive/_clay0aucoin@gmail.com/movies_on_m/movies_on_m.csv"
    else:
        TARGET_DIR = r"/mnt/m/Movies/"
        OUTPUT_CSV = r"/mnt/c/Users/Administrator/Dropbox/movies_on_m"

    VIDEO_EXTS = {'.mp4', '.mkv', '.avi', '.mov', '.fll'}

    FIELDS = [
        "Name of file", "Path of file", "Size Bytes", "Size KiB", "Size GiB", "File Type",
        "Movie BR", "Audio BR", "Audio Channels", "Audio Tracks", "Movie Name", "Collection",
        "Genre", "Edition", "Director", "IMDB ID", "Modified Time"
    ]

    EXCLUDE_KEYWORDS = ["featurette", "trailer", "sample", "behind the scenes"]
    EXCLUDE_DIR_KEYWORDS = ["Featurettes", "trailer", "sample", "behind the scenes"]

    def extract_metadata(file_path):
        info = MediaInfo.parse(file_path)
        base = os.path.basename(file_path)
        root, ext = os.path.splitext(base)
        st = os.stat(file_path)
        size = st.st_size

        row = {
            "Name of file": base,
            "Path of file": os.path.dirname(file_path),
            "Size Bytes": size,
            "Size KiB": round(size / 1024, 2),
            "Size GiB": round(size / (1024 ** 3), 4),
            "File Type": ext.lstrip('.'),
            "Movie BR": "", "Audio BR": "", "Audio Channels": "",
            "Audio Tracks": "", "Movie Name": "", "Collection": "",
            "Genre": "", "Edition": "", "Director": "", "IMDB ID": "",
            "Modified Time": float(st.st_mtime)
        }

        general = next((t for t in info.tracks if t.track_type == 'General'), None)
        videos = [t for t in info.tracks if t.track_type == 'Video']
        audios = [t for t in info.tracks if t.track_type == 'Audio']
        texts  = [t for t in info.tracks if t.track_type in ('Text', 'Subtitle')]

        if general:
            row.update({
                "Movie Name": general.movie_name or '',
                "Collection": general.law_rating or '',
                "Genre": general.genre or '',
                "Edition": general.composer or '',
                "Director": general.director or '',
                "IMDB ID": general.imdb_id or '',
            })

        if videos:
            vt = videos[0]
            br = vt.bit_rate and round(int(vt.bit_rate) / 1000, 2) or ''
            duration_hms = ''
            if vt.duration:
                total_sec = int(float(vt.duration) / 1000)
                hours = total_sec // 3600
                minutes = (total_sec % 3600) // 60
                seconds = total_sec % 60
                duration_hms = f"{hours}:{minutes:02}:{seconds:02}"

        channel_counts = []
        details = []
        for i, at in enumerate(audios):
            ch = str(at.channel_s or '').strip()
            lang = at.language or ''
            fmt  = at.format or ''
            try:
                br_value = int(float(at.bit_rate))
                br = f"{br_value // 1000}kbps"
            except (ValueError, TypeError):
                br = ''
            detail = ' '.join(filter(None, [lang, f"{ch}ch", fmt, br]))
            if ch:
                channel_counts.append(ch)
            if detail:
                details.append(detail)
            if i == 0 and at.bit_rate:
                try:
                    row["Audio BR"] = round(float(at.bit_rate) / 1000, 2)
                except (ValueError, TypeError):
                    row["Audio BR"] = ''

        row["Audio Channels"] = '+'.join(channel_counts)
        row["Audio Tracks"]   = '; '.join(details)

        return row

    CACHE_FILE = OUTPUT_CSV.replace(".csv", "_cache.json")
    TIMING_CSV = OUTPUT_CSV.replace(".csv", "_timing.csv")

    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            file_cache = json.load(f)
    else:
        file_cache = {}

    existing_rows = []
    if os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, 'r', encoding='utf8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_rows.append(row)

    # Remove deleted files
    delCount = 0
    verified_cache = {}
    for rel_path, sig in file_cache.items():
        full_path = os.path.join(TARGET_DIR, rel_path)
        if os.path.exists(full_path):
            verified_cache[rel_path] = sig
        else:
            delCount += 1
            print(f"[DELETED] [{delCount}] {rel_path} no longer exists")

    file_cache = verified_cache
    updated_rows = []
    deduped_paths = set()
    start_time = time.time()
    count = 0

    with open(TIMING_CSV, 'w', newline='', encoding='utf8') as timefile:
        time_writer = csv.DictWriter(timefile, fieldnames=["Filename", "File Time (s)", "Total Elapsed (s)"])
        time_writer.writeheader()

        for root, _, files in os.walk(TARGET_DIR):
            if any(kw.lower() in root.lower() for kw in EXCLUDE_DIR_KEYWORDS):
                continue

            for fname in files:
                if any(kw.lower() in fname.lower() for kw in EXCLUDE_KEYWORDS):
                    continue

                ext = os.path.splitext(fname)[1].lower()
                if ext in VIDEO_EXTS:
                    path = os.path.join(root, fname)
                    rel_path = os.path.relpath(path, TARGET_DIR)

                    stat = os.stat(path)
                    sig_key = {"size": stat.st_size, "mtime": stat.st_mtime}

                    if rel_path in file_cache and file_cache[rel_path] == sig_key:
                        continue

                    file_start = time.time()
                    try:
                        row = extract_metadata(path)
                        updated_rows.append(row)
                        file_cache[rel_path] = sig_key
                        deduped_paths.add(rel_path)

                        count += 1
                        file_duration = time.time() - file_start
                        total_elapsed = time.time() - start_time
                        time_writer.writerow({
                            "Filename": fname,
                            "File Time (s)": f"{file_duration:.2f}",
                            "Total Elapsed (s)": f"{total_elapsed:.2f}"
                        })

                        total_str = f"{int(total_elapsed // 60)}m {int(total_elapsed % 60)}s" if total_elapsed >= 60 else f"{int(total_elapsed)}s"
                        print(f"[{count}] {total_str}   |   {file_duration:.2f}s   —   {fname}")

                    except Exception as e:
                        print(f"[ERROR] {fname} — {e}")
                        notify("Metadata Script", "❌ An error occurred. Please check the log.")

    # Deduplicate and merge
    all_rows = existing_rows + updated_rows
    final_rows = {}
    for row in all_rows:
        rel_path = os.path.relpath(os.path.join(row["Path of file"], row["Name of file"]), TARGET_DIR)
        if os.path.exists(os.path.join(row["Path of file"], row["Name of file"])):
            final_rows[rel_path] = row

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDS)
        writer.writeheader()
        for row in sorted(final_rows.values(), key=lambda r: r["Name of file"]):
            writer.writerow(row)

    with open(CACHE_FILE, 'w') as f:
        json.dump(file_cache, f, indent=2)

    total_time = time.time() - start_time
    if delCount>0:
        if delCount>1:
            fileDisplay = "files"
        else:
            fileDisplay = "file"
        print(f"🗑️ {delCount} {fileDisplay} Deleted")
    print(f"✅ Finished in {int(total_time)}s — {len(updated_rows)} updated, {len(file_cache)} total")
    notify("Metadata Script", "✅ Script completed successfully.")

finally:
    os.remove(LOCK_FILE)