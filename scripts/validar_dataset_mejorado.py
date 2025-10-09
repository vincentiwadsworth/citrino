#!/usr/bin/env python3
"""
Script de validación del dataset mejorado y motor de recomendación.
"""

import json
from src.recommendation_engine import RecommendationEngine

def main():
    print("=== Validación del Dataset Mejorado ===")

    # Cargar el nuevo dataset mejorado
    try:
        with open('data/propiedades_mejorado.json', 'r', encoding='utf-8') as f:
            propiedades_mejoradas = json.load(f)
        print(f"Dataset mejorado cargado: {len(propiedades_mejoradas)} propiedades")
    except Exception as e:
        print(f"Error cargando dataset mejorado: {e}")
        return

    # Crear motor y cargar propiedades
    engine = RecommendationEngine()
    engine.cargar_propiedades(propiedades_mejoradas)
    print("Propiedades cargadas en el motor")

    # Test con perfiles de ejemplo
    perfiles_test = [
        {
            "nombre": "Familia Martínez López",
            "composicion_familiar": {"adultos": 2, "ninos": [{"edad": 8}, {"edad": 12}], "adultos_mayores": 0},
            "presupuesto": {"min": 250000, "max": 350000, "tipo": "compra"},
            "necesidades": ["escuela_primaria", "supermercado"],
            "preferencias": {"seguridad": "alta", "ubicacion": "norte"}
        },
        {
            "nombre": "Pareja joven profesional",
            "composicion_familiar": {"adultos": 2, "ninos": [], "adultos_mayores": 0},
            "presupuesto": {"min": 180000, "max": 250000, "tipo": "compra"},
            "necesidades": ["universidad", "comercio"],
            "preferencias": {"ubicacion": "centro", "tipo_propiedad": "apartamento"}
        },
        {
            "nombre": "Adulto mayor jubilado",
            "composicion_familiar": {"adultos": 1, "ninos": [], "adultos_mayores": 1},
            "presupuesto": {"min": 120000, "max": 180000, "tipo": "compra"},
            "necesidades": ["hospital", "supermercado"],
            "preferencias": {"seguridad": "alta", "ubicacion": "zona tranquila"}
        }
    ]

    print("\n=== Resultados de Recomendación ===")
    for perfil in perfiles_test:
        print(f"\n{perfil['nombre']}:")
        recomendaciones = engine.generar_recomendaciones(perfil, limite=3)

        if recomendaciones:
            for i, rec in enumerate(recomendaciones, 1):
                prop = rec['propiedad']
                caract = prop.get('caracteristicas_principales', {})
                ubic = prop.get('ubicacion', {})

                print(f"  {i}. {prop.get('nombre', 'Sin nombre')}")
                print(f"     Precio: ${caract.get('precio', 0):,.0f}")
                print(f"     Superficie: {caract.get('superficie_m2', 0)}m²")
                print(f"     Habitaciones: {caract.get('habitaciones', 0)}")
                print(f"     Baños: {caract.get('banos_completos', 0)} + {caract.get('banos_medios', 0)}")
                print(f"     Ubicación: {ubic.get('barrio', 'N/A')}, {ubic.get('zona', 'N/A')}")
                print(f"     Compatibilidad: {rec['compatibilidad']}%")
                print(f"     Justificación: {rec['justificacion']}")
                print()
        else:
            print("  No se encontraron recomendaciones")

    # Mostrar estadísticas de rendimiento
    stats = engine.obtener_estadisticas_rendimiento()
    print(f"\n=== Estadísticas de Rendimiento ===")
    print(f"Cálculos realizados: {stats['calculos_realizados']}")
    print(f"Tiempo promedio: {stats['tiempo_promedio']*1000:.2f}ms")
    print(f"Cache hit rate: {stats['cache_hit_rate']:.2%}")
    print(f"Tamaño cache: {stats['cache_size']}")

    # Análisis del dataset
    print(f"\n=== Análisis del Dataset ===")
    zonas = {}
    rangos_precio = {"económico": 0, "medio": 0, "alto": 0, "premium": 0}
    rangos_superficie = {"pequeño": 0, "medio": 0, "grande": 0, "extra_grande": 0}

    for prop in propiedades_mejoradas:
        # Análisis por zonas
        zona = prop.get('ubicacion', {}).get('zona', 'otra')
        zonas[zona] = zonas.get(zona, 0) + 1

        # Análisis por precio
        precio = prop.get('caracteristicas_principales', {}).get('precio', 0)
        if precio < 150000:
            rangos_precio["económico"] += 1
        elif precio < 250000:
            rangos_precio["medio"] += 1
        elif precio < 350000:
            rangos_precio["alto"] += 1
        else:
            rangos_precio["premium"] += 1

        # Análisis por superficie
        superficie = prop.get('caracteristicas_principales', {}).get('superficie_m2', 0)
        if superficie < 80:
            rangos_superficie["pequeño"] += 1
        elif superficie < 120:
            rangos_superficie["medio"] += 1
        elif superficie < 200:
            rangos_superficie["grande"] += 1
        else:
            rangos_superficie["extra_grande"] += 1

    print("Distribución por zonas:")
    for zona, count in zonas.items():
        print(f"  {zona}: {count} propiedades ({count/len(propiedades_mejoradas)*100:.1f}%)")

    print("\nDistribución por precio:")
    for rango, count in rangos_precio.items():
        print(f"  {rango}: {count} propiedades ({count/len(propiedades_mejoradas)*100:.1f}%)")

    print("\nDistribución por superficie:")
    for rango, count in rangos_superficie.items():
        print(f"  {rango}: {count} propiedades ({count/len(propiedades_mejoradas)*100:.1f}%)")

    print(f"\n=== Validación Completada ===")

if __name__ == "__main__":
    main()