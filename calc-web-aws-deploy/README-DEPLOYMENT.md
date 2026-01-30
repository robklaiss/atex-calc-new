# Atex Calculator - AWS Deployment Package

Este paquete contiene todos los archivos necesarios para desplegar la aplicación Atex Calculator en AWS EC2 o Lightsail con Ubuntu 22.04.

## Contenido del paquete

### Aplicación Flask
- `app.py` - Aplicación principal Flask
- `app/` - Módulos de la aplicación
  - `templates/` - Plantillas HTML
  - `static/` - Archivos estáticos (CSS, JS, imágenes)
  - `utils/` - Utilidades de la aplicación
- `init_db.py` - Script para inicializar la base de datos
- `passenger_wsgi.py` - Punto de entrada WSGI para Gunicorn

### Configuración
- `requirements.txt` - Dependencias de Python
- `.env.example` - Variables de entorno de ejemplo
- `nginx-calculadora.conf` - Configuración de Nginx

### Scripts de despliegue
- `deploy.sh` - Script de despliegue completo
- `lightsail-deploy.sh` - Script simplificado para Lightsail

### Documentación
- `DEPLOYMENT-AWS.md` - Guía detallada de despliegue
- `README-DEPLOYMENT.md` - Este archivo

## Despliegue rápido

### Opción 1: Usando el script completo (recomendado)

```bash
# 1. Sube este paquete completo al servidor
scp -r calc-web-aws-deploy/ ubuntu@tu-servidor:/tmp/

# 2. Conéctate al servidor
ssh ubuntu@tu-servidor

# 3. Ejecuta el script de despliegue
cd /tmp/calc-web-aws-deploy
sudo chmod +x deploy.sh
sudo ./deploy.sh
```

### Opción 2: Manual paso a paso

```bash
# 1. Crear directorio de aplicación
sudo mkdir -p /var/www/calculadora
sudo chown ubuntu:ubuntu /var/www/calculadora

# 2. Copiar archivos
cp -r /tmp/calc-web-aws-deploy/* /var/www/calculadora/
cd /var/www/calculadora

# 3. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# 6. Inicializar base de datos
python init_db.py

# 7. Crear servicio systemd
sudo nano /etc/systemd/system/calculadora.service
# Pegar el contenido del servicio

# 8. Iniciar servicio
sudo systemctl daemon-reload
sudo systemctl enable calculadora
sudo systemctl start calculadora

# 9. Configurar Nginx
sudo cp nginx-calculadora.conf /etc/nginx/sites-available/calculadora
sudo ln -s /etc/nginx/sites-available/calculadora /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Requisitos del servidor

- Ubuntu 22.04 LTS
- Python 3.10+
- Nginx instalado
- Acceso sudo
- Dominio configurado (calculadora.atex.la)

## Post-despliegue

1. **Verificar que la aplicación funciona:**
   ```bash
   curl http://localhost
   ```

2. **Verificar logs:**
   ```bash
   sudo journalctl -u calculadora -f
   ```

3. **Configurar SSL (recomendado):**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d calculadora.atex.la
   ```

## Estructura después del despliegue

```
/var/www/calculadora/
├── app/                 # Aplicación Flask
├── venv/               # Entorno virtual Python
├── database/           # Base de datos SQLite
├── uploads/            # Archivos subidos
├── app.py              # Aplicación principal
├── passenger_wsgi.py   # WSGI entry point
└── requirements.txt    # Dependencias
```

## Solución de problemas

- **502 Bad Gateway:** Verificar que Gunicorn está corriendo
- **Archivos estáticos no cargan:** Revisar permisos y configuración Nginx
- **Error de base de datos:** Asegurarse que database/ tiene permisos de escritura
