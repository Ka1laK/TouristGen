import sys
sys.path.insert(0, '.')
import traceback

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.poi_service import POIService
from app.services.hours_utils import is_poi_available

db = SessionLocal()
poi_service = POIService(db)

# User's selected POI IDs
poi_ids = [410, 407]
day_of_week = "Tuesday"
start_time_minutes = 540  # 09:00

print(f"Checking POIs {poi_ids} for availability on {day_of_week} at 9:00...")

for poi_id in poi_ids:
    poi = poi_service.get_poi_by_id(poi_id)
    if poi is None:
        print(f"POI {poi_id}: NOT FOUND in database!")
        continue
        
    print(f"\nPOI {poi_id}: {poi.name}")
    print(f"  Opening Hours: {poi.opening_hours}")
    print(f"  Visit Duration: {poi.visit_duration}")
    
    is_avail = is_poi_available(
        poi.opening_hours,
        day_of_week,
        start_time_minutes,
        poi.visit_duration
    )
    print(f"  Available: {is_avail}")

db.close()
