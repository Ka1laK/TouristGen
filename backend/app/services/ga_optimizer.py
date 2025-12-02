import random
import numpy as np
from typing import List, Tuple, Optional
from .toptw_solver import TOPTWSolver, POINode, TOPTWConstraints
import logging

logger = logging.getLogger(__name__)


class GeneticAlgorithm:
    """
    Genetic Algorithm for solving TOPTW
    
    Uses:
    - Tournament selection
    - Ordered crossover (OX)
    - Multiple mutation operators (swap, insert, shuffle)
    - Elitism
    """
    
    def __init__(
        self,
        pois: List[POINode],
        constraints: TOPTWConstraints,
        population_size: int = 100,
        generations: int = 200,
        mutation_rate: float = 0.15,
        crossover_rate: float = 0.8,
        elite_ratio: float = 0.1,
        tournament_size: int = 5
    ):
        self.pois = pois
        self.constraints = constraints
        self.solver = TOPTWSolver(pois, constraints)
        
        # GA parameters
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_ratio = elite_ratio
        self.tournament_size = tournament_size
        
        # State
        self.population = []
        self.best_solution = None
        self.best_fitness = 0.0
        self.fitness_history = []
        
    def set_distance_matrix(self, time_matrix: np.ndarray):
        """Set the travel time matrix for the solver"""
        self.solver.set_distance_matrix(time_matrix)
    
    def initialize_population(self):
        """Create initial population with diverse routes"""
        self.population = []
        num_pois = len(self.pois)
        
        if num_pois == 0:
            logger.warning("No POIs available for route generation")
            return
        
        for _ in range(self.population_size):
            # Random route length - ensure we don't request more POIs than available
            max_route_length = min(12, num_pois)
            min_route_length = min(3, num_pois)  # Can't require 3 if we only have 1-2 POIs
            
            if max_route_length < min_route_length:
                route_length = max_route_length
            else:
                route_length = random.randint(min_route_length, max_route_length)
            
            # Create random route
            route = random.sample(range(num_pois), min(route_length, num_pois))
            self.population.append(route)
        
        # Add some greedy-initialized routes for diversity
        greedy_routes = self._generate_greedy_routes(min(10, self.population_size // 10))
        self.population.extend(greedy_routes)
        
        # Trim to population size
        self.population = self.population[:self.population_size]
    
    def _generate_greedy_routes(self, count: int) -> List[List[int]]:
        """Generate routes using greedy heuristics"""
        routes = []
        
        for _ in range(count):
            route = []
            available = set(range(len(self.pois)))
            current_time = self.constraints.start_time
            total_time = 0
            
            # Start with a random POI
            if available:
                current_idx = random.choice(list(available))
                route.append(current_idx)
                available.remove(current_idx)
                
                poi = self.pois[current_idx]
                current_time = max(current_time, poi.opening_time) + poi.visit_duration
                total_time += poi.visit_duration
            
            # Greedily add POIs
            while available and total_time < self.constraints.max_duration:
                # Find best next POI (high popularity, close distance)
                best_score = -float('inf')
                best_idx = None
                
                for idx in available:
                    poi = self.pois[idx]
                    
                    # Estimate travel time
                    travel_time = self.solver._estimate_travel_time(
                        self.pois[route[-1]], poi
                    )
                    
                    # Check if feasible
                    arrival_time = current_time + travel_time
                    if arrival_time >= poi.closing_time:
                        continue
                    
                    # Score based on popularity and distance
                    score = poi.popularity - (travel_time * 0.5)
                    
                    if score > best_score:
                        best_score = score
                        best_idx = idx
                
                if best_idx is None:
                    break
                
                route.append(best_idx)
                available.remove(best_idx)
                
                poi = self.pois[best_idx]
                travel_time = self.solver._estimate_travel_time(
                    self.pois[route[-2]], poi
                )
                current_time += travel_time
                current_time = max(current_time, poi.opening_time)
                current_time += poi.visit_duration
                total_time += travel_time + poi.visit_duration
            
            if len(route) >= 3:
                routes.append(route)
        
        return routes
    
    def tournament_selection(self) -> List[int]:
        """Select parent using tournament selection"""
        tournament = random.sample(self.population, min(self.tournament_size, len(self.population)))
        fitnesses = [self.solver.calculate_fitness(route) for route in tournament]
        winner_idx = np.argmax(fitnesses)
        return tournament[winner_idx].copy()
    
    def ordered_crossover(self, parent1: List[int], parent2: List[int]) -> Tuple[List[int], List[int]]:
        """
        Ordered Crossover (OX) operator
        Preserves relative order of cities
        """
        if len(parent1) < 2 or len(parent2) < 2:
            return parent1.copy(), parent2.copy()
        
        # Use shorter parent length
        size = min(len(parent1), len(parent2))
        
        # Select two crossover points
        cx_point1, cx_point2 = sorted(random.sample(range(size), 2))
        
        # Create offspring
        child1 = self._create_ox_child(parent1[:size], parent2[:size], cx_point1, cx_point2)
        child2 = self._create_ox_child(parent2[:size], parent1[:size], cx_point1, cx_point2)
        
        return child1, child2
    
    def _create_ox_child(self, parent1: List[int], parent2: List[int], 
                         start: int, end: int) -> List[int]:
        """Helper for OX crossover"""
        size = len(parent1)
        child = [-1] * size
        
        # Copy segment from parent1
        child[start:end] = parent1[start:end]
        
        # Fill remaining positions from parent2
        parent2_filtered = [gene for gene in parent2 if gene not in child]
        
        # Fill positions
        child_idx = end
        for gene in parent2_filtered:
            if child_idx >= size:
                child_idx = 0
            
            while child[child_idx] != -1:
                child_idx += 1
                if child_idx >= size:
                    child_idx = 0
            
            child[child_idx] = gene
        
        return child
    
    def mutate(self, route: List[int]) -> List[int]:
        """
        Apply mutation operators
        - Swap: exchange two positions
        - Insert: move one gene to another position
        - Shuffle: shuffle a subsequence
        - Add/Remove: add or remove a POI
        """
        if random.random() > self.mutation_rate:
            return route
        
        mutated = route.copy()
        
        if len(mutated) < 2:
            # Try to add a POI
            all_pois = set(range(len(self.pois)))
            available = list(all_pois - set(mutated))
            if available:
                mutated.append(random.choice(available))
            return mutated
        
        mutation_type = random.choice(["swap", "insert", "shuffle", "add", "remove"])
        
        if mutation_type == "swap":
            i, j = random.sample(range(len(mutated)), 2)
            mutated[i], mutated[j] = mutated[j], mutated[i]
        
        elif mutation_type == "insert":
            i, j = random.sample(range(len(mutated)), 2)
            gene = mutated.pop(i)
            mutated.insert(j, gene)
        
        elif mutation_type == "shuffle":
            if len(mutated) >= 4:
                i, j = sorted(random.sample(range(len(mutated)), 2))
                chunk = mutated[i:j]
                random.shuffle(chunk)
                mutated[i:j] = chunk
        
        elif mutation_type == "add":
            # Add a new POI
            all_pois = set(range(len(self.pois)))
            available = list(all_pois - set(mutated))
            if available and len(mutated) < 15:  # Limit route length
                new_poi = random.choice(available)
                insert_pos = random.randint(0, len(mutated))
                mutated.insert(insert_pos, new_poi)
        
        elif mutation_type == "remove":
            # Remove a POI
            if len(mutated) > 3:  # Keep minimum 3 POIs
                remove_idx = random.randint(0, len(mutated) - 1)
                mutated.pop(remove_idx)
        
        return mutated
    
    def evolve(self, verbose: bool = False) -> Tuple[List[int], float]:
        """
        Main evolution loop
        
        Returns:
            (best_route, best_fitness)
        """
        logger.info(f"Starting GA evolution: {self.generations} generations, population {self.population_size}")
        
        # Initialize population
        self.initialize_population()
        
        if not self.population:
            logger.error("Failed to initialize population")
            return [], 0.0
        
        # Evolution loop
        for generation in range(self.generations):
            # Evaluate fitness for all individuals
            fitnesses = [self.solver.calculate_fitness(route) for route in self.population]
            
            # Track best solution
            max_fitness_idx = np.argmax(fitnesses)
            gen_best_fitness = fitnesses[max_fitness_idx]
            
            if gen_best_fitness > self.best_fitness:
                self.best_fitness = gen_best_fitness
                self.best_solution = self.population[max_fitness_idx].copy()
                
                if verbose:
                    logger.info(f"Gen {generation}: New best fitness = {self.best_fitness:.2f}")
            
            # Store fitness history
            self.fitness_history.append({
                "generation": generation,
                "best_fitness": gen_best_fitness,
                "avg_fitness": np.mean(fitnesses),
                "worst_fitness": np.min(fitnesses)
            })
            
            # Create new generation
            new_population = []
            
            # Elitism: keep best individuals
            elite_count = max(1, int(self.elite_ratio * self.population_size))
            elite_indices = np.argsort(fitnesses)[-elite_count:]
            
            for idx in elite_indices:
                new_population.append(self.population[idx].copy())
            
            # Generate offspring
            while len(new_population) < self.population_size:
                # Selection
                parent1 = self.tournament_selection()
                parent2 = self.tournament_selection()
                
                # Crossover
                if random.random() < self.crossover_rate:
                    child1, child2 = self.ordered_crossover(parent1, parent2)
                else:
                    child1, child2 = parent1.copy(), parent2.copy()
                
                # Mutation
                child1 = self.mutate(child1)
                child2 = self.mutate(child2)
                
                new_population.append(child1)
                if len(new_population) < self.population_size:
                    new_population.append(child2)
            
            # Update population
            self.population = new_population[:self.population_size]
            
            # Early stopping if no improvement for many generations
            if generation > 50 and len(self.fitness_history) > 50:
                recent_best = [h["best_fitness"] for h in self.fitness_history[-50:]]
                if max(recent_best) == min(recent_best):
                    logger.info(f"Early stopping at generation {generation} (no improvement)")
                    break
        
        logger.info(f"Evolution complete. Best fitness: {self.best_fitness:.2f}")
        
        return self.best_solution, self.best_fitness
    
    def get_statistics(self) -> dict:
        """Get evolution statistics"""
        return {
            "best_fitness": self.best_fitness,
            "generations_run": len(self.fitness_history),
            "fitness_history": self.fitness_history,
            "final_population_size": len(self.population)
        }
