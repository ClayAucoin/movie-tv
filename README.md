# Media Metadata & Arr Automation — README

A practical, end-to-end guide to the scripts in this repo: what they do, how to run them on Windows and Linux, how to schedule them, and how the companion Google Apps Scripts pull the generated CSVs into Google Sheets.

> **Who this is for**: This repo is designed for a local media setup that exports metadata from your library, keeps Radarr/Sonarr data fresh, and mirrors the results into Sheets for dashboards and audits.

---
---



## Table of Contents

1. [Repo Overview](#repo-overview)
2. [Environment & Prereqs](#environment--prereqs)
3. [Configuration](#configuration)
4. [Script Catalog](#script-catalog)
   - [Import Metadata](#1-import-metadata)
   - [Features Directory Check](#2-features-directory-check)
   - [Update Radarr](#3-update-radarr)
   - [Update Sonarr](#4-update-sonarr)
   - [Dump MediaInfo](#5-dump-mediainfo)
   - [Get Field List (Radarr)](#6-get-field-list-radarr)
   - [Get Field List (Sonarr)](#7-get-field-list-sonarr)
5. [Running the Scripts](#running-the-scripts)
   - [Windows](#windows)
   - [Linux](#linux)
6. [VBScript launchers (silent mode)](#vbscript-launchers-silent-mode)
7. [Windows Task Scheduler setup](#windows-task-scheduler-setup)
8. [Google Sheets companion (Apps Script)](#google-sheets-companion-apps-script)
9. [Troubleshooting](#troubleshooting)
10. [Appendix: Example Repo Layout](#appendix-example-repo-layout)

---

## Repo Overview

These scripts work together to extract rich metadata from local media, validate directory structure, update Radarr and Sonarr datasets, and export clean CSVs for analysis in Google Sheets.

**Outputs include**:

- CSV exports for Movies and TV Shows (from Radarr/Sonarr)
- Media metadata CSV/JSON for your local library
- Log files and a cache JSON to skip unchanged files

---

## Environment & Prereqs

- **Python 3.10+** recommended
- **pip** and a **virtual environment** per project
- **Radarr** and **Sonarr** reachable from the machine running the scripts
- **API Keys** for Radarr and Sonarr
- **MediaInfo** installed if you use the CLI, or `pymediainfo` if using the Python binding
- **Windows** users: `pythonw.exe` available for silent runs
- Optional: **Google Drive** for hosting CSVs that Sheets will read

**Install Python deps**:

```bash
# from the repo root
python -m venv .venv
# Windows:
.venv\Scripts\pip install -r requirements.txt
# Linux/macOS:
source .venv/bin/activate && pip install -r requirements.txt
```

A typical `requirements.txt` for this repo may include:

```
python-dotenv
requests
pymediainfo
urllib3
idna
charset-normalizer
```

If you use Windows toast notifications in some scripts, you may also see:

```
pywin32
win10toast
```

---

## Configuration

Create a `.env` file in the repo root. Example:

```
# Radarr
RADARR_URL=http://127.0.0.1:7878
RADARR_API_KEY=your_radarr_api_key

# Sonarr
SONARR_URL=http://127.0.0.1:8989
SONARR_API_KEY=your_sonarr_api_key

# Paths
LIBRARY_ROOT=D:\Media
OUTPUT_DIR=D:\Exports\media-metadata
LOG_DIR=D:\Exports\logs

# Behavior
MAX_WORKERS=8
SKIP_SMALLER_THAN_BYTES=1048576
```

Most scripts also accept CLI flags for overrides. See each section below.

---

## Script Catalog

### 1) Import Metadata

**Script**: `importMetaData/importmetadata.py`  
**Purpose**: Walk your media library, extract technical and descriptive metadata per file using MediaInfo, and export to CSV (and optionally JSON). Caches previous results to skip unchanged files. Handles rename and deletion detection.

**Typical outputs**:

- `media_metadata.csv`
- `media_metadata.json` (optional)
- `cache.json` for change detection
- `run_timing.csv` (optional timing per file)

**Key flags**:

```
--root "D:\Media"               # library root to scan
--out "D:\Exports\media-metadata\media_metadata.csv"
--json "D:\Exports\media-metadata\media_metadata.json"
--log "D:\Exports\logs\import_metadata.log"
--max-workers 8
--skip-smaller 1048576          # ignore tiny files
--task_scheduler                # suppresses popups/notifications in code
--no-json                       # disable json output if supported
```

**Notes**:

- Deletion detection removes rows for files that no longer exist.
- Rename detection updates existing rows without duplicating.
- If you see "CSV not removing deleted rows," ensure the script writes the filtered DataFrame back to the same CSV and uses a stable unique key (full path + size + mtime or a hash).

---

### 2) Features Directory Check

**Script**: `tools/features_directory_check.py`  
**Purpose**: Verify required directory structure exists (e.g., specific folders under each movie or TV show), create missing directories if requested, and report anomalies.

**Typical flags**:

```
--root "D:\Media\Movies"
--expect "Featurettes,Subtitles,Extras"
--create-missing
--report "D:\Exports\logs\features_dir_report.csv"
```

**What it checks**:

- Presence of expected subfolders
- Empty folders
- Unexpected extra folders (if you pass a strict flag)
- Can emit a CSV report for audit

---

### 3) Update Radarr

**Script**: `arr/Radarr/updateRadarrData.py`  
**Purpose**: Query Radarr API, export movie library to CSV, and optionally normalize fields for Sheets.

**Typical flags**:

```
--url http://127.0.0.1:7878
--api-key <key>
--out "D:\Exports\radarr\radarr_movies.csv"
--log "D:\Exports\logs\radarr_update.log"
--fields "title,year,qualityProfileId,hasFile,monitored,tmdbId,imdbId,path,sizeOnDisk"
```

**Notes**:

- Respects `.env` values if flags are omitted.
- If rate limits or timeouts occur, increase retry/backoff in the code if available.

---

### 4) Update Sonarr

**Script**: `arr/Sonarr/updateSonarrData.py`  
**Purpose**: Query Sonarr API, export series and episodes to CSV. Optionally split series.csv and episodes.csv.

**Typical flags**:

```
--url http://127.0.0.1:8989
--api-key <key>
--series-out "D:\Exports\sonarr\sonarr_series.csv"
--episodes-out "D:\Exports\sonarr\sonarr_episodes.csv"
--log "D:\Exports\logs\sonarr_update.log"
--fields-series "title,year,network,qualityProfileId,monitored,tmdbId,tvdbId,path"
--fields-episodes "seriesId,seasonNumber,episodeNumber,airDate,hasFile,monitored"
```

---

### 5) Dump MediaInfo

**Script**: `tools/dump_mediainfo.py`  
**Purpose**: Dump full MediaInfo for a specific file or a folder to CSV or JSON. Useful for spot checks and for designing your column selections.

**Typical flags**:

```
--input "D:\Media\Movies\Some.Movie.2019\Some.Movie.2019.mkv"
--out "D:\Exports\debug\mediainfo_dump.json"
--csv "D:\Exports\debug\mediainfo_dump.csv"
--recursive
```

**Backends**:

- `pymediainfo` Python binding
- Or shell out to `mediainfo` CLI if preferred

---

### 6) Get Field List (Radarr)

**Script**: `arr/Radarr/get_field_list_radarr.py`  
**Purpose**: Query a sample of Radarr items and output a flattened list of keys as a CSV. Lets you pick stable columns for your main export.

**Typical flags**:

```
--url http://127.0.0.1:7878
--api-key <key>
--sample 50
--out "D:\Exports\radarr\radarr_field_list.csv"
```

---

### 7) Get Field List (Sonarr)

**Script**: `arr/Sonarr/get_field_list_sonarr.py`  
**Purpose**: Same as above but for Sonarr series and episodes.

**Typical flags**:

```
--url http://127.0.0.1:8989
--api-key <key>
--sample 50
--out "D:\Exports\sonarr\sonarr_field_list.csv"
```

---

## Running the Scripts

### Windows

From a normal terminal:

```powershell
# activate venv
.\.venv\Scripts\Activate.ps1

# run import
python .\importMetaData\importmetadata.py --task_scheduler

# run Radarr export
python .\arr\Radarr\updateRadarrData.py

# run Sonarr export
python .\arr\Sonarr\updateSonarrData.py
```

Silent background using `pythonw.exe`:

```powershell
# no console window
pythonw.exe .\importMetaData\importmetadata.py --task_scheduler
pythonw.exe .\arr\Radarr\updateRadarrData.py --task_scheduler
pythonw.exe .\arr\Sonarr\updateSonarrData.py --task_scheduler
```

Make sure `pythonw.exe` in your PATH aligns with your venv’s Python, or pass the full path to the venv interpreter’s `pythonw.exe`.

### Linux

```bash
source .venv/bin/activate

python importMetaData/importmetadata.py
python arr/Radarr/updateRadarrData.py
python arr/Sonarr/updateSonarrData.py
```

You can cron these if needed, but the primary scheduling guidance below is for Windows Task Scheduler.

---

## VBScript launchers (silent mode)

Place these in a `vbs/` folder and double-click to run silently. They use `pythonw.exe` to avoid a console window.

**`vbs/silent_importmetadata.vbs`**

```vb
Dim objShell
Set objShell = CreateObject("WScript.Shell")
objShell.Run """C:\Path\to\repo\.venv\Scripts\pythonw.exe"" ""C:\Path\to\repo\importMetaData\importmetadata.py"" /task_scheduler", 0, False
Set objShell = Nothing
```

**`vbs/silent_update_radarr.vbs`**

```vb
Dim objShell
Set objShell = CreateObject("WScript.Shell")
objShell.Run """C:\Path\to\repo\.venv\Scripts\pythonw.exe"" ""C:\Path\to\repo\arr\Radarr\updateRadarrData.py"" /task_scheduler", 0, False
Set objShell = Nothing
```

**`vbs/silent_update_sonarr.vbs`**

```vb
Dim objShell
Set objShell = CreateObject("WScript.Shell")
objShell.Run """C:\Path\to\repo\.venv\Scripts\pythonw.exe"" ""C:\Path\to\repo\arr\Sonarr\updateSonarrData.py"" /task_scheduler", 0, False
Set objShell = Nothing
```

> If your scripts use `--task_scheduler` instead of `/task_scheduler`, just switch the argument accordingly.

---

## Windows Task Scheduler setup

You can configure everything in the GUI or via `schtasks`. Here are both.

### Quick GUI steps

1. Open **Task Scheduler** → **Create Task…** (not Basic).
2. **General** tab
   - Name:
     - Metadata: `_movies - Update metadata - movies and feats`
     - Radarr & Sonarr: `_movies - Update metadata - movies and feats`
   - Run whether user is logged on or not
   - Configure for: Windows 10 or later
3. **Triggers** tab → **New…**
   - One time: Start 1:00:00
   - Daily at 2:00 AM (example)
   - Repeat task every: 5 minutes
   - Enabled
4. **Actions** tab → **New…**
   - **Program/script**: `C:\Path\to\repo\.venv\Scripts\pythonw.exe`
   - **Add arguments**: `C:\Path\to\repo\importMetaData\importmetadata.py --task_scheduler`
   - **Start in**: `C:\Path\to\repo`
5. **Conditions** tab: Uncheck "Start the task only if the computer is on AC power" if needed.
6. **Settings** tab:
   - Allow task to be run on demand. Stop if runs longer than X hours if you want a safeguard.
   - Run task as soon as possible agter a scheduled start is missed
7. Save. Enter your credentials when prompted.

Repeat for **Update Radarr** and **Update Sonarr** with their respective python files and arguments.

### Command-line setup

```cmd
schtasks /Create /TN "Import Media Metadata" /SC DAILY /ST 02:00 ^
 /TR "\"C:\Path\to\repo\.venv\Scripts\pythonw.exe\" \"C:\Path\to\repo\importMetaData\importmetadata.py\" --task_scheduler" ^
 /RL HIGHEST /F

schtasks /Create /TN "Update Radarr CSV" /SC HOURLY /MO 6 ^
 /TR "\"C:\Path\to\repo\.venv\Scripts\pythonw.exe\" \"C:\Path\to\repo\arr\Radarr\updateRadarrData.py\" --task_scheduler" ^
 /RL HIGHEST /F

schtasks /Create /TN "Update Sonarr CSV" /SC HOURLY /MO 6 ^
 /TR "\"C:\Path\to\repo\.venv\Scripts\pythonw.exe\" \"C:\Path\to\repo\arr\Sonarr\updateSonarrData.py\" --task_scheduler" ^
 /RL HIGHEST /F
```

If your scripts expect `/task_scheduler` instead, replace the flag.

---

## Google Sheets companion (Apps Script)

These scripts import the CSVs hosted on Google Drive into specific Sheets only when the file changed since the last import. They use a time-driven trigger (for example every 15 minutes).

### How it works

- You upload or sync `radarr_movies.csv`, `sonarr_series.csv`, `sonarr_episodes.csv`, `media_metadata.csv` to **Drive**.
- Apps Script checks the Drive file’s `modifiedTime`. If it changed since last import, it downloads and refreshes the target sheet.
- It logs a short summary to a hidden "Logs" sheet.

### Setup steps

1. Open your Google Sheet → Extensions → Apps Script.
2. Create a new script file and paste the code below.
3. Replace the `FILE_IDS` map with your Drive file IDs and target sheet names.
4. Run `setupTriggers()` once to create the time-driven trigger.
5. Use the **Media Data** menu in the Sheet to run imports on demand.

### Apps Script code

```javascript
// === Config ===
const FILE_IDS = {
  radarrMovies: { fileId: "YOUR_DRIVE_FILE_ID_1", sheetName: "Radarr Movies" },
  sonarrSeries: { fileId: "YOUR_DRIVE_FILE_ID_2", sheetName: "Sonarr Series" },
  sonarrEpisodes: {
    fileId: "YOUR_DRIVE_FILE_ID_3",
    sheetName: "Sonarr Episodes",
  },
  mediaMetadata: {
    fileId: "YOUR_DRIVE_FILE_ID_4",
    sheetName: "Media Metadata",
  },
};

const PROP_LAST_IMPORT_PREFIX = "lastImport__"; // per fileId
const LOG_SHEET = "Logs";

function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu("Media Data")
    .addItem("Import All Now", "importAllNow")
    .addSeparator()
    .addItem("Import Radarr Movies", "importRadarrMovies")
    .addItem("Import Sonarr Series", "importSonarrSeries")
    .addItem("Import Sonarr Episodes", "importSonarrEpisodes")
    .addItem("Import Media Metadata", "importMediaMetadata")
    .addToUi();
}

function setupTriggers() {
  // Clear old triggers
  ScriptApp.getProjectTriggers().forEach((t) => ScriptApp.deleteTrigger(t));
  // Every 15 minutes
  ScriptApp.newTrigger("scheduledImport").timeBased().everyMinutes(15).create();
}

function scheduledImport() {
  importIfChanged(FILE_IDS.radarrMovies);
  importIfChanged(FILE_IDS.sonarrSeries);
  importIfChanged(FILE_IDS.sonarrEpisodes);
  importIfChanged(FILE_IDS.mediaMetadata);
}

function importAllNow() {
  importCSVIntoSheet(FILE_IDS.radarrMovies);
  importCSVIntoSheet(FILE_IDS.sonarrSeries);
  importCSVIntoSheet(FILE_IDS.sonarrEpisodes);
  importCSVIntoSheet(FILE_IDS.mediaMetadata);
}

function importRadarrMovies() {
  importCSVIntoSheet(FILE_IDS.radarrMovies);
}
function importSonarrSeries() {
  importCSVIntoSheet(FILE_IDS.sonarrSeries);
}
function importSonarrEpisodes() {
  importCSVIntoSheet(FILE_IDS.sonarrEpisodes);
}
function importMediaMetadata() {
  importCSVIntoSheet(FILE_IDS.mediaMetadata);
}

function importIfChanged(entry) {
  const file = DriveApp.getFileById(entry.fileId);
  const modified = file.getLastUpdated().getTime();
  const propKey = PROP_LAST_IMPORT_PREFIX + entry.fileId;
  const props = PropertiesService.getDocumentProperties();
  const last = Number(props.getProperty(propKey) || 0);
  if (modified > last) {
    importCSVIntoSheet(entry);
    props.setProperty(propKey, String(modified));
  }
}

function importCSVIntoSheet(entry) {
  const file = DriveApp.getFileById(entry.fileId);
  const blob = file.getBlob();
  const csv = Utilities.parseCsv(blob.getDataAsString());
  const ss = SpreadsheetApp.getActive();
  let sh = ss.getSheetByName(entry.sheetName);
  if (!sh) sh = ss.insertSheet(entry.sheetName);

  // Replace all data
  sh.clearContents();
  if (csv.length) {
    sh.getRange(1, 1, csv.length, csv[0].length).setValues(csv);
  }

  logRun(
    `Imported "${entry.sheetName}" from file ${entry.fileId} with ${csv.length} rows.`
  );
}

function logRun(msg) {
  const ss = SpreadsheetApp.getActive();
  let sh = ss.getSheetByName(LOG_SHEET);
  if (!sh) {
    sh = ss.insertSheet(LOG_SHEET);
    sh.hideSheet();
    sh.appendRow(["Timestamp", "Message"]);
  }
  sh.appendRow([new Date(), msg]);
}
```

> Drive "on change" triggers do not fire for file content updates. Time-driven triggers are the reliable approach. The script stores the last imported timestamp per file to avoid re-processing unchanged CSVs.

---

## Troubleshooting

- **`ModuleNotFoundError: No module named 'dotenv'` on Linux**  
  Install inside the Linux venv: `pip install python-dotenv`. Make sure you are activating the correct venv before running.
- **Silent runs still show a window**  
  Confirm you are launching with `pythonw.exe` and not `python.exe`. Double-check the VBScript path to the venv's `pythonw.exe`.
- **CSV not updating in Sheets**  
  Open the bound Apps Script and run `scheduledImport()` manually to test. Check the file IDs and that the CSV delimiter is a comma. If the CSV is big, split into separate per-entity files.
- **Network errors to Radarr/Sonarr**  
  Verify the URLs and API keys. If running across subnets, ensure firewall/NAT rules allow access.
- **Performance**  
  Increase `MAX_WORKERS`, but watch disk and CPU. Consider hashing large files only once. Exclude sample clips and extras with a path filter.
- **Paths with spaces**  
  Always quote paths in VBScript and Task Scheduler arguments.

---

## Appendix: Example Repo Layout

```
repo-root/
├─ .venv/
├─ .env
├─ requirements.txt
├─ importMetaData/
│  ├─ importmetadata.py
│  ├─ helpers/
│  └─ README_snippet.md
├─ arr/
│  ├─ Radarr/
│  │  ├─ updateRadarrData.py
│  │  └─ get_field_list_radarr.py
│  └─ Sonarr/
│     ├─ updateSonarrData.py
│     └─ get_field_list_sonarr.py
├─ tools/
│  ├─ dump_mediainfo.py
│  └─ features_directory_check.py
├─ vbs/
│  ├─ silent_importmetadata.vbs
│  ├─ silent_update_radarr.vbs
│  └─ silent_update_sonarr.vbs
├─ exports/                # optional default output location
│  ├─ media_metadata.csv
│  ├─ radarr_movies.csv
│  ├─ sonarr_series.csv
│  ├─ sonarr_episodes.csv
│  └─ logs/
└─ README.md
```

---

**Tip**: Commit this README and adjust paths, flags, and field lists to match your environment. If you want, split the README into per-script docs under each folder and link them from here.
