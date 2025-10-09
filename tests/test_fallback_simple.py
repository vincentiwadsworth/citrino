"""
Test simple del sistema de fallback a OpenRouter
"""
import sys
import os

# Agregar src al path
sys.path.insert(0, 'src')

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

from llm_integration import LLMIntegration

def test_fallback():
    """Test simple de fallback."""
    print("="*80)
    print("TEST DE FALLBACK A OPENROUTER")
    print("="*80)
    
    # Inicializar LLM
    llm = LLMIntegration()
    config = llm.obtener_info_configuracion()
    
    print("\n[CONFIGURACIÓN]")
    print(f"  Provider primario: {config['provider']}")
    print(f"  Modelo primario: {config['model']}")
    print(f"  Fallback habilitado: {os.getenv('OPENROUTER_FALLBACK_ENABLED', 'false')}")
    print(f"  Modelo fallback: {os.getenv('OPENROUTER_MODEL', 'N/A')}")
    
    # Prompt de prueba
    prompt = """Extrae la información de esta descripción de propiedad:

"Casa en venta, 3 dormitorios, 2 baños, 150m2, zona Equipetrol, $85,000 USD"

Responde en formato JSON con estos campos:
- precio (número)
- moneda (USD o BOB)
- habitaciones (número)
- banos (número)
- superficie (número en m2)
- zona (string)

JSON:"""
    
    print("\n[PROMPT]")
    print(f"  {prompt[:100]}...")
    
    print("\n[EJECUTANDO CONSULTA CON FALLBACK...]")
    try:
        resultado = llm.consultar_con_fallback(prompt, use_fallback=True)
        
        print("\n[RESULTADO]")
        print(f"  >> Provider usado: {resultado['provider_usado']}")
        print(f"  >> Modelo usado: {resultado['model_usado']}")
        print(f"  >> Fallback activado: {resultado['fallback_activado']}")
        print(f"  >> Intentos: {resultado['intentos']}")
        
        print("\n[RESPUESTA LLM]")
        print(resultado['respuesta'][:500])
        
        print("\n" + "="*80)
        print(">> TEST EXITOSO")
        print("="*80)
        
    except Exception as e:
        print(f"\n[ERROR]: {e}")
        print("\n" + "="*80)
        print(">> TEST FALLIDO")
        print("="*80)
        return False
    
    return True

if __name__ == "__main__":
    success = test_fallback()
    sys.exit(0 if success else 1)
