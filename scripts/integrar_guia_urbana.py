#!/usr/bin/env python3
"""
Integración de datos de la guía urbana municipal a la base de datos principal de Citrino
"""

import json
import os
import sys
from datetime import datetime

# Agregar directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

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
        # Verificar si es una lista de propiedades o un diccionario
        if isinstance(datos, list):
            return datos
        elif isinstance(datos, dict) and 'propiedades' in datos:
            return datos['propiedades']
        else:
            print("Formato de archivo no reconocido")
            return []

def procesar_propiedad_municipal(prop_municipal):
    """Procesa una propiedad municipal para integrarla al formato estándar"""

    # Extraer coordenadas con manejo de errores
    try:
        ubicacion = prop_municipal.get('ubicacion', {})
        if isinstance(ubicacion, dict):
            coordenadas = ubicacion.get('coordenadas', {})
            if isinstance(coordenadas, dict):
                lat = coordenadas.get('lat', 0)
                lng = coordenadas.get('lng', 0)
            else:
                lat, lng = 0, 0
        else:
            lat, lng = 0, 0
    except:
        lat, lng = 0, 0

    # Procesar servicios cercanos con manejo de errores
    try:
        servicios_cercanos = prop_municipal.get('servicios_cercanos', [])
        if not isinstance(servicios_cercanos, list):
            servicios_cercanos = []

        servicios_por_tipo = {}

        for servicio in servicios_cercanos:
            if isinstance(servicio, dict):
                tipo = servicio.get('tipo', 'desconocido')
                if tipo not in servicios_por_tipo:
                    servicios_por_tipo[tipo] = []

                servicios_por_tipo[tipo].append({
                    'nombre': servicio.get('nombre', ''),
                    'distancia_m': servicio.get('distancia_m', 0),
                    'direccion': servicio.get('direccion', ''),
                    'tipo_servicio': servicio.get('tipo_servicio', 'publico')
                })
    except:
        servicios_por_tipo = {}

    # Calcular estadísticas de servicios con manejo de errores
    stats_servicios = {}
    try:
        for tipo, servicios in servicios_por_tipo.items():
            if servicios:
                distancias = [s.get('distancia_m', 0) for s in servicios if isinstance(s, dict)]
                if distancias:
                    stats_servicios[tipo] = {
                        'cantidad': len(servicios),
                        'distancia_promedio_m': round(sum(distancias) / len(distancias), 0),
                        'distancia_minima_m': min(distancias),
                        'servicio_cercano': min(servicios, key=lambda x: x.get('distancia_m', float('inf')))
                    }
    except:
        stats_servicios = {}

    # Crear propiedad en formato estándar con manejo seguro de datos
    try:
        caract_principales = prop_municipal.get('caracteristicas_principales', {})
        if isinstance(caract_principales, dict):
            precio = caract_principales.get('precio', 0)
            superficie = caract_principales.get('superficie_m2', 0)
            habitaciones = caract_principales.get('habitaciones', 0)
            dormitorios = caract_principales.get('dormitorios', 0)
            banos_completos = caract_principales.get('banos_completos', 0)
            banos_medios = caract_principales.get('banos_medios', 0)
            cochera = caract_principales.get('cochera_garaje', False)
            espacios_garaje = caract_principales.get('numero_espacios_garaje', 0)
        else:
            precio = superficie = habitaciones = dormitorios = banos_completos = banos_medios = 0
            cochera = False
            espacios_garaje = 0

        ubicacion = prop_municipal.get('ubicacion', {})
        if isinstance(ubicacion, dict):
            barrio = ubicacion.get('barrio', '')
            zona = ubicacion.get('zona', '')
            direccion = ubicacion.get('direccion', '')
            distrito = ubicacion.get('distrito_municipal', '')
            unidad_vecinal = ubicacion.get('unidad_vecinal', '')
            manzana = ubicacion.get('manzana_catastral', '')
        else:
            barrio = zona = direccion = distrito = unidad_vecinal = manzana = ''

        propiedad_estandar = {
            'id': f"municipal_{prop_municipal.get('id', 'unknown')}",
            'nombre': prop_municipal.get('nombre', ''),
            'fuente': 'guia_urbana_municipal',
            'descripcion': f"Propiedad municipal con datos administrativos completos. Ubicada en {barrio}, {zona}.",
            'caracteristicas_principales': {
                'precio': precio,
                'superficie_m2': superficie,
                'habitaciones': habitaciones,
                'dormitorios': dormitorios,
                'banos_completos': banos_completos,
                'banos_medios': banos_medios,
                'cochera_garaje': cochera,
                'numero_espacios_garaje': espacios_garaje
            },
        'ubicacion': {
            'direccion': direccion,
            'barrio': barrio,
            'zona': zona,
            'coordenadas': {
                'lat': lat,
                'lng': lng
            },
            'datos_administrativos': {
                'distrito_municipal': distrito,
                'unidad_vecinal': unidad_vecinal,
                'manzana_catastral': manzana
            }
        },
        'detalles_adicionales': {
            'antiguedad_anios': 0,
            'estado_conservacion': '',
            'piso': 0,
            'amoblado': False
        },
        'condominio': {},
        'valoracion_municipal': {
            'valor_m2_promedio_zona': 0,
            'tendencia_plusvalia': '',
            'demanda_sectorial': '',
            'seguridad_zona': '',
            'nivel_socioeconomico': ''
        },
        'servicios_cercanos': stats_servicios,
        'puntuacion_servicios': calcular_puntuacion_servicios(stats_servicios),
        'fecha_incorporacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    return propiedad_estandar
    except Exception as e:
        print(f"Error creando propiedad estandar: {e}")
        return None

def calcular_puntuacion_servicios(servicios_stats):
    """Calcula una puntuación basada en la accesibilidad a servicios"""

    pesos_servicios = {
        'escuela_primaria': 0.20,
        'colegio_privado': 0.15,
        'supermercado': 0.15,
        'hospital': 0.15,
        'farmacia': 0.10,
        'area_verde': 0.10,
        'universidad': 0.10,
        'restaurante': 0.05
    }

    puntuacion_total = 0
    detalles_puntuacion = {}

    for tipo_servicio, peso in pesos_servicios.items():
        if tipo_servicio in servicios_stats:
            stats = servicios_stats[tipo_servicio]
            distancia_promedio = stats['distancia_promedio_m']

            # Calcular puntuación por distancia (más cerca = mejor)
            if distancia_promedio <= 300:
                puntuacion_distancia = 1.0
            elif distancia_promedio <= 600:
                puntuacion_distancia = 0.7
            elif distancia_promedio <= 1000:
                puntuacion_distancia = 0.4
            else:
                puntuacion_distancia = 0.1

            puntuacion_servicio = puntuacion_distancia * peso
            puntuacion_total += puntuacion_servicio

            detalles_puntuacion[tipo_servicio] = {
                'puntuacion': round(puntuacion_servicio, 3),
                'distancia_promedio_m': distancia_promedio,
                'cantidad': stats['cantidad']
            }

    return {
        'puntuacion_total': round(puntuacion_total, 3),
        'detalles': detalles_puntuacion
    }

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
        try:
            # Depuración: mostrar tipo y contenido
            print(f"Procesando item {i+1}: tipo={type(prop_municipal)}")
            if isinstance(prop_municipal, str):
                print(f"  Contenido string: {prop_municipal[:100]}...")
                continue

            propiedad_procesada = procesar_propiedad_municipal(prop_municipal)
            propiedades_municipales_procesadas.append(propiedad_procesada)
        except Exception as e:
            if isinstance(prop_municipal, dict):
                print(f"Error procesando propiedad {prop_municipal.get('id', 'desconocido')}: {e}")
            else:
                print(f"Error procesando item {i+1}: {e}")
            continue

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
    generar_resumen_estadistico(base_integrada)

    return True

def generar_resumen_estadistico(base_datos):
    """Genera un resumen estadístico de la integración"""

    total_propiedades = len(base_datos)
    propiedades_municipales = [p for p in base_datos if p.get('fuente') == 'guia_urbana_municipal']

    print("\n**RESUMEN ESTADISTICO DE INTEGRACION**")
    print("=" * 50)
    print(f"Total propiedades: {total_propiedades:,}")
    print(f"Propiedades municipales: {len(propiedades_municipales)}")
    print(f"Porcentaje municipal: {(len(propiedades_municipales) / total_propiedades * 100):.1f}%")

    # Analizar calidad de datos municipales
    if propiedades_municipales:
        puntuaciones_servicios = [p.get('puntuacion_servicios', {}).get('puntuacion_total', 0) for p in propiedades_municipales]
        promedio_puntuacion = sum(puntuaciones_servicios) / len(puntuaciones_servicios)

        print(f"Puntuación promedio de servicios: {promedio_puntuacion:.3f}")

        # Top servicios por propiedad
        top_servicios = {}
        for prop in propiedades_municipales:
            servicios = prop.get('servicios_cercanos', {})
            for tipo, stats in servicios.items():
                if tipo not in top_servicios:
                    top_servicios[tipo] = []
                top_servicios[tipo].append(stats['distancia_promedio_m'])

        print("\n**SERVICIOS MUNICIPALES PROMEDIO**")
        for servicio, distancias in sorted(top_servicios.items()):
            promedio_dist = sum(distancias) / len(distancias)
            print(f"{servicio.replace('_', ' ').title()}: {promedio_dist:.0f}m")

    print("\n**Integracion completada exitosamente**")

if __name__ == "__main__":
    integrar_guia_urbana()