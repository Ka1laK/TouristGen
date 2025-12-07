from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.services.poi_service import POIService
from app.services.maps_service import LimaPlacesExtractor
from app.models.poi import POI
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Pydantic models for request/response
class POIResponse(BaseModel):
    id: int
    name: str
    address: Optional[str]
    latitude: float
    longitude: float
    district: str
    category: str
    popularity: int
    rating: float
    price_level: int
    opening_hours: Optional[dict]
    closed_days: Optional[List[str]]
    visit_duration: int
    tags: Optional[List[str]]
    description: Optional[str]
    image_url: Optional[str]
    
    class Config:
        from_attributes = True


class POICreate(BaseModel):
    name: str
    address: Optional[str] = None
    latitude: float
    longitude: float
    district: str
    category: str
    popularity: int = 50
    rating: float = 0.0
    price_level: int = 1
    opening_hours: Optional[dict] = None
    closed_days: Optional[List[str]] = None
    visit_duration: int = 60
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None

class SyncRequest(BaseModel):
    districts: Optional[List[str]] = None
    force_refresh: bool = False

def run_sync_task(districts: Optional[List[str]]):
    """Background task to run the extraction"""
    logger.info("Starting background sync task...")
    try:
        extractor = LimaPlacesExtractor()
        # If no districts provided to task, it uses default list in service
        result = extractor.extract_and_populate_db(districts=districts)
        logger.info(f"Background sync complete. Added: {result['added']}, Updated: {result['updated']}")
    except Exception as e:
        logger.error(f"Background sync failed: {e}")


@router.post("/sync", status_code=202)
def sync_pois_from_google(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger a background task to fetch POIs from Google Places API (New).
    This replaces static JSON loading.
    
    - **districts**: List of districts to scan (optional, defaults to all if empty)
    """
    # Validation logic could go here
    
    background_tasks.add_task(run_sync_task, request.districts)
    
    return {
        "message": "Sync task started in background",
        "details": f"Targeting {len(request.districts) if request.districts else 'ALL'} districts"
    }


@router.get("/", response_model=List[POIResponse])
def get_all_pois(
    district: Optional[str] = Query(None, description="Filter by district"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_rating: Optional[float] = Query(None, description="Minimum rating"),
    max_price: Optional[int] = Query(None, description="Maximum price level"),
    db: Session = Depends(get_db)
):
    """Get all POIs with optional filters"""
    service = POIService(db)
    
    if district:
        pois = service.get_pois_by_district(district)
    elif category:
        pois = service.get_pois_by_category(category)
    else:
        pois = service.get_all_pois()
    
    # Apply additional filters
    if min_rating is not None:
        pois = [poi for poi in pois if poi.rating >= min_rating]
    
    if max_price is not None:
        pois = [poi for poi in pois if poi.price_level <= max_price]
    
    return pois


@router.get("/{poi_id}", response_model=POIResponse)
def get_poi(poi_id: int, db: Session = Depends(get_db)):
    """Get a specific POI by ID"""
    service = POIService(db)
    poi = service.get_poi_by_id(poi_id)
    
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    
    return poi


@router.post("/", response_model=POIResponse)
def create_poi(poi_data: POICreate, db: Session = Depends(get_db)):
    """Create a new POI"""
    service = POIService(db)
    poi = service.create_poi(poi_data.model_dump())
    return poi


@router.get("/districts/list")
def get_districts(db: Session = Depends(get_db)):
    """Get list of all districts"""
    service = POIService(db)
    districts = service.get_districts()
    return {"districts": districts}


@router.get("/categories/list")
def get_categories(db: Session = Depends(get_db)):
    """Get list of all categories"""
    service = POIService(db)
    categories = service.get_categories()
    return {"categories": categories}


@router.get("/popular/top")
def get_popular_pois(
    limit: int = Query(10, description="Number of POIs to return"),
    db: Session = Depends(get_db)
):
    """Get most popular POIs"""
    service = POIService(db)
    pois = service.get_popular_pois(limit=limit)
    return pois


@router.get("/stats/overview")
def get_stats(db: Session = Depends(get_db)):
    """Get overview statistics"""
    service = POIService(db)
    
    pois_list = service.get_all_pois() # Optimize: Avoid fetching all if just counting
    total_pois = len(pois_list)
    districts = service.get_districts()
    categories = service.get_categories()
    district_counts = service.get_poi_count_by_district()
    
    return {
        "total_pois": total_pois,
        "total_districts": len(districts),
        "total_categories": len(categories),
        "districts": districts,
        "categories": categories,
        "pois_per_district": district_counts
    }
