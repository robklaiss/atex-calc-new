import ezdxf

# Create a new DXF document
doc = ezdxf.new('R2010')
msp = doc.modelspace()

# Create total surface polygon (rectangle)
total_points = [(0, 0), (10, 0), (10, 8), (0, 8), (0, 0)]
msp.add_lwpolyline(total_points, close=True, dxfattribs={'layer': 'superficieTotal'})

# Create caseton polygons (squares)
caseton_positions = [(1, 1), (4, 1), (7, 1), (1, 4), (4, 4), (7, 4)]
for x, y in caseton_positions:
    caseton_points = [(x, y), (x+2, y), (x+2, y+2), (x, y+2), (x, y)]
    msp.add_lwpolyline(caseton_points, close=True, dxfattribs={'layer': 'superficieCasetones'})

# Create solid areas
solid_points1 = [(0, 6), (10, 6), (10, 8), (0, 8), (0, 6)]
msp.add_lwpolyline(solid_points1, close=True, dxfattribs={'layer': 'superficieMacizos'})

solid_points2 = [(0, 0), (1, 0), (1, 6), (0, 6), (0, 0)]
msp.add_lwpolyline(solid_points2, close=True, dxfattribs={'layer': 'superficieMacizos'})

# Save the file
doc.saveas('test_losa.dxf')
print("Test DXF file created: test_losa.dxf")
