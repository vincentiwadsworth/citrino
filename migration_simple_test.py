#!/usr/bin/env python3
"""
Script simple de migración directa para probar PostgreSQL + PostGIS
"""

import os
import sys
import pandas as pd
import psycopg2
from pathlib import Path

def main():
    # Configuración
    db_config = {
        'host': 'localhost',
        'database': 'citrino',
        'user': 'citrino_app',
        'password': 'citrino123',
        'port': '5432'
    }

    directorio_excel = 'data/raw/relevamiento'
    archivos_excel = list(Path(directorio_excel).glob("*.xlsx"))

    print(f"Encontrados {len(archivos_excel)} archivos Excel")

    # Conectar a DB
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        print("Conexión exitosa a PostgreSQL")

        # Contar archivos procesados
        total_propiedades = 0

        for archivo in archivos_excel:
            print(f"\nProcesando: {archivo.name}")

            try:
                # Leer Excel
                df = pd.read_excel(str(archivo))
                print(f"  - Filas leídas: {len(df)}")

                # Procesar propiedades básicas
                for idx, row in df.iterrows():
                    try:
                        # Extraer datos básicos
                        titulo = str(row.get('Título', '')).strip()
                        precio = str(row.get('Precio', '')).strip()
                        url = str(row.get('URL', '')).strip()

                        if not titulo or not precio or not url:
                            continue

                        # Extraer precio numérico
                        import re
                        numeros = re.findall(r'[0-9,]+', precio)
                        if numeros:
                            precio_num = float(numeros[0].replace(',', ''))
                        else:
                            continue

                        # Coordenadas
                        lat = row.get('Latitud')
                        lon = row.get('Longitud')

                        if pd.isna(lat) or pd.isna(lon):
                            lat_num, lon_num = None, None
                        else:
                            try:
                                lat_num = float(lat)
                                lon_num = float(lon)
                            except:
                                lat_num, lon_num = None, None

                        # Insertar propiedad
                        cursor.execute("""
                            INSERT INTO propiedades
                            (titulo, descripcion, precio_usd, url, latitud, longitud,
                             proveedor_datos, codigo_proveedor, coordenadas_validas)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (url) DO NOTHING
                        """, (
                            titulo,
                            str(row.get('Descripción', ''))[:500],  # Limitar descripción
                            precio_num,
                            url,
                            lat_num,
                            lon_num,
                            'excel_migracion',
                            archivo.name,
                            lat_num is not None and lon_num is not None
                        ))

                        total_propiedades += 1

                    except Exception as e:
                        print(f"    Error en fila {idx}: {e}")
                        continue

                print(f"  - Propiedades procesadas: {len(df)}")

            except Exception as e:
                print(f"Error procesando archivo {archivo}: {e}")
                continue

        # Commit y actualizar coordenadas PostGIS
        conn.commit()

        # Actualizar coordenadas PostGIS
        cursor.execute("SELECT actualizar_coordenadas_propiedades()")
        actualizadas = cursor.fetchone()[0]

        print(f"\n=== RESUMEN ===")
        print(f"Total propiedades insertadas: {total_propiedades}")
        print(f"Coordenadas PostGIS actualizadas: {actualizadas}")

        # Verificar resultados
        cursor.execute("SELECT COUNT(*) FROM propiedades")
        total_db = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM propiedades WHERE coordenadas IS NOT NULL")
        con_coordenadas = cursor.fetchone()[0]

        print(f"Propiedades en BD: {total_db}")
        print(f"Con coordenadas PostGIS: {con_coordenadas}")

        cursor.close()
        conn.close()

        print("\nMigración completada exitosamente!")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())