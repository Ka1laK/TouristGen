"""
Diagnostic test for travel time calculation.
This script sends a route generation request and captures the response.
Check the backend console for detailed logs showing which routing method was used.
"""
import requests
import json
import time

print("=" * 60)
print("TRAVEL TIME DIAGNOSTIC TEST")
print("=" * 60)

# Wait for server to be ready
time.sleep(2)

# Use POIs that are more likely to be open (e.g., parks, malls)
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
        "latitude": -12.1191,  # Near Parque Kennedy
        "longitude": -77.0311
    }
}

print(f"\nStart Location: {payload['start_location']}")
print(f"Transport Mode: {payload['transport_mode']}")
print(f"Day/Time: {payload['day_of_week']} at {payload['start_time']}")
print("\nSending request...")

try:
    response = requests.post(
        "http://localhost:8000/api/optimize/generate-route",
        json=payload,
        timeout=120
    )
    
    print(f"\nResponse Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        timeline = data.get("timeline", [])
        
        print(f"\n[OK] Route generated with {len(timeline)} POIs")
        print("-" * 40)
        
        if timeline:
            first = timeline[0]
            print(f"First POI: {first.get('poi_name')}")
            print(f"Travel Time (from backend): {first.get('travel_time')} minutes")
            print(f"Arrival Time: {first.get('arrival_time')}")
            
            print("\nAll POI Travel Times:")
            for i, item in enumerate(timeline):
                print(f"  {i+1}. {item.get('poi_name')}: {item.get('travel_time')} min")
    else:
        print(f"\n[ERROR] {response.text[:500]}")
        
except Exception as e:
    print(f"\n[ERROR] Request failed: {e}")

print("\n" + "=" * 60)
print("CHECK BACKEND CONSOLE FOR DETAILED ROUTING LOGS")
print("Look for: [OSRM OK] or [GEODESIC]")
print("=" * 60)
