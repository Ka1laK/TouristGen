"""
Debug what the optimizer actually sees for travel times
"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.services.poi_service import POIService
from app.services.routes_service import RoutesService
from app.config import settings
import numpy as np

def debug_actual_times():
    print("="*60)
    print("DEBUGGING ACTUAL TRAVEL TIMES IN OPTIMIZER")
    print("="*60)
    
    db = SessionLocal()
    poi_service = POIService(db)
    
    # Get some POIs
    pois = poi_service.get_all_pois()[:5]
    
    print(f"\nUsing {len(pois)} POIs:")
    for i, poi in enumerate(pois):
        print(f"  [{i}] {poi.name} ({poi.latitude:.4f}, {poi.longitude:.4f})")
    
    # Get distance matrix
    routes_service = RoutesService(api_key=settings.openrouteservice_api_key)
    coordinates = [(poi.latitude, poi.longitude) for poi in pois]
    
    print(f"\nAPI Key: {'Configured' if settings.openrouteservice_api_key else 'MISSING'}")
    print(f"Calculating distance matrix for driving-car...")
    
    time_matrix = routes_service.get_distance_matrix(coordinates, profile="driving-car")
    
    print(f"\nMatrix shape: {time_matrix.shape}")
    print(f"\nTravel times (in MINUTES):")
    
    # Print matrix
    header = "       " + "".join([f"[{i:2d}]    " for i in range(len(pois))])
    print(header)
    
    for i in range(len(pois)):
        row = f"[{i:2d}]   "
        for j in range(len(pois)):
            row += f"{time_matrix[i][j]:6.1f}  "
        print(row)
    
    print("\nPairwise travel times:")
    for i in range(len(pois)):
        for j in range(i+1, len(pois)):
            from geopy.distance import geodesic
            dist = geodesic(coordinates[i], coordinates[j]).kilometers
            time = time_matrix[i][j]
            print(f"  {pois[i].name[:20]:20s} → {pois[j].name[:20]:20s}: {time:5.1f} min ({dist:.1f} km)")
    
    db.close()

if __name__ == "__main__":
    debug_actual_times()
