from app.database import SessionLocal
from app.models.poi import POI
from app.services.hours_utils import is_poi_available

db = SessionLocal()
pois = db.query(POI).filter(POI.is_active == True).limit(10).all()

print('Testing POI availability for Monday 09:00')
for p in pois:
    available = is_poi_available(p.opening_hours, "Monday", 540, p.visit_duration)
    print(f'{p.id}: {p.name[:35]} - available: {available}')
    print(f'   hours: {p.opening_hours}')

db.close()
