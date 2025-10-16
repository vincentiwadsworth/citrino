#!/usr/bin/env python3
"""
Test simple de conexión a PostgreSQL
"""

import psycopg2
import os
import sys

def test_connection():
    """Probar conexión a PostgreSQL"""
    try:
        # Configuración
        db_config = {
            'host': 'localhost',
            'database': 'citrino',
            'user': 'citrino_app',
            'password': 'citrino123',
            'port': '5432'
        }

        print("Intentando conectar a PostgreSQL...")
        print(f"Host: {db_config['host']}")
        print(f"Database: {db_config['database']}")
        print(f"User: {db_config['user']}")
        print(f"Port: {db_config['port']}")

        # Establecer conexión con manejo de encoding
        conn = psycopg2.connect(**db_config)
        conn.set_client_encoding('LATIN1')  # Cambiar encoding para evitar problemas

        cursor = conn.cursor()

        # Probar query simple
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"Conexión exitosa!")
        print(f"PostgreSQL version: {version}")

        # Contar propiedades
        cursor.execute("SELECT COUNT(*) FROM propiedades;")
        count = cursor.fetchone()[0]
        print(f"Propiedades en BD: {count}")

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"Error de conexión: {e}")
        return False

if __name__ == '__main__':
    test_connection()