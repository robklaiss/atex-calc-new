from flask import Flask, render_template, request, jsonify, send_file, session
import os
import json
from datetime import datetime
import sqlite3
from werkzeug.utils import secure_filename
import uuid

# Get the absolute path of the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.secret_key = 'your-secret-key-change-in-production'
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.config['DATABASE'] = os.path.join(BASE_DIR, 'database', 'atex_calculations.db')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.dirname(app.config['DATABASE']), exist_ok=True)

# Import utilities
from app.utils.dxf_processor import process_dxf_file
from app.utils.pdf_generator import generate_pdf_report
from app.utils.calculations import calculate_atex_quantities
from app.utils.geometry_plotter import generate_geometry_preview
from app.utils.section_plotter import generate_section_plot


def _fetch_caseton(caseton_id=None, caseton_name=None):
    if not caseton_id and not caseton_name:
        return None
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    if caseton_id:
        cursor.execute("SELECT * FROM casetones WHERE id = ?", (caseton_id,))
    else:
        cursor.execute("SELECT * FROM casetones WHERE name = ?", (caseton_name,))
    row = cursor.fetchone()
    conn.close()
    return row


def _build_section_preview(caseton_row, slab_thickness_m):
    if not caseton_row:
        return None
    try:
        _, name, side1, side2, height, bw, bs, *_ = caseton_row
        bf_cm = float(side1)
        bs_cm = float(bs)
        bw_cm = float(bw)
        hv_cm = float(height)
        total_thickness_cm = max(float(slab_thickness_m or 0.0) * 100.0, 0.0)
        hf_cm = max(total_thickness_cm - hv_cm, 5.0)
        he_cm = total_thickness_cm if total_thickness_cm > 0 else hv_cm + hf_cm
        section = generate_section_plot(
            'aligerada', bf_cm, bs_cm, bw_cm, hv_cm, hf_cm, he_cm
        )
        return {
            'name': name,
            'image': section.image_base64,
            'metrics': {
                'bf_cm': bf_cm,
                'bs_cm': bs_cm,
                'bw_cm': bw_cm,
                'hv_cm': hv_cm,
                'hf_cm': hf_cm,
                'total_thickness_cm': total_thickness_cm or (hv_cm + hf_cm),
                'inertia_cm4': section.inertia_cm4,
                'area_cm2': section.area_cm2,
                'value_ratio': section.value_ratio,
                'equivalent_solid_height_cm': section.equivalent_solid_height_cm,
            }
        }
    except Exception:
        return None

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/calculator')
def calculator():
    """Calculator page"""
    return render_template('calculator.html')

@app.route('/api/upload-dxf', methods=['POST'])
def upload_dxf():
    """Process DXF file and extract geometry"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and file.filename.lower().endswith('.dxf'):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        try:
            # Process DXF file
            result = process_dxf_file(filepath)
            preview_data = generate_geometry_preview(result)
            if preview_data:
                result['preview'] = preview_data
            session['geometry_data'] = result
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            # Clean up uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)
    
    return jsonify({'error': 'Invalid file format'}), 400

@app.route('/api/calculate', methods=['POST'])
def calculate():
    """Perform calculations based on input data"""
    try:
        data = request.get_json()
        
        # Get geometry data from session or request
        geometry_data = data.get('geometry') or session.get('geometry_data', {})
        
        slab_thickness = data.get('slab_thickness')
        if slab_thickness is None:
            slab_thickness = data.get('slabThickness', 0.20)
        selected_caseton_id = data.get('selected_caseton_id') or data.get('selectedCasetonId')
        selected_caseton_name = data.get('selected_caseton_name') or data.get('selectedCasetonName') or data.get('casetonType')
        try:
            if selected_caseton_id is not None:
                selected_caseton_id = int(selected_caseton_id)
        except ValueError:
            selected_caseton_id = None

        # Calculate quantities
        results = calculate_atex_quantities(
            geometry_data=geometry_data,
            country=data.get('country', 'Colombia'),
            slab_thickness=slab_thickness,
            concrete_strength=data.get('concrete_strength', 25),
            steel_strength=data.get('steel_strength', 420),
            selected_caseton=selected_caseton_id,
            database_path=app.config['DATABASE']
        )
        
        caseton_row = _fetch_caseton(selected_caseton_id, selected_caseton_name)
        section_preview = _build_section_preview(caseton_row, slab_thickness)
        if section_preview:
            results.setdefault('section', section_preview)

        # Store results in session for PDF generation
        session['calculation_results'] = results
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-pdf', methods=['POST'])
def generate_pdf():
    """Generate PDF report"""
    try:
        data = request.get_json()
        
        # Get calculation results from session
        results = session.get('calculation_results', {})
        
        # Generate PDF
        pdf_path = generate_pdf_report(
            results=results,
            project_data=data.get('project_data', {}),
            output_dir=app.config['UPLOAD_FOLDER']
        )
        
        return send_file(pdf_path, as_attachment=True, download_name='atex_report.pdf')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/countries')
def get_countries():
    """Get list of available countries"""
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM countries ORDER BY name")
    countries = [{'id': row[0], 'name': row[1], 'currency': row[2], 'exchange_rate': row[3]} 
                 for row in cursor.fetchall()]
    conn.close()
    return jsonify(countries)

@app.route('/api/casetones')
def get_casetones():
    """Get list of available casetones"""
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM casetones ORDER BY name")
    casetones = [{'id': row[0], 'name': row[1], 'side1': row[2], 'side2': row[3], 
                  'height': row[4], 'bw': row[5], 'bs': row[6], 'consumption': row[7], 
                  'rental_price': row[8]} for row in cursor.fetchall()]
    conn.close()
    return jsonify(casetones)

@app.route('/api/save-calculation', methods=['POST'])
def save_calculation():
    """Save calculation to database"""
    try:
        data = request.get_json()
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO calculations (name, country, date, data, results)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data.get('name', 'Untitled'),
            data.get('country', ''),
            datetime.now().isoformat(),
            json.dumps(data.get('input_data', {})),
            json.dumps(data.get('results', {}))
        ))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/calculations')
def get_calculations():
    """Get saved calculations"""
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM calculations ORDER BY date DESC")
    calculations = [{'id': row[0], 'name': row[1], 'country': row[2], 'date': row[3]} 
                    for row in cursor.fetchall()]
    conn.close()
    return jsonify(calculations)

@app.route('/download-test-dxf')
def download_test_dxf():
    """Download a test DXF file"""
    test_file_path = os.path.join(BASE_DIR, 'test_losa.dxf')
    if os.path.exists(test_file_path):
        return send_file(test_file_path, as_attachment=True, download_name='ejemplo_losa.dxf')
    else:
        return "Test file not found", 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
