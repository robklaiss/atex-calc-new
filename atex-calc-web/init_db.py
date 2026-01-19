import sqlite3
import json

def init_database():
    """Initialize SQLite database with tables and sample data"""
    conn = sqlite3.connect('database/atex_calculations.db')
    cursor = conn.cursor()
    
    # Create countries table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            currency TEXT NOT NULL,
            exchange_rate REAL NOT NULL
        )
    """)
    
    # Insert sample countries
    countries = [
        ('Colombia', 'Peso colombiano', 3850.0),
        ('México', 'Peso mexicano', 17.0),
        ('Perú', 'Sol peruano', 3.8),
        ('Chile', 'Peso chileno', 850.0),
        ('Ecuador', 'Dólar americano', 1.0),
        ('Argentina', 'Peso argentino', 350.0),
        ('Brasil', 'Real brasileño', 5.0),
        ('España', 'Euro', 0.92),
        ('Estados Unidos', 'Dólar americano', 1.0),
        ('Paraguay', 'Guaraní paraguayo', 7350.0)
    ]
    
    cursor.executemany(
        "INSERT OR IGNORE INTO countries (name, currency, exchange_rate) VALUES (?, ?, ?)",
        countries
    )
    
    # Create casetones table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS casetones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            side1 REAL NOT NULL,
            side2 REAL NOT NULL,
            height REAL NOT NULL,
            bw REAL NOT NULL,
            bs REAL NOT NULL,
            consumption REAL NOT NULL,
            rental_price REAL NOT NULL
        )
    """)
    
    # Insert sample casetones
    casetones = [
        ('Casetón 30x30', 30, 30, 20, 5, 5, 0.085, 2.50),
        ('Casetón 40x40', 40, 40, 25, 6, 6, 0.110, 3.20),
        ('Casetón 50x50', 50, 50, 30, 7, 7, 0.135, 4.00),
        ('Casetón 60x60', 60, 60, 35, 8, 8, 0.160, 4.80),
        ('Casetón 70x70', 70, 70, 40, 9, 9, 0.185, 5.60),
        ('Casetón 80x80', 80, 80, 45, 10, 10, 0.210, 6.40),
        ('Casetón 90x90', 90, 90, 50, 11, 11, 0.235, 7.20),
        ('Casetón 100x100', 100, 100, 55, 12, 12, 0.260, 8.00)
    ]
    
    cursor.executemany(
        "INSERT OR IGNORE INTO casetones (name, side1, side2, height, bw, bs, consumption, rental_price) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        casetones
    )
    
    # Create calculations table for saved calculations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS calculations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            country TEXT NOT NULL,
            date TEXT NOT NULL,
            data TEXT NOT NULL,
            results TEXT NOT NULL
        )
    """)
    
    # Create APU (Análisis de Precios Unitarios) table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS apu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL,
            technology TEXT NOT NULL,
            description TEXT NOT NULL,
            unit TEXT NOT NULL,
            unit_price REAL NOT NULL
        )
    """)
    
    # Insert sample APU items for Colombia
    apu_items_colombia = [
        ('Colombia', 'Maciza', 'Hormigón fck=25 [MPA]', 'm3', 116.00),
        ('Colombia', 'Maciza', 'Acero fck=420 [MPA]', 'kg', 0.76),
        ('Colombia', 'Maciza', 'Mano de Obra Losa', 'm2', 15.50),
        ('Colombia', 'Maciza', 'Encofrado Losa', 'm2', 35.20),
        ('Colombia', 'Maciza', 'Alquiler de equipo', 'm2', 2.80),
        ('Colombia', 'Atex', 'Hormigón fck=25 [MPA]', 'm3', 116.00),
        ('Colombia', 'Atex', 'Acero fck=420 [MPA]', 'kg', 0.76),
        ('Colombia', 'Atex', 'Mano de Obra Losa', 'm2', 12.40),
        ('Colombia', 'Atex', 'Casetón (alquiler)', 'unidad', 2.50),
        ('Colombia', 'Atex', 'Alquiler de equipo', 'm2', 2.80),
        ('Colombia', 'ePlaca', 'Hormigón fck=25 [MPA]', 'm3', 116.00),
        ('Colombia', 'ePlaca', 'Acero fck=420 [MPA]', 'kg', 0.76),
        ('Colombia', 'ePlaca', 'Mano de Obra Losa', 'm2', 14.00),
        ('Colombia', 'ePlaca', 'Alquiler de equipo', 'm2', 2.80)
    ]
    
    cursor.executemany(
        "INSERT OR IGNORE INTO apu_items (country, technology, description, unit, unit_price) VALUES (?, ?, ?, ?, ?)",
        apu_items_colombia
    )
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_database()
