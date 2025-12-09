import sys
sys.path.insert(0, '.')
import traceback

print("=" * 60)
print("STEP-BY-STEP DEBUG")
print("=" * 60)

try:
    print("\n1. Importing modules...")
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    from app.services.poi_service import POIService
    from app.services.weather_service import WeatherService
    from app.services.routes_service import RoutesService
    from app.services.aco_optimizer import AntColonyOptimizer
    from app.services.toptw_solver import POINode, TOPTWConstraints
    from app.services.hours_utils import is_poi_available
    from app.config import settings
    print("   OK")
    
    print("\n2. Creating DB session...")
    db = SessionLocal()
    poi_service = POIService(db)
    routes_service = RoutesService(api_key=settings.openrouteservice_api_key)
    print("   OK")
    
    print("\n3. Getting POIs...")
    poi_ids = [410, 407]
    pois = [poi_service.get_poi_by_id(pid) for pid in poi_ids]
    pois = [p for p in pois if p is not None]
    print(f"   Found {len(pois)} POIs: {[p.name for p in pois]}")
    
    print("\n4. Checking availability...")
    start_time_minutes = 540  # 09:00
    day_of_week = "Tuesday"
    available_pois = []
    for poi in pois:
        is_avail = is_poi_available(poi.opening_hours, day_of_week, start_time_minutes, poi.visit_duration)
        print(f"   {poi.name}: {'AVAILABLE' if is_avail else 'UNAVAILABLE'}")
        if is_avail:
            available_pois.append(poi)
    pois = available_pois
    print(f"   After filter: {len(pois)} POIs")
    
    if not pois:
        print("   ERROR: No POIs available!")
        sys.exit(1)
    
    print("\n5. Creating POINode objects...")
    poi_nodes = []
    for poi in pois:
        poi_node = POINode(
            id=poi.id,
            name=poi.name,
            latitude=poi.latitude,
            longitude=poi.longitude,
            popularity=poi.popularity,
            opening_time=540,
            closing_time=1260,
            visit_duration=poi.visit_duration,
            category=poi.category,
            price=0.0,
            rating=poi.rating or 4.0,
            tags=[],
            district=poi.district or "Unknown",
            opening_hours=poi.opening_hours,
            phone=poi.phone
        )
        poi_nodes.append(poi_node)
    print(f"   Created {len(poi_nodes)} POINode objects")
    
    print("\n6. Creating constraints...")
    constraints = TOPTWConstraints(
        max_duration=480,
        max_budget=200,
        start_time=start_time_minutes,
        user_pace="medium",
        mandatory_categories=[],
        avoid_categories=[],
        preferred_districts=[],
        weather_conditions={},
        transport_mode="driving-car",
        day_of_week="Tuesday"
    )
    print("   OK")
    
    print("\n7. Getting distance matrix...")
    start_loc = (-12.1268334, -77.0297725)
    all_coords = [start_loc] + [(p.latitude, p.longitude) for p in poi_nodes]
    print(f"   Coordinates: {len(all_coords)} points")
    matrix = routes_service.get_distance_matrix(all_coords, profile="driving-car")
    print(f"   Matrix shape: {matrix.shape}")
    print(f"   Matrix:\n{matrix}")
    
    start_to_poi_times = matrix[0, 1:].tolist()
    time_matrix = matrix[1:, 1:]
    print(f"   Start to POI times: {start_to_poi_times}")
    
    print("\n8. Creating ACO optimizer...")
    aco = AntColonyOptimizer(
        pois=poi_nodes,
        constraints=constraints,
        num_ants=40,
        iterations=80,
        alpha=1.0,
        beta=2.5,
        start_location=start_loc
    )
    print("   OK")
    
    print("\n9. Setting distance matrix...")
    aco.set_distance_matrix(time_matrix)
    print("   OK")
    
    print("\n10. Setting start_to_poi_times...")
    aco.set_start_to_poi_times(start_to_poi_times)
    print("   OK")
    
    print("\n11. Running ACO solve...")
    best_route, best_fitness = aco.solve(verbose=True)
    print(f"   Best route: {best_route}")
    print(f"   Best fitness: {best_fitness}")
    
    print("\n12. Getting route details...")
    details = aco.solver.get_route_details(best_route, start_location=start_loc)
    print(f"   Timeline items: {len(details.get('timeline', []))}")
    print(f"   Total duration: {details.get('total_duration')}")
    
    print("\n" + "=" * 60)
    print("SUCCESS!")
    print("=" * 60)
    
    db.close()
    
except Exception as e:
    print(f"\nERROR at step: {e}")
    traceback.print_exc()
