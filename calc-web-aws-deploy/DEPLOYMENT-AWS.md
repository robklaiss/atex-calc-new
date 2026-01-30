# AWS EC2 Deployment Guide

## Prerequisites
- AWS EC2 instance with Ubuntu 22.04 LTS
- Nginx installed and running
- Domain `calculadora.atex.la` pointing to the EC2 instance
- Sudo access

## Quick Deployment

1. **Upload the project to EC2:**
   ```bash
   # Copy project to EC2 (run from your local machine)
   scp -r atex-calc-web/ ubuntu@your-ec2-ip:/tmp/
   ```

2. **SSH into EC2 and deploy:**
   ```bash
   ssh ubuntu@your-ec2-ip
   cd /tmp/atex-calc-web
   sudo chmod +x deploy.sh
   sudo ./deploy.sh
   ```

## Manual Steps (if needed)

1. **Create application directory:**
   ```bash
   sudo mkdir -p /var/www/calculadora
   sudo chown ubuntu:ubuntu /var/www/calculadora
   ```

2. **Copy files:**
   ```bash
   cp -r /tmp/atex-calc-web/* /var/www/calculadora/
   ```

3. **Create virtual environment:**
   ```bash
   cd /var/www/calculadora
   python3.10 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Initialize database (if init_db.py exists):**
   ```bash
   python init_db.py
   ```

5. **Create systemd service:**
   ```bash
   sudo nano /etc/systemd/system/calculadora.service
   # Copy the service configuration from deploy.sh
   ```

6. **Start service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable calculadora
   sudo systemctl start calculadora
   ```

7. **Configure Nginx:**
   ```bash
   sudo cp nginx-calculadora.conf /etc/nginx/sites-available/calculadora
   sudo ln -s /etc/nginx/sites-available/calculadora /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

## Useful Commands

```bash
# Check application status
sudo systemctl status calculadora

# View application logs
sudo journalctl -u calculadora -f

# Restart application
sudo systemctl restart calculadora

# View Nginx logs
sudo tail -f /var/log/nginx/error.log
```

## SSL/HTTPS (Recommended)

After deployment, secure your site with Let's Encrypt:

```bash
# Install Certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d calculadora.atex.la
```

## Troubleshooting

1. **If the service fails to start:**
   - Check logs: `sudo journalctl -u calculadora -n 50`
   - Verify Python paths in the service file
   - Ensure all dependencies are installed

2. **If 502 Bad Gateway:**
   - Check if Gunicorn is running: `ps aux | grep gunicorn`
   - Check if port 8000 is listening: `netstat -tlnp | grep 8000`
   - Review Nginx error logs

3. **If static files aren't loading:**
   - Verify static file permissions
   - Check Nginx configuration for the /static location
   - Ensure static files exist at /var/www/calculadora/app/static
