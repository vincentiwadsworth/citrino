#!/usr/bin/env python3
"""
Add sample services to test spatial queries
"""
import sys
import os
sys.path.append('migration/config')

from database_config import create_connection

def add_sample_services():
    """Add sample urban services"""
    print("Adding sample urban services...")

    conn = create_connection()
    cursor = conn.cursor()

    sample_services = [
        {
            'nombre': 'Colegio San Agustín',
            'tipo': 'Educación',
            'zona': 'Equipetrol',
            'direccion': 'Avenida Equipetrol #500',
            'descripcion': 'Colegio primario y secundario privado'
        },
        {
            'nombre': 'Centro Comercial Las Brisas',
            'tipo': 'Comercio',
            'zona': 'Urbar',
            'direccion': 'Calle Urbar #100',
            'descripcion': 'Centro comercial con tiendas y restaurantes'
        },
        {
            'nombre': 'Policía Nacional',
            'tipo': 'Seguridad',
            'zona': 'Centro',
            'direccion': 'Plaza Principal s/n',
            'descripcion': 'Comisaría de policía central'
        },
        {
            'nombre': 'Banco Unión',
            'tipo': 'Finanzas',
            'zona': 'Equipetrol',
            'direccion': 'Avenida Equipetrol #200',
            'descripcion': 'Agencia bancaria con cajeros automáticos'
        },
        {
            'nombre': 'Clínica Alemana',
            'tipo': 'Salud',
            'zona': 'Sopocachi',
            'direccion': 'Avenida Sopocachi #300',
            'descripcion': 'Clínica privada con servicios de urgencias'
        }
    ]

    try:
        for service in sample_services:
            query = """
            INSERT INTO servicios (nombre, tipo, zona, direccion, descripcion)
            VALUES (%s, %s, %s, %s, %s)
            """

            cursor.execute(query, (
                service['nombre'], service['tipo'], service['zona'],
                service['direccion'], service['descripcion']
            ))

            print(f"OK: Added service - {service['nombre']} ({service['tipo']})")

        conn.commit()

        # Verify services
        cursor.execute("SELECT COUNT(*) FROM servicios")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT tipo, COUNT(*) FROM servicios GROUP BY tipo ORDER BY COUNT(*) DESC")
        tipos = cursor.fetchall()

        print(f"\n=== SERVICES SUMMARY ===")
        print(f"Total services in database: {total}")
        print("Services by type:")
        for tipo, count in tipos:
            print(f"  - {tipo}: {count} services")

    except Exception as e:
        print(f"ERROR adding services: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_sample_services()