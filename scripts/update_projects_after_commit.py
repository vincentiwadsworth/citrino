#!/usr/bin/env python3
"""
Script para actualizar GitHub Projects después de cada commit al README.
Este script se ejecuta después de actualizar el README para sincronizar el estado del proyecto.
"""

import subprocess
import json
import re
from datetime import datetime
import sys

def run_command(cmd):
    """Ejecutar un comando y retornar la salida."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando comando: {e}")
        return None

def get_latest_commit_message():
    """Obtener el mensaje del último commit."""
    return run_command("git log -1 --pretty=format:'%s'")

def get_project_items():
    """Obtener los items del proyecto."""
    try:
        items_json = run_command('gh project item-list 2 --owner vincentiwadsworth --format json')
        if not items_json:
            return []

        items_data = json.loads(items_json)
        return items_data.get('items', [])
    except json.JSONDecodeError as e:
        print(f"Error decodificando JSON: {e}")
        return []

def get_project_id():
    """Obtener el ID del proyecto."""
    return "PVT_kwHOCLQG084BDlEf"

def get_status_field_id():
    """Obtener el ID del campo Status."""
    return "PVTSSF_lAHOCLQG084BDlEfzg1dQvI"

def update_project_status(commit_message):
    """Actualizar el estado de las tarjetas del proyecto basado en el commit."""
    items = get_project_items()

    if not items:
        print("No se encontraron items en el proyecto.")
        return

    # Analizar el commit para determinar qué tarjeta actualizar
    commit_lower = commit_message.lower()

    # Mapeo de palabras clave a IDs de items (usando los IDs de los items del proyecto)
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
        'optimizacion': 'PVTI_lAHOCLQG084BDlEfzge9tO4'
    }

    # Buscar el item correspondiente
    item_to_update = None
    for keyword, item_id in item_mapping.items():
        if keyword in commit_lower:
            item_to_update = item_id
            break

    if item_to_update:
        # Actualizar el status del item a "Done" usando el formato correcto
        cmd = f'gh project item-edit --id {item_to_update} --field-id {get_status_field_id()} --single-select-option-id "98236657" --project-id {get_project_id()}'
        result = run_command(cmd)
        if result:
            print(f"Item {item_to_update} actualizado a 'Done'")
        else:
            print(f"No se pudo actualizar el item {item_to_update}")
    else:
        print("No se encontró un item correspondiente al commit message")

def create_new_project_item(commit_message):
    """Crear un nuevo item en el proyecto si no existe uno correspondiente."""
    # Extraer el título del commit (eliminar prefijos como "docs:", "feat:", etc.)
    clean_title = re.sub(r'^(docs|feat|fix|test|perf|refactor|chore|build|style):\s*', '', commit_message)

    # Crear nuevo item
    result = run_command(f'gh project item-create --project-id 2 --title "{clean_title}" --body "Automatically created from commit: {commit_message}"')

    if result:
        print(f"Nuevo item creado: {clean_title}")
    else:
        print(f"No se pudo crear el item para: {clean_title}")

def main():
    """Función principal."""
    print("Actualizando GitHub Projects después del commit...")

    # Obtener el último commit
    commit_message = get_latest_commit_message()
    if not commit_message:
        print("No se pudo obtener el último commit")
        return

    print(f"Último commit: {commit_message}")

    # Intentar actualizar un item existente
    update_project_status(commit_message)

    # Opcional: Crear nuevo item si no hay correspondencia
    if '--create-new' in sys.argv:
        create_new_project_item(commit_message)

if __name__ == "__main__":
    main()