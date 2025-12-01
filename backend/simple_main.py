"""
Simplified main.py for testing - minimal version
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TouristGen Pro - Simple")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuickRouteRequest(BaseModel):
    max_duration: int = 480
    max_budget: float = 200
    start_time: str = "09:00"
    preferred_districts: List[str] = []


@app.get("/")
def root():
    logger.info("Root endpoint called")
    return {"message": "TouristGen Pro API - Simple Version", "status": "running"}


@app.post("/api/optimize/quick-route")
def quick_route(request: QuickRouteRequest):
    logger.info(f"Quick route called with: {request}")
    
    # Mock response with sample POIs
    response = {
        "route_id": "quick_test_123",
        "route": [
            {
                "id": 1,
                "name": "Parque Kennedy",
                "latitude": -12.1203,
                "longitude": -77.0294,
                "district": "Miraflores",
                "category": "Park",
                "popularity": 85,
                "rating": 4.5,
                "price_level": 1,
                "visit_duration": 45
            },
            {
                "id": 2,
                "name": "Larcomar",
                "latitude": -12.1344,
                "longitude": -77.0256,
                "district": "Miraflores",
                "category": "Shopping",
                "popularity": 90,
                "rating": 4.6,
                "price_level": 3,
                "visit_duration": 120
            },
            {
                "id": 3,
                "name": "Puente de los Suspiros",
                "latitude": -12.1489,
                "longitude": -77.0219,
                "district": "Barranco",
                "category": "Landmark",
                "popularity": 85,
                "rating": 4.6,
                "price_level": 1,
                "visit_duration": 20
            }
        ],
        "timeline": [
            {
                "poi_id": 1,
                "poi_name": "Parque Kennedy",
                "category": "Park",
                "district": "Miraflores",
                "arrival_time": "09:00",
                "departure_time": "09:45",
                "visit_duration": 45,
                "travel_time": 0,
                "wait_time": 0,
                "price": 10.0,
                "latitude": -12.1203,
                "longitude": -77.0294
            },
            {
                "poi_id": 2,
                "poi_name": "Larcomar",
                "category": "Shopping",
                "district": "Miraflores",
                "arrival_time": "10:00",
                "departure_time": "12:00",
                "visit_duration": 120,
                "travel_time": 15,
                "wait_time": 0,
                "price": 30.0,
                "latitude": -12.1344,
                "longitude": -77.0256
            },
            {
                "poi_id": 3,
                "poi_name": "Puente de los Suspiros",
                "category": "Landmark",
                "district": "Barranco",
                "arrival_time": "12:20",
                "departure_time": "12:40",
                "visit_duration": 20,
                "travel_time": 20,
                "wait_time": 0,
                "price": 10.0,
                "latitude": -12.1489,
                "longitude": -77.0219
            }
        ],
        "total_duration": 220,
        "total_cost": 50.0,
        "fitness_score": 250.0,
        "start_time": "09:00",
        "end_time": "12:40",
        "num_pois": 3,
        "weather_summary": None
    }
    
    logger.info("Returning quick route response")
    return response


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting simple server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
