import unittest
import requests
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://127.0.0.1:5000"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class TestErrorHandling(unittest.TestCase):
    def setUp(self):
        # Check if server is running before tests
        try:
            requests.get(BASE_URL)
        except requests.ConnectionError:
            self.skipTest("Flask server is not running. Please start the server first.")

    def test_invalid_lane_id(self):
        try:
            response = requests.get(f"{BASE_URL}/video_feed/10")
            self.assertEqual(response.status_code, 400)
        except requests.ConnectionError:
            self.fail("Could not connect to the Flask server")

    def test_missing_video_files(self):
        missing_files = []
        for i in range(1, 5):
            video_path = os.path.join(BASE_DIR, "videos", f"Lane_{i}.mp4")
            if not os.path.exists(video_path):
                missing_files.append(f"Lane_{i}.mp4")
        
        self.assertEqual(len(missing_files), 0, 
                        f"Missing video files in {os.path.join(BASE_DIR, 'videos')}: {missing_files}")

    def test_invalid_request(self):
        try:
            response = requests.get(f"{BASE_URL}/invalid_endpoint")
            self.assertEqual(response.status_code, 404)
        except requests.ConnectionError:
            self.fail("Could not connect to the Flask server")

if __name__ == "__main__":
    unittest.main()
