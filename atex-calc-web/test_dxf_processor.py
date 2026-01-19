#!/usr/bin/env python3
import sys
sys.path.append('/Users/robinklaiss/Dev/atex-calc-new/atex-calc-web')

from app.utils.dxf_processor import process_dxf_file
import json

# Test the DXF processor
try:
    result = process_dxf_file('/Users/robinklaiss/Dev/atex-calc-new/atex-calc-web/test_losa.dxf')
    print("DXF processing successful!")
    print(f"Total area: {result['areas']['superficieTotal']:.2f} m²")
    print(f"Number of casetones: {len(result['casetones'])}")
    print(f"Errors: {result['errores']}")
    if 'debug_info' in result:
        print(f"Entity counts: {result['debug_info']['entity_counts']}")
        print(f"Layers found: {result['debug_info']['layers_found']}")
except Exception as e:
    print(f"Error: {str(e)}")
