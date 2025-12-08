# backend/app/debug_optimizer.py
"""
Debug script to visualize the POI selection and scoring process.
Run this to understand why the optimizer chooses a specific order.
"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.poi import POI
from app.services.toptw_solver import POINode, TOPTWConstraints, TOPTWSolver
from app.services.hours_utils import calculate_urgency_weight
from geopy.distance import geodesic
import json

def debug_poi_selection(
    start_lat: float,
    start_lon: float,
    start_time: str = "09:00",
    day_of_week: str = "Monday",
    radius_km: float = 5.0
):
    """
    Debug the POI selection process.
    Shows why each POI gets a specific score and order.
    """
    db = SessionLocal()
    
    # Convert time to minutes
    hours, minutes = map(int, start_time.split(':'))
    start_time_minutes = hours * 60 + minutes
    
    print("=" * 80)
    print("[DEBUG] POI Selection Process")
    print("=" * 80)
    print(f"[START] Location: ({start_lat}, {start_lon})")
    print(f"[TIME] Start Time: {start_time} ({start_time_minutes} minutes from midnight)")
    print(f"[DAY] Day: {day_of_week}")
    print(f"[RADIUS] Search Radius: {radius_km} km")
    print("=" * 80)
    
    # Get POIs near the start location
    pois = db.query(POI).filter(POI.is_active == True).all()
    
    nearby_pois = []
    for poi in pois:
        dist = geodesic((start_lat, start_lon), (poi.latitude, poi.longitude)).kilometers
        if dist <= radius_km:
            nearby_pois.append((poi, dist))
    
    print(f"\n[FOUND] {len(nearby_pois)} POIs within {radius_km} km")
    print("-" * 80)
    
    # Calculate scores for each POI
    scored_pois = []
    for poi, distance in nearby_pois:
        # Urgency weight
        opening_hours = poi.opening_hours if poi.opening_hours else {}
        urgency = calculate_urgency_weight(
            opening_hours,
            day_of_week,
            start_time_minutes,
            poi.visit_duration or 60
        )
        
        # Distance score (closer = higher)
        distance_score = 1.0 / (1.0 + distance * 0.2)
        
        # Combined score
        combined_score = urgency * distance_score
        
        scored_pois.append({
            'id': poi.id,
            'name': poi.name[:40],
            'category': poi.category,
            'district': poi.district,
            'distance_km': round(distance, 2),
            'distance_score': round(distance_score, 3),
            'urgency': round(urgency, 3),
            'combined_score': round(combined_score, 4),
            'opening_hours': opening_hours,
            'popularity': poi.popularity
        })
    
    # Sort by combined score (descending)
    scored_pois.sort(key=lambda x: x['combined_score'], reverse=True)
    
    print("\n[RANKING] POI RANKING (sorted by combined_score)")
    print("-" * 80)
    print(f"{'#':>3} | {'ID':>4} | {'Name':<40} | {'Dist':>6} | {'DistScore':>8} | {'Urgency':>7} | {'Combined':>8}")
    print("-" * 80)
    
    for i, poi in enumerate(scored_pois[:20], 1):  # Top 20
        print(f"{i:>3} | {poi['id']:>4} | {poi['name']:<40} | {poi['distance_km']:>5}km | {poi['distance_score']:>8} | {poi['urgency']:>7} | {poi['combined_score']:>8}")
    
    print("-" * 80)
    
    # Show POIs with urgency = 0 (closed)
    closed_pois = [p for p in scored_pois if p['urgency'] == 0]
    if closed_pois:
        print(f"\n[CLOSED] POIs ({len(closed_pois)} total - urgency = 0)")
        for poi in closed_pois[:5]:
            print(f"   - {poi['name']} (opening_hours: {poi['opening_hours']})")
    
    # Show analysis
    print("\n" + "=" * 80)
    print("[ANALYSIS]")
    print("=" * 80)
    
    if scored_pois:
        first = scored_pois[0]
        print(f"[OK] First POI selected: {first['name']}")
        print(f"   - Distance: {first['distance_km']} km (score: {first['distance_score']})")
        print(f"   - Urgency: {first['urgency']}")
        print(f"   - Combined: {first['combined_score']}")
        print(f"   - Opening Hours: {first['opening_hours']}")
        
        # Compare with closest POI
        closest = min(scored_pois, key=lambda x: x['distance_km'])
        if closest['id'] != first['id']:
            print(f"\n[WARN] Closest POI is different: {closest['name']} ({closest['distance_km']} km)")
            print(f"   - Its combined score: {closest['combined_score']} vs first's {first['combined_score']}")
            print(f"   - Urgency difference: {first['urgency'] - closest['urgency']}")
    
    db.close()
    return scored_pois


if __name__ == "__main__":
    # Example: Debug with a specific start location
    # Comas area (from the user's screenshot)
    
    print("\n" + ">>> " * 20)
    print("Running POI Selection Debug...")
    print(">>> " * 20 + "\n")
    
    # Test case 2: Miraflores at 7pm (some places should be closing soon)
    START_LAT = -12.1191  # Miraflores
    START_LON = -77.0311
    START_TIME = "19:00"  # 7pm - many places close at 10pm, so urgency should vary
    DAY = "Monday"
    
    results = debug_poi_selection(
        start_lat=START_LAT,
        start_lon=START_LON,
        start_time=START_TIME,
        day_of_week=DAY,
        radius_km=5.0
    )
    
    print("\n[DONE] Debug complete. Review the scores to understand POI selection.")
