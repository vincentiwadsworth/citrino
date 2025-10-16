#!/usr/bin/env python3
"""
Script para probar el sistema completo de chat Citrino
con LLM funcionando y motor de búsqueda reparado
"""

import requests
import json
import time
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_api_health():
    """Prueba que la API esté funcionando"""
    print("=== PRUEBA DE SALUD API ===")
    try:
        response = requests.get('http://localhost:5001/api/health', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"OK: API Health funcional")
            print(f"   Status: {data['status']}")
            print(f"   Propiedades cargadas: {data['total_propiedades']}")
            print(f"   Datos cargados: {data['datos_cargados']}")
            return True
        else:
            print(f"ERROR: API Health fallo: {response.status_code}")
            return False
    except Exception as e:
        print(f"ERROR: Conectando a API: {e}")
        return False

def test_busqueda_simple():
    """Prueba búsqueda simple de propiedades"""
    print("\n=== PRUEBA DE BÚSQUEDA SIMPLE ===")
    try:
        payload = {
            "zona": "Equipetrol",
            "precio_min": 50000,
            "precio_max": 200000,
            "tipo_propiedad": "departamento"
        }

        response = requests.post('http://localhost:5001/api/buscar', json=payload, timeout=15)
        if response.status_code == 200:
            data = response.json()
            print(f"OK: Búsqueda exitosa")
            print(f"   Total resultados: {data['total_resultados']}")
            if data['total_resultados'] > 0:
                prop = data['propiedades'][0]
                print(f"   Ejemplo: {prop['nombre']} - ${prop['precio']:,} - {prop['zona']}")
            return True
        else:
            print(f"ERROR: Búsqueda fallo: {response.status_code}")
            return False
    except Exception as e:
        print(f"ERROR: Búsqueda: {e}")
        return False

def test_recomendaciones():
    """Prueba sistema de recomendaciones"""
    print("\n=== PRUEBA DE RECOMENDACIONES ===")
    try:
        payload = {
            "id": "test_profile",
            "presupuesto_min": 100000,
            "presupuesto_max": 300000,
            "zona_preferida": "Equipetrol",
            "tipo_propiedad": "departamento",
            "adultos": 2,
            "limite": 5
        }

        response = requests.post('http://localhost:5001/api/recomendar-mejorado', json=payload, timeout=15)
        if response.status_code == 200:
            data = response.json()
            print(f"OK: Recomendaciones exitosas")
            print(f"   Total recomendaciones: {data['total_recomendaciones']}")
            if data['total_recomendaciones'] > 0:
                rec = data['recomendaciones'][0]
                print(f"   Ejemplo: {rec['nombre']} - Compatibilidad: {rec['compatibilidad']}%")
            return True
        else:
            print(f"ERROR: Recomendaciones fallo: {response.status_code}")
            return False
    except Exception as e:
        print(f"ERROR: Recomendaciones: {e}")
        return False

def test_chat_con_llm():
    """Prueba el chat completo con LLM"""
    print("\n=== PRUEBA DE CHAT COMPLETO CON LLM ===")
    try:
        mensaje = "Busco un departamento en Equipetrol con presupuesto de 200000 dolares para una familia de 4 personas"

        payload = {
            "mensaje": mensaje
        }

        print(f"Enviando mensaje: '{mensaje}'")
        response = requests.post('http://localhost:5001/api/chat/process', json=payload, timeout=30)

        if response.status_code == 200:
            data = response.json()
            print(f"OK: Chat procesado exitosamente")
            print(f"   LLM usado: {data.get('llm_usado', False)}")
            print(f"   Provider usado: {data.get('provider_usado', 'N/A')}")
            print(f"   Fallback activado: {data.get('fallback_activado', False)}")
            print(f"   Recomendaciones generadas: {len(data.get('recomendaciones', []))}")

            # Mostrar perfil extraído
            perfil = data.get('perfil', {})
            if perfil:
                print(f"   Perfil extraído:")
                print(f"     Presupuesto: {perfil.get('presupuesto', {})}")
                print(f"     Preferencias: {perfil.get('preferencias', {})}")

            # Mostrar respuesta
            respuesta = data.get('respuesta', '')
            if respuesta:
                print(f"   Respuesta: {respuesta[:100]}...")

            # Mostrar recomendaciones si hay
            recomendaciones = data.get('recomendaciones', [])
            if recomendaciones:
                print(f"   Recomendaciones encontradas: {len(recomendaciones)}")
                for i, rec in enumerate(recomendaciones[:3], 1):
                    print(f"     {i}. {rec['nombre']} - ${rec['precio']:,} - {rec['zona']}")

            return True
        else:
            print(f"ERROR: Chat fallo: {response.status_code}")
            return False
    except Exception as e:
        print(f"ERROR: Chat: {e}")
        return False

def test_recomendaciones_con_llm():
    """Prueba recomendaciones con enriquecimiento LLM"""
    print("\n=== PRUEBA DE RECOMENDACIONES CON LLM ===")
    try:
        payload = {
            "id": "test_llm_enriched",
            "presupuesto_min": 150000,
            "presupuesto_max": 250000,
            "zona_preferida": "Equipetrol",
            "tipo_propiedad": "departamento",
            "informacion_llm": "Cliente es inversionista experimentado que busca propiedades con potencial de plusvalía a 3 años. Tiene experiencia en alquileres y quiere comprar su primera propiedad para inversión.",
            "limite": 3
        }

        response = requests.post('http://localhost:5001/api/recomendar-mejorado-llm', json=payload, timeout=45)

        if response.status_code == 200:
            data = response.json()
            print(f"OK: Recomendaciones con LLM exitosas")
            print(f"   Total recomendaciones: {data['total']}")
            print(f"   LLM disponible: {data.get('llmAvailable', False)}")
            print(f"   Análisis personalizado: {data.get('personalizedAnalysis', False)}")

            # Mostrar briefing si existe
            briefing = data.get('briefing')
            if briefing:
                print(f"   Briefing generado: {len(briefing)} caracteres")
                print(f"   Primeras líneas: {briefing[:200]}...")

            return True
        else:
            print(f"ERROR: Recomendaciones LLM fallo: {response.status_code}")
            return False
    except Exception as e:
        print(f"ERROR: Recomendaciones LLM: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("INICIANDO PRUEBAS COMPLETAS DEL SISTEMA CITRINO")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Esperar un momento a que los servidores inicien
    print("Esperando que los servidores esten listos...")
    time.sleep(2)

    # Ejecutar pruebas
    resultados = []

    resultados.append(("API Health", test_api_health()))
    resultados.append(("Busqueda Simple", test_busqueda_simple()))
    resultados.append(("Recomendaciones", test_recomendaciones()))
    resultados.append(("Chat con LLM", test_chat_con_llm()))
    resultados.append(("Recomendaciones con LLM", test_recomendaciones_con_llm()))

    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE PRUEBAS")
    print("=" * 60)

    exitos = 0
    for nombre, resultado in resultados:
        estado = "EXITO" if resultado else "FALLO"
        print(f"{nombre:25} : {estado}")
        if resultado:
            exitos += 1

    print(f"\nResultado final: {exitos}/{len(resultados)} pruebas exitosas")

    if exitos == len(resultados):
        print("TODAS LAS PRUEBAS EXITOSAS! Sistema Citrino funcionando perfectamente.")
        print("\nAccesos disponibles:")
        print("   * Frontend: http://localhost:8080")
        print("   * Chat: http://localhost:8080/chat.html")
        print("   * API Health: http://localhost:5001/api/health")
    elif exitos >= 3:
        print("Mayoria de pruebas exitosas. Sistema parcialmente funcional.")
    else:
        print("Multiples fallos. Sistema necesita mas reparaciones.")

    return exitos == len(resultados)

if __name__ == '__main__':
    main()