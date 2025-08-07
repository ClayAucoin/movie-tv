# configSonarr.py - Common Configuration Variables

SONARR_URL = "http://192.168.1.205:8989"  # Replace with your Sonarr IP or hostname
API_KEY = "e011965887634f9e8bd33536020dc1ed"  # Replace with your actual API key

# Correct API endpoint
API_URL = f"{SONARR_URL}/api/v3/series"


"""
Add this data:

import configSonarr  # Import the config module

SONARR_URL = configSonarr.SONARR_URL
API_KEY = configSonarr.API_KEY
API_URL = configSonarr.API_URL
"""