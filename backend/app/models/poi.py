from sqlalchemy import Column, Integer, String, Float, JSON, Boolean, Text
from app.database import Base

class POI(Base):
    """Point of Interest model"""
    __tablename__ = "pois"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    address = Column(String(300))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    district = Column(String(100), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)  # Museum, Park, Beach, Restaurant, etc.
    
    # Scoring attributes
    popularity = Column(Integer, default=50)  # 1-100
    rating = Column(Float, default=0.0)  # 0-5 stars
    price_level = Column(Integer, default=1)  # 1-4 ($-$$$$)
    
    # Time constraints
    opening_hours = Column(JSON)  # {"monday": "09:00-18:00", "tuesday": "09:00-18:00", ...}
    closed_days = Column(JSON)  # ["sunday", "monday"]
    visit_duration = Column(Integer, default=60)  # Average visit time in minutes
    
    # Additional info
    tags = Column(JSON)  # ["cultural", "family-friendly", "outdoor", "historical"]
    description = Column(Text)
    image_url = Column(String(500))
    phone = Column(String(20))
    website = Column(String(300))
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Learning weights (adjusted based on feedback)
    learned_popularity = Column(Float, default=1.0)  # Multiplier based on user feedback
    
    def __repr__(self):
        return f"<POI(id={self.id}, name='{self.name}', district='{self.district}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "district": self.district,
            "category": self.category,
            "popularity": self.popularity,
            "rating": self.rating,
            "price_level": self.price_level,
            "opening_hours": self.opening_hours,
            "closed_days": self.closed_days,
            "visit_duration": self.visit_duration,
            "tags": self.tags,
            "description": self.description,
            "image_url": self.image_url,
            "phone": self.phone,
            "website": self.website
        }
