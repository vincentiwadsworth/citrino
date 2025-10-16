#!/usr/bin/env python3
"""
Test simple para verificar que API actualizada funciona con Docker wrapper
"""

import sys
import os
sys.path.append('migration/config')
sys.path.append('api')

from database_config import create_connection

def test_api_actualizada():
    print('=== TEST DE API ACTUALIZADA CON COLUMNAS CORRECTAS ===')

    try:
        conn = create_connection()

        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, titulo, precio_usd,
                       ST_X(coordenadas::geometry),
                       ST_Y(coordenadas::geometry),
                       zona
                FROM propiedades
                LIMIT 3
            """)

            resultados = cursor.fetchall()
            print(f'CONSULTA SQL: OK ({len(resultados)} resultados)')

            if resultados:
                print('EJEMPLO DE PROPIEDAD:')
                print(f'  ID: {resultados[0][0]}')
                print(f'  Título: {resultados[0][1]}')
                print(f'  Precio: ${resultados[0][2]}')
                print(f'  Longitud: {resultados[0][3]}')
                print(f'  Latitud: {resultados[0][4]}')
                print(f'  Zona: {resultados[0][5]}')

        conn.close()
        print('TEST SQL: COMPLETADO CORRECTAMENTE')

        # Probar inicialización de API
        print('\n=== TEST DE INICIALIZACIÓN DE API ===')
        os.environ['USE_POSTGRES'] = 'true'

        from server import inicializar_datos
        resultado = inicializar_datos()
        print(f'INICIALIZACIÓN API: {resultado}')

        return True

    except Exception as e:
        print(f'ERROR: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_api_actualizada()
    if success:
        print('\n✓ API ACTUALIZADA FUNCIONANDO CORRECTAMENTE')
    else:
        print('\n✗ ERROR EN API ACTUALIZADA')