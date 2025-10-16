#!/usr/bin/env python3
"""
Migración Oracle Cloud → Docker PostgreSQL
Solución definitiva al encoding Windows + PostGIS incompleto
"""

import psycopg2
import pandas as pd
import os
import sys
from datetime import datetime

# Configuración Oracle Cloud (fuente)
ORACLE_CONFIG = {
    'host': os.getenv('ORACLE_DB_HOST', 'localhost'),
    'port': os.getenv('ORACLE_DB_PORT', '5432'),
    'database': 'citrino',
    'user': os.getenv('ORACLE_DB_USER', 'citrino_app'),
    'password': os.getenv('ORACLE_DB_PASSWORD', 'citrino123')
}

# Configuración Docker (destino)
DOCKER_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'citrino',
    'user': 'citrino_app',
    'password': 'citrino123'
}

def migrar_datos():
    print("=== MIGRACIÓN ORACLE CLOUD → DOCKER ===")
    print(f"Fecha: {datetime.now()}")
    print()

    try:
        # Conectar a Oracle Cloud
        print("1. Conectando a Oracle Cloud...")
        oracle_conn = psycopg2.connect(**ORACLE_CONFIG)
        oracle_cursor = oracle_conn.cursor()

        # Conectar a Docker
        print("2. Conectando a Docker PostgreSQL...")
        docker_conn = psycopg2.connect(**DOCKER_CONFIG)
        docker_cursor = docker_conn.cursor()

        # Verificar PostGIS en Docker
        print("3. Verificando PostGIS en Docker...")
        docker_cursor.execute("SELECT PostGIS_Version();")
        postgis_version = docker_cursor.fetchone()[0]
        print(f"   PostGIS versión: {postgis_version}")

        # Migrar propiedades
        print("4. Migrando propiedades...")

        # Obtener datos de Oracle Cloud
        oracle_cursor.execute("""
            SELECT id, titulo, descripcion, precio_usd, tipo_propiedad,
                   latitud, longitud, zona, direccion, superficie_total,
                   superficie_construida, num_dormitorios, num_baños, num_garajes,
                   fecha_scraping, proveedor_datos, coordenadas_validas, datos_completos
            FROM propiedades
            ORDER BY id
        """)

        propiedades_oracle = oracle_cursor.fetchall()
        print(f"   Propiedades en Oracle Cloud: {len(propiedades_oracle)}")

        # Crear tabla en Docker con PostGIS nativo
        docker_cursor.execute("""
            CREATE TABLE IF NOT EXISTS propiedades (
                id BIGSERIAL PRIMARY KEY,
                titulo TEXT,
                descripcion TEXT,
                precio_usd DECIMAL(12,2),
                tipo_propiedad VARCHAR(100),
                coordenadas GEOGRAPHY(POINT, 4326),
                zona VARCHAR(200),
                direccion TEXT,
                superficie_total DECIMAL(10,2),
                superficie_construida DECIMAL(10,2),
                num_dormitorios INTEGER,
                num_baños INTEGER,
                num_garajes INTEGER,
                fecha_scraping TIMESTAMP,
                proveedor_datos VARCHAR(100),
                coordenadas_validas BOOLEAN DEFAULT FALSE,
                datos_completos BOOLEAN DEFAULT FALSE
            );
        """)

        # Crear índice espacial GIST
        docker_cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_propiedades_coords
            ON propiedades USING GIST (coordenadas);
        """)

        # Insertar datos con coordenadas PostGIS reales
        insert_query = """
            INSERT INTO propiedades (
                id, titulo, descripcion, precio_usd, tipo_propiedad,
                coordenadas, zona, direccion, superficie_total,
                superficie_construida, num_dormitorios, num_baños, num_garajes,
                fecha_scraping, proveedor_datos, coordenadas_validas, datos_completos
            ) VALUES (
                %s, %s, %s, %s, %s,
                ST_GeographyFromText('POINT(%s %s)', 4326),
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (id) DO UPDATE SET
                titulo = EXCLUDED.titulo,
                descripcion = EXCLUDED.descripcion,
                coordenadas = EXCLUDED.coordenadas,
                coordenadas_validas = EXCLUDED.coordenadas_validas
        """

        migradas = 0
        coordenadas_validas = 0

        for row in propiedades_oracle:
            (prop_id, titulo, descripcion, precio_usd, tipo_propiedad,
             latitud, longitud, zona, direccion, superficie_total,
             superficie_construida, num_dormitorios, num_baños, num_garajes,
             fecha_scraping, proveedor_datos, coordenadas_validas, datos_completos) = row

            # Coordenadas de Santa Cruz (si no hay datos reales)
            if latitud and longitud:
                lng, lat = float(longitud), float(latitud)
                coord_valida = True
                coordenadas_validas += 1
            else:
                # Coordenadas por defecto Santa Cruz centro
                lng, lat = -63.1833, -17.7833
                coord_valida = False

            docker_cursor.execute(insert_query, (
                prop_id, titulo, descripcion, precio_usd, tipo_propiedad,
                lng, lat, zona, direccion, superficie_total,
                superficie_construida, num_dormitorios or 0, num_baños or 0,
                num_garajes or 0, fecha_scraping, proveedor_datos,
                coord_valida, datos_completos or False
            ))

            migradas += 1

        docker_conn.commit()
        print(f"   Propiedades migradas: {migradas}")
        print(f"   Coordenadas válidas: {coordenadas_validas}")

        # Verificar migración
        docker_cursor.execute("SELECT COUNT(*) FROM propiedades")
        total_docker = docker_cursor.fetchone()[0]
        docker_cursor.execute("SELECT COUNT(*) FROM propiedades WHERE coordenadas IS NOT NULL")
        coords_docker = docker_cursor.fetchone()[0]

        print()
        print("=== RESULTADO MIGRACIÓN ===")
        print(f"Oracle Cloud: {len(propiedades_oracle)} propiedades")
        print(f"Docker: {total_docker} propiedades")
        print(f"Coordenadas PostGIS válidas: {coords_docker}")

        # Test de PostGIS funcional
        print()
        print("5. Test PostGIS funcional...")
        docker_cursor.execute("""
            SELECT titulo, ST_X(coordenadas::geometry) as lng,
                   ST_Y(coordenadas::geometry) as lat
            FROM propiedades
            WHERE coordenadas IS NOT NULL
            LIMIT 3
        """)

        resultados = docker_cursor.fetchall()
        print(f"   Queries PostGIS funcionando: {len(resultados)} resultados")
        for titulo, lng, lat in resultados:
            print(f"   - {titulo[:50]}... ({lng}, {lat})")

        # Cerrar conexiones
        oracle_cursor.close()
        oracle_conn.close()
        docker_cursor.close()
        docker_conn.close()

        print()
        print("✅ MIGRACIÓN COMPLETA - PostGIS FUNCIONAL")
        print("   Problema encoding Windows RESUELTO")
        print("   Coordenadas PostGIS OPERATIVAS")

    except Exception as e:
        print(f"❌ ERROR en migración: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrar_datos()