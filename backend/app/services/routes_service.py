import requests
from typing import List, Tuple, Dict, Optional
import numpy as np
from geopy.distance import geodesic
import logging

logger = logging.getLogger(__name__)


class RoutesService:
    """
    Routes service for calculating distances and travel times
    
    Uses:
    1. OpenRouteService API (requires free API key) - preferred
    2. Fallback to geodesic distance calculations
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.ors_url = "https://api.openrouteservice.org/v2"
        self.osrm_url = "http://router.project-osrm.org"  # OSRM Public Demo Server
        self.api_key = api_key
        self.use_api = api_key is not None and api_key != ""
        
        if not self.use_api:
            logger.warning("No OpenRouteService API key provided. Will attempt to use OSRM Public API as fallback.")
            
        # Simple in-memory cache for distance matrices
        # Key: tuple of sorted coordinates (to be order-independent for cache hit, though matrix is order-dependent)
        # Value: numpy array
        self._matrix_cache = {}
    
    def get_distance_matrix(
        self,
        coordinates: List[Tuple[float, float]],
        profile: str = "foot-walking"
    ) -> np.ndarray:
        """
        Get distance/time matrix between multiple points
        
        Args:
            coordinates: List of (latitude, longitude) tuples
            profile: "foot-walking", "driving-car", "cycling-regular"
        
        Returns:
            Time matrix in minutes (numpy array)
        """
        # Create a cache key based on coordinates and profile
        # We use a tuple of coordinates as the key
        cache_key = (tuple(coordinates), profile)
        
        if cache_key in self._matrix_cache:
            logger.info("[CACHE] Using CACHED distance matrix")
            return self._matrix_cache[cache_key]

        logger.info(f"[CALC] Calculating distance matrix for {len(coordinates)} points, profile: {profile}")

        # 1. Try OpenRouteService if configured
        if self.use_api:
            logger.info("[ORS] API key present, attempting ORS...")
            try:
                matrix = self._get_ors_matrix(coordinates, profile)
                self._matrix_cache[cache_key] = matrix
                logger.info(f"[ORS OK] Matrix shape {matrix.shape}")
                if len(coordinates) > 1:
                    logger.info(f"   Start->POI times (min): {matrix[0, 1:].tolist()[:5]}")
                return matrix
            except Exception as e:
                logger.error(f"[ORS FAIL] {e}")
        else:
            logger.info("[ORS] No API key, skipping ORS")
        
        # 2. Try OSRM Public API (Project-OSRM)
        logger.info("[OSRM] Attempting OSRM Public API...")
        try:
            matrix = self._get_osrm_matrix(coordinates, profile)
            self._matrix_cache[cache_key] = matrix
            logger.info(f"[OSRM OK] Matrix shape {matrix.shape}")
            if len(coordinates) > 1:
                logger.info(f"   Start->POI times (min): {matrix[0, 1:].tolist()[:5]}")
            return matrix
        except Exception as e:
            logger.warning(f"[OSRM FAIL] {e}")

        # 3. Fallback to geodesic distance
        logger.warning("[GEODESIC] Using straight-line distance (INACCURATE!)")
        matrix = self._calculate_geodesic_matrix(coordinates, profile)
        self._matrix_cache[cache_key] = matrix
        if len(coordinates) > 1:
            logger.info(f"   Geodesic Start->POI times (min): {matrix[0, 1:].tolist()[:5]}")
        return matrix
    
    def _get_ors_matrix(
        self,
        coordinates: List[Tuple[float, float]],
        profile: str
    ) -> np.ndarray:
        """Get matrix from OpenRouteService API"""
        url = f"{self.ors_url}/matrix/{profile}"
        
        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }
        
        # ORS expects [longitude, latitude]
        locations = [[lon, lat] for lat, lon in coordinates]
        
        body = {
            "locations": locations,
            "metrics": ["duration"],
            "units": "m"  # meters and seconds
        }
        
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Convert seconds to minutes
        durations = np.array(data["durations"])
        return durations / 60.0  # Convert to minutes

    def _get_osrm_matrix(
        self,
        coordinates: List[Tuple[float, float]],
        profile: str
    ) -> np.ndarray:
        """Get matrix from OSRM Public API"""
        # Map profiles to OSRM supported profiles
        osrm_profile_map = {
            "driving-car": "driving",
            "cycling-regular": "driving", # OSRM demo often lacks cycling, use driving as approx
            "foot-walking": "walking"
        }
        osrm_profile = osrm_profile_map.get(profile, "driving")
        
        # OSRM URL format: /table/v1/{profile}/{lon},{lat};{lon},{lat}?sources=...
        coords_str = ";".join([f"{lon},{lat}" for lat, lon in coordinates])
        url = f"{self.osrm_url}/table/v1/{osrm_profile}/{coords_str}"
        
        # params = {"sources": "0"} # We want full matrix, so no source filter needed for N*N
        
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("code") != "Ok":
             raise Exception(f"OSRM returned error code: {data.get('code')}")
        
        # Convert seconds to minutes
        durations = np.array(data["durations"])
        # Handle None/null values (unreachable) by replacing with large number or 0
        durations = np.nan_to_num(durations, nan=99999.0)
        
        return durations / 60.0  # Convert to minutes

    def _calculate_geodesic_matrix(
        self,
        coordinates: List[Tuple[float, float]],
        profile: str
    ) -> np.ndarray:
        """
        Calculate distance matrix using geodesic distance
        
        Assumes average speeds:
        - Walking: 4 km/h
        - Cycling: 15 km/h
        - Driving: 30 km/h (city traffic)
        """
        n = len(coordinates)
        matrix = np.zeros((n, n))
        
        # Speed in km/h - Updated for realistic Lima traffic
        speeds = {
            "foot-walking": 4.5,      # Average walking speed
            "cycling-regular": 15.0,
            "driving-car": 25.0       # Lima city traffic average (more realistic)
        }
        speed = speeds.get(profile, 4.5)
        
        for i in range(n):
            for j in range(n):
                if i == j:
                    matrix[i][j] = 0
                else:
                    # Calculate geodesic distance
                    dist_km = geodesic(coordinates[i], coordinates[j]).kilometers
                    
                    # Convert to time in minutes
                    time_hours = dist_km / speed
                    time_minutes = time_hours * 60
                    
                    matrix[i][j] = time_minutes
        
        return matrix
    
    def get_route(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        profile: str = "foot-walking"
    ) -> Optional[Dict]:
        """
        Get detailed route between two points
        
        Returns:
            {
                "distance": float (km),
                "duration": float (minutes),
                "geometry": [...],  # List of coordinates
                "steps": [...]  # Turn-by-turn directions
            }
        """
        # 1. Try OpenRouteService if configured
        if self.use_api:
            try:
                url = f"{self.ors_url}/directions/{profile}"
                
                headers = {
                    "Authorization": self.api_key,
                    "Content-Type": "application/json"
                }
                
                # ORS expects [longitude, latitude]
                body = {
                    "coordinates": [
                        [start[1], start[0]],
                        [end[1], end[0]]
                    ],
                    "instructions": True
                }
                
                response = requests.post(url, json=body, headers=headers, timeout=15)
                response.raise_for_status()
                
                data = response.json()
                
                if "routes" in data and len(data["routes"]) > 0:
                    route = data["routes"][0]
                    summary = route["summary"]
                    
                    return {
                        "distance": summary["distance"] / 1000,  # Convert to km
                        "duration": summary["duration"] / 60,  # Convert to minutes
                        "geometry": route.get("geometry", {}).get("coordinates", []),
                        "steps": route.get("segments", [{}])[0].get("steps", [])
                    }
            except Exception as e:
                logger.error(f"ORS route error: {e}. Falling back to OSRM.")
        
        # 2. Try OSRM Public API
        try:
            result = self._get_osrm_route(start, end, profile)
            if result:
                return result
        except Exception as e:
            logger.warning(f"OSRM route error: {e}. Falling back to geodesic.")
        
        # 3. Fallback: simple straight line
        dist_km = geodesic(start, end).kilometers
        speed = 4.0 if profile == "foot-walking" else 30.0
        duration_min = (dist_km / speed) * 60
        
        return {
            "distance": dist_km,
            "duration": duration_min,
            "geometry": [start, end],
            "steps": []
        }

    def _get_osrm_route(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        profile: str
    ) -> Optional[Dict]:
        """Get route from OSRM Public API"""
        osrm_profile_map = {
            "driving-car": "driving",
            "cycling-regular": "driving",
            "foot-walking": "walking"
        }
        osrm_profile = osrm_profile_map.get(profile, "driving")
        
        # OSRM format: /route/v1/{profile}/{lon},{lat};{lon},{lat}
        coords_str = f"{start[1]},{start[0]};{end[1]},{end[0]}"
        url = f"{self.osrm_url}/route/v1/{osrm_profile}/{coords_str}"
        
        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "true"
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("code") != "Ok" or not data.get("routes"):
            return None
        
        route = data["routes"][0]
        
        return {
            "distance": route["distance"] / 1000,  # meters to km
            "duration": route["duration"] / 60,  # seconds to minutes
            "geometry": route.get("geometry", {}).get("coordinates", []),
            "steps": route.get("legs", [{}])[0].get("steps", [])
        }
    
    def get_isochrone(
        self,
        location: Tuple[float, float],
        time_minutes: int,
        profile: str = "foot-walking"
    ) -> Optional[Dict]:
        """
        Get isochrone (reachable area within time limit)
        
        Args:
            location: (latitude, longitude)
            time_minutes: Time limit in minutes
            profile: Travel profile
        
        Returns:
            GeoJSON polygon of reachable area
        """
        if not self.use_api:
            logger.warning("Isochrone requires ORS API key")
            return None
        
        try:
            url = f"{self.ors_url}/isochrones/{profile}"
            
            headers = {
                "Authorization": self.api_key,
                "Content-Type": "application/json"
            }
            
            body = {
                "locations": [[location[1], location[0]]],
                "range": [time_minutes * 60],  # Convert to seconds
                "range_type": "time"
            }
            
            response = requests.post(url, json=body, headers=headers, timeout=15)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting isochrone: {e}")
            return None
    
    def calculate_route_polyline(
        self,
        waypoints: List[Tuple[float, float]],
        profile: str = "foot-walking"
    ) -> List[Tuple[float, float]]:
        """
        Calculate route through multiple waypoints
        
        Returns list of coordinates forming the route
        """
        if len(waypoints) < 2:
            return waypoints
        
        if not self.use_api:
            # Simple fallback: return waypoints as-is
            return waypoints
        
        try:
            url = f"{self.ors_url}/directions/{profile}"
            
            headers = {
                "Authorization": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Convert to [lon, lat] format
            coordinates = [[wp[1], wp[0]] for wp in waypoints]
            
            body = {
                "coordinates": coordinates,
                "instructions": False
            }
            
            response = requests.post(url, json=body, headers=headers, timeout=20)
            response.raise_for_status()
            
            data = response.json()
            
            if "routes" in data and len(data["routes"]) > 0:
                geometry = data["routes"][0].get("geometry", {})
                coords = geometry.get("coordinates", [])
                
                # Convert back to [lat, lon]
                return [(lat, lon) for lon, lat in coords]
            
            return waypoints
            
        except Exception as e:
            logger.error(f"Error calculating route polyline: {e}")
            return waypoints
