#!/usr/bin/env python3
"""
Integración simple de datos de la guía urbana municipal a la base de datos principal de Citrino
"""

import json
import os
import sys
from datetime import datetime

def cargar_base_datos_principal():
    """Carga la base de datos principal de Citrino"""
    ruta_bd = os.path.join(os.path.dirname(__file__), '..', 'data', 'base_datos_citrino_limpios.json')

    if not os.path.exists(ruta_bd):
        print("No se encontro la base de datos principal")
        return []

    with open(ruta_bd, 'r', encoding='utf-8') as f:
        return json.load(f)

def cargar_guia_urbana():
    """Carga los datos de la guia urbana municipal"""
    ruta_guia = os.path.join(os.path.dirname(__file__), '..', 'data', 'propiedades_mejorado.json')

    if not os.path.exists(ruta_guia):
        print("No se encontro la guia urbana municipal")
        return []

    with open(ruta_guia, 'r', encoding='utf-8') as f:
        datos = json.load(f)
        # Verificar si es una lista de propiedades
        if isinstance(datos, list):
            return datos
        else:
            print("Formato de archivo no reconocido")
            return []

def procesar_propiedad_municipal_simple(prop_municipal):
    """Procesa una propiedad municipal de forma simple"""

    try:
        # Extraer datos básicos con seguridad
        caract = prop_municipal.get('caracteristicas_principales', {})
        if not isinstance(caract, dict):
            caract = {}

        ubic = prop_municipal.get('ubicacion', {})
        if not isinstance(ubic, dict):
            ubic = {}

        # Crear propiedad en formato estándar simplificado
        propiedad_estandar = {
            'id': f"municipal_{prop_municipal.get('id', 'unknown')}",
            'nombre': prop_municipal.get('nombre', ''),
            'fuente': 'guia_urbana_municipal',
            'descripcion': f"Propiedad municipal con datos administrativos completos.",
            'caracteristicas_principales': {
                'precio': caract.get('precio', 0),
                'superficie_m2': caract.get('superficie_m2', 0),
                'habitaciones': caract.get('habitaciones', 0),
                'dormitorios': caract.get('dormitorios', 0),
                'banos_completos': caract.get('banos_completos', 0),
                'banos_medios': caract.get('banos_medios', 0),
                'cochera_garaje': caract.get('cochera_garaje', False),
                'numero_espacios_garaje': caract.get('numero_espacios_garaje', 0)
            },
            'ubicacion': {
                'direccion': ubic.get('direccion', ''),
                'barrio': ubic.get('barrio', ''),
                'zona': ubic.get('zona', ''),
                'coordenadas': {
                    'lat': ubic.get('coordenadas', {}).get('lat', 0),
                    'lng': ubic.get('coordenadas', {}).get('lng', 0)
                },
                'datos_administrativos': {
                    'distrito_municipal': ubic.get('distrito_municipal', ''),
                    'unidad_vecinal': ubic.get('unidad_vecinal', ''),
                    'manzana_catastral': ubic.get('manzana_catastral', '')
                }
            },
            'servicios_cercanos': prop_municipal.get('servicios_cercanos', []),
            'fecha_incorporacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        return propiedad_estandar

    except Exception as e:
        print(f"Error procesando propiedad: {e}")
        return None

def integrar_guia_urbana():
    """Función principal de integración"""
    print("Iniciando integracion de Guia Urbana Municipal...")

    # Cargar datos
    bd_principal = cargar_base_datos_principal()
    guia_urbana = cargar_guia_urbana()

    if not bd_principal or not guia_urbana:
        print("No se pudieron cargar los datos necesarios")
        return False

    print(f"Base de datos principal: {len(bd_principal):,} propiedades")
    print(f"Guia urbana municipal: {len(guia_urbana)} propiedades")

    # Procesar propiedades municipales
    propiedades_municipales_procesadas = []

    for i, prop_municipal in enumerate(guia_urbana):
        if isinstance(prop_municipal, dict):
            propiedad_procesada = procesar_propiedad_municipal_simple(prop_municipal)
            if propiedad_procesada:
                propiedades_municipales_procesadas.append(propiedad_procesada)

    print(f"Propiedades municipales procesadas: {len(propiedades_municipales_procesadas)}")

    # Integrar a la base de datos principal
    base_integrada = bd_principal + propiedades_municipales_procesadas

    # Guardar base de datos integrada
    ruta_salida = os.path.join(os.path.dirname(__file__), '..', 'data', 'base_datos_citrino_con_municipal.json')

    with open(ruta_salida, 'w', encoding='utf-8') as f:
        json.dump(base_integrada, f, ensure_ascii=False, indent=2)

    print(f"Base de datos integrada guardada en: {ruta_salida}")
    print(f"Total final de propiedades: {len(base_integrada):,}")

    # Generar resumen estadístico
    propiedades_municipales = [p for p in base_integrada if p.get('fuente') == 'guia_urbana_municipal']

    print("\n**RESUMEN ESTADISTICO DE INTEGRACION**")
    print("=" * 50)
    print(f"Total propiedades: {len(base_integrada):,}")
    print(f"Propiedades municipales: {len(propiedades_municipales)}")
    print(f"Porcentaje municipal: {(len(propiedades_municipales) / len(base_integrada) * 100):.1f}%")

    # Mostrar algunas propiedades municipales de ejemplo
    if propiedades_municipales:
        print("\n**EJEMPLOS DE PROPIEDADES MUNICIPALES**")
        for i, prop in enumerate(propiedades_municipales[:3]):
            print(f"{i+1}. {prop['nombre']} - {prop['ubicacion']['zona']} - ${prop['caracteristicas_principales']['precio']:,}")

    print("\n**Integracion completada exitosamente**")
    return True

if __name__ == "__main__":
    integrar_guia_urbana()