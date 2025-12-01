from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON
from datetime import datetime
from app.database import Base

class Feedback(Base):
    """User feedback on routes and POIs"""
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Route information
    route_id = Column(String(100), index=True)  # UUID for the generated route
    poi_id = Column(Integer, ForeignKey("pois.id"), nullable=False)
    
    # User feedback
    rating = Column(Float)  # 1-5 stars for the POI
    visited = Column(Integer, default=0)  # 1 if visited, 0 if skipped
    too_crowded = Column(Integer, default=0)  # 1 if user reported crowding
    
    # Context
    weather_condition = Column(String(50))  # "sunny", "rainy", "cloudy"
    temperature = Column(Float)  # Celsius
    user_pace = Column(String(20))  # "slow", "medium", "fast"
    time_of_day = Column(String(20))  # "morning", "afternoon", "evening"
    
    # Additional feedback
    comments = Column(String(500))
    suggested_duration = Column(Integer)  # If user thinks visit_duration should be different
    
    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_session = Column(String(100))  # Session identifier
    
    def __repr__(self):
        return f"<Feedback(id={self.id}, poi_id={self.poi_id}, rating={self.rating})>"
