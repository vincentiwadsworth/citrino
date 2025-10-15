#!/usr/bin/env python3
"""
Script de debugging para analizar la estructura de la Guía Urbana
y detectar problemas en el parsing de coordenadas.
"""

import pandas as pd
import re

def analizar_guia_urbana():
    """Analiza la estructura de la guía urbana para debugging."""

    # Leer archivo
    df_raw = pd.read_excel('data/raw/guia/GUIA URBANA.xlsx', header=None)
    print(f"Dimensiones crudas: {df_raw.shape}")

    # Encontrar fila de headers
    header_row = None
    for idx, row in df_raw.iterrows():
        valores_unicos = set(str(cell).strip() for cell in row if pd.notna(cell) and str(cell).strip() not in ['', 'nan'])
        if any(header in valores_unicos for header in ['UV', 'MZ', 'SUB_SISTEM', 'NIVEL', 'GOOGLE_MAP']):
            header_row = idx
            print(f"Fila de headers detectada en índice {idx}: {list(valores_unicos)}")
            break

    # Leer con headers detectados
    df = pd.read_excel('data/raw/guia/GUIA URBANA.xlsx', header=header_row)
    print(f"\nDataFrame con headers: {df.shape}")
    print(f"Columnas: {list(df.columns)}")

    # Analizar primeras filas de datos
    print("\nPrimeras 10 filas de datos:")
    for idx in range(min(10, len(df))):
        row = df.iloc[idx]
        print(f"\nFila {idx}:")
        for col in df.columns:
            value = row[col]
            if pd.notna(value) and str(value).strip() not in ['', 'nan']:
                print(f"  {col}: {value}")

    # Buscar coordenadas en el dataset
    print("\n=== BÚSQUEDA DE COORDENADAS ===")
    coordenadas_encontradas = []

    for idx, row in df.iterrows():
        for col in df.columns:
            value = str(row[col])
            if re.search(r'-?\d+\.\d+,\s*-?\d+\.\d+', value):
                coordenadas_encontradas.append((idx, col, value))
                if len(coordenadas_encontradas) <= 5:  # Primeras 5
                    print(f"Fila {idx}, Columna {col}: {value}")

    print(f"\nTotal coordenadas encontradas: {len(coordenadas_encontradas)}")

    # Analizar distribución de UVs
    print("\n=== DISTRIBUCIÓN DE UV ===")
    uvs = set()
    for idx, row in df.iterrows():
        for col in df.columns:
            value = str(row[col]).strip()
            if value.startswith('UV') and len(value) > 2:
                uvs.add(value)

    print(f"UVs únicos encontrados: {sorted(list(uvs))[:10]}...")
    print(f"Total UVs: {len(uvs)}")

if __name__ == "__main__":
    analizar_guia_urbana()