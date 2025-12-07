"""
Geocoding API endpoints - Proxy for Nominatim to avoid CORS issues
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
import requests
import logging
import time

router = APIRouter()
logger = logging.getLogger(__name__)

# Rate limiting
last_request_time = 0
MIN_REQUEST_INTERVAL = 1.0  # seconds between requests (Nominatim policy)

def rate_limit():
    """Ensure we don't exceed Nominatim's rate limit (1 request per second)"""
    global last_request_time
    current_time = time.time()
    time_since_last = current_time - last_request_time
    
    if time_since_last < MIN_REQUEST_INTERVAL:
        time.sleep(MIN_REQUEST_INTERVAL - time_since_last)
    
    last_request_time = time.time()


@router.get("/search")
def search_location(
    q: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=10, description="Maximum number of results")
) -> List[Dict]:
    """
    Search for locations using Nominatim geocoding
    
    This endpoint proxies requests to Nominatim to avoid CORS issues
    and ensures proper User-Agent headers are sent.
    """
    try:
        rate_limit()
        
        # Add Lima, Peru context to improve results
        search_query = f"{q}, Lima, Peru"
        
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": search_query,
                "format": "json",
                "limit": limit,
                "addressdetails": 1
            },
            headers={
                "User-Agent": "TouristGen/1.0 (Educational Project)"
            },
            timeout=10
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Transform to our format
        results = []
        for item in data:
            results.append({
                "display_name": item.get("display_name", ""),
                "lat": float(item.get("lat", 0)),
                "lon": float(item.get("lon", 0)),
                "address": item.get("address", {})
            })
        
        logger.info(f"Geocoding search for '{q}' returned {len(results)} results")
        return results
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout searching for location: {q}")
        raise HTTPException(status_code=504, detail="Geocoding service timeout")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching for location: {e}")
        raise HTTPException(status_code=502, detail="Geocoding service error")
    except Exception as e:
        logger.error(f"Unexpected error in geocoding search: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/reverse")
def reverse_geocode(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude")
) -> Dict:
    """
    Reverse geocode coordinates to get address
    
    This endpoint proxies requests to Nominatim to avoid CORS issues.
    """
    try:
        rate_limit()
        
        response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={
                "lat": lat,
                "lon": lon,
                "format": "json"
            },
            headers={
                "User-Agent": "TouristGen/1.0 (Educational Project)"
            },
            timeout=10
        )
        
        response.raise_for_status()
        data = response.json()
        
        result = {
            "display_name": data.get("display_name", ""),
            "lat": float(data.get("lat", lat)),
            "lon": float(data.get("lon", lon)),
            "address": data.get("address", {})
        }
        
        logger.info(f"Reverse geocoding for ({lat}, {lon}) successful")
        return result
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout reverse geocoding: ({lat}, {lon})")
        raise HTTPException(status_code=504, detail="Geocoding service timeout")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error reverse geocoding: {e}")
        raise HTTPException(status_code=502, detail="Geocoding service error")
    except Exception as e:
        logger.error(f"Unexpected error in reverse geocoding: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
