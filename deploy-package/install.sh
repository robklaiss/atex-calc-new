#!/usr/bin/env bash

set -euo pipefail

ZIP_PATH=${ZIP_PATH:-./atex-calc-deploy.zip}
PACKAGE_DIR_NAME=${PACKAGE_DIR_NAME:-atex-calc-web}
APP_DIR=${APP_DIR:-/opt/atex-calc-web}
SERVICE_NAME=${SERVICE_NAME:-atex-calc}
APP_USER=${APP_USER:-${SUDO_USER:-$USER}}
DOMAIN_NAME=${DOMAIN_NAME:-_}
SECRET_KEY=${SECRET_KEY:-changeme}
GUNICORN_WORKERS=${GUNICORN_WORKERS:-3}
PYTHON_BIN=${PYTHON_BIN:-python3}
KEEP_TEMP=${KEEP_TEMP:-0}

TMP_DIR=""

require_root() {
    if [[ $EUID -ne 0 ]]; then
        echo "Este script debe ejecutarse con sudo o como root" >&2
        exit 1
    fi
}

cleanup() {
    [[ -n "$TMP_DIR" && -d "$TMP_DIR" && $KEEP_TEMP -eq 0 ]] && rm -rf "$TMP_DIR"
}

trap cleanup EXIT

detect_pkg_manager() {
    if command -v apt-get >/dev/null 2>&1; then
        PKG_MANAGER="apt"
    elif command -v dnf >/dev/null 2>&1; then
        PKG_MANAGER="dnf"
    elif command -v yum >/dev/null 2>&1; then
        PKG_MANAGER="yum"
    else
        echo "No se detectó gestor de paquetes compatible (apt/dnf/yum)." >&2
        exit 1
    fi
}

install_prereqs() {
    case "$PKG_MANAGER" in
        apt)
            export DEBIAN_FRONTEND=noninteractive
            apt-get update -y
            apt-get install -y unzip rsync
            ;;
        dnf)
            dnf install -y unzip rsync
            ;;
        yum)
            yum install -y unzip rsync
            ;;
    esac
}

extract_package() {
    if [[ ! -f "$ZIP_PATH" ]]; then
        echo "No se encontró el archivo ZIP: $ZIP_PATH" >&2
        exit 1
    fi
    TMP_DIR="$(mktemp -d)"
    echo "Descomprimiendo paquete en $TMP_DIR..."
    unzip -q "$ZIP_PATH" -d "$TMP_DIR"
    SRC_DIR="$TMP_DIR/$PACKAGE_DIR_NAME"
    if [[ ! -d "$SRC_DIR" ]]; then
        local first_dir
        first_dir=$(find "$TMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1 || true)
        if [[ -z "$first_dir" ]]; then
            echo "No se encontraron carpetas dentro del ZIP." >&2
            exit 1
        fi
        SRC_DIR="$first_dir"
    fi
    echo "Paquete extraído en $SRC_DIR"
}

run_installer() {
    if [[ ! -x "$SRC_DIR/install_lightsail.sh" ]]; then
        chmod +x "$SRC_DIR/install_lightsail.sh"
    fi
    echo "Ejecutando instalador con APP_DIR=$APP_DIR..."
    APP_DIR="$APP_DIR" \
    SERVICE_NAME="$SERVICE_NAME" \
    APP_USER="$APP_USER" \
    DOMAIN_NAME="$DOMAIN_NAME" \
    SECRET_KEY="$SECRET_KEY" \
    GUNICORN_WORKERS="$GUNICORN_WORKERS" \
    PYTHON_BIN="$PYTHON_BIN" \
    bash "$SRC_DIR/install_lightsail.sh"
}

main() {
    require_root
    detect_pkg_manager
    install_prereqs
    extract_package
    run_installer
    echo "\nInstalación completada. Servicio: $SERVICE_NAME. Directorio: $APP_DIR"
    if [[ $KEEP_TEMP -eq 1 ]]; then
        echo "Los archivos extraídos se conservaron en: $TMP_DIR"
    fi
}

main "$@"
