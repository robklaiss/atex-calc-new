#!/bin/bash

# Deployment script for ATex Calculator to AWS Lightsail
# This script prepares and deploys the application

set -e

# Configuration
REMOTE_USER="ubuntu"
REMOTE_HOST="your-lightsail-ip"  # Replace with your Lightsail IP
REMOTE_DIR="/var/www/atex-calc-web"
LOCAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="atex-calc-web"

echo "Starting deployment process for ATex Calculator..."

# Step 1: Clean and prepare the deployment package
echo "Step 1: Preparing deployment package..."

# Remove old deployment directory if it exists
rm -rf "$LOCAL_DIR/$APP_NAME"

# Create deployment directory
mkdir -p "$LOCAL_DIR/$APP_NAME"

# Copy application files
echo "Copying application files..."
rsync -av --progress \
    --exclude '.git*' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude 'venv' \
    --exclude 'uploads/*' \
    --exclude 'database/*.db' \
    --exclude '.DS_Store' \
    --exclude 'deploy-aws' \
    --exclude 'deploy-package' \
    "../atex-calc-web/" "$LOCAL_DIR/$APP_NAME/"

# Copy deployment-specific files
echo "Adding deployment-specific files..."
cp "$LOCAL_DIR/atex-calc.service" "$LOCAL_DIR/$APP_NAME/"
cp "$LOCAL_DIR/nginx-atex-calc.conf" "$LOCAL_DIR/$APP_NAME/"

# Create deployment zip
echo "Creating deployment archive..."
cd "$LOCAL_DIR"
zip -r "${APP_NAME}-deploy-$(date +%Y%m%d-%H%M%S).zip" "$APP_NAME/"

# Step 2: Upload to Lightsail
if [ "$REMOTE_HOST" != "your-lightsail-ip" ]; then
    echo "Step 2: Uploading to Lightsail at $REMOTE_HOST..."
    
    # Create backup of current deployment
    ssh "$REMOTE_USER@$REMOTE_HOST" "sudo cp -r $REMOTE_DIR $REMOTE_DIR.backup.$(date +%Y%m%d-%H%M%S) || true"
    
    # Upload the new deployment
    scp -r "$LOCAL_DIR/$APP_NAME" "$REMOTE_USER@$REMOTE_HOST:/tmp/"
    
    # Step 3: Deploy on remote server
    echo "Step 3: Deploying on remote server..."
    ssh "$REMOTE_USER@$REMOTE_HOST" << EOF
        # Stop the service
        sudo systemctl stop atex-calc || true
        
        # Remove old deployment
        sudo rm -rf $REMOTE_DIR
        
        # Move new deployment
        sudo mv /tmp/$APP_NAME $REMOTE_DIR
        
        # Set permissions
        sudo chown -R ubuntu:www-data $REMOTE_DIR
        
        # Create necessary directories
        mkdir -p $REMOTE_DIR/uploads
        mkdir -p $REMOTE_DIR/database
        sudo chown -R ubuntu:www-data $REMOTE_DIR/uploads $REMOTE_DIR/database
        
        # Create virtual environment
        cd $REMOTE_DIR
        python3.12 -m venv venv
        source venv/bin/activate
        
        # Install dependencies
        pip install --upgrade pip setuptools wheel
        pip install -r requirements.txt
        
        # Initialize database if it doesn't exist
        if [ ! -f database/atex_calculations.db ]; then
            python init_db.py
        fi
        
        # Install systemd service
        sudo cp atex-calc.service /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable atex-calc
        
        # Install nginx configuration
        sudo cp nginx-atex-calc.conf /etc/nginx/sites-available/atex-calc
        sudo ln -sf /etc/nginx/sites-available/atex-calc /etc/nginx/sites-enabled/
        sudo rm -f /etc/nginx/sites-enabled/default
        
        # Test nginx configuration
        sudo nginx -t
        
        # Start services
        sudo systemctl start atex-calc
        sudo systemctl reload nginx
        
        echo "Deployment completed successfully!"
        echo "Application is running at: http://$(curl -s http://checkip.amazonaws.com)"
EOF
else
    echo ""
    echo "Deployment package created at: $LOCAL_DIR/${APP_NAME}-deploy-*.zip"
    echo ""
    echo "To deploy manually:"
    echo "1. Copy the zip file to your Lightsail instance"
    echo "2. Extract it to /var/www/atex-calc-web"
    echo "3. Run the installation script: sudo ./install_lightsail.sh"
    echo ""
    echo "Or update the REMOTE_HOST variable in this script and run again."
fi

echo "Deployment process completed!"
