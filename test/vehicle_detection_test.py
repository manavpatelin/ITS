import unittest
import cv2
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now import from the main_timer package
from detection import model, vehicle_classes

class TestVehicleDetection(unittest.TestCase):
    def test_vehicle_detection(self):
        frame = cv2.imread("D:/main_timer/videos/WhatsApp Image 2025-02-06 at 14.34.47_c8f5373b.jpg")
        if frame is None:
            self.fail("Could not load test image. Please check the path.")
            
        results = model(frame)

        detected_classes = set()
        for r in results:
            for box in r.boxes:
                class_id = int(box.cls.item())
                detected_classes.add(class_id)

        # Check if at least one vehicle is detected
        self.assertTrue(any(cls in vehicle_classes for cls in detected_classes))
        print(f"Detected vehicle classes: {[vehicle_classes[cls] for cls in detected_classes if cls in vehicle_classes]}")

    def test_ambulance_detection(self):
        # Update path to use absolute path
        frame = cv2.imread("D:/main_timer/videos/WhatsApp Image 2025-02-06 at 14.34.47_c8f5373b.jpg")  # Make sure this file exists
        if frame is None:
            self.skipTest("Ambulance test image not found. Test skipped.")
            
        results = model(frame)

        ambulance_detected = any(int(box.cls.item()) == 0 for r in results for box in r.boxes)
        self.assertTrue(ambulance_detected, "No ambulance detected in the test image")

if __name__ == "__main__":
    unittest.main()
