#!/usr/bin/env python3
"""
Script para probar el API de Citrino
"""

import requests
import json

# Configuración
BASE_URL = "http://localhost:5000"

def test_health():
    """Probar endpoint de salud"""
    print("1. Probando health check...")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_search():
    """Probar búsqueda de propiedades"""
    print("2. Probando búsqueda de propiedades...")
    data = {
        "zona": "Equipetrol",
        "precio_min": 150000,
        "precio_max": 300000,
        "habitaciones_min": 2,
        "banos_min": 2,
        "tiene_garaje": True,
        "limite": 5
    }

    response = requests.post(f"{BASE_URL}/api/buscar", json=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Total resultados: {result.get('total_resultados', 0)}")
    print("Propiedades encontradas:")
    for prop in result.get('propiedades', [])[:3]:
        print(f"  - {prop['nombre']}: ${prop['precio']:,} ({prop['zona']})")
    print()

def test_recommend():
    """Probar recomendaciones"""
    print("3. Probando recomendaciones...")
    data = {
        "presupuesto_min": 200000,
        "presupuesto_max": 350000,
        "adultos": 2,
        "ninos": [8, 12],
        "zona_preferida": "Las Palmas",
        "tipo_propiedad": "casa",
        "necesidades": ["seguridad", "areas_comunes", "estacionamiento"],
        "limite": 3
    }

    response = requests.post(f"{BASE_URL}/api/recomendar", json=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Total recomendaciones: {result.get('total_recomendaciones', 0)}")
    print("Recomendaciones:")
    for rec in result.get('recomendaciones', []):
        print(f"  - {rec['nombre']}: ${rec['precio']:,} ({rec['compatibilidad']}% compatibilidad)")
    print()

def test_statistics():
    """Probar estadísticas"""
    print("4. Probando estadísticas...")
    response = requests.get(f"{BASE_URL}/api/estadisticas")
    print(f"Status: {response.status_code}")
    result = response.json()
    stats = result.get('estadisticas', {})
    print(f"Total propiedades: {stats.get('total_propiedades', 0):,}")
    print(f"Precio promedio: ${stats.get('precio_promedio', 0):,.0f}")
    print(f"Superficie promedio: {stats.get('superficie_promedio', 0):.1f} m²")
    print()

def test_zones():
    """Probar obtener zonas"""
    print("5. Probando obtener zonas...")
    response = requests.get(f"{BASE_URL}/api/zonas")
    print(f"Status: {response.status_code}")
    result = response.json()
    zonas = result.get('zonas', [])
    print(f"Total zonas: {len(zonas)}")
    print("Primeras 10 zonas:")
    for zona in zonas[:10]:
        print(f"  - {zona}")
    print()

if __name__ == "__main__":
    print("=== Probando API Citrino ===")
    print(f"Base URL: {BASE_URL}")
    print()

    try:
        test_health()
        test_search()
        test_recommend()
        test_statistics()
        test_zones()

        print("=== Todas las pruebas completadas ===")
    except requests.exceptions.ConnectionError:
        print("Error: No se pudo conectar al servidor")
        print("Asegúrate de que el servidor esté corriendo en http://localhost:5000")
        print("Ejecuta: python api/server.py")
    except Exception as e:
        print(f"Error inesperado: {e}")