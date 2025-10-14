#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Guía simple de procesamiento incremental para mayor control.

Ejemplos prácticos para procesar datos en lotes pequeños y seguros.
"""

def mostrar_ejemplos_uso():
    """
    Muestra ejemplos de comandos para procesamiento controlado.
    """
    print("GUIA DE PROCESAMIENTO INCREMENTAL")
    print("=" * 50)
    print()

    print("EJEMPLO 1: Procesar lote pequeño de prueba")
    print("-" * 40)
    print("python scripts/build_relevamiento_dataset_incremental.py --batch-size 10 --max-propiedades 10")
    print("Resultado: Procesa solo 10 propiedades y las guarda inmediatamente")
    print()

    print("EJEMPLO 2: Procesar solo 2 archivos")
    print("-" * 40)
    print("python scripts/build_relevamiento_dataset_incremental.py --batch-size 15 --max-archivos 2")
    print("Resultado: Procesa solo los primeros 2 archivos encontrados")
    print()

    print("EJEMPLO 3: Procesar lote mediano")
    print("-" * 40)
    print("python scripts/build_relevamiento_dataset_incremental.py --batch-size 25 --max-propiedades 50")
    print("Resultado: Procesa 50 propiedades en lotes de 25")
    print()

    print("EJEMPLO 4: Continuar desde donde se quedo")
    print("-" * 40)
    print("python scripts/build_relevamiento_dataset_incremental.py --continuar")
    print("Resultado: Reanuda desde el ultimo checkpoint guardado")
    print()

def verificar_estado_actual():
    """
    Verifica el estado actual del procesamiento.
    """
    import os
    import json
    from glob import glob

    print("ESTADO ACTUAL DEL PROCESAMIENTO")
    print("-" * 40)

    data_dir = "data"

    # Buscar archivos de base de datos
    archivos_db = glob(f"{data_dir}/base_datos_relevamiento*.json")
    archivos_db.sort()

    if archivos_db:
        print("Archivos de base de datos encontrados:")
        for archivo in archivos_db:
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                    total = datos.get('metadata', {}).get('total_propiedades', 0)
                    fecha = datos.get('metadata', {}).get('fecha_procesamiento', 'N/A')
                    print(f"  {os.path.basename(archivo)}: {total:,} propiedades")
                    print(f"    Fecha: {fecha}")
            except:
                print(f"  {os.path.basename(archivo)}: No se pudo leer")
    else:
        print("No se encontraron archivos de base de datos")

    # Verificar checkpoint
    checkpoint_file = f"{data_dir}/.procesamiento_checkpoint.json"
    if os.path.exists(checkpoint_file):
        print("Checkpoint pendiente encontrado:")
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                estado = json.load(f)
                print(f"  Propiedades procesadas: {estado.get('propiedades_procesadas', 0):,}")
                print(f"  Ultimo archivo: {estado.get('ultimo_archivo', 'N/A')}")
        except:
            print("  No se pudo leer el checkpoint")
    else:
        print("No hay checkpoint pendiente")

    print()

def mostrar_recomendaciones():
    """
    Muestra recomendaciones para el procesamiento.
    """
    print("RECOMENDACIONES DE USO")
    print("-" * 40)

    print("1. PRUEBA CON LOTES PEQUENOS:")
    print("   - Empieza con lotes de 10-20 propiedades")
    print("   - Verifica la calidad de los datos")
    print()

    print("2. ESCALA PROGRESIVA:")
    print("   - Aumenta gradualmente a 50-100 propiedades")
    print("   - Usa lotes de 20-50 para balance velocidad/seguridad")
    print()

    print("3. CONTROL DE ERRORES:")
    print("   - Si hay interrupcion, usa --continuar")
    print("   - Los checkpoints guardan progreso automaticamente")
    print()

    print("4. MONITOREO:")
    print("   - Revisa archivos .lote_*.json generados")
    print("   - Verifica consistencia de datos")
    print()

    print("5. LIMPIEZA:")
    print("   - Al final solo queda 'base_datos_relevamiento.json'")
    print("   - Los archivos temporales pueden eliminarse")
    print()

def main():
    """
    Función principal.
    """
    mostrar_ejemplos_uso()
    verificar_estado_actual()
    mostrar_recomendaciones()

    print("ACCIONES DISPONIBLES:")
    print("-" * 40)
    print("1. Copia y pega algun comando de ejemplo")
    print("2. Verifica los resultados en la carpeta data/")
    print("3. Usa --continuar si hay interrupciones")
    print("4. Monitorea el tamaño y calidad de los archivos generados")

if __name__ == "__main__":
    main()