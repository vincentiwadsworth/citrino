#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple para verificar el sistema de fallback LLM.
"""

import os
from dotenv import load_dotenv
from src.llm_integration import LLMIntegration

# Cargar variables de entorno
load_dotenv()

def test_fallback():
    """Test del sistema de fallback."""
    print("TEST DE FALLBACK LLM")
    print("=" * 40)

    # Inicializar LLM con configuración del .env
    llm = LLMIntegration()

    print(f"Configuración inicial:")
    print(f"  Provider: {llm.config.provider}")
    print(f"  Model: {llm.config.model}")
    print(f"  API Key configurada: {bool(llm.config.api_key)}")
    print()

    # Verificar cadena de fallback
    chain = llm._get_provider_chain()
    print(f"Cadena de providers:")
    for i, (provider, model) in enumerate(chain):
        print(f"  {i+1}. {provider} - {model}")
    print()

    # Verificar variables de entorno
    print("Variables de entorno:")
    print(f"  OPENROUTER_FALLBACK_ENABLED: {os.getenv('OPENROUTER_FALLBACK_ENABLED')}")
    print(f"  OPENROUTER_API_KEY configurada: {bool(os.getenv('OPENROUTER_API_KEY'))}")
    print(f"  OPENROUTER_MODEL: {os.getenv('OPENROUTER_MODEL')}")
    print()

    # Test simple
    prompt = "Responde con solo: {'test': 'ok'}"

    try:
        print("Intentando consulta con fallback...")
        resultado = llm.consultar_con_fallback(prompt, use_fallback=True)

        print("✅ ÉXITO:")
        print(f"  Provider usado: {resultado['provider_usado']}")
        print(f"  Model usado: {resultado['model_usado']}")
        print(f"  Fallback activado: {resultado['fallback_activado']}")
        print(f"  Intentos: {resultado['intentos']}")
        print(f"  Respuesta: {resultado['respuesta'][:100]}...")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("Todos los providers fallaron")

if __name__ == "__main__":
    test_fallback()