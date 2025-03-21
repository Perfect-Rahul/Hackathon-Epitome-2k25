import cv2
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from ultralytics import YOLO

# Configuration
NUM_SIGNALS = 4  # N, S, E, W directions
NUM_PARTICLES = 20
MAX_ITERATIONS = 50
GREEN_RANGE = (10, 90)  # Green time range in seconds
W, C1, C2 = 0.9, 2.0, 2.0  # PSO parameters: inertia, cognitive, social
MAX_VELOCITY = 5  # Maximum velocity for PSO particles

# Load YOLOv8 model
model = YOLO('yolov8n.pt')  # Nano model for speed

# PSO class for optimizing green times based on vehicle counts
class PSO:
    def __init__(self, vehicle_counts):
        self.vehicle_counts = vehicle_counts  # [N, S, E, W]
        self.particles = np.random.uniform(GREEN_RANGE[0], GREEN_RANGE[1], (NUM_PARTICLES, NUM_SIGNALS))
        self.velocities = np.random.uniform(-MAX_VELOCITY, MAX_VELOCITY, (NUM_PARTICLES, NUM_SIGNALS))
        self.p_best = self.particles.copy()
        self.g_best = self.particles[0].copy()
        self.p_best_cost = np.array([float('inf')] * NUM_PARTICLES)
        self.g_best_cost = float('inf')
        self.w = W

    def fitness(self, particle):
        """Calculate cost: minimize variance of (green_time / vehicles) ratios."""
        ratios = [particle[i] / (self.vehicle_counts[i] + 1e-6) for i in range(NUM_SIGNALS)]  # Avoid division by zero
        variance = np.var(ratios)
        return variance

    def update(self):
        """Update particle positions and velocities."""
        for i in range(NUM_PARTICLES):
            cost = self.fitness(self.particles[i])
            if cost < self.p_best_cost[i]:
                self.p_best[i] = self.particles[i].copy()
                self.p_best_cost[i] = cost
            if cost < self.g_best_cost:
                self.g_best = self.particles[i].copy()
                self.g_best_cost = cost

            r1, r2 = np.random.random(), np.random.random()
            cognitive = C1 * r1 * (self.p_best[i] - self.particles[i])
            social = C2 * r2 * (self.g_best - self.particles[i])
            self.velocities[i] = self.w * self.velocities[i] + cognitive + social
            self.velocities[i] = np.clip(self.velocities[i], -MAX_VELOCITY, MAX_VELOCITY)
            self.particles[i] += self.velocities[i]
            self.particles[i] = np.clip(self.particles[i], GREEN_RANGE[0], GREEN_RANGE[1])
        self.w = max(0.4, self.w - 0.5 / MAX_ITERATIONS)  # Decrease inertia

# Vehicle detection function using YOLOv8
def detect_vehicles(image):
    if image is None:
        print("Error: Image not loaded.")
        return 0, None
    
    # Vehicle classes from COCO dataset
    vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck (excluding person)

    
    results = model(image)
    detected_vehicles = [box for box in results[0].boxes if int(box.cls) in vehicle_classes]
    
  
    count = len(detected_vehicles)
    
    
    for box in detected_vehicles:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        label = model.names[int(box.cls)]
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    return count, image

# Traffic Simulation Class for Video
class TrafficSimulation:
    def __init__(self, video_paths):
        """Initialize with video paths and set up VideoCapture objects."""
        self.caps = [cv2.VideoCapture(path) for path in video_paths]
        self.vehicle_counts = [0] * NUM_SIGNALS
        self.signal_times = [30] * NUM_SIGNALS 
        self.vehicle_queues = [0] * NUM_SIGNALS

      
        for i, cap in enumerate(self.caps):
            if not cap.isOpened():
                print(f"Error: Could not open video {video_paths[i]}.")
                self.caps[i] = None

    def read_frames(self):
        """Read frames from all video sources."""
        frames = []
        for cap in self.caps:
            if cap is None:
                return None
            ret, frame = cap.read()
            if not ret:
                return None
            frames.append(frame)
        return frames

    def update_vehicle_counts(self, frames):
        """Update vehicle counts based on current frames."""
        for i, frame in enumerate(frames):
            count, _ = detect_vehicles(frame)
            self.vehicle_counts[i] = count

    def optimize_green_times(self):
        """Optimize green times using PSO based on current vehicle counts."""
        self.pso = PSO(self.vehicle_counts)
        for iteration in range(MAX_ITERATIONS):
            self.pso.update()
        self.signal_times = self.pso.g_best.copy()

    def simulate_flow(self):
        """Simulate traffic flow based on green times."""
        for i in range(NUM_SIGNALS):
            green_time = self.signal_times[i]
            flow = min(self.vehicle_queues[i], green_time * 0.5)  
            self.vehicle_queues[i] = max(0, self.vehicle_queues[i] - flow + self.vehicle_counts[i] * 0.1)

    def run(self):
        """Run the traffic simulation with video input."""
        fig = plt.figure(figsize=(15, 10))
        
        axes = [fig.add_subplot(2, 3, i + 1) for i in range(4)] + [fig.add_subplot(2, 3, (5, 6))]
        for ax in axes[:4]:
            ax.axis('off')
            ax.set_title(['North', 'South', 'East', 'West'][axes.index(ax)])

        
        img_objects = [axes[i].imshow(np.zeros((480, 640, 3), dtype=np.uint8)) for i in range(4)]

        def update(frame_idx):
            """Update function for animation."""
           
            frames = self.read_frames()
            if frames is None:
                anim.event_source.stop()
                return

            
            if frame_idx % 30 == 0:
                self.update_vehicle_counts(frames)
                self.optimize_green_times()
                print(f"Frame {frame_idx}: Vehicle counts: {self.vehicle_counts}, Green times: {self.signal_times}")

            # Simulate traffic flow
            self.simulate_flow()

            for i, frame in enumerate(frames):
                _, annotated = detect_vehicles(frame)
                img_objects[i].set_data(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB))

           
            axes[4].clear()
            x = np.arange(NUM_SIGNALS)
            axes[4].bar(x, self.signal_times, label='Green Time (s)', color='green')
            axes[4].set_title(f"Traffic Simulation (Frame {frame_idx})")
            axes[4].set_xlabel("Directions")
            axes[4].set_ylabel("Green Time (s)")
            axes[4].set_xticks(x)
            axes[4].set_xticklabels(['North', 'South', 'East', 'West'])
            axes[4].legend()
            axes[4].set_ylim(0, max(self.signal_times) + 10)
            for i, green in enumerate(self.signal_times):
                axes[4].text(i, green + 1, f'{int(green)}', ha='center')

        anim = FuncAnimation(fig, update, frames=range(1000), interval=33)
        plt.tight_layout()
        plt.show()

        
        for cap in self.caps:
            if cap is not None:
                cap.release()

        return anim


if __name__ == "__main__":
  
    video_paths = [
        "North.mp4","South.mp4","East.mp4","West.mp4"
    ]
    sim = TrafficSimulation(video_paths)
    animation = sim.run()