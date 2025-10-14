#!/usr/bin/env python3
"""
Script simple para probar el sistema Citrino
"""

import requests
import json
import time

def test_api_health():
    """Prueba que la API este funcionando"""
    print("=== PRUEBA API HEALTH ===")
    try:
        response = requests.get('http://localhost:5001/api/health', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"OK: API Health funcional")
            print(f"   Status: {data['status']}")
            print(f"   Propiedades: {data['total_propiedades']}")
            return True
        else:
            print(f"ERROR: API Health fallo: {response.status_code}")
            return False
    except Exception as e:
        print(f"ERROR: Conectando a API: {e}")
        return False

def test_busqueda():
    """Prueba busqueda simple"""
    print("\n=== PRUEBA BUSQUEDA ===")
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
            print(f"OK: Busqueda exitosa")
            print(f"   Resultados: {data['total_resultados']}")
            if data['total_resultados'] > 0:
                prop = data['propiedades'][0]
                print(f"   Ejemplo: {prop['nombre']} - ${prop['precio']:,}")
            return True
        else:
            print(f"ERROR: Busqueda fallo: {response.status_code}")
            return False
    except Exception as e:
        print(f"ERROR: Busqueda: {e}")
        return False

def test_chat():
    """Prueba chat con LLM"""
    print("\n=== PRUEBA CHAT CON LLM ===")
    try:
        payload = {
            "mensaje": "Busco un departamento en Equipetrol con presupuesto de 200000 dolares para una familia de 4 personas"
        }

        response = requests.post('http://localhost:5001/api/chat/process', json=payload, timeout=30)

        if response.status_code == 200:
            data = response.json()
            print(f"OK: Chat procesado")
            print(f"   LLM usado: {data.get('llm_usado', False)}")
            print(f"   Provider: {data.get('provider_usado', 'N/A')}")
            print(f"   Recomendaciones: {len(data.get('recomendaciones', []))}")

            recomendaciones = data.get('recomendaciones', [])
            if recomendaciones:
                print(f"   Ejemplo: {recomendaciones[0]['nombre']} - ${recomendaciones[0]['precio']:,}")

            return True
        else:
            print(f"ERROR: Chat fallo: {response.status_code}")
            return False
    except Exception as e:
        print(f"ERROR: Chat: {e}")
        return False

def main():
    """Funcion principal"""
    print("INICIANDO PRUEBAS SISTEMA CITRINO")
    print("=" * 50)

    # Esperar servidores
    time.sleep(2)

    # Ejecutar pruebas
    resultados = []
    resultados.append(("API Health", test_api_health()))
    resultados.append(("Busqueda", test_busqueda()))
    resultados.append(("Chat LLM", test_chat()))

    # Resumen
    print("\n" + "=" * 50)
    print("RESUMEN PRUEBAS")
    print("=" * 50)

    exitos = 0
    for nombre, resultado in resultados:
        estado = "EXITO" if resultado else "FALLO"
        print(f"{nombre:15} : {estado}")
        if resultado:
            exitos += 1

    print(f"\nResultado: {exitos}/{len(resultados)} pruebas exitosas")

    if exitos == len(resultados):
        print("TODAS LAS PRUEBAS EXITOSAS!")
        print("Sistema Citrino funcionando perfectamente.")
    else:
        print(f"Pruebas con fallos: {len(resultados) - exitos}")

    return exitos == len(resultados)

if __name__ == '__main__':
    main()