"""
python "C:/Users/Administrator/projects/movie-tv/importMetaData/featurettesDirCheck.py"

"""


import os
import csv
import sys
import ctypes
from datetime import datetime

# ---------------- Configuration ----------------
# Prefer UNC in scheduled tasks; fall back to mapped drive if available.
SEARCH_DIR_PRIMARY = r"\\192.168.1.205\Media\Movies"   # walk this when available
SEARCH_DIR_FALLBACK = r"M:\Movies"                     # else walk this

# How you want paths to appear in the CSV (display prefix)
DISPLAY_PREFIX = r"M:\Movies"                          # always show M:\Movies\...

# Write to a local path the Task Scheduler session always has access to.
OUTPUT_LOCAL = r"C:\_\featurettes_folders.csv"

# Optional mirror to Google Drive (will only run if the path exists in this session)
OUTPUT_GDRIVE = r"E:\My Drive\__clay0aucoin@gmail.com\movies_on_m\featurettes_folders.csv"

# Lock against concurrent writers (based on the local output)
LOCK_FILE = OUTPUT_LOCAL + ".lock"

# Check if the script is running with the "/task_scheduler" argument
is_task_scheduler = '/task_scheduler' in sys.argv


def notify(title, message):
    try:
        if not is_task_scheduler:
            ctypes.windll.user32.MessageBoxW(0, message, title, 0x40)
    except Exception:
        pass


# ----------------- Helpers ---------------------
def acquire_lock(lock_path):
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
        return True
    except FileExistsError:
        return False


def release_lock(lock_path):
    try:
        if os.path.exists(lock_path):
            os.remove(lock_path)
    except Exception:
        pass


def to_display_path(p: str) -> str:
    """
    Rewrite a found path to the desired display prefix.
    If we walked the UNC primary, swap that prefix for DISPLAY_PREFIX.
    If we already walked M:, return as-is.
    """
    src = SEARCH_DIR_PRIMARY.rstrip("\\/").lower()
    if p.lower().startswith(src):
        suffix = p[len(src):]  # keep leading backslash in suffix if present
        # Ensure we don't duplicate separators
        return DISPLAY_PREFIX.rstrip("\\/") + suffix
    return p


def atomic_write_csv(path, rows):
    """Write CSV to a temp file and atomically replace the destination."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Directory with Featurettes"])
        for r in rows:
            w.writerow([to_display_path(r)])
    os.replace(tmp, path)


def verify_csv_rows(path):
    try:
        with open(path, newline="", encoding="utf-8") as f:
            row_count = sum(1 for _ in f)
        return max(0, row_count - 1)  # exclude header
    except Exception:
        return None


# ------------------- Main ----------------------
def main():
    search_dir = SEARCH_DIR_PRIMARY if os.path.exists(SEARCH_DIR_PRIMARY) else SEARCH_DIR_FALLBACK
    output_csv = OUTPUT_LOCAL

    if not acquire_lock(LOCK_FILE):
        print("Another instance is writing the CSV right now. Exiting.")
        sys.exit(0)

    msg = "Featurettes search finished."  # default for notify
    try:
        # Collect results (case-insensitive match for 'Featurettes')
        results = []
        for root, dirs, files in os.walk(search_dir):
            if any(d.lower() == "featurettes" for d in dirs):
                results.append(root)

        # Write local CSV atomically (paths mapped to DISPLAY_PREFIX)
        atomic_write_csv(output_csv, results)

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"[{ts}] Found {len(results)} directories with a 'Featurettes' subfolder."
        print(msg)
        print(f"[{ts}] Wrote: {output_csv}")

        # Verify local file
        vr = verify_csv_rows(output_csv)
        if vr is not None:
            print(f"[{ts}] Verify (local): {vr} data rows present.")

        # Optional: mirror to Google Drive if its parent exists
        try:
            gdrive_parent = os.path.dirname(OUTPUT_GDRIVE)
            if gdrive_parent and os.path.exists(gdrive_parent):
                tmp_g = OUTPUT_GDRIVE + ".tmp"
                with open(tmp_g, "w", newline="", encoding="utf-8") as f:
                    w = csv.writer(f)
                    w.writerow(["Directory with Featurettes"])
                    for r in results:
                        w.writerow([to_display_path(r)])
                os.replace(tmp_g, OUTPUT_GDRIVE)
                gvr = verify_csv_rows(OUTPUT_GDRIVE)
                if gvr is not None:
                    print(f"[{ts}] Mirrored to: {OUTPUT_GDRIVE} (rows: {gvr})")
            else:
                print(f"[{ts}] Mirror skipped: Google Drive path not available in this session.")
        except Exception as e:
            print(f"[{ts}] Mirror skipped due to error: {e}")

    finally:
        release_lock(LOCK_FILE)
    notify("Featurette Directory Search", msg)


if __name__ == "__main__":
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scan started")
    print(f"Primary:  {SEARCH_DIR_PRIMARY}")
    print(f"Fallback: {SEARCH_DIR_FALLBACK}")
    using = SEARCH_DIR_PRIMARY if os.path.exists(SEARCH_DIR_PRIMARY) else SEARCH_DIR_FALLBACK
    print(f"Using:    {using}")
    print(f"Display:  {DISPLAY_PREFIX}")
    print(f"Local out:{OUTPUT_LOCAL}")
    print(f"GDrive:   {OUTPUT_GDRIVE}")
    main()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Done")
