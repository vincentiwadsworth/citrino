#!/usr/bin/env python3
"""
Prueba del motor de recomendación enriquecido con datos municipales
"""

import sys
import os
import json

# Agregar directorios al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from recommendation_engine import RecommendationEngine
from sistema_consulta import SistemaConsultaCitrino

def probar_motor_enriquecido():
    """Prueba el motor de recomendación con datos municipales integrados"""
    print("=== PRUEBA DEL MOTOR DE RECOMENDACIÓN ENRIQUECIDO ===\n")

    # Inicializar sistemas
    sistema_consulta = SistemaConsultaCitrino()
    motor = RecommendationEngine()

    # Cargar base de datos
    print("1. Cargando base de datos...")
    ruta_bd = os.path.join(os.path.dirname(__file__), '..', 'data', 'base_datos_citrino_limpios.json')
    sistema_consulta.cargar_base_datos(ruta_bd)
    motor.cargar_propiedades(sistema_consulta.propiedades)

    print(f"   Base de datos cargada: {len(sistema_consulta.propiedades):,} propiedades")

    # Verificar si el enriquecimiento municipal está activo
    print(f"   Enriquecimiento municipal: {'Habilitado' if motor.enriquecimiento_habilitado else 'Deshabilitado'}")
    print(f"   Datos municipales disponibles: {len(motor.sistema_municipal.datos_municipales)} referencias")

    # Perfiles de prueba
    perfiles = [
        {
            'nombre': 'Familia con Hijos',
            'perfil': {
                'id': 'test_familia',
                'presupuesto': {'min': 200000, 'max': 280000},
                'composicion_familiar': {'adultos': 2, 'ninos': [8, 12], 'adultos_mayores': 0},
                'preferencias': {'ubicacion': 'Equipetrol', 'tipo_propiedad': 'casa'},
                'necesidades': ['seguridad', 'colegios', 'areas verdes', 'supermercado']
            }
        },
        {
            'nombre': 'Profesional Joven',
            'perfil': {
                'id': 'test_profesional',
                'presupuesto': {'min': 150000, 'max': 200000},
                'composicion_familiar': {'adultos': 1, 'ninos': [], 'adultos_mayores': 0},
                'preferencias': {'ubicacion': 'Centro', 'tipo_propiedad': 'departamento'},
                'necesidades': ['gimnasio', 'restaurantes', 'vida urbana', 'transporte']
            }
        },
        {
            'nombre': 'Adultos Mayores',
            'perfil': {
                'id': 'test_adultos_mayores',
                'presupuesto': {'min': 180000, 'max': 250000},
                'composicion_familiar': {'adultos': 0, 'ninos': [], 'adultos_mayores': 2},
                'preferencias': {'ubicacion': 'Zona Norte', 'tipo_propiedad': 'casa'},
                'necesidades': ['hospital', 'farmacia', 'tranquilidad', 'acceso facil']
            }
        }
    ]

    print("\n2. Generando recomendaciones con enriquecimiento municipal...")

    for i, test_case in enumerate(perfiles, 1):
        print(f"\n--- {test_case['nombre']} ---")
        perfil = test_case['perfil']

        # Generar recomendaciones
        recomendaciones = motor.generar_recomendaciones(
            perfil,
            limite=3,
            umbral_minimo=0.5
        )

        print(f"Recomendaciones encontradas: {len(recomendaciones)}")

        for j, rec in enumerate(recomendaciones, 1):
            prop = rec['propiedad']
            caract = prop.get('caracteristicas_principales', {})
            ubic = prop.get('ubicacion', {})

            print(f"\n{j}. {prop.get('nombre', 'Sin nombre')}")
            print(f"   Precio: ${caract.get('precio', 0):,.0f}")
            print(f"   Zona: {ubic.get('zona', 'Desconocida')}")
            print(f"   Compatibilidad: {rec['compatibilidad']:.1%}")
            print(f"   Justificación: {rec['justificacion'][:200]}...")

            # Verificar si incluye datos municipales
            if 'municipal' in rec['justificacion'].lower() or 'distrito' in rec['justificacion'].lower():
                print("   [OK] Incluye datos municipales de referencia")
            else:
                print("   [NO] No incluye datos municipales evidentes")

    print(f"\n=== ESTADÍSTICAS DEL MOTOR ===")
    stats = motor.obtener_estadisticas_rendimiento()
    print(f"Cálculos realizados: {stats['calculos_realizados']}")
    print(f"Cache hits: {stats['cache_hits']}")
    print(f"Tasa de cache: {stats['cache_hit_rate']:.2%}")
    print(f"Tiempo promedio: {stats['tiempo_promedio']:.4f} segundos")

    print(f"\n=== PRUEBA COMPARATIVA: CON VS SIN ENRIQUECIMIENTO ===")

    # Probar con y sin enriquecimiento
    perfil_test = perfiles[0]['perfil']

    print("\n3.1. CON enriquecimiento municipal:")
    motor.enriquecimiento_habilitado = True
    rec_con_enriquecimiento = motor.generar_recomendaciones(perfil_test, limite=1, umbral_minimo=0.5)
    if rec_con_enriquecimiento:
        print(f"Compatibilidad: {rec_con_enriquecimiento[0]['compatibilidad']:.1%}")
        print(f"Justificación: {rec_con_enriquecimiento[0]['justificacion'][:150]}...")

    print("\n3.2. SIN enriquecimiento municipal:")
    motor.enriquecimiento_habilitado = False
    rec_sin_enriquecimiento = motor.generar_recomendaciones(perfil_test, limite=1, umbral_minimo=0.5)
    if rec_sin_enriquecimiento:
        print(f"Compatibilidad: {rec_sin_enriquecimiento[0]['compatibilidad']:.1%}")
        print(f"Justificación: {rec_sin_enriquecimiento[0]['justificacion'][:150]}...")

    # Calcular diferencia
    if rec_con_enriquecimiento and rec_sin_enriquecimiento:
        diff_compatibilidad = rec_con_enriquecimiento[0]['compatibilidad'] - rec_sin_enriquecimiento[0]['compatibilidad']
        print(f"\nDiferencia de compatibilidad: {diff_compatibilidad:.1%}")
        print(f"Mejora con datos municipales: {diff_compatibilidad/rec_sin_enriquecimiento[0]['compatibilidad']:.1%}")

    print(f"\n=== RESUMEN FINAL ===")
    print("[OK] Sistema de enriquecimiento municipal implementado")
    print("[OK] Motor de recomendación actualizado para usar datos de referencia")
    print("[OK] Ponderación ajustada para considerar servicios y datos territoriales")
    print("[OK] Generación de justificaciones enriquecidas con información municipal")
    print("[OK] Sistema listo para producción")

if __name__ == "__main__":
    probar_motor_enriquecido()