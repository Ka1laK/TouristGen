# backend/app/services/weight_optimizer.py
"""
Weight Optimizer Service - Uses regression to learn optimal weights from user feedback.

Flow:
1. User rates a route (1-5 stars)
2. Feedback stored in route_feedback table
3. When 30+ feedbacks exist, regression calculates optimal weights
4. New weights stored in learned_weights table
5. ACO uses learned weights instead of static defaults
"""
import logging
from typing import Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session
import numpy as np

from app.models.feedback import RouteFeedback, LearnedWeights
from app.services.optimization_weights import OptimizationWeights

logger = logging.getLogger(__name__)

# Configuration
MINIMUM_FEEDBACK_COUNT = 30  # Minimum feedbacks required before learning


@dataclass
class WeightOptimizerConfig:
    """Configuration for the weight optimizer"""
    minimum_feedback: int = MINIMUM_FEEDBACK_COUNT
    retrain_threshold: int = 10  # Retrain after this many new feedbacks


class WeightOptimizer:
    """
    Calculates optimal weights using linear regression on user feedback.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.config = WeightOptimizerConfig()
    
    def get_feedback_count(self) -> int:
        """Get total number of feedback records"""
        return self.db.query(RouteFeedback).count()
    
    def should_recalculate(self) -> bool:
        """Check if we have enough feedback to calculate new weights"""
        count = self.get_feedback_count()
        if count < self.config.minimum_feedback:
            logger.info(f"Not enough feedback yet: {count}/{self.config.minimum_feedback}")
            return False
        
        # Check if we have new feedbacks since last calculation
        active_weights = self.db.query(LearnedWeights).filter(
            LearnedWeights.is_active == True
        ).first()
        
        if not active_weights:
            # No weights calculated yet, should calculate
            return True
        
        # Check if enough new feedbacks since last calculation
        new_count = count - (active_weights.feedback_count or 0)
        return new_count >= self.config.retrain_threshold
    
    def calculate_optimal_weights(self) -> Optional[dict]:
        """
        Use linear regression to find optimal weights based on feedback.
        
        The regression finds which factors correlate most with high user ratings.
        """
        try:
            # Get all feedback records
            feedbacks = self.db.query(RouteFeedback).all()
            
            if len(feedbacks) < self.config.minimum_feedback:
                logger.warning(f"Insufficient feedback: {len(feedbacks)}")
                return None
            
            # Prepare data for regression
            # X: Features (characteristics of the route)
            # y: Target (user rating)
            X = []
            y = []
            
            for fb in feedbacks:
                # Normalize features to 0-1 range for fair comparison
                features = [
                    1.0 / (1.0 + (fb.total_distance_km or 1)),  # Inverse distance (closer = better)
                    (fb.avg_poi_popularity or 0) / 100.0,        # Popularity normalized
                    (fb.avg_poi_rating or 0) / 5.0,              # Rating normalized
                    0.5  # Urgency placeholder (not easily stored)
                ]
                X.append(features)
                y.append(fb.overall_rating)
            
            X = np.array(X)
            y = np.array(y)
            
            # Simple linear regression using normal equation
            # β = (X^T X)^(-1) X^T y
            XtX = X.T @ X
            Xty = X.T @ y
            
            # Add small regularization to prevent singular matrix
            regularization = 0.01 * np.eye(XtX.shape[0])
            coefficients = np.linalg.solve(XtX + regularization, Xty)
            
            # Ensure all coefficients are positive (weights should be positive)
            coefficients = np.maximum(coefficients, 0.05)
            
            # Normalize to sum to 1
            total = np.sum(coefficients)
            normalized_weights = coefficients / total
            
            # Calculate R² for model quality
            y_pred = X @ coefficients
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            logger.info(f"Calculated weights: distance={normalized_weights[0]:.3f}, "
                       f"popularity={normalized_weights[1]:.3f}, "
                       f"rating={normalized_weights[2]:.3f}, "
                       f"urgency={normalized_weights[3]:.3f}, "
                       f"R²={r_squared:.3f}")
            
            return {
                "distance_weight": float(normalized_weights[0]),
                "popularity_weight": float(normalized_weights[1]),
                "rating_weight": float(normalized_weights[2]),
                "urgency_weight": float(normalized_weights[3]),
                "model_accuracy": float(r_squared),
                "feedback_count": len(feedbacks)
            }
            
        except Exception as e:
            logger.error(f"Error calculating weights: {e}")
            return None
    
    def save_weights(self, weights: dict) -> LearnedWeights:
        """Save new weights to database, deactivating previous ones"""
        try:
            # Deactivate all previous weights
            self.db.query(LearnedWeights).update({LearnedWeights.is_active: False})
            
            # Create new active weights
            new_weights = LearnedWeights(
                distance_weight=weights["distance_weight"],
                popularity_weight=weights["popularity_weight"],
                urgency_weight=weights["urgency_weight"],
                rating_weight=weights["rating_weight"],
                feedback_count=weights["feedback_count"],
                model_accuracy=weights["model_accuracy"],
                is_active=True
            )
            
            self.db.add(new_weights)
            self.db.commit()
            self.db.refresh(new_weights)
            
            logger.info(f"Saved new learned weights with ID {new_weights.id}")
            return new_weights
            
        except Exception as e:
            logger.error(f"Error saving weights: {e}")
            self.db.rollback()
            raise
    
    def run_optimization(self) -> Optional[LearnedWeights]:
        """Main entry point: check if should recalculate and do it"""
        if not self.should_recalculate():
            return None
        
        weights = self.calculate_optimal_weights()
        if weights:
            return self.save_weights(weights)
        return None


def get_current_weights(db: Session) -> OptimizationWeights:
    """
    Get the current weights to use for optimization.
    Returns learned weights if available, otherwise static defaults.
    """
    # Try to get active learned weights
    learned = db.query(LearnedWeights).filter(
        LearnedWeights.is_active == True
    ).first()
    
    if learned:
        logger.info(f"Using learned weights (accuracy: {learned.model_accuracy:.3f})")
        return OptimizationWeights(
            distance_weight=learned.distance_weight,
            popularity_weight=learned.popularity_weight,
            urgency_weight=learned.urgency_weight,
            rating_weight=learned.rating_weight
        )
    else:
        logger.info("Using default static weights (no learned weights available)")
        return OptimizationWeights()  # Returns defaults


def save_route_feedback(
    db: Session,
    route_id: str,
    rating: int,
    route_data: dict,
    weights_used: OptimizationWeights
) -> RouteFeedback:
    """
    Save user feedback for a route.
    
    Args:
        db: Database session
        route_id: Unique identifier for the route
        rating: User rating (1-5)
        route_data: Dict with route characteristics (duration, cost, etc.)
        weights_used: The weights that were used to generate this route
    """
    feedback = RouteFeedback(
        route_id=route_id,
        overall_rating=rating,
        total_distance_km=route_data.get("total_distance_km"),
        total_duration_min=route_data.get("total_duration"),
        num_pois=route_data.get("num_pois"),
        total_cost=route_data.get("total_cost"),
        avg_poi_rating=route_data.get("avg_poi_rating"),
        avg_poi_popularity=route_data.get("avg_poi_popularity"),
        distance_weight=weights_used.distance_weight,
        popularity_weight=weights_used.popularity_weight,
        urgency_weight=weights_used.urgency_weight,
        rating_weight=weights_used.rating_weight,
        fitness_score=route_data.get("fitness_score")
    )
    
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    logger.info(f"Saved feedback for route {route_id}: {rating} stars")
    
    return feedback
