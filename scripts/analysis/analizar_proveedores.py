#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analizar las columnas y estructura de datos de cada proveedor.
"""

import pandas as pd
import json
from pathlib import Path
from collections import defaultdict
import sys
import codecs

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def analizar_proveedor(file_path: Path):
    """Analiza un archivo Excel de proveedor."""
    try:
        # Leer Excel
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # Extraer info del nombre
        parts = file_path.stem.split()
        fecha = parts[0] if len(parts) > 0 else "unknown"
        codigo = parts[1] if len(parts) > 1 else "unknown"
        
        info = {
            'archivo': file_path.name,
            'fecha': fecha,
            'codigo_proveedor': codigo,
            'total_filas': len(df),
            'total_columnas': len(df.columns),
            'columnas': list(df.columns),
            'columnas_lowercase': [c.lower().strip() for c in df.columns],
            'sample_row': {}
        }
        
        # Tomar una fila de muestra (primera no vacía)
        for idx, row in df.iterrows():
            if row.notna().sum() > 3:  # Al menos 3 campos no vacíos
                for col in df.columns:
                    val = row[col]
                    if pd.notna(val):
                        val_str = str(val)[:100]  # Limitar a 100 chars
                        info['sample_row'][col] = val_str
                break
        
        # Analizar campos clave
        info['tiene_url'] = any('url' in str(c).lower() for c in df.columns)
        info['tiene_precio'] = any('precio' in str(c).lower() or 'price' in str(c).lower() for c in df.columns)
        info['tiene_coordenadas'] = any('lat' in str(c).lower() for c in df.columns) and any('lon' in str(c).lower() for c in df.columns)
        info['tiene_zona'] = any('zona' in str(c).lower() or 'barrio' in str(c).lower() for c in df.columns)
        
        return info
        
    except Exception as e:
        return {
            'archivo': file_path.name,
            'error': str(e)
        }


def main():
    print("="*80)
    print("  ANÁLISIS DE COLUMNAS POR PROVEEDOR")
    print("="*80)
    
    raw_dir = Path("data/raw")
    archivos = sorted(raw_dir.glob("*.xlsx"))
    
    print(f"\nArchivos encontrados: {len(archivos)}")
    
    # Agrupar por proveedor
    por_proveedor = defaultdict(list)
    
    for archivo in archivos:
        print(f"\nAnalizando: {archivo.name}...")
        info = analizar_proveedor(archivo)
        
        if 'error' not in info:
            por_proveedor[info['codigo_proveedor']].append(info)
            print(f"  -> {info['total_filas']} filas, {info['total_columnas']} columnas")
    
    # Reporte detallado por proveedor
    print("\n" + "="*80)
    print("  REPORTE DETALLADO POR PROVEEDOR")
    print("="*80)
    
    for codigo, archivos_info in sorted(por_proveedor.items()):
        print(f"\n{'='*80}")
        print(f"PROVEEDOR {codigo}")
        print(f"{'='*80}")
        print(f"Total archivos: {len(archivos_info)}")
        print(f"Fechas: {', '.join(a['fecha'] for a in archivos_info)}")
        
        total_filas = sum(a['total_filas'] for a in archivos_info)
        print(f"Total filas (todas las fechas): {total_filas}")
        
        # Analizar consistencia de columnas entre fechas
        print(f"\nCOLUMNAS:")
        
        # Obtener todas las columnas únicas
        todas_columnas = set()
        for info in archivos_info:
            todas_columnas.update(info['columnas'])
        
        print(f"  Total columnas únicas: {len(todas_columnas)}")
        
        # Ver si las columnas son consistentes entre fechas
        if len(archivos_info) > 1:
            cols_primera = set(archivos_info[0]['columnas'])
            cols_ultima = set(archivos_info[-1]['columnas'])
            
            solo_primera = cols_primera - cols_ultima
            solo_ultima = cols_ultima - cols_primera
            comunes = cols_primera & cols_ultima
            
            print(f"  Columnas comunes entre fechas: {len(comunes)}")
            if solo_primera:
                print(f"  Solo en {archivos_info[0]['fecha']}: {len(solo_primera)}")
                for col in list(solo_primera)[:5]:
                    print(f"    - {col}")
            if solo_ultima:
                print(f"  Solo en {archivos_info[-1]['fecha']}: {len(solo_ultima)}")
                for col in list(solo_ultima)[:5]:
                    print(f"    - {col}")
        
        # Mostrar lista de columnas de la última fecha
        print(f"\n  Lista completa de columnas ({archivos_info[-1]['fecha']}):")
        for i, col in enumerate(archivos_info[-1]['columnas'], 1):
            print(f"    {i:2d}. {col}")
        
        # Mostrar muestra de datos
        print(f"\n  MUESTRA DE DATOS ({archivos_info[-1]['fecha']}):")
        sample = archivos_info[-1]['sample_row']
        for col, val in list(sample.items())[:10]:
            print(f"    {col:30s}: {val}")
        
        # Indicadores de campos clave
        print(f"\n  CAMPOS CLAVE:")
        for info in archivos_info:
            print(f"    Fecha {info['fecha']}:")
            print(f"      - URL: {'✓' if info['tiene_url'] else '✗'}")
            print(f"      - Precio: {'✓' if info['tiene_precio'] else '✗'}")
            print(f"      - Coordenadas: {'✓' if info['tiene_coordenadas'] else '✗'}")
            print(f"      - Zona: {'✓' if info['tiene_zona'] else '✗'}")
    
    # Guardar análisis completo en JSON
    output_file = Path("data/analisis_proveedores.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dict(por_proveedor), f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*80}")
    print(f"Análisis completo guardado en: {output_file}")
    print("="*80)


if __name__ == "__main__":
    main()
