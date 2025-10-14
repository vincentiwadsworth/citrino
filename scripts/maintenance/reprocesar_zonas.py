#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para reprocesar el dataset existente y extraer zonas geográficas reales.
Corrige el problema donde 'zona' contiene la fuente de datos en vez de la ubicación.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

# Importar el extractor de zonas
from zonas_extractor import ZonasExtractor


def reprocesar_datos(input_file: str, output_file: str):
    """
    Reprocesa el dataset para extraer zonas reales.
    
    Args:
        input_file: Ruta al archivo JSON con datos actuales
        output_file: Ruta donde guardar datos corregidos
    """
    print("=" * 80)
    print("REPROCESAMIENTO DE DATOS - EXTRACCI\u00d3N DE ZONAS REALES")
    print("=" * 80)
    
    # Cargar datos
    print(f"\n1. Cargando datos desde {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    propiedades = data.get('propiedades', [])
    print(f"   Cargadas {len(propiedades):,} propiedades")
    
    # Inicializar extractor
    extractor = ZonasExtractor()
    
    # Estadísticas
    stats = {
        'total': len(propiedades),
        'con_zona_original': 0,
        'zona_extraida_titulo': 0,
        'zona_extraida_descripcion': 0,
        'sin_zona_final': 0,
        'fuente_datos_identificada': 0
    }
    
    zonas_encontradas = defaultdict(int)
    fuentes_datos = defaultdict(int)
    
    # Procesar cada propiedad
    print("\n2. Reprocesando propiedades...")
    for i, prop in enumerate(propiedades):
        if (i + 1) % 200 == 0:
            print(f"   Procesadas {i + 1:,}/{len(propiedades):,} propiedades...")
        
        # Guardar zona original como fuente_datos si parece ser fuente
        zona_original = prop.get('zona', '').strip()
        if zona_original:
            stats['con_zona_original'] += 1
            
            # Detectar si es fuente de datos (en mayúsculas, nombres de competidores, etc.)
            if zona_original.isupper() or zona_original in ['ULTRACASAS', 'INFOCASAS']:
                prop['fuente_datos'] = zona_original
                stats['fuente_datos_identificada'] += 1
                fuentes_datos[zona_original] += 1
                prop['zona'] = ''  # Limpiar zona
            else:
                # Intentar normalizar si ya parece ser zona
                zona_normalizada = extractor.normalizar_zona(zona_original)
                if zona_normalizada:
                    prop['zona'] = zona_normalizada
                    zonas_encontradas[zona_normalizada] += 1
                    continue
        
        # Extraer zona del título
        titulo = prop.get('titulo', '')
        if titulo:
            zona_titulo = extractor.extraer_zona_principal(titulo)
            if zona_titulo:
                prop['zona'] = zona_titulo
                zonas_encontradas[zona_titulo] += 1
                stats['zona_extraida_titulo'] += 1
                
                # También guardar referencias completas
                referencias = extractor.extraer_referencias_ubicacion(titulo)
                if referencias['anillos'] or referencias['radiales']:
                    prop['referencias_ubicacion'] = referencias
                
                continue
        
        # Si no se encontró en título, buscar en descripción
        descripcion = prop.get('descripcion', '')
        if descripcion:
            zona_desc = extractor.extraer_zona_principal(descripcion)
            if zona_desc:
                prop['zona'] = zona_desc
                zonas_encontradas[zona_desc] += 1
                stats['zona_extraida_descripcion'] += 1
                
                # También guardar referencias completas
                referencias = extractor.extraer_referencias_ubicacion(descripcion)
                if referencias['anillos'] or referencias['radiales']:
                    prop['referencias_ubicacion'] = referencias
                
                continue
        
        # Si llegamos aquí, no se pudo extraer zona
        prop['zona'] = ''
        stats['sin_zona_final'] += 1
    
    # Actualizar metadata
    data['metadata']['fecha_reprocesamiento'] = str(Path(output_file).stat().st_mtime if Path(output_file).exists() else '')
    data['metadata']['reprocesamiento_zonas'] = {
        'version': '1.0',
        'extractor_zonas': True,
        'estadisticas': stats
    }
    
    # Guardar datos corregidos
    print(f"\n3. Guardando datos corregidos en {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Imprimir reporte
    print("\n" + "=" * 80)
    print("REPORTE DE REPROCESAMIENTO")
    print("=" * 80)
    
    print(f"\nTotal propiedades:               {stats['total']:,}")
    print(f"Con zona original:               {stats['con_zona_original']:,} ({stats['con_zona_original']/stats['total']*100:.1f}%)")
    print(f"Fuente de datos identificada:    {stats['fuente_datos_identificada']:,}")
    print(f"Zona extraída desde título:      {stats['zona_extraida_titulo']:,} ({stats['zona_extraida_titulo']/stats['total']*100:.1f}%)")
    print(f"Zona extraída desde descripción: {stats['zona_extraida_descripcion']:,} ({stats['zona_extraida_descripcion']/stats['total']*100:.1f}%)")
    print(f"Sin zona al final:               {stats['sin_zona_final']:,} ({stats['sin_zona_final']/stats['total']*100:.1f}%)")
    
    # Calcular propiedades con zona
    con_zona_final = stats['total'] - stats['sin_zona_final']
    print(f"\n✅ CON ZONA FINAL:                {con_zona_final:,} ({con_zona_final/stats['total']*100:.1f}%)")
    print(f"❌ SIN ZONA FINAL:                {stats['sin_zona_final']:,} ({stats['sin_zona_final']/stats['total']*100:.1f}%)")
    
    # Mejora vs estado anterior
    mejora = con_zona_final - stats['con_zona_original']
    print(f"\n📈 MEJORA: +{mejora:,} propiedades con zona ({mejora/stats['total']*100:.1f}% del total)")
    
    # Zonas más frecuentes
    print(f"\n📍 TOP 10 ZONAS ENCONTRADAS:")
    for i, (zona, cantidad) in enumerate(sorted(zonas_encontradas.items(), key=lambda x: x[1], reverse=True)[:10], 1):
        print(f"{i:2d}. {zona:30s}: {cantidad:5d} ({cantidad/con_zona_final*100:5.1f}%)")
    
    # Fuentes de datos
    if fuentes_datos:
        print(f"\n📊 FUENTES DE DATOS IDENTIFICADAS:")
        for fuente, cantidad in sorted(fuentes_datos.items(), key=lambda x: x[1], reverse=True):
            print(f"   {fuente:20s}: {cantidad:5d}")
    
    print("\n" + "=" * 80)
    print(f"✅ Reprocesamiento completado exitosamente")
    print(f"   Archivo generado: {output_file}")
    print("=" * 80)


def main():
    """Función principal."""
    # Configurar encoding para Windows
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    
    # Rutas
    base_dir = Path(__file__).parent.parent
    input_file = base_dir / 'data' / 'base_datos_relevamiento.json'
    output_file = base_dir / 'data' / 'base_datos_relevamiento_zonas_corregidas.json'
    
    # Verificar que existe el archivo de entrada
    if not input_file.exists():
        print(f"❌ Error: No se encontró el archivo {input_file}")
        sys.exit(1)
    
    # Ejecutar reprocesamiento
    try:
        reprocesar_datos(str(input_file), str(output_file))
    except Exception as e:
        print(f"\n❌ Error durante el reprocesamiento: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
