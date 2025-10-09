import pandas as pd
import glob

# Encontrar archivo del proveedor 02
archivos = glob.glob('data/raw/*02.xlsx')
if archivos:
    archivo = [a for a in archivos if not a.startswith('data/raw/~$')][0]
    print(f"Archivo: {archivo}\n")
    
    # Leer Excel
    df = pd.read_excel(archivo, engine='openpyxl')
    
    print(f"Total filas: {len(df)}")
    print(f"\nColumnas encontradas ({len(df.columns)}):")
    for i, col in enumerate(df.columns):
        print(f"{i}: {col}")
    
    # Mostrar primera fila con datos
    print(f"\n\nPrimera fila (valores no nulos):")
    first_row = df.iloc[0]
    for col in df.columns:
        val = first_row[col]
        if pd.notna(val) and str(val).strip():
            print(f"  {col}: {str(val)[:60]}...")
