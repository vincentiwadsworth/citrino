#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar preservación de moneda original (USD/BOB).
"""

import sys
from pathlib import Path

# Agregar paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from build_relevamiento_dataset import ProcesadorDatosRelevamiento

def test_preservacion_moneda():
    """Prueba que las monedas se preserven correctamente."""
    print("="*80)
    print("TEST: Preservación de Monedas Originales (USD/BOB)")
    print("="*80)
    
    # Procesar solo el primer archivo (pequeño)
    procesador = ProcesadorDatosRelevamiento()
    archivos = procesador.encontrar_archivos_excel()
    
    if not archivos:
        print("ERROR: No se encontraron archivos Excel")
        return
    
    # Procesar solo primer archivo
    archivo = archivos[0]
    print(f"\nProcesando: {Path(archivo).name}")
    propiedades = procesador.procesar_archivo(archivo)
    
    # Analizar monedas
    print(f"\nTotal propiedades procesadas: {len(propiedades)}")
    
    con_precio = [p for p in propiedades if p.get('precio')]
    print(f"Con precio: {len(con_precio)}")
    
    if con_precio:
        print("\nMuestras de propiedades con precio:")
        for i, p in enumerate(con_precio[:5]):
            precio = p.get('precio')
            moneda = p.get('moneda', 'N/A')
            tipo = p.get('tipo_propiedad', 'N/A')
            zona = p.get('zona', 'N/A')
            
            print(f"\n{i+1}. Tipo: {tipo}")
            print(f"   Zona: {zona}")
            print(f"   Precio: {precio} {moneda}")
            print(f"   ID: {p['id']}")
        
        # Estadísticas por moneda
        usd_count = sum(1 for p in con_precio if p.get('moneda') == 'USD')
        bob_count = sum(1 for p in con_precio if p.get('moneda') == 'BOB')
        otra_count = len(con_precio) - usd_count - bob_count
        
        print("\n" + "="*80)
        print("ESTADÍSTICAS POR MONEDA")
        print("="*80)
        print(f"USD: {usd_count} propiedades ({usd_count/len(con_precio)*100:.1f}%)")
        print(f"BOB: {bob_count} propiedades ({bob_count/len(con_precio)*100:.1f}%)")
        if otra_count:
            print(f"Otra/N/A: {otra_count} propiedades ({otra_count/len(con_precio)*100:.1f}%)")
        
        # Verificar que NO haya campos precio_usd, precio_original, moneda_original
        campos_viejos = []
        for p in propiedades:
            if 'precio_usd' in p:
                campos_viejos.append('precio_usd')
            if 'precio_original' in p:
                campos_viejos.append('precio_original')
            if 'moneda_original' in p:
                campos_viejos.append('moneda_original')
        
        if campos_viejos:
            print(f"\n⚠️  ADVERTENCIA: Se encontraron campos del sistema viejo: {set(campos_viejos)}")
        else:
            print("\n✓ ÉXITO: No se encontraron campos del sistema de conversión viejo")
        
        print("\n" + "="*80)
        print("✓ TEST COMPLETADO")
        print("="*80)
    else:
        print("\nADVERTENCIA: No se encontraron propiedades con precio")

if __name__ == "__main__":
    test_preservacion_moneda()
