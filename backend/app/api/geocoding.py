"""
Geocoding API endpoints - Using Google Geocoding API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict
import requests
import logging

from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Google Geocoding API endpoint
GOOGLE_GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"


async def geocode_location(query: str, limit: int = 3) -> List[Dict]:
    """
    Geocode a location string to coordinates using Google Geocoding API.
    
    This is a helper function that can be called from other modules.
    Unlike the endpoint, this doesn't raise HTTPException on errors.
    
    Args:
        query: Location text to geocode
        limit: Maximum results to return
        
    Returns:
        List of dicts with lat, lon, display_name keys
    """
    try:
        api_key = settings.google_maps_api_key
        if not api_key:
            logger.error("Google Maps API key not configured")
            return []
        
        # Add Lima, Peru context to improve results
        search_query = f"{query}, Lima, Peru"
        
        response = requests.get(
            GOOGLE_GEOCODING_URL,
            params={
                "address": search_query,
                "key": api_key,
                "language": "es",
                "region": "pe"  # Bias results to Peru
            },
            timeout=10
        )
        
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "OK":
            logger.warning(f"Google Geocoding API status: {data.get('status')}")
            return []
        
        results = []
        for item in data.get("results", [])[:limit]:
            location = item.get("geometry", {}).get("location", {})
            
            # Extract address components
            address_components = {}
            for component in item.get("address_components", []):
                for comp_type in component.get("types", []):
                    address_components[comp_type] = component.get("long_name", "")
            
            results.append({
                "display_name": item.get("formatted_address", ""),
                "lat": float(location.get("lat", 0)),
                "lon": float(location.get("lng", 0)),
                "address": address_components,
                "place_id": item.get("place_id", "")
            })
        
        logger.info(f"Google Geocoded '{query}' -> {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"Google Geocoding error for '{query}': {e}")
        return []


@router.get("/search")
def search_location(
    q: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=10, description="Maximum number of results")
) -> List[Dict]:
    """
    Search for locations using Google Geocoding API
    
    Returns geocoded locations with coordinates and address details.
    """
    try:
        api_key = settings.google_maps_api_key
        if not api_key:
            logger.error("Google Maps API key not configured")
            raise HTTPException(status_code=500, detail="Geocoding service not configured")
        
        # Add Lima, Peru context to improve results
        search_query = f"{q}, Lima, Peru"
        
        response = requests.get(
            GOOGLE_GEOCODING_URL,
            params={
                "address": search_query,
                "key": api_key,
                "language": "es",
                "region": "pe"
            },
            timeout=10
        )
        
        response.raise_for_status()
        data = response.json()
        
        status = data.get("status")
        if status == "ZERO_RESULTS":
            return []
        elif status != "OK":
            logger.error(f"Google Geocoding API error: {status} - {data.get('error_message', '')}")
            raise HTTPException(status_code=502, detail=f"Geocoding service error: {status}")
        
        # Transform to our format
        results = []
        for item in data.get("results", [])[:limit]:
            location = item.get("geometry", {}).get("location", {})
            
            # Extract address components
            address_components = {}
            for component in item.get("address_components", []):
                for comp_type in component.get("types", []):
                    address_components[comp_type] = component.get("long_name", "")
            
            results.append({
                "display_name": item.get("formatted_address", ""),
                "lat": float(location.get("lat", 0)),
                "lon": float(location.get("lng", 0)),
                "address": address_components,
                "place_id": item.get("place_id", "")
            })
        
        logger.info(f"Google Geocoding search for '{q}' returned {len(results)} results")
        return results
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout searching for location: {q}")
        raise HTTPException(status_code=504, detail="Geocoding service timeout")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching for location: {e}")
        raise HTTPException(status_code=502, detail="Geocoding service error")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in geocoding search: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/reverse")
def reverse_geocode(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude")
) -> Dict:
    """
    Reverse geocode coordinates to get address using Google Geocoding API
    """
    try:
        api_key = settings.google_maps_api_key
        if not api_key:
            logger.error("Google Maps API key not configured")
            raise HTTPException(status_code=500, detail="Geocoding service not configured")
        
        response = requests.get(
            GOOGLE_GEOCODING_URL,
            params={
                "latlng": f"{lat},{lon}",
                "key": api_key,
                "language": "es",
                "result_type": "street_address|route|neighborhood|locality"
            },
            timeout=10
        )
        
        response.raise_for_status()
        data = response.json()
        
        status = data.get("status")
        if status == "ZERO_RESULTS":
            return {
                "display_name": f"{lat}, {lon}",
                "lat": lat,
                "lon": lon,
                "address": {}
            }
        elif status != "OK":
            logger.error(f"Google Reverse Geocoding error: {status}")
            raise HTTPException(status_code=502, detail=f"Geocoding service error: {status}")
        
        # Get the first (most precise) result
        first_result = data.get("results", [{}])[0]
        location = first_result.get("geometry", {}).get("location", {})
        
        # Extract address components
        address_components = {}
        for component in first_result.get("address_components", []):
            for comp_type in component.get("types", []):
                address_components[comp_type] = component.get("long_name", "")
        
        result = {
            "display_name": first_result.get("formatted_address", ""),
            "lat": float(location.get("lat", lat)),
            "lon": float(location.get("lng", lon)),
            "address": address_components,
            "place_id": first_result.get("place_id", "")
        }
        
        logger.info(f"Google Reverse geocoding for ({lat}, {lon}) successful")
        return result
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout reverse geocoding: ({lat}, {lon})")
        raise HTTPException(status_code=504, detail="Geocoding service timeout")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error reverse geocoding: {e}")
        raise HTTPException(status_code=502, detail="Geocoding service error")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in reverse geocoding: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
