#!/usr/bin/env python3
"""
Script de prueba para verificar la integración con Z.AI
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Añadir src al path
sys.path.append('src')

from llm_integration import LLMIntegration, LLMConfig

def test_zai_connection():
    """Prueba la conexión con Z.AI"""
    print("=" * 60)
    print("PRUEBA DE INTEGRACIÓN Z.AI")
    print("=" * 60)
    
    # Verificar que la API key esté configurada
    api_key = os.getenv('ZAI_API_KEY')
    if not api_key:
        print("❌ Error: ZAI_API_KEY no está configurada en .env")
        return False
    
    print(f"✅ API Key configurada: {api_key[:20]}...")
    print()
    
    # Crear configuración de LLM
    config = LLMConfig(
        provider='zai',
        api_key=api_key,
        model=os.getenv('LLM_MODEL', 'glm-4.5-air')
    )
    
    llm = LLMIntegration(config)
    
    # Validar configuración
    print("Validando configuración...")
    if not llm.validar_configuracion():
        print("❌ Error: Configuración inválida")
        return False
    
    print("✅ Configuración válida")
    print()
    
    # Probar con mensaje de ejemplo
    mensaje_prueba = "Busco un departamento en Equipetrol de 3 habitaciones, presupuesto hasta 200000 dólares"
    
    print(f"📝 Mensaje de prueba:")
    print(f"   '{mensaje_prueba}'")
    print()
    print("🔄 Procesando con Z.AI (puede tardar 10-30 segundos)...")
    
    try:
        perfil = llm.parsear_perfil_desde_texto(mensaje_prueba)
        
        print()
        print("✅ RESPUESTA DE Z.AI:")
        print("-" * 60)
        print(f"Composición familiar: {perfil.get('composicion_familiar', {})}")
        print(f"Presupuesto: {perfil.get('presupuesto', {})}")
        print(f"Necesidades: {perfil.get('necesidades', [])}")
        print(f"Preferencias: {perfil.get('preferencias', {})}")
        print("-" * 60)
        print()
        print("✅ ¡Integración con Z.AI funcionando correctamente!")
        return True
        
    except Exception as e:
        print()
        print(f"❌ Error al procesar con Z.AI: {e}")
        print()
        print("Posibles causas:")
        print("  1. API Key inválida o expirada")
        print("  2. Sin créditos en la cuenta de Z.AI")
        print("  3. Problemas de conectividad")
        print("  4. Límite de rate excedido")
        return False

if __name__ == '__main__':
    try:
        success = test_zai_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Prueba interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)
