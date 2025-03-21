import numpy as np
import networkx as nx
from dataclasses import dataclass
from typing import List, Dict, Tuple
import random
import time

@dataclass
class Vehicle:
    id: int
    position: Tuple[float, float]
    speed: float
    direction: str  # 'N', 'S', 'E', 'W'
    arrival_time: float
    target_intersection = None
    current_road = None  # Track which road the vehicle is on
    is_emergency: bool = False  # New field for emergency vehicles

    def move(self, delta_time: float):
        """Move the vehicle based on its direction and speed"""
        dx = dy = 0
        if self.direction == 'N':
            dy = -self.speed * delta_time
        elif self.direction == 'S':
            dy = self.speed * delta_time
        elif self.direction == 'E':
            dx = self.speed * delta_time
        elif self.direction == 'W':
            dx = -self.speed * delta_time
        
        # Update position
        self.position = (self.position[0] + dx, self.position[1] + dy)

class Intersection:
    def __init__(self, id: int, position: Tuple[float, float]):
        self.id = id
        self.position = position
        self.signals = {
            'N': 'red',
            'S': 'red',
            'E': 'red',
            'W': 'red'
        }
        self.green_times = {
            'N': 30,
            'S': 30,
            'E': 30,
            'W': 30
        }
        self.approaching_vehicles: Dict[str, List[Vehicle]] = {
            'N': [], 'S': [], 'E': [], 'W': []
        }
        self.connected_intersections = []
        self.last_signal_change = time.time()
        self.current_phase = 0
        self.phases = [
            {'N': 'green', 'S': 'green', 'E': 'red', 'W': 'red'},
            {'N': 'red', 'S': 'red', 'E': 'green', 'W': 'green'}
        ]
        self.emergency_mode = False
        self.emergency_direction = None
        self.emergency_wait_time = 0
        self.emergency_threshold = 3
        self.emergency_priority = False
        self.emergency_priority_direction = None
        self.emergency_green_time = 0.5  # Reduced to 0.5 seconds for quick passage
        self.signal_transition_delay = 0.2  # Reduced to 0.2 seconds for faster response
        self.transition_start_time = 0
        self.is_transitioning = False

    def update_signals(self):
        """Update traffic signals based on timing and emergency vehicles"""
        current_time = time.time()
        phase_duration = 30  
        
        
        emergency_vehicles = []
        for direction in self.approaching_vehicles:
            for vehicle in self.approaching_vehicles[direction]:
                if vehicle.is_emergency:
                    emergency_vehicles.append((direction, vehicle))
        
        if emergency_vehicles:
            # Emergency mode: Set all signals to green briefly
            self.emergency_mode = True
            self.emergency_direction = emergency_vehicles[0][0]
            self.emergency_priority = True
            self.emergency_priority_direction = self.emergency_direction
            
            
            if not self.is_transitioning:
                self.is_transitioning = True
                self.transition_start_time = current_time
               
                self.signals = {d: 'red' for d in ['N', 'S', 'E', 'W']}
                return
            
            
            if current_time - self.transition_start_time >= self.signal_transition_delay:
              
                self.signals = {d: 'green' for d in ['N', 'S', 'E', 'W']}
                self.is_transitioning = False
                self.last_signal_change = current_time
                self.emergency_wait_time = 0
            return
        
       
        if self.emergency_mode:
            if self.emergency_wait_time < self.emergency_green_time:
                self.emergency_wait_time += 0.1 
                self.signals = {d: 'green' for d in ['N', 'S', 'E', 'W']}
                return
            else:
                # Immediately return to normal signals
                self.emergency_mode = False
                self.emergency_direction = None
                self.emergency_wait_time = 0
                self.emergency_priority = False
                self.emergency_priority_direction = None
                self.is_transitioning = False
        
        # Normal signal operation with coordination
        if current_time - self.last_signal_change >= phase_duration:
            self.current_phase = (self.current_phase + 1) % len(self.phases)
            self.last_signal_change = current_time
        
        self.signals = self.phases[self.current_phase].copy()

    def _coordinate_emergency_signals(self):
        """Coordinate signals with connected intersections for emergency vehicles"""
        for connected in self.connected_intersections:
          
            if connected.emergency_mode:
                
                connected.signals = {d: 'green' for d in ['N', 'S', 'E', 'W']}
                connected.emergency_priority = True
                connected.emergency_priority_direction = self.emergency_direction
                connected.last_signal_change = time.time()
                connected.emergency_wait_time = 0

    def is_approaching(self, vehicle: Vehicle) -> bool:
        """Check if vehicle is approaching this intersection"""
        distance = np.sqrt(
            (vehicle.position[0] - self.position[0])**2 +
            (vehicle.position[1] - self.position[1])**2
        )
        return distance < 100  

    def update_approaching_vehicles(self, vehicles: List[Vehicle]):
        """Simulate computer vision detection of approaching vehicles"""
        self.approaching_vehicles = {'N': [], 'S': [], 'E': [], 'W': []}
        for vehicle in vehicles:
            if self.is_approaching(vehicle):
                self.approaching_vehicles[vehicle.direction].append(vehicle)

    def predict_arrivals(self) -> Dict[str, List[float]]:
        """Predict arrival times for approaching vehicles"""
        arrival_times = {}
        for direction in self.approaching_vehicles:
            arrival_times[direction] = [
                v.arrival_time for v in self.approaching_vehicles[direction]
            ]
        return arrival_times

    def _update_vehicles(self, delta_time: float):
        """Update vehicle positions and generate new vehicles"""
       
        self.vehicles = [v for v in self.vehicles if self._is_in_network(v)]
      
        for vehicle in self.vehicles:
            nearest_intersection = self._find_nearest_intersection(vehicle)
            if nearest_intersection:
                vehicle.target_intersection = nearest_intersection
                
                if self._is_at_intersection(vehicle, nearest_intersection):
                   
                    if vehicle.is_emergency:
                        
                        if nearest_intersection.signals[vehicle.direction] == 'green':
                            vehicle.move(delta_time)
                        else:
                       
                            nearest_intersection.emergency_mode = True
                            nearest_intersection.emergency_direction = vehicle.direction
                            nearest_intersection.is_transitioning = True
                            nearest_intersection.transition_start_time = time.time()
                            
                            nearest_intersection.signals = {d: 'red' for d in ['N', 'S', 'E', 'W']}
                            self._stop_at_intersection(vehicle, nearest_intersection)
                    else:
                        
                        if nearest_intersection.signals[vehicle.direction] == 'green':
                       
                            can_proceed = True
                            for other_vehicle in self.vehicles:
                                if other_vehicle != vehicle and other_vehicle.is_emergency and \
                                   self._is_at_intersection(other_vehicle, nearest_intersection):
                                    can_proceed = False
                                    break
                            
                            if can_proceed:
                                vehicle.move(delta_time)
                            else:
                                self._stop_at_intersection(vehicle, nearest_intersection)
                        else:
                            self._stop_at_intersection(vehicle, nearest_intersection)
                else:
                    vehicle.move(delta_time)
            else:
                vehicle.move(delta_time)

class PSO:
    def __init__(self, num_particles: int, num_intersections: int):
        self.num_particles = num_particles
        self.num_intersections = num_intersections
        self.particles = []
        self.best_positions = []
        self.best_scores = []
        self.global_best_position = None
        self.global_best_score = float('inf')
        self.iteration = 0
        self.initialize_particles()

    def initialize_particles(self):
        """Initialize particles with random positions"""
        for _ in range(self.num_particles):
            # Each particle represents green times for each direction at each intersection
            position = []
            for _ in range(self.num_intersections):
                # Random green times for each direction (N, S, E, W)
                position.extend([random.uniform(20, 40) for _ in range(4)])
            self.particles.append(position)
            self.best_positions.append(position.copy())
            self.best_scores.append(float('inf'))

    def update(self, intersections: List[Intersection], vehicles: List[Vehicle]):
        """Update particle positions based on traffic conditions"""
        self.iteration += 1
        
        # traffic density for each intersection
        traffic_densities = self._calculate_traffic_densities(intersections, vehicles)
        
        # particle positions based on traffic conditions
        for i in range(self.num_particles):
            # Calculate score based on traffic conditions
            score = self._calculate_score(self.particles[i], traffic_densities)
            
          
            if score < self.best_scores[i]:
                self.best_scores[i] = score
                self.best_positions[i] = self.particles[i].copy()
            
         
            if score < self.global_best_score:
                self.global_best_score = score
                self.global_best_position = self.particles[i].copy()
            
           
            self._update_particle_position(i)
        
        
        self._apply_solution(intersections)

    def _calculate_traffic_densities(self, intersections: List[Intersection], vehicles: List[Vehicle]) -> List[Dict[str, float]]:
        """Calculate traffic density for each direction at each intersection"""
        densities = []
        for intersection in intersections:
            density = {'N': 0, 'S': 0, 'E': 0, 'W': 0}
            
            # Count vehicles approaching from each direction
            for vehicle in vehicles:
                if self._is_approaching_intersection(vehicle, intersection):
                    density[vehicle.direction] += 1
            
            # Normalize densities
            total = sum(density.values())
            if total > 0:
                for direction in density:
                    density[direction] /= total
            
            densities.append(density)
        return densities

    def _is_approaching_intersection(self, vehicle: Vehicle, intersection: Intersection) -> bool:
        """Check if a vehicle is approaching an intersection"""
        distance = np.sqrt(
            (vehicle.position[0] - intersection.position[0])**2 +
            (vehicle.position[1] - intersection.position[1])**2
        )
        return distance < 100  # Detection radius

    def _calculate_score(self, position: List[float], traffic_densities: List[Dict[str, float]]) -> float:
        """Calculate score based on traffic conditions and signal timings"""
        score = 0
        for i, density in enumerate(traffic_densities):
           
            green_times = position[i*4:(i+1)*4]
            
            # Calculate weighted score based on traffic density and green time
            for direction, d in density.items():
                idx = {'N': 0, 'S': 1, 'E': 2, 'W': 3}[direction]
              
                score += (d - green_times[idx]/120)**2
        
        return score

    def _update_particle_position(self, particle_idx: int):
        """Update particle position using PSO equations"""
        w = 0.7  # Inertia weight
        c1 = 1.5  # Cognitive weight
        c2 = 1.5  # Social weight
        
        for i in range(len(self.particles[particle_idx])):
            # Update velocity
            r1, r2 = random.random(), random.random()
            cognitive_velocity = c1 * r1 * (self.best_positions[particle_idx][i] - self.particles[particle_idx][i])
            social_velocity = c2 * r2 * (self.global_best_position[i] - self.particles[particle_idx][i])
            
            # Update position
            self.particles[particle_idx][i] += cognitive_velocity + social_velocity
            
            # Clamp to valid range (20-40 seconds)
            self.particles[particle_idx][i] = max(20, min(40, self.particles[particle_idx][i]))

    def _apply_solution(self, intersections: List[Intersection]):
        """Apply the best solution to traffic signals"""
        if self.global_best_position is None:
            return
        
        for i, intersection in enumerate(intersections):
            
            green_times = self.global_best_position[i*4:(i+1)*4]
            
         
            for direction, time in zip(['N', 'S', 'E', 'W'], green_times):
                intersection.green_times[direction] = time

class TrafficNetwork:
    def __init__(self, num_intersections: int):
        self.intersections = self._create_intersections(num_intersections)
        self.vehicles = []
        self.pso = PSO(num_particles=20, num_intersections=9)  
        self.max_vehicles = 60  
        self.spawn_probability = 0.15
        self.emergency_spawn_probability = 0.02
        self.last_update_time = time.time()
        self.vehicle_count = 0
        self.emergency_vehicle_count = 0

    def _create_intersections(self, num_intersections: int) -> List[Intersection]:
        """Create a grid of intersections with coordinated signals"""
        intersections = []
        grid_size = 3  
        spacing = 150
        
        # Create intersections in a grid pattern
        for i in range(grid_size):
            for j in range(grid_size):
                intersection = Intersection(
                    id=len(intersections),
                    position=(i * spacing, j * spacing)
                )
                intersections.append(intersection)
        
        # Connect intersections in a grid pattern with coordinated signals
        for i in range(grid_size):
            for j in range(grid_size):
                current_idx = i * grid_size + j
                
                # Connect to right neighbor (horizontal road)
                if j < grid_size - 1:
                    intersections[current_idx].connected_intersections.append(intersections[current_idx + 1])
                    intersections[current_idx + 1].connected_intersections.append(intersections[current_idx])
                
                # Connect to bottom neighbor (vertical road)
                if i < grid_size - 1:
                    intersections[current_idx].connected_intersections.append(intersections[current_idx + grid_size])
                    intersections[current_idx + grid_size].connected_intersections.append(intersections[current_idx])
        
        # Set initial phases for coordination
        for i in range(len(intersections)):
         
            intersections[i].current_phase = (i % 2)
        
        return intersections

    def update(self, delta_time: float):
        """Update the traffic network state"""
        # Update vehicle positions
        self._update_vehicles(delta_time)
        
        # Update traffic signals
        for intersection in self.intersections:
            intersection.update_signals()
        
        # Update PSO optimization
        self.pso.update(self.intersections, self.vehicles)

    def _update_vehicles(self, delta_time: float):
        """Update vehicle positions and generate new vehicles"""
        
        self.vehicles = [v for v in self.vehicles if self._is_in_network(v)]
        
       
        for vehicle in self.vehicles:
            nearest_intersection = self._find_nearest_intersection(vehicle)
            if nearest_intersection:
                vehicle.target_intersection = nearest_intersection
                
                if self._is_at_intersection(vehicle, nearest_intersection):
                    
                    if vehicle.is_emergency:
                        
                        if nearest_intersection.signals[vehicle.direction] == 'green':
                            vehicle.move(delta_time)
                        else:
                          
                            nearest_intersection.emergency_mode = True
                            nearest_intersection.emergency_direction = vehicle.direction
                            nearest_intersection.is_transitioning = True
                            nearest_intersection.transition_start_time = time.time()
                           
                            nearest_intersection.signals = {d: 'red' for d in ['N', 'S', 'E', 'W']}
                            self._stop_at_intersection(vehicle, nearest_intersection)
                    else:
                       
                        if nearest_intersection.signals[vehicle.direction] == 'green':
                          
                            can_proceed = True
                            for other_vehicle in self.vehicles:
                                if other_vehicle != vehicle and other_vehicle.is_emergency and \
                                   self._is_at_intersection(other_vehicle, nearest_intersection):
                                    can_proceed = False
                                    break
                            
                            if can_proceed:
                                vehicle.move(delta_time)
                            else:
                                self._stop_at_intersection(vehicle, nearest_intersection)
                        else:
                            self._stop_at_intersection(vehicle, nearest_intersection)
                else:
                    vehicle.move(delta_time)
            else:
                vehicle.move(delta_time)
        
        
        if len(self.vehicles) < self.max_vehicles and random.random() < self.spawn_probability:
       
            if random.random() < 0.4:  
                direction = 'S'
            else:
                direction = random.choice(['N', 'E', 'W'])
            
            position = self._get_spawn_position(direction)
            new_vehicle = Vehicle(
                id=self.vehicle_count,
                position=position,
                speed=random.uniform(30, 50),
                direction=direction,
                arrival_time=time.time(),
                is_emergency=False
            )
            self.vehicle_count += 1
            self.vehicles.append(new_vehicle)
        
     
        if random.random() < self.emergency_spawn_probability:
            direction = random.choice(['N', 'S', 'E', 'W'])
            position = self._get_spawn_position(direction)
            emergency_vehicle = Vehicle(
                id=f"E{self.emergency_vehicle_count}",
                position=position,
                speed=random.uniform(50, 70), 
                direction=direction,
                arrival_time=time.time(),
                is_emergency=True
            )
            self.emergency_vehicle_count += 1
            self.vehicles.append(emergency_vehicle)

    def _is_at_intersection(self, vehicle: Vehicle, intersection: Intersection) -> bool:
        """Check if a vehicle is at an intersection"""
        distance = np.sqrt(
            (vehicle.position[0] - intersection.position[0])**2 +
            (vehicle.position[1] - intersection.position[1])**2
        )
        return distance < 10  

    def _stop_at_intersection(self, vehicle: Vehicle, intersection: Intersection):
        """Stop a vehicle at an intersection"""
   
        vehicle.position = intersection.position

    def _find_nearest_intersection(self, vehicle: Vehicle) -> Intersection:
        """Find the nearest intersection to a vehicle"""
        nearest = None
        min_distance = float('inf')
        
        for intersection in self.intersections:
            distance = np.sqrt(
                (vehicle.position[0] - intersection.position[0])**2 +
                (vehicle.position[1] - intersection.position[1])**2
            )
            if distance < min_distance:
                min_distance = distance
                nearest = intersection
        
        return nearest

    def _is_in_network(self, vehicle: Vehicle) -> bool:
        """Check if vehicle is still within the network bounds"""
        x, y = vehicle.position
        max_x = max(i.position[0] for i in self.intersections)
        max_y = max(i.position[1] for i in self.intersections)
        return -100 <= x <= max_x + 100 and -100 <= y <= max_y + 100  # Increased bounds

    def _get_spawn_position(self, direction: str) -> Tuple[float, float]:
        """Get spawn position for new vehicles based on direction"""
        grid_size = 3
        spacing = 150
        
        if direction == 'N':
            # Spawn at bottom of vertical roads
            x = random.choice([i * spacing for i in range(grid_size)])
            return (x, spacing * (grid_size - 1) + 50)
        elif direction == 'S':
            # Spawn at top of vertical roads
            x = random.choice([i * spacing for i in range(grid_size)])
            return (x, -50)
        elif direction == 'E':
            # Spawn at left of horizontal roads
            y = random.choice([i * spacing for i in range(grid_size)])
            return (-50, y)
        else:  # 'W'
            # Spawn at right of horizontal roads
            y = random.choice([i * spacing for i in range(grid_size)])
            return (spacing * (grid_size - 1) + 50, y)

    def _find_next_intersection(self, vehicle: Vehicle) -> Intersection:
        """Find the next intersection in the vehicle's path"""
        current_intersection = self._find_nearest_intersection(vehicle)
        if not current_intersection:
            return None
            
        # Find the next intersection based on vehicle direction
        next_intersection = None
        min_distance = float('inf')
        
        for intersection in current_intersection.connected_intersections:
            # Check if the intersection is in the vehicle's direction
            if self._is_in_direction(vehicle, intersection):
                distance = np.sqrt(
                    (intersection.position[0] - vehicle.position[0])**2 +
                    (intersection.position[1] - vehicle.position[1])**2
                )
                if distance < min_distance:
                    min_distance = distance
                    next_intersection = intersection
        
        return next_intersection

    def _is_in_direction(self, vehicle: Vehicle, intersection: Intersection) -> bool:
        """Check if an intersection is in the vehicle's direction"""
        dx = intersection.position[0] - vehicle.position[0]
        dy = intersection.position[1] - vehicle.position[1]
        
        if vehicle.direction == 'N':
            return dy < 0
        elif vehicle.direction == 'S':
            return dy > 0
        elif vehicle.direction == 'E':
            return dx > 0
        else:  # 'W'
            return dx < 0

# Example usage
if __name__ == "__main__":
    # Create a network with 9 intersections (3x3 grid)
    network = TrafficNetwork(num_intersections=9)
    
    # Simulation loop
    for _ in range(100):  # Run for 100 timesteps
        network.update(0.1)
        
        # Print some statistics
        total_vehicles = sum(len(intersection.approaching_vehicles['N'] +
                               intersection.approaching_vehicles['S'] +
                               intersection.approaching_vehicles['E'] +
                               intersection.approaching_vehicles['W'])
                           for intersection in network.intersections)
        print(f"Total vehicles in network: {total_vehicles}") 