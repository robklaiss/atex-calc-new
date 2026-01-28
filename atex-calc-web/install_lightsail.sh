#!/usr/bin/env bash

set -euo pipefail

# ---------------------------------------------
# Atex Calculator Lightsail installer
# ---------------------------------------------

APP_DIR=${APP_DIR:-/var/www/atex-calc-web}
SERVICE_NAME=${SERVICE_NAME:-atex-calc}
DOMAIN_NAME=${DOMAIN_NAME:-_}
GUNICORN_WORKERS=${GUNICORN_WORKERS:-3}
PYTHON_BIN=${PYTHON_BIN:-python3}
APP_USER=${APP_USER:-ubuntu}
SCRIPT_SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$APP_DIR/venv"
SYSTEMD_UNIT="/etc/systemd/system/${SERVICE_NAME}.service"

require_root() {
    if [[ $EUID -ne 0 ]]; then
        echo "Este script debe ejecutarse con sudo o como root" >&2
        exit 1
    fi
}

ensure_user_exists() {
    if ! id -u "$APP_USER" >/dev/null 2>&1; then
        echo "Creando usuario del sistema $APP_USER..."
        useradd --system --create-home --shell /bin/bash "$APP_USER"
    fi
}

detect_pkg_manager() {
    if command -v apt-get >/dev/null 2>&1; then
        PKG_MANAGER="apt"
    elif command -v dnf >/dev/null 2>&1; then
        PKG_MANAGER="dnf"
    elif command -v yum >/dev/null 2>&1; then
        PKG_MANAGER="yum"
    else
        echo "No se encontró un gestor de paquetes compatible (apt/dnf/yum)." >&2
        exit 1
    fi
}

install_os_packages() {
    echo "Instalando paquetes del sistema..."
    case "$PKG_MANAGER" in
        apt)
            export DEBIAN_FRONTEND=noninteractive
            apt-get update -y
            apt-get install -y python3.12 python3.12-venv python3.12-dev python3-pip build-essential \
                libfreetype6-dev libjpeg-dev zlib1g-dev libpng-dev sqlite3 git nginx
            ;;
        dnf)
            dnf install -y python3 python3-devel python3-pip gcc gcc-c++ freetype-devel \
                libjpeg-turbo-devel zlib-devel libpng-devel sqlite git nginx
            ;;
        yum)
            yum install -y python3 python3-devel python3-pip gcc gcc-c++ freetype-devel \
                libjpeg-turbo-devel zlib-devel libpng-devel sqlite git nginx
            ;;
    esac
}

sync_project_files() {
    echo "Sincronizando archivos hacia $APP_DIR..."
    mkdir -p "$APP_DIR"
    rsync -a --delete \
        --exclude 'venv' \
        --exclude '__pycache__' \
        --exclude '*.pyc' \
        "$SCRIPT_SRC_DIR/" "$APP_DIR/"
    chown -R "$APP_USER":www-data "$APP_DIR"
}

setup_virtualenv() {
    echo "Creando entorno virtual en $VENV_DIR..."
    sudo -u "$APP_USER" python3.12 -m venv "$VENV_DIR"
    sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install --upgrade pip wheel
    sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"
}

initialize_database() {
    echo "Inicializando base de datos SQLite..."
    sudo -u "$APP_USER" env \
        PATH="$VENV_DIR/bin:$PATH" \
        "$VENV_DIR/bin/python" "$APP_DIR/init_db.py"
}

create_systemd_service() {
    echo "Creando servicio systemd $SERVICE_NAME..."
    cat >"$SYSTEMD_UNIT" <<EOF
[Unit]
Description=Atex Calculator (Gunicorn)
After=network.target

[Service]
User=$APP_USER
Group=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/gunicorn --workers $GUNICORN_WORKERS --bind 127.0.0.1:8000 passenger_wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    systemctl restart "$SERVICE_NAME"
}

configure_nginx() {
    echo "Configurando Nginx..."
    local nginx_conf
    if [[ -d /etc/nginx/sites-available ]]; then
        nginx_conf="/etc/nginx/sites-available/${SERVICE_NAME}.conf"
        cat >"$nginx_conf" <<EOF
server {
    listen 80;
    server_name $DOMAIN_NAME;

    client_max_body_size 50M;

    location /static/ {
        alias $APP_DIR/app/static/;
    }

    location / {
        include proxy_params;
        proxy_set_header Host $host;
        proxy_pass http://127.0.0.1:8000;
    }
}
EOF
        ln -sf "$nginx_conf" \
            "/etc/nginx/sites-enabled/${SERVICE_NAME}.conf"
    else
        nginx_conf="/etc/nginx/conf.d/${SERVICE_NAME}.conf"
        cat >"$nginx_conf" <<EOF
server {
    listen 80;
    server_name $DOMAIN_NAME;

    client_max_body_size 50M;

    location /static/ {
        alias $APP_DIR/app/static/;
    }

    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://127.0.0.1:8000;
    }
}
EOF
    fi
    nginx -t
    systemctl enable nginx
    systemctl restart nginx
}

main() {
    require_root
    detect_pkg_manager
    install_os_packages
    ensure_user_exists
    sync_project_files
    setup_virtualenv
    initialize_database
    create_systemd_service
    configure_nginx

    cat <<INFO

Instalación completada.

- Código desplegado en: $APP_DIR
- Servicio systemd: $SERVICE_NAME (systemctl status $SERVICE_NAME)
- Gunicorn running on: 127.0.0.1:8000
- Configuración Nginx: ver archivo generado en /etc/nginx/

Recuerda configurar la variable SECRET_KEY en el archivo .env
Puedes ajustar DOMAIN_NAME, APP_DIR exportando las variables antes de ejecutar el script.
INFO
}

main "$@"
