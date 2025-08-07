# configSonarr.py - Common Configuration Variables

RADARR_URL = "http://192.168.1.205:7878"  # Replace with your Sonarr IP or hostname
API_KEY = "92315363a3c9466295befa6b7a7a197e"  # Replace with your actual API key

# Correct API endpoint
API_URL = f"{RADARR_URL}/api/v3/movie"


"""
Add this data:

import configSonarr  # Import the config module

SONARR_URL = configSonarr.SONARR_URL
API_KEY = configSonarr.API_KEY
API_URL = configSonarr.API_URL
"""