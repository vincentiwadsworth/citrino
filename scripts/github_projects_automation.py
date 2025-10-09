#!/usr/bin/env python3
"""
Script para automatizar la gestión de GitHub Projects basado en commits.
Este script analiza los commits recientes y actualiza las tarjetas del proyecto automáticamente.
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

def get_recent_commits(limit=10):
    """Obtener los commits más recientes."""
    commits = run_command("git log --oneline -{}".format(limit))
    if not commits:
        return []

    commit_list = []
    for line in commits.split('\n'):
        if line.strip():
            parts = line.split(' ', 1)
            if len(parts) == 2:
                commit_hash, message = parts
                commit_list.append({
                    'hash': commit_hash,
                    'message': message.strip()
                })

    return commit_list

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

def analyze_commit_type(commit_message):
    """Analizar el tipo de commit basado en el mensaje."""
    # Patrones para identificar tipos de commits
    patterns = {
        'feat': r'^(feat|feature):',
        'fix': r'^(fix|bugfix):',
        'docs': r'^(docs|documentation):',
        'test': r'^(test|testing):',
        'perf': r'^(perf|performance):',
        'refactor': r'^(refactor|refactoring):',
        'chore': r'^(chore|maintenance):',
        'build': r'^(build|ci):',
        'style': r'^(style|formatting):'
    }

    for commit_type, pattern in patterns.items():
        if re.match(pattern, commit_message, re.IGNORECASE):
            return commit_type

    return 'other'

def get_project_status():
    """Obtener el estado actual del proyecto."""
    # Obtener información del proyecto
    project_info = run_command('gh project view 2 --owner vincentiwadsworth --format json')
    if project_info:
        try:
            project_data = json.loads(project_info)
            return {
                'total_items': project_data.get('items', {}).get('totalCount', 0),
                'closed': project_data.get('closed', False),
                'title': project_data.get('title', 'Unknown Project')
            }
        except json.JSONDecodeError:
            pass

    return {'total_items': 0, 'closed': False, 'title': 'Unknown Project'}

def generate_dashboard():
    """Generar un dashboard para el README."""
    commits = get_recent_commits(15)
    project_status = get_project_status()
    items = get_project_items()

    # Analizar commits por tipo
    commit_types = {}
    for commit in commits:
        commit_type = analyze_commit_type(commit['message'])
        commit_types[commit_type] = commit_types.get(commit_type, 0) + 1

    # Generar dashboard
    dashboard = f"""
## GRAFICO: Dashboard del Proyecto

Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### 📈 Estado General
- **Proyecto**: {project_status['title']}
- **Total de Tareas**: {project_status['total_items']}
- **Commits Recientes**: {len(commits)}
- **Estado**: {'OK: Activo' if not project_status['closed'] else '⏸️ Inactivo'}

### ACTUALIZANDO: Actividad Reciente
"""

    # Añadir commits recientes
    if commits:
        dashboard += "#### DOC: Últimos Commits\n"
        for i, commit in enumerate(commits[:8], 1):
            commit_type = analyze_commit_type(commit['message'])
            emoji = {
                'feat': 'NUEVO:',
                'fix': 'CONFIG:',
                'docs': '📚',
                'test': '🧪',
                'perf': '⚡',
                'refactor': 'ACTUALIZANDO:',
                'chore': '🧹',
                'build': '🔨',
                'style': '💎'
            }.get(commit_type, 'DOC:')

            dashboard += f"{i}. {emoji} `{commit['hash'][:7]}` {commit['message']}\n"

    # Añadir distribución por tipo
    if commit_types:
        dashboard += f"\n#### GRAFICO: Distribución de Commits\n"
        for commit_type, count in sorted(commit_types.items()):
            emoji = {
                'feat': 'NUEVO:',
                'fix': 'CONFIG:',
                'docs': '📚',
                'test': '🧪',
                'perf': '⚡',
                'refactor': 'ACTUALIZANDO:',
                'chore': '🧹',
                'build': '🔨',
                'style': '💎',
                'other': 'DOC:'
            }.get(commit_type, 'DOC:')
            dashboard += f"- {emoji} **{commit_type.upper()}**: {count} commits\n"

    # Añadir items del proyecto
    if items:
        dashboard += f"\n#### 📋 Tareas del Proyecto ({len(items)} items)\n"
        for i, item in enumerate(items[:6], 1):
            title = item.get('title', 'Sin título')
            # Eliminar emojis del título para mejor visualización
            clean_title = re.sub(r'^[OK:⏳ACTUALIZANDO:⏸️]+ ', '', title)
            dashboard += f"{i}. {clean_title}\n"

    return dashboard

if __name__ == "__main__":
    # Generar dashboard y guardarlo en un archivo
    dashboard_content = generate_dashboard()

    # Guardar en archivo temporal
    with open('dashboard_temp.md', 'w', encoding='utf-8') as f:
        f.write(dashboard_content)

    print("Dashboard generado exitosamente:")
    print("=" * 50)
    print(dashboard_content)
    print("=" * 50)

    # Opcional: actualizar el README automáticamente
    if '--update-readme' in sys.argv:
        print("\nACTUALIZANDO: Actualizando README.md...")
        # Aquí podríamos agregar lógica para actualizar el README
        print("AVISO: Actualización automática del README aún no implementada")