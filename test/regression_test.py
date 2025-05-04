import unittest
import sys
import os
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vehicle_counter import (
    get_vehicle_counts, 
    get_ambulance_status, 
    start_vehicle_counting, 
    stop_vehicle_counting
)

class TestRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Initialize vehicle counting before running tests"""
        # Start vehicle counting with test videos
        video_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "videos")
        video_paths = [os.path.join(video_dir, f"Lane_{i}.mp4") for i in range(1, 5)]
        
        # Check if videos exist
        for path in video_paths:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Test video not found: {path}")
        
        # Start counting
        start_vehicle_counting(video_paths)
        # Wait for initial counts
        time.sleep(2)

    @classmethod
    def tearDownClass(cls):
        """Clean up after tests"""
        stop_vehicle_counting()

    def test_no_negative_vehicle_counts(self):
        counts = get_vehicle_counts()
        self.assertIsNotNone(counts, "Vehicle counts should not be None")
        self.assertIsInstance(counts, dict, "Vehicle counts should be a dictionary")
        self.assertTrue(all(count >= 0 for count in counts.values()),
                       f"Found negative counts: {counts}")

    def test_ambulance_status_format(self):
        status = get_ambulance_status()
        self.assertIsNotNone(status, "Ambulance status should not be None")
        self.assertIsInstance(status, dict, "Ambulance status should be a dictionary")
        self.assertTrue(all(isinstance(v, bool) for v in status.values()),
                       f"Invalid status values: {status}")

    def test_vehicle_count_keys(self):
        counts = get_vehicle_counts()
        # Update expected keys to match the actual implementation
        expected_keys = {'1', '2', '3', '4'}  # Lane numbers
        self.assertEqual(set(counts.keys()), expected_keys,
                        f"Missing or extra lane numbers: {set(counts.keys())}")

if __name__ == "__main__":
    unittest.main()
