#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de setup para Chatbot UI Citrino

Este script facilita la configuración inicial del entorno
para ejecutar Chatbot UI con la API de Citrino.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def create_env_file():
    """Crea el archivo .env desde el template."""
    env_example = Path('.env.example')
    env_file = Path('.env')

    if env_file.exists():
        print(" Archivo .env ya existe")
        return True

    if not env_example.exists():
        print(" No se encuentra el archivo .env.example")
        return False

    # Copiar template a .env
    with open(env_example, 'r', encoding='utf-8') as f:
        content = f.read()

    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(" Archivo .env creado desde template")
    print("  Recuerda configurar tus API keys en .env")
    return True

def check_docker():
    """Verifica si Docker está instalado."""
    try:
        result = subprocess.run(['docker', '--version'],
                              capture_output=True, text=True)
        print(f" Docker encontrado: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print(" Docker no está instalado")
        print("   Por favor, instala Docker desde https://docker.com")
        return False

def check_docker_compose():
    """Verifica si docker-compose está instalado."""
    try:
        result = subprocess.run(['docker-compose', '--version'],
                              capture_output_output=True, text=True)
        print(f" Docker Compose encontrado: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print(" Docker Compose no está instalado")
        print("   Por favor, instala Docker Compose")
        return False

def create_directories():
    """Crea los directorios necesarios."""
    directories = ['config', 'db', 'logs']

    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f" Directorio '{directory}' listo")

def check_dependencies():
    """Verifica las dependencias del proyecto."""
    parent_dir = Path('..')
    required_files = [
        parent_dir / 'api' / 'server.py',
        parent_dir / 'src' / 'llm_integration.py',
        parent_dir / 'src' / 'recommendation_engine_mejorado.py',
        parent_dir / 'data' / 'metrics'
    ]

    missing_files = []
    for file_path in required_files:
        if not file_path.exists():
            missing_files.append(str(file_path))

    if missing_files:
        print(" Archivos requeridos faltantes:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False

    print(" Todas las dependencias encontradas")
    return True

def generate_dockerfile():
    """Genera Dockerfile para la API si no existe."""
    dockerfile_path = Path('..') / 'Dockerfile'

    if dockerfile_path.exists():
        print(" Dockerfile ya existe")
        return True

    dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del proyecto
COPY . .

# Exponer puerto
EXPOSE 5001

# Iniciar la aplicación
CMD ["python", "api/server.py"]
"""

    with open(dockerfile_path, 'w', encoding='utf-8') as f:
        f.write(dockerfile_content)

    print(" Dockerfile generado")
    return True

def check_data_files():
    """Verifica que existan archivos de datos."""
    parent_dir = Path('..')
    data_dir = parent_dir / 'data'

    if not data_dir.exists():
        print(" Directorio de datos no encontrado")
        return False

    # Buscar archivos de análisis generados
    analysis_files = list(data_dir.glob('metrics/analisis_data_raw_*.json'))

    if analysis_files:
        latest_file = max(analysis_files, key=os.path.getctime)
        print(f" Archivo de análisis encontrado: {latest_file.name}")

        # Verificar que contenga propiedades
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                prop_count = len(data.get('propiedades', []))
                print(f" {prop_count} propiedades en el análisis")
                return prop_count > 0
        except Exception as e:
            print(f"  Error leyendo archivo de análisis: {e}")
            return False
    else:
        print("  No se encontraron archivos de análisis en data/metrics/")
        print("   Ejecuta primero: python scripts/analysis/procesar_y_analizar_raw.py")
        return False

def run_setup():
    """Ejecuta el setup completo."""
    print("="*60)
    print(" SETUP DE CHATBOT UI - CITRINO")
    print("="*60)

    # Cambiar al directorio del chatbot
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    steps = [
        ("Verificando Docker", check_docker),
        ("Verificando Docker Compose", check_docker_compose),
        ("Creando directorios", create_directories),
        ("Creando archivo .env", create_env_file),
        ("Verificando dependencias", check_dependencies),
        ("Verificando archivos de datos", check_data_files),
        ("Generando Dockerfile", generate_dockerfile),
    ]

    all_good = True
    for step_name, step_func in steps:
        print(f"\n {step_name}...")
        if not step_func():
            all_good = False

    if all_good:
        print("\n" + "="*60)
        print(" SETUP COMPLETADO")
        print("="*60)
        print("\n PRÓXIMOS PASOS:")
        print("1. Configura tus API keys en .env:")
        print("   - ZAI_API_KEY=clave_zai")
        print("   - OPENROUTER_API_KEY=clave_openrouter")
        print("\n2. Inicia el chatbot:")
        print("   docker-compose -f docker-compose.dev.yml up")
        print("\n3. Accede a:")
        print("   - Chatbot UI: http://localhost:3000")
        print("   - API Citrino: http://localhost:5001")
        print("   - Health Check: http://localhost:5001/api/health")
        print("\n Para más información, consulta README.md")
        return True
    else:
        print("\n SETUP INCOMPLETO")
        print("Por favor, resuelve los problemas indicados arriba.")
        return False

def show_help():
    """Muestra la ayuda del script."""
    print("""
 SETUP DE CHATBOT UI - CITRINO

Uso:
  python setup.py    - Ejecuta el setup completo

Este script verifica y configura el entorno necesario para
ejecutar Chatbot UI con la API de Citrino.

Requisitos:
- Docker y Docker Compose instalados
- API keys para Z.AI y OpenRouter (opcional)
- Archivos de datos procesados del primer commit

Para más información, consulta README.md
""")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        show_help()
    else:
        success = run_setup()
        sys.exit(0 if success else 1)