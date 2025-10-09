#!/usr/bin/env python3
"""
Script de verificación de servicios para la reunión
Ejecutar este script para confirmar que todo está funcionando
"""

import requests
import time
import subprocess
import sys
from datetime import datetime

def check_api():
    """Verificar si la API está funcionando"""
    try:
        response = requests.get("http://localhost:5000/api/health", timeout=3)
        if response.status_code == 200:
            data = response.json()
            print("[OK] API: Funcionando correctamente")
            print(f"     Propiedades: {data.get('total_propiedades', 0):,}")
            return True
        else:
            print(f"[ERROR] API: Error HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] API: No responde - {e}")
        return False

def check_streamlit():
    """Verificar si Streamlit está accesible"""
    try:
        response = requests.get("http://localhost:8501", timeout=3)
        if response.status_code == 200:
            print("[OK] Streamlit: Funcionando correctamente")
            return True
        else:
            print(f"[ERROR] Streamlit: Error HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Streamlit: No responde - {e}")
        return False

def start_api_if_needed():
    """Iniciar API si no está corriendo"""
    try:
        # Verificar si el puerto 5000 está en uso
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
        if ':5000' not in result.stdout:
            print("[INFO] Iniciando servidor API...")
            subprocess.Popen(['python', 'api/server.py'],
                           cwd=r'C:\Users\nicol\OneDrive\Documentos\trabajo\citrino\citrino')
            time.sleep(3)
            return check_api()
        else:
            return check_api()
    except Exception as e:
        print(f"[ERROR] Error al iniciar API: {e}")
        return False

def main():
    print("VERIFICACION DE SERVICIOS CITRINO")
    print("=" * 40)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Verificar API
    api_ok = start_api_if_needed()

    # Verificar Streamlit
    streamlit_ok = check_streamlit()

    print()
    print("RESUMEN:")
    print("=" * 20)

    if api_ok and streamlit_ok:
        print("TODOS LOS SERVICIOS FUNCIONAN")
        print()
        print("ACCESO DEMO:")
        print("   http://localhost:8501")
        print()
        print("ACCESO API:")
        print("   http://localhost:5000")
        print()
        print("LISTO PARA LA REUNION")
        return 0
    elif api_ok:
        print("SOLO API FUNCIONA")
        print("   Streamlit necesita ser iniciado manualmente")
        return 1
    elif streamlit_ok:
        print("SOLO STREAMLIT FUNCIONA")
        print("   La API puede no responder correctamente")
        return 1
    else:
        print("NINGUN SERVICIO FUNCIONA")
        print()
        print("SOLUCIONES:")
        print("1. Ejecutar: iniciar_demo.bat")
        print("2. Verificar que Python este instalado")
        print("3. Revisar bloqueos de firewall/antivirus")
        return 2

if __name__ == "__main__":
    sys.exit(main())