import sys
sys.path.insert(0, '.')

from app.services.routes_service import RoutesService

# Test OSRM matrix with sample coordinates
coords = [
    (-12.1268334, -77.0297725),  # Start location
    (-12.1191, -77.0311),        # Kennedy Park
    (-12.1183, -77.0277)         # Another POI
]

service = RoutesService()  # No API key
print("Testing OSRM matrix...")

try:
    matrix = service.get_distance_matrix(coords, profile="driving-car")
    print(f"Matrix shape: {matrix.shape}")
    print(f"Matrix:\n{matrix}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
