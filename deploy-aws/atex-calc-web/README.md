# Calculadora Atex - Versión Web

Aplicación web para calcular y comparar costos entre el sistema constructivo Atex (losas con casetones) y losas tradicionales macizas.

## Características

- Procesamiento de archivos DXF para extracción de geometría
- Cálculo automático de cantidades de hormigón y acero
- Análisis comparativo de costos entre diferentes sistemas constructivos
- Base de datos con precios para múltiples países
- Generación de reportes en PDF
- Interfaz web moderna y responsiva

## Tecnologías Utilizadas

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Base de Datos**: SQLite
- **Procesamiento DXF**: ezdxf, shapely
- **Generación PDF**: ReportLab
- **Gráficos**: Matplotlib

## Requisitos

- Python 3.8+
- pip (gestor de paquetes de Python)

## Instalación

1. Clonar el repositorio:
```bash
git clone <repository-url>
cd atex-calc-web
```

2. Crear entorno virtual:
```bash
python -m venv venv
# En Windows
venv\Scripts\activate
# En macOS/Linux
source venv/bin/activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Inicializar la base de datos:
```bash
python init_db.py
```

5. Ejecutar la aplicación:
```bash
python app.py
```

6. Abrir el navegador en http://localhost:5000

## Estructura del Proyecto

```
atex-calc-web/
├── app.py                 # Aplicación principal Flask
├── init_db.py            # Script de inicialización de BD
├── requirements.txt      # Dependencias Python
├── app/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css # Estilos personalizados
│   │   ├── js/
│   │   │   └── main.js   # JavaScript principal
│   │   └── images/       # Imágenes de la aplicación
│   ├── templates/
│   │   ├── base.html     # Plantilla base
│   │   ├── index.html    # Página de inicio
│   │   └── calculator.html # Calculadora
│   └── utils/
│       ├── dxf_processor.py  # Procesamiento de DXF
│       ├── calculations.py   # Lógica de cálculos
│       └── pdf_generator.py  # Generación de PDF
├── database/             # Base de datos SQLite
└── uploads/             # Archivos temporales
```

## Uso

1. **Cargar Archivo DXF**: 
   - Arrastre y suelte un archivo DXF o haga clic para seleccionarlo
   - El archivo debe contener las capas: superficieTotal, superficieCasetones, superficieMacizos, superficieVacios

2. **Configurar Parámetros**:
   - Ingrese los datos del proyecto
   - Seleccione el país
   - Configure el espesor de la losa y resistencias de materiales
   - Seleccione el tipo de casetón si aplica

3. **Calcular**:
   - Presione el botón "Calcular Costos"
   - Revise los resultados en las tablas comparativas

4. **Generar Reporte**:
   - Presione "Generar PDF" para descargar el reporte completo

## Despliegue en HostGator

HostGator soporta aplicaciones Python a través de cPanel con Passenger. Siga estos pasos:

1. **Preparar la aplicación**:
   - Actualizar `app.py` para producción:
     ```python
     if __name__ == '__main__':
         app.run(debug=False, host='0.0.0.0', port=5000)
     ```

2. **Crear archivo passenger_wsgi.py**:
   ```python
   import sys
   import os
   
   sys.path.insert(0, os.path.dirname(__file__))
   
   from app import app as application
   ```

3. **Crear requirements.txt en el servidor**:
   - Asegúrese de incluir todas las dependencias

4. **Configurar en cPanel**:
   - Vaya a "Setup Python App"
   - Cree una nueva aplicación Python
   - Configure la versión de Python y el directorio raíz
   - Instale los requisitos usando pip
   - Inicie la aplicación

5. **Configurar dominio**:
   - Configure el dominio o subdominio para apuntar a la aplicación

## Variables de Entorno

Para producción, configure las siguientes variables de entorno:

- `FLASK_ENV`: production
- `SECRET_KEY`: Clave secreta única para la aplicación
- `DATABASE_URL`: URL de la base de datos (si no usa SQLite)

## Soporte

Para soporte técnico o preguntas, contacte al administrador del sistema.

## Licencia

© 2024 - Calculadora Atex - Todos los derechos reservados
