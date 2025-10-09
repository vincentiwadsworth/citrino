#!/usr/bin/env python3
"""
Script de validación de perfiles de prospectos
Valida consistencia y realismo de los perfiles para el sistema de recomendación
"""

import json
import os
from pathlib import Path

def cargar_datos():
    """Cargar propiedades y perfiles"""
    base_path = Path(__file__).parent.parent

    with open(base_path / 'data' / 'propiedades.json', 'r', encoding='utf-8') as f:
        propiedades = json.load(f)

    perfiles_path = base_path / 'data' / 'perfiles'
    perfiles = []

    for perfil_file in perfiles_path.glob('perfil_*.json'):
        with open(perfil_file, 'r', encoding='utf-8') as f:
            perfiles.append(json.load(f))

    return propiedades, perfiles

def validar_presupuesto(perfil, propiedades):
    """Valida que el presupuesto del perfil sea realista"""
    presupuesto_min = perfil['presupuesto']['min']
    presupuesto_max = perfil['presupuesto']['max']

    precios = [prop['caracteristicas']['precio'] for prop in propiedades]
    precio_min_global = min(precios)
    precio_max_global = max(precios)

    # Verificar que el rango sea realista
    if presupuesto_min < precio_min_global * 0.8:
        print(f"ADVERTENCIA {perfil['nombre']}: Presupuesto mínimo muy bajo (${presupuesto_min:,} vs mínimo ${precio_min_global:,})")

    if presupuesto_max > precio_max_global * 1.2:
        print(f"ADVERTENCIA {perfil['nombre']}: Presupuesto máximo muy alto (${presupuesto_max:,} vs máximo ${precio_max_global:,})")

    # Verificar que haya propiedades en el rango
    propiedades_en_rango = [
        prop for prop in propiedades
        if presupuesto_min <= prop['caracteristicas']['precio'] <= presupuesto_max
    ]

    if not propiedades_en_rango:
        print(f"ERROR {perfil['nombre']}: No hay propiedades en el rango de presupuesto")
        return False

    print(f"OK {perfil['nombre']}: {len(propiedades_en_rango)} propiedades en rango (${presupuesto_min:,}-${presupuesto_max:,})")
    return True

def validar_composicion_familiar(perfil):
    """Valida que la composición familiar sea consistente"""
    composicion = perfil['composicion_familiar']

    # Validar coherencia
    total_personas = composicion['adultos'] + len(composicion['ninos']) + composicion['adultos_mayores']

    if total_personas == 0:
        print(f"ERROR {perfil['nombre']}: No hay personas en la composición familiar")
        return False

    # Validar necesidades vs composición
    necesidades = perfil['necesidades']

    if 'escuela_primaria' in necesidades and not any(nino['edad'] <= 12 for nino in composicion['ninos']):
        print(f"ADVERTENCIA {perfil['nombre']}: Necesita escuela primaria pero no tiene niños en edad escolar")

    if 'universidad' in necesidades and not any(nino['edad'] >= 17 for nino in composicion['ninos']):
        print(f"ADVERTENCIA {perfil['nombre']}: Necesita universidad pero no tiene jóvenes en edad universitaria")

    print(f"OK {perfil['nombre']}: Composición familiar válida ({total_personas} personas)")
    return True

def validar_servicios_requeridos(perfil, propiedades):
    """Valida que los servicios requeridos estén disponibles en propiedades"""
    necesidades = perfil['necesidades']

    # Contar cuántas propiedades tienen cada servicio requerido
    servicios_disponibles = {}

    for necesidad in necesidades:
        if necesidad == 'area_verde':
            continue  # No está en datos de servicios

        count = 0
        for prop in propiedades:
            if necesidad in prop.get('servicios_cercanos', {}):
                if prop['servicios_cercanos'][necesidad]:
                    count += 1

        servicios_disponibles[necesidad] = count

    for servicio, count in servicios_disponibles.items():
        if count == 0:
            print(f"ERROR {perfil['nombre']}: Servicio '{servicio}' no disponible en ninguna propiedad")
            return False
        elif count < len(propiedades) // 2:
            print(f"ADVERTENCIA {perfil['nombre']}: Servicio '{servicio}' disponible solo en {count}/{len(propiedades)} propiedades")
        else:
            print(f"OK {perfil['nombre']}: Servicio '{servicio}' disponible en {count}/{len(propiedades)} propiedades")

    return True

def validar_coherencia_general(perfil):
    """Valida coherencia general del perfil"""
    composicion = perfil['composicion_familiar']
    presupuesto = perfil['presupuesto']
    preferencias = perfil['preferencias']

    # Validar coherencia presupuesto vs composición
    total_personas = composicion['adultos'] + len(composicion['ninos']) + composicion['adultos_mayores']

    if total_personas >= 4 and presupuesto['max'] < 200000:
        print(f"ADVERTENCIA {perfil['nombre']}: Familia numerosa ({total_personas} personas) con presupuesto bajo")

    # Validar coherencia vehículos vs estacionamiento
    if composicion.get('vehiculos', 0) > 0:
        if 'estacionamiento' not in preferencias.get('caracteristicas_deseadas', []):
            print(f"ADVERTENCIA {perfil['nombre']}: Tiene vehículo pero no solicita estacionamiento")

    print(f"OK {perfil['nombre']}: Coherencia general validada")
    return True

def main():
    """Función principal de validación"""
    print("Validando perfiles de prospectos...")
    print("=" * 50)

    propiedades, perfiles = cargar_datos()

    print(f"Cargadas {len(propiedades)} propiedades y {len(perfiles)} perfiles")
    print()

    perfiles_validos = 0

    for perfil in perfiles:
        print(f"\nValidando perfil: {perfil['nombre']}")
        print("-" * 40)

        validaciones = [
            validar_presupuesto(perfil, propiedades),
            validar_composicion_familiar(perfil),
            validar_servicios_requeridos(perfil, propiedades),
            validar_coherencia_general(perfil)
        ]

        if all(validaciones):
            print(f"OK {perfil['nombre']}: Perfil VALIDO")
            perfiles_validos += 1
        else:
            print(f"ERROR {perfil['nombre']}: Perfil con ERRORES")

    print("\n" + "=" * 50)
    print(f"Resumen: {perfiles_validos}/{len(perfiles)} perfiles válidos")

    if perfiles_validos == len(perfiles):
        print("TODOS los perfiles son válidos y realistas")
    else:
        print("Algunos perfiles necesitan ajustes")

if __name__ == "__main__":
    main()