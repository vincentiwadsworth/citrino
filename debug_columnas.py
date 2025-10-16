#!/usr/bin/env python3
"""
Debug script para verificar qué columnas se generan
"""

import sys
sys.path.append('migration/config')
from database_config import create_connection

def debug_columnas():
    print('=== DEBUG DE COLUMNAS ===')

    try:
        conn = create_connection()

        with conn.cursor() as cursor:
            query = """
                SELECT id, titulo, descripcion, precio_usd, tipo_propiedad,
                       ST_X(coordenadas::geometry) as longitud,
                       ST_Y(coordenadas::geometry) as latitud,
                       zona, direccion, superficie_total,
                       superficie_construida, num_dormitorios, num_banos, num_garajes,
                       fecha_scraping, proveedor_datos, coordenadas_validas, datos_completos
                FROM propiedades
                ORDER BY id
                LIMIT 3
            """

            cursor.execute(query)
            resultados = cursor.fetchall()

            print(f'Columnas generadas: {[desc[0] for desc in cursor.description]}')
            print(f'Número de resultados: {len(resultados)}')

            if resultados:
                print(f'Primera fila (cruda): {resultados[0]}')
                print(f'Columnas esperadas: {len([desc[0] for desc in cursor.description])}')
                print(f'Columnas reales: {len(resultados[0])}')
                print(f'Datos como dict:')
                for i, col_name in enumerate([desc[0] for desc in cursor.description]):
                    if i < len(resultados[0]):
                        print(f'  {col_name}: {resultados[0][i]}')
                    else:
                        print(f'  {col_name}: [MISSING]')

        conn.close()

    except Exception as e:
        print(f'ERROR: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_columnas()