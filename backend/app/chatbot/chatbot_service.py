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

logger = logging.getLogger(__name__)


# In-memory session storage (for simplicity - could be Redis in production)
_sessions: Dict[str, ConversationState] = {}


class ChatbotService:
    """
    Service that manages chatbot conversations and parameter extraction
    """
    
    REQUIRED_PARAMS = ["max_duration", "max_budget", "start_time", "preferred_districts"]
    
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
        """Merge new parameters into existing ones (new values override)"""
        for key, value in new_params.items():
            if value is not None:
                if key == "mandatory_categories" and isinstance(value, list):
                    # Append categories, avoid duplicates
                    existing_cats = set(existing.mandatory_categories)
                    existing.mandatory_categories = list(existing_cats.union(set(value)))
                elif key == "avoid_categories" and isinstance(value, list):
                    existing_cats = set(existing.avoid_categories)
                    existing.avoid_categories = list(existing_cats.union(set(value)))
                elif key == "preferred_districts" and isinstance(value, list):
                    existing_dists = set(existing.preferred_districts)
                    existing.preferred_districts = list(existing_dists.union(set(value)))
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
        if not params.preferred_districts:
            missing.append("preferred_districts")
            
        return missing
    
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
            "user_pace": params.user_pace or "medium",
            "mandatory_categories": params.mandatory_categories,
            "avoid_categories": params.avoid_categories,
            "preferred_districts": params.preferred_districts,
            "transport_mode": params.transport_mode or "driving-car",
            "start_location": None  # Will need to geocode start_location_text if provided
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
