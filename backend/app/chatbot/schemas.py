"""
Pydantic schemas for the chatbot module
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatMessage(BaseModel):
    """Single chat message"""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now)


class ExtractedParameters(BaseModel):
    """Parameters extracted from conversation by Gemini"""
    max_duration: Optional[int] = Field(None, description="Trip duration in minutes (60-720)")
    max_budget: Optional[float] = Field(None, description="Budget in soles")
    start_time: Optional[str] = Field(None, description="Start time in HH:MM format")
    user_pace: Optional[str] = Field(None, description="Pace: slow, medium, fast")
    mandatory_categories: List[str] = Field(default_factory=list)
    avoid_categories: List[str] = Field(default_factory=list)
    preferred_districts: List[str] = Field(default_factory=list)
    transport_mode: Optional[str] = Field(None, description="driving-car or foot-walking")
    start_location_text: Optional[str] = Field(None, description="Text description of start location")
    day_of_week: Optional[str] = Field(None, description="Day of week: Monday, Tuesday, etc.")
    place_references: List[str] = Field(default_factory=list, description="Place names mentioned by user for district inference")
    

class ConversationState(BaseModel):
    """State of an ongoing conversation"""
    session_id: str
    messages: List[ChatMessage] = Field(default_factory=list)
    extracted_params: ExtractedParameters = Field(default_factory=ExtractedParameters)
    is_complete: bool = Field(False, description="All required params collected")
    missing_params: List[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    """Request to send a message to the chatbot"""
    message: str = Field(..., description="User message", min_length=1)
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")


class ChatResponse(BaseModel):
    """Response from the chatbot"""
    session_id: str
    assistant_message: str
    extracted_params: ExtractedParameters
    missing_params: List[str]
    is_ready_to_generate: bool
    

class GenerateRouteFromChatRequest(BaseModel):
    """Request to generate route from chat session"""
    session_id: str
    # Optional overrides
    start_location: Optional[Dict[str, float]] = Field(None, description="Override start location {latitude, longitude}")
