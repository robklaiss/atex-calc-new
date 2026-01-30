#!/bin/bash
# AWS Lightsail deployment script for Atex Calculator
# Uso: ./lightsail-deploy.sh /ruta/a/atex-calc-web

set -e

# Verificar argumento
if [ $# -eq 0 ]; then
    echo "Uso: $0 /ruta/a/la/carpeta/atex-calc-web"
    echo "Ejemplo: $0 /tmp/atex-calc-web"
    exit 1
fi

SOURCE_DIR="$1"
APP_DIR="/var/www/calculadora"
SERVICE_NAME="calculadora"
DOMAIN="calculadora.atex.la"

echo "Iniciando despliegue en AWS Lightsail..."
echo "Directorio fuente: $SOURCE_DIR"
echo "Directorio de aplicación: $APP_DIR"

# Verificar que el directorio fuente existe
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: El directorio $SOURCE_DIR no existe"
    exit 1
fi

# Verificar sudo
if [ "$EUID" -ne 0 ]; then
    echo "Por favor ejecuta con sudo"
    exit 1
fi

# Crear directorio de aplicación
echo "Creando directorio de aplicación..."
mkdir -p "$APP_DIR"
chown ubuntu:ubuntu "$APP_DIR"

# Copiar archivos de la aplicación
echo "Copiando archivos de la aplicación..."
rsync -av --exclude='__pycache__' --exclude='*.pyc' --exclude='venv' \
    "$SOURCE_DIR/" "$APP_DIR/"
chown -R ubuntu:ubuntu "$APP_DIR"

# Copiar archivos de configuración
echo "Instalando archivos de configuración..."
cp passenger_wsgi.py "$APP_DIR/"
cp requirements.txt "$APP_DIR/"

# Crear entorno virtual
echo "Creando entorno virtual Python..."
sudo -u ubuntu python3 -m venv "$APP_DIR/venv"

# Instalar dependencias
echo "Instalando dependencias Python..."
sudo -u ubuntu "$APP_DIR/venv/bin/pip" install --upgrade pip
sudo -u ubuntu "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

# Inicializar base de datos si existe
if [ -f "$APP_DIR/init_db.py" ]; then
    echo "Inicializando base de datos..."
    cd "$APP_DIR"
    sudo -u ubuntu "$APP_DIR/venv/bin/python" init_db.py
fi

# Crear servicio systemd
echo "Creando servicio systemd..."
cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=Atex Calculator Flask App
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn \\
    --workers 3 \\
    --bind 127.0.0.1:8000 \\
    passenger_wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Iniciar servicio
echo "Iniciando servicio..."
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

# Configurar Nginx
echo "Configurando Nginx..."
cat > "/etc/nginx/sites-available/$SERVICE_NAME" << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location /static {
        alias $APP_DIR/app/static;
        expires 30d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Activar sitio de Nginx
ln -sf "/etc/nginx/sites-available/$SERVICE_NAME" "/etc/nginx/sites-enabled/"
rm -f /etc/nginx/sites-enabled/default

# Probar y recargar Nginx
nginx -t && systemctl reload nginx

echo ""
echo "¡Despliegue completado!"
echo "La aplicación debería estar disponible en: http://$DOMAIN"
echo ""
echo "Comandos útiles:"
echo "  Ver logs: sudo journalctl -u $SERVICE_NAME -f"
echo "  Reiniciar: sudo systemctl restart $SERVICE_NAME"
echo "  Estado: sudo systemctl status $SERVICE_NAME"
