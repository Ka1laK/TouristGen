# backend/app/api/feedback.py
"""
API endpoints for route feedback collection and weight optimization.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
import logging

from app.database import get_db
from app.models.feedback import RouteFeedback, LearnedWeights
from app.services.weight_optimizer import (
    WeightOptimizer,
    save_route_feedback,
    get_current_weights
)
from app.services.optimization_weights import WEIGHTS

router = APIRouter()
logger = logging.getLogger(__name__)


class FeedbackRequest(BaseModel):
    """Request model for submitting route feedback"""
    route_id: str = Field(..., description="Unique route identifier")
    rating: int = Field(..., ge=1, le=5, description="User rating 1-5 stars")
    
    # Route characteristics
    total_duration: Optional[int] = None
    total_cost: Optional[float] = None
    num_pois: Optional[int] = None
    fitness_score: Optional[float] = None
    avg_poi_rating: Optional[float] = None
    avg_poi_popularity: Optional[float] = None
    total_distance_km: Optional[float] = None


class FeedbackResponse(BaseModel):
    """Response after submitting feedback"""
    success: bool
    feedback_id: int
    message: str
    total_feedback_count: int
    weights_updated: bool = False


class WeightsResponse(BaseModel):
    """Response with current weights"""
    distance_weight: float
    popularity_weight: float
    urgency_weight: float
    rating_weight: float
    is_learned: bool
    feedback_count: Optional[int] = None
    model_accuracy: Optional[float] = None


@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """
    Submit user feedback for a generated route.
    If enough feedback exists, triggers weight recalculation.
    """
    try:
        # Save the feedback
        route_data = {
            "total_duration": request.total_duration,
            "total_cost": request.total_cost,
            "num_pois": request.num_pois,
            "fitness_score": request.fitness_score,
            "avg_poi_rating": request.avg_poi_rating,
            "avg_poi_popularity": request.avg_poi_popularity,
            "total_distance_km": request.total_distance_km
        }
        
        # Get current weights that were used
        current_weights = get_current_weights(db)
        
        feedback = save_route_feedback(
            db=db,
            route_id=request.route_id,
            rating=request.rating,
            route_data=route_data,
            weights_used=current_weights
        )
        
        # Check if we should recalculate weights
        optimizer = WeightOptimizer(db)
        total_count = optimizer.get_feedback_count()
        
        weights_updated = False
        if optimizer.should_recalculate():
            logger.info("Triggering weight recalculation...")
            result = optimizer.run_optimization()
            if result:
                weights_updated = True
                logger.info(f"Weights updated successfully!")
        
        return FeedbackResponse(
            success=True,
            feedback_id=feedback.id,
            message=f"¡Gracias por tu calificación de {request.rating} estrellas!",
            total_feedback_count=total_count,
            weights_updated=weights_updated
        )
        
    except Exception as e:
        logger.error(f"Error saving feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weights", response_model=WeightsResponse)
async def get_weights(db: Session = Depends(get_db)):
    """
    Get current optimization weights (learned or static).
    """
    # Check for learned weights
    learned = db.query(LearnedWeights).filter(
        LearnedWeights.is_active == True
    ).first()
    
    if learned:
        return WeightsResponse(
            distance_weight=learned.distance_weight,
            popularity_weight=learned.popularity_weight,
            urgency_weight=learned.urgency_weight,
            rating_weight=learned.rating_weight,
            is_learned=True,
            feedback_count=learned.feedback_count,
            model_accuracy=learned.model_accuracy
        )
    else:
        return WeightsResponse(
            distance_weight=WEIGHTS.distance_weight,
            popularity_weight=WEIGHTS.popularity_weight,
            urgency_weight=WEIGHTS.urgency_weight,
            rating_weight=WEIGHTS.rating_weight,
            is_learned=False
        )


@router.get("/stats")
async def get_feedback_stats(db: Session = Depends(get_db)):
    """
    Get feedback statistics for monitoring.
    """
    total = db.query(RouteFeedback).count()
    
    if total > 0:
        from sqlalchemy import func
        avg_rating = db.query(func.avg(RouteFeedback.overall_rating)).scalar()
    else:
        avg_rating = None
    
    # Get weight history
    weight_history = db.query(LearnedWeights).order_by(
        LearnedWeights.created_at.desc()
    ).limit(5).all()
    
    return {
        "total_feedback": total,
        "average_rating": round(float(avg_rating), 2) if avg_rating else None,
        "minimum_required": 30,
        "ready_for_learning": total >= 30,
        "weight_updates": len(weight_history),
        "latest_weights": weight_history[0].to_dict() if weight_history else None
    }
