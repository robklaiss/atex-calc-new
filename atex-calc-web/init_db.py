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
            system TEXT NOT NULL,
            consumption REAL NOT NULL,
            rental_price REAL NOT NULL
        )
    """)

    # Ensure legacy tables include the system column
    cursor.execute("PRAGMA table_info(casetones)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    if 'system' not in existing_columns:
        cursor.execute("ALTER TABLE casetones ADD COLUMN system TEXT DEFAULT 'bidireccional'")
    
    # Reset casetones data with canonical list
    cursor.execute("DELETE FROM casetones")

    # Insert sample casetones
    casetones = [
        # Bidireccional families
        ('610x210', 61.0, 61.0, 21.0, 7.0, 12.2, 'bidireccional', 0.111, 0.12),
        ('610x260', 61.0, 61.0, 26.0, 7.0, 14.8, 'bidireccional', 0.135, 0.12),
        ('610x300', 61.0, 61.0, 30.0, 7.0, 17.2, 'bidireccional', 0.157, 0.12),
        ('660x180', 66.0, 66.0, 18.0, 12.0, 15.0, 'bidireccional', 0.116, 0.12),
        ('660x210', 66.0, 66.0, 21.0, 12.0, 17.2, 'bidireccional', 0.133, 0.12),
        ('660x260', 66.0, 66.0, 26.0, 12.0, 19.7, 'bidireccional', 0.160, 0.12),
        ('660x300', 66.0, 66.0, 30.0, 12.0, 22.2, 'bidireccional', 0.185, 0.12),
        ('700x260', 70.0, 70.0, 26.0, 12.0, 16.4, 'bidireccional', 0.145, 0.12),
        ('800x200', 80.0, 80.0, 20.0, 12.5, 15.6, 'bidireccional', 0.114, 0.12),
        ('800x250', 80.0, 80.0, 25.0, 12.5, 17.1, 'bidireccional', 0.134, 0.12),
        ('800x300', 80.0, 80.0, 30.0, 12.5, 20.0, 'bidireccional', 0.159, 0.12),
        ('800x350', 80.0, 80.0, 35.0, 12.5, 22.5, 'bidireccional', 0.186, 0.12),
        ('800x400', 80.0, 80.0, 40.0, 12.5, 25.8, 'bidireccional', 0.219, 0.12),
        # Unidireccional families
        ('610Ux210', 61.0, 61.0, 21.0, 7.0, 12.2, 'unidireccional', 0.083, 0.12),
        ('610Ux260', 61.0, 61.0, 26.0, 7.0, 14.8, 'unidireccional', 0.096, 0.12),
        ('610Ux300', 61.0, 61.0, 30.0, 7.0, 17.2, 'unidireccional', 0.110, 0.12),
        ('655Ux180', 70.0, 65.5, 18.0, 11.5, 14.4, 'unidireccional', 0.086, 0.12),
        ('655Ux210', 70.0, 65.5, 21.0, 11.5, 16.7, 'unidireccional', 0.095, 0.12),
        ('655Ux260', 70.0, 65.5, 26.0, 11.5, 19.3, 'unidireccional', 0.111, 0.12),
        ('655Ux300', 70.0, 65.5, 30.0, 11.5, 21.7, 'unidireccional', 0.126, 0.12),
        ('755Ux200', 80.0, 75.5, 20.0, 8.0, 11.1, 'unidireccional', 0.075, 0.12),
        ('755Ux250', 80.0, 75.5, 25.0, 8.0, 12.6, 'unidireccional', 0.084, 0.12),
        ('755Ux300', 80.0, 75.5, 30.0, 8.0, 15.5, 'unidireccional', 0.097, 0.12),
        ('755Ux350', 80.0, 75.5, 35.0, 8.0, 18.0, 'unidireccional', 0.110, 0.12),
        ('755Ux400', 80.0, 75.5, 40.0, 8.0, 21.3, 'unidireccional', 0.128, 0.12),
    ]
    
    cursor.executemany(
        "INSERT OR IGNORE INTO casetones (name, side1, side2, height, bw, bs, system, consumption, rental_price) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
