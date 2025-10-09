#!/usr/bin/env python3
"""
Script para actualizar GitHub Projects después de cada commit.
Este script actualiza automáticamente las tarjetas del proyecto basado en el mensaje del commit.
"""

import subprocess
import json
import re
from datetime import datetime
import os

def run_command(cmd):
    """Ejecutar un comando y retornar la salida."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando comando: {e}")
        print(f"Stderr: {e.stderr}")
        return None

def get_latest_commit_message():
    """Obtener el mensaje del último commit."""
    return run_command("git log -1 --pretty=format:'%s'")

def update_project_status(commit_message):
    """Actualizar el estado de las tarjetas del proyecto basado en el commit."""

    # Configuración del proyecto
    project_id = "PVT_kwHOCLQG084BDlEf"
    status_field_id = "PVTSSF_lAHOCLQG084BDlEfzg1dQvI"
    done_option_id = "98236657"

    # Mapeo de palabras clave a IDs de items
    item_mapping = {
        'commit 1': 'PVTI_lAHOCLQG084BDlEfzge9tNs',
        'commit 2': 'PVTI_lAHOCLQG084BDlEfzge9tOc',
        'commit 3': 'PVTI_lAHOCLQG084BDlEfzge9tOk',
        'commit 4': 'PVTI_lAHOCLQG084BDlEfzge9tOs',
        'commit 5': 'PVTI_lAHOCLQG084BDlEfzge9tO4',
        'estructura': 'PVTI_lAHOCLQG084BDlEfzge9tNs',
        'motor': 'PVTI_lAHOCLQG084BDlEfzge9tOc',
        'test': 'PVTI_lAHOCLQG084BDlEfzge9tOk',
        'cli': 'PVTI_lAHOCLQG084BDlEfzge9tOs',
        'optimizacion': 'PVTI_lAHOCLQG084BDlEfzge9tO4',
        'docs': 'PVTI_lAHOCLQG084BDlEfzge9tNs',  # Para commits de documentación
        'readme': 'PVTI_lAHOCLQG084BDlEfzge9tNs'
    }

    # Analizar el commit para determinar qué tarjeta actualizar
    commit_lower = commit_message.lower()

    print(f"Analizando commit: {commit_message}")

    # Buscar el item correspondiente
    item_to_update = None
    for keyword, item_id in item_mapping.items():
        if keyword in commit_lower:
            item_to_update = item_id
            print(f"Item encontrado: {item_id} (keyword: {keyword})")
            break

    if item_to_update:
        # Actualizar el status del item a "Done"
        cmd = f'gh project item-edit --id {item_to_update} --field-id {status_field_id} --single-select-option-id {done_option_id} --project-id {project_id}'
        print(f"Ejecutando: {cmd}")
        result = run_command(cmd)
        if result is not None:  # El comando funciona incluso sin output
            print(f"OK: Item {item_to_update} actualizado a 'Done'")
            return True
        else:
            print(f"ERROR: No se pudo actualizar el item {item_to_update}")
            return False
    else:
        print("AVISO: No se encontró un item correspondiente al commit message")
        return False

def main():
    """Función principal."""
    print("Actualizando GitHub Projects después del commit...")

    # Obtener el último commit
    commit_message = get_latest_commit_message()
    if not commit_message:
        print("ERROR: No se pudo obtener el último commit")
        return False

    print(f"Ultimo commit: {commit_message}")

    # Actualizar el estado del proyecto
    success = update_project_status(commit_message)

    if success:
        print("OK: GitHub Projects actualizado exitosamente")
        return True
    else:
        print("ERROR: No se pudo actualizar GitHub Projects")
        return False

if __name__ == "__main__":
    main()