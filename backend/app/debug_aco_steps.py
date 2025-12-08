# backend/app/debug_aco_steps.py
"""
Detailed debug of ACO step-by-step decisions.
Shows exactly why each POI is selected at each step.
"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.poi import POI
from app.services.poi_service import POIService
from app.services.toptw_solver import POINode, TOPTWConstraints, TOPTWSolver
from app.services.optimization_weights import WEIGHTS
from geopy.distance import geodesic
import numpy as np

def debug_aco_steps(
    start_lat: float,
    start_lon: float,
    start_time_str: str = "09:00",
    day_of_week: str = "Monday"
):
    """Debug ACO step by step"""
    db = SessionLocal()
    
    hours, minutes = map(int, start_time_str.split(':'))
    start_time = hours * 60 + minutes
    start_location = (start_lat, start_lon)
    
    print("=" * 100)
    print("ACO STEP-BY-STEP DEBUG")
    print("=" * 100)
    
    # Get POIs
    poi_service = POIService(db)
    all_pois = poi_service.get_all_pois()
    
    pois = []
    for poi in all_pois:
        dist = geodesic(start_location, (poi.latitude, poi.longitude)).kilometers
        if dist <= 5.0:
            pois.append(poi)
    
    print(f"Found {len(pois)} POIs within 5km")
    
    # Create POI nodes
    poi_nodes = []
    for poi in pois[:15]:  # Limit to 15 for clearer debug
        node = POINode(
            id=poi.id,
            name=poi.name,
            latitude=poi.latitude,
            longitude=poi.longitude,
            popularity=poi.popularity or 50,
            opening_time=540,
            closing_time=1200,
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
    
    # Create simple distance matrix (in minutes)
    n = len(poi_nodes)
    time_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                dist = geodesic(
                    (poi_nodes[i].latitude, poi_nodes[i].longitude),
                    (poi_nodes[j].latitude, poi_nodes[j].longitude)
                ).kilometers
                time_matrix[i][j] = int(dist * 3)  # ~3 min per km
    
    # Show distance matrix snippet
    print("\n[DISTANCE MATRIX] (in minutes, first 5 POIs)")
    print("-" * 60)
    print(f"{'':>20}", end="")
    for j in range(min(5, n)):
        print(f"{poi_nodes[j].name[:8]:>10}", end="")
    print()
    
    for i in range(min(5, n)):
        print(f"{poi_nodes[i].name[:20]:>20}", end="")
        for j in range(min(5, n)):
            print(f"{time_matrix[i][j]:>10.0f}", end="")
        print()
    
    # Simulate one ant's construction
    print("\n" + "=" * 100)
    print("SIMULATING ANT CONSTRUCTION")
    print("=" * 100)
    
    # Find first POI (closest to start)
    distances_from_start = []
    for idx, poi in enumerate(poi_nodes):
        dist = geodesic(start_location, (poi.latitude, poi.longitude)).kilometers
        distances_from_start.append((idx, poi.name, dist))
    
    distances_from_start.sort(key=lambda x: x[2])
    
    print("\n[STEP 0] Choosing FIRST POI (by proximity to start)")
    print("-" * 60)
    for idx, name, dist in distances_from_start[:5]:
        print(f"   POI {idx}: {name[:30]:30} - {dist:.2f} km")
    
    current_idx = distances_from_start[0][0]
    print(f"\n   --> Selected: {poi_nodes[current_idx].name} (closest)")
    
    route = [current_idx]
    visited = {current_idx}
    current_time = start_time + poi_nodes[current_idx].visit_duration
    
    # Simulate next steps
    for step in range(1, 4):  # Show 3 more steps
        print(f"\n[STEP {step}] From: {poi_nodes[current_idx].name}")
        print("-" * 60)
        
        candidates = []
        for next_idx in range(n):
            if next_idx in visited:
                continue
            
            next_poi = poi_nodes[next_idx]
            travel_time = time_matrix[current_idx][next_idx]
            
            # Calculate heuristic components (same as ACO)
            dist_score = max(0.0, 1.0 - (travel_time / 60.0))
            pop_score = min(1.0, next_poi.popularity / 100.0)
            
            arrival_time = current_time + travel_time
            time_left = next_poi.closing_time - arrival_time
            urgency_score = max(0.0, min(1.0, 1.0 - (time_left / 300.0)))
            
            rating_score = (next_poi.rating / 5.0) if next_poi.rating else 0.5
            
            # Combined score
            total = (
                (dist_score * WEIGHTS.distance_weight) +
                (pop_score * WEIGHTS.popularity_weight) +
                (urgency_score * WEIGHTS.urgency_weight) +
                (rating_score * WEIGHTS.rating_weight)
            )
            
            candidates.append({
                'idx': next_idx,
                'name': next_poi.name[:25],
                'travel_time': travel_time,
                'dist_score': dist_score,
                'pop_score': pop_score,
                'urgency': urgency_score,
                'rating': rating_score,
                'total': total
            })
        
        # Sort by total score
        candidates.sort(key=lambda x: x['total'], reverse=True)
        
        # Show top 5 candidates
        print(f"{'POI':<25} | {'Travel':>6} | {'Dist':>6} | {'Pop':>5} | {'Urg':>5} | {'Rate':>5} | {'TOTAL':>7}")
        print("-" * 80)
        
        for c in candidates[:5]:
            print(f"{c['name']:<25} | {c['travel_time']:>5}m | {c['dist_score']:>6.3f} | {c['pop_score']:>5.2f} | {c['urgency']:>5.2f} | {c['rating']:>5.2f} | {c['total']:>7.4f}")
        
        # Select best
        if candidates:
            selected = candidates[0]
            current_idx = selected['idx']
            route.append(current_idx)
            visited.add(current_idx)
            current_time += time_matrix[route[-2]][current_idx] + poi_nodes[current_idx].visit_duration
            print(f"\n   --> Selected: {poi_nodes[current_idx].name} (highest score: {selected['total']:.4f})")
    
    # Final route
    print("\n" + "=" * 100)
    print("FINAL ROUTE")
    print("=" * 100)
    for i, idx in enumerate(route, 1):
        poi = poi_nodes[idx]
        dist = geodesic(start_location, (poi.latitude, poi.longitude)).kilometers
        print(f"   {i}. {poi.name} ({dist:.2f} km from start)")
    
    db.close()


if __name__ == "__main__":
    debug_aco_steps(
        start_lat=-11.9226161,
        start_lon=-77.0487985,
        start_time_str="09:00",
        day_of_week="Monday"
    )
