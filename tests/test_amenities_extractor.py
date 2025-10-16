#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Prueba para AmenitiesExtractor

Prueba el extractor de amenities con datos reales del Proveedor 02.
"""

import json
import pandas as pd
import sys
from pathlib import Path

# Agregar path para importar módulos
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from amenities_extractor import AmenitiesExtractor

def cargar_datos_prueba():
    """Carga datos de prueba del Proveedor 02."""
    try:
        file_path = "data/raw/relevamiento/2025.08.29 02.xlsx"
        df = pd.read_excel(file_path)
        print(f"Cargados {len(df)} registros del Proveedor 02")
        return df
    except Exception as e:
        print(f"Error cargando datos: {e}")
        return pd.DataFrame()

def procesar_muestra(df, num_muestras=10):
    """Procesa una muestra de datos para probar el extractor."""
    # Filtrar propiedades con amenities
    con_amenities = df[df['Amenities'].notna() & (df['Amenities'] != '')]
    print(f"Propiedades con amenities: {len(con_amenities)}")

    # Tomar muestra
    muestra = con_amenities.head(num_muestras)
    print(f"Procesando muestra de {len(muestra)} propiedades")

    # Convertir a lista de diccionarios
    propiedades = muestra.to_dict('records')

    return propiedades

def main():
    """Función principal de prueba."""
    print("=" * 60)
    print("PRUEBA DE AMENITIESEXTRACTOR")
    print("=" * 60)

    # Cargar datos
    df = cargar_datos_prueba()
    if df.empty:
        return 1

    # Obtener muestra
    propiedades_muestra = procesar_muestra(df, 10)
    if not propiedades_muestra:
        print("No hay propiedades con amenities para procesar")
        return 1

    # Crear extractor
    extractor = AmenitiesExtractor()

    # Procesar muestra
    print("\nProcesando muestra con extractor híbrido...")
    propiedades_procesadas, stats = extractor.procesar_lote_propiedades(propiedades_muestra)

    # Mostrar resultados
    print(f"\nResultados del procesamiento:")
    print(f"Total procesadas: {stats['total_propiedades']}")
    print(f"Con amenities: {stats['con_amenities']}")
    print(f"Solo regex: {stats['solo_regex']}")
    print(f"Con IA: {stats['con_ia']}")
    print(f"Errores: {stats['errores']}")

    print(f"\nCategorías encontradas:")
    for categoria, count in stats['categorias_encontradas'].items():
        print(f"  • {categoria}: {count}")

    # Mostrar ejemplos detallados
    print(f"\nEjemplos de extracción:")
    print("-" * 40)

    for i, prop in enumerate(propiedades_procesadas[:3]):
        print(f"\nEjemplo {i+1}:")
        print(f"  Amenities original: {prop.get('Amenities', '')}")
        print(f"  Amenities estructurados:")
        if 'amenities_estructurados' in prop:
            for categoria, datos in prop['amenities_estructurados'].items():
                print(f"    {categoria}: {datos}")
        else:
            print("    No se extrajeron amenities")

    # Generar reporte
    reporte = extractor.generar_reporte_extraccion(stats)
    print(f"\n{reporte}")

    # Guardar resultados de prueba
    output_file = "data/test_amenities_extraction.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'fecha': pd.Timestamp.now().isoformat(),
                'total_muestra': len(propiedades_muestra)
            },
            'estadisticas': stats,
            'propiedades_procesadas': propiedades_procesadas[:5]  # Solo primeros 5 ejemplos
        }, f, ensure_ascii=False, indent=2, default=str)

    print(f"Resultados guardados en: {output_file}")
    print("Prueba completada exitosamente")

    return 0

if __name__ == "__main__":
    exit(main())