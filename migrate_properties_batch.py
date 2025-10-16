#!/usr/bin/env python3
"""
Simplified batch migration for properties extracted by ETL
"""
import sys
import os
sys.path.append('migration/config')

from database_config import create_connection
import pandas as pd
from pathlib import Path

def migrate_sample_properties():
    """Migrate a sample of properties to test the system"""
    print("Starting simplified property migration...")

    conn = create_connection()
    cursor = conn.cursor()

    # Create a sample property with realistic data
    sample_properties = [
        {
            'titulo': 'Departamento en Equipetrol - 2 Dormitorios',
            'precio_usd': 125000.00,
            'tipo_propiedad': 'Departamento',
            'zona': 'Equipetrol',
            'direccion': 'Avenida Equipetrol, Santa Cruz',
            'superficie_total': 120.50,
            'superficie_construida': 85.00,
            'num_dormitorios': 2,
            'num_banios': 2,
            'num_garajes': 1,
            'descripcion': 'Hermoso departamento en excelente ubicacion',
            'url': 'https://example.com/prop/1',
            'proveedor_datos': 'test_migration',
            'coordenadas_validas': True,
            'datos_completos': True
        },
        {
            'titulo': 'Casa en Urbar - 3 Dormitorios con Jardín',
            'precio_usd': 250000.00,
            'tipo_propiedad': 'Casa',
            'zona': 'Urbar',
            'direccion': 'Calle Urbar, Santa Cruz',
            'superficie_total': 280.00,
            'superficie_construida': 180.00,
            'num_dormitorios': 3,
            'num_banios': 3,
            'num_garajes': 2,
            'descripcion': 'Espaciosa casa familiar con jardin privado',
            'url': 'https://example.com/prop/2',
            'proveedor_datos': 'test_migration',
            'coordenadas_validas': True,
            'datos_completos': True
        },
        {
            'titulo': 'Oficina en Centro - Ideal para Negocios',
            'precio_usd': 95000.00,
            'tipo_propiedad': 'Oficina',
            'zona': 'Centro',
            'direccion': 'Centro Histórico, Santa Cruz',
            'superficie_total': 65.00,
            'superficie_construida': 65.00,
            'num_dormitorios': 0,
            'num_banios': 1,
            'num_garajes': 0,
            'descripcion': 'Oficina comercial en zona estratégica',
            'url': 'https://example.com/prop/3',
            'proveedor_datos': 'test_migration',
            'coordenadas_validas': True,
            'datos_completos': True
        }
    ]

    try:
        for i, prop in enumerate(sample_properties, 1):
            query = """
            INSERT INTO propiedades (
                titulo, precio_usd, tipo_propiedad, zona, direccion,
                superficie_total, superficie_construida, num_dormitorios,
                num_banios, num_garajes, descripcion, url, proveedor_datos,
                coordenadas_validas, datos_completos
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            cursor.execute(query, (
                prop['titulo'], prop['precio_usd'], prop['tipo_propiedad'],
                prop['zona'], prop['direccion'], prop['superficie_total'],
                prop['superficie_construida'], prop['num_dormitorios'],
                prop['num_banios'], prop['num_garajes'], prop['descripcion'],
                prop['url'], prop['proveedor_datos'], prop['coordenadas_validas'],
                prop['datos_completos']
            ))

            print(f"OK: Inserted property {i}: {prop['titulo']}")

        conn.commit()

        # Verify insertion
        cursor.execute("SELECT COUNT(*) FROM propiedades")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT zona, COUNT(*) FROM propiedades GROUP BY zona")
        zonas = cursor.fetchall()

        print(f"\n=== MIGRATION SUMMARY ===")
        print(f"Total properties in database: {total}")
        print("Properties by zone:")
        for zona, count in zonas:
            print(f"  - {zona}: {count} properties")

    except Exception as e:
        print(f"ERROR during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_sample_properties()