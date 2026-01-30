#!/bin/bash
# AWS EC2 Ubuntu 22.04 deployment script for Atex Calculator

# Exit on any error
set -e

echo "Starting deployment of Atex Calculator on AWS EC2..."

# Set variables
APP_DIR="/var/www/calculadora"
PYTHON_VERSION="3.10"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="calculadora"
DOMAIN="calculadora.atex.la"
NGINX_CONF="/etc/nginx/sites-available/$SERVICE_NAME"
NGINX_ENABLED="/etc/nginx/sites-enabled/$SERVICE_NAME"

echo "Application directory: $APP_DIR"
echo "Python version: $PYTHON_VERSION"
echo "Domain: $DOMAIN"

# Check if running as root for system operations
if [ "$EUID" -ne 0 ]; then
    echo "Please run with sudo for system operations"
    exit 1
fi

# Create application directory if it doesn't exist
if [ ! -d "$APP_DIR" ]; then
    echo "Creating application directory..."
    mkdir -p "$APP_DIR"
    chown ubuntu:ubuntu "$APP_DIR"
fi

# Copy application files (assumes script is run from the project source)
echo "Copying application files..."
cp -r . "$APP_DIR/"
chown -R ubuntu:ubuntu "$APP_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    sudo -u ubuntu python3.$PYTHON_VERSION -m venv "$VENV_DIR"
fi

# Activate virtual environment and install dependencies
echo "Installing Python packages..."
sudo -u ubuntu "$VENV_DIR/bin/pip" install --upgrade pip
sudo -u ubuntu "$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"

# Ensure gunicorn is installed
sudo -u ubuntu "$VENV_DIR/bin/pip" install gunicorn

# Initialize database if needed
if [ -f "$APP_DIR/init_db.py" ]; then
    echo "Initializing database..."
    cd "$APP_DIR"
    sudo -u ubuntu "$VENV_DIR/bin/python" init_db.py
fi

# Create systemd service
echo "Creating systemd service..."
cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=Atex Calculator Flask App
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/gunicorn \\
    --workers 3 \\
    --bind 127.0.0.1:8000 \\
    passenger_wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start service
echo "Starting application service..."
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

# Create nginx configuration
echo "Configuring Nginx..."
cat > "$NGINX_CONF" << EOF
server {
    listen 80;
    server_name $DOMAIN;

    # Serve static files directly
    location /static {
        alias $APP_DIR/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy requests to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
EOF

# Enable nginx site
if [ ! -L "$NGINX_ENABLED" ]; then
    ln -s "$NGINX_CONF" "$NGINX_ENABLED"
fi

# Test nginx configuration
echo "Testing Nginx configuration..."
nginx -t

# Reload nginx
echo "Reloading Nginx..."
systemctl reload nginx

# Check service status
echo "Checking service status..."
systemctl status "$SERVICE_NAME" --no-pager

echo ""
echo "Deployment completed successfully!"
echo "Your application should be available at: http://$DOMAIN"
echo ""
echo "Useful commands:"
echo "  - Check logs: sudo journalctl -u $SERVICE_NAME -f"
echo "  - Restart service: sudo systemctl restart $SERVICE_NAME"
echo "  - Check status: sudo systemctl status $SERVICE_NAME"
echo "  - View nginx logs: sudo tail -f /var/log/nginx/error.log"
