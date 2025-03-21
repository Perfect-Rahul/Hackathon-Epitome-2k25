import pygame
import numpy as np
from traffic_network import TrafficNetwork, Vehicle, Intersection
import time
import cv2
import os

class Visualizer:
    def __init__(self, network: TrafficNetwork):
        pygame.init()
        self.network = network
        self.width = 1200
        self.height = 800
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Adaptive Traffic Network Simulation")
        
        
        self.recording = False
        self.video_writer = None
        self.recorded_frames = []
        
       
       
        self.BACKGROUND = (240, 240, 240)
        self.ROAD_COLOR = (80, 80, 80)  
        self.INTERSECTION_COLOR = (200, 200, 200)
        self.SIGNAL_RED = (255, 0, 0) 
        self.SIGNAL_GREEN = (0, 255, 0) 
        self.SIGNAL_OFF = (100, 100, 100) 
        
        
        self.VEHICLE_COLORS = {
            'N': (255, 0, 0),      # Bright Red for North
            'S': (0, 0, 255),      # Bright Blue for South
            'E': (0, 255, 0),      # Bright Green for East
            'W': (255, 165, 0)     # Bright Orange for West
        }
        
        
        self.VEHICLE_SHADOWS = {
            'N': (180, 0, 0),      
            'S': (0, 0, 180),    
            'E': (0, 180, 0),     
            'W': (180, 120, 0)    
        }
        
        self.TEXT_COLOR = (0, 0, 0)
        self.DIRECTION_COLOR = (255, 255, 255)  
        
        self.scale = 1.3  
        self.center_x = self.width // 2 + 200 
        self.center_y = self.height // 2
        self.offset_x = -300  
        self.offset_y = -250  

        self.last_update_time = time.time()

    def start_recording(self):
        """Start recording the simulation"""
        self.recording = True
        self.recorded_frames = []
        print("Recording started...")

    def stop_recording(self):
        """Stop recording and save the video"""
        if not self.recording:
            return

        self.recording = False
        print("Recording stopped. Saving video...")

       
        if not os.path.exists('output'):
            os.makedirs('output')

       
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = f'output/traffic_simulation_{timestamp}.mp4'
        
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, 30.0, (self.width, self.height))
        
       
        for frame in self.recorded_frames:
            out.write(frame)
        
        out.release()
        print(f"Video saved to: {output_path}")

    def draw_traffic_light(self, pos, color, size=20):  # Increased size
        """Draw a single traffic light with glow effect"""
        # Draw outer glow
        pygame.draw.circle(self.screen, color, pos, size + 8)
        # Draw main light
        pygame.draw.circle(self.screen, (255, 255, 255), pos, size + 4)
        pygame.draw.circle(self.screen, color, pos, size)
        # Add shine effect
        shine_pos = (pos[0] - size//3, pos[1] - size//3)
        pygame.draw.circle(self.screen, (255, 255, 255), shine_pos, 4)

    def draw_intersection(self, intersection: Intersection):
        """Draw an intersection with its traffic signals"""
        x = int(intersection.position[0] * self.scale) + self.center_x + self.offset_x
        y = int(intersection.position[1] * self.scale) + self.center_y + self.offset_y
        
        
        pygame.draw.rect(self.screen, (180, 180, 180), (x-22, y-22, 44, 44))
        pygame.draw.rect(self.screen, self.INTERSECTION_COLOR, (x-20, y-20, 40, 40))
        
        
        signal_positions = {
            'N': {'pos': (x, y-30), 'box': pygame.Rect(x-25, y-45, 50, 25)},  # Top signal
            'S': {'pos': (x, y+30), 'box': pygame.Rect(x-25, y+20, 50, 25)},  # Bottom signal
            'E': {'pos': (x+30, y), 'box': pygame.Rect(x+20, y-25, 25, 50)},  # Right signal
            'W': {'pos': (x-30, y), 'box': pygame.Rect(x-45, y-25, 25, 50)}   # Left signal
        }
        
        
        for direction, signal_info in signal_positions.items():
            pos = signal_info['pos']
            box = signal_info['box']
            
            
            pygame.draw.rect(self.screen, (100, 100, 100), box)  # Shadow
            pygame.draw.rect(self.screen, (200, 200, 200), box.inflate(-4, -4))  # Signal box
            
          
            if intersection.signals[direction] == 'green':
                self.draw_traffic_light(pos, self.SIGNAL_GREEN)
            else:  # red
                self.draw_traffic_light(pos, self.SIGNAL_RED)
            
          
            font = pygame.font.Font(None, 24)
            text = font.render(direction, True, (0, 0, 0))
            text_rect = text.get_rect(center=(pos[0], pos[1] + (15 if direction in ['N', 'S'] else 0)))
            self.screen.blit(text, text_rect)
        
       
        road_width = 25  
       
        pygame.draw.rect(self.screen, self.ROAD_COLOR, (x-road_width//2, y-120, road_width, 240))
        
        pygame.draw.rect(self.screen, self.ROAD_COLOR, (x-120, y-road_width//2, 240, road_width))
        
       
        pygame.draw.rect(self.screen, self.INTERSECTION_COLOR, (x-road_width//2, y-road_width//2, road_width, road_width))

    def draw_vehicle(self, vehicle: Vehicle):
        """Draw a vehicle with direction indicator"""
        x = int(vehicle.position[0] * self.scale) + self.center_x + self.offset_x
        y = int(vehicle.position[1] * self.scale) + self.center_y + self.offset_y
        
        
        if vehicle.is_emergency:
            vehicle_color = (255, 0, 0)  # Bright red for emergency vehicles
            shadow_color = (180, 0, 0)   # Darker red for shadow
            size = 10  # Slightly larger for emergency vehicles
        else:
            vehicle_color = self.VEHICLE_COLORS[vehicle.direction]
            shadow_color = self.VEHICLE_SHADOWS[vehicle.direction]
            size = 8
        
       
        pygame.draw.circle(self.screen, shadow_color, (x+2, y+2), size)
        pygame.draw.circle(self.screen, vehicle_color, (x, y), size)
        
       
        direction_offsets = {
            'N': (0, -12),
            'S': (0, 12),
            'E': (12, 0),
            'W': (-12, 0)
        }
        
        dx, dy = direction_offsets[vehicle.direction]
        pygame.draw.line(self.screen, vehicle_color, 
                        (x, y), (x + dx, y + dy), 4)
        
        if vehicle.direction in ['N', 'S']:
            pygame.draw.line(self.screen, vehicle_color,
                           (x - 5, y + dy), (x + 5, y + dy), 4)
        else:
            pygame.draw.line(self.screen, vehicle_color,
                           (x + dx, y - 5), (x + dx, y + 5), 4)
        
        # Add emergency indicator if it's an emergency vehicle
        if vehicle.is_emergency:
            # Draw flashing lights
            if int(time.time() * 10) % 2 == 0:
                pygame.draw.circle(self.screen, (255, 255, 255), (x, y), size + 2, 2)

    def draw_connections(self):
        """Draw connections between intersections with improved visibility"""
        for intersection in self.network.intersections:
            x1 = int(intersection.position[0] * self.scale) + self.center_x + self.offset_x
            y1 = int(intersection.position[1] * self.scale) + self.center_y + self.offset_y
            
            for connected in intersection.connected_intersections:
                x2 = int(connected.position[0] * self.scale) + self.center_x + self.offset_x
                y2 = int(connected.position[1] * self.scale) + self.center_y + self.offset_y
                
                is_horizontal = abs(y2 - y1) < abs(x2 - x1)
                
             
                if is_horizontal:
                    pygame.draw.rect(self.screen, (100, 100, 100), 
                                   (min(x1, x2), y1-12, abs(x2-x1), 24))
                else:
                    pygame.draw.rect(self.screen, (100, 100, 100), 
                                   (x1-12, min(y1, y2), 24, abs(y2-y1)))
                
              
                if is_horizontal:
                    pygame.draw.rect(self.screen, self.ROAD_COLOR, 
                                   (min(x1, x2), y1-10, abs(x2-x1), 20))
                else:
                    pygame.draw.rect(self.screen, self.ROAD_COLOR, 
                                   (x1-10, min(y1, y2), 20, abs(y2-y1)))
                
               
                if is_horizontal:
                    for x in range(int(min(x1, x2)), int(max(x1, x2)), 15):
                        pygame.draw.rect(self.screen, (255, 255, 255), 
                                       (x, y1-2, 8, 4))
                else:
                    for y in range(int(min(y1, y2)), int(max(y1, y2)), 15):
                        pygame.draw.rect(self.screen, (255, 255, 255), 
                                       (x1-2, y, 4, 8))

    def draw_stats(self):
        """Draw statistics with improved visibility"""
        font = pygame.font.Font(None, 36)  
        
      
        total_vehicles = len(self.network.vehicles)
        vehicles_per_direction = {
            'N': sum(1 for v in self.network.vehicles if v.direction == 'N' and not v.is_emergency),
            'S': sum(1 for v in self.network.vehicles if v.direction == 'S' and not v.is_emergency),
            'E': sum(1 for v in self.network.vehicles if v.direction == 'E' and not v.is_emergency),
            'W': sum(1 for v in self.network.vehicles if v.direction == 'W' and not v.is_emergency)
        }
        emergency_vehicles = sum(1 for v in self.network.vehicles if v.is_emergency)
        
       
        panel_rect = pygame.Rect(10, 10, 300, 350)  
        pygame.draw.rect(self.screen, (255, 255, 255), panel_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), panel_rect, 2)
        
      
        text_vehicles = font.render(f"Total Vehicles: {total_vehicles}", True, self.TEXT_COLOR)
        self.screen.blit(text_vehicles, (20, 20))
        
     
        text_emergency = font.render(f"Emergency Vehicles: {emergency_vehicles}", True, (255, 0, 0))
        self.screen.blit(text_emergency, (20, 50))
        
        
        legend_font = pygame.font.Font(None, 28)  
        y_pos = 90
        for direction, count in vehicles_per_direction.items():
          
            color = self.VEHICLE_COLORS[direction]
            shadow_color = self.VEHICLE_SHADOWS[direction]
            pygame.draw.circle(self.screen, shadow_color, (32, y_pos + 10), 8)
            pygame.draw.circle(self.screen, color, (30, y_pos + 10), 8)
           
            text = legend_font.render(f"{direction}: {count}", True, self.TEXT_COLOR)
            self.screen.blit(text, (50, y_pos))
            y_pos += 30  
        
        # PSO iteration count and optimization status
        text_iterations = font.render(f"Iteration: {self.network.pso.iteration}", True, self.TEXT_COLOR)
        self.screen.blit(text_iterations, (20, y_pos + 10))
        
        # adaptive timing information
        y_pos += 40
        text_adaptive = font.render("Adaptive Timing Active", True, (0, 180, 0))
        self.screen.blit(text_adaptive, (20, y_pos))
        
        # green times for each intersection
        y_pos += 40
        for i, intersection in enumerate(self.network.intersections):
            text = legend_font.render(f"Intersection {i+1} Green Times:", True, self.TEXT_COLOR)
            self.screen.blit(text, (20, y_pos))
            y_pos += 25
            for direction, time in intersection.green_times.items():
                color = self.VEHICLE_COLORS[direction]
                text = legend_font.render(f"{direction}: {time:.1f}s", True, color)
                self.screen.blit(text, (40, y_pos))
                y_pos += 25

    def update(self):
        """Update visualization"""
        current_time = time.time()
        delta_time = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Update network state
        self.network.update(delta_time)
        
       
        self.screen.fill(self.BACKGROUND)
        self.draw_connections()
      
        for intersection in self.network.intersections:
            self.draw_intersection(intersection)
        
        
        for vehicle in self.network.vehicles:
            self.draw_vehicle(vehicle)
            
        self.draw_stats()
        pygame.display.flip()

        
        if self.recording:
            
            view = pygame.surfarray.array3d(self.screen)
            view = view.transpose([1, 0, 2])
            frame = cv2.cvtColor(view, cv2.COLOR_RGB2BGR)
            self.recorded_frames.append(frame)

if __name__ == "__main__":
    
    network = TrafficNetwork(num_intersections=4)
    
 
    vis = Visualizer(network)
    
    # Main loop
    running = True
    recording_started = False
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Press 'R' to start/stop recording
                    if not recording_started:
                        vis.start_recording()
                        recording_started = True
                    else:
                        vis.stop_recording()
                        recording_started = False
        
        
        vis.update()
        
       
        pygame.time.Clock().tick(60)
    
    # Stop recording if active
    if recording_started:
        vis.stop_recording()
    
    pygame.quit() 