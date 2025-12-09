import requests
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verification")

API_URL = "http://localhost:8000/api/optimize/generate-route"

def test_route_generation():
    # Payload simulating user request in Miraflores
    payload = {
        "max_duration": 240,  # 4 hours
        "max_budget": 200.0,
        "start_time": "10:00",
        "user_pace": "medium",
        "mandatory_categories": [],
        "avoid_categories": [],
        "preferred_districts": ["Miraflores"],
        "start_location": {
            "latitude": -12.119,  # Near Parque Kennedy
            "longitude": -77.029
        },
        "transport_mode": "driving-car",
        "day_of_week": "Saturday"
    }
    
    logger.info("Sending request...")
    try:
        response = requests.post(API_URL, json=payload)
        
        if response.status_code != 200:
            logger.error(f"Error: {response.status_code}")
            logger.error(response.text)
            return
            
        data = response.json()
        
        timeline = data.get("timeline", [])
        if not timeline:
            logger.warning("No timeline returned")
            return
            
        first_item = timeline[0]
        travel_time = first_item.get("travel_time")
        poi_name = first_item.get("poi_name")
        
        logger.info(f"Route Generated!")
        logger.info(f"First POI: {poi_name}")
        logger.info(f"Travel Time from Start: {travel_time} minutes")
        
        if travel_time < 3 and travel_time > 0:
            logger.warning("Travel time is suspiciously low (< 3 min). Likely fallback to Geodesic.")
        elif travel_time == 0:
             logger.warning("Travel time is 0. Start location might be same as POI.")
        else:
            logger.info("Travel time looks reasonable (>= 3 min).")
            
    except Exception as e:
        logger.error(f"Request failed: {e}")

if __name__ == "__main__":
    test_route_generation()
