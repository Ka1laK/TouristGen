# backend/app/test_optimizer_flow.py
"""
Complete test script to debug the FULL optimizer flow.
Simulates exactly what optimizer.py does, step by step.
"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.poi import POI
from app.services.poi_service import POIService
from app.services.routes_service import RoutesService
from app.services.aco_optimizer import AntColonyOptimizer
from app.services.toptw_solver import POINode, TOPTWConstraints, TOPTWSolver
from app.services.hours_utils import is_poi_available, calculate_urgency_weight
from geopy.distance import geodesic
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_full_optimization(
    start_lat: float,
    start_lon: float,
    start_time: str = "09:00",
    day_of_week: str = "Monday",
    max_duration: int = 480,
    max_budget: float = 200,
    transport_mode: str = "driving-car"
):
    """
    Simulate the full optimization process from optimizer.py
    """
    db = SessionLocal()
    
    # Convert time to minutes
    hours, minutes = map(int, start_time.split(':'))
    start_time_minutes = hours * 60 + minutes
    
    start_location = (start_lat, start_lon)
    
    print("=" * 100)
    print("FULL OPTIMIZER FLOW TEST")
    print("=" * 100)
    print(f"Start Location: {start_location}")
    print(f"Start Time: {start_time} ({start_time_minutes} min)")
    print(f"Day: {day_of_week}")
    print(f"Max Duration: {max_duration} min")
    print(f"Max Budget: ${max_budget}")
    print("=" * 100)
    
    # ============================================================
    # STEP 1: Get POIs (similar to optimizer.py)
    # ============================================================
    print("\n[STEP 1] Fetching POIs from database...")
    
    poi_service = POIService(db)
    all_pois = poi_service.get_all_pois()
    
    # Filter by distance (like optimizer does)
    pois = []
    for poi in all_pois:
        dist = geodesic((start_lat, start_lon), (poi.latitude, poi.longitude)).kilometers
        if dist <= 5.0:  # 5km radius
            pois.append(poi)
    
    print(f"   -> Total POIs in DB: {len(all_pois)}")
    print(f"   -> Found {len(pois)} POIs within 5km of start location")
    
    # ============================================================
    # STEP 2: Convert to POINode objects
    # ============================================================
    print("\n[STEP 2] Converting to POINode objects...")
    
    poi_nodes = []
    for poi in pois:
        node = POINode(
            id=poi.id,
            name=poi.name,
            latitude=poi.latitude,
            longitude=poi.longitude,
            popularity=poi.popularity or 50,
            opening_time=540,  # 9am default
            closing_time=1200, # 8pm default
            visit_duration=poi.visit_duration or 60,
            price=float(poi.price_level or 0) * 10,
            category=poi.category or "General",
            district=poi.district or "Unknown",
            opening_hours=poi.opening_hours if poi.opening_hours else {},
            phone=poi.phone,
            rating=poi.rating or 0.0,
            tags=poi.tags or []
        )
        poi_nodes.append(node)
    
    print(f"   -> Created {len(poi_nodes)} POINode objects")
    
    # ============================================================
    # STEP 3: Filter by availability (like optimizer.py does)
    # ============================================================
    print(f"\n[STEP 3] Filtering POIs by availability ({day_of_week} @ {start_time})...")
    
    available_pois = []
    filtered_out = []
    for poi in poi_nodes:
        if is_poi_available(poi.opening_hours, day_of_week, start_time_minutes):
            available_pois.append(poi)
        else:
            filtered_out.append(poi)
    
    print(f"   -> Available: {len(available_pois)}")
    print(f"   -> Filtered out (closed): {len(filtered_out)}")
    if filtered_out:
        print(f"   -> Filtered names: {[p.name[:30] for p in filtered_out[:5]]}")
    
    poi_nodes = available_pois
    
    # ============================================================
    # STEP 4: Create constraints
    # ============================================================
    print("\n[STEP 4] Creating constraints...")
    
    constraints = TOPTWConstraints(
        max_duration=max_duration,
        max_budget=max_budget,
        start_time=start_time_minutes,
        user_pace="medium",
        mandatory_categories=[],
        avoid_categories=[],
        preferred_districts=[],
        weather_conditions={},
        transport_mode=transport_mode,
        day_of_week=day_of_week
    )
    print(f"   -> Constraints created successfully")
    
    # ============================================================
    # STEP 5: Calculate distance matrix
    # ============================================================
    print("\n[STEP 5] Calculating distance matrix...")
    
    routes_service = RoutesService()
    coordinates = [(poi.latitude, poi.longitude) for poi in poi_nodes]
    
    try:
        time_matrix = routes_service.get_distance_matrix(coordinates, profile=transport_mode)
        print(f"   -> Matrix shape: {time_matrix.shape}")
    except Exception as e:
        print(f"   -> ERROR getting distance matrix: {e}")
        print("   -> Using geodesic fallback...")
        n = len(coordinates)
        time_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i != j:
                    dist = geodesic(coordinates[i], coordinates[j]).kilometers
                    time_matrix[i][j] = int(dist * 3)  # ~3 min per km
    
    # ============================================================
    # STEP 6: Run ACO Optimizer
    # ============================================================
    print("\n[STEP 6] Running ACO Optimizer...")
    print(f"   -> Start location tuple: {start_location}")
    
    aco = AntColonyOptimizer(
        pois=poi_nodes,
        constraints=constraints,
        num_ants=40,
        iterations=80,
        alpha=1.0,
        beta=2.5,
        start_location=start_location
    )
    
    aco.set_distance_matrix(time_matrix)
    
    print("   -> Running ACO solve()...")
    best_route, best_fitness = aco.solve(verbose=False)
    
    print(f"   -> Best route has {len(best_route)} POIs")
    print(f"   -> Best fitness: {best_fitness:.2f}")
    
    # ============================================================
    # STEP 7: Analyze the route order
    # ============================================================
    print("\n" + "=" * 100)
    print("ROUTE ANALYSIS")
    print("=" * 100)
    
    if best_route:
        print(f"\n{'Order':>5} | {'ID':>4} | {'POI Name':<40} | {'Dist from Start':>14} | {'Urgency':>7}")
        print("-" * 100)
        
        for order, idx in enumerate(best_route, 1):
            poi = poi_nodes[idx]
            dist_from_start = geodesic(start_location, (poi.latitude, poi.longitude)).kilometers
            urgency = calculate_urgency_weight(
                poi.opening_hours,
                day_of_week,
                start_time_minutes,
                poi.visit_duration
            )
            print(f"{order:>5} | {poi.id:>4} | {poi.name[:40]:<40} | {dist_from_start:>12.2f}km | {urgency:>7.2f}")
        
        print("-" * 100)
        
        # Check if first POI is the closest
        first_idx = best_route[0]
        first_poi = poi_nodes[first_idx]
        first_dist = geodesic(start_location, (first_poi.latitude, first_poi.longitude)).kilometers
        
        # Find actual closest
        min_dist = float('inf')
        closest_idx = 0
        for idx, poi in enumerate(poi_nodes):
            dist = geodesic(start_location, (poi.latitude, poi.longitude)).kilometers
            if dist < min_dist:
                min_dist = dist
                closest_idx = idx
        
        closest_poi = poi_nodes[closest_idx]
        
        print(f"\n[INFO] First POI in route: {first_poi.name} ({first_dist:.2f} km from start)")
        print(f"[INFO] Closest POI overall: {closest_poi.name} ({min_dist:.2f} km from start)")
        
        if first_idx != closest_idx:
            first_urgency = calculate_urgency_weight(
                first_poi.opening_hours, day_of_week, start_time_minutes, first_poi.visit_duration
            )
            closest_urgency = calculate_urgency_weight(
                closest_poi.opening_hours, day_of_week, start_time_minutes, closest_poi.visit_duration
            )
            print(f"\n[CHECK] First POI urgency: {first_urgency}")
            print(f"[CHECK] Closest POI urgency: {closest_urgency}")
            
            first_combined = first_urgency * (1.0 / (1.0 + first_dist * 0.2))
            closest_combined = closest_urgency * (1.0 / (1.0 + min_dist * 0.2))
            print(f"[CHECK] First POI combined score: {first_combined:.4f}")
            print(f"[CHECK] Closest POI combined score: {closest_combined:.4f}")
            
            if first_combined > closest_combined:
                print("\n[EXPLAIN] First POI was chosen because it has a HIGHER combined score")
                print("          (urgency compensates for distance)")
            else:
                print("\n[WARNING] Something unexpected - closest has higher score but wasn't chosen")
    
    db.close()
    return best_route, best_fitness


if __name__ == "__main__":
    print("\n" + "=" * 100)
    print("OPTIMIZER FLOW TEST")
    print("=" * 100 + "\n")
    
    # Use coordinates similar to the user's test case (Comas area)
    # Adjust these to match your specific test
    result = test_full_optimization(
        start_lat=-11.9333,   # Comas area
        start_lon=-77.0461,
        start_time="09:00",
        day_of_week="Monday",
        max_duration=480,
        max_budget=200,
        transport_mode="driving-car"
    )
    
    print("\n" + "=" * 100)
    print("TEST COMPLETE")
    print("=" * 100)
