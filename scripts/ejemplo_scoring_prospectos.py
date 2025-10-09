#!/usr/bin/env python3
"""
Ejemplos prácticos de uso del sistema de scoring de prospectos
Demuestra diferentes tipos de prospectos y sus evaluaciones
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from scoring_prospectos import ScoringProspectos, crear_prospecto_desde_dict

def ejemplo_familia_completa():
    """Ejemplo de familia con hijos - típico prospecto caliente"""
    print("=== EJEMPLO 1: Familia con Hijos (Prospecto Caliente) ===")

    datos = {
        'adultos': 2,
        'ninos_edades': [6, 9, 14],
        'adolescentes_edades': [],
        'adultos_mayores': 0,
        'tiene_mascotas': True,

        'presupuesto_min': 220000,
        'presupuesto_max': 300000,
        'tiene_financiamiento': True,
        'cuota_inicial': 70000,

        'tipo_propiedad': 'casa',
        'habitaciones_min': 4,
        'banos_min': 3,
        'superficie_min': 180,
        'necesita_garaje': True,
        'zonas_preferencia': ['Zona Norte', 'Equipetrol'],

        'urgencia': 'corta',
        'nivel_conocimiento_mercado': 'medio',
        'motivacion': 'primera_vivienda',

        'servicios_cercanos_requeridos': ['escuelas', 'seguridad', 'supermercados'],
        'caracteristicas_esenciales': ['jardin', 'seguridad_24h', 'garaje_para_2_autos'],
        'asesor': 'María González'
    }

    prospecto = crear_prospecto_desde_dict(datos)
    scoring = ScoringProspectos()
    resultado = scoring.calcular_puntuacion_total(prospecto)

    mostrar_resultado(resultado)

def ejemplo_pareja_joven():
    """Ejemplo de pareja joven profesional - prospecto tibio"""
    print("\n=== EJEMPLO 2: Pareja Joven Profesional (Prospecto Tibio) ===")

    datos = {
        'adultos': 2,
        'ninos_edades': [],
        'adolescentes_edades': [],
        'adultos_mayores': 0,
        'tiene_mascotas': False,

        'presupuesto_min': 150000,
        'presupuesto_max': 200000,
        'tiene_financiamiento': False,
        'cuota_inicial': 40000,

        'tipo_propiedad': 'departamento',
        'habitaciones_min': 2,
        'banos_min': 1,
        'superficie_min': 80,
        'necesita_garaje': True,
        'zonas_preferencia': ['Centro', 'Equipetrol'],

        'urgencia': 'media',
        'nivel_conocimiento_mercado': 'bajo',
        'motivacion': 'primera_vivienda',

        'servicios_cercanos_requeridos': ['universidades', 'transporte'],
        'caracteristicas_esenciales': ['terraza', 'moderno', 'gimnasio'],
        'asesor': 'Carlos Rodríguez'
    }

    prospecto = crear_prospecto_desde_dict(datos)
    scoring = ScoringProspectos()
    resultado = scoring.calcular_puntuacion_total(prospecto)

    mostrar_resultado(resultado)

def ejemplo_adulto_mayor():
    """Ejemplo de adulto mayor - prospecto especializado"""
    print("\n=== EJEMPLO 3: Adulto Mayor (Prospecto con Necesidades Específicas) ===")

    datos = {
        'adultos': 1,
        'ninos_edades': [],
        'adolescentes_edades': [],
        'adultos_mayores': 1,
        'tiene_mascotas': False,

        'presupuesto_min': 120000,
        'presupuesto_max': 160000,
        'tiene_financiamiento': True,
        'cuota_inicial': 50000,

        'tipo_propiedad': 'departamento',
        'habitaciones_min': 1,
        'banos_min': 1,
        'superficie_min': 60,
        'necesita_garaje': False,
        'zonas_preferencia': ['Equipetrol'],

        'urgencia': 'corta',
        'nivel_conocimiento_mercado': 'alto',
        'motivacion': 'cambio',

        'servicios_cercanos_requeridos': ['hospitales', 'farmacias'],
        'caracteristicas_esenciales': ['ascensor', 'seguridad_24h', 'accesibilidad'],
        'asesor': 'Ana Silva'
    }

    prospecto = crear_prospecto_desde_dict(datos)
    scoring = ScoringProspectos()
    resultado = scoring.calcular_puntuacion_total(prospecto)

    mostrar_resultado(resultado)

def ejemplo_inversionista():
    """Ejemplo de inversionista - prospecto con criterios específicos"""
    print("\n=== EJEMPLO 4: Inversionista (Prospecto Analítico) ===")

    datos = {
        'adultos': 1,
        'ninos_edades': [],
        'adolescentes_edades': [],
        'adultos_mayores': 0,
        'tiene_mascotas': False,

        'presupuesto_min': 180000,
        'presupuesto_max': 350000,
        'tiene_financiamiento': True,
        'cuota_inicial': 150000,

        'tipo_propiedad': 'departamento',
        'habitaciones_min': 2,
        'banos_min': 1,
        'superficie_min': 70,
        'necesita_garaje': True,
        'zonas_preferencia': ['Centro', 'Zona Norte'],

        'urgencia': 'media',
        'nivel_conocimiento_mercado': 'alto',
        'motivacion': 'inversion',

        'servicios_cercanos_requeridos': ['universidades', 'centros_comerciales'],
        'caracteristicas_esenciales': ['potencial_alquiler', 'plusvalia', 'buen_estado'],
        'asesor': 'Luis Mendoza'
    }

    prospecto = crear_prospecto_desde_dict(datos)
    scoring = ScoringProspectos()
    resultado = scoring.calcular_puntuacion_total(prospecto)

    mostrar_resultado(resultado)

def ejemplo_presupuesto_bajo():
    """Ejemplo de presupuesto poco realista - prospecto frío"""
    print("\n=== EJEMPLO 5: Presupuesto Irrealista (Prospecto Frío) ===")

    datos = {
        'adultos': 2,
        'ninos_edades': [3, 7],
        'adolescentes_edades': [],
        'adultos_mayores': 0,
        'tiene_mascotas': True,

        'presupuesto_min': 80000,
        'presupuesto_max': 100000,
        'tiene_financiamiento': False,
        'cuota_inicial': 20000,

        'tipo_propiedad': 'casa',
        'habitaciones_min': 3,
        'banos_min': 2,
        'superficie_min': 150,
        'necesita_garaje': True,
        'zonas_preferencia': ['Equipetrol', 'Zona Norte'],

        'urgencia': 'larga',
        'nivel_conocimiento_mercado': 'bajo',
        'motivacion': 'primera_vivienda',

        'servicios_cercanos_requeridos': ['escuelas', 'seguridad'],
        'caracteristicas_esenciales': ['jardin', 'garaje'],
        'asesor': 'Pedro Santos'
    }

    prospecto = crear_prospecto_desde_dict(datos)
    scoring = ScoringProspectos()
    resultado = scoring.calcular_puntuacion_total(prospecto)

    mostrar_resultado(resultado)

def mostrar_resultado(resultado):
    """Muestra los resultados de evaluación de forma formateada"""
    print(f"Puntuación: {resultado['puntuacion_total']}/100")
    print(f"Clasificación: {resultado['clasificacion'].upper()}")
    print(f"Prioridad: {resultado['prioridad']}")
    print(f"Perfil Familiar: {resultado['perfil_familiar']}")
    print(f"Recomendación: {resultado['recomendacion']}")

    print(f"\nPotencial de Propiedades:")
    potencial = resultado['potencial_propiedades']
    print(f"  - Total estimado: {potencial['estimado_total']:,} propiedades")
    print(f"  - Cumplen criterios: {potencial['cumplen_criterios']} propiedades")
    print(f"  - Altamente recomendadas: {potencial['altamente_recomendadas']} propiedades")

    if resultado['fortalezas']:
        print(f"\nFortalezas:")
        for fortaleza in resultado['fortalezas']:
            print(f"  [OK] {fortaleza}")

    if resultado['debilidades']:
        print(f"\nÁreas de mejora:")
        for debilidad in resultado['debilidades']:
            print(f"  [!] {debilidad}")

    # Mostrar detalles de puntuación
    print(f"\nDesglose de Puntuación:")
    puntuaciones = resultado['puntuaciones_detalle']
    for factor, puntuacion in sorted(puntuaciones.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {factor.replace('_', ' ').title()}: {puntuacion} puntos")

def main():
    """Función principal que ejecuta todos los ejemplos"""
    print("Sistema de Scoring de Prospectos Citrino")
    print("=" * 50)
    print("Ejemplos de diferentes tipos de prospectos\n")

    # Ejecutar ejemplos
    ejemplo_familia_completa()
    ejemplo_pareja_joven()
    ejemplo_adulto_mayor()
    ejemplo_inversionista()
    ejemplo_presupuesto_bajo()

    print("\n" + "=" * 50)
    print("Análisis completado")
    print("Estos ejemplos muestran cómo el sistema de scoring ayuda a:")
    print("• Identificar prospectos con alto potencial de cierre")
    print("• Detectar necesidades específicas por tipo de cliente")
    print("• Priorizar esfuerzos de seguimiento")
    print("• Enfocar la búsqueda de propiedades")

if __name__ == "__main__":
    main()