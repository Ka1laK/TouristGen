"""
Chatbot service - manages conversation state and orchestrates parameter extraction
"""
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import logging

from .schemas import (
    ChatMessage, 
    ExtractedParameters, 
    ConversationState,
    ChatResponse
)
from .gemini_service import GeminiService
from app.database import SessionLocal
from app.services.poi_service import POIService
from app.services.maps_service import search_text_new_api
from app.config import settings

logger = logging.getLogger(__name__)


# In-memory session storage (for simplicity - could be Redis in production)
_sessions: Dict[str, ConversationState] = {}


class ChatbotService:
    """
    Service that manages chatbot conversations and parameter extraction
    """
    
    REQUIRED_PARAMS = ["max_duration", "max_budget", "start_time", "day_of_week", "preferred_districts"]
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        self.gemini = GeminiService(api_key=gemini_api_key)
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> ConversationState:
        """Get existing session or create a new one"""
        if session_id and session_id in _sessions:
            return _sessions[session_id]
        
        new_session_id = session_id or str(uuid.uuid4())
        session = ConversationState(session_id=new_session_id)
        _sessions[new_session_id] = session
        return session
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a session"""
        if session_id in _sessions:
            del _sessions[session_id]
            return True
        return False
    
    async def process_message(self, message: str, session_id: Optional[str] = None) -> ChatResponse:
        """
        Process a user message and return chatbot response
        
        Args:
            message: User's message
            session_id: Optional session ID for continuity
            
        Returns:
            ChatResponse with assistant message and extracted parameters
        """
        # Get or create session
        session = self.get_or_create_session(session_id)
        
        # Add user message to history
        user_msg = ChatMessage(role="user", content=message)
        session.messages.append(user_msg)
        
        # Prepare conversation history for Gemini
        history = [{"role": m.role, "content": m.content} for m in session.messages]
        
        # Call Gemini to process message
        result = await self.gemini.process_message(message, history)
        
        # Update extracted parameters (merge with existing)
        new_params = result.get("extracted_params", {})
        self._merge_params(session.extracted_params, new_params)
        
        # Infer districts from place_references (NOT from start_location)
        if session.extracted_params.place_references:
            inferred_districts = await self._infer_districts_from_places(
                session.extracted_params.place_references
            )
            for district in inferred_districts:
                if district not in session.extracted_params.preferred_districts:
                    session.extracted_params.preferred_districts.append(district)
                    logger.info(f"Inferred district '{district}' from place references")
        
        # Calculate missing parameters
        missing = self._get_missing_params(session.extracted_params)
        session.missing_params = missing
        session.is_complete = len(missing) == 0
        
        # Add assistant response to history
        assistant_msg = ChatMessage(
            role="assistant", 
            content=result.get("assistant_message", "")
        )
        session.messages.append(assistant_msg)
        
        # Build response
        return ChatResponse(
            session_id=session.session_id,
            assistant_message=result.get("assistant_message", ""),
            extracted_params=session.extracted_params,
            missing_params=missing,
            is_ready_to_generate=session.is_complete
        )
    
    def _merge_params(self, existing: ExtractedParameters, new_params: Dict[str, Any]):
        """
        Merge new parameters into existing ones.
        Implements category conflict resolution: categories in avoid remove from mandatory and vice versa.
        """
        for key, value in new_params.items():
            if value is not None:
                if key == "mandatory_categories" and isinstance(value, list):
                    # Add to mandatory, remove from avoid (conflict resolution)
                    for cat in value:
                        if cat in existing.avoid_categories:
                            existing.avoid_categories.remove(cat)
                            logger.info(f"Conflict resolution: Moved '{cat}' from avoid to mandatory")
                        if cat not in existing.mandatory_categories:
                            existing.mandatory_categories.append(cat)
                            
                elif key == "avoid_categories" and isinstance(value, list):
                    # Add to avoid, remove from mandatory (conflict resolution)
                    for cat in value:
                        if cat in existing.mandatory_categories:
                            existing.mandatory_categories.remove(cat)
                            logger.info(f"Conflict resolution: Moved '{cat}' from mandatory to avoid")
                        if cat not in existing.avoid_categories:
                            existing.avoid_categories.append(cat)
                            
                elif key == "preferred_districts" and isinstance(value, list):
                    existing_dists = set(existing.preferred_districts)
                    existing.preferred_districts = list(existing_dists.union(set(value)))
                    
                elif key == "place_references" and isinstance(value, list):
                    # Append place references, avoid duplicates
                    existing_refs = set(existing.place_references)
                    existing.place_references = list(existing_refs.union(set(value)))
                    
                elif hasattr(existing, key):
                    setattr(existing, key, value)
    
    def _get_missing_params(self, params: ExtractedParameters) -> list:
        """Get list of missing required parameters"""
        missing = []
        
        if not params.max_duration:
            missing.append("max_duration")
        if not params.max_budget:
            missing.append("max_budget")
        if not params.start_time:
            missing.append("start_time")
        if not params.day_of_week:
            missing.append("day_of_week")
        if not params.preferred_districts:
            missing.append("preferred_districts")
            
        return missing
    
    async def _infer_districts_from_places(self, place_references: list) -> list:
        """
        Infer districts from place names by searching the database.
        Falls back to Google Places API if not found in DB.
        
        Args:
            place_references: List of place names mentioned by user
            
        Returns:
            List of inferred district names
        """
        inferred_districts = []
        
        db = SessionLocal()
        try:
            poi_service = POIService(db)
            
            for place_name in place_references:
                # Search in database first
                matching_pois = poi_service.search_by_name(place_name, limit=3)
                
                if matching_pois:
                    # Found in DB - use the district of the best match
                    best_match = matching_pois[0]
                    if best_match.district and best_match.district not in inferred_districts:
                        inferred_districts.append(best_match.district)
                        logger.info(f"Found '{place_name}' in DB -> District: {best_match.district}")
                else:
                    # Not found in DB - try Google Places API as fallback
                    logger.info(f"'{place_name}' not in DB, trying Google Places API...")
                    try:
                        api_key = settings.google_maps_api_key
                        if api_key:
                            results = search_text_new_api(f"{place_name} Lima Peru", api_key)
                            if results:
                                # Extract district from address
                                address = results[0].get('formattedAddress', '')
                                district = self._extract_district_from_address(address)
                                if district and district not in inferred_districts:
                                    inferred_districts.append(district)
                                    logger.info(f"Found '{place_name}' via API -> District: {district}")
                    except Exception as e:
                        logger.warning(f"Failed to search Google Places for '{place_name}': {e}")
                        
        finally:
            db.close()
        
        return inferred_districts
    
    def _extract_district_from_address(self, address: str) -> Optional[str]:
        """Extract district name from a formatted address."""
        # Known districts in Lima
        KNOWN_DISTRICTS = [
            "Miraflores", "Barranco", "San Isidro", "Surco", "Santiago de Surco",
            "La Molina", "San Borja", "San Miguel", "Pueblo Libre", "Jesús María",
            "Lince", "Magdalena", "Magdalena del Mar", "Chorrillos", "Lima", 
            "Lima Cercado", "Callao", "La Victoria", "Breña", "Rímac",
            "Los Olivos", "San Martín de Porres", "Comas", "Independencia",
            "San Juan de Lurigancho", "Ate", "Santa Anita", "El Agustino",
            "San Juan de Miraflores", "Villa El Salvador", "Villa María del Triunfo"
        ]
        
        address_lower = address.lower()
        for district in KNOWN_DISTRICTS:
            if district.lower() in address_lower:
                return district
        
        return None
    
    def get_optimization_params(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get parameters ready for the optimization API
        
        Returns None if required params are missing
        """
        if session_id not in _sessions:
            return None
        
        session = _sessions[session_id]
        params = session.extracted_params
        
        # Check if complete
        if not session.is_complete:
            return None
        
        # Build optimization request format
        return {
            "max_duration": params.max_duration,
            "max_budget": params.max_budget,
            "start_time": params.start_time,
            "day_of_week": params.day_of_week,
            "user_pace": params.user_pace or "medium",
            "mandatory_categories": params.mandatory_categories,
            "avoid_categories": params.avoid_categories,
            "preferred_districts": params.preferred_districts,
            "transport_mode": params.transport_mode or "driving-car",
            "start_location": None  # Start location geocoding not implemented
        }
    
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of the current session state"""
        if session_id not in _sessions:
            return None
        
        session = _sessions[session_id]
        return {
            "session_id": session.session_id,
            "message_count": len(session.messages),
            "extracted_params": session.extracted_params.model_dump(),
            "missing_params": session.missing_params,
            "is_ready": session.is_complete
        }
