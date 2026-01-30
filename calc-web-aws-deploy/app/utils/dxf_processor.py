import json
import os
import ezdxf
from shapely.geometry import Polygon
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_dxf_file(filepath):
    """Process DXF file and extract slab geometry"""
    try:
        # Configuration of layers - include common variations
        LAYER_MAPPING = {
            # Spanish variations
            "superficieTotal": ["superficieTotal", "superficie_total", "SuperficieTotal", "TOTAL", "total", "contorno", "perimetro"],
            "superficieVacios": ["superficieVacios", "superficie_vacios", "SuperficieVacios", "VACIOS", "vacios", "huecos"],
            "superficieMacizos": ["superficieMacizos", "superficie_macizos", "SuperficieMacizos", "MACIZOS", "macizos", "solidos"],
            "superficieCasetones": ["superficieCasetones", "superficie_casetones", "SuperficieCasetones", "CASETONES", "casetones", "nervios"]
        }
        
        # Initialize layers dictionary
        LAYERS = {
            "superficieTotal": [],
            "superficieVacios": [],
            "superficieMacizos": [],
            "superficieCasetones": []
        }
        
        # Read DXF
        logger.info(f"Reading DXF file: {filepath}")
        doc = ezdxf.readfile(filepath)
        msp = doc.modelspace()
        
        # Count entities by type for debugging
        entity_counts = {}
        found_layers = set()
        
        for entity in msp:
            entity_type = entity.dxftype()
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
            
            # Get layer name
            if hasattr(entity.dxf, 'layer'):
                layer = entity.dxf.layer
                found_layers.add(layer)
                
                # Check if this layer matches any of our expected layers
                for target_layer, variations in LAYER_MAPPING.items():
                    if layer in variations:
                        if entity_type in ["LWPOLYLINE", "POLYLINE"]:
                            try:
                                if entity_type == "LWPOLYLINE":
                                    puntos = [(p[0], p[1]) for p in entity.get_points()]
                                    is_closed = entity.closed
                                else:  # POLYLINE
                                    puntos = [(p[0], p[1]) for p in entity.vertices]
                                    is_closed = entity.is_closed if hasattr(entity, 'is_closed') else entity.closed
                                
                                if is_closed and len(puntos) >= 3:
                                    poly = Polygon(puntos)
                                    if poly.is_valid:
                                        LAYERS[target_layer].append(poly)
                                        logger.info(f"Added polygon to {target_layer} from layer '{layer}': {len(puntos)} points, area={poly.area:.2f}")
                                    else:
                                        logger.warning(f"Invalid polygon in layer '{layer}'")
                                else:
                                    logger.warning(f"Entity not closed or insufficient points in layer '{layer}'")
                            except Exception as e:
                                logger.error(f"Error processing entity in layer '{layer}': {str(e)}")
                        
                        # Also check for CIRCLE entities that might represent casetones
                        elif entity_type == "CIRCLE" and target_layer == "superficieCasetones":
                            try:
                                center = entity.dxf.center
                                radius = entity.dxf.radius
                                # Approximate circle as polygon with many points
                                import math
                                num_points = 32
                                puntos = []
                                for i in range(num_points):
                                    angle = 2 * math.pi * i / num_points
                                    x = center[0] + radius * math.cos(angle)
                                    y = center[1] + radius * math.sin(angle)
                                    puntos.append((x, y))
                                
                                poly = Polygon(puntos)
                                if poly.is_valid:
                                    LAYERS[target_layer].append(poly)
                                    logger.info(f"Added circle to {target_layer} from layer '{layer}': radius={radius:.2f}, area={poly.area:.2f}")
                            except Exception as e:
                                logger.error(f"Error processing circle in layer '{layer}': {str(e)}")
        
        logger.info(f"Entity types found: {entity_counts}")
        logger.info(f"All layers found in DXF: {sorted(found_layers)}")
        
        # Validations
        errors = []
        warnings = []
        
        if len(LAYERS["superficieTotal"]) != 1:
            errors.append(f"Debe existir exactamente un polígono en superficieTotal (encontrados: {len(LAYERS['superficieTotal'])})")
            # Suggest possible matching layers
            possible_total_layers = [l for l in found_layers if any(v in l.lower() for v in ['total', 'contorno', 'perimetro', 'borde'])]
            if possible_total_layers:
                warnings.append(f"Capas que podrían ser superficieTotal: {', '.join(possible_total_layers)}")
        
        if len(LAYERS["superficieCasetones"]) < 1:
            errors.append(f"Debe existir al menos un polígono en superficieCasetones (encontrados: {len(LAYERS['superficieCasetones'])})")
            # Suggest possible matching layers
            possible_caseton_layers = [l for l in found_layers if any(v in l.lower() for v in ['caseton', 'nervio', 'viga'])]
            if possible_caseton_layers:
                warnings.append(f"Capas que podrían ser superficieCasetones: {', '.join(possible_caseton_layers)}")
        
        # Log layer information
        for layer_name, polygons in LAYERS.items():
            logger.info(f"Layer {layer_name}: {len(polygons)} polygons")
        
        # Process casetones
        casetones_info = []
        
        for i, poly in enumerate(LAYERS["superficieCasetones"], start=0):
            minx, miny, maxx, maxy = poly.bounds
            
            info = {
                "id": i,
                "x_min": minx,
                "x_max": maxx,
                "distX": maxx - minx,
                "y_min": miny,
                "y_max": maxy,
                "distY": maxy - miny,
                "area": poly.area
            }
            casetones_info.append(info)
        
        # Calculate void and solid areas
        areas_vacios = [p.area for p in LAYERS["superficieVacios"]]
        areas_macizos = [p.area for p in LAYERS["superficieMacizos"]]
        
        area_total_vacios = sum(areas_vacios)
        area_total_macizos = sum(areas_macizos)
        
        # Prepare output
        salida = {
            "areas": {
                "superficieTotal": LAYERS["superficieTotal"][0].area if LAYERS["superficieTotal"] else 0.0,
                "superficieVacios": {
                    "individuales": areas_vacios,
                    "total": area_total_vacios
                },
                "superficieMacizos": {
                    "individuales": areas_macizos,
                    "total": area_total_macizos
                }
            },
            "casetones": casetones_info,
            "errores": errors,
            "warnings": warnings,
            "debug_info": {
                "entity_counts": entity_counts,
                "layers_found": sorted(found_layers),
                "layer_mapping": LAYER_MAPPING
            }
        }
        
        # Serialize geometries
        def serializar_poligonos(polys):
            salida = []
            for i, poly in enumerate(polys, start=0):
                salida.append({
                    "id": i,
                    "coordenadas": list(poly.exterior.coords)
                })
            return salida
        
        geometria = {
            "superficieTotal": serializar_poligonos(LAYERS["superficieTotal"]),
            "superficieVacios": serializar_poligonos(LAYERS["superficieVacios"]),
            "superficieMacizos": serializar_poligonos(LAYERS["superficieMacizos"]),
            "superficieCasetones": serializar_poligonos(LAYERS["superficieCasetones"])
        }
        
        salida["geometria"] = geometria
        
        logger.info(f"DXF processing completed. Errors: {len(errors)}, Warnings: {len(warnings)}")
        return salida
        
    except Exception as e:
        logger.error(f"Error processing DXF file: {str(e)}")
        raise Exception(f"Error al procesar archivo DXF: {str(e)}")
