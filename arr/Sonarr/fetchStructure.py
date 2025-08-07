# 🔹 Fetch Season and Episode Details from Series Data
def get_season_data(series):
    """Fetches season and episode data from a series."""
    season_data = {}
    total_episodes = 0
    my_count = 0

    # Debugging: Print the series data structure for inspection
    print(f"🔍 Inspecting series data for {series['title']}: {series.keys()}")  # This will show available keys

    for season in series["seasons"]:
        # Debugging: Print season data for inspection
        print(f"    Season Data: {season}")

        # Skip past seasons that are not yet aired (use available info, e.g., seasonNumber, episodeCount)
        # We can adapt this based on the structure we find
        if "seasonNumber" in season:  # Ensure that we have the key to process the season
            total_episodes = season["episodeCount"]
            my_count = season["episodeFileCount"]
            break

    season_data["total_episodes"] = total_episodes
    season_data["my_count"] = my_count
    return season_data
