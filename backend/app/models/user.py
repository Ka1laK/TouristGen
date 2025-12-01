from sqlalchemy import Column, Integer, String, JSON, DateTime
from datetime import datetime
from app.database import Base

class UserProfile(Base):
    """User profile and preferences"""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True)
    
    # Preferences
    preferred_categories = Column(JSON)  # ["museum", "park", "beach"]
    avoided_categories = Column(JSON)  # ["nightlife", "shopping"]
    preferred_districts = Column(JSON)  # ["Miraflores", "Barranco"]
    
    # Behavioral patterns
    typical_pace = Column(String(20), default="medium")  # "slow", "medium", "fast"
    typical_budget = Column(Integer, default=100)  # Typical budget in local currency
    typical_duration = Column(Integer, default=480)  # Typical trip duration in minutes (8 hours)
    
    # Learning data
    visit_history = Column(JSON)  # List of visited POI IDs
    favorite_pois = Column(JSON)  # List of favorite POI IDs
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserProfile(id={self.id}, session_id='{self.session_id}')>"
