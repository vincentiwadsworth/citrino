#!/usr/bin/env python3
"""
Sistema de enriquecimiento de recomendaciones con datos de la guía urbana municipal
Utiliza los datos municipales como información de referencia, no como propiedades disponibles
"""

import json
import os
import math
from typing import Dict, List, Any, Optional
from datetime import datetime

class SistemaEnriquecimientoMunicipal:
    """Sistema para enriquecer recomendaciones con datos de referencia de la guía urbana"""

    def __init__(self):
        self.datos_municipales = {}
        self.indices_servicios = {}
        self.cargar_datos_municipales()

    def cargar_datos_municipales(self):
        """Carga los datos de la guía urbana municipal como referencia"""
        ruta_guia = os.path.join(os.path.dirname(__file__), '..', 'data', 'guia_urbana_municipal.json')

        if not os.path.exists(ruta_guia):
            print("No se encontró la guía urbana municipal")
            return

        try:
            with open(ruta_guia, 'r', encoding='utf-8') as f:
                datos = json.load(f)

            if isinstance(datos, list):
                self.datos_municipales = {prop.get('id', f"prop_{i}"): prop for i, prop in enumerate(datos)}
            else:
                self.datos_municipales = datos

            self.crear_indices_servicios()
            print(f"Guía urbana municipal cargada: {len(self.datos_municipales)} referencias")

        except Exception as e:
            print(f"Error cargando guía urbana: {e}")

    def crear_indices_servicios(self):
        """Crea índices de servicios por zona para búsquedas rápidas"""
        self.indices_servicios = {
            'escuelas': {},
            'hospitales': {},
            'supermercados': {},
            'parques': {},
            'transporte': {}
        }

        for prop_id, prop_municipal in self.datos_municipales.items():
            servicios = prop_municipal.get('servicios_cercanos', {})
            ubicacion = prop_municipal.get('ubicacion', {})
            zona = ubicacion.get('zona', 'Desconocida')

            if zona not in self.indices_servicios['escuelas']:
                self.indices_servicios['escuelas'][zona] = []
                self.indices_servicios['hospitales'][zona] = []
                self.indices_servicios['supermercados'][zona] = []
                self.indices_servicios['parques'][zona] = []
                self.indices_servicios['transporte'][zona] = []

            # Indexar servicios por distancia
            for tipo_servicio, servicios_lista in servicios.items():
                if isinstance(servicios_lista, list):
                    for servicio in servicios_lista:
                        if isinstance(servicio, dict):
                            distancia = servicio.get('distancia_m', 1000)
                            if tipo_servicio == 'escuela_primaria' or tipo_servicio == 'colegio_privado':
                                self.indices_servicios['escuelas'][zona].append(distancia)
                            elif tipo_servicio == 'hospital' or tipo_servicio == 'centro_salud':
                                self.indices_servicios['hospitales'][zona].append(distancia)
                            elif tipo_servicio == 'supermercado':
                                self.indices_servicios['supermercados'][zona].append(distancia)
                            elif tipo_servicio == 'parque' or tipo_servicio == 'area_verde':
                                self.indices_servicios['parques'][zona].append(distancia)
                            elif tipo_servicio == 'transporte_publico':
                                self.indices_servicios['transporte'][zona].append(distancia)

    def calcular_puntuacion_servicios(self, zona: str, necesidades: List[str]) -> float:
        """Calcula puntuación de servicios para una zona según necesidades específicas"""
        if zona not in self.indices_servicios['escuelas']:
            return 0.5  # Puntuación neutra si no hay datos

        puntuacion = 0.0
        factores = 0

        # Evaluar servicios según necesidades
        if any('colegio' in necesidad.lower() or 'escuela' in necesidad.lower() for necesidad in necesidades):
            if self.indices_servicios['escuelas'][zona]:
                distancia_promedio = sum(self.indices_servicios['escuelas'][zona]) / len(self.indices_servicios['escuelas'][zona])
                puntuacion += max(0, 1 - (distancia_promedio / 1000))  # Mejor si está cerca
                factores += 1

        if any('hospital' in necesidad.lower() or 'médico' in necesidad.lower() or 'salud' in necesidad.lower() for necesidad in necesidades):
            if self.indices_servicios['hospitales'][zona]:
                distancia_promedio = sum(self.indices_servicios['hospitales'][zona]) / len(self.indices_servicios['hospitales'][zona])
                puntuacion += max(0, 1 - (distancia_promedio / 1500))
                factores += 1

        if any('supermercado' in necesidad.lower() or 'compras' in necesidad.lower() for necesidad in necesidades):
            if self.indices_servicios['supermercados'][zona]:
                distancia_promedio = sum(self.indices_servicios['supermercados'][zona]) / len(self.indices_servicios['supermercados'][zona])
                puntuacion += max(0, 1 - (distancia_promedio / 800))
                factores += 1

        if any('parque' in necesidad.lower() or 'area verde' in necesidad.lower() for necesidad in necesidades):
            if self.indices_servicios['parques'][zona]:
                distancia_promedio = sum(self.indices_servicios['parques'][zona]) / len(self.indices_servicios['parques'][zona])
                puntuacion += max(0, 1 - (distancia_promedio / 600))
                factores += 1

        return puntuacion / max(factores, 1)

    def obtener_datos_administrativos_zona(self, zona: str) -> Dict[str, Any]:
        """Obtiene datos administrativos consolidados para una zona"""
        datos_zona = {
            'distritos': set(),
            'unidades_vecinales': set(),
            'valoracion_promedio': 0,
            'densidad_servicios': 0,
            'seguridad_referencial': 0.5
        }

        propiedades_zona = [p for p in self.datos_municipales.values()
                          if p.get('ubicacion', {}).get('zona') == zona]

        if not propiedades_zona:
            return datos_zona

        total_propiedades = len(propiedades_zona)
        valoraciones = []

        for prop in propiedades_zona:
            ubic = prop.get('ubicacion', {})
            if ubic.get('distrito_municipal'):
                datos_zona['distritos'].add(ubic['distrito_municipal'])
            if ubic.get('unidad_vecinal'):
                datos_zona['unidades_vecinales'].add(ubic['unidad_vecinal'])

            # Recopilar valoraciones si existen
            caract = prop.get('caracteristicas_principales', {})
            if caract.get('valoracion_municipal'):
                valoraciones.append(caract['valoracion_municipal'])

        # Calcular valoración promedio
        if valoraciones:
            datos_zona['valoracion_promedio'] = sum(valoraciones) / len(valoraciones)

        # Calcular densidad de servicios
        total_servicios = 0
        for servicios_tipo in self.indices_servicios.values():
            if zona in servicios_tipo:
                total_servicios += len(servicios_tipo[zona])

        datos_zona['densidad_servicios'] = total_servicios / max(total_propiedades, 1)

        return datos_zona

    def enriquecer_recomendacion(self, propiedad: Dict[str, Any], necesidades: List[str]) -> Dict[str, Any]:
        """Enriquece una recomendación con datos municipales de referencia"""

        # Extraer información básica
        caract = propiedad.get('caracteristicas_principales', {})
        ubicacion = propiedad.get('ubicacion', {})
        zona = ubicacion.get('zona', 'Desconocida')

        # Obtener datos municipales de referencia para la zona
        datos_administrativos = self.obtener_datos_administrativos_zona(zona)
        puntuacion_servicios = self.calcular_puntuacion_servicios(zona, necesidades)

        # Calcular factor de enriquecimiento municipal
        factor_enriquecimiento = 1.0
        if puntuacion_servicios > 0.7:
            factor_enriquecimiento = 1.15  # +15% si hay excelentes servicios
        elif puntuacion_servicios < 0.3:
            factor_enriquecimiento = 0.9   # -10% si hay servicios deficientes

        # Generar justificación enriquecida
        justificacion_adicional = self.generar_justificacion_enriquecida(
            zona, datos_administrativos, puntuacion_servicios, necesidades
        )

        return {
            'factor_enriquecimiento': factor_enriquecimiento,
            'puntuacion_servicios': round(puntuacion_servicios * 100, 1),
            'datos_administrativos': datos_administrativos,
            'justificacion_adicional': justificacion_adicional,
            'servicios_destacados': self.obtener_servicios_destacados(zona, necesidades)
        }

    def generar_justificacion_enriquecida(self, zona: str, datos_admin: Dict[str, Any],
                                         puntuacion_servicios: float, necesidades: List[str]) -> str:
        """Genera justificación adicional basada en datos municipales"""

        justificacion = ""

        # Información de distritos
        if datos_admin['distritos']:
            distritos_str = ", ".join(sorted(datos_admin['distritos']))
            justificacion += f"Ubicada en distritos municipales: {distritos_str}. "

        # Valoración municipal
        if datos_admin['valoracion_promedio'] > 0:
            valoracion = datos_admin['valoracion_promedio']
            if valoracion >= 4:
                justificacion += f"Zona con alta valoración municipal ({valoracion:.1f}/5). "
            elif valoracion >= 3:
                justificacion += f"Zona con buena valoración municipal ({valoracion:.1f}/5). "

        # Servicios según necesidades
        if puntuacion_servicios >= 0.8:
            justificacion += "Excelente accesibilidad a servicios esenciales. "
        elif puntuacion_servicios >= 0.6:
            justificacion += "Buena cobertura de servicios cercanos. "
        elif puntuacion_servicios < 0.4:
            justificacion += "Considerar distancia a servicios principales. "

        # Densidad de servicios
        if datos_admin['densidad_servicios'] > 5:
            justificacion += "Zona con alta densidad de servicios y comodidades. "

        return justificacion.strip()

    def obtener_servicios_destacados(self, zona: str, necesidades: List[str]) -> List[Dict[str, Any]]:
        """Obtiene los servicios más destacados para una zona y necesidades específicas"""

        servicios_destacados = []

        # Servicios educativos si son necesarios
        if any('colegio' in n.lower() or 'escuela' in n.lower() for n in necesidades):
            if zona in self.indices_servicios['escuelas'] and self.indices_servicios['escuelas'][zona]:
                distancia_min = min(self.indices_servicios['escuelas'][zona])
                if distancia_min < 500:
                    servicios_destacados.append({
                        'tipo': 'Educativo',
                        'descripcion': f'Centros educativos a {distancia_min}m',
                        'puntuacion': 5
                    })

        # Servicios de salud si son necesarios
        if any('hospital' in n.lower() or 'médico' in n.lower() for n in necesidades):
            if zona in self.indices_servicios['hospitales'] and self.indices_servicios['hospitales'][zona]:
                distancia_min = min(self.indices_servicios['hospitales'][zona])
                if distancia_min < 1000:
                    servicios_destacados.append({
                        'tipo': 'Salud',
                        'descripcion': f'Centros de salud a {distancia_min}m',
                        'puntuacion': 5
                    })

        # Comercio
        if zona in self.indices_servicios['supermercados'] and self.indices_servicios['supermercados'][zona]:
            distancia_min = min(self.indices_servicios['supermercados'][zona])
            if distancia_min < 300:
                servicios_destacados.append({
                    'tipo': 'Comercio',
                    'descripcion': f'Supermercados a {distancia_min}m',
                    'puntuacion': 4
                })

        # Areas verdes
        if zona in self.indices_servicios['parques'] and self.indices_servicios['parques'][zona]:
            distancia_min = min(self.indices_servicios['parques'][zona])
            if distancia_min < 400:
                servicios_destacados.append({
                    'tipo': 'Recreación',
                    'descripcion': f'Áreas verdes a {distancia_min}m',
                    'puntuacion': 4
                })

        return servicios_destacados[:3]  # Máximo 3 servicios destacados

def probar_sistema_enriquecimiento():
    """Prueba el sistema de enriquecimiento con datos de ejemplo"""
    print("=== PRUEBA DE SISTEMA DE ENRIQUECIMIENTO MUNICIPAL ===\n")

    sistema = SistemaEnriquecimientoMunicipal()

    # Propiedad de ejemplo
    propiedad_ejemplo = {
        'id': 'franz_a261494d',
        'nombre': 'Casa en Equipetrol',
        'caracteristicas_principales': {
            'precio': 269595,
            'superficie_m2': 159,
            'habitaciones': 3,
            'banos_completos': 2
        },
        'ubicacion': {
            'zona': 'Equipetrol',
            'direccion': 'Av. Principal y Calle Secundaria'
        }
    }

    # Necesidades de ejemplo
    necesidades_familia = ['seguridad', 'colegios', 'areas verdes', 'supermercado']
    necesidades_adultos_mayores = ['hospital', 'farmacia', 'tranquilidad', 'acceso facil']

    print("1. Enriquecimiento para familia con hijos:")
    resultado_familia = sistema.enriquecer_recomendacion(propiedad_ejemplo, necesidades_familia)
    print(f"   - Factor de enriquecimiento: {resultado_familia['factor_enriquecimiento']:.2f}")
    print(f"   - Puntuación de servicios: {resultado_familia['puntuacion_servicios']}%")
    print(f"   - Justificación adicional: {resultado_familia['justificacion_adicional']}")
    print(f"   - Servicios destacados: {len(resultado_familia['servicios_destacados'])}")
    for serv in resultado_familia['servicios_destacados']:
        print(f"     * {serv['tipo']}: {serv['descripcion']}")

    print("\n2. Enriquecimiento para adultos mayores:")
    resultado_adultos = sistema.enriquecer_recomendacion(propiedad_ejemplo, necesidades_adultos_mayores)
    print(f"   - Factor de enriquecimiento: {resultado_adultos['factor_enriquecimiento']:.2f}")
    print(f"   - Puntuación de servicios: {resultado_adultos['puntuacion_servicios']}%")
    print(f"   - Justificación adicional: {resultado_adultos['justificacion_adicional']}")
    print(f"   - Servicios destacados: {len(resultado_adultos['servicios_destacados'])}")
    for serv in resultado_adultos['servicios_destacados']:
        print(f"     * {serv['tipo']}: {serv['descripcion']}")

    print(f"\n=== RESUMEN ===")
    print(f"Datos municipales cargados: {len(sistema.datos_municipales)} referencias")
    print(f"Zonas con información de servicios: {len(sistema.indices_servicios['escuelas'])}")
    print("Sistema listo para integrar con motor de recomendaciones")

if __name__ == "__main__":
    probar_sistema_enriquecimiento()