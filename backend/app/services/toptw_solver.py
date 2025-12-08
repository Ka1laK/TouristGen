from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from datetime import datetime, timedelta
import logging
from app.services.hours_utils import calculate_urgency_weight
logger = logging.getLogger(__name__)


@dataclass
class POINode:
    """Represents a Point of Interest for optimization"""
    id: int
    name: str
    latitude: float
    longitude: float
    popularity: int  # 1-100
    opening_time: int  # minutes from midnight
    closing_time: int  # minutes from midnight
    visit_duration: int  # minutes
    category: str
    price: float
    rating: float
    tags: List[str]
    district: str
    learned_weight: float = 1.0
    opening_hours: Dict[str, str]=None
    phone: str=None


@dataclass
class TOPTWConstraints:
    """Constraints for the TOPTW problem"""
    max_duration: int  # Total time available (minutes)
    max_budget: float  # Maximum budget
    start_time: int  # Start time in minutes from midnight
    user_pace: str  # "slow", "medium", "fast"
    mandatory_categories: List[str]  # Must visit at least one
    avoid_categories: List[str]  # Avoid these
    preferred_districts: List[str]  # Prefer these districts
    weather_conditions: Dict[str, any]  # Current weather data
    transport_mode: str = "driving-car"  # Transport mode for travel time calculations
    day_of_week: str = "Monday" # NUEVO - Día del tour

class TOPTWSolver:
    """
    Team Orienteering Problem with Time Windows Solver
    
    Objective: Maximize total score while respecting:
    - Time windows (opening/closing hours)
    - Total duration constraint
    - Budget constraint
    - Weather conditions
    - User preferences
    """
    
    # Maximum wait time allowed (in minutes) before a POI opens
    MAX_WAIT_TIME = 30
    
    def __init__(self, pois: List[POINode], constraints: TOPTWConstraints):
        self.pois = pois
        self.constraints = constraints
        self.distance_matrix = None  # Will be set externally
        self.time_matrix = None  # Travel time matrix (minutes)
        self.start_to_poi_times = None  # Travel times from start location to each POI (from ORS API)
        
        # Import centralized weights
        from app.services.optimization_weights import WEIGHTS
        self.weights = WEIGHTS
        
        # Legacy aliases for backward compatibility
        self.alpha = WEIGHTS.travel_time_penalty
        self.beta = WEIGHTS.cost_penalty
        self.gamma = WEIGHTS.constraint_violation
        
    def set_distance_matrix(self, time_matrix: np.ndarray):
        """Set the travel time matrix between POIs (in minutes)"""
        self.time_matrix = time_matrix
    
    def set_start_to_poi_times(self, times: List[float]):
        """Set travel times from start location to each POI (from OpenRouteService API)"""
        self.start_to_poi_times = times

        
    def calculate_fitness(self, route: List[int]) -> float:
        """
        Calculate fitness score for a route
        
        Fitness = Σ(Popularity × WeatherWeight × UserWeight × LearnedWeight) 
                  - (α × TravelTime) - (β × Cost) - Penalties
        """
        if not route or len(route) == 0:
            return 0.0
            
        total_score = 0.0
        total_time = 0
        total_cost = 0.0
        current_time = self.constraints.start_time
        penalties = 0.0
        
        # Track visited categories for mandatory requirements
        visited_categories = set()
        
        for i, poi_idx in enumerate(route):
            poi = self.pois[poi_idx]
            if poi_idx >= len(self.pois):
                penalties += 1000  # Invalid POI index
                continue
                
            visited_categories.add(poi.category)
            
            # Travel time to this POI
            if i > 0:
                prev_idx = route[i-1]
                if self.time_matrix is not None and prev_idx < len(self.time_matrix):
                    travel_time = self.time_matrix[prev_idx][poi_idx]
                else:
                    # Fallback: estimate based on distance
                    travel_time = self._estimate_travel_time(
                        self.pois[prev_idx], poi
                    )
                
                total_time += travel_time
                current_time += travel_time
            
            # Check if POI is in avoided categories
            if poi.category in self.constraints.avoid_categories:
                penalties += 50
                continue
            
            # Time window constraints
            if current_time < poi.opening_time:
                # Arrived too early - must wait
                wait_time = poi.opening_time - current_time
                
                # Skip POIs that require excessive waiting
                if wait_time > self.MAX_WAIT_TIME:
                    penalties += 500  # Heavy penalty for excessive wait
                    continue  # Skip this POI - not worth waiting
                
                penalties += wait_time * 2.0  # Stronger waiting penalty
                current_time = poi.opening_time
                total_time += wait_time
            
            if current_time >= poi.closing_time:
                # Arrived too late - cannot visit
                penalties += 200  # Heavy penalty for missing POI
                continue
            
            if current_time + poi.visit_duration > poi.closing_time:
                # Not enough time to visit before closing
                penalties += 150
                continue
            
            # Visit the POI
            total_time += poi.visit_duration
            current_time += poi.visit_duration
            total_cost += poi.price
            
            # Calculate weighted score
            weather_weight = self._calculate_weather_weight(poi)
            user_weight = self._calculate_user_preference_weight(poi)
            
            # NUEVO: Calcular peso de urgencia basado en cierre próximo
            urgency_weight = calculate_urgency_weight(
                poi.opening_hours if hasattr(poi, 'opening_hours') else {},
                self.constraints.day_of_week,
                current_time,
                poi.visit_duration
            )
            
            # Si urgency_weight es 0, el POI ya no es visitable
            if urgency_weight == 0:
                penalties += 300  # Penalización fuerte
                continue
            
            poi_score = (
                poi.popularity * 
                weather_weight * 
                user_weight * 
                poi.learned_weight *
                urgency_weight *  # NUEVO: peso de urgencia
                (poi.rating / 5.0)  # Normalize rating to 0-1
            )
            
            total_score += poi_score
        
        # Check mandatory categories
        for category in self.constraints.mandatory_categories:
            if category not in visited_categories:
                penalties += 100  # Penalty for missing mandatory category
        
        # Duration constraint
        if total_time > self.constraints.max_duration:
            overtime = total_time - self.constraints.max_duration
            penalties += overtime * self.gamma
        
        # Budget constraint
        if total_cost > self.constraints.max_budget:
            over_budget = total_cost - self.constraints.max_budget
            penalties += over_budget * self.beta * 10
        
        # Pace adjustment
        pace_multiplier = self._get_pace_multiplier()
        adjusted_time = total_time * pace_multiplier
        
        if adjusted_time > self.constraints.max_duration:
            penalties += (adjusted_time - self.constraints.max_duration) * self.gamma
        
        # Final fitness calculation
        fitness = total_score - (self.alpha * total_time) - (self.beta * total_cost) - penalties
        
        return max(0.0, fitness)
    
    def _calculate_weather_weight(self, poi: POINode) -> float:
        """Calculate weight adjustment based on weather conditions"""
        weight = 1.0
        weather = self.constraints.weather_conditions
        
        if not weather:
            return weight
        
        # Rain penalty for outdoor activities
        if weather.get("precipitation", 0) > 2:  # mm/hour
            if any(tag in poi.tags for tag in ["outdoor", "park", "beach"]):
                weight *= 0.5  # Reduce score for outdoor POIs in rain
            elif any(tag in poi.tags for tag in ["museum", "indoor", "cultural"]):
                weight *= 1.3  # Boost indoor POIs in rain
        
        # Temperature considerations
        temp = weather.get("temperature", 20)
        if temp > 30:  # Hot weather
            if "outdoor" in poi.tags:
                weight *= 0.7
            elif "indoor" in poi.tags:
                weight *= 1.2
        elif temp < 15:  # Cool weather
            if "beach" in poi.tags:
                weight *= 0.6
        
        # Wind considerations
        if weather.get("wind_speed", 0) > 30:  # km/h
            if "beach" in poi.tags or "outdoor" in poi.tags:
                weight *= 0.8
        
        return weight
    
    def _calculate_user_preference_weight(self, poi: POINode) -> float:
        """Calculate weight based on user preferences"""
        weight = 1.0
        
        # Category preferences
        if poi.category in self.constraints.mandatory_categories:
            weight *= 1.5
        
        if poi.category in self.constraints.avoid_categories:
            weight *= 0.2
        
        # District preferences
        if self.constraints.preferred_districts:
            if poi.district in self.constraints.preferred_districts:
                weight *= 1.3
            else:
                weight *= 0.8
        
        return weight
    
    def _get_pace_multiplier(self) -> float:
        """Get time multiplier based on user pace"""
        pace_multipliers = {
            "slow": 1.3,
            "medium": 1.0,
            "fast": 0.8
        }
        return pace_multipliers.get(self.constraints.user_pace, 1.0)
    
    def _estimate_travel_time(self, poi1: POINode, poi2: POINode) -> float:
        """Estimate travel time between two POIs using haversine distance"""
        # Haversine formula for distance
        lat1, lon1 = np.radians(poi1.latitude), np.radians(poi1.longitude)
        lat2, lon2 = np.radians(poi2.latitude), np.radians(poi2.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        
        # Earth radius in km
        distance_km = 6371 * c
        
        # Use transport mode from constraints for speed
        speeds = {
            "foot-walking": 4.5,      # km/h
            "cycling-regular": 15.0,
            "driving-car": 25.0       # Lima city traffic average
        }
        speed = speeds.get(self.constraints.transport_mode, 25.0)
        
        time_hours = distance_km / speed
        time_minutes = time_hours * 60
        
        return time_minutes
    
    def validate_route(self, route: List[int]) -> Tuple[bool, List[str]]:
        """Validate if a route is feasible"""
        errors = []
        
        if not route:
            errors.append("Route is empty")
            return False, errors
        
        current_time = self.constraints.start_time
        total_time = 0
        total_cost = 0.0
        
        for i, poi_idx in enumerate(route):
            if poi_idx >= len(self.pois):
                errors.append(f"Invalid POI index: {poi_idx}")
                continue
            
            poi = self.pois[poi_idx]
            
            # Add travel time
            if i > 0:
                prev_idx = route[i-1]
                if self.time_matrix is not None:
                    travel_time = self.time_matrix[prev_idx][poi_idx]
                else:
                    travel_time = self._estimate_travel_time(self.pois[prev_idx], poi)
                
                current_time += travel_time
                total_time += travel_time
            
            # Check time window
            if current_time >= poi.closing_time:
                errors.append(f"POI {poi.name} closes before arrival")
            
            # Visit
            current_time += poi.visit_duration
            total_time += poi.visit_duration
            total_cost += poi.price
        
        # Check constraints
        if total_time > self.constraints.max_duration:
            errors.append(f"Total time ({total_time} min) exceeds limit ({self.constraints.max_duration} min)")
        
        if total_cost > self.constraints.max_budget:
            errors.append(f"Total cost (${total_cost}) exceeds budget (${self.constraints.max_budget})")
        
        return len(errors) == 0, errors
    
    def get_route_details(self, route: List[int], start_location: tuple = None) -> Dict:
        """Get detailed information about a route
        
        Args:
            route: List of POI indices
            start_location: Optional (latitude, longitude) tuple for start point
        """
        if not route:
            return {}
        
        # Smart visit duration distribution
        total_pois = len(route)
        available_time = self.constraints.max_duration
        
        # Calculate total travel time first (including from start if provided)
        total_travel_time = 0
        
        # Add travel time from start location to first POI
        if start_location:
            first_poi = self.pois[route[0]]
            from geopy.distance import geodesic
            dist_km = geodesic(start_location, (first_poi.latitude, first_poi.longitude)).kilometers
            speeds = {
                "foot-walking": 4.5,
                "cycling-regular": 15.0,
                "driving-car": 25.0
            }
            speed = speeds.get(self.constraints.transport_mode, 25.0)
            total_travel_time += (dist_km / speed) * 60  # Convert to minutes
        
        for i in range(len(route)):
            if i > 0:
                prev_idx = route[i-1]
                poi_idx = route[i]
                if self.time_matrix is not None:
                    total_travel_time += self.time_matrix[prev_idx][poi_idx]
                else:
                    total_travel_time += self._estimate_travel_time(self.pois[prev_idx], self.pois[poi_idx])
        
        # Time available for visits (excluding travel)
        visit_time_budget = available_time - total_travel_time
        
        # Distribute visit time intelligently based on POI importance
        visit_durations = {}
        total_importance = sum(poi.popularity for poi in [self.pois[idx] for idx in route])
        
        for poi_idx in route:
            poi = self.pois[poi_idx]
            # Allocate time proportional to popularity, with min/max bounds
            if total_importance > 0:
                allocated_time = (poi.popularity / total_importance) * visit_time_budget
                # Bounds: minimum 30 min, maximum 180 min (3 hours)
                visit_durations[poi_idx] = max(30, min(180, int(allocated_time)))
            else:
                visit_durations[poi_idx] = poi.visit_duration
        
        timeline = []
        current_time = self.constraints.start_time
        total_cost = 0.0
        total_distance = 0.0
        
        for i, poi_idx in enumerate(route):
            poi = self.pois[poi_idx]
            
            # Travel time
            travel_time = 0
            if i == 0 and start_location:
                # Use ORS API travel time if available (set via set_start_to_poi_times)
                if self.start_to_poi_times is not None and poi_idx < len(self.start_to_poi_times):
                    travel_time = self.start_to_poi_times[poi_idx]
                    logger.info(f"Using ORS travel time to first POI '{poi.name}': {travel_time:.1f} min")
                else:
                    # Fallback: Calculate travel from start location to first POI using geodesic
                    from geopy.distance import geodesic
                    dist_km = geodesic(start_location, (poi.latitude, poi.longitude)).kilometers
                    speeds = {
                        "foot-walking": 4.5,
                        "cycling-regular": 15.0,
                        "driving-car": 25.0
                    }
                    speed = speeds.get(self.constraints.transport_mode, 25.0)
                    travel_time = (dist_km / speed) * 60  # Convert to minutes
                    logger.warning(f"Using fallback geodesic travel time to first POI: {travel_time:.1f} min")
                current_time += travel_time
            elif i > 0:
                prev_idx = route[i-1]
                if self.time_matrix is not None:
                    travel_time = self.time_matrix[prev_idx][poi_idx]
                else:
                    travel_time = self._estimate_travel_time(self.pois[prev_idx], poi)
                
                current_time += travel_time
            
            # Adjust for opening time
            arrival_time = current_time
            wait_time = 0
            if current_time < poi.opening_time:
                wait_time = poi.opening_time - current_time
                
                # Skip POIs that require excessive waiting
                if wait_time > self.MAX_WAIT_TIME:
                    continue  # Don't include in timeline
                
                current_time = poi.opening_time
            
            # Use smart visit duration
            smart_visit_duration = visit_durations.get(poi_idx, poi.visit_duration)
            departure_time = current_time + smart_visit_duration
            
            # Determine if location is free (price_level 0 or price 0)
            is_free = (poi.price == 0 or poi.price == 0.0 or 
                      (hasattr(poi, 'price_level') and poi.price_level == 0))
            
            timeline.append({
                "poi_id": poi.id,
                "poi_name": poi.name,
                "category": poi.category,
                "district": poi.district,
                "rating": poi.rating,  # Add rating for star display
                "arrival_time": self._minutes_to_time_string(arrival_time),
                "departure_time": self._minutes_to_time_string(departure_time),
                "visit_duration": smart_visit_duration,
                "travel_time": int(travel_time),
                "wait_time": int(wait_time) if wait_time > 0 else 0,
                "wait_warning": wait_time > 15,  # Flag if wait > 15 min
                "price": poi.price,
                "latitude": poi.latitude,
                "longitude": poi.longitude,
                "transport_mode": self.constraints.transport_mode,
                "is_free": is_free
            })
            
            current_time = departure_time
            total_cost += poi.price
        
        return {
            "timeline": timeline,
            "total_duration": current_time - self.constraints.start_time,
            "total_cost": total_cost,
            "num_pois": len(route),
            "start_time": self._minutes_to_time_string(self.constraints.start_time),
            "end_time": self._minutes_to_time_string(current_time)
        }
    
    def _minutes_to_time_string(self, minutes: int) -> str:
        """Convert minutes from midnight to HH:MM format"""
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        return f"{hours:02d}:{mins:02d}"
