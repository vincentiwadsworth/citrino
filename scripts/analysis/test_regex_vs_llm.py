#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test comparativo: Regex vs LLM vs Híbrido
Mide la reducción de tokens y costo al usar el sistema híbrido.
"""

import sys
import os
import pandas as pd
from pathlib import Path

# Agregar src al path
sys.path.insert(0, 'src')

from regex_extractor import RegexExtractor
from description_parser import DescriptionParser

def main():
    print("="*80)
    print("TEST COMPARATIVO: Regex vs LLM vs Híbrido")
    print("="*80)
    
    # Leer muestra del Proveedor 02
    archivo = "data/raw/2025.08.29 02.xlsx"
    print(f"\nLeyendo: {archivo}")
    
    df = pd.read_excel(archivo, engine='openpyxl')
    df.columns = [c.lower().strip() for c in df.columns]
    
    if 'descripción' in df.columns:
        df = df.rename(columns={'descripción': 'descripcion'})
    if 'ubicación' in df.columns:
        df = df.rename(columns={'ubicación': 'ubicacion'})
    
    # Filtrar con descripción
    df_desc = df[df['descripcion'].notna()].copy()
    print(f"Total propiedades con descripción: {len(df_desc)}")
    
    # Tomar muestra de 10
    muestra = df_desc.head(10)
    print(f"Analizando muestra de {len(muestra)} propiedades\n")
    
    # Inicializar extractores
    print("Inicializando extractores...")
    regex_extractor = RegexExtractor()
    parser_hibrido = DescriptionParser(use_regex_first=True)
    
    print("\n" + "="*80)
    print("ANÁLISIS POR PROPIEDAD")
    print("="*80)
    
    resultados_regex = []
    
    for idx, row in muestra.iterrows():
        print(f"\nPROPIEDAD {idx + 1}:")
        print("-"*80)
        
        tipo = row.get('tipo', '')
        desc = str(row['descripcion'])
        
        print(f"Tipo: {tipo}")
        print(f"Descripción: {len(desc)} caracteres")
        
        # TEST 1: Solo Regex
        print("\n[1] EXTRACCIÓN CON REGEX:")
        regex_result = regex_extractor.extract_all(desc, tipo)
        campos_extraidos = regex_result.get('_regex_extraction_success', 0)
        print(f"  [OK] Campos extraidos: {campos_extraidos}")
        
        if regex_result.get('precio'):
            print(f"  - Precio: {regex_result['precio']} {regex_result.get('moneda', 'USD')}")
        if regex_result.get('habitaciones'):
            print(f"  - Habitaciones: {regex_result['habitaciones']}")
        if regex_result.get('banos'):
            print(f"  - Banos: {regex_result['banos']}")
        if regex_result.get('superficie'):
            print(f"  - Superficie: {regex_result['superficie']} m2")
        if regex_result.get('zona'):
            print(f"  - Zona: {regex_result['zona']}")
        if regex_result.get('amenities'):
            print(f"  - Amenities: {len(regex_result['amenities'])} encontrados")
        
        # Determinar si regex es suficiente
        tiene_precio = regex_result.get('precio') is not None
        tiene_zona = regex_result.get('zona') is not None
        tiene_superficie = regex_result.get('superficie') is not None
        es_suficiente = tiene_precio and (tiene_zona or tiene_superficie)
        
        if es_suficiente:
            print(f"  [OK] REGEX ES SUFICIENTE - No se necesita LLM")
            necesita_llm = False
        else:
            print(f"  [!] REGEX INSUFICIENTE - Se necesita LLM para completar")
            necesita_llm = True
        
        resultados_regex.append({
            'idx': idx,
            'campos_regex': campos_extraidos,
            'necesita_llm': necesita_llm
        })
        
        print("="*80)
    
    # RESUMEN
    print("\n" + "="*80)
    print("RESUMEN DE RESULTADOS")
    print("="*80)
    
    total = len(resultados_regex)
    solo_regex = sum(1 for r in resultados_regex if not r['necesita_llm'])
    necesita_llm = sum(1 for r in resultados_regex if r['necesita_llm'])
    promedio_campos = sum(r['campos_regex'] for r in resultados_regex) / total
    
    print(f"\nTotal propiedades analizadas: {total}")
    print(f"  [OK] Solo con Regex (sin LLM): {solo_regex} ({solo_regex/total*100:.1f}%)")
    print(f"  [!] Requieren LLM:             {necesita_llm} ({necesita_llm/total*100:.1f}%)")
    print(f"  [*] Promedio campos/regex:    {promedio_campos:.1f}")
    
    # Estimacion de ahorro
    print(f"\n[$] ESTIMACION DE AHORRO:")
    print(f"  - Llamadas LLM evitadas: {solo_regex} de {total}")
    print(f"  - Reduccion de llamadas: {solo_regex/total*100:.1f}%")
    
    # Costo aproximado (basado en GLM-4.6: ~$0.001 por 1K tokens)
    # Asumiendo ~500 tokens por llamada completa
    tokens_por_llamada_completa = 500
    tokens_por_llamada_parcial = 250
    
    tokens_sin_regex = total * tokens_por_llamada_completa
    tokens_con_regex = (solo_regex * 0) + (necesita_llm * tokens_por_llamada_parcial)
    
    print(f"\n[TOKENS]:")
    print(f"  - Sin Regex (LLM siempre):   {tokens_sin_regex:,} tokens")
    print(f"  - Con Regex (hibrido):       {tokens_con_regex:,} tokens")
    print(f"  - Reduccion:                 {tokens_sin_regex - tokens_con_regex:,} tokens ({(1-tokens_con_regex/tokens_sin_regex)*100:.1f}%)")
    
    # Para el dataset completo (1,579 propiedades)
    total_props = 1579
    llamadas_evitadas = int(total_props * (solo_regex/total))
    tokens_ahorrados = int(total_props * tokens_por_llamada_completa * (solo_regex/total))
    
    print(f"\n[PROYECCION] PARA TODO EL PROVEEDOR 02 ({total_props} propiedades):")
    print(f"  - Llamadas LLM evitadas:     {llamadas_evitadas:,}")
    print(f"  - Tokens ahorrados:          {tokens_ahorrados:,}")
    print(f"  - Costo evitado (aprox):     ${tokens_ahorrados * 0.001 / 1000:.2f}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
