import math
import os
import sqlite3
from datetime import datetime


def _parse_float(value, default=None):
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(',', '.')
        if not cleaned:
            return default
        try:
            return float(cleaned)
        except ValueError:
            return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

class Caseton:
    """Represents a waffle slab form (caseton)"""
    def __init__(self, nombre, lado1, lado2, altura, bw, bs, system, consumo_base, precio_alquiler_dia):
        self.nombre = nombre
        self.lado1 = _parse_float(lado1, 0.0)  # cm
        self.lado2 = _parse_float(lado2, 0.0)  # cm
        self.altura = _parse_float(altura, 0.0)  # cm
        self.bw = _parse_float(bw, 0.0)  # cm
        self.bs = _parse_float(bs, 0.0)  # cm
        self.system = system
        self.consumo_base = _parse_float(consumo_base, 0.0)  # m3/m2 for 5cm slab
        self.precio_alquiler_dia = _parse_float(precio_alquiler_dia, 0.0)
    
    def get_lado1_m(self):
        return self.lado1 / 100.0
    
    def get_lado2_m(self):
        return self.lado2 / 100.0
    
    def get_altura_m(self):
        return self.altura / 100.0
    
    def get_area_m2(self):
        return self.get_lado1_m() * self.get_lado2_m()

def calculate_atex_quantities(geometry_data, country='Colombia', slab_thickness=0.20, 
                             concrete_strength=25, steel_strength=420, selected_caseton=None, 
                             database_path=None, slab_geometry=None, beam_height_cm=None):
    """Calculate quantities for ATex system"""

    slab_thickness = _parse_float(slab_thickness, 0.20)
    beam_height_cm = _parse_float(beam_height_cm, None)
    
    # Use provided database path or default
    if not database_path:
        database_path = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'atex_calculations.db')
    
    # Get database connection
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    
    # Get country data
    cursor.execute("SELECT currency, exchange_rate FROM countries WHERE name = ?", (country,))
    country_data = cursor.fetchone()
    if not country_data:
        defaults_by_name = {
            'República Dominicana': ('Peso dominicano', 62.6),
            'Republica Dominicana': ('Peso dominicano', 62.6),
            'Colombia': ('Peso colombiano', 3850.0),
            'Panamá': ('Dólar americano', 1.0),
        }
        country_data = defaults_by_name.get(country) or ('Peso colombiano', 3850.0)
    
    # Get APU items
    cursor.execute("""
        SELECT description, unit, unit_price 
        FROM apu_items 
        WHERE country = ? AND technology = 'Atex'
    """, (country,))
    apu_items = cursor.fetchall()
    
    # Calculate areas provided by the DXF
    areas = geometry_data.get('areas', {})
    area_total = float(areas.get('superficieTotal') or 0.0)
    area_vacios = float((areas.get('superficieVacios') or {}).get('total') or 0.0)
    area_macizos = float((areas.get('superficieMacizos') or {}).get('total') or 0.0)
    area_casetones = sum(float(c.get('area') or 0.0) for c in geometry_data.get('casetones', []))

    area_neta = max(area_total - area_vacios, 0.0)
    # Caseton area cannot exceed the usable net area after subtracting macizos
    max_casetones_area = max(area_neta - area_macizos, 0.0)
    area_casetones = min(area_casetones, max_casetones_area)

    area_vigas = max(area_neta - area_macizos - area_casetones, 0.0)
    
    # Calculate concrete volume
    # Base slab (5cm) + waffle portion
    base_thickness = 0.05
    extra_thickness = max(slab_thickness - base_thickness, 0.0)
    volumen_base = area_neta * base_thickness  # 5cm base slab only on usable area
    volumen_casetones = area_casetones * extra_thickness * 0.4  # 40% efficiency
    volumen_macizos = area_macizos * slab_thickness
    volumen_total = volumen_base + volumen_casetones + volumen_macizos
    
    # Calculate steel reinforcement
    # Typical reinforcement: 0.15 kg/m2 for 5cm slab + additional for thickness
    refuerzo_base = area_neta * 0.15
    refuerzo_adicional = area_neta * extra_thickness * 8.0  # kg/m2 per cm of thickness
    acero_total = refuerzo_base + refuerzo_adicional
    
    # Calculate formwork (casetones)
    caseton_height_m = None
    if selected_caseton:
        cursor.execute("SELECT * FROM casetones WHERE id = ?", (selected_caseton,))
        caseton_data = cursor.fetchone()
        if caseton_data:
            (
                _,
                nombre,
                lado1,
                lado2,
                altura,
                bw,
                bs,
                system_label,
                consumo_base,
                precio_alquiler,
            ) = caseton_data
            caseton = Caseton(
                nombre,
                lado1,
                lado2,
                altura,
                bw,
                bs,
                system_label,
                consumo_base,
                precio_alquiler,
            )
            caseton_height_m = caseton.get_altura_m()
            num_casetones = area_casetones / caseton.get_area_m2()
            costo_alquiler_casetones = num_casetones * caseton.precio_alquiler_dia
        else:
            num_casetones = 0
            costo_alquiler_casetones = 0
    else:
        # Default calculation
        num_casetones = area_casetones / 0.09  # Assuming 30x30 cm casetones
        costo_alquiler_casetones = num_casetones * 2.50

    # Calculate labor costs
    mano_obra_losa = area_neta * 12.40  # Reduced labor cost for ATex

    # Calculate equipment rental
    alquiler_equipo = area_neta * 2.80
    
    # Prepare APU table
    apu_tecnologia_atex = []
    consecutivo = 1

    def _unit_price(value, fallback):
        parsed = _parse_float(value, None)
        return parsed if parsed is not None else fallback
    
    # Add concrete
    precio_hormigon = _unit_price(next((p[2] for p in apu_items if 'Hormigón' in p[0]), None), 116.00)
    apu_tecnologia_atex.append({
        'consecutivo': str(consecutivo),
        'descripcion': 'Hormigón fck=25 [MPA]',
        'unidad': 'm3',
        'cantidad': f'{volumen_total:.2f}',
        'subTotal': f'{volumen_total * precio_hormigon:.2f}'
    })
    consecutivo += 1
    
    # Add steel
    precio_acero = _unit_price(next((p[2] for p in apu_items if 'Acero' in p[0]), None), 0.76)
    apu_tecnologia_atex.append({
        'consecutivo': str(consecutivo),
        'descripcion': 'Acero fck=420 [MPA]',
        'unidad': 'kg',
        'cantidad': f'{acero_total:.2f}',
        'subTotal': f'{acero_total * precio_acero:.2f}'
    })
    consecutivo += 1
    
    # Add labor
    apu_tecnologia_atex.append({
        'consecutivo': str(consecutivo),
        'descripcion': 'Mano de Obra Losa',
        'unidad': 'm2',
        'cantidad': f'{area_neta:.2f}',
        'subTotal': f'{mano_obra_losa:.2f}'
    })
    consecutivo += 1
    
    # Add caseton rental
    apu_tecnologia_atex.append({
        'consecutivo': str(consecutivo),
        'descripcion': 'Casetón (alquiler)',
        'unidad': 'unidad',
        'cantidad': f'{num_casetones:.0f}',
        'subTotal': f'{costo_alquiler_casetones:.2f}'
    })
    consecutivo += 1
    
    # Add equipment
    apu_tecnologia_atex.append({
        'consecutivo': str(consecutivo),
        'descripcion': 'Alquiler de equipo',
        'unidad': 'm2',
        'cantidad': f'{area_neta:.2f}',
        'subTotal': f'{alquiler_equipo:.2f}'
    })
    
    # Calculate totals
    total_atex = sum(float(item['subTotal'].replace(',', '.')) for item in apu_tecnologia_atex)
    
    # Calculate comparison with traditional slab
    volumen_losa_tradicional = area_neta * slab_thickness
    acero_losa_tradicional = area_neta * (slab_thickness * 10.0 + 0.15)  # More steel for traditional
    encofrado_tradicional = area_neta * 35.20  # Formwork cost
    mano_obra_tradicional = area_neta * 15.50
    
    # Traditional slab costs
    costo_hormigon_tradicional = volumen_losa_tradicional * precio_hormigon
    costo_acero_tradicional = acero_losa_tradicional * precio_acero
    costo_total_tradicional = (costo_hormigon_tradicional + costo_acero_tradicional + 
                              encofrado_tradicional + mano_obra_tradicional + alquiler_equipo)
    
    # Calculate savings
    ahorro_total = costo_total_tradicional - total_atex
    porcentaje_ahorro = (ahorro_total / costo_total_tradicional) * 100 if costo_total_tradicional > 0 else 0

    def _to_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    hv_cm = None
    hlosa_aligerada_cm = None
    hlosa_maciza_cm = None
    if isinstance(slab_geometry, dict) and slab_geometry:
        slab_type = (slab_geometry.get('type') or 'aligerada').lower()
        if slab_type == 'maciza':
            hlosa_maciza_cm = _to_float(slab_geometry.get('h_cm') or slab_geometry.get('he_cm'))
        else:
            hv_cm = _to_float(slab_geometry.get('hv_cm'))
            hf_cm = _to_float(slab_geometry.get('hf_cm'))
            hlosa_aligerada_cm = _to_float(slab_geometry.get('slab_height_cm'))
            if hlosa_aligerada_cm is None and hv_cm is not None and hf_cm is not None:
                hlosa_aligerada_cm = hv_cm + hf_cm

    if hlosa_maciza_cm is None:
        hlosa_maciza_cm = slab_thickness * 100.0 if slab_thickness else None

    if hv_cm is None:
        if caseton_height_m is not None:
            hv_cm = caseton_height_m * 100.0

    if hv_cm is None and slab_thickness:
        hv_cm = max(slab_thickness * 100.0 - 5.0, 0.0)

    if hlosa_aligerada_cm is None and hv_cm is not None:
        hlosa_aligerada_cm = hv_cm + 5.0

    if beam_height_cm is None:
        beam_height_cm = _to_float((slab_geometry or {}).get('beam_height_cm'))
    beam_height_cm = beam_height_cm if beam_height_cm is not None else 0.0
    h_vigas_m = max(beam_height_cm, 0.0) / 100.0

    apu_tecnologia_eps = []
    total_eps = None
    if hv_cm is not None and hlosa_aligerada_cm is not None:
        hv_m = hv_cm / 100.0
        h_losa_aligerada_m = hlosa_aligerada_cm / 100.0

        eps_vol_hormigon = ((area_casetones * 0.30) * hv_m) + (area_casetones * (h_losa_aligerada_m - hv_m)) + (area_vigas * h_vigas_m)
        eps_eps = (area_casetones * 0.85) * hv_m
        eps_madera = area_neta
        eps_clavos_accesorios = area_vigas
        eps_mano_de_obra = area_neta
        eps_encofrado = area_neta * 1.2
        eps_malla_electr = area_neta
        eps_acero = area_neta * 15.0
        eps_separadores = area_neta

        apu_tecnologia_eps = [
            {'consecutivo': '1', 'descripcion': 'Volumen Hormigón fck=25 [MPA]', 'unidad': 'm3', 'cantidad': f'{eps_vol_hormigon:.2f}', 'subTotal': f'{(eps_vol_hormigon * 115.94):.2f}'},
            {'consecutivo': '2', 'descripcion': 'Volumen EPS requerido', 'unidad': 'm3', 'cantidad': f'{eps_eps:.2f}', 'subTotal': f'{(eps_eps * 45.00):.2f}'},
            {'consecutivo': '3', 'descripcion': 'Madera encofrado (prorrateada)', 'unidad': 'm2', 'cantidad': f'{eps_madera:.2f}', 'subTotal': f'{(eps_madera * 2.40):.2f}'},
            {'consecutivo': '4', 'descripcion': 'Clavos y accesorios', 'unidad': 'm2', 'cantidad': f'{eps_clavos_accesorios:.2f}', 'subTotal': f'{(eps_clavos_accesorios * 0.50):.2f}'},
            {'consecutivo': '5', 'descripcion': 'Mano obra instalación', 'unidad': 'm2', 'cantidad': f'{eps_mano_de_obra:.2f}', 'subTotal': f'{(eps_mano_de_obra * 1.00):.2f}'},
            {'consecutivo': '6', 'descripcion': 'Encofrado + Mano de Obra', 'unidad': 'm2', 'cantidad': f'{eps_encofrado:.2f}', 'subTotal': f'{(eps_encofrado * 10.00):.2f}'},
            {'consecutivo': '7', 'descripcion': 'Malla electrosoldada', 'unidad': 'm2', 'cantidad': f'{eps_malla_electr:.2f}', 'subTotal': f'{(eps_malla_electr * 3.50):.2f}'},
            {'consecutivo': '8', 'descripcion': 'Acero Reforzado AP420', 'unidad': 'm2', 'cantidad': f'{eps_acero:.2f}', 'subTotal': f'{(eps_acero * 1.34):.2f}'},
            {'consecutivo': '9', 'descripcion': 'Separadores y accesorios', 'unidad': 'm2', 'cantidad': f'{eps_separadores:.2f}', 'subTotal': f'{(eps_separadores * 0.80):.2f}'},
        ]
        total_eps = sum(float(item['subTotal'].replace(',', '.')) for item in apu_tecnologia_eps)

    apu_tecnologia_postensado = []
    total_postensado = None
    if hlosa_maciza_cm is not None:
        h_losa_maciza_m = max(hlosa_maciza_cm, 0.0) / 100.0
        vol_concreto = (area_casetones * 0.110) + (area_vigas * h_vigas_m) + (area_macizos * h_losa_maciza_m)
        formaleta = area_neta
        acero_pasivo = area_neta * 8.00
        torones = area_neta * 3.00
        anclajes = area_neta * 0.16
        tesados = area_neta
        mano_obra = area_neta

        apu_tecnologia_postensado = [
            {'consecutivo': '1', 'descripcion': 'Volumen Concreto Estructural', 'unidad': 'm3', 'cantidad': f'{vol_concreto:.2f}', 'subTotal': f'{(vol_concreto * 115.94):.2f}'},
            {'consecutivo': '2', 'descripcion': 'Formaleta', 'unidad': 'm2', 'cantidad': f'{formaleta:.2f}', 'subTotal': f'{(formaleta * 12.00):.2f}'},
            {'consecutivo': '3', 'descripcion': 'Acero Pasivo', 'unidad': 'kg', 'cantidad': f'{acero_pasivo:.2f}', 'subTotal': f'{(acero_pasivo * 1.00):.2f}'},
            {'consecutivo': '4', 'descripcion': 'Torones', 'unidad': 'kg', 'cantidad': f'{torones:.2f}', 'subTotal': f'{(torones * 2.30):.2f}'},
            {'consecutivo': '5', 'descripcion': 'Anclajes', 'unidad': 'und', 'cantidad': f'{anclajes:.2f}', 'subTotal': f'{(anclajes * 20.00):.2f}'},
            {'consecutivo': '6', 'descripcion': 'Tesado', 'unidad': 'm2', 'cantidad': f'{tesados:.2f}', 'subTotal': f'{(tesados * 11.00):.2f}'},
            {'consecutivo': '7', 'descripcion': 'Mano de Obra especializada', 'unidad': 'm2', 'cantidad': f'{mano_obra:.2f}', 'subTotal': f'{(mano_obra * 45.00):.2f}'},
        ]
        total_postensado = sum(float(item['subTotal'].replace(',', '.')) for item in apu_tecnologia_postensado)
    
    conn.close()
    
    # Return results
    return {
        'texto': {
            'Moneda': country_data[0],
            'Fecha': datetime.now().strftime('%d/%m/%Y'),
            'Cambio': str(country_data[1]),
            'Obra': '',
            'Ciudad': '',
            'Pais': country,
            'Cliente': '',
            'Tipo de Obra': 'Residencial'
        },
        'tablas': {
            'APUtecnologiaAtex': apu_tecnologia_atex,
            'APUtecnologiaMaciza': [
                {
                    'consecutivo': '1',
                    'descripcion': 'Hormigón fck=25 [MPA]',
                    'unidad': 'm3',
                    'cantidad': f'{volumen_losa_tradicional:.2f}',
                    'subTotal': f'{costo_hormigon_tradicional:.2f}'
                },
                {
                    'consecutivo': '2',
                    'descripcion': 'Acero fck=420 [MPA]',
                    'unidad': 'kg',
                    'cantidad': f'{acero_losa_tradicional:.2f}',
                    'subTotal': f'{costo_acero_tradicional:.2f}'
                },
                {
                    'consecutivo': '3',
                    'descripcion': 'Mano de Obra Losa',
                    'unidad': 'm2',
                    'cantidad': f'{area_neta:.2f}',
                    'subTotal': f'{mano_obra_tradicional:.2f}'
                },
                {
                    'consecutivo': '4',
                    'descripcion': 'Encofrado Losa',
                    'unidad': 'm2',
                    'cantidad': f'{area_neta:.2f}',
                    'subTotal': f'{encofrado_tradicional:.2f}'
                },
                {
                    'consecutivo': '5',
                    'descripcion': 'Alquiler de equipo',
                    'unidad': 'm2',
                    'cantidad': f'{area_neta:.2f}',
                    'subTotal': f'{alquiler_equipo:.2f}'
                }
            ],
            'APUtecnologiaEPS': apu_tecnologia_eps,
            'APUtecnologiaPostensado': apu_tecnologia_postensado,
        },
        'resumen': {
            'areaTotal': area_total,
            'areaTotalPlano': area_total,
            'areaVaciosPlano': area_vacios,
            'areaMacizosPlano': area_macizos,
            'areaCasetonesPlano': area_casetones,
            'areaUtilCalculada': area_neta,
            'volumenHormigonAtex': volumen_total,
            'volumenHormigonMaciza': volumen_losa_tradicional,
            'aceroAtex': acero_total,
            'aceroMacizo': acero_losa_tradicional,
            'costoTotalAtex': total_atex,
            'costoTotalMacizo': costo_total_tradicional,
            'costoTotalEPS': total_eps,
            'costoTotalPostensado': total_postensado,
            'ahorroTotal': ahorro_total,
            'porcentajeAhorro': porcentaje_ahorro
        }
    }
