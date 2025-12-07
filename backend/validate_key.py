import requests
import os

# Manual env parsing to avoid dependencies
env_path = os.path.join(os.path.dirname(__file__), '.env')
api_key = ""

if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("OPENROUTESERVICE_API_KEY="):
                api_key = line.split("=", 1)[1].strip()
                break

print(f"Testing API Key: {api_key[:10]}...")

if not api_key:
    print("Error: No API key found in .env file.")
    exit(1)

# ORS Status/Health endpoint or a simple direction request
url = "https://api.openrouteservice.org/v2/directions/foot-walking"
headers = {
    "Authorization": api_key,
    "Content-Type": "application/json"
}
body = {
    "coordinates": [[-77.0428, -12.0464], [-77.0420, -12.0460]] # Short walk in Lima
}

try:
    response = requests.post(url, json=body, headers=headers)
    if response.status_code == 200:
        print("SUCCESS: API Key is valid and working!")
        print(f"Response: {response.json().get('routes')[0].get('summary')}")
    else:
        print(f"FAILED: API returned status code {response.status_code}")
        print(f"Error: {response.text}")
except Exception as e:
    print(f"ERROR: Could not connect to API. {e}")
