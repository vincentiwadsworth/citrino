#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Prueba de Configuración LLM

Verifica que la configuración de LLM sea correcta y prueba la conexión.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar path para importar módulos
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from llm_integration import LLMIntegration

def test_configuracion():
    """Prueba la configuración del LLM."""
    print("CONFIGURACION LLM")
    print("=" * 50)

    # Crear instancia de LLM
    llm = LLMIntegration()

    # Mostrar configuración
    config_info = llm.obtener_info_configuracion()
    print("Configuracion actual:")
    for key, value in config_info.items():
        print(f"  {key}: {value}")

    # Validar configuración
    if not llm.validar_configuracion():
        print("\n[ERROR] Configuracion invalida")
        print("Revise las variables de entorno en el archivo .env")
        return False

    print("\n[OK] Configuracion basica valida")
    return True

def test_conexion_simple():
    """Prueba una conexión simple al LLM."""
    print("\nPRUEBA DE CONEXION")
    print("=" * 50)

    llm = LLMIntegration()

    # Prompt de prueba simple
    prompt_prueba = """
Responde unicamente con la palabra "OK" si puedes leer este mensaje correctamente.
"""

    try:
        print("Enviando prueba de conexion...")
        resultado = llm.consultar_con_fallback(prompt_prueba)

        if resultado['respuesta'] and 'OK' in resultado['respuesta']:
            print(f"[OK] Conexion exitosa")
            print(f"   Provider usado: {resultado['provider_usado']}")
            print(f"   Modelo usado: {resultado['model_usado']}")
            print(f"   Fallback activado: {resultado['fallback_activado']}")
            print(f"   Intentos: {resultado['intentos']}")
            return True
        else:
            print(f"[ERROR] Respuesta inesperada: {resultado['respuesta']}")
            return False

    except Exception as e:
        print(f"[ERROR] Error de conexion: {e}")
        return False

def test_extraccion_estructurada():
    """Prueba la extracción de datos estructurados."""
    print("\nPRUEBA DE EXTRACCION ESTRUCTURADA")
    print("=" * 50)

    llm = LLMIntegration()

    # Prompt de prueba para extracción estructurada
    prompt_prueba = """
Analiza el siguiente texto y extrae informacion estructurada en formato JSON:

"Departamento en venta en Equipetrol, 3 habitaciones, 2 banos, 150m2, precio $120,000 USD"

Responde unicamente con este JSON:
{
    "tipo_propiedad": "departamento",
    "ubicacion": "equipetrol",
    "habitaciones": 3,
    "banos": 2,
    "superficie": 150,
    "precio": 120000,
    "moneda": "USD"
}
"""

    try:
        print("Enviando prueba de extraccion estructurada...")
        resultado = llm.extract_structured_data(prompt_prueba)

        print(f"[OK] Extraccion exitosa")
        print(f"   Provider usado: {llm._get_provider_chain()[0][0]}")
        print(f"   Respuesta: {resultado[:200]}...")
        return True

    except Exception as e:
        print(f"[ERROR] Error en extraccion estructurada: {e}")
        return False

def main():
    """Funcion principal."""
    print("TEST DE CONFIGURACION LLM")
    print("=" * 60)

    # Paso 1: Probar configuracion
    if not test_configuracion():
        return 1

    # Paso 2: Probar conexion simple
    if not test_conexion_simple():
        return 1

    # Paso 3: Probar extraccion estructurada
    if not test_extraccion_estructurada():
        return 1

    print("\n" + "=" * 60)
    print("[OK] TODAS LAS PRUEBAS SUPERADAS")
    print("El sistema LLM esta funcionando correctamente")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    exit(main())