#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Prueba para PriceCorrector

Prueba el corrector de precios con datos reales del Proveedor 02.
"""

import json
import pandas as pd
import sys
from pathlib import Path

# Agregar path para importar módulos
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from price_corrector import PriceCorrector

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

def encontrar_precios_invalidos(df):
    """Encuentra propiedades con precios inválidos."""
    if 'Precio' not in df.columns:
        print("No se encontró columna 'Precio'")
        return pd.DataFrame()

    # Definir precios inválidos
    invalidos = df[df['Precio'].astype(str).str.contains(r'0\.00|0,00|0 BOB|0 USD', na=False, case=False)]
    print(f"Propiedades con precios inválidos: {len(invalidos)}")

    return invalidos

def procesar_muestra(df_invalios, num_muestras=10):
    """Procesa una muestra de propiedades con precios inválidos."""
    if len(df_invalios) == 0:
        print("No hay propiedades con precios inválidos para procesar")
        return []

    # Tomar muestra
    muestra = df_invalios.head(num_muestras)
    print(f"Procesando muestra de {len(muestra)} propiedades con precios inválidos")

    # Convertir a lista de diccionarios
    propiedades = muestra.to_dict('records')

    return propiedades

def main():
    """Función principal de prueba."""
    print("=" * 60)
    print("PRUEBA DE PRICECORRECTOR")
    print("=" * 60)

    # Cargar datos
    df = cargar_datos_prueba()
    if df.empty:
        return 1

    # Encontrar precios inválidos
    df_invalidos = encontrar_precios_invalidos(df)

    # Obtener muestra
    propiedades_muestra = procesar_muestra(df_invalidos, 20)
    if not propiedades_muestra:
        print("No hay propiedades con precios inválidos para procesar")
        return 1

    # Crear corrector
    corrector = PriceCorrector()

    # Procesar muestra
    print(f"\nProcesando muestra con corrector de precios...")
    propiedades_procesadas, stats = corrector.procesar_lote_propiedades(propiedades_muestra)

    # Mostrar resultados
    print(f"\nResultados del procesamiento:")
    print(f"Total procesadas: {stats['total_propiedades']}")
    print(f"Precios inválidos detectados: {stats['precios_invalidos']}")
    print(f"Precios corregidos: {stats['precios_corregidos']}")
    print(f"Correcciones con regex: {stats['correcciones_regex']}")
    print(f"Correcciones con IA: {stats['correcciones_ia']}")
    print(f"Errores: {stats['errores']}")

    print(f"\nMétodos usados:")
    for metodo, count in stats['metodos_usados'].items():
        print(f"  • {metodo}: {count}")

    # Mostrar ejemplos detallados
    print(f"\nEjemplos de corrección:")
    print("-" * 40)

    ejemplos_mostrados = 0
    for i, prop in enumerate(propiedades_procesadas):
        if prop.get('precio_status') == 'corregido' and ejemplos_mostrados < 5:
            print(f"\nEjemplo {ejemplos_mostrados + 1}:")
            print(f"  ID: {prop.get('id', 'N/A')}")
            print(f"  Precio original: {prop.get('precio_original', 'N/A')}")
            print(f"  Precio corregido: {prop.get('precio_corregido', 'N/A')} {prop.get('moneda_corregida', 'N/A')}")
            print(f"  Método: {prop.get('precio_metodo', 'N/A')}")
            print(f"  Confianza: {prop.get('precio_confianza', 'N/A')}")
            print(f"  Contexto: {prop.get('precio_contexto', 'N/A')[:100]}")
            ejemplos_mostrados += 1

    # Generar reporte
    reporte = corrector.generar_reporte_correccion(stats)
    print(f"\n{reporte}")

    # Guardar resultados de prueba
    output_file = "data/test_price_correction.json"
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