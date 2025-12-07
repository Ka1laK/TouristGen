import sys
import os
import requests
import json

# Add the backend directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

def test_autofetch():
    print("--- TEST AUTO-FETCH (COMAS) ---")
    
    # Comas coordinates (approx)
    comas_lat = -11.9333
    comas_lon = -77.0500
    
    # URL for generate-route (mimicking frontend request)
    url = "http://localhost:8000/api/optimize/generate-route"
    
    payload = {
        "start_location": {
            "latitude": comas_lat,
            "longitude": comas_lon
        },
        "max_duration": 240,
        "max_budget": 100,
        "start_time": "10:00",
        "transport_mode": "driving-car"
    }
    
    print(f"Requesting route from Comas ({comas_lat}, {comas_lon})...")
    print("Expected behavior: Backend should pause, fetch Comas POIs from Google, and return a route.")
    
    try:
        # Note: This requires the backend to be running.
        # We can also test by invoking the service directly if backend is not running, 
        # but integration test is better.
        # Let's check if backend is running first? 
        # If not, we'll unit test the extraction logic directly.
        
        try:
             response = requests.post(url, json=payload, timeout=60) # Long timeout for fetch
             if response.status_code == 200:
                 print("Success! Route generated.")
                 data = response.json()
                 print(f"Route ID: {data['route_id']}")
                 print(f"POIs in route: {len(data['route'])}")
                 for p in data['route']:
                     print(f"- {p['name']} ({p.get('district', 'Unknown')})")
                 return True
             else:
                 print(f"Request failed: {response.status_code} - {response.text}")
                 return False
        except requests.exceptions.ConnectionError:
            print("Backend not running. Testing via direct service call...")
            
            # Direct service test
            from app.services.maps_service import LimaPlacesExtractor
            from app.services.poi_service import POIService
            from app.database import SessionLocal
            
            db = SessionLocal()
            extractor = LimaPlacesExtractor()
            
            print("Calling fetch_pois_by_coordinates directly...")
            count = extractor.fetch_pois_by_coordinates(comas_lat, comas_lon, radius=2000)
            print(f"Fetched {count} POIs.")
            
            # Verify in DB
            poi_service = POIService(db)
            nearby = poi_service.count_pois_near(comas_lat, comas_lon, radius_km=3.0)
            print(f"POIs in DB near target: {nearby}")
            
            db.close()
            return count > 0

    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))
    test_autofetch()
