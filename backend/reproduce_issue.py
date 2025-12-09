import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reproduce")

API_URL = "http://localhost:8000/api/optimize/generate-route"

def run_test():
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
        "latitude": -11.9873089,
        "longitude": -77.0694147
      },
      "selected_poi_ids": [
        469,
        474,
        1166
      ]
    }
    
    logger.info("Sending user payload...")
    try:
        response = requests.post(API_URL, json=payload)
        logger.info(f"Status: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Response: {response.text}")
        else:
            logger.info("Success!")
            print(json.dumps(response.json(), indent=2))
            
    except Exception as e:
        logger.error(f"Failed: {e}")

if __name__ == "__main__":
    run_test()
