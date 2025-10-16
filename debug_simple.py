#!/usr/bin/env python3
"""
Debug simple sin coordenadas PostGIS
"""

import sys
sys.path.append('migration/config')
from database_config import create_connection

def debug_simple():
    print('=== DEBUG SIMPLE SIN COORDENADAS ===')

    try:
        conn = create_connection()

        with conn.cursor() as cursor:
            # Consulta simple sin coordenadas PostGIS
            query = """
                SELECT id, titulo, COALESCE(precio_usd, 0) as precio_usd,
                       COALESCE(tipo_propiedad, 'sin_tipo') as tipo_propiedad,
                       COALESCE(zona, 'sin_zona') as zona
                FROM propiedades
                ORDER BY id
                LIMIT 3
            """

            cursor.execute(query)
            resultados = cursor.fetchall()

            print(f'Columnas: {[desc[0] for desc in cursor.description]}')
            print(f'Número de resultados: {len(resultados)}')

            if resultados:
                print(f'Primera fila: {resultados[0]}')
                print(f'Columnas reales: {len(resultados[0])}')

                print(f'Datos como dict:')
                for i, col_name in enumerate([desc[0] for desc in cursor.description]):
                    if i < len(resultados[0]):
                        print(f'  {col_name}: {resultados[0][i]}')

        conn.close()

    except Exception as e:
        print(f'ERROR: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_simple()