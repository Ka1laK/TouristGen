import requests
import time

time.sleep(2)

payload = {
    "max_duration": 480,
    "max_budget": 500,
    "start_time": "10:00",
    "day_of_week": "Tuesday",
    "user_pace": "medium",
    "mandatory_categories": [],
    "avoid_categories": [],
    "preferred_districts": ["Miraflores"],
    "transport_mode": "driving-car",
    "start_location": {
        "latitude": -12.1191,
        "longitude": -77.0311
    }
}

r = requests.post(
    "http://localhost:8000/api/optimize/generate-route",
    json=payload,
    timeout=120
)

print(f"Status: {r.status_code}")

if r.status_code == 200:
    d = r.json()
    t = d.get("timeline", [])
    print(f"POIs in route: {len(t)}")
    if t:
        for i, item in enumerate(t):
            print(f"  {i+1}. {item.get('poi_name')}: travel={item.get('travel_time')} min")
else:
    print(f"Error: {r.text[:300]}")
