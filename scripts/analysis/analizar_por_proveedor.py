#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script temporal para analizar calidad de datos por proveedor.
"""

import json
from collections import defaultdict
from pathlib import Path

def analizar_por_proveedor():
    """Analiza la calidad de datos agrupados por código de proveedor."""
    
    ruta_datos = Path("data/base_datos_relevamiento.json")
    
    print("Cargando datos...")
    with open(ruta_datos, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    propiedades = data.get('propiedades', [])
    print(f"Total propiedades: {len(propiedades)}\n")
    
    # Agrupar por proveedor
    proveedores = defaultdict(list)
    for prop in propiedades:
        codigo = prop.get('codigo_proveedor', 'DESCONOCIDO')
        proveedores[codigo].append(prop)
    
    print("="*80)
    print("ANÁLISIS DE CALIDAD POR PROVEEDOR")
    print("="*80)
    
    resultados = []
    
    for codigo in sorted(proveedores.keys()):
        props = proveedores[codigo]
        total = len(props)
        
        # Analizar calidad de datos
        con_precio = sum(1 for p in props if p.get('precio'))
        con_zona = sum(1 for p in props if p.get('zona'))
        con_coords = sum(1 for p in props if p.get('latitud') and p.get('longitud'))
        con_superficie = sum(1 for p in props if p.get('superficie'))
        con_habitaciones = sum(1 for p in props if p.get('habitaciones'))
        con_banos = sum(1 for p in props if p.get('banos'))
        con_titulo = sum(1 for p in props if p.get('titulo'))
        
        # Ver fuente de datos
        fuentes = set(p.get('fuente_datos') for p in props if p.get('fuente_datos'))
        
        # Calcular score de calidad
        campos_criticos = [con_precio, con_zona, con_coords]
        score = (sum(campos_criticos) / (3 * total)) * 100 if total > 0 else 0
        
        resultados.append({
            'codigo': codigo,
            'total': total,
            'score': score,
            'con_precio': con_precio,
            'con_zona': con_zona,
            'con_coords': con_coords,
            'con_superficie': con_superficie,
            'con_habitaciones': con_habitaciones,
            'con_banos': con_banos,
            'con_titulo': con_titulo,
            'fuentes': fuentes
        })
    
    # Ordenar por score (peor primero)
    resultados.sort(key=lambda x: x['score'])
    
    for r in resultados:
        estado = "[CRITICO]" if r['score'] < 30 else "[REGULAR]" if r['score'] < 60 else "[BUENO]"
        print(f"\n{estado} PROVEEDOR {r['codigo']} ({r['total']} propiedades)")
        print(f"   Score de Calidad:    {r['score']:.1f}%")
        print(f"   Con precio:          {r['con_precio']:4d} ({r['con_precio']/r['total']*100:5.1f}%)")
        print(f"   Con zona:            {r['con_zona']:4d} ({r['con_zona']/r['total']*100:5.1f}%)")
        print(f"   Con coordenadas:     {r['con_coords']:4d} ({r['con_coords']/r['total']*100:5.1f}%)")
        print(f"   Con superficie:      {r['con_superficie']:4d} ({r['con_superficie']/r['total']*100:5.1f}%)")
        print(f"   Con habitaciones:    {r['con_habitaciones']:4d} ({r['con_habitaciones']/r['total']*100:5.1f}%)")
        print(f"   Con baños:           {r['con_banos']:4d} ({r['con_banos']/r['total']*100:5.1f}%)")
        print(f"   Con título:          {r['con_titulo']:4d} ({r['con_titulo']/r['total']*100:5.1f}%)")
        if r['fuentes']:
            print(f"   Fuentes detectadas:  {', '.join(r['fuentes'])}")
    
    print("\n" + "="*80)
    print("RESUMEN")
    print("="*80)
    peor = resultados[0]
    print(f"\n*** PROVEEDOR CON PEORES RESULTADOS: {peor['codigo']}")
    print(f"   - {peor['total']} propiedades ({peor['total']/len(propiedades)*100:.1f}% del total)")
    print(f"   - Score de calidad: {peor['score']:.1f}%")
    print(f"   - Solo {peor['con_precio']} propiedades con precio ({peor['con_precio']/peor['total']*100:.1f}%)")
    print(f"   - Solo {peor['con_zona']} propiedades con zona ({peor['con_zona']/peor['total']*100:.1f}%)")
    print(f"   - {peor['con_coords']} propiedades con coordenadas ({peor['con_coords']/peor['total']*100:.1f}%)")
    
    if fuentes := peor['fuentes']:
        print(f"   - Fuentes: {', '.join(fuentes)}")
    
    print("\nDISTRIBUCION DE PROPIEDADES:")
    for r in sorted(resultados, key=lambda x: x['total'], reverse=True):
        barra = "█" * int(r['total'] / len(propiedades) * 50)
        print(f"   Proveedor {r['codigo']}: {barra} {r['total']:4d} ({r['total']/len(propiedades)*100:5.1f}%)")
    
    print("\n")

if __name__ == "__main__":
    analizar_por_proveedor()
