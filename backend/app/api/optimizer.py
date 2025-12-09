from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime
import numpy as np
import logging

from app.database import get_db
from app.services.poi_service import POIService
from app.services.weather_service import WeatherService
from app.services.routes_service import RoutesService
from app.services.aco_optimizer import AntColonyOptimizer
from app.services.toptw_solver import POINode, TOPTWConstraints
from app.services.maps_service import LimaPlacesExtractor
from app.config import settings
from app.services.hours_utils import is_poi_available, calculate_urgency_weight
router = APIRouter()
logger = logging.getLogger(__name__)


def convert_price_level_to_cost(price_level: int) -> float:
    """
    Convert Google Places API priceLevel to estimated cost in Peruvian Soles.
    
    Google Places API (New) priceLevel values:
    - PRICE_LEVEL_FREE (0): Free entry/service
    - PRICE_LEVEL_INEXPENSIVE (1): Budget-friendly (< S/ 30)
    - PRICE_LEVEL_MODERATE (2): Mid-range (S/ 30-60)
    - PRICE_LEVEL_EXPENSIVE (3): High-end (S/ 60-100)
    - PRICE_LEVEL_VERY_EXPENSIVE (4): Premium (> S/ 100)
    
    These values represent typical costs for Lima, Peru.
    """
    price_mapping = {
        0: 0.0,    # FREE - museums, parks, public spaces
        1: 25.0,   # INEXPENSIVE - street food, small cafes, basic attractions
        2: 50.0,   # MODERATE - restaurants, mid-tier attractions
        3: 80.0,   # EXPENSIVE - fine dining, premium experiences
        4: 150.0,  # VERY_EXPENSIVE - luxury restaurants, exclusive venues
    }
    return price_mapping.get(price_level, 0.0)


# Request/Response models
class OptimizationRequest(BaseModel):
    max_duration: int = Field(..., description="Maximum trip duration in minutes", ge=60, le=720)
    max_budget: float = Field(..., description="Maximum budget", ge=0)
    start_time: str = Field(..., description="Start time in HH:MM format", pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    user_pace: str = Field("medium", description="User walking pace", pattern="^(slow|medium|fast)$")
    mandatory_categories: List[str] = Field(default=[], description="Categories that must be included")
    avoid_categories: List[str] = Field(default=[], description="Categories to avoid")
    preferred_districts: List[str] = Field(default=[], description="Preferred districts")
    start_location: Optional[Dict[str, float]] = Field(None, description="Starting location {lat, lon}")
    selected_poi_ids: Optional[List[int]] = Field(None, description="Pre-selected POI IDs to optimize")
    transport_mode: str = Field("driving-car", description="Transport mode", pattern="^(driving-car|foot-walking)$")
    day_of_week: str = Field("Monday", description="Day of week", pattern="^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)$")

class TimelineItem(BaseModel):
    poi_id: int
    poi_name: str
    category: str
    district: str
    arrival_time: str
    departure_time: str
    visit_duration: int
    travel_time: int
    wait_time: int
    price: float
    latitude: float
    longitude: float
    weather: Optional[Dict] = None
    # Contact information for POI detail modal
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    rating: Optional[float] = None
    opening_hours: Optional[Dict] = None
    popularity: Optional[int] = None


class OptimizationResponse(BaseModel):
    route_id: str
    route: List[Dict]
    timeline: List[TimelineItem]
    total_duration: int
    total_cost: float
    fitness_score: float
    start_time: str
    end_time: str
    num_pois: int
    weather_summary: Optional[Dict] = None
    route_geometry: Optional[List[Dict]] = None


class FeedbackRequest(BaseModel):
    route_id: str
    poi_id: int
    rating: Optional[float] = Field(None, ge=1, le=5)
    visited: int = Field(..., ge=0, le=1)
    too_crowded: int = Field(0, ge=0, le=1)
    comments: Optional[str] = None


@router.post("/generate-route", response_model=OptimizationResponse)
async def generate_route(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate optimized tourist route using Genetic Algorithm
    
    This is the main endpoint that:
    1. Fetches POIs from database
    2. Gets weather forecast
    3. Calculates distance matrix
    4. Runs genetic algorithm
    5. Returns optimized route with timeline
    """
    try:
        logger.info(f"Generating route with params: {request.model_dump()}")
        
        # Initialize services
        poi_service = POIService(db)
        weather_service = WeatherService()
        routes_service = RoutesService(api_key=settings.openrouteservice_api_key)
        
        # --- AUTO-FETCH LOGIC ---
        # If start_location is provided, check if we have POIs nearby. 
        # If not, fetch from Google before proceeding.
        if request.start_location:
            lat = request.start_location["latitude"]
            lon = request.start_location["longitude"]
            
            # Check DB count within ~2km (approx 0.018 degrees)
            nearby_count = poi_service.count_pois_near(lat, lon, radius_km=2.0)
            logger.info(f"POIs found near start location ({lat}, {lon}): {nearby_count}")
            
            if nearby_count < 5:
                logger.info("Low POI count detected. Triggering Auto-Fetch from Google...")
                extractor = LimaPlacesExtractor()
                # Run synchronously to ensure data is available for this request
                extractor.fetch_pois_by_coordinates(lat, lon, radius=2500)
                logger.info("Auto-Fetch complete.")
        # ------------------------
        
        # Get POIs based on preferences
        # If user has pre-selected specific POIs (from recommendations), use only those
        if request.selected_poi_ids:
            logger.info(f"Using pre-selected POI IDs: {request.selected_poi_ids}")
            pois = [poi_service.get_poi_by_id(poi_id) for poi_id in request.selected_poi_ids]
            pois = [poi for poi in pois if poi is not None]  # Filter out None values
        else:
            # Otherwise, filter by districts and get top POIs
            # 1. Get filtered POIs by district/preferences
            pois = poi_service.filter_pois(
                districts=request.preferred_districts if request.preferred_districts else None,
                categories=None,  # Don't filter categories here, let GA handle it
                min_rating=3.0  # Only consider reasonably rated POIs
            )
            
            # 2. ESSENTIAL: Explicitly add POIs near the start location (in case district filter missed them)
            # This fixes the issue where "Unknown District" POIs or border POIs were excluded
            if request.start_location:
                 nearby_db_pois = poi_service.get_all_pois() # We could optimize this query
                 # Filter manually for distance
                 lat_start = request.start_location["latitude"]
                 lon_start = request.start_location["longitude"]
                 
                 # Add any valid POI within 3km of start
                 nearby_matches = []
                 for p in nearby_db_pois:
                     dist = ((p.latitude - lat_start)**2 + (p.longitude - lon_start)**2)**0.5
                     # Approx 0.027 degrees is ~3km
                     if dist < 0.027 and p.is_active:
                         nearby_matches.append(p)
                 
                 # Merge without duplicates
                 existing_ids = {p.id for p in pois}
                 for np in nearby_matches:
                     if np.id not in existing_ids:
                         pois.append(np)
                         logger.info(f"Added nearby POI to optimization candidates: {np.name}")

            if not pois:
                raise HTTPException(status_code=404, detail="No POIs found matching criteria")
            
            # OPTIMIZATION: Limit to top 15 most popular POIs to speed up calculation
            # Sort by popularity and take top 15
            pois = sorted(pois, key=lambda x: x.popularity, reverse=True)[:20]
        
        logger.info(f"Found {len(pois)} POIs before availability filter")
        
        # NUEVO: Filtrar POIs que NO estarán disponibles según opening_hours
        start_time_minutes = _time_str_to_minutes(request.start_time)
        available_pois = []
        for poi in pois:
            if is_poi_available(
                poi.opening_hours,
                request.day_of_week,
                start_time_minutes,
                poi.visit_duration
            ):
                available_pois.append(poi)
            else:
                logger.info(f"Filtered out POI '{poi.name}' - closed on {request.day_of_week} at {request.start_time}")
        
        pois = available_pois
        
        if not pois:
            raise HTTPException(
                status_code=404,
                detail=f"No hay lugares disponibles para {request.day_of_week} a las {request.start_time}"
            )
        
        logger.info(f"Found {len(pois)} POIs for optimization after availability filter")
        
        # Convert to POINode objects
        poi_nodes = []
        for poi in pois:
            # Parse opening hours (simplified - assume same hours every day)
            opening_time = 540  # 09:00 default
            closing_time = 1080  # 18:00 default
            
            if poi.opening_hours and isinstance(poi.opening_hours, dict):
                # Try to parse first available day
                for day, hours in poi.opening_hours.items():
                    if hours and "-" in hours:
                        try:
                            open_str, close_str = hours.split("-")
                            opening_time = _time_str_to_minutes(open_str.strip())
                            closing_time = _time_str_to_minutes(close_str.strip())
                            break
                        except:
                            pass
            
            poi_node = POINode(
                id=poi.id,
                name=poi.name,
                latitude=poi.latitude,
                longitude=poi.longitude,
                popularity=poi.popularity,
                opening_time=opening_time,
                closing_time=closing_time,
                visit_duration=poi.visit_duration,
                category=poi.category,
                price=convert_price_level_to_cost(poi.price_level or 0),  # Realistic price based on Google API levels
                rating=poi.rating,
                tags=poi.tags or [],
                district=poi.district,
                learned_weight=poi.learned_popularity,
                opening_hours=poi.opening_hours,
                phone=poi.phone
            )
            poi_nodes.append(poi_node)
        
        # Get weather forecast (use Lima center coordinates as reference)
        lima_center = (-12.0464, -77.0428)
        weather_data = weather_service.get_current_weather(lima_center[0], lima_center[1])
        
        # Create constraints
        start_time_minutes = _time_str_to_minutes(request.start_time)
        
        constraints = TOPTWConstraints(
            max_duration=request.max_duration,
            max_budget=request.max_budget,
            start_time=start_time_minutes,
            user_pace=request.user_pace,
            mandatory_categories=request.mandatory_categories,
            avoid_categories=request.avoid_categories,
            preferred_districts=request.preferred_districts,
            weather_conditions=weather_data or {},
            transport_mode=request.transport_mode,
            day_of_week=request.day_of_week  # FIXED: Pass day_of_week for opening hours logic
        )
        
        # Extract start location for ACO
        start_loc_tuple = None
        if request.start_location:
            start_loc_tuple = (
                request.start_location.get('latitude'),
                request.start_location.get('longitude')
            )
        
        # Calculate distance matrix - INCLUDE START LOCATION for accurate first POI travel time
        if settings.openrouteservice_api_key:
            logger.info(f"ORS API Key present: {settings.openrouteservice_api_key[:5]}... (first 5 chars)")
        else:
            logger.warning("ORS API Key MISSING in settings")

        logger.info(f"Calculating distance matrix for {len(poi_nodes)} POIs using {request.transport_mode}...")
        
        # Build coordinates list: start location (if provided) + all POIs
        if start_loc_tuple:
            logger.info(f"Start location provided: {start_loc_tuple}")
            all_coordinates = [start_loc_tuple] + [(poi.latitude, poi.longitude) for poi in poi_nodes]
            time_matrix_with_start = routes_service.get_distance_matrix(all_coordinates, profile=request.transport_mode)
            
            # Extract time from start to each POI (row 0, columns 1 to N)
            if time_matrix_with_start.shape[1] > 1:
                start_to_poi_times = time_matrix_with_start[0, 1:].tolist()
                
                # Extract POI-to-POI matrix (rows 1 to N, columns 1 to N)
                time_matrix = time_matrix_with_start[1:, 1:]
                
                logger.info(f"Calculated distance matrix with start location: {time_matrix_with_start.shape}")
                logger.info(f"Start to first 3 POIs times (min): {start_to_poi_times[:3]}")
                if len(start_to_poi_times) > 0:
                     logger.info(f"Time to nearest POI: {min(start_to_poi_times):.2f} min. Time to farthest: {max(start_to_poi_times):.2f} min")
            else:
                logger.warning("Matrix shape mismatch after adding start location")
                start_to_poi_times = None
                time_matrix = None
        else:
            # No start location, just POI-to-POI matrix
            logger.info("No start location provided")
            coordinates = [(poi.latitude, poi.longitude) for poi in poi_nodes]
            time_matrix = routes_service.get_distance_matrix(coordinates, profile=request.transport_mode)
            start_to_poi_times = None
            logger.info(f"Calculated distance matrix (no start location): {time_matrix.shape}")
        
        # PRIMARY: Ant Colony Optimization (faster and better for routing)
        aco = AntColonyOptimizer(
            pois=poi_nodes,
            constraints=constraints,
            num_ants=40,
            iterations=80,
            alpha=1.0,
            beta=2.5,
            start_location=start_loc_tuple
        )
        
        aco.set_distance_matrix(time_matrix)
        
        # Pass start-to-POI times for accurate first POI travel time calculation
        if start_to_poi_times:
            aco.set_start_to_poi_times(start_to_poi_times)
        
        logger.info("Starting Ant Colony Optimization (primary)...")
        best_route, best_fitness = aco.solve(verbose=True)
        
        # Store solver reference for later use
        solver = aco.solver
        
        # Fallback to GA if ACO fails
        if not best_route:
            logger.warning("ACO failed to find route, falling back to GA")
            ga = GeneticAlgorithm(
                pois=poi_nodes,
                constraints=constraints,
                population_size=30,
                generations=40,
                start_location=start_loc_tuple
            )
            ga.set_distance_matrix(time_matrix)
            if start_to_poi_times:
                ga.set_start_to_poi_times(start_to_poi_times)
            best_route, best_fitness = ga.evolve()
            solver = ga.solver
        
        if not best_route:
            logger.error(f"Both ACO and GA failed to generate a route. POI count: {len(poi_nodes)}, Duration limit: {constraints.max_duration} min")
            raise HTTPException(status_code=500, detail=f"Could not generate route with {len(poi_nodes)} POIs. Try adding more locations or adjusting time.")
        
        logger.info(f"Optimization complete. Best fitness: {best_fitness:.2f}")
        
        # Extract start location coordinates if provided
        start_loc_coords = None
        if request.start_location:
            start_loc_coords = (
                request.start_location.get('latitude'),
                request.start_location.get('longitude')
            )
        
        # Get route details with start location and accurate travel times
        route_details = solver.get_route_details(best_route, start_location=start_loc_coords)
        
        # Generate route ID
        route_id = f"route_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        
        # Build response
        route_pois = [poi_nodes[idx].id for idx in best_route]
        route_poi_objects = [poi_service.get_poi_by_id(poi_id) for poi_id in route_pois]
        
        # Enrich timeline with weather and contact information
        timeline_items = []
        for i, item in enumerate(route_details["timeline"]):
            # Get the corresponding POI object for contact info
            poi_id = item["poi_id"]
            poi_obj = next((p for p in route_poi_objects if p and p.id == poi_id), None)
            
            # Create timeline item with contact fields
            timeline_data = {
                **item,
                "phone": poi_obj.phone if poi_obj else None,
                "website": poi_obj.website if poi_obj else None,
                "address": poi_obj.address if poi_obj else None,
                "description": poi_obj.description if poi_obj else None,
                "rating": poi_obj.rating if poi_obj else item.get("rating"),
                "opening_hours": poi_obj.opening_hours if poi_obj else None,
                "popularity": poi_obj.popularity if poi_obj else None
            }
            
            timeline_item = TimelineItem(**timeline_data)
            
            # Add weather forecast for this time
            arrival_time = _time_str_to_minutes(item["arrival_time"])
            # Simplified: use current weather for all times
            timeline_item.weather = weather_data
            
            timeline_items.append(timeline_item)
        
        # CRITICAL FIX: Build route array from timeline_items to ensure perfect sync
        # This ensures Map (uses route) and Timeline (uses timeline) show the same POIs
        # Previously, route used full best_route while timeline filtered out excessive-wait POIs
        route_from_timeline = []
        for item in timeline_items:
            poi_obj = next((p for p in route_poi_objects if p and p.id == item.poi_id), None)
            if poi_obj:
                route_from_timeline.append(poi_obj.to_dict())

        # Get route geometry (streets and avenues) - USING SYNCED ROUTE
        route_geometry = []
        if len(route_from_timeline) > 1:
            try:
                # Extract coordinates from synced POIs (matches timeline)
                route_coords = [(poi["latitude"], poi["longitude"]) for poi in route_from_timeline]
                
                # Get detailed geometry from OpenRouteService
                from app.api.quick_optimizer import get_route_geometry
                route_geometry = get_route_geometry(route_coords)
                
            except Exception as e:
                logger.error(f"Error calculating route geometry: {e}")
                route_geometry = []

        response = OptimizationResponse(
            route_id=route_id,
            route=route_from_timeline,  # Now synced with timeline
            timeline=timeline_items,
            total_duration=int(round(route_details["total_duration"])),
            total_cost=route_details["total_cost"],
            fitness_score=best_fitness,
            start_time=route_details["start_time"],
            end_time=route_details["end_time"],
            num_pois=len(route_from_timeline),  # Use synced count
            weather_summary=weather_data,
            route_geometry=route_geometry  # Now using synced coordinates
        )
        
        return response

        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        logger.error(f"Error generating route: {e}\n{tb_str}")
        raise HTTPException(status_code=500, detail=f"Failed to generate route: {str(e)}")


@router.post("/reoptimize")
async def reoptimize_route(
    route_id: str,
    current_poi_index: int,
    remaining_time: int,
    db: Session = Depends(get_db)
):
    """
    Re-optimize route from current position
    
    Useful when user wants to adjust route mid-trip
    """
    # This would be similar to generate_route but starting from current position
    # For now, return a simple response
    return {
        "message": "Re-optimization not yet implemented",
        "route_id": route_id
    }


@router.post("/feedback")
async def submit_feedback(
    feedback: FeedbackRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Submit user feedback for a POI in a route
    
    This feedback is used to improve future recommendations
    """
    try:
        # Get weather service
        weather_service = WeatherService()
        
        # Get current weather
        lima_center = (-12.0464, -77.0428)
        weather_data = weather_service.get_current_weather(lima_center[0], lima_center[1])
        
        # Create feedback record
        feedback_record = Feedback(
            route_id=feedback.route_id,
            poi_id=feedback.poi_id,
            rating=feedback.rating,
            visited=feedback.visited,
            too_crowded=feedback.too_crowded,
            weather_condition=weather_service.get_weather_description(
                weather_data.get("weather_code", 0) if weather_data else 0
            ),
            temperature=weather_data.get("temperature") if weather_data else None,
            comments=feedback.comments,
            timestamp=datetime.utcnow()
        )
        
        db.add(feedback_record)
        db.commit()
        
        # Update learned weights in background
        background_tasks.add_task(update_learned_weights, db)
        
        return {"message": "Feedback submitted successfully", "feedback_id": feedback_record.id}
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail="Error submitting feedback")


def update_learned_weights(db: Session):
    """Background task to update POI learned weights"""
    try:
        poi_service = POIService(db)
        poi_service.update_learned_weights()
        logger.info("Updated learned weights from feedback")
    except Exception as e:
        logger.error(f"Error updating learned weights: {e}")


def _time_str_to_minutes(time_str: str) -> int:
    """Convert HH:MM to minutes from midnight"""
    try:
        hours, minutes = map(int, time_str.split(":"))
        return hours * 60 + minutes
    except:
        return 540  # Default to 09:00
