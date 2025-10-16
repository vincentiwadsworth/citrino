#!/usr/bin/env python3
"""
Test simple para verificar que el API funciona para la presentación
"""

import requests
import json

def test_api_basico():
    """Prueba básica del API Citrino"""
    base_url = "http://localhost:5000"

    print("=== Test API Citrino ===")
    print(f"Base URL: {base_url}")
    print()

    try:
        # 1. Probar health check
        print("1. Probando health check...")
        response = requests.get(f"{base_url}/api/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Total propiedades: {data.get('total_propiedades', 'N/A')}")
        print()

        # 2. Probar búsqueda simple
        print("2. Probando búsqueda simple...")
        search_data = {
            "zona": "Equipetrol",
            "precio_min": 150000,
            "precio_max": 250000,
            "limite": 3
        }
        response = requests.post(f"{base_url}/api/buscar", json=search_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Resultados encontrados: {data.get('total_resultados', 0)}")
            for i, prop in enumerate(data.get('propiedades', [])[:2], 1):
                print(f"   {i}. {prop.get('nombre', 'N/A')} - ${prop.get('precio', 0):,}")
        print()

        # 3. Probar recomendación con briefing
        print("3. Probando recomendación con briefing...")
        rec_data = {
            "presupuesto_min": 200000,
            "presupuesto_max": 300000,
            "adultos": 2,
            "ninos": [8, 12],
            "zona_preferida": "Zona Norte",
            "tipo_propiedad": "casa",
            "necesidades": ["seguridad", "areas_comunes"],
            "limite": 2
        }
        response = requests.post(f"{base_url}/api/recomendar", json=rec_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Recomendaciones: {data.get('total_recomendaciones', 0)}")

            # Mostrar briefing personalizado
            if 'briefing_personalizado' in data:
                print("\n   === BRIEFING PERSONALIZADO ===")
                briefing = data['briefing_personalizado']
                # Mostrar primeras líneas del briefing
                lineas = briefing.split('\n')[:15]
                for linea in lineas:
                    if linea.strip():
                        print(f"   {linea}")
                print("   ...")
                print("   === FIN BRIEFING ===\n")

        print(" Todas las pruebas completadas con éxito!")
        return True

    except requests.exceptions.ConnectionError:
        print(" Error: No se pudo conectar al servidor")
        print("   Asegúrate de que el servidor esté corriendo en http://localhost:5000")
        print("   Ejecuta: python api/server.py")
        return False
    except Exception as e:
        print(f" Error inesperado: {e}")
        return False

if __name__ == "__main__":
    test_api_basico()