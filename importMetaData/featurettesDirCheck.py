"""
python "C:/_lib/data/_scripts_/py/_projects/ImportMetaData/featurettesDirCheck.py"

"""

import os
import csv

# Define the search directory and output CSV path
search_dir = r"M:\Movies"
output_csv = r"E:\My Drive\_clay0aucoin@gmail.com\movies_on_m\featurettes_folders.csv"

# List to hold directories that contain a 'Featurettes' subdirectory
results = []

# Walk through the directory tree
for root, dirs, files in os.walk(search_dir):
    if "Featurettes" in dirs:
        results.append(root)

# Ensure the output directory exists
os.makedirs(os.path.dirname(output_csv), exist_ok=True)

# Write results to CSV
with open(output_csv, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["Directory with Featurettes"])
    for path in results:
        writer.writerow([path])

print(f"Found {len(results)} directories with a 'Featurettes' subfolder.")
print(f"Results saved to: {output_csv}")
