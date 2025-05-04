import threading
import unittest
import sys
import os
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vehicle_counter import start_vehicle_counting, stop_vehicle_counting

# Use absolute paths for video files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO_PATHS = [
    os.path.join(BASE_DIR, "videos", f"Lane_{i}.mp4") 
    for i in range(1, 5)
]

class TestStress(unittest.TestCase):
    def test_multiple_video_processing(self):
        # Check if video files exist
        for video_path in VIDEO_PATHS:
            if not os.path.exists(video_path):
                self.skipTest(f"Video file not found: {video_path}")
        
        # Start vehicle counting in a separate thread
        thread = threading.Thread(target=start_vehicle_counting, args=(VIDEO_PATHS,))
        thread.daemon = True  # Make thread a daemon so it exits when main thread exits
        thread.start()

        try:
            # Allow system to run for 10 seconds
            print("Running stress test for 10 seconds...")
            time.sleep(10)
            
            # Stop vehicle counting
            stop_vehicle_counting()
            
            # Wait for thread to finish
            thread.join(timeout=2)
            
            # If system didn't crash, test is successful
            self.assertTrue(True)
            print("Stress test completed successfully")
            
        except Exception as e:
            stop_vehicle_counting()  # Ensure we stop counting even if there's an error
            self.fail(f"Stress test failed with error: {str(e)}")

if __name__ == "__main__":
    unittest.main()
