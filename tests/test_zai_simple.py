"""Test simple de integración con z.ai GLM-4.6"""
import os
import sys

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv()

# Verificar que las variables estén configuradas
if not os.getenv('ZAI_API_KEY'):
    print("ERROR: ZAI_API_KEY no está configurada en .env")
    sys.exit(1)

sys.path.insert(0, 'src')

from llm_integration import LLMIntegration

print("Inicializando LLM con GLM-4.6...")
llm = LLMIntegration()

print(f"Configuración: {llm.obtener_info_configuracion()}")

# Test simple
prompt = """Extrae precio, habitaciones y baños de esta descripción:

"Hermoso departamento de 3 dormitorios, 2 baños completos. Precio: $85,000 USD"

Responde SOLO con JSON:
{"precio": <número>, "moneda": "USD", "habitaciones": <número>, "banos": <número>}"""

print("\nEnviando consulta de prueba...")
try:
    response = llm.consultar(prompt)
    print(f"\n[OK] Respuesta recibida:\n{response}")
    print("\n[OK] Test exitoso - z.ai GLM-4.6 funcionando correctamente")
except Exception as e:
    print(f"\n[ERROR] Error: {e}")
    sys.exit(1)
