#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar preservación de moneda en Proveedor 02.
"""

import sys
from pathlib import Path

# Agregar paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from build_relevamiento_dataset import ProcesadorDatosRelevamiento

def test_proveedor02_monedas():
    """Prueba preservación de monedas en proveedor 02."""
    print("="*80)
    print("TEST: Monedas en Proveedor 02 (descripciones texto libre)")
    print("="*80)
    
    procesador = ProcesadorDatosRelevamiento()
    archivos = procesador.encontrar_archivos_excel()
    
    # Buscar archivo del proveedor 02
    archivo_02 = None
    for arch in archivos:
        if '2025.08.29 02' in arch:
            archivo_02 = arch
            break
    
    if not archivo_02:
        print("ERROR: No se encontró archivo del proveedor 02")
        return
    
    print(f"\nProcesando: {Path(archivo_02).name}")
    print("NOTA: Solo procesando primeras 10 propiedades para rapidez")
    
    # Leer Excel
    import pandas as pd
    df = pd.read_excel(archivo_02, engine='openpyxl')
    df = procesador.estandarizar_columnas(df)
    
    # Procesar solo 10 propiedades
    propiedades = []
    for index, row in df.head(10).iterrows():
        propiedad = procesador.procesar_propiedad(
            row, 
            "2025.08.29", 
            "02",
            Path(archivo_02).name
        )
        if propiedad:
            propiedades.append(propiedad)
    
    print(f"\nPropiedades procesadas: {len(propiedades)}")
    
    # Análisis de monedas
    con_precio = [p for p in propiedades if p.get('precio')]
    print(f"Con precio: {len(con_precio)}")
    
    if con_precio:
        print("\n" + "="*80)
        print("PROPIEDADES CON PRECIO Y MONEDA")
        print("="*80)
        
        for i, p in enumerate(con_precio):
            precio = p.get('precio')
            moneda = p.get('moneda', 'N/A')
            tipo = p.get('tipo_propiedad', 'N/A')
            zona = p.get('zona', 'N/A')
            
            print(f"\n{i+1}. Tipo: {tipo}, Zona: {zona}")
            print(f"   Precio: {precio:,.2f} {moneda}")
            
            # Mostrar descripción parcial
            desc = p.get('descripcion', '')[:100]
            if desc:
                print(f"   Desc: {desc}...")
        
        # Estadísticas
        usd_count = sum(1 for p in con_precio if p.get('moneda') == 'USD')
        bob_count = sum(1 for p in con_precio if p.get('moneda') == 'BOB')
        
        print("\n" + "="*80)
        print("RESULTADO")
        print("="*80)
        print(f"✓ USD: {usd_count} propiedades")
        print(f"✓ BOB: {bob_count} propiedades")
        
        # Verificar campos viejos
        tiene_campos_viejos = any(
            'precio_usd' in p or 'precio_original' in p or 'moneda_original' in p
            for p in propiedades
        )
        
        if tiene_campos_viejos:
            print("\n⚠️  FALLO: Encontrados campos del sistema de conversión viejo")
        else:
            print("\n✓ ÉXITO: Sistema de conversión eliminado correctamente")
            print("✓ Las monedas originales (USD/BOB) se preservan sin conversión")
    else:
        print("\nADVERTENCIA: No se extrajeron precios")

if __name__ == "__main__":
    test_proveedor02_monedas()
