"""
Test OpenRouteService API responses to debug travel time calculations
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTESERVICE_API_KEY")

# Test coordinates in Lima (relatively far apart)
# Miraflores to Callao - approx 15km
test_coords = [
    (-12.1175, -77.0290),  # Miraflores (Kennedy Park)
    (-12.0553, -77.1185),  # Callao (Plaza Grau)
]

# Also test a longer distance
# Comas to Miraflores - approx 20km
test_coords_long = [
    (-11.9459, -77.0584),  # Comas
    (-12.1175, -77.0290),  # Miraflores
]

def test_ors_matrix(coords, name):
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    
    url = "https://api.openrouteservice.org/v2/matrix/driving-car"
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json"
    }
    
    # ORS expects [longitude, latitude]
    locations = [[lon, lat] for lat, lon in coords]
    
    body = {
        "locations": locations,
        "metrics": ["duration", "distance"],
        "units": "m"
    }
    
    print(f"Request body: {body}")
    
    response = requests.post(url, json=body, headers=headers, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nRaw API Response:")
        print(f"  Durations (seconds): {data.get('durations')}")
        print(f"  Distances (meters): {data.get('distances')}")
        
        durations = data.get('durations', [[]])
        distances = data.get('distances', [[]])
        
        if len(durations) > 1 and len(durations[0]) > 1:
            dur_seconds = durations[0][1]  # From point 0 to point 1
            dur_minutes = dur_seconds / 60.0
            
            dist_meters = distances[0][1] if distances and len(distances[0]) > 1 else 0
            dist_km = dist_meters / 1000.0
            
            print(f"\n  Interpreted:")
            print(f"    Distance: {dist_km:.2f} km")
            print(f"    Duration: {dur_seconds:.0f} seconds = {dur_minutes:.1f} minutes")
            print(f"    Average speed: {(dist_km / (dur_minutes/60)):.1f} km/h" if dur_minutes > 0 else "")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    print(f"API Key configured: {'Yes' if API_KEY else 'NO - MISSING!'}")
    
    if not API_KEY:
        print("Please set OPENROUTESERVICE_API_KEY in .env")
    else:
        test_ors_matrix(test_coords, "Miraflores to Callao (~15km)")
        test_ors_matrix(test_coords_long, "Comas to Miraflores (~20km)")
