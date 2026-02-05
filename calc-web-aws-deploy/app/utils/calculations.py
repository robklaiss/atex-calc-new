import math
import sqlite3
from datetime import datetime

class Caseton:
    """Represents a waffle slab form (caseton)"""
    def __init__(self, nombre, lado1, lado2, altura, bw, bs, consumo_base, precio_alquiler_dia):
        self.nombre = nombre
        self.lado1 = lado1  # cm
        self.lado2 = lado2  # cm
        self.altura = altura  # cm
        self.bw = bw  # cm
        self.bs = bs  # cm
        self.consumo_base = consumo_base  # m3/m2 for 5cm slab
        self.precio_alquiler_dia = precio_alquiler_dia
    
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
                             database_path=None):
    """Calculate quantities for ATex system"""
    
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
    
    # Calculate areas
    area_total = geometry_data.get('areas', {}).get('superficieTotal', 0)
    area_casetones = sum(c['area'] for c in geometry_data.get('casetones', []))
    area_macizos = geometry_data.get('areas', {}).get('superficieMacizos', {}).get('total', 0)
    area_vacios = geometry_data.get('areas', {}).get('superficieVacios', {}).get('total', 0)
    
    # Calculate concrete volume
    # Base slab (5cm) + waffle portion
    volumen_base = area_total * 0.05  # 5cm base slab
    volumen_casetones = area_casetones * (slab_thickness - 0.05) * 0.4  # 40% efficiency
    volumen_macizos = area_macizos * slab_thickness
    volumen_total = volumen_base + volumen_casetones + volumen_macizos
    
    # Calculate steel reinforcement
    # Typical reinforcement: 0.15 kg/m2 for 5cm slab + additional for thickness
    refuerzo_base = area_total * 0.15
    refuerzo_adicional = area_total * (slab_thickness - 0.05) * 8.0  # kg/m2 per cm of thickness
    acero_total = refuerzo_base + refuerzo_adicional
    
    # Calculate formwork (casetones)
    if selected_caseton:
        cursor.execute("SELECT * FROM casetones WHERE id = ?", (selected_caseton,))
        caseton_data = cursor.fetchone()
        if caseton_data:
            caseton = Caseton(*caseton_data[1:])
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
    mano_obra_losa = area_total * 12.40  # Reduced labor cost for ATex
    
    # Calculate equipment rental
    alquiler_equipo = area_total * 2.80
    
    # Prepare APU table
    apu_tecnologia_atex = []
    consecutivo = 1
    
    # Add concrete
    precio_hormigon = next((p[2] for p in apu_items if 'Hormigón' in p[0]), 116.00)
    apu_tecnologia_atex.append({
        'consecutivo': str(consecutivo),
        'descripcion': 'Hormigón fck=25 [MPA]',
        'unidad': 'm3',
        'cantidad': f'{volumen_total:.2f}',
        'subTotal': f'{volumen_total * precio_hormigon:.2f}'
    })
    consecutivo += 1
    
    # Add steel
    precio_acero = next((p[2] for p in apu_items if 'Acero' in p[0]), 0.76)
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
        'cantidad': f'{area_total:.2f}',
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
        'cantidad': f'{area_total:.2f}',
        'subTotal': f'{alquiler_equipo:.2f}'
    })
    
    # Calculate totals
    total_atex = sum(float(item['subTotal'].replace(',', '.')) for item in apu_tecnologia_atex)
    
    # Calculate comparison with traditional slab
    volumen_losa_tradicional = area_total * slab_thickness
    acero_losa_tradicional = area_total * (slab_thickness * 10.0 + 0.15)  # More steel for traditional
    encofrado_tradicional = area_total * 35.20  # Formwork cost
    mano_obra_tradicional = area_total * 15.50
    
    # Traditional slab costs
    costo_hormigon_tradicional = volumen_losa_tradicional * precio_hormigon
    costo_acero_tradicional = acero_losa_tradicional * precio_acero
    costo_total_tradicional = (costo_hormigon_tradicional + costo_acero_tradicional + 
                              encofrado_tradicional + mano_obra_tradicional + alquiler_equipo)
    
    # Calculate savings
    ahorro_total = costo_total_tradicional - total_atex
    porcentaje_ahorro = (ahorro_total / costo_total_tradicional) * 100 if costo_total_tradicional > 0 else 0
    
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
                    'cantidad': f'{area_total:.2f}',
                    'subTotal': f'{mano_obra_tradicional:.2f}'
                },
                {
                    'consecutivo': '4',
                    'descripcion': 'Encofrado Losa',
                    'unidad': 'm2',
                    'cantidad': f'{area_total:.2f}',
                    'subTotal': f'{encofrado_tradicional:.2f}'
                },
                {
                    'consecutivo': '5',
                    'descripcion': 'Alquiler de equipo',
                    'unidad': 'm2',
                    'cantidad': f'{area_total:.2f}',
                    'subTotal': f'{alquiler_equipo:.2f}'
                }
            ]
        },
        'resumen': {
            'areaTotal': area_total,
            'volumenHormigonAtex': volumen_total,
            'volumenHormigonMaciza': volumen_losa_tradicional,
            'aceroAtex': acero_total,
            'aceroMacizo': acero_losa_tradicional,
            'costoTotalAtex': total_atex,
            'costoTotalMacizo': costo_total_tradicional,
            'ahorroTotal': ahorro_total,
            'porcentajeAhorro': porcentaje_ahorro
        }
    }
