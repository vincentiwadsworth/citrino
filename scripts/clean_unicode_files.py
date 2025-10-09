#!/usr/bin/env python3
"""
Script para limpiar caracteres Unicode problemáticos de archivos existentes.
Este script busca y reemplaza emojis y otros caracteres Unicode que causan
problemas en entornos Windows.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Configurar entorno para manejo Unicode
os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents'))
from unicode_utils import remove_problematic_chars

def find_files_with_unicode(directory: str = '.', extensions: List[str] = None) -> List[Path]:
    """Encontrar archivos con caracteres Unicode problemáticos."""
    if extensions is None:
        extensions = ['.py', '.md', '.txt', '.sh', '.yml', '.yaml', '.json']

    unicode_files = []
    directory_path = Path(directory)

    # Patrones de caracteres Unicode problemáticos
    unicode_patterns = [
        r'[\u2700-\u27BF]',  # Dingbats
        r'[\u2600-\u26FF]',  # Miscellaneous Symbols
        r'[\u1F300-\u1F5FF]', # Miscellaneous Symbols and Pictographs
        r'[\u1F600-\u1F64F]', # Emoticons
        r'[\u1F680-\u1F6FF]', # Transport and Map Symbols
    ]

    for extension in extensions:
        for file_path in directory_path.rglob(f'*{extension}'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Buscar caracteres problemáticos
                for pattern in unicode_patterns:
                    if re.search(pattern, content):
                        unicode_files.append(file_path)
                        break
            except (UnicodeDecodeError, PermissionError):
                continue

    return unicode_files

def clean_file(file_path: Path) -> Tuple[bool, int]:
    """Limpiar caracteres Unicode de un archivo."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # Contar caracteres problemáticos antes de limpiar
        unicode_patterns = [
            r'[\u2700-\u27BF\u2600-\u26FF\u1F300-\u1F5FF\u1F600-\u1F64F\u1F680-\u1F6FF]'
        ]
        total_problematic = 0
        for pattern in unicode_patterns:
            matches = re.findall(pattern, original_content)
            total_problematic += len(matches)

        if total_problematic == 0:
            return True, 0

        # Limpiar contenido
        cleaned_content = remove_problematic_chars(original_content)

        # Verificar si hubo cambios
        if cleaned_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            return True, total_problematic
        else:
            return True, 0

    except Exception as e:
        print(f"Error procesando {file_path}: {e}")
        return False, 0

def main():
    """Función principal."""
    print("Buscando archivos con caracteres Unicode problemáticos...")
    print()

    # Encontrar archivos con Unicode
    unicode_files = find_files_with_unicode()

    if not unicode_files:
        print("No se encontraron archivos con caracteres Unicode problemáticos.")
        return

    print(f"Se encontraron {len(unicode_files)} archivos con caracteres Unicode:")
    for file_path in unicode_files:
        print(f"  - {file_path}")
    print()

    # Limpiar archivos
    print("Limpiando archivos...")
    print("-" * 50)

    total_cleaned = 0
    total_files_processed = 0

    for file_path in unicode_files:
        print(f"Procesando: {file_path}")
        success, count = clean_file(file_path)

        if success:
            if count > 0:
                print(f"  OK: Limpiados {count} caracteres problemáticos")
                total_cleaned += count
            else:
                print(f"  OK: No se encontraron caracteres para limpiar")
            total_files_processed += 1
        else:
            print(f"  ERROR: Error al procesar el archivo")

    print()
    print("Resumen:")
    print(f"  Archivos procesados: {total_files_processed}")
    print(f"  Caracteres limpiados: {total_cleaned}")

    if total_cleaned > 0:
        print(f"\nOK: Se han limpiado {total_cleaned} caracteres Unicode problemáticos.")
    else:
        print(f"\nOK: No se encontraron caracteres para limpiar.")

if __name__ == "__main__":
    main()