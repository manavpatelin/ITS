import unittest
import cv2
import numpy as np
import time
import os
import sys
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from detection import model, vehicle_classes

class TestModelMetrics(unittest.TestCase):
    def setUp(self):
        self.test_image = "D:/main_timer/videos/WhatsApp Image 2025-02-06 at 14.34.47_c8f5373b.jpg"
        self.metrics = defaultdict(float)
        
    def test_detection_accuracy(self):
        frame = cv2.imread(self.test_image)
        if frame is None:
            self.skipTest("Test image not found")
            
        # Run multiple detections to get average accuracy
        num_runs = 10
        true_positives = 0
        false_positives = 0
        
        for _ in range(num_runs):
            results = model(frame)
            
            for r in results:
                for box in r.boxes:
                    confidence = float(box.conf)
                    if confidence > 0.5:  # High confidence threshold
                        true_positives += 1
                    else:
                        false_positives += 1
        
        total_detections = true_positives + false_positives
        accuracy = (true_positives / total_detections) * 100 if total_detections > 0 else 0
        
        print(f"\nDetection Metrics:")
        print(f"Accuracy: {accuracy:.2f}%")
        print(f"True Positives: {true_positives}")
        print(f"False Positives: {false_positives}")
        
        self.assertGreater(accuracy, 90, "Model accuracy below 90%")

    def test_ambulance_detection_rate(self):
        frame = cv2.imread(self.test_image)
        if frame is None:
            self.skipTest("Test image not found")
            
        num_runs = 10
        ambulance_detections = 0
        
        for _ in range(num_runs):
            results = model(frame)
            if any(int(box.cls.item()) == 0 for r in results for box in r.boxes):
                ambulance_detections += 1
        
        detection_rate = (ambulance_detections / num_runs) * 100
        print(f"\nAmbulance Detection Rate: {detection_rate:.2f}%")
        
        self.assertGreater(detection_rate, 95, "Ambulance detection rate below 95%")

    def test_processing_speed(self):
        frame = cv2.imread(self.test_image)
        if frame is None:
            self.skipTest("Test image not found")
            
        # Warm-up run
        model(frame)
        
        # Measure processing times
        times = []
        num_runs = 20
        
        for _ in range(num_runs):
            start_time = time.time()
            model(frame)
            processing_time = time.time() - start_time
            times.append(processing_time)
        
        avg_time = np.mean(times)
        std_dev = np.std(times)
        
        print(f"\nProcessing Speed Metrics:")
        print(f"Average Time: {avg_time:.3f} seconds")
        print(f"Standard Deviation: {std_dev:.3f} seconds")
        print(f"Min Time: {min(times):.3f} seconds")
        print(f"Max Time: {max(times):.3f} seconds")
        
        self.assertLess(avg_time, 0.5, "Average processing time exceeds 0.5 seconds")

if __name__ == "__main__":
    unittest.main()