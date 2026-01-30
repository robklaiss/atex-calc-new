import sys
import os

# Get the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Import the Flask app instance
# This works with both Passenger and Gunicorn
from app import app as application

# For Gunicorn, the application variable should be available at module level
# No additional configuration needed
