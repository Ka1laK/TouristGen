import json
import logging
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.poi import POI
from app.database import Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_pois(json_file: str):
    """Import POIs from a JSON file into the database"""
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            pois_data = json.load(f)
            
        logger.info(f"Loaded {len(pois_data)} POIs from {json_file}")
        
        count_new = 0
        count_updated = 0
        
        for poi_data in pois_data:
            # Check if POI already exists (by name and district)
            existing_poi = session.query(POI).filter(
                POI.name == poi_data["name"],
                POI.district == poi_data["district"]
            ).first()
            
            if existing_poi:
                # Update existing POI
                logger.info(f"Updating existing POI: {poi_data['name']}")
                for key, value in poi_data.items():
                    if hasattr(existing_poi, key):
                        setattr(existing_poi, key, value)
                count_updated += 1
            else:
                # Create new POI
                logger.info(f"Creating new POI: {poi_data['name']}")
                new_poi = POI(**poi_data)
                # Set default popularity if not provided
                if not hasattr(new_poi, 'popularity') or new_poi.popularity is None:
                    new_poi.popularity = int(poi_data.get('rating', 3.0) * 20) # Estimate popularity from rating
                
                session.add(new_poi)
                count_new += 1
        
        session.commit()
        logger.info(f"Import complete. New: {count_new}, Updated: {count_updated}")
        
    except Exception as e:
        logger.error(f"Error importing POIs: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    import_pois("san_miguel_pois.json")
