import pandas as pd
import glob

# Encontrar archivo del proveedor 02
archivos = glob.glob('data/raw/*02.xlsx')
if archivos:
    archivo = [a for a in archivos if not a.startswith('data/raw/~$')][0]
    print(f"Archivo: {archivo}\n")
    
    # Leer Excel
    df = pd.read_excel(archivo, engine='openpyxl')
    
    # Ver cuántas tienen descripción
    desc_col = 'Descripción'
    if desc_col in df.columns:
        con_desc = df[desc_col].notna() & (df[desc_col].astype(str).str.strip() != '') & (df[desc_col].astype(str).str.lower() != 'nan')
        print(f"Filas con descripción: {con_desc.sum()} de {len(df)}")
        
        # Mostrar algunas descripciones
        filas_con_desc = df[con_desc].head(5)
        print(f"\nPrimeras 5 filas con descripción:")
        for idx, row in filas_con_desc.iterrows():
            desc = str(row[desc_col])[:100]
            print(f"\n  Fila {idx}:")
            print(f"    Tipo: {row.get('Tipo', 'N/A')}")
            print(f"    Ubicación: {row.get('Ubicación', 'N/A')[:40]}")
            print(f"    Descripción: {desc}...")
    else:
        print("NO SE ENCONTRÓ COLUMNA 'Descripción'")
        print(f"Columnas: {list(df.columns)}")
