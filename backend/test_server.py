"""
Ultra-simple FastAPI server for testing
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Server is working!", "status": "ok"}


@app.post("/api/optimize/quick-route")
def quick_route(data: dict):
    print(f"Received request: {data}")
    
    return {
        "route_id": "test_123",
        "route": [
            {"id": 1, "name": "Parque Kennedy", "latitude": -12.1203, "longitude": -77.0294, "district": "Miraflores", "category": "Park", "popularity": 85, "rating": 4.5, "price_level": 1, "visit_duration": 45, "tags": [], "description": "Iconic park"}
        ],
        "timeline": [
            {"poi_id": 1, "poi_name": "Parque Kennedy", "category": "Park", "district": "Miraflores", "arrival_time": "09:00", "departure_time": "09:45", "visit_duration": 45, "travel_time": 0, "wait_time": 0, "price": 10.0, "latitude": -12.1203, "longitude": -77.0294}
        ],
        "total_duration": 45,
        "total_cost": 10.0,
        "fitness_score": 100.0,
        "start_time": "09:00",
        "end_time": "09:45",
        "num_pois": 1
    }


if __name__ == "__main__":
    import uvicorn
    print("Starting ultra-simple server on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
