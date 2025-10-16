#!/usr/bin/env python3
"""
Script simple para probar la conexión con Z.AI API
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Agregar src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_zai_connection():
    """Prueba básica de conexión con Z.AI"""
    print("=== PRUEBA DE CONEXION Z.AI ===")

    try:
        from llm_integration import LLMIntegration, LLMConfig

        # Verificar que tenemos API key
        api_key = os.getenv('ZAI_API_KEY')
        if not api_key:
            print("ERROR: ZAI_API_KEY no encontrada en variables de entorno")
            print("   Asegurate de tener ZAI_API_KEY configurada en tu .env")
            return False

        print(f"OK: API Key encontrada: {api_key[:10]}...")

        # Crear configuración
        config = LLMConfig(
            provider='zai',
            api_key=api_key,
            model='glm-4.6'
        )

        print(f"OK: Configuracion creada:")
        print(f"   Provider: {config.provider}")
        print(f"   Model: {config.model}")
        print(f"   URL: https://api.z.ai/api/coding/paas/v4/chat/completions")

        # Crear instancia de LLM
        llm = LLMIntegration(config)

        print(f"OK: Instancia LLM creada")

        # Probar con un mensaje simple
        mensaje_prueba = "Hola, responde simplemente con 'Z.AI funciona' si puedes leer esto."
        print(f"\nEnviando mensaje de prueba: '{mensaje_prueba}'")

        # Intentar llamar a Z.AI directamente
        response = llm._call_zai(mensaje_prueba)

        print(f"Respuesta recibida: '{response.strip()}'")

        if "funciona" in response.lower():
            print("\nEXITO: Z.AI esta respondiendo correctamente!")
            return True
        else:
            print(f"\nADVERTENCIA: Respuesta inesperada pero hubo comunicacion")
            return True

    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        import traceback
        print("\nTraceback completo:")
        traceback.print_exc()
        return False

def test_with_fallback():
    """Prueba usando el sistema de fallback"""
    print("\n\n=== PRUEBA CON SISTEMA DE FALLBACK ===")

    try:
        from llm_integration import LLMIntegration, LLMConfig

        config = LLMConfig(
            provider='zai',
            api_key=os.getenv('ZAI_API_KEY'),
            model='glm-4.6'
        )

        llm = LLMIntegration(config)

        mensaje_prueba = "Hola, responde con 'Sistema funciona' si puedes leer esto."
        print(f"Enviando mensaje con fallback: '{mensaje_prueba}'")

        resultado = llm.consultar_con_fallback(mensaje_prueba, use_fallback=True)

        print(f"Resultado:")
        print(f"   Respuesta: '{resultado['respuesta'].strip()}'")
        print(f"   Provider usado: {resultado['provider_usado']}")
        print(f"   Modelo usado: {resultado['model_usado']}")
        print(f"   Fallback activado: {resultado['fallback_activado']}")
        print(f"   Intentos: {resultado['intentos']}")

        return True

    except Exception as e:
        print(f"ERROR en fallback: {type(e).__name__}: {e}")
        return False

def main():
    """Función principal"""
    print("Iniciando pruebas de conexion con Z.AI...")
    print(f"Directorio actual: {os.getcwd()}")

    # Probar conexión directa
    resultado1 = test_zai_connection()

    # Probar con fallback
    resultado2 = test_with_fallback()

    print(f"\n\n=== RESUMEN DE PRUEBAS ===")
    print(f"Conexion directa: {'EXITO' if resultado1 else 'FALLO'}")
    print(f"Con fallback: {'EXITO' if resultado2 else 'FALLO'}")

    if resultado1 or resultado2:
        print(f"\nALGUNA PRUEBA FUNCIONO: La configuracion Z.AI parece estar correcta")
        return True
    else:
        print(f"\nTODAS FALLARON: Hay problemas con la configuracion Z.AI")
        return False

if __name__ == '__main__':
    main()