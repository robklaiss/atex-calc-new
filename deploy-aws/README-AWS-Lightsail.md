# ATex Calculator - AWS Lightsail Deployment Guide

This directory contains everything needed to deploy the ATex Calculator on AWS Lightsail.

## Quick Deploy (Recommended)

### Prerequisites
- AWS Lightsail instance with Ubuntu 22.04
- Domain name pointed to your Lightsail IP (optional)
- SSH access to the Lightsail instance

### Option 1: Automated Deployment Script

1. **Update the deployment script**:
   ```bash
   cd deploy-aws
   nano deploy-to-lightsail.sh
   # Replace "your-lightsail-ip" with your actual Lightsail IP
   ```

2. **Make the script executable**:
   ```bash
   chmod +x deploy-to-lightsail.sh
   ```

3. **Run the deployment**:
   ```bash
   ./deploy-to-lightsail.sh
   ```

The script will:
- Prepare the deployment package
- Upload it to your Lightsail instance
- Install all dependencies
- Configure and start the services

### Option 2: Manual Deployment

1. **Create deployment package**:
   ```bash
   ./deploy-to-lightsail.sh
   # This creates a zip file in deploy-aws/
   ```

2. **Upload to Lightsail**:
   ```bash
   scp atex-calc-web-deploy-*.zip ubuntu@your-lightsail-ip:/tmp/
   ```

3. **SSH into your Lightsail instance**:
   ```bash
   ssh ubuntu@your-lightsail-ip
   ```

4. **Extract and install**:
   ```bash
   cd /tmp
   unzip atex-calc-web-deploy-*.zip
   sudo mv atex-calc-web /var/www/
   cd /var/www/atex-calc-web
   sudo ./install_lightsail.sh
   ```

## Manual Setup (If you prefer step-by-step)

### 1. Initial Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.12 python3.12-venv python3.12-dev python3-pip \
    build-essential libfreetype6-dev libjpeg-dev zlib1g-dev libpng-dev \
    sqlite3 nginx git

# Create app directory
sudo mkdir -p /var/www/atex-calc-web
sudo chown ubuntu:www-data /var/www/atex-calc-web
```

### 2. Deploy Application

```bash
# Copy application files (from your local machine)
scp -r ../atex-calc-web/* ubuntu@your-lightsail-ip:/var/www/atex-calc-web/

# On the server
cd /var/www/atex-calc-web

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 3. Initialize Database

```bash
# Create directories
mkdir -p uploads database
sudo chown -R ubuntu:www-data uploads database

# Initialize database
python init_db.py
```

### 4. Configure Services

**Systemd Service** (`/etc/systemd/system/atex-calc.service`):
```ini
[Unit]
Description=Gunicorn service for Atex Calculadora
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/var/www/atex-calc-web
Environment="PATH=/var/www/atex-calc-web/venv/bin"
ExecStart=/var/www/atex-calc-web/venv/bin/gunicorn \
  --workers 3 \
  --bind 127.0.0.1:8000 \
  passenger_wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

**Nginx Configuration** (`/etc/nginx/sites-available/atex-calc`):
```nginx
server {
    server_name calculadora.atex.la;
    
    client_max_body_size 50M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static {
        alias /var/www/atex-calc-web/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 5. Start Services

```bash
# Enable and start the application service
sudo systemctl daemon-reload
sudo systemctl enable atex-calc
sudo systemctl start atex-calc

# Configure Nginx
sudo ln -sf /etc/nginx/sites-available/atex-calc /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

## Security Considerations

1. **Update the secret key**:
   - Create a `.env` file in `/var/www/atex-calc-web/`
   - Add: `SECRET_KEY=your-random-secret-key-here`

2. **Configure firewall**:
   ```bash
   sudo ufw allow 'Nginx Full'
   sudo ufw allow ssh
   sudo ufw enable
   ```

3. **Set up SSL (recommended)**:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d calculadora.atex.la
   ```

## Monitoring and Maintenance

### Check Service Status
```bash
# Application status
sudo systemctl status atex-calc

# Nginx status
sudo systemctl status nginx

# View logs
sudo journalctl -u atex-calc -f
```

### Update Application
```bash
# Stop service
sudo systemctl stop atex-calc

# Update files
cd /var/www/atex-calc-web
git pull origin main  # if using git
# or upload new files

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl start atex-calc
```

### Database Backup
```bash
# Create backup script
cat > /home/ubuntu/backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/ubuntu/backups"
DATE=$(date +%Y%m%d-%H%M%S)
mkdir -p $BACKUP_DIR
cp /var/www/atex-calc-web/database/atex_calculations.db $BACKUP_DIR/atex_calculations_$DATE.db
# Keep only last 7 days
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
EOF

chmod +x /home/ubuntu/backup-db.sh

# Add to crontab for daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * /home/ubuntu/backup-db.sh") | crontab -
```

## Troubleshooting

### Common Issues

1. **502 Bad Gateway**: Check if Gunicorn is running
   ```bash
   sudo systemctl status atex-calc
   sudo journalctl -u atex-calc -n 50
   ```

2. **Import Errors**: Ensure all dependencies are installed
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Permission Issues**: Check file permissions
   ```bash
   sudo chown -R ubuntu:www-data /var/www/atex-calc-web
   ```

4. **Database Issues**: Check if database exists and is writable
   ```bash
   ls -la database/
   sudo chmod 666 database/atex_calculations.db
   ```

## Performance Optimization

1. **Enable Gzip compression** in Nginx
2. **Configure caching** for static files
3. **Use CDN** for static assets if needed
4. **Monitor resource usage** and consider upgrading Lightsail plan if needed

## Support

For issues related to:
- **Application**: Check the logs at `/var/log/atex-calc/`
- **Server**: Use `sudo journalctl`
- **Nginx**: Check `/var/log/nginx/error.log`

Remember to replace `calculadora.atex.la` with your actual domain name throughout the configuration.
