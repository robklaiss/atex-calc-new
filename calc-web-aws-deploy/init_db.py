import sqlite3
import json
import os

# Get the absolute path of the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'database', 'atex_calculations.db')

def init_database():
    """Initialize SQLite database with tables and sample data"""
    # Ensure database directory exists
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
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
        ('Panamá', 'Dólar americano', 1.0),
        ('Colombia', 'Peso colombiano', 3850.0),
        ('República Dominicana', 'Peso dominicano', 62.6),
        ('México', 'Peso mexicano', 17.0),
        ('Perú', 'Sol peruano', 3.8),
        ('Chile', 'Peso chileno', 850.0),
        ('Ecuador', 'Dólar americano', 1.0),
        ('Argentina', 'Peso argentino', 350.0),
        ('Bolivia', 'Boliviano', 6.9),
        ('Brasil', 'Real brasileño', 5.0),
        ('España', 'Euro', 0.92),
        ('Estados Unidos', 'Dólar americano', 1.0),
        ('Paraguay', 'Guaraní paraguayo', 7350.0)
    ]
    
    cursor.executemany(
        """
        INSERT INTO countries (name, currency, exchange_rate)
        VALUES (?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            currency = excluded.currency,
            exchange_rate = excluded.exchange_rate
        """,
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
        ('ATEX 800x200', 80, 80, 20, 12, 12, 0.135, 2.50),
        ('ATEX 800x250', 80, 80, 25, 12, 12, 0.150, 2.80),
        ('ATEX 800x300', 80, 80, 30, 12, 12, 0.169, 3.00),
        ('ATEX 800x350', 80, 80, 35, 12, 12, 0.196, 3.20),
        ('ATEX 800x400', 80, 80, 40, 12, 12, 0.229, 3.40),
        ('ATEX 1000x200', 100, 100, 20, 12, 12, 0.150, 3.50),
        ('ATEX 1000x250', 100, 100, 25, 12, 12, 0.175, 3.80),
        ('ATEX 1000x300', 100, 100, 30, 12, 12, 0.200, 4.10),
        ('ATEX 1000x350', 100, 100, 35, 12, 12, 0.230, 4.40),
        ('ATEX 1000x400', 100, 100, 40, 12, 12, 0.265, 4.70)
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
