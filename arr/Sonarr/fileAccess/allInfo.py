import os
import csv
import time
from pathlib import Path
import win32com.client  # For extended properties (Windows only)

# Directory to scan (change this)
directory = r"C:\_lib\data\_scripts_\py\_tut\projects\Sonarr"

# Output CSV file
csv_file = "file_info.csv"


# Function to get extended properties (Windows Only)
def get_file_properties(file_path):
    properties = ["Title", "Author", "Company"]
    try:
        shell = win32com.client.Dispatch("Shell.Application")
        folder = shell.NameSpace(os.path.dirname(file_path))
        item = folder.ParseName(os.path.basename(file_path))

        if item:
            return {prop: folder.GetDetailsOf(item, properties.index(prop)) for prop in properties}
    except Exception as e:
        print(f"Error retrieving extended properties for {file_path}: {e}")
    return {}


# Open CSV file for writing
with open(csv_file, "w", newline="", encoding="utf-8") as csvfile:
    csv_writer = csv.writer(csvfile)

    # Define column headers
    headers = ["File Name", "File Path", "Size (bytes)", "Created", "Modified", "Extension", "Title", "Author",
               "Company"]
    csv_writer.writerow(headers)

    # Walk through all files and subdirectories
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_info = os.stat(file_path)

            # Get basic file details
            file_size = file_info.st_size
            created_time = time.ctime(file_info.st_ctime)
            modified_time = time.ctime(file_info.st_mtime)
            extension = Path(file_path).suffix

            # Get extended properties (Windows only)
            extended_props = get_file_properties(file_path)
            title = extended_props.get("Title", "")
            author = extended_props.get("Author", "")
            company = extended_props.get("Company", "")

            # Write row to CSV
            csv_writer.writerow(
                [file, file_path, file_size, created_time, modified_time, extension, title, author, company])

print(f"File information saved to {csv_file}")
