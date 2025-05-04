import time
import cv2
import unittest
import sys
import os
import numpy as np
from collections import defaultdict
import requests

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from detection import model

BASE_URL = "http://127.0.0.1:5000"

class TestPerformance(unittest.TestCase):
    def test_frame_processing_time(self):
        frame = cv2.imread("D:/main_timer/videos/WhatsApp Image 2025-02-06 at 14.34.47_c8f5373b.jpg")
        if frame is None:
            self.skipTest("Test image not found")
        
        # Warm-up run to initialize CUDA
        model(frame)
        
        # Measure average over multiple runs
        num_runs = 5
        processing_times = []
        detection_counts = []
        
        # Expected number of objects in the test image
        expected_objects = 8  # 1 person, 2 cars, 2 motorcycles, 2 trucks
        
        for _ in range(num_runs):
            start_time = time.time()
            results = model(frame)
            processing_time = time.time() - start_time
            processing_times.append(processing_time)
            
            # Count detections with confidence > 0.5
            detections = sum(len([box for box in r.boxes if float(box.conf) > 0.5]) for r in results)
            detection_counts.append(detections)
        
        avg_processing_time = np.mean(processing_times)
        avg_detections = np.mean(detection_counts)
        
        # Calculate accuracy based on expected objects
        accuracy = min((avg_detections / expected_objects) * 100, 100)
        
        print(f"\nPerformance Metrics:")
        print(f"Average Processing Time: {avg_processing_time:.4f} sec")
        print(f"Detection Accuracy: {accuracy:.2f}%")
        print(f"Average Detections per Frame: {avg_detections:.1f}")
        print(f"Expected Objects: {expected_objects}")
        print(f"Processing Time Range: {min(processing_times):.4f} - {max(processing_times):.4f} sec")
        
        # Assertions
        self.assertLess(avg_processing_time, 0.5, "Processing time exceeds 500ms")
        self.assertGreaterEqual(accuracy, 70, "Detection accuracy below 70%")
        self.assertGreater(avg_detections, 0, "No objects detected in test image")

    def test_api_response_time(self):
        """Test API endpoint response times"""
        endpoints = ['/vehicle_counts', '/traffic_states', '/ambulance_status']
        response_times = defaultdict(list)
        
        try:
            for _ in range(10):  # Test each endpoint 10 times
                for endpoint in endpoints:
                    start_time = time.time()
                    response = requests.get(f"{BASE_URL}{endpoint}")
                    response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                    response_times[endpoint].append(response_time)
                    
                    # Also check response validity
                    self.assertEqual(response.status_code, 200)
                    self.assertIsInstance(response.json(), dict)
            
            print("\nAPI Response Time Metrics:")
            for endpoint, times in response_times.items():
                avg_time = np.mean(times)
                print(f"{endpoint}: {avg_time:.2f}ms average")
                self.assertLess(avg_time, 100, f"Response time for {endpoint} exceeds 100ms")
                
        except requests.ConnectionError:
            self.skipTest("Flask server is not running. Please start the server first.")

if __name__ == "__main__":
    unittest.main()
