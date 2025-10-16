#!/usr/bin/env python3
"""
Debug específico de la consulta que usa la API
"""

import sys
sys.path.append('migration/config')
from database_config import create_connection

def debug_api_query():
    print('=== DEBUG CONSULTA API ===')

    try:
        conn = create_connection()

        with conn.cursor() as cursor:
            # Consulta exacta que usa la API
            query = """
                SELECT id, titulo, descripcion, precio_usd, tipo_propiedad,
                       0.0 as longitud,  -- Temporal: coordenadas PostGIS necesitan fix
                       0.0 as latitud,   -- Temporal: coordenadas PostGIS necesitan fix
                       COALESCE(zona, 'sin_zona') as zona,
                       COALESCE(direccion, '') as direccion,
                       COALESCE(superficie_total, 0) as superficie_total,
                       COALESCE(superficie_construida, 0) as superficie_construida,
                       COALESCE(num_dormitorios, 0) as num_dormitorios,
                       COALESCE(num_banos, 0) as num_banos,
                       COALESCE(num_garajes, 0) as num_garajes,
                       COALESCE(fecha_scraping, NOW()) as fecha_scraping,
                       COALESCE(proveedor_datos, 'postgresql') as proveedor_datos,
                       COALESCE(coordenadas_validas, false) as coordenadas_validas,
                       COALESCE(datos_completos, false) as datos_completos
                FROM propiedades
                ORDER BY id
                LIMIT 3
            """

            cursor.execute(query)
            resultados = cursor.fetchall()

            print(f'Columnas generadas: {[desc[0] for desc in cursor.description]}')
            print(f'Número de resultados: {len(resultados)}')

            if resultados:
                print(f'Primera fila (completa): {resultados[0]}')
                print(f'Columnas reales: {len(resultados[0])}')
                print(f'Columnas esperadas: {len(cursor.description)}')

                # Crear dict como lo hace la API
                columnas = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                if rows:
                    prop_dict = dict(zip(columnas, rows[0]))
                    print(f'Dict creado: {prop_dict}')

                    # Verificar keys
                    print(f'Keys disponibles: {list(prop_dict.keys())}')
                    if 'id' in prop_dict:
                        print(f'ID encontrado: {prop_dict["id"]}')
                    else:
                        print('ERROR: Key "id" no encontrada')

        conn.close()

    except Exception as e:
        print(f'ERROR: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_api_query()