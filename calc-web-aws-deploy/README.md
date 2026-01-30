# AWS Lightsail Deployment Files

Esta carpeta contiene los archivos esenciales para desplegar la aplicación Atex Calculator en AWS Lightsail o EC2 con Ubuntu 22.04.

## Archivos incluidos

- `deploy.sh` - Script de instalación automatizado
- `nginx-calculadora.conf` - Configuración de Nginx
- `passenger_wsgi.py` - Punto de entrada WSGI para Gunicorn
- `requirements.txt` - Dependencias de Python
- `DEPLOYMENT-AWS.md` - Guía completa de despliegue

## Instrucciones rápidas

1. Sube estos archivos y la carpeta `atex-calc-web` completa a tu servidor:
   ```bash
   scp -r atex-calc-web deploy-aws/ ubuntu@tu-servidor:/tmp/
   ```

2. Conéctate al servidor y ejecuta:
   ```bash
   ssh ubuntu@tu-servidor
   cd /tmp/deploy-aws
   sudo chmod +x deploy.sh
   sudo ./deploy.sh
   ```

El script instalará automáticamente:
- Entorno virtual Python 3.10
- Dependencias desde requirements.txt
- Servicio systemd (calculadora.service)
- Configuración de Nginx
- Iniciará la aplicación

## Requisitos previos

- Ubuntu 22.04 LTS
- Nginx instalado
- Python 3.10 disponible
- Acceso sudo
- Dominio calculadora.atex.la apuntando al servidor
