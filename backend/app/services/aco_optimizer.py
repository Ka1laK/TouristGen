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
        q: float = 100.0     # Pheromone deposit factor
    ):
        self.pois = pois
        self.constraints = constraints
        self.solver = TOPTWSolver(pois, constraints)
        
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
        
    def set_distance_matrix(self, time_matrix: np.ndarray):
        """Set the travel time matrix for the solver"""
        self.solver.set_distance_matrix(time_matrix)
        
    def _calculate_heuristic(self, current_idx: int, next_idx: int, current_time: int) -> float:
        """
        Calculate heuristic value (eta) for moving from current to next node.
        Uses centralized weights from optimization_weights.py for consistency with fitness calculation.
        """
        from app.services.optimization_weights import WEIGHTS
        
        next_poi = self.pois[next_idx]
        
        # 1. Distance/Time Heuristic (lower travel time = better)
        travel_time = 0
        if self.solver.time_matrix is not None:
            travel_time = self.solver.time_matrix[current_idx][next_idx]
        else:
            travel_time = self.solver._estimate_travel_time(self.pois[current_idx], next_poi)
            
        # Avoid division by zero
        dist_score = 1.0 / (travel_time + 1.0)
        
        # 2. Popularity Heuristic
        pop_score = next_poi.popularity / 100.0
        
        # 3. Time Window Heuristic (urgency)
        arrival_time = current_time + travel_time
        
        # Check feasibility first
        if arrival_time >= next_poi.closing_time:
            return 0.0
            
        # Urgency: how close are we to closing time?
        time_left = next_poi.closing_time - arrival_time
        urgency_score = 1.0 / (time_left + 1.0)
        
        # 4. Rating Heuristic (new - for consistency with fitness)
        rating_score = next_poi.rating / 5.0 if next_poi.rating else 0.5
        
        # Combine heuristics using CENTRALIZED WEIGHTS
        return (
            (dist_score * WEIGHTS.distance_weight) +
            (pop_score * WEIGHTS.popularity_weight) +
            (urgency_score * WEIGHTS.urgency_weight) +
            (rating_score * WEIGHTS.rating_weight)
        )

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
        NUEVO: Prioriza POIs con cierre próximo para visitarlos primero.
        """
        current_time = self.constraints.start_time
        
        # NUEVO: Calcular urgencias para decisión inicial
        urgencies = []
        for idx, poi in enumerate(self.pois):
            urgency = calculate_urgency_weight(
                poi.opening_hours if hasattr(poi, 'opening_hours') else {},
                self.constraints.day_of_week,
                current_time,
                poi.visit_duration
            )
            urgencies.append((idx, urgency))
        
        # Ordenar por urgencia descendente (más urgentes primero)
        urgent_pois = sorted(urgencies, key=lambda x: x[1], reverse=True)
        
        # Comenzar con POI más urgente que sea visitable
        current_idx = None
        for poi_idx, urgency in urgent_pois:
            if urgency > 0:  # Es visitable
                current_idx = poi_idx
                break
        
        # Fallback: si no hay POIs urgentes, elegir aleatorio
        if current_idx is None:
            start_candidates = [i for i, p in enumerate(self.pois) 
                               if p.opening_time <= self.constraints.start_time + 60]
            if not start_candidates:
                start_candidates = list(range(self.num_nodes))
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
            departure = max(arrival, next_poi.opening_time) + next_poi.visit_duration
            
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
