import sys
import os

# Add the application directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the Flask application
from app import app as application

# Configure for production
os.environ['FLASK_ENV'] = 'production'

# Set the secret key (use environment variable in production)
if not os.environ.get('SECRET_KEY'):
    app.secret_key = 'change-this-secret-key-in-production'

# Disable debug mode
app.debug = False
