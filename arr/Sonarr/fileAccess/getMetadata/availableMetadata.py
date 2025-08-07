import os
import win32com.client

# Change this to any file you want to inspect
file_path = r"E:\My Drive\_clay0aucoin@gmail.com\Sonarr\sonarr.csv"

shell = win32com.client.Dispatch("Shell.Application")
folder = shell.NameSpace(os.path.dirname(file_path))
item = folder.ParseName(os.path.basename(file_path))

# Iterate through all possible indexes (0-300 is a safe range)
for i in range(1000):
    property_name = folder.GetDetailsOf(None, i)
    property_value = folder.GetDetailsOf(item, i)
    if property_name:  # Only print non-empty property names
        print(f"{i}: {property_name} -> {property_value}")
