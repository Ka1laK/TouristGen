import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_osrm")

API_URL = "http://localhost:8000/api/optimize/generate-route"

def test_osrm_integration():
    payload = {
        "max_duration": 240,
        "max_budget": 100,
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

    logger.info("Sending request to generate route...")
    try:
        response = requests.post(API_URL, json=payload, timeout=60)
        
        if response.status_code != 200:
            logger.error(f"Error: {response.status_code}")
            logger.error(response.text[:500])
            return
        
        data = response.json()
        timeline = data.get("timeline", [])
        
        if not timeline:
            logger.warning("No timeline returned")
            return
        
        first_item = timeline[0]
        travel_time = first_item.get("travel_time", 0)
        poi_name = first_item.get("poi_name", "Unknown")
        
        logger.info(f"First POI: {poi_name}")
        logger.info(f"Travel Time to First POI: {travel_time} minutes")
        
        if travel_time >= 5:
            logger.info("SUCCESS: Travel time is reasonable (>= 5 min). OSRM integration is working!")
        elif travel_time > 0 and travel_time < 5:
            logger.warning("Travel time is low (<5 min) - POI might be very close or still using geodesic.")
        else:
            logger.warning("Travel time is 0 - check start location or debugging needed.")
            
    except Exception as e:
        logger.error(f"Request failed: {e}")

if __name__ == "__main__":
    test_osrm_integration()
