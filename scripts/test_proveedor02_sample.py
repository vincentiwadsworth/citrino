"""
Test de extracción LLM con muestra del Proveedor 02
"""
import sys
import os
import pandas as pd
from pathlib import Path

# Agregar src al path
sys.path.insert(0, 'src')

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv()

# Verificar que las variables estén configuradas
if not os.getenv('ZAI_API_KEY'):
    print("ERROR: ZAI_API_KEY no está configurada en .env")
    sys.exit(1)

from description_parser import DescriptionParser

def main():
    # Leer archivo del Proveedor 02
    archivo = "data/raw/2025.08.29 02.xlsx"
    print(f"Leyendo archivo: {archivo}\n")
    
    df = pd.read_excel(archivo, engine='openpyxl')
    
    # Estandarizar nombres de columnas
    df.columns = [col.lower().strip().replace(' ', '_') for col in df.columns]
    
    # Mapear descripción con acento
    if 'descripción' in df.columns:
        df = df.rename(columns={'descripción': 'descripcion'})
    
    print(f"Total filas: {len(df)}")
    print(f"Columnas: {list(df.columns)}\n")
    
    # Filtrar solo filas con descripción
    df_con_desc = df[df['descripcion'].notna() & (df['descripcion'].astype(str).str.strip() != '')]
    print(f"Filas con descripcion: {len(df_con_desc)}\n")
    
    # Tomar las primeras 5
    sample = df_con_desc.head(5)
    
    # Inicializar parser
    print("Inicializando parser LLM...")
    parser = DescriptionParser()
    print(f"Parser inicializado. Configuracion: {parser.llm.obtener_info_configuracion()}\n")
    
    # Procesar cada propiedad
    print("="*80)
    for idx, row in sample.iterrows():
        print(f"\nPROPIEDAD {idx + 1}:")
        print("-"*80)
        
        # Mostrar datos originales
        tipo = row.get('tipo', '')
        precio_orig = row.get('precio', '')
        ubicacion = row.get('ubicación', row.get('ubicacion', ''))
        descripcion_full = str(row['descripcion'])
        
        print(f"Tipo: {tipo}")
        print(f"Precio original: {precio_orig}")
        print(f"Ubicacion: {ubicacion}")
        print(f"Descripcion length: {len(descripcion_full)} chars")
        
        # Extraer con LLM
        print("\n[Extrayendo con GLM-4.6...]")
        try:
            resultado = parser.extract_from_description(
                descripcion=str(row['descripcion']),
                titulo=str(row.get('tipo', ''))
            )
            
            print("\n[RESULTADO EXTRAIDO]:")
            print(f"  Precio: {resultado.get('precio')} {resultado.get('moneda', '')}")
            print(f"  Habitaciones: {resultado.get('habitaciones')}")
            print(f"  Banos: {resultado.get('banos')}")
            print(f"  Superficie: {resultado.get('superficie')} m2")
            print(f"  Zona: {resultado.get('zona')}")
            print(f"  Tipo: {resultado.get('tipo_propiedad')}")
            
        except Exception as e:
            print(f"\n[ERROR]: {e}")
        
        print("="*80)
    
    # Mostrar estadísticas
    print("\n\nESTADISTICAS:")
    print(f"  Total requests: {parser.stats['total_requests']}")
    print(f"  Cache hits: {parser.stats['cache_hits']}")
    print(f"  LLM calls: {parser.stats['llm_calls']}")
    print(f"  Errors: {parser.stats['errors']}")

if __name__ == "__main__":
    main()
