#!/usr/bin/env python3
"""
Simple test for property migration using Docker wrapper
"""
import sys
import os
sys.path.append('migration/config')
sys.path.append('migration/scripts')

from database_config import create_connection

def test_simple_insert():
    """Test inserting a simple property record"""
    conn = create_connection()
    cursor = conn.cursor()

    # Insertar una propiedad de prueba
    query = """
    INSERT INTO propiedades (titulo, precio_usd, zona, url, coordenadas_validas, datos_completos)
    VALUES (%s, %s, %s, %s, %s, %s)
    """

    try:
        cursor.execute(query, (
            'Test Property Migration',
            150000.00,
            'Equipetrol',
            'https://test.com/property/1',
            True,
            True
        ))
        conn.commit()
        print("Property inserted successfully!")

        # Verificar inserción
        cursor.execute("SELECT COUNT(*) FROM propiedades")
        count = cursor.fetchone()[0]
        print(f"Total properties: {count}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_simple_insert()