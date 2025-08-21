"""
python "C:/Users/Administrator/projects/movie-tv/importMetaData/importmetadata.py"

    TARGET_DIR = r"M:/Movie Test Dir 1/"
    TARGET_DIR = r"M:/Movies/"

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
from datetime import datetime

# ---------------------------
# Config & Utilities
# ---------------------------

# Check if the script is running with the "/task_scheduler" argument
is_task_scheduler = '/task_scheduler' in sys.argv

def notify(title, message):
    try:
        if not is_task_scheduler:
            ctypes.windll.user32.MessageBoxW(0, message, title, 0x40)
    except Exception:
        # If not on Windows or GUI not available, ignore
        pass

def ensure_dir(path):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def log_setup(output_csv):
    log_path = output_csv.replace(".csv", "_run.log")
    ensure_dir(output_csv)
    return log_path

def log(msg, *, also_print=True):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as lf:
            lf.write(line + "\n")
    except Exception:
        # last resort: ignore logging failure
        pass
    if also_print:
        print(line, flush=True)

# ---------------------------
# Lock file (single instance)
# ---------------------------

LOCK_FILE = 'script.lock'
if os.path.exists(LOCK_FILE):
    print("Another instance is already running. Exiting.", flush=True)
    sys.exit()

with open(LOCK_FILE, 'w') as f:
    f.write(str(os.getpid()))

try:
    # ---------------------------
    # Paths
    # ---------------------------
    if platform.system() == "Windows":
        OUTPUT_CSV = r"E:/My Drive/__clay0aucoin@gmail.com/movies_on_m/movies_on_m.csv"

        # original directories
        TARGET_DIR = r"\\192.168.1.205\Media\Movies"  # <-- replace with your share
        M_LETTER = r"M:\Movies"
        UNC_FALLBACK = r"\\192.168.1.205\Media\Movies"  # <-- replace

        # testing directories
        # TARGET_DIR = r"\\192.168.1.205\Media\Movie Test Dir 1"  # <-- replace with your share
        # M_LETTER = r"M:\Movie Test Dir 1"
        # UNC_FALLBACK = r"\\192.168.1.205\Media\Movie Test Dir 1"  # <-- replace

        TARGET_DIR = M_LETTER if os.path.exists(M_LETTER) else UNC_FALLBACK
    else:
        TARGET_DIR = r"/mnt/m/Movies/"
        OUTPUT_CSV = r"/mnt/c/Users/Administrator/Dropbox/movies_on_m"

    ensure_dir(OUTPUT_CSV)
    LOG_FILE = log_setup(OUTPUT_CSV)
    TIMING_CSV = OUTPUT_CSV.replace(".csv", "_timing.csv")
    CACHE_FILE = OUTPUT_CSV.replace(".csv", "_cache.json")

    # ---------------------------
    # Start Banner
    # ---------------------------
    log("=== Metadata extraction started ===")
    log(f"Working directory: {os.getcwd()}")
    log(f"Target dir: {TARGET_DIR}")
    log(f"Output CSV: {OUTPUT_CSV}")
    log(f"Timing CSV: {TIMING_CSV}")
    log(f"Cache file: {CACHE_FILE}")

    # ---------------------------
    # Settings
    # ---------------------------
    VIDEO_EXTS = ('.mp4', '.mkv', '.avi', '.mov', '.flv')
    FIELDS = [
        "Name of file", "Path of file", "Size Bytes", "Size KiB", "Size GiB", "File Type",
        "Movie BR", "Audio BR", "Audio Channels", "Audio Tracks", "Movie Name", "Collection",
        "Genre", "Edition", "Director", "IMDB ID", "Modified Time",
        "Video Track Titles", "Audio Track Titles",
        "Video Tracks", "Audio Tracks JSON", "Sub Titles", "Chapters"
    ]
    EXCLUDE_KEYWORDS = ["featurette", "trailer", "sample", "behind the scenes"]
    EXCLUDE_DIR_KEYWORDS = ["Featurettes", "trailer", "sample", "behind the scenes"]

    # ---------------------------
    # Locate mediainfo
    # ---------------------------
    MEDIAINFO = r"C:\Tools\MediaInfo\mediainfo.exe"  # <-- set to your actual path
    # MEDIAINFO = os.environ.get("MEDIAINFO_PATH") or MEDIAINFO  # optional env override

    try:
        _chk = subprocess.run(
            [MEDIAINFO, "--Version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system()=="Windows" else 0
        )
        if _chk.returncode != 0:
            log(f"Warning: mediainfo returned code {_chk.returncode}. stderr={_chk.stderr.strip()}")
    except FileNotFoundError:
        msg = ("mediainfo CLI not found. Install it or set MEDIAINFO_PATH env var to full path, "
               "e.g., C:\\Tools\\MediaInfo\\mediainfo.exe")
        log(msg)
        notify("Metadata Script", msg)
        raise

    # ---------------------------
    # Load cache & existing CSV
    # ---------------------------
    file_cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                file_cache = json.load(f)
        except Exception as e:
            log(f"Cache load error: {e} (continuing with empty cache)")

    # prune deleted
    verified_cache = {}
    delCount = 0
    for rel_path, sig in file_cache.items():
        full_path = os.path.join(TARGET_DIR, rel_path)
        if os.path.exists(full_path):
            verified_cache[rel_path] = sig
        else:
            delCount += 1
            log(f"[DELETED] [{delCount}] {rel_path} no longer exists")
    file_cache = verified_cache

    existing_rows = []
    if os.path.exists(OUTPUT_CSV):
        try:
            with open(OUTPUT_CSV, 'r', encoding='utf8', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing_rows.append(row)
            log(f"Loaded {len(existing_rows)} existing rows from CSV")
        except Exception as e:
            log(f"Error reading existing CSV: {e}")

    # ---------------------------
    # Extraction helpers
    # ---------------------------
    def extract_metadata_cli(path, rel_path, stat, start_time):
        try:
            result = subprocess.run(
                [MEDIAINFO, '--Output=JSON', path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                #timeout=20,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system()=="Windows" else 0
            )

            if result.returncode != 0 or not result.stdout.strip():
                log(f"[mediainfo ERROR] {os.path.basename(path)} rc={result.returncode} stderr={result.stderr.strip()}")
                return None, None, None

            try:
                data = json.loads(result.stdout)
            except Exception as je:
                log(f"[JSON ERROR] {os.path.basename(path)} — {je}. STDERR: {result.stderr.strip()}")
                return None, None, None

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
                "Modified Time": float(stat.st_mtime),
                "Video Track Titles": "", "Audio Track Titles": "",
                "Video Tracks": "", "Audio Tracks JSON": "",
                "Sub Titles": "", "Chapters": ""
            }

            video_tracks, audio_tracks, text_tracks = [], [], []
            channel_counts = []
            details = []

            for track in tracks:
                ttype = track.get('@type')

                if ttype == 'General':
                    row["Movie Name"] = track.get("Movie", "") or track.get("Title", "")
                    extra = track.get("extra", {})
                    row["Collection"] = track.get("Law rating", "") or extra.get("LAW_RATING", "")
                    row["Genre"] = track.get("Genre", "") or extra.get("GENRE", "")
                    row["Edition"] = track.get("Composer", "") or extra.get("COMPOSER", "")
                    row["Director"] = track.get("Director", "") or extra.get("DIRECTOR", "")
                    row["IMDB ID"] = track.get("InternetMovieDatabase", "") or extra.get("IMDB_ID", "")

                    # Chapters (Menu.extra)
                    for t in tracks:
                        if t.get('@type') == "Menu" and "extra" in t:
                            try:
                                row["Chapters"] = json.dumps({"@type": "Menu", "extra": t["extra"]}, ensure_ascii=False)
                            except Exception:
                                row["Chapters"] = ""

                elif ttype == 'Video':
                    # Build "mini JSON" for video
                    subset = {}
                    for k in ("@type", "StreamOrder", "ID", "Format", "Format_Level",
                              "HDR_Format_Compatibility", "CodecID", "BitRate", "Width",
                              "Height", "DisplayAspectRatio", "Title", "Language",
                              "Default", "Forced"):
                        if k in track:
                            subset[k] = track[k]
                    video_tracks.append(subset)

                    br = track.get("BitRate")
                    if br:
                        try:
                            row["Movie BR"] = round(int(float(br)) / 1000, 2)
                        except Exception:
                            pass

                elif ttype == 'Audio':
                    # Build "mini JSON" for audio
                    subset = {}
                    for k in ("@type", "@typeorder", "StreamOrder", "ID", "Format",
                              "Format_Commercial_IfAny", "CodecID", "BitRate", "Channels",
                              "ChannelPositions", "ChannelLayout", "SamplingRate",
                              "Compression_Mode", "Delay", "Video_Delay", "Title",
                              "Language", "Default", "Forced"):
                        if k in track:
                            subset[k] = track[k]
                    audio_tracks.append(subset)

                    ch = track.get("Channels", "")
                    lang = track.get("Language", "")
                    fmt = track.get("Format", "")
                    br = track.get("BitRate")
                    br_kbps = ""
                    try:
                        if br:
                            br_kbps = f"{int(float(br)) // 1000}kbps"
                    except Exception:
                        pass

                    detail = ' '.join(filter(None, [lang, f"{ch}ch" if ch else "", fmt, br_kbps]))
                    if ch:
                        channel_counts.append(str(ch))
                    if detail.strip():
                        details.append(detail.strip())
                    if not row["Audio BR"] and br:
                        try:
                            row["Audio BR"] = round(float(br) / 1000, 2)
                        except Exception:
                            pass

                elif ttype == 'Text':
                    subset = {}
                    for k in ("@type", "@typeorder", "StreamOrder", "ID", "Format", "CodecID",
                              "Language", "Default", "Forced"):
                        if k in track:
                            subset[k] = track[k]
                    text_tracks.append(subset)

            # Finalize computed fields
            row["Audio Channels"] = '+'.join(channel_counts)
            row["Audio Tracks"] = '; '.join(details)
            row["Video Tracks"] = json.dumps(video_tracks, ensure_ascii=False)
            row["Audio Tracks JSON"] = json.dumps(audio_tracks, ensure_ascii=False)
            row["Sub Titles"] = json.dumps(text_tracks, ensure_ascii=False)

            # Titles
            row["Video Track Titles"] = ", ".join(
                [t.get("Title", "") for t in tracks if t.get("@type") == "Video" and t.get("Title")]
            )
            row["Audio Track Titles"] = ", ".join(
                [t.get("Title", "") for t in tracks if t.get("@type") == "Audio" and t.get("Title")]
            )

            return rel_path, row, time.time() - start_time

        except Exception as e:
            log(f"[ERROR] {os.path.basename(path)} — {e}")
            return None, None, None

    # ---------------------------
    # Gather files to process
    # ---------------------------
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
            try:
                stat = os.stat(path)
            except FileNotFoundError:
                log(f"[SKIP] File vanished: {path}")
                continue
            sig = {"size": stat.st_size, "mtime": stat.st_mtime}
            if rel_path in file_cache and file_cache[rel_path] == sig:
                continue
            files_to_process.append((path, rel_path, stat))

    #log(f"Discovered {len(files_to_process)} files to process")
    log(f"Discovered {len(files_to_process)} files to process in: {TARGET_DIR}")
    if not files_to_process:
        log("No new files or any changed files.")

    # ---------------------------
    # Process in parallel
    # ---------------------------
    start_time = time.time()
    updated_rows = []
    ensure_dir(TIMING_CSV)
    with open(TIMING_CSV, 'w', newline='', encoding='utf8') as tf:
        time_writer = csv.DictWriter(tf, fieldnames=["Filename", "File Time (s)", "Total Elapsed (s)"])
        time_writer.writeheader()

        max_workers = min(8, max(1, os.cpu_count() or 4))
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(extract_metadata_cli, p, r, s, time.time()): (p, r)
                for p, r, s in files_to_process
            }
            for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
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
                    log(f"[{len(updated_rows)}] {duration:.2f}s — {row['Name of file']}")

    # ---------------------------
    # Merge, write CSV, save cache
    # ---------------------------
    all_rows = existing_rows + updated_rows
    final_rows = {}
    for row in all_rows:
        rel_path = os.path.relpath(os.path.join(row["Path of file"], row["Name of file"]), TARGET_DIR)
        if os.path.exists(os.path.join(row["Path of file"], row["Name of file"])):
            final_rows[rel_path] = row

    ensure_dir(OUTPUT_CSV)
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for row in sorted(final_rows.values(), key=lambda r: r["Name of file"]):
            writer.writerow(row)

    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(file_cache, f, indent=2)

    total_time = time.time() - start_time
    if delCount > 0:
        file_display = "file" if delCount == 1 else "files"
        log(f"🗑️ {delCount} {file_display} Deleted")

    summary = f"Finished in {int(total_time)}s — {len(updated_rows)} updated, {len(file_cache)} total"
    log("✅ " + summary)
    notify("Metadata Script", f"✅ Script completed successfully.\n\n{summary}")

finally:
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except Exception:
        pass
