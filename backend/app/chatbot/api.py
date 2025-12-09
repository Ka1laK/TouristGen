"""
Chatbot API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
import logging

from .schemas import ChatRequest, ChatResponse, GenerateRouteFromChatRequest
from .chatbot_service import ChatbotService
from app.database import get_db
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize chatbot service
_chatbot_service: Optional[ChatbotService] = None


def get_chatbot_service() -> ChatbotService:
    """Dependency to get chatbot service instance"""
    global _chatbot_service
    if _chatbot_service is None:
        # Get Gemini API key from settings or environment
        gemini_key = getattr(settings, 'gemini_api_key', None)
        _chatbot_service = ChatbotService(gemini_api_key=gemini_key)
    return _chatbot_service


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    chatbot: ChatbotService = Depends(get_chatbot_service)
):
    """
    Send a message to the chatbot
    
    The chatbot will:
    1. Understand your request in natural language
    2. Extract trip parameters (duration, budget, districts, etc.)
    3. Ask for missing information if needed
    4. Let you know when ready to generate a route
    
    Example messages:
    - "Quiero una salida romántica con mi novia en Miraflores"
    - "Tenemos poco presupuesto y unas 3 horas libres"
    - "Saldremos a las 2pm"
    """
    try:
        response = await chatbot.process_message(
            message=request.message,
            session_id=request.session_id
        )
        return response
    except Exception as e:
        logger.error(f"Error processing chat message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session(
    session_id: str,
    chatbot: ChatbotService = Depends(get_chatbot_service)
):
    """Get current session state and extracted parameters"""
    summary = chatbot.get_session_summary(session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")
    return summary


@router.delete("/session/{session_id}")
async def clear_session(
    session_id: str,
    chatbot: ChatbotService = Depends(get_chatbot_service)
):
    """Clear a chat session and start fresh"""
    success = chatbot.clear_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session cleared", "session_id": session_id}


@router.post("/generate-route")
async def generate_route_from_chat(
    request: GenerateRouteFromChatRequest,
    chatbot: ChatbotService = Depends(get_chatbot_service),
    db: Session = Depends(get_db)
):
    """
    Generate optimized route using parameters extracted from chat
    
    This endpoint:
    1. Gets the extracted parameters from the chat session
    2. Auto-populates POIs if districts have few places
    3. Validates all required parameters are present
    4. Calls the main optimization API
    5. Returns the optimized route
    """
    # Minimum POIs required per district before triggering auto-fetch
    MIN_POIS_PER_DISTRICT = 5
    
    # Get optimization parameters from session
    params = chatbot.get_optimization_params(request.session_id)
    
    if params is None:
        # Get session to check what's missing
        summary = chatbot.get_session_summary(request.session_id)
        if summary is None:
            raise HTTPException(status_code=404, detail="Session not found")
        raise HTTPException(
            status_code=400, 
            detail=f"Missing required parameters: {summary.get('missing_params', [])}"
        )
    
    # --- AUTO-POPULATE LOGIC ---
    # Check if districts have enough POIs, if not, fetch from Google Places API
    preferred_districts = params.get("preferred_districts", [])
    if preferred_districts:
        from app.services.poi_service import POIService
        from app.services.maps_service import LimaPlacesExtractor
        
        poi_service = POIService(db)
        districts_to_populate = []
        
        for district in preferred_districts:
            pois_in_district = poi_service.get_pois_by_district(district)
            poi_count = len(pois_in_district)
            logger.info(f"District '{district}' has {poi_count} POIs")
            
            if poi_count < MIN_POIS_PER_DISTRICT:
                districts_to_populate.append(district)
        
        # Fetch POIs for districts with insufficient places
        if districts_to_populate:
            logger.info(f"Auto-populating POIs for districts: {districts_to_populate}")
            try:
                extractor = LimaPlacesExtractor()
                extractor.extract_and_populate_db(districts=districts_to_populate)
                logger.info(f"Successfully populated POIs for: {districts_to_populate}")
            except Exception as e:
                logger.warning(f"Failed to auto-populate POIs: {e}")
                # Continue anyway - we'll use whatever POIs are available
    # -----------------------------
    
    # Apply any overrides
    if request.start_location:
        params["start_location"] = request.start_location
    
    # Geocode start_location_text if provided but no direct start_location
    if not params.get("start_location") and params.get("start_location_text"):
        from app.api.geocoding import geocode_location
        try:
            start_text = params["start_location_text"]
            logger.info(f"Geocoding start location: {start_text}")
            geocode_result = await geocode_location(start_text)
            if geocode_result and len(geocode_result) > 0:
                params["start_location"] = {
                    "latitude": float(geocode_result[0]["lat"]),
                    "longitude": float(geocode_result[0]["lon"])
                }
                logger.info(f"Geocoded '{start_text}' to {params['start_location']}")
            else:
                logger.warning(f"Could not geocode: {start_text}")
        except Exception as e:
            logger.warning(f"Geocoding failed for '{params['start_location_text']}': {e}")
    
    # Remove start_location_text since the optimizer expects start_location dict
    params.pop("start_location_text", None)
    
    # Import and call the optimization endpoint
    from app.api.optimizer import generate_route, OptimizationRequest
    from fastapi import BackgroundTasks
    
    try:
        # Create optimization request
        opt_request = OptimizationRequest(**params)
        
        # Call the existing optimization logic
        background_tasks = BackgroundTasks()
        result = await generate_route(opt_request, background_tasks, db)
        
        return {
            "success": True,
            "session_id": request.session_id,
            "route": result
        }
    except Exception as e:
        logger.error(f"Error generating route from chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def chatbot_health(
    chatbot: ChatbotService = Depends(get_chatbot_service)
):
    """Check if chatbot service is healthy"""
    return {
        "status": "healthy",
        "gemini_available": chatbot.gemini.is_available()
    }
