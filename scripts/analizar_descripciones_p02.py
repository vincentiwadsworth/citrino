#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analizar descripciones del Proveedor 02 para identificar patrones extraíbles con regex."""

import pandas as pd
import json

def main():
    archivo = "data/raw/2025.08.29 02.xlsx"
    print(f"Leyendo: {archivo}\n")
    
    df = pd.read_excel(archivo, engine='openpyxl')
    df.columns = [c.lower().strip() for c in df.columns]
    
    # Mapear descripción
    if 'descripción' in df.columns:
        df = df.rename(columns={'descripción': 'descripcion'})
    if 'ubicación' in df.columns:
        df = df.rename(columns={'ubicación': 'ubicacion'})
    
    print(f"Total filas: {len(df)}")
    print(f"Columnas: {list(df.columns)}\n")
    
    # Filtrar con descripción
    df_desc = df[df['descripcion'].notna()].copy()
    print(f"Con descripción: {len(df_desc)}\n")
    
    # Tomar muestra
    muestra = df_desc.head(10)
    
    print("="*80)
    for idx, row in muestra.iterrows():
        print(f"\nEJEMPLO {idx + 1}:")
        print("-"*80)
        print(f"Tipo: {row.get('tipo', 'N/A')}")
        print(f"Ubicación: {row.get('ubicacion', 'N/A')}")
        
        desc = str(row['descripcion'])
        # Limpiar emojis para poder imprimir
        desc_clean = desc.encode('ascii', 'ignore').decode('ascii')
        
        print(f"\nDescripción ({len(desc)} chars):")
        print(desc_clean[:400])
        if len(desc) > 400:
            print("...")
        print("="*80)

if __name__ == "__main__":
    main()
