import random
import numpy as np
from typing import List, Tuple, Dict, Optional
from .toptw_solver import TOPTWSolver, POINode, TOPTWConstraints
from .hours_utils import calculate_urgency_weight
import logging

logger = logging.getLogger(__name__)

class AntColonyOptimizer:
    """
    Ant Colony Optimization (ACO) for solving TOPTW
    
    Uses:
    - Pheromone matrix to learn good transitions
    - Heuristic information (distance, popularity, time windows)
    - Elitist pheromone update
    """
    
    def __init__(
        self,
        pois: List[POINode],
        constraints: TOPTWConstraints,
        num_ants: int = 30,
        iterations: int = 100,
        alpha: float = 1.0,  # Pheromone importance
        beta: float = 2.5,   # Heuristic importance
        evaporation_rate: float = 0.1,
        q: float = 100.0,    # Pheromone deposit factor
        start_location: tuple = None  # (latitude, longitude) of starting point
    ):
        self.pois = pois
        self.constraints = constraints
        self.solver = TOPTWSolver(pois, constraints)
        self.start_location = start_location  # Store start location for route optimization
        
        # ACO parameters
        self.num_ants = num_ants
        self.iterations = iterations
        self.alpha = alpha
        self.beta = beta
        self.evaporation_rate = evaporation_rate
        self.q = q
        
        # State
        self.num_nodes = len(pois)
        self.pheromone_matrix = np.ones((self.num_nodes, self.num_nodes)) * 0.1
        self.best_solution = []
        self.best_fitness = 0.0
        self.fitness_history = []
    
    def set_start_location(self, start_location: tuple):
        """Set the starting location (latitude, longitude) for route optimization"""
        self.start_location = start_location
        
    def set_distance_matrix(self, time_matrix: np.ndarray):
        """Set the travel time matrix for the solver"""
        self.solver.set_distance_matrix(time_matrix)
    
    def set_start_to_poi_times(self, times: List[float]):
        """Set travel times from start location to each POI (from OpenRouteService)"""
        self.start_to_poi_times = times
        self.solver.set_start_to_poi_times(times)
        
    # Maximum wait time allowed (in minutes) before a POI opens
    MAX_WAIT_TIME = 30

    
    def _calculate_heuristic(self, current_idx: int, next_idx: int, current_time: int) -> float:
        """
        Calculate heuristic value (eta) for moving from current to next node.
        Uses centralized weights from optimization_weights.py for consistency with fitness calculation.
        
        IMPORTANT: All scores are normalized to 0.0-1.0 scale so weights work as intended.
        """
        from app.services.optimization_weights import WEIGHTS
        from app.services.hours_utils import parse_opening_hours
        
        next_poi = self.pois[next_idx]
        
        # 1. Distance/Time Heuristic (NORMALIZED: 0-1 scale)
        # 0 min travel = 1.0, 60+ min travel = 0.0
        travel_time = 0
        if self.solver.time_matrix is not None:
            travel_time = self.solver.time_matrix[current_idx][next_idx]
        else:
            travel_time = self.solver._estimate_travel_time(self.pois[current_idx], next_poi)
        
        # Normalize: closer = higher score (linear decay over 60 min)
        dist_score = max(0.0, 1.0 - (travel_time / 60.0))
        
        # 2. Popularity Heuristic (already 0-1: pop/100)
        pop_score = min(1.0, next_poi.popularity / 100.0)
        
        # 3. Time Window Heuristic - CHECK BOTH OPENING AND CLOSING TIME
        arrival_time = current_time + travel_time
        
        # Get actual opening hours for the day
        opening_time = next_poi.opening_time
        closing_time = next_poi.closing_time
        
        # If we have detailed opening_hours, parse them
        if hasattr(next_poi, 'opening_hours') and next_poi.opening_hours:
            parsed_open, parsed_close = parse_opening_hours(
                next_poi.opening_hours, 
                self.constraints.day_of_week
            )
            if parsed_open is not None:
                opening_time = parsed_open
                closing_time = parsed_close
        
        # Check if POI is closed this day
        if opening_time is None:
            return 0.0  # Closed today - infeasible
        
        # Check if we arrive after closing
        if arrival_time >= closing_time:
            return 0.0  # Can't visit - too late
        
        # FIX: Check if POI hasn't opened yet and calculate wait time
        wait_time = 0
        if arrival_time < opening_time:
            wait_time = opening_time - arrival_time
            # EXCLUDE POIs that require excessive waiting
            if wait_time > self.MAX_WAIT_TIME:
                return 0.0  # Too much waiting - not worth it
        
        # Urgency: normalize based on how much time left (0-1 scale)
        # Less than 60 min left = high urgency (1.0), more than 300 min = low urgency (0.0)
        effective_arrival = max(arrival_time, opening_time)  # Account for wait time
        time_left = closing_time - effective_arrival
        urgency_score = max(0.0, min(1.0, 1.0 - (time_left / 300.0)))
        
        # 4. Rating Heuristic (already 0-1: rating/5)
        rating_score = (next_poi.rating / 5.0) if next_poi.rating else 0.5
        
        # 5. Wait time penalty (reduce score if we have to wait)
        wait_penalty = 1.0 - (wait_time / self.MAX_WAIT_TIME) if wait_time > 0 else 1.0
        
        # Combine heuristics using CENTRALIZED WEIGHTS
        # Now all scores are 0-1, so weights work as intended!
        total = (
            (dist_score * WEIGHTS.distance_weight) +
            (pop_score * WEIGHTS.popularity_weight) +
            (urgency_score * WEIGHTS.urgency_weight) +
            (rating_score * WEIGHTS.rating_weight)
        ) * wait_penalty  # Apply wait penalty to total score
        
        return total

    def _select_next_node(self, ant_route: List[int], visited: set, current_time: int) -> Optional[int]:
        """Select the next node for an ant using probabilistic transition rule"""
        current_idx = ant_route[-1]
        
        probabilities = []
        candidates = []
        
        for next_idx in range(self.num_nodes):
            if next_idx in visited:
                continue
            
            # Calculate transition probability
            pheromone = self.pheromone_matrix[current_idx][next_idx] ** self.alpha
            heuristic = self._calculate_heuristic(current_idx, next_idx, current_time) ** self.beta
            
            if heuristic > 0:
                prob = pheromone * heuristic
                probabilities.append(prob)
                candidates.append(next_idx)
        
        if not candidates:
            return None
            
        # Normalize probabilities
        total_prob = sum(probabilities)
        if total_prob == 0:
            return random.choice(candidates)
            
        probabilities = [p / total_prob for p in probabilities]
        
        # Roulette wheel selection
        return np.random.choice(candidates, p=probabilities)

    def _construct_solution(self) -> List[int]:
        """
        Construct a single ant's solution.
        Considers start_location for first POI selection (distance + urgency).
        """
        from geopy.distance import geodesic
        
        current_time = self.constraints.start_time
        
        # Calculate combined score for first POI: urgency + proximity to start
        poi_scores = []
        for idx, poi in enumerate(self.pois):
            # 1. Urgency weight
            urgency = calculate_urgency_weight(
                poi.opening_hours if hasattr(poi, 'opening_hours') else {},
                self.constraints.day_of_week,
                current_time,
                poi.visit_duration
            )
            
            # 2. Distance from start_location (if provided)
            distance_score = 1.0
            if self.start_location and urgency > 0:
                try:
                    dist_km = geodesic(
                        self.start_location, 
                        (poi.latitude, poi.longitude)
                    ).kilometers
                    # Inverse distance: closer = higher score (max 1.0, min ~0.1)
                    distance_score = 1.0 / (1.0 + dist_km * 0.2)
                except:
                    distance_score = 0.5  # Default if geodesic fails
            
            # Combined score: urgency * distance proximity
            # This balances "needs to visit soon" with "is nearby"
            combined_score = urgency * distance_score
            poi_scores.append((idx, combined_score, urgency))
        
        # Sort by combined score (best first)
        poi_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Select first POI with positive urgency
        current_idx = None
        for poi_idx, combined, urgency in poi_scores:
            if urgency > 0:  # Must be visitable
                current_idx = poi_idx
                break
        
        # Fallback: if no POIs are urgently visitable, select by distance only
        if current_idx is None:
            start_candidates = [i for i, p in enumerate(self.pois) 
                               if p.opening_time <= self.constraints.start_time + 60]
            if not start_candidates:
                start_candidates = list(range(self.num_nodes))
            
            # If we have start_location, sort by distance
            if self.start_location and start_candidates:
                try:
                    start_candidates.sort(
                        key=lambda idx: geodesic(
                            self.start_location,
                            (self.pois[idx].latitude, self.pois[idx].longitude)
                        ).kilometers
                    )
                    current_idx = start_candidates[0]  # Closest POI
                except:
                    current_idx = random.choice(start_candidates)
            else:
                current_idx = random.choice(start_candidates)
        
        route = [current_idx]
        visited = {current_idx}
        
        current_time = self.constraints.start_time + self.pois[current_idx].visit_duration
        
        while True:
            next_idx = self._select_next_node(route, visited, current_time)
            
            if next_idx is None:
                break
                
            # Check global constraints (max duration)
            travel_time = 0
            if self.solver.time_matrix is not None:
                travel_time = self.solver.time_matrix[route[-1]][next_idx]
            else:
                travel_time = self.solver._estimate_travel_time(self.pois[route[-1]], self.pois[next_idx])
                
            next_poi = self.pois[next_idx]
            arrival = current_time + travel_time
            
            # FIX: Get actual opening time for the day
            opening_time = next_poi.opening_time
            if hasattr(next_poi, 'opening_hours') and next_poi.opening_hours:
                from app.services.hours_utils import parse_opening_hours
                parsed_open, _ = parse_opening_hours(
                    next_poi.opening_hours, 
                    self.constraints.day_of_week
                )
                if parsed_open is not None:
                    opening_time = parsed_open
            
            # FIX: Check wait time - skip if too long
            if arrival < opening_time:
                wait_time = opening_time - arrival
                if wait_time > self.MAX_WAIT_TIME:
                    continue  # Skip this POI - too much waiting
            
            departure = max(arrival, opening_time) + next_poi.visit_duration
            
            if departure - self.constraints.start_time > self.constraints.max_duration:
                break
                
            route.append(next_idx)
            visited.add(next_idx)
            current_time = departure
            
        return route

    def _update_pheromones(self, solutions: List[Tuple[List[int], float]]):
        """Update pheromone matrix based on solutions"""
        # Evaporation
        self.pheromone_matrix *= (1.0 - self.evaporation_rate)
        
        # Deposit
        for route, fitness in solutions:
            if fitness <= 0:
                continue
                
            deposit = self.q * fitness
            
            for i in range(len(route) - 1):
                u, v = route[i], route[i+1]
                self.pheromone_matrix[u][v] += deposit
                self.pheromone_matrix[v][u] += deposit # Symmetric for undirected graph logic

    def solve(self, verbose: bool = False) -> Tuple[List[int], float]:
        """Main ACO loop"""
        logger.info(f"Starting ACO: {self.iterations} iterations, {self.num_ants} ants")
        
        for iteration in range(self.iterations):
            solutions = []
            
            # Construct solutions for all ants
            for _ in range(self.num_ants):
                route = self._construct_solution()
                fitness = self.solver.calculate_fitness(route)
                solutions.append((route, fitness))
                
                # Update global best
                if fitness > self.best_fitness:
                    self.best_fitness = fitness
                    self.best_solution = route.copy()
                    if verbose:
                        logger.info(f"Iter {iteration}: New best fitness = {self.best_fitness:.2f}")
            
            # Update pheromones
            self._update_pheromones(solutions)
            
            # History
            avg_fitness = np.mean([s[1] for s in solutions])
            self.fitness_history.append({
                "iteration": iteration,
                "best_fitness": max([s[1] for s in solutions]),
                "avg_fitness": avg_fitness
            })
            
        logger.info(f"ACO complete. Best fitness: {self.best_fitness:.2f}")
        return self.best_solution, self.best_fitness
