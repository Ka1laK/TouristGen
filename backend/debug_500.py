import requests
import json

payload = {
    "max_duration": 480,
    "max_budget": 200,
    "start_time": "09:00",
    "day_of_week": "Tuesday",
    "user_pace": "medium",
    "mandatory_categories": [],
    "avoid_categories": [],
    "preferred_districts": [],
    "transport_mode": "driving-car",
    "start_location": {
        "latitude": -12.1268334,
        "longitude": -77.0297725
    },
    "selected_poi_ids": [410, 407]
}

try:
    response = requests.post(
        "http://localhost:8000/api/optimize/generate-route",
        json=payload,
        timeout=120
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:2000]}")
except Exception as e:
    print(f"Error: {e}")
