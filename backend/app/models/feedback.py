from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from app.database import Base
from datetime import datetime


class RouteFeedback(Base):
    """Stores user feedback for generated routes - used for weight optimization"""
    __tablename__ = "route_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # User rating (1-5 stars)
    overall_rating = Column(Integer, nullable=False)
    
    # Route characteristics for regression
    total_distance_km = Column(Float)
    total_duration_min = Column(Integer)
    num_pois = Column(Integer)
    total_cost = Column(Float)
    avg_poi_rating = Column(Float)
    avg_poi_popularity = Column(Float)
    
    # Weights used when generating this route
    distance_weight = Column(Float)
    popularity_weight = Column(Float)
    urgency_weight = Column(Float)
    rating_weight = Column(Float)
    
    # Fitness score achieved
    fitness_score = Column(Float)
    
    def __repr__(self):
        return f"<RouteFeedback(route_id={self.route_id}, rating={self.overall_rating})>"


class LearnedWeights(Base):
    """Stores learned optimization weights from regression analysis"""
    __tablename__ = "learned_weights"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Learned weight values
    distance_weight = Column(Float, nullable=False)
    popularity_weight = Column(Float, nullable=False)
    urgency_weight = Column(Float, nullable=False)
    rating_weight = Column(Float, nullable=False)
    
    # Metadata
    feedback_count = Column(Integer)  # Number of feedbacks used to train
    model_accuracy = Column(Float)    # R² score of the regression model
    is_active = Column(Boolean, default=True)  # Only one should be active
    
    def __repr__(self):
        return f"<LearnedWeights(id={self.id}, active={self.is_active}, accuracy={self.model_accuracy})>"
    
    def to_dict(self):
        return {
            "distance_weight": self.distance_weight,
            "popularity_weight": self.popularity_weight,
            "urgency_weight": self.urgency_weight,
            "rating_weight": self.rating_weight,
            "feedback_count": self.feedback_count,
            "model_accuracy": self.model_accuracy
        }
