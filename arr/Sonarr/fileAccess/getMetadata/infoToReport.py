import os
import csv
import win32com.client

# Directory to scan (change this)
directory = r"C:\_lib\data\_scripts_\py\_tut\projects\Sonarr"

# Output CSV file
csv_file = "file_metadata.csv"

def get_all_metadata_fields():
    """Retrieve all available metadata fields."""
    shell = win32com.client.Dispatch("Shell.Application")
    folder = shell.NameSpace(directory)

    metadata_fields = []
    for i in range(300):  # Checking up to 300 fields (safe range)
        field_name = folder.GetDetailsOf(None, i)
        if field_name:  # Ignore empty fields
            metadata_fields.append((i, field_name))

    return metadata_fields

def get_file_metadata(file_path, metadata_fields):
    """Retrieve metadata for a given file."""
    shell = win32com.client.Dispatch("Shell.Application")
    folder = shell.NameSpace(os.path.dirname(file_path))
    item = folder.ParseName(os.path.basename(file_path))

    if item:
        return [folder.GetDetailsOf(item, index) for index, _ in metadata_fields]
    return [""] * len(metadata_fields)  # Return empty values if metadata is unavailable

# Get all metadata field names
metadata_fields = get_all_metadata_fields()

# Open CSV file for writing
with open(csv_file, "w", newline="", encoding="utf-8") as csvfile:
    csv_writer = csv.writer(csvfile)

    # Write header row
    headers = ["File Name", "File Path", "Size (bytes)"] + [field_name for _, field_name in metadata_fields]
    csv_writer.writerow(headers)

    # Walk through all files and folders
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.stat(file_path).st_size

            # Retrieve file metadata
            metadata_values = get_file_metadata(file_path, metadata_fields)

            # Write row to CSV
            csv_writer.writerow([file, file_path, file_size] + metadata_values)

print(f"File metadata saved to {csv_file}")
