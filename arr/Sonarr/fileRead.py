import os
import time
# from pathlib import Path

def file_compare():
    file_path_orig = r"E:\My Drive\_clay0aucoin@gmail.com\Sonarr\sonarr.csv"
    file_path_copy = r"E:\My Drive\_clay0aucoin@gmail.com\Sonarr\sonarr1.csv"

    # Using os.stat() to get file details
    file_info_orig = os.stat(file_path_orig)
    file_info_copy = os.stat(file_path_copy)

    # Get information
    res_orig = time.ctime(file_info_orig.st_mtime)
    res_copy = time.ctime(file_info_copy.st_mtime)

    # Print information
    # print(f"Orig Modified: {time.ctime(file_info_orig.st_mtime)}")
    # print(f"Orig Modified: {res_orig}")
    # print(f"Copy Modified: {res_copy}")

    # print()

    if res_orig == res_copy:
        # print("They equal")
        return True
    else:
        # print("They DON'T equal")
        return False