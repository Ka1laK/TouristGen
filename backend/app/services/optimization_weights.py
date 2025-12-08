# backend/app/services/optimization_weights.py
"""
Centralized optimization weights configuration.
All optimization algorithms should use these weights to ensure consistency.
"""
from dataclasses import dataclass


@dataclass
class OptimizationWeights:
    """
    Unified weights for route optimization.
    Used by both ACO heuristic and TOPTW fitness calculation.
    """
    # === Heuristic Component Weights (should sum to 1.0) ===
    distance_weight: float = 0.35      # Closer POIs preferred
    popularity_weight: float = 0.30    # More popular POIs preferred
    urgency_weight: float = 0.20       # POIs closing soon get priority
    rating_weight: float = 0.15        # Higher rated POIs preferred
    
    # === Fitness Penalty Weights ===
    travel_time_penalty: float = 0.1   # Penalty per minute of travel
    cost_penalty: float = 0.5          # Penalty per unit of cost
    constraint_violation: float = 2.0  # Penalty for violating constraints
    
    # === Time Window Penalties ===
    wait_time_penalty: float = 0.5     # Penalty per minute of waiting
    missed_poi_penalty: float = 200    # Penalty for missing a POI (closed)
    insufficient_time_penalty: float = 150  # Penalty for not enough visit time
    avoided_category_penalty: float = 50    # Penalty for visiting avoided category
    mandatory_missing_penalty: float = 100  # Penalty for missing mandatory category
    
    # === Urgency Penalties ===
    non_visitable_penalty: float = 300  # Penalty when urgency_weight = 0


# Singleton instance - import this in other modules
WEIGHTS = OptimizationWeights()
