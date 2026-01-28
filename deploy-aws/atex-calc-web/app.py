from flask import Flask, render_template, request, jsonify, send_file
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
from app.utils.homologation import generate_homologation_analysis


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


def _build_original_section_table(metrics):
    if not metrics:
        return []
    try:
        return [
            {
                'item': 'Ancho Afer.',
                'spec': 'b(o) (cm)',
                'value': round(float(metrics.get('bf_cm', 0.0)), 1)
            },
            {
                'item': 'Inercia.',
                'spec': 'I(o) (cm4)',
                'value': round(float(metrics.get('inertia_cm4', 0.0)), 2)
            },
            {
                'item': 'b(o)/I(o)',
                'spec': '(1/cm3) x 10^3',
                'value': round(float(metrics.get('value_ratio', 0.0)), 3)
            }
        ]
    except Exception:
        return []


def _build_geometry_analysis(geometry_data):
    if not geometry_data:
        return None

    areas = geometry_data.get('areas', {})
    area_total = float(areas.get('superficieTotal') or 0.0)
    area_vacios = float(areas.get('superficieVacios', {}).get('total') or 0.0)
    area_macizos = float(areas.get('superficieMacizos', {}).get('total') or 0.0)
    casetones = geometry_data.get('casetones', [])
    area_casetones = sum(float(c.get('area') or 0.0) for c in casetones)
    area_neta = max(area_total - area_vacios, 0.0)
    area_vigas = max(area_total - area_macizos - area_casetones, 0.0)

    def pct(value):
        return (value / area_total * 100.0) if area_total else 0.0

    return {
        'areas': {
            'bruta_m2': area_total,
            'neta_m2': area_neta,
            'vacios_m2': area_vacios,
            'paneles_macizos_m2': area_macizos,
            'paneles_casetones_m2': area_casetones,
            'vigas_m2': area_vigas,
        },
        'percentages': {
            'neta_pct': pct(area_neta),
            'paneles_macizos_pct': pct(area_macizos),
            'paneles_casetones_pct': pct(area_casetones),
            'vigas_pct': pct(area_vigas),
        },
        'counts': {
            'casetones': len(casetones),
        }
    }


def _fetch_default_caseton():
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM casetones ORDER BY id LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row


def _caseton_row_to_params(caseton_row, slab_thickness_m):
    if not caseton_row:
        return None
    try:
        _, _, side1, side2, height, bw, bs, *_ = caseton_row
        bf_cm = float(side1) if side1 else float(side2 or 0.0)
        bs_cm = float(bs or 0.0)
        bw_cm = float(bw or 0.0)
        hv_cm = float(height or 0.0)
        total_thickness_cm = max(float(slab_thickness_m or 0.0) * 100.0, 0.0)
        hf_cm = max(total_thickness_cm - hv_cm, 5.0)
        if total_thickness_cm <= 0:
            total_thickness_cm = hv_cm + hf_cm
        return {
            'bf_cm': bf_cm,
            'bs_cm': bs_cm,
            'bw_cm': bw_cm,
            'hv_cm': hv_cm,
            'hf_cm': hf_cm,
            'total_thickness_cm': total_thickness_cm,
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
        geometry_data = data.get('geometry') or {}
        
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
        fallback_params = _caseton_row_to_params(caseton_row, slab_thickness)
        if fallback_params is None:
            default_row = _fetch_default_caseton()
            fallback_params = _caseton_row_to_params(default_row, slab_thickness)

        section_preview = _build_section_preview(caseton_row, slab_thickness)
        if section_preview:
            results.setdefault('section', section_preview)
        else:
            if fallback_params:
                # Build a simple preview with derived metrics when DB data exists
                derived_section = generate_section_plot(
                    'aligerada',
                    fallback_params['bf_cm'],
                    fallback_params['bs_cm'],
                    fallback_params['bw_cm'],
                    fallback_params['hv_cm'],
                    fallback_params['hf_cm'],
                    fallback_params['total_thickness_cm'],
                )
                section_preview = {
                    'name': selected_caseton_name or (caseton_row[1] if caseton_row else 'Casetón ATEX'),
                    'image': derived_section.image_base64,
                    'metrics': {
                        'bf_cm': fallback_params['bf_cm'],
                        'bs_cm': fallback_params['bs_cm'],
                        'bw_cm': fallback_params['bw_cm'],
                        'hv_cm': fallback_params['hv_cm'],
                        'hf_cm': fallback_params['hf_cm'],
                        'total_thickness_cm': fallback_params['total_thickness_cm'],
                        'inertia_cm4': derived_section.inertia_cm4,
                        'area_cm2': derived_section.area_cm2,
                        'value_ratio': derived_section.value_ratio,
                        'equivalent_solid_height_cm': derived_section.equivalent_solid_height_cm,
                    }
                }
                results.setdefault('section', section_preview)

        homologation = generate_homologation_analysis(
            database_path=app.config['DATABASE'],
            section_metrics=section_preview['metrics'] if section_preview else None,
            fallback_params=fallback_params
        )
        results.setdefault('homologation', homologation)
        if homologation.get('original_metrics'):
            results.setdefault('original_section', homologation['original_metrics'])
            results.setdefault('original_section_table', _build_original_section_table(homologation['original_metrics']))

        geometry_analysis = _build_geometry_analysis(geometry_data)
        if geometry_analysis:
            results.setdefault('geometry_analysis', geometry_analysis)

        if not selected_caseton_id:
            recommended = homologation.get('recommended')
            if recommended and recommended.get('caseton'):
                fallback_row = _fetch_caseton(None, recommended['caseton'])
                section_preview = section_preview or _build_section_preview(fallback_row, slab_thickness)
                if section_preview:
                    results['section'] = section_preview
                selected_caseton_name = recommended['caseton']
                results.setdefault('recommended_caseton', recommended)


        # Return results to client for PDF generation
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-pdf', methods=['POST'])
def generate_pdf():
    """Generate PDF report"""
    try:
        data = request.get_json() or {}
        
        # Get calculation results from request payload
        results = data.get('results', {})
        
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
