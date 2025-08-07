"""
python "C:/_lib/data/_scripts_/py/_projects/ImportMetaData/importmetadata_OUTCOME.py"

    TARGET_DIR = r"M:/Movie Test Dir 1/"

"""


import os
import csv
import platform
import time
from pymediainfo import MediaInfo
import json
import sys

LOCK_FILE = 'script.lock'

if os.path.exists(LOCK_FILE):
    print("Another instance is already running. Exiting.")
    sys.exit()

with open(LOCK_FILE, 'w') as f:
    f.write(str(os.getpid()))

try:
    if platform.system() == "Windows":
        TARGET_DIR = r"M:/Movie Test Dir 1/"
        #TARGET_DIR = r"M:/Movies/"
        OUTPUT_CSV = r"E:/My Drive/_clay0aucoin@gmail.com/movies_on_m/movies_on_m.csv"
    else:
        TARGET_DIR = r"/mnt/m/Movies/"
        OUTPUT_CSV = r"/mnt/c/Users/Administrator/Dropbox/movies_on_m"

    VIDEO_EXTS = {'.mp4', '.mkv', '.avi', '.mov', '.fll'}

    FIELDS = [
        "Name of file", "Path of file", "Size Bytes", "Size KiB", "Size GiB", "File Type",
        "Length", "Released", "Width", "Height", "Movie BR", "Audio BR",
        "Audio Channels", "Audio Tracks", "Subtitle Tracks", "Movie Name", "Collection",
        "Genre", "Description", "Edition", "Director", "Modified Time"
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
            "Length": "", "Released": "", "Width": "", "Height": "",
            "Movie BR": "", "Audio BR": "", "Audio Channels": "",
            "Audio Tracks": "", "Subtitle Tracks": "", "Movie Name": "", "Collection": "",
            "Genre": "", "Description": "", "Edition": "", "Director": "",
            "Modified Time": float(st.st_mtime)
        }

        general = next((t for t in info.tracks if t.track_type == 'General'), None)
        videos = [t for t in info.tracks if t.track_type == 'Video']
        audios = [t for t in info.tracks if t.track_type == 'Audio']
        texts = [t for t in info.tracks if t.track_type in ('Text', 'Subtitle')]

        if general:
            row.update({
                "Movie Name": general.movie_name or '',
                "Collection": general.law_rating or '',
                "Genre": general.genre or '',
                "Description": general.description or '',
                "Edition": general.composer or '',
                "Director": general.director or '',
                "Released": general.released_date or general.tagged_date or ''
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

            row.update({
                "Length": duration_hms,
                "Width": vt.width or '',
                "Height": vt.height or '',
                "Movie BR": br
            })

        channel_counts = []
        details = []
        for i, at in enumerate(audios):
            ch = str(at.channel_s or '').strip()
            lang = at.language or ''
            fmt = at.format or ''
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
        row["Audio Tracks"] = '; '.join(details)

        subs = []
        for st in texts:
            lang = st.language or ''
            fmt = st.format or ''
            detail = ' '.join(filter(None, [lang, fmt]))
            if detail:
                subs.append(detail)
        row["Subtitle Tracks"] = '; '.join(subs)

        return row

    CACHE_FILE = OUTPUT_CSV.replace(".csv", "_cache.json")
    TIMING_CSV = OUTPUT_CSV.replace(".csv", "_timing.csv")

    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            file_cache = json.load(f)
    else:
        file_cache = {}

    existing_rows = []
    existing_index = {}

    if os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, 'r', encoding='utf8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                full_path = os.path.join(row["Path of file"], row["Name of file"])
                if os.path.exists(full_path):
                    rel_path = os.path.relpath(full_path, TARGET_DIR)
                    existing_rows.append(row)
                    existing_index[rel_path] = row

    rev_cache = {
        f"{sig['size']}-{sig['mtime']}": path
        for path, sig in file_cache.items()
    }

    updated_rows = {}
    start_time = time.time()
    count = 0

    with open(TIMING_CSV, 'w', newline='', encoding='utf8') as timefile:
        time_writer = csv.DictWriter(timefile, fieldnames=["Filename", "File Time (s)", "Total Elapsed (s)"])
        time_writer.writeheader()

        all_files = set()

        for root_dir, dirs, files in os.walk(TARGET_DIR):
            if any(kw.lower() in root_dir.lower() for kw in EXCLUDE_DIR_KEYWORDS):
                continue

            for fname in files:
                if any(kw.lower() in fname.lower() for kw in EXCLUDE_KEYWORDS):
                    continue

                ext = os.path.splitext(fname)[1].lower()
                if ext in VIDEO_EXTS:
                    path = os.path.join(root_dir, fname)
                    rel_path = os.path.relpath(path, TARGET_DIR)
                    all_files.add(rel_path)
                    stat = os.stat(path)

                    file_signature = {
                        "size": stat.st_size,
                        "mtime": stat.st_mtime
                    }
                    sig_key = f"{file_signature['size']}-{file_signature['mtime']}"
                    seen_rel_path = rev_cache.get(sig_key)

                    if seen_rel_path == rel_path:
                        continue

                    if seen_rel_path and seen_rel_path in existing_index:
                        old_row = existing_index.pop(seen_rel_path)
                        existing_rows.remove(old_row)
                        del file_cache[seen_rel_path]

                    file_start = time.time()
                    try:
                        row = extract_metadata(path)
                        file_cache[rel_path] = file_signature
                        updated_rows[rel_path] = row

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
                        print(f"[ERROR] Skipping {fname} — {e}")
                        continue

    # Remove missing files from cache and existing_rows
    for rel_path in list(file_cache):
        if rel_path not in all_files:
            print(f"[REMOVED] {rel_path}")
            file_cache.pop(rel_path, None)
            if rel_path in existing_index:
                existing_rows.remove(existing_index[rel_path])

    for rel_path, new_row in updated_rows.items():
        new_sig = file_cache[rel_path]
        existing_rows = [
            row for row in existing_rows
            if not (
                int(row.get("Size Bytes", -1)) == new_sig["size"] and
                abs(float(row.get("Modified Time", 0.0)) - new_sig["mtime"]) < 2
            )
        ]
        existing_rows.append(new_row)

    deduped = {}
    for row in reversed(existing_rows):
        rel_path = os.path.relpath(os.path.join(row["Path of file"], row["Name of file"]), TARGET_DIR)
        if rel_path not in deduped:
            deduped[rel_path] = row

    existing_rows = sorted(deduped.values(), key=lambda r: r["Name of file"])

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDS)
        writer.writeheader()
        for row in existing_rows:
            writer.writerow(row)

    with open(CACHE_FILE, 'w') as f:
        json.dump(file_cache, f, indent=2)

    if 'total_str' not in locals():
        total_str = "0s"

    print(f"\n✅ Processed {count} new/updated files in {total_str}")
    print(f"CSV written to {OUTPUT_CSV}")
    print(f"Timing log written to {TIMING_CSV}")
    print(f"Cache file updated at {CACHE_FILE}")

finally:
    os.remove(LOCK_FILE)
