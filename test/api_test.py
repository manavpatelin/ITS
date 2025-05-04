import unittest
import requests
import subprocess
import time
import os
import signal
import sys
import socket

BASE_URL = "http://127.0.0.1:5000"

def is_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Start the Flask server before running tests"""
        # Check if the server is already running
        if is_port_in_use(5000):
            print("Flask server is already running on port 5000")
            cls.external_server = True
            return
            
        cls.external_server = False
        try:
            # Start the Flask app in a separate process
            print("Starting Flask server for testing...")
            # Fix the path construction by using os.path.join properly
            app_path = os.path.join('d:\\', 'main_timer', 'app.py')
            
            # Make sure the app.py exists
            if not os.path.exists(app_path):
                raise FileNotFoundError(f"Could not find app.py at {app_path}")
                
            # Start with shell=True to avoid console window
            cls.flask_process = subprocess.Popen(
                f'"{sys.executable}" "{app_path}"',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for the server to start (with timeout)
            start_time = time.time()
            while not is_port_in_use(5000):
                if time.time() - start_time > 10:  # 10 second timeout
                    raise TimeoutError("Flask server failed to start within 10 seconds")
                time.sleep(0.5)
                
            print("Flask server started for testing")
            # Additional wait to ensure routes are registered
            time.sleep(2)
        except Exception as e:
            print(f"Failed to start Flask server: {e}")
            if hasattr(cls, 'flask_process'):
                cls.flask_process.terminate()
            sys.exit(1)
    
    @classmethod
    def tearDownClass(cls):
        """Stop the Flask server after running tests"""
        if not cls.external_server and hasattr(cls, 'flask_process'):
            # Terminate the Flask process
            cls.flask_process.terminate()
            try:
                cls.flask_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate gracefully
                cls.flask_process.kill()
            print("Flask server stopped")
    
    def test_vehicle_counts_api(self):
        try:
            response = requests.get(f"{BASE_URL}/vehicle_counts")
            self.assertEqual(response.status_code, 200)
            self.assertIsInstance(response.json(), dict)
        except requests.exceptions.ConnectionError:
            self.fail("Could not connect to the Flask server. Make sure it's running.")

    def test_traffic_states_api(self):
        try:
            response = requests.get(f"{BASE_URL}/traffic_states")
            self.assertEqual(response.status_code, 200)
            self.assertIsInstance(response.json(), dict)
        except requests.exceptions.ConnectionError:
            self.fail("Could not connect to the Flask server. Make sure it's running.")

    def test_ambulance_status_api(self):
        try:
            response = requests.get(f"{BASE_URL}/ambulance_status")
            self.assertEqual(response.status_code, 200)
            self.assertIsInstance(response.json(), dict)
        except requests.exceptions.ConnectionError:
            self.fail("Could not connect to the Flask server. Make sure it's running.")

if __name__ == "__main__":
    unittest.main()
