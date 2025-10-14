import pandas as pd
import glob

# Encontrar archivo del proveedor 02
archivos = glob.glob('data/raw/*02.xlsx')
if archivos:
    archivo = [a for a in archivos if not a.startswith('data/raw/~$')][0]
    
    # Leer Excel
    df = pd.read_excel(archivo, engine='openpyxl')
    
    print("Columnas originales:")
    for col in df.columns:
        print(f"  '{col}'")
    
    # Aplicar transformación como en el código
    df.columns = [col.lower().strip().replace(' ', '_') for col in df.columns]
    
    print("\nColumnas después de transformación:")
    for col in df.columns:
        print(f"  '{col}'")
    
    # Verificar si 'descripcion' está
    if 'descripcion' in df.columns:
        print("\n✓ La columna 'descripcion' existe después del mapeo")
    elif 'descripción' in df.columns:
        print("\n✗ La columna es 'descripción' (con acento)")
    else:
        print("\n✗ No se encontró columna de descripción")
        print(f"Columnas disponibles: {list(df.columns)}")
