#!/usr/bin/env python3
import ezdxf
import sys

def analyze_dxf(filepath):
    """Analyze a DXF file and show all layers and entities"""
    try:
        doc = ezdxf.readfile(filepath)
        msp = doc.modelspace()
        
        print(f"\nAnálisis del archivo: {filepath}")
        print("=" * 50)
        
        # Get all layers
        layers = set()
        entity_counts = {}
        closed_polylines = {}
        
        for entity in msp:
            entity_type = entity.dxftype()
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
            
            if hasattr(entity.dxf, 'layer'):
                layers.add(entity.dxf.layer)
                
                # Check for closed polylines
                if entity_type in ["LWPOLYLINE", "POLYLINE"]:
                    layer = entity.dxf.layer
                    if layer not in closed_polylines:
                        closed_polylines[layer] = []
                    
                    if entity_type == "LWPOLYLINE":
                        is_closed = entity.closed
                        points = len(entity.get_points())
                    else:
                        is_closed = entity.is_closed if hasattr(entity, 'is_closed') else entity.closed
                        points = len(list(entity.vertices))
                    
                    closed_polylines[layer].append({
                        'closed': is_closed,
                        'points': points
                    })
        
        print(f"\nCapas encontradas ({len(layers)}):")
        for layer in sorted(layers):
            print(f"  - {layer}")
        
        print(f"\nTipos de entidades:")
        for entity_type, count in sorted(entity_counts.items()):
            print(f"  - {entity_type}: {count}")
        
        print(f"\nPolilíneas cerradas por capa:")
        for layer, polylines in sorted(closed_polylines.items()):
            closed_count = sum(1 for p in polylines if p['closed'])
            total_count = len(polylines)
            print(f"  - {layer}: {closed_count}/{total_count} cerradas")
            
            # Show details for non-closed polylines
            for i, p in enumerate(polylines):
                if not p['closed']:
                    print(f"    * Polilínea {i+1}: {p['points']} puntos (abierta)")
        
        # Suggest possible mappings
        print(f"\nSugerencias de mapeo:")
        layer_lower = [l.lower() for l in layers]
        
        for layer in sorted(layers):
            lower = layer.lower()
            suggestions = []
            
            if any(word in lower for word in ['total', 'contorno', 'perimetro', 'borde', 'general']):
                suggestions.append("superficieTotal")
            if any(word in lower for word in ['caseton', 'nervio', 'viga', 'reticula']):
                suggestions.append("superficieCasetones")
            if any(word in lower for word in ['macizo', 'sólido', 'solido', 'viga']):
                suggestions.append("superficieMacizos")
            if any(word in lower for word in ['vacio', 'hueco', 'abertura']):
                suggestions.append("superficieVacios")
            
            if suggestions:
                print(f"  - '{layer}' podría ser: {', '.join(suggestions)}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_dxf(sys.argv[1])
    else:
        print("Uso: python analyze_dxf.py <archivo.dxf>")
