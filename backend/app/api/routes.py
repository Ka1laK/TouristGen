from fastapi import APIRouter, Query, HTTPException
from typing import List, Tuple
from pydantic import BaseModel
from app.services.routes_service import RoutesService
from app.config import settings

router = APIRouter()
routes_service = RoutesService(api_key=settings.openrouteservice_api_key)


class CoordinatePair(BaseModel):
    latitude: float
    longitude: float


class RouteRequest(BaseModel):
    start: CoordinatePair
    end: CoordinatePair
    profile: str = "foot-walking"


class MatrixRequest(BaseModel):
    coordinates: List[CoordinatePair]
    profile: str = "foot-walking"


@router.post("/calculate")
def calculate_route(request: RouteRequest):
    """Calculate route between two points"""
    try:
        start = (request.start.latitude, request.start.longitude)
        end = (request.end.latitude, request.end.longitude)
        
        route = routes_service.get_route(start, end, request.profile)
        
        if not route:
            raise HTTPException(status_code=404, detail="Route not found")
        
        return route
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating route: {str(e)}")


@router.post("/matrix")
def calculate_matrix(request: MatrixRequest):
    """Calculate distance/time matrix for multiple points"""
    try:
        coordinates = [
            (coord.latitude, coord.longitude) 
            for coord in request.coordinates
        ]
        
        matrix = routes_service.get_distance_matrix(coordinates, request.profile)
        
        return {
            "matrix": matrix.tolist(),
            "unit": "minutes",
            "profile": request.profile,
            "size": len(coordinates)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating matrix: {str(e)}")


@router.get("/isochrone")
def get_isochrone(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
    time_minutes: int = Query(..., description="Time limit in minutes", ge=5, le=120),
    profile: str = Query("foot-walking", description="Travel profile")
):
    """Get isochrone (reachable area within time limit)"""
    try:
        location = (latitude, longitude)
        isochrone = routes_service.get_isochrone(location, time_minutes, profile)
        
        if not isochrone:
            return {
                "message": "Isochrone calculation requires OpenRouteService API key",
                "available": False
            }
        
        return isochrone
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating isochrone: {str(e)}")
