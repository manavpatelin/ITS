from threading import Thread, Lock
import cv2
from detection import model, vehicle_classes
import time
import random

class VehicleCounter:
    def __init__(self):
        self.counts = {}
        self.ambulance_present = {}
        self.lock = Lock()
        self.running = True
        self.detection_interval = 3
        self.last_detection_time = {}
        # Add vehicle type tracking
        self.vehicle_type_counts = {
            "Cars": 0,
            "Trucks": 0,
            "Motorcycles": 0,
            "Buses": 0,
            "Emergency": 0
        }

    def start_counting(self, video_paths):
        self.threads = []
        for lane_id, video_path in enumerate(video_paths, 1):
            self.last_detection_time[lane_id] = 0
            self.ambulance_present[str(lane_id)] = False
            self.counts[str(lane_id)] = 0  # Initialize counts
            thread = Thread(target=self._count_vehicles, args=(lane_id, video_path))
            thread.daemon = True
            thread.start()
            self.threads.append(thread)

    def _count_vehicles(self, lane_id, video_path):
        cap = cv2.VideoCapture(video_path)
        reset_time = time.time()
        
        while self.running:
            current_time = time.time()
            
            # Reset vehicle type counts every hour to prevent overflow
            if current_time - reset_time >= 3600:  # 1 hour
                with self.lock:
                    for vehicle_type in self.vehicle_type_counts:
                        self.vehicle_type_counts[vehicle_type] = 0
                reset_time = current_time
                
            if current_time - self.last_detection_time.get(lane_id, 0) >= self.detection_interval:
                ret, frame = cap.read()
                if not ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                
                ambulance_detected = False
                results = model(frame)
                vehicle_count = 0
                
                # Track vehicle types
                vehicle_types_detected = {
                    "Cars": 0,
                    "Trucks": 0,
                    "Motorcycles": 0,
                    "Buses": 0,
                    "Emergency": 0
                }

                for r in results:
                    for box in r.boxes:
                        class_id = int(box.cls.item())
                        if class_id in vehicle_classes:
                            vehicle_count += 1
                            
                            # Map class_id to vehicle type
                            if class_id == 0:  # ambulance
                                ambulance_detected = True
                                vehicle_types_detected["Emergency"] += 1
                            elif class_id == 2:  # car
                                vehicle_types_detected["Cars"] += 1
                            elif class_id == 3:  # motorbike
                                vehicle_types_detected["Motorcycles"] += 1
                            elif class_id == 5:  # bus
                                vehicle_types_detected["Buses"] += 1
                            elif class_id == 7:  # truck
                                vehicle_types_detected["Trucks"] += 1

                with self.lock:
                    self.counts[str(lane_id)] = vehicle_count
                    self.ambulance_present[str(lane_id)] = ambulance_detected
                    
                    # Update vehicle type counts
                    for vehicle_type, count in vehicle_types_detected.items():
                        if count > 0:
                            self.vehicle_type_counts[vehicle_type] += count

                self.last_detection_time[lane_id] = current_time
                
            time.sleep(0.1)
        cap.release()

    def get_counts(self):
        with self.lock:
            return dict(self.counts)

    def get_ambulance_status(self):
        with self.lock:
            return dict(self.ambulance_present)
            
    def get_vehicle_type_counts(self):
        with self.lock:
            return dict(self.vehicle_type_counts)

    def stop(self):
        self.running = False
        for thread in self.threads:
            thread.join()

vehicle_counter = VehicleCounter()

def start_vehicle_counting(video_paths):
    vehicle_counter.start_counting(video_paths)

def get_vehicle_counts():
    return vehicle_counter.get_counts()

def get_ambulance_status():
    return vehicle_counter.get_ambulance_status()
    
def get_vehicle_type_counts():
    return vehicle_counter.get_vehicle_type_counts()

def stop_vehicle_counting():
    vehicle_counter.stop()