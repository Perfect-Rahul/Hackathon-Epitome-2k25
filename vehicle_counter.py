import cv2
import numpy as np
from ultralytics import YOLO
import time

def process_video():
    
    model = YOLO('yolov8n.pt')
    
    
    cap = cv2.VideoCapture('traffic.mp4')
    
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    
    output_path = 'output/traffic_counted.mp4'
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Initialize counters
    total_vehicles = 0
    frame_count = 0
    
    # Process each frame
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_count += 1
        
        
        results = model(frame, classes=[2, 3, 5, 7])  # Only detect vehicles (car, motorcycle, bus, truck)
        
        # Count vehicles in current frame
        vehicles_in_frame = len(results[0].boxes)
        total_vehicles += vehicles_in_frame
        
        # Draw bounding boxes and count
        for result in results:
            boxes = result.boxes
            for box in boxes:
               
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
          
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
               
                conf = float(box.conf[0])
                cv2.putText(frame, f'{conf:.2f}', (x1, y1-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Add vehicle count to frame
        cv2.putText(frame, f'Vehicles in frame: {vehicles_in_frame}', (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f'Total vehicles: {total_vehicles}', (20, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f'Average: {total_vehicles/frame_count:.1f}', (20, 120),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
     
        out.write(frame)
        
        # Display progress
        if frame_count % 30 == 0:
            print(f'Processed {frame_count} frames...')
    

    # Release resources
    cap.release()
    out.release()
    print(f'Video processing complete. Output saved to: {output_path}')
    print(f'Total frames processed: {frame_count}')
    print(f'Total vehicles detected: {total_vehicles}')
    print(f'Average vehicles per frame: {total_vehicles/frame_count:.1f}')



if __name__ == "__main__":
    # Create output directory if it doesn't exist
    import os
    if not os.path.exists('output'):
        os.makedirs('output')
    
    
    process_video() 