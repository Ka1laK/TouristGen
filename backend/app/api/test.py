from fastapi import APIRouter
from pydantic import BaseModel
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class TestResponse(BaseModel):
    message: str
    status: str


@router.get("/test", response_model=TestResponse)
def test_endpoint():
    """Simple test endpoint to verify API is working"""
    logger.info("Test endpoint called successfully")
    return TestResponse(
        message="Backend is working correctly!",
        status="ok"
    )


@router.post("/test-route")
def test_route_generation():
    """Test route generation without heavy computation"""
    logger.info("Test route generation called")
    
    # Simple mock response
    return {
        "message": "Test successful",
        "route": [
            {"id": 1, "name": "Test POI 1"},
            {"id": 2, "name": "Test POI 2"}
        ],
        "status": "ok"
    }
