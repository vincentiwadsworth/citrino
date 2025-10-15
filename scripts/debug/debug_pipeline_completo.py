#!/usr/bin/env python3
"""
DEBUG COMPLETO DEL PIPELINE ETL
Investiga dónde exactamente falla el procesamiento en el pipeline completo
"""

import sys
from pathlib import Path

# Agregar path para importar el ETL
sys.path.insert(0, str(Path(__file__).parent.parent / 'etl'))

from build_guia_urbana_dataset_v2 import GuiaUrbanaETL

def debug_etl_paso_a_paso():
    """Debug paso a paso del ETL para encontrar dónde falla."""
    print("=== DEBUG COMPLETO DEL PIPELINE ETL ===")

    # 1. Crear instancia del ETL
    etl = GuiaUrbanaETL()
    print(f"1. ETL inicializado: {type(etl)}")

    # 2. Leer archivo Excel
    print("\n2. Leyendo archivo Excel...")
    df = etl.leer_guia_urbana_excel("data/raw/guia/GUIA URBANA.xlsx")
    if df is None:
        print("   ERROR: No se pudo leer el archivo Excel")
        return

    print(f"   OK: DataFrame leído con shape {df.shape}")
    print(f"   Columnas: {list(df.columns)[:10]}...")

    # 3. Procesar primeras 5 filas manualmente
    print("\n3. Procesando primeras 5 filas manualmente...")
    for i in range(min(5, len(df))):
        row = df.iloc[i]
        print(f"\n   Fila {i}:")
        print(f"   Valores crudos: {dict(row.head(10))}")

        # Procesar con el método del ETL
        servicio = etl.procesar_fila_servicio(row, i)
        print(f"   Resultado ETL: {servicio}")

        if servicio:
            coords = servicio.get('ubicacion', {}).get('coordenadas')
            validas = servicio.get('metadatos', {}).get('coordenadas_validadas', False)
            print(f"   Coordenadas: {coords}")
            print(f"   Válidas: {validas}")

def debug_extraccion_servicios():
    """Debug específico del método de extracción de servicios."""
    print("\n=== DEBUG EXTRACCIÓN DE SERVICIOS ===")

    etl = GuiaUrbanaETL()
    df = etl.leer_guia_urbana_excel("data/raw/guia/GUIA URBANA.xlsx")

    if df is None:
        return

    # Extraer servicios
    print("Extrayendo servicios...")
    servicios = etl.extraer_servicios_urbanos(df)

    print(f"Total servicios extraídos: {len(servicios)}")

    # Analizar primeros 10 servicios
    print("\nAnálisis de primeros 10 servicios:")
    coordenadas_validas = 0
    coordenadas_invalidas = 0

    for i, servicio in enumerate(servicios[:10], 1):
        print(f"\nServicio {i}:")
        print(f"  ID: {servicio.get('id')}")
        print(f"  Nombre: {servicio.get('nombre')}")
        print(f"  UV: {servicio.get('ubicacion', {}).get('uv')}")

        coords = servicio.get('ubicacion', {}).get('coordenadas')
        validas = servicio.get('metadatos', {}).get('coordenadas_validadas', False)

        print(f"  Coordenadas: {coords}")
        print(f"  Válidas: {validas}")

        if validas:
            coordenadas_validas += 1
        else:
            coordenadas_invalidas += 1

    print(f"\nResumen primeras 10:")
    print(f"  Válidas: {coordenadas_validas}")
    print(f"  Inválidas: {coordenadas_invalidas}")

    # Verificar estadísticas del ETL
    print(f"\nEstadísticas ETL:")
    for key, value in etl.estadisticas.items():
        print(f"  {key}: {value}")

def debug_column_mapping():
    """Debug del mapeo de columnas."""
    print("\n=== DEBUG MAPEO DE COLUMNAS ===")

    etl = GuiaUrbanaETL()
    df = etl.leer_guia_urbana_excel("data/raw/guia/GUIA URBANA.xlsx")

    if df is None:
        return

    print(f"Columnas del DataFrame: {list(df.columns)}")

    # Probar diferentes formas de buscar coordenadas
    print("\nBuscando coordenadas en diferentes columnas:")
    for i, row in enumerate(df.head(10).itertuples()):
        print(f"\nFila {i}:")
        for col_idx, (col_name, value) in enumerate(row._asdict().items()):
            if col_idx >= 10:  # Limitar a primeras 10 columnas
                break
            if pd.notna(value) and 'GOOGLE_MAP' in str(value) or ',' in str(value):
                print(f"  Columna {col_idx} ({col_name}): {value}")

def main():
    """Función principal."""
    print("DEBUG CRÍTICO - PIPELINE ETL COMPLETO")
    print("=====================================")

    # Importar pandas para los debugs
    import pandas as pd
    globals()['pd'] = pd

    try:
        debug_etl_paso_a_paso()
        debug_extraccion_servicios()
        debug_column_mapping()

        print("\n=== DEBUG COMPLETADO ===")
        print("Revisar los resultados para identificar el problema")

    except Exception as e:
        print(f"\nERROR EN DEBUG: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()