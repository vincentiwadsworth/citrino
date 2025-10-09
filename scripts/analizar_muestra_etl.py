#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de análisis detallado para optimizar el ETL de relevamiento.
Analiza la muestra de datos para identificar problemas y oportunidades de mejora.
"""

import json
import pandas as pd
from collections import defaultdict, Counter
from datetime import datetime

def analizar_muestra_etl():
    """Analiza la muestra de datos generada por el ETL."""

    # Cargar datos
    with open('data/base_datos_relevamiento.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    propiedades = data['propiedades']

    print("ANALISIS DETALLADO DE MUESTRA ETL")
    print("=" * 60)
    print(f"Fecha de análisis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total propiedades: {len(propiedades)}")
    print(f"Archivos procesados: {len(data['metadata']['archivos_procesados'])}")
    print()

    # 1. ANALISIS POR PROVEEDOR
    print("1. ANALISIS POR PROVEEDOR")
    print("-" * 30)

    analisis_proveedores = defaultdict(lambda: {
        'total': 0,
        'con_precio': 0,
        'con_zona': 0,
        'con_coords': 0,
        'con_descripcion': 0,
        'enriquecidas_llm': 0,
        'monedas': defaultdict(int)
    })

    for p in propiedades:
        prov = p['codigo_proveedor']
        analisis_proveedores[prov]['total'] += 1

        if p.get('precio'):
            analisis_proveedores[prov]['con_precio'] += 1
        if p.get('zona'):
            analisis_proveedores[prov]['con_zona'] += 1
        if p.get('latitud') and p.get('longitud'):
            analisis_proveedores[prov]['con_coords'] += 1
        if p.get('descripcion'):
            analisis_proveedores[prov]['con_descripcion'] += 1
        if p.get('precio_origen') == 'llm_extraction':
            analisis_proveedores[prov]['enriquecidas_llm'] += 1

        mon = p.get('moneda', 'NO_ESPECIFICADA')
        analisis_proveedores[prov]['monedas'][mon] += 1

    for prov in sorted(analisis_proveedores.keys()):
        stats = analisis_proveedores[prov]
        print(f"\nProveedor {prov}:")
        print(f"   Total: {stats['total']} propiedades")
        print(f"   Con precio: {stats['con_precio']}/{stats['total']} ({(stats['con_precio']/stats['total']*100):.1f}%)")
        print(f"   Con zona: {stats['con_zona']}/{stats['total']} ({(stats['con_zona']/stats['total']*100):.1f}%)")
        print(f"   Con coordenadas: {stats['con_coords']}/{stats['total']} ({(stats['con_coords']/stats['total']*100):.1f}%)")
        print(f"   Con descripción: {stats['con_descripcion']}/{stats['total']} ({(stats['con_descripcion']/stats['total']*100):.1f}%)")
        print(f"   Enriquecidas LLM: {stats['enriquecidas_llm']}")
        print(f"   Monedas: {dict(stats['monedas'])}")

    # 2. PROBLEMAS DE CALIDAD IDENTIFICADOS
    print("\n\n2. PROBLEMAS DE CALIDAD IDENTIFICADOS")
    print("-" * 40)

    problemas = []

    # Precio nulo o missing
    sin_precio = [p for p in propiedades if not p.get('precio')]
    if sin_precio:
        problemas.append(f"ERROR: {len(sin_precio)} propiedades sin precio ({len(sin_precio)/len(propiedades)*100:.1f}%)")

    # Zona missing
    sin_zona = [p for p in propiedades if not p.get('zona')]
    if sin_zona:
        problemas.append(f"ERROR: {len(sin_zona)} propiedades sin zona ({len(sin_zona)/len(propiedades)*100:.1f}%)")

    # Coordenadas inconsistentes
    sin_coords = [p for p in propiedades if not (p.get('latitud') and p.get('longitud'))]
    if sin_coords:
        problemas.append(f"ERROR: {len(sin_coords)} propiedades sin coordenadas ({len(sin_coords)/len(propiedades)*100:.1f}%)")

    # Moneda no especificada
    sin_moneda = [p for p in propiedades if p.get('moneda') in [None, 'NO_ESPECIFICADA']]
    if sin_moneda:
        problemas.append(f"ERROR: {len(sin_moneda)} propiedades sin moneda especificada ({len(sin_moneda)/len(propiedades)*100:.1f}%)")

    for problema in problemas:
        print(f"   {problema}")

    # 3. OPORTUNIDADES DE MEJORA
    print("\n\n3. OPORTUNIDADES DE MEJORA")
    print("-" * 35)

    # Detectar patrones de precios que podrían extraerse de descripciones
    descripciones_con_precios = []
    for p in propiedades:
        if not p.get('precio') and p.get('descripcion'):
            desc = p['descripcion'].lower()
            if any(palabra in desc for palabra in ['$', 'usd', 'bs', 'precio', 'costo']):
                descripciones_con_precios.append(p['id'])

    if descripciones_con_precios:
        print(f"INFO: {len(descripciones_con_precios)} propiedades tienen precios potenciales en descripciones sin extraer")

    # Detectar zonas en descripciones
    zonas_en_descripciones = []
    zonas_conocidas = ['equipetrol', 'urubó', 'urubo', 'santa cruz', 'lazareto', 'tarope', 'la ramada']

    for p in propiedades:
        if not p.get('zona') and p.get('descripcion'):
            desc = p['descripcion'].lower()
            for zona in zonas_conocidas:
                if zona in desc:
                    zonas_en_descripciones.append((p['id'], zona))
                    break

    if zonas_en_descripciones:
        print(f"INFO: {len(zonas_en_descripciones)} propiedades tienen zonas potenciales en descripciones")
        print(f"   Ejemplos: {zonas_en_descripciones[:3]}")

    # 4. RECOMENDACIONES ESTRATEGICAS
    print("\n\n4. RECOMENDACIONES ESTRATEGICAS")
    print("-" * 40)

    print("BASADO EN EL ANALISIS:")
    print()

    print("ESTRATEGIA DE PROCESAMIENTO:")
    print("   * Proveedor 01: Datos estructurados, buena calidad de coordenadas")
    print("   * Proveedor 02: Datos en texto libre, requiere mas LLM")
    print("   * Proveedor 03: Datos limitados, enfocar en extraccion de coordenadas")
    print("   * Proveedor 04: Datos estructurados con descripciones ricas")
    print("   * Proveedor 05: Datos semi-estructurados, extraccion de precios necesaria")
    print()

    print("MEJORAS RECOMENDADAS:")
    print("   1. Extraccion de precios de descripciones (regex + LLM)")
    print("   2. Deteccion de monedas (USD/BOB) en textos")
    print("   3. Extraccion mejorada de zonas de textos")
    print("   4. Validacion de coordenadas para Santa Cruz")
    print("   5. Procesamiento diferenciado por proveedor")
    print()

    print("OPTIMIZACION DE TOKENS LLM:")
    print("   * Priorizar proveedor 02 para LLM (datos no estructurados)")
    print("   * Usar regex primero para extraccion simple")
    print("   * Aplicar LLM solo cuando regex falla")
    print("   * Cache agresivo para patrones repetitivos")

    # 5. ESTIMACION PARA PROCESO COMPLETO
    print("\n\n5. ESTIMACION PARA PROCESO COMPLETO")
    print("-" * 40)

    # Estimar propiedades totales basado en archivos
    total_estimado = 0
    archivos_info = {
        '2025.08.15 05.xlsx': 60,
        '2025.08.17 01.xlsx': 96,
        '2025.08.29 01.xlsx': 85,
        '2025.08.29 02.xlsx': 1593,  # El más grande
        '2025.08.29 03.xlsx': 19,
        '2025.08.29 04.xlsx': 119,
        '2025.08.29 05.xlsx': 38
    }

    for archivo in data['metadata']['archivos_procesados']:
        nombre = archivo.split('\\')[-1]
        if nombre in archivos_info:
            total_estimado += archivos_info[nombre]

    print(f"Estimacion total de propiedades: {total_estimado:,}")
    print(f"Muestra actual: {len(propiedades)} ({(len(propiedades)/total_estimado)*100:.1f}%)")
    print(f"Proyeccion de problemas:")
    print(f"   * Sin precio: ~{int(len(sin_precio)/len(propiedades)*total_estimado):,} propiedades")
    print(f"   * Sin zona: ~{int(len(sin_zona)/len(propiedades)*total_estimado):,} propiedades")
    print(f"   * LLM necesarios: ~{int(1593*0.8):,} para proveedor 02")

    print("\n" + "=" * 60)
    print("ANALISIS COMPLETADO - Listo para optimizacion ETL")

if __name__ == "__main__":
    analizar_muestra_etl()