#!/bin/bash

# Quick deployment script for ATex Calculator to AWS Lightsail
# Usage: ./quick-deploy.sh your-lightsail-ip

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <lightsail-ip>"
    echo "Example: $0 123.45.67.89"
    exit 1
fi

LIGHTSAIL_IP=$1
APP_NAME="atex-calc-web"
REMOTE_USER="ubuntu"
REMOTE_DIR="/var/www/atex-calc-web"

echo "Quick deploying ATex Calculator to $LIGHTSAIL_IP..."

# Find the latest deployment zip
ZIP_FILE=$(ls -1t ${APP_NAME}-deploy-*.zip | head -n1)

if [ ! -f "$ZIP_FILE" ]; then
    echo "Deployment zip not found. Running deploy-to-lightsail.sh first..."
    ./deploy-to-lightsail.sh
    ZIP_FILE=$(ls -1t ${APP_NAME}-deploy-*.zip | head -n1)
fi

echo "Using deployment file: $ZIP_FILE"

# Upload and deploy
scp "$ZIP_FILE" "$REMOTE_USER@$LIGHTSAIL_IP:/tmp/"

ssh "$REMOTE_USER@$LIGHTSAIL_IP" << EOF
    # Stop the service
    sudo systemctl stop atex-calc || true
    
    # Backup current deployment
    sudo cp -r $REMOTE_DIR $REMOTE_DIR.backup.\$(date +%Y%m%d-%H%M%S) || true
    
    # Remove old deployment and extract new
    sudo rm -rf $REMOTE_DIR
    sudo mkdir -p $REMOTE_DIR
    sudo unzip /tmp/$ZIP_FILE -d /var/www/
    sudo mv /var/www/$APP_NAME/* $REMOTE_DIR/
    sudo rmdir /var/www/$APP_NAME
    
    # Set permissions
    sudo chown -R ubuntu:www-data $REMOTE_DIR
    
    # Create virtual environment and install dependencies
    cd $REMOTE_DIR
    python3.12 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt
    
    # Create necessary directories
    mkdir -p uploads database
    sudo chown -R ubuntu:www-data uploads database
    
    # Initialize database if needed
    if [ ! -f database/atex_calculations.db ]; then
        python init_db.py
    fi
    
    # Install/update services
    sudo cp atex-calc.service /etc/systemd/system/atex-calc.service
    sudo systemctl daemon-reload
    sudo systemctl enable atex-calc
    
    sudo cp nginx-atex-calc.conf /etc/nginx/sites-available/atex-calc
    sudo ln -sf /etc/nginx/sites-available/atex-calc /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t
    
    # Start services
    sudo systemctl start atex-calc
    sudo systemctl reload nginx
    
    # Clean up
    rm /tmp/$ZIP_FILE
    
    echo "Deployment completed successfully!"
    echo "Application should be running at: http://$LIGHTSAIL_IP"
EOF

echo "Deployment finished!"
