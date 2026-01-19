#!/bin/bash
# HostGator deployment script for Atex Calculator

# Exit on any error
set -e

echo "Starting deployment of Atex Calculator..."

# Set variables
APP_DIR="/home/$USER/public_html/atex-calc-web"
PYTHON_VERSION="3.9"
VENV_DIR="$APP_DIR/venv"

echo "Application directory: $APP_DIR"
echo "Python version: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    /opt/cpanel/ea-python39/bin/python3.9 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing Python packages..."
pip install -r "$APP_DIR/requirements.txt"

# Initialize database
echo "Initializing database..."
cd "$APP_DIR"
python init_db.py

# Set correct permissions
echo "Setting permissions..."
chmod 755 "$APP_DIR"
chmod -R 755 "$APP_DIR/app"
chmod -R 755 "$APP_DIR/database"
chmod -R 755 "$APP_DIR/uploads"
chmod 644 "$APP_DIR/passenger_wsgi.py"
chmod 644 "$APP_DIR/.htaccess"

# Restart Passenger application
echo "Restarting application..."
mkdir -p "$APP_DIR/tmp"
touch "$APP_DIR/tmp/restart.txt"

echo "Deployment completed successfully!"
echo "Your application should be available at your domain."
echo ""
echo "Important notes:"
echo "1. Update the 'username' in .htaccess with your actual cPanel username"
echo "2. Set up a cron job to restart the application periodically if needed"
echo "3. Monitor application logs in $APP_DIR/logs/passenger.log"
