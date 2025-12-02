"""
Quick route generator - uses real database and OpenRouteService for route geometry
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import requests

from app.database import get_db
from app.services.poi_service import POIService
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


class QuickOptimizationRequest(BaseModel):
    max_duration: int = Field(480, description="Maximum trip duration in minutes")
    max_budget: float = Field(200, description="Maximum budget")
    start_time: str = Field("09:00", description="Start time in HH:MM format")
    user_pace: str = Field("medium", description="Walking pace")
    mandatory_categories: List[str] = Field(default=[], description="Must visit categories")
    avoid_categories: List[str] = Field(default=[], description="Categories to avoid")
    preferred_districts: List[str] = Field(default=[], description="Preferred districts")
    start_location: Optional[Dict] = Field(None, description="Start location")
    selected_poi_ids: Optional[List[int]] = Field(None, description="Specific POI IDs to include in route")
    transport_mode: str = Field("driving-car", description="Transport mode")


def get_route_geometry(coordinates: List[tuple], profile="foot-walking") -> List[Dict]:
    """
    Get route geometry from OpenRouteService or fallback to geodesic
    Returns list of route segments with geometry
    """
    route_segments = []
    
    # Try OpenRouteService if API key is available
    if settings.openrouteservice_api_key:
        try:
            # Format coordinates for ORS (lon, lat format)
            ors_coords = [[lon, lat] for lat, lon in coordinates]
            
            url = "https://api.openrouteservice.org/v2/directions/foot-walking/geojson"
            headers = {
                "Authorization": settings.openrouteservice_api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "coordinates": ors_coords,
                "instructions": True,
                "elevation": False
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract route segments from GeoJSON
                if "features" in data and len(data["features"]) > 0:
                    feature = data["features"][0]
                    geometry = feature["geometry"]
                    properties = feature["properties"]
                    
                    # Get segments from the route
                    segments = properties.get("segments", [])
                    
                    for i, segment in enumerate(segments):
                        route_segments.append({
                            "coordinates": geometry["coordinates"],
                            "distance": segment.get("distance", 0),
                            "duration": segment.get("duration", 0),
                            "steps": segment.get("steps", [])
                        })
                    
                    logger.info(f"Successfully got route geometry from OpenRouteService")
                    return route_segments
            else:
                logger.warning(f"OpenRouteService returned status {response.status_code}")
        except Exception as e:
            logger.error(f"Error getting route from OpenRouteService: {e}")
    
    # Fallback: return straight lines between points
    logger.info("Using fallback: generating straight-line geometry")
    
    fallback_geometry = []
    for i in range(len(coordinates) - 1):
        start = coordinates[i]
        end = coordinates[i+1]
        
        # Create a simple segment with start and end points
        # GeoJSON expects [lon, lat]
        segment = {
            "coordinates": [
                [start[1], start[0]], # Start [lon, lat]
                [end[1], end[0]]      # End [lon, lat]
            ],
            "distance": 0, # Could calculate haversine if needed
            "duration": 0,
            "steps": []
        }
        fallback_geometry.append(segment)
        
    return fallback_geometry


@router.post("/quick-route")
def generate_quick_route(
    request: QuickOptimizationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a quick route using real database POIs and route geometry
    """
    try:
        logger.info(f"Quick route generation started with params: {request.model_dump()}")
        
        # Get POI service
        poi_service = POIService(db)
        
        pois = []
        
        # Priority 1: Use selected POIs if provided
        if request.selected_poi_ids:
            logger.info(f"Using specific POIs: {request.selected_poi_ids}")
            all_pois = poi_service.get_all_pois()
            pois = [p for p in all_pois if p.id in request.selected_poi_ids]
            
            # Preserve order of selected_poi_ids if possible, or just use list order
            # For now, we'll trust the DB retrieval order or sort by popularity/proximity later
            # But user wants "connect them", so maybe TSP? For quick route, let's just keep them
            # or maybe sort by nearest neighbor greedy?
            # Let's stick to the retrieved list for now, maybe sort by ID or keep as is.
            
        else:
            # Priority 2: Filter from database based on preferences
            if request.preferred_districts:
                pois = poi_service.filter_pois(districts=request.preferred_districts, min_rating=3.0)
            else:
                pois = poi_service.get_all_pois()
            
            # Filter by categories
            if request.mandatory_categories:
                pois = [poi for poi in pois if poi.category in request.mandatory_categories]
            
            if request.avoid_categories:
                pois = [poi for poi in pois if poi.category not in request.avoid_categories]
            
            # Sort by popularity and select top POIs
            pois = sorted(pois, key=lambda x: x.popularity, reverse=True)[:5]
        
        logger.info(f"Selected {len(pois)} POIs for routing")
        
        if not pois:
            raise HTTPException(status_code=404, detail="No POIs found for routing")
        
        # Build route
        route = []
        timeline = []
        current_time_minutes = 540  # 09:00
        total_cost = 0.0
        
        # Get coordinates for route geometry
        coordinates = [(poi.latitude, poi.longitude) for poi in pois]
        
        # Get route geometry from OpenRouteService
        route_geometry = get_route_geometry(coordinates)
        
        for i, poi in enumerate(pois):
            route.append({
                "id": poi.id,
                "name": poi.name,
                "latitude": poi.latitude,
                "longitude": poi.longitude,
                "district": poi.district,
                "category": poi.category,
                "popularity": poi.popularity,
                "rating": poi.rating,
                "price_level": poi.price_level,
                "visit_duration": poi.visit_duration,
                "tags": poi.tags or [],
                "description": poi.description or f"Visita {poi.name} en {poi.district}"
            })
            
            # Calculate timeline
            arrival = current_time_minutes
            departure = current_time_minutes + poi.visit_duration
            travel_time = 15 if i > 0 else 0  # Assume 15 min travel between POIs
            
            timeline.append({
                "poi_id": poi.id,
                "poi_name": poi.name,
                "category": poi.category,
                "district": poi.district,
                "arrival_time": f"{arrival//60:02d}:{arrival%60:02d}",
                "departure_time": f"{departure//60:02d}:{departure%60:02d}",
                "visit_duration": poi.visit_duration,
                "travel_time": travel_time,
                "wait_time": 0,
                "price": float(poi.price_level * 10),
                "latitude": poi.latitude,
                "longitude": poi.longitude
            })
            
            current_time_minutes = departure + travel_time
            total_cost += poi.price_level * 10
        
        total_duration = current_time_minutes - 540
        
        response = {
            "route_id": f"route_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "route": route,
            "route_geometry": route_geometry,  # Add route geometry
            "timeline": timeline,
            "total_duration": total_duration,
            "total_cost": total_cost,
            "fitness_score": 100.0,
            "start_time": "09:00",
            "end_time": f"{current_time_minutes//60:02d}:{current_time_minutes%60:02d}",
            "num_pois": len(pois),
            "weather_summary": None
        }
        
        logger.info(f"Quick route generated successfully with {len(pois)} POIs")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in quick route: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend-pois")
def recommend_pois(
    request: QuickOptimizationRequest,
    db: Session = Depends(get_db)
):
    """
    Get recommended POIs based on preferences (Fast, no routing)
    """
    try:
        logger.info(f"Recommendation request: {request.model_dump()}")
        
        # Get POI service
        poi_service = POIService(db)
        
        pois = []
        
        # Logic 1: If start location is provided, find nearby POIs
        # Handle both lat/lng and latitude/longitude keys
        start_lat = None
        start_lon = None
        
        if request.start_location:
            if "lat" in request.start_location and "lng" in request.start_location:
                start_lat = request.start_location["lat"]
                start_lon = request.start_location["lng"]
            elif "latitude" in request.start_location and "longitude" in request.start_location:
                start_lat = request.start_location["latitude"]
                start_lon = request.start_location["longitude"]
        
        if start_lat is not None and start_lon is not None:
            logger.info(f"Using start location for recommendations: {start_lat}, {start_lon}")
            all_pois = poi_service.get_all_pois()
            
            # Calculate distance to each POI
            pois_with_dist = []
            for poi in all_pois:
                # Simple Euclidean approximation for sorting is enough here, or Haversine
                dist = ((poi.latitude - start_lat)**2 + (poi.longitude - start_lon)**2)**0.5
                pois_with_dist.append((poi, dist))
            
            # Sort by distance
            pois_with_dist.sort(key=lambda x: x[1])
            pois = [p[0] for p in pois_with_dist]
            
            # Apply other filters if present (categories)
            if request.mandatory_categories:
                pois = [p for p in pois if p.category in request.mandatory_categories]
                
            # Take top 10 closest
            pois = pois[:10]
            
        # Logic 2: If no start location, filter by district
        elif request.preferred_districts:
            logger.info(f"Filtering by districts: {request.preferred_districts}")
            pois = poi_service.filter_pois(districts=request.preferred_districts, min_rating=3.0)
            logger.info(f"Found {len(pois)} POIs in districts {request.preferred_districts}")
        
        # Logic 3: Fallback to all POIs (sorted by popularity)
        else:
            logger.info("No start location or districts, fetching all POIs")
            pois = poi_service.get_all_pois()
            
        if not pois:
            logger.warning(f"No POIs found. Districts: {request.preferred_districts}, StartLoc: {request.start_location}")
            # If specific district was requested but no POIs found, don't return Miraflores fallback!
            if request.preferred_districts:
                 return {"pois": [], "count": 0, "message": "No places found in this district"}
            
            raise HTTPException(status_code=404, detail="No POIs found")
        
        # Smart filtering by budget and time
        # Filter POIs that fit within budget
        if request.max_budget:
            affordable_pois = [poi for poi in pois if poi.price_level * 10 <= request.max_budget]
            if affordable_pois:
                pois = affordable_pois
                logger.info(f"Filtered to {len(pois)} affordable POIs (budget: {request.max_budget})")
        
        # Estimate how many POIs can fit in available time
        if request.max_duration:
            avg_visit_time = 60  # Average 60 minutes per POI
            avg_travel_time = 15 if request.transport_mode == "driving-car" else 20  # Travel between POIs
            time_per_poi = avg_visit_time + avg_travel_time
            max_pois = max(3, int(request.max_duration / time_per_poi))
            logger.info(f"Limiting to {max_pois} POIs based on available time ({request.max_duration} min)")
        else:
            max_pois = 10
            
        # Filter by categories (if not already done in Logic 1)
        if start_lat is None:
            if request.mandatory_categories:
                pois = [poi for poi in pois if poi.category in request.mandatory_categories]
            
            if request.avoid_categories:
                pois = [poi for poi in pois if poi.category not in request.avoid_categories]
                
            # Sort by popularity and apply limit
            pois = sorted(pois, key=lambda x: x.popularity, reverse=True)[:max_pois]
        
        return {
            "pois": [poi.to_dict() for poi in pois],
            "count": len(pois)
        }
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        # Only return fallback if it was a generic error, NOT if we just found 0 results
        return {
            "pois": [],
            "count": 0,
            "error": str(e)
        }
