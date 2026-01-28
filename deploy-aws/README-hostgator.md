# Despliegue de Atex Calc en HostGator

Esta carpeta `deploy-gator/atex-calc-web` contiene todos los archivos que debes subir al hosting compartido de HostGator. Sigue los pasos:

1. **Comprimir y subir**
   - Empaca el contenido de `deploy-gator/atex-calc-web` en un zip.
   - En cPanel, abre **File Manager** y súbelo a `public_html/`.
   - Descomprime dentro de `public_html/atex-calc-web/`.

2. **Configurar la app de Python**
   - En cPanel, entra en **Setup Python App**.
   - Selecciona Python 3.9 (o la versión disponible más cercana).
   - Directorio de aplicación: `/home/<usuario>/public_html/atex-calc-web`.
   - Archivo de entrada: `passenger_wsgi.py`.

3. **Instalar dependencias**
   - Desde el panel de la app, abre el terminal o usa el botón *Run Pip Installer* con `requirements.txt`.
   - Alternativamente, vía SSH: activa el virtualenv que crea HostGator y ejecuta `pip install -r requirements.txt` dentro de la carpeta.

4. **Inicializar base de datos**
   - Una vez dentro del virtualenv, ejecuta `python init_db.py` para crear `database/atex_calculations.db` con los datos base.

5. **Actualizar .htaccess**
   - Edita `.htaccess` y reemplaza `username` por tu usuario real de cPanel para `PassengerAppRoot` y `PYTHONPATH`.

6. **Variables de entorno**
   - En el mismo panel de la app define al menos:
     - `FLASK_ENV=production`
     - `SECRET_KEY=<tu_clave>`
   - Si usas otra base de datos configura `DATABASE_URL`.

7. **Reiniciar Passenger**
   - Crea o toca `tmp/restart.txt` (ya hay script `deploy.sh` con este paso) o usa el botón *Restart* en cPanel.

8. **Probar en línea**
   - Apunta tu dominio o subdominio al directorio `public_html/atex-calc-web` desde **Domains > Subdomains**.
   - Accede a la URL para verificar que carga la calculadora.

## Archivos clave
- `.htaccess`: configuración de Passenger y headers.
- `passenger_wsgi.py`: punto de entrada.
- `requirements.txt`: dependencias.
- `deploy.sh`: script opcional para automatizar pasos vía SSH.

Con esto la aplicación debería quedar lista para operar en HostGator.
