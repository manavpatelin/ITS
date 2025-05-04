# Fix the import to use absolute imports instead of relative imports
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use absolute imports
from detection import model
from vehicle_counter import start_vehicle_counting
