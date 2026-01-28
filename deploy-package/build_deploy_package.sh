#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="$ROOT_DIR/atex-calc-web"
DIST_DIR="$ROOT_DIR/deploy-package/dist"
PACKAGE_DIR_NAME=${PACKAGE_DIR_NAME:-atex-calc-web}
ZIP_NAME=${ZIP_NAME:-atex-calc-deploy.zip}

if [[ ! -d "$SRC_DIR" ]]; then
    echo "No se encontró el directorio fuente $SRC_DIR" >&2
    exit 1
fi

rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

STAGING_DIR="$DIST_DIR/$PACKAGE_DIR_NAME"
mkdir -p "$STAGING_DIR"

echo "Copiando archivos de la aplicación..."
rsync -a \
    --exclude 'venv' \
    --exclude '.venv' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '*.db' \
    --exclude 'uploads/*' \
    "$SRC_DIR/" "$STAGING_DIR/"

echo "Generando archivo ZIP..."
pushd "$DIST_DIR" >/dev/null
zip -rq "$ZIP_NAME" "$PACKAGE_DIR_NAME"
popd >/dev/null

cp "$ROOT_DIR/deploy-package/install.sh" "$DIST_DIR/install.sh"

echo "Paquete generado en: $DIST_DIR/$ZIP_NAME"
echo "Incluye script de instalación: $DIST_DIR/install.sh"
