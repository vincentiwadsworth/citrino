"""
Motor de recomendación mejorado con georreferenciación real y guía urbana
Implementa cálculo de distancias reales entre propiedades y servicios
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
import json
import math
from functools import lru_cache
import time
import threading
from pathlib import Path


class RecommendationEngineMejorado:
    """Motor de recomendación con georreferenciación real y guía urbana."""

    def __init__(self):
        self.propiedades = []
        self.guias_urbanas = []
        self.indice_servicios_espaciales = {}
        self.pesos = {
            'presupuesto': 0.25,
            'composicion_familiar': 0.20,
            'servicios_cercanos': 0.30,  # Aumentado peso por ser ahora más preciso
            'demografia': 0.15,
            'preferencias': 0.10
        }
        # Cache para cálculos repetitivos
        self._cache_puntuaciones = {}
        self._cache_compatibility = {}
        self._cache_distancias = {}
        self._cache_lock = threading.Lock()
        # Estadísticas de rendimiento
        self.stats = {
            'calculos_realizados': 0,
            'cache_hits': 0,
            'tiempo_total': 0.0,
            'distancias_calculadas': 0
        }

    def cargar_propiedades(self, propiedades: List[Dict[str, Any]]):
        """Carga las propiedades disponibles en el motor."""
        self.propiedades = propiedades
        self._limpiar_cache()

    def cargar_guias_urbanas(self, ruta_guias: str):
        """Carga la guía urbana y crea índices espaciales."""
        try:
            with open(ruta_guias, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.guias_urbanas = data.get('servicios_consolidados', [])

            # Crear índice espacial para búsquedas eficientes
            self._crear_indice_espacial_servicios()
            print(f"Guia urbana cargada: {len(self.guias_urbanas)} servicios indexados")

        except Exception as e:
            print(f"Error cargando guia urbana: {e}")
            self.guias_urbanas = []

    def _crear_indice_espacial_servicios(self):
        """Crea un índice espacial para búsquedas eficientes de servicios."""
        self.indice_servicios_espaciales = {}

        for servicio in self.guias_urbanas:
            categoria = servicio.get('categoria_principal', 'otros')
            if categoria not in self.indice_servicios_espaciales:
                self.indice_servicios_espaciales[categoria] = []

            if 'coordenadas' in servicio:
                coords = servicio['coordenadas']
                if coords.get('lat') and coords.get('lng'):
                    self.indice_servicios_espaciales[categoria].append({
                        'nombre': servicio.get('nombre', ''),
                        'coordenadas': coords,
                        'direccion': servicio.get('direccion', ''),
                        'tipo': servicio.get('tipo', '')
                    })

    def _limpiar_cache(self):
        """Limpia el cache de cálculos."""
        with self._cache_lock:
            self._cache_puntuaciones.clear()
            self._cache_compatibility.clear()
            self._cache_distancias.clear()

    def _generar_cache_key(self, perfil: Dict[str, Any], propiedad: Dict[str, Any], funcion: str) -> str:
        """Genera una clave única para el cache."""
        perfil_id = str(hash(str(sorted(perfil.items()))))
        propiedad_id = propiedad.get('id', str(hash(str(sorted(propiedad.items())))))
        return f"{funcion}:{perfil_id}:{propiedad_id}"

    @staticmethod
    def _calcular_distancia_haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        Calcula la distancia entre dos puntos usando la fórmula de Haversine.
        Retorna distancia en kilómetros.
        """
        # Convertir a radianes
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])

        # Diferencias
        dlat = lat2 - lat1
        dlng = lng2 - lng1

        # Fórmula de Haversine
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))

        # Radio de la Tierra en kilómetros
        r = 6371

        return c * r

    def _encontrar_servicios_cercanos(self, propiedad_coords: Dict[str, float],
                                    categorias_busqueda: List[str],
                                    radio_km: float = 3.0) -> List[Dict]:
        """
        Encuentra servicios cercanos a una propiedad dentro de un radio específico.
        """
        servicios_cercanos = []

        if not propiedad_coords or 'lat' not in propiedad_coords or 'lng' not in propiedad_coords:
            return servicios_cercanos

        prop_lat = propiedad_coords['lat']
        prop_lng = propiedad_coords['lng']

        for categoria in categorias_busqueda:
            if categoria in self.indice_servicios_espaciales:
                for servicio in self.indice_servicios_espaciales[categoria]:
                    serv_coords = servicio['coordenadas']
                    distancia = self._calcular_distancia_haversine(
                        prop_lat, prop_lng, serv_coords['lat'], serv_coords['lng']
                    )

                    if distancia <= radio_km:
                        servicios_cercanos.append({
                            **servicio,
                            'categoria': categoria,
                            'distancia_km': round(distancia, 2)
                        })

        self.stats['distancias_calculadas'] += 1
        return sorted(servicios_cercanos, key=lambda x: x['distancia_km'])

    def _mapear_necesidades_a_categorias(self, necesidades: List[str]) -> List[str]:
        """
        Mapea necesidades genéricas a categorías específicas de la guía urbana.
        """
        mapeo = {
            'educacion': ['educacion'],
            'escuela_primaria': ['educacion'],
            'colegio': ['educacion'],
            'universidad': ['educacion'],

            'salud': ['salud'],
            'hospital': ['salud'],
            'clinica': ['salud'],
            'servicios_medicos': ['salud'],

            'seguridad': ['transporte'],  # Asociamos seguridad con accesibilidad policial
            'transporte': ['transporte'],
            'accesibilidad': ['transporte'],

            'comercio': ['abastecimiento'],
            'supermercado': ['abastecimiento'],
            'abastecimiento': ['abastecimiento'],

            'deporte': ['deporte'],
            'gimnasio': ['deporte'],
            'areas_verdes': ['deporte'],

            'cultura': ['otros'],
            'entretenimiento': ['otros'],

            'estacionamiento': ['transporte'],
            'areas_comunes': ['deporte', 'otros'],
            'plusvalia': ['abastecimiento', 'transporte'],
            'rentabilidad': ['abastecimiento', 'transporte'],
            'ubicacion_estrategica': ['transporte', 'abastecimiento'],
            'inversion_segura': ['salud', 'transporte'],
            'prestigio': ['educacion', 'salud'],
            'calidad_construccion': ['otros'],
            'tranquilidad': ['deporte'],
            'colegios_cercanos': ['educacion'],
            'espacio': ['deporte']
        }

        categorias = set()
        for necesidad in necesidades:
            necesidad_lower = necesidad.lower()
            if necesidad_lower in mapeo:
                categorias.update(mapeo[necesidad_lower])

        return list(categorias) if categorias else ['educacion', 'salud', 'transporte']

    def calcular_compatibilidad(self, perfil: Dict[str, Any], propiedad: Dict[str, Any]) -> float:
        """
        Calcula el porcentaje de compatibilidad usando georreferenciación real.
        """
        inicio_tiempo = time.time()
        self.stats['calculos_realizados'] += 1

        # Verificar cache primero
        cache_key = self._generar_cache_key(perfil, propiedad, 'compatibilidad')
        with self._cache_lock:
            if cache_key in self._cache_compatibility:
                self.stats['cache_hits'] += 1
                self.stats['tiempo_total'] += time.time() - inicio_tiempo
                return self._cache_compatibility[cache_key]

        puntuaciones = {}

        # 1. Evaluación de presupuesto (25%)
        presupuesto = perfil.get('presupuesto', {})
        if presupuesto:
            presupuesto_min = presupuesto.get('min', 0)
            presupuesto_max = presupuesto.get('max', float('inf'))
            precio_propiedad = propiedad.get('caracteristicas_principales', {}).get('precio', 0)
            puntuaciones['presupuesto'] = self._evaluar_presupuesto_cercania(
                presupuesto_min, presupuesto_max, precio_propiedad
            )
        else:
            puntuaciones['presupuesto'] = 0.0

        # 2. Evaluación de composición familiar (20%)
        puntuaciones['composicion_familiar'] = self._evaluar_composicion_familiar(perfil, propiedad)

        # 3. Evaluación de servicios cercanos con georreferenciación real (30%)
        puntuaciones['servicios_cercanos'] = self._evaluar_servicios_georreferenciados(perfil, propiedad)

        # 4. Evaluación demográfica (15%)
        puntuaciones['demografia'] = self._evaluar_demografia(perfil, propiedad)

        # 5. Evaluación de preferencias (10%)
        puntuaciones['preferencias'] = self._evaluar_preferencias(perfil, propiedad)

        # Cálculo final con ponderación
        compatibilidad = sum(puntuaciones[area] * peso for area, peso in self.pesos.items())
        resultado = round(compatibilidad * 100, 1)  # Convertir a porcentaje

        # Guardar en cache
        with self._cache_lock:
            self._cache_compatibility[cache_key] = resultado

        self.stats['tiempo_total'] += time.time() - inicio_tiempo
        return resultado

    def _evaluar_presupuesto_cercania(self, presupuesto_min: int, presupuesto_max: int, precio_propiedad: int) -> float:
        """Evalúa adecuación presupuestaria con lógica mejorada."""
        if presupuesto_min <= precio_propiedad <= presupuesto_max:
            return 1.0
        elif precio_propiedad < presupuesto_min:
            # Si está por debajo, calcular qué tan cerca está del mínimo
            margen = presupuesto_max - presupuesto_min
            diferencia = presupuesto_min - precio_propiedad
            return max(0.3, 1.0 - (diferencia / margen))
        else:
            # Si está por encima, penalizar proporcionalmente
            exceso = precio_propiedad - presupuesto_max
            margen = presupuesto_max - presupuesto_min
            penalizacion = max(0.1, 1.0 - (exceso / margen))
            return max(0.1, penalizacion)

    def _evaluar_servicios_georreferenciados(self, perfil: Dict[str, Any], propiedad: Dict[str, Any]) -> float:
        """
        Evalúa servicios cercanos usando georreferenciación real.
        Esta es la función principal que reemplaza la evaluación por suposiciones.
        """
        if not self.guias_urbanas:
            return 0.5  # Valor neutro si no hay guía urbana cargada

        necesidades = perfil.get('necesidades', [])
        if not necesidades:
            return 0.6  # Valor por defecto si no hay necesidades específicas

        # Mapear necesidades a categorías de la guía urbana
        categorias_busqueda = self._mapear_necesidades_a_categorias(necesidades)

        # Obtener coordenadas de la propiedad
        propiedad_coords = propiedad.get('ubicacion', {}).get('coordenadas', {})
        if not propiedad_coords:
            return 0.3

        # Buscar servicios en diferentes radios
        radios_busqueda = [1.0, 2.0, 3.0, 5.0]  # km
        puntuacion_servicios = 0.0
        total_servicios_encontrados = 0

        for radio in radios_busqueda:
            servicios_cercanos = self._encontrar_servicios_cercanos(
                propiedad_coords, categorias_busqueda, radio
            )

            if servicios_cercanos:
                total_servicios_encontrados += len(servicios_cercanos)

                # Calcular puntuación para este radio
                # Servicios más cercanos valen más
                peso_radio = 1.0 / radio  # Radio más pequeño = mayor peso
                servicios_categoria = {}

                for servicio in servicios_cercanos:
                    categoria = servicio['categoria']
                    if categoria not in servicios_categoria:
                        servicios_categoria[categoria] = []
                    servicios_categoria[categoria].append(servicio)

                # Bonificar por diversidad de categorías
                diversidad = len(servicios_categoria) / max(1, len(categorias_busqueda))
                cantidad_servicios = len(servicios_cercanos)

                puntuacion_radio = (diversidad * 0.5 + min(cantidad_servicios / 5, 1.0) * 0.5) * peso_radio
                puntuacion_servicios = max(puntuacion_servicios, puntuacion_radio)

        # Normalizar puntuación
        if total_servicios_encontrados == 0:
            return 0.1  # Muy bajo si no hay servicios cercanos
        elif total_servicios_encontrados <= 3:
            return min(0.6, puntuacion_servicios)
        elif total_servicios_encontrados <= 8:
            return min(0.8, puntuacion_servicios)
        else:
            return min(1.0, puntuacion_servicios)

    def _evaluar_composicion_familiar(self, perfil: Dict[str, Any], propiedad: Dict[str, Any]) -> float:
        """Evalúa si la propiedad se adecua a la composición familiar."""
        composicion = perfil.get('composicion_familiar', {})
        caracteristicas = propiedad.get('caracteristicas_principales', {})
        detalles = propiedad.get('detalles_construccion', {})
        condominio = propiedad.get('condominio', {})

        total_personas = composicion.get('adultos', 0) + len(composicion.get('ninos', [])) + composicion.get('adultos_mayores', 0)
        habitaciones = caracteristicas.get('habitaciones', 0)
        dormitorios = caracteristicas.get('dormitorios', 0)
        banos_completos = caracteristicas.get('banos_completos', 0)
        superficie = caracteristicas.get('superficie_m2', 0)
        cochera_garaje = caracteristicas.get('cochera_garaje', False)

        if total_personas == 0:
            return 0.0

        puntuacion = 0.0

        # 1. Evaluación de habitaciones (40% del peso)
        if habitaciones > 0:
            if composicion.get('ninos'):
                habitaciones_necesarias = max(2, (total_personas + 1) // 2)
            else:
                habitaciones_necesarias = max(1, (total_personas + 1) // 2)

            if habitaciones >= habitaciones_necesarias:
                puntuacion += 0.4
            else:
                puntuacion += max(0.1, (habitaciones / habitaciones_necesarias) * 0.4)

        # 2. Evaluación de baños (25% del peso)
        banos_totales = banos_completos
        banos_necesarios = max(1, total_personas / 3)

        if banos_totales >= banos_necesarios:
            puntuacion += 0.25
        else:
            puntuacion += max(0.05, (banos_totales / banos_necesarios) * 0.25)

        # 3. Evaluación de superficie (20% del peso)
        if superficie > 0:
            superficie_minima = total_personas * 25  # 25m² por persona
            if superficie >= superficie_minima:
                puntuacion += 0.2
            else:
                puntuacion += max(0.05, (superficie / superficie_minima) * 0.2)

        # 4. Evaluación de garaje (10% del peso)
        if cochera_garaje:
            puntuacion += 0.1

        # 5. Evaluación de amenities de condominio (5% del peso)
        if condominio.get('es_condominio_cerrado', False):
            amenities = condominio.get('amenidades', [])
            if len(amenities) >= 3:
                puntuacion += 0.05
            elif len(amenities) >= 1:
                puntuacion += 0.03

        return min(1.0, puntuacion)

    def _evaluar_demografia(self, perfil: Dict[str, Any], propiedad: Dict[str, Any]) -> float:
        """Evalúa factores demográficos y de sector."""
        composicion = perfil.get('composicion_familiar', {})
        valorizacion = propiedad.get('valorizacion_sector', {})
        ubicacion = propiedad.get('ubicacion', {})

        puntuacion = 0.0
        total_personas = composicion.get('adultos', 0) + len(composicion.get('ninos', [])) + composicion.get('adultos_mayores', 0)

        # 1. Seguridad del sector (40%)
        seguridad_zona = valorizacion.get('seguridad_zona', '').lower()
        if seguridad_zona == 'alta':
            puntuacion += 0.4
        elif seguridad_zona == 'media':
            puntuacion += 0.25
        elif seguridad_zona == 'baja':
            puntuacion += 0.1

        # 2. Demanda del sector (30%)
        demanda_sector = valorizacion.get('demanda_sector', '').lower()
        if demanda_sector in ['muy_alta', 'alta']:
            puntuacion += 0.3
        elif demanda_sector == 'media':
            puntuacion += 0.15

        # 3. Plusvalía (20%)
        plusvalia = valorizacion.get('plusvalia_tendencia', '').lower()
        if plusvalia == 'creciente':
            puntuacion += 0.2
        elif plusvalia == 'estable':
            puntuacion += 0.1

        # 4. Nivel socioeconómico (10%)
        nivel_socioeconomico = valorizacion.get('nivel_socioeconomico', '').lower()
        if nivel_socioeconomico in ['alto', 'medio_alto']:
            puntuacion += 0.1
        elif nivel_socioeconomico == 'medio':
            puntuacion += 0.05

        return min(1.0, puntuacion)

    def _evaluar_preferencias(self, perfil: Dict[str, Any], propiedad: Dict[str, Any]) -> float:
        """Evalúa las preferencias de ubicación y estilo de vida."""
        preferencias = perfil.get('preferencias', {})
        ubicacion = propiedad.get('ubicacion', {})
        caracteristicas = propiedad.get('caracteristicas_principales', {})
        detalles = propiedad.get('detalles_construccion', {})
        condominio = propiedad.get('condominio', {})
        valorizacion = propiedad.get('valorizacion_sector', {})

        puntuacion = 0.0

        # 1. Preferencia de ubicación (0.35 puntos)
        if 'ubicacion' in preferencias and preferencias['ubicacion']:
            ubicacion_preferida = preferencias['ubicacion'].lower()
            zona_actual = ubicacion.get('zona', '').lower() if ubicacion.get('zona') else ''

            if ubicacion_preferida in zona_actual:
                puntuacion += 0.35
            elif 'norte' in ubicacion_preferida and 'norte' in zona_actual:
                puntuacion += 0.25
            elif 'centro' in ubicacion_preferida and 'centro' in zona_actual:
                puntuacion += 0.25
            elif any(zona in ubicacion_preferida for zona in ['equipetrol', 'las palmas', 'urubó']):
                if any(zona in zona_actual for zona in ['equipetrol', 'las palmas', 'urubó']):
                    puntuacion += 0.2

        # 2. Preferencia de tipo de propiedad (0.25 puntos)
        if 'tipo_propiedad' in preferencias and preferencias['tipo_propiedad']:
            tipo_preferido = preferencias['tipo_propiedad'].lower()
            tipo_actual = propiedad.get('tipo', '').lower()

            if tipo_preferido in tipo_actual:
                puntuacion += 0.25

        # 3. Características deseadas (0.20 puntos)
        if 'caracteristicas_deseadas' in preferencias:
            caracteristicas_deseadas = preferencias['caracteristicas_deseadas']
            caracteristicas_disponibles = []

            if detalles.get('aire_acondicionado', False):
                caracteristicas_disponibles.append('aire_acondicionado')
            if detalles.get('balcon', False):
                caracteristicas_disponibles.append('balcon')
            if detalles.get('terraza', False):
                caracteristicas_disponibles.append('terraza')
            if caracteristicas.get('superficie_m2', 0) >= 100:
                caracteristicas_disponibles.append('espacioso')
            if condominio.get('es_condominio_cerrado', False):
                caracteristicas_disponibles.append('condominio_cerrado')

            coincidencias = sum(1 for deseada in caracteristicas_deseadas if deseada in caracteristicas_disponibles)
            if caracteristicas_deseadas:
                puntuacion += (coincidencias / len(caracteristicas_deseadas)) * 0.2

        # 4. Seguridad (0.15 puntos)
        if 'seguridad' in preferencias and preferencias['seguridad']:
            seguridad_preferida = preferencias['seguridad'].lower()
            seguridad_real = valorizacion.get('seguridad_zona', '').lower() if valorizacion.get('seguridad_zona') else ''
            condominio_seguro = condominio.get('seguridad_24h', False)

            if seguridad_preferida == 'alta' and (seguridad_real == 'alta' or condominio_seguro):
                puntuacion += 0.15
            elif seguridad_preferida == 'media' and seguridad_real in ['media', 'alta']:
                puntuacion += 0.08

        # 5. Nivel socioeconómico (0.05 puntos)
        if 'nivel_socioeconomico' in preferencias and preferencias['nivel_socioeconomico']:
            nivel_preferido = preferencias['nivel_socioeconomico'].lower()
            nivel_real = valorizacion.get('nivel_socioeconomico', '').lower() if valorizacion.get('nivel_socioeconomico') else ''

            if nivel_preferido in nivel_real:
                puntuacion += 0.05

        return min(1.0, puntuacion)

    def generar_recomendaciones(self, perfil: Dict[str, Any], limite: int = 5,
                            umbral_minimo: float = 0.1) -> List[Dict[str, Any]]:
        """Genera recomendaciones usando el motor mejorado."""
        if not self.propiedades:
            return []

        # Optimización: Pre-filtrar propiedades por zona preferida
        zona_preferida = perfil.get('preferencias', {}).get('ubicacion', '').lower()
        propiedades_a_evaluar = self.propiedades

        if zona_preferida and zona_preferida != '':
            # Buscar propiedades que coincidan con la zona preferida
            propiedades_filtradas = []
            for prop in self.propiedades:
                zona_prop = prop.get('ubicacion', {}).get('zona', '').lower()
                if zona_preferida in zona_prop or zona_prop in zona_preferida:
                    propiedades_filtradas.append(prop)

            # Si encontramos propiedades en la zona preferida, usarlas
            if propiedades_filtradas:
                propiedades_a_evaluar = propiedades_filtradas
                print(f"Evaluando {len(propiedades_a_evaluar)} propiedades en zona '{zona_preferida}'")
            else:
                print(f"No se encontraron propiedades en '{zona_preferida}', evaluando todas {len(self.propiedades)}")

        # Calcular compatibilidad para cada propiedad
        recomendaciones = []
        for propiedad in propiedades_a_evaluar:
            compatibilidad = self.calcular_compatibilidad(perfil, propiedad)

            if compatibilidad >= (umbral_minimo * 100):  # Convertir umbral a porcentaje
                # Generar justificación mejorada
                justificacion = self._generar_justificacion_mejorada(perfil, propiedad, compatibilidad)

                recomendaciones.append({
                    'propiedad': propiedad,
                    'compatibilidad': compatibilidad,
                    'justificacion': justificacion,
                    'servicios_cercanos': self._obtener_resumen_servicios_cercanos(perfil, propiedad)
                })

        # Ordenar por compatibilidad y limitar resultados
        recomendaciones.sort(key=lambda x: x['compatibilidad'], reverse=True)
        return recomendaciones[:limite]

    def _generar_justificacion_mejorada(self, perfil: Dict[str, Any], propiedad: Dict[str, Any], compatibilidad: float) -> str:
        """Genera justificación detallada basada en análisis real."""
        caracteristicas = propiedad.get('caracteristicas_principales', {})
        ubicacion = propiedad.get('ubicacion', {})
        valorizacion = propiedad.get('valorizacion_sector', {})

        presupuesto = perfil.get('presupuesto', {})
        presupuesto_min = presupuesto.get('min', 0)
        presupuesto_max = presupuesto.get('max', float('inf'))
        precio = caracteristicas.get('precio', 0)

        justificacion = []

        # Presupuesto
        if presupuesto_min <= precio <= presupuesto_max:
            justificacion.append(f"Precio de ${precio:,} está dentro del presupuesto (${presupuesto_max:,}).")
        elif precio < presupuesto_min:
            justificacion.append(f"Precio de ${precio:,} está por debajo del presupuesto mínimo (${presupuesto_min:,}).")
        else:
            justificacion.append(f"Precio de ${precio:,} excede el presupuesto máximo (${presupuesto_max:,}).")

        # Ubicación y valorización
        zona = ubicacion.get('zona', 'No especificada')
        seguridad = valorizacion.get('seguridad_zona', 'No especificada')
        demanda = valorizacion.get('demanda_sector', 'No especificada')

        justificacion.append(f"Ubicada en zona {zona.lower()} con seguridad {seguridad.lower()} y demanda {demanda.lower()}.")

        # Servicios cercanos (solo si tenemos guía urbana)
        if self.guias_urbanas:
            servicios_resumen = self._obtener_resumen_servicios_cercanos(perfil, propiedad)
            if servicios_resumen:
                justificacion.append(f"Cuenta con {servicios_resumen} en áreas cercanas.")

        # Características principales
        habitaciones = caracteristicas.get('habitaciones', 0)
        banos = caracteristicas.get('banos_completos', 0)
        superficie = caracteristicas.get('superficie_m2', 0)

        justificacion.append(f"Ofrece {habitaciones} habitaciones, {banos} baños y {superficie}m² de superficie.")

        return " ".join(justificacion)

    def _obtener_resumen_servicios_cercanos(self, perfil: Dict[str, Any], propiedad: Dict[str, Any]) -> str:
        """Obtiene un resumen de servicios cercanos para la justificación."""
        if not self.guias_urbanas:
            return ""

        necesidades = perfil.get('necesidades', [])
        if not necesidades:
            return ""

        categorias_busqueda = self._mapear_necesidades_a_categorias(necesidades)
        propiedad_coords = propiedad.get('ubicacion', {}).get('coordenadas', {})

        if not propiedad_coords:
            return ""

        servicios_cercanos = self._encontrar_servicios_cercanos(propiedad_coords, categorias_busqueda, 2.0)

        if not servicios_cercanos:
            return ""

        # Agrupar por categoría
        servicios_por_categoria = {}
        for servicio in servicios_cercanos:
            categoria = servicio['categoria']
            if categoria not in servicios_por_categoria:
                servicios_por_categoria[categoria] = []
            servicios_por_categoria[categoria].append(servicio)

        # Generar resumen
        resumen = []
        for categoria, servicios in servicios_por_categoria.items():
            count = len(servicios)
            distancia_promedio = sum(s['distancia_km'] for s in servicios) / count
            resumen.append(f"{count} servicios de {categoria} a {distancia_promedio:.1f}km en promedio")

        return ", ".join(resumen)

    def obtener_estadisticas_rendimiento(self) -> Dict[str, Any]:
        """Retorna estadísticas de rendimiento del motor."""
        cache_efficiency = (self.stats['cache_hits'] / max(1, self.stats['calculos_realizados'])) * 100

        return {
            'calculos_realizados': self.stats['calculos_realizados'],
            'cache_hits': self.stats['cache_hits'],
            'cache_efficiency': round(cache_efficiency, 2),
            'tiempo_total': round(self.stats['tiempo_total'], 3),
            'tiempo_promedio': round(self.stats['tiempo_total'] / max(1, self.stats['calculos_realizados']), 6),
            'distancias_calculadas': self.stats['distancias_calculadas'],
            'servicios_indexados': len(self.guias_urbanas),
            'categorias_disponibles': list(self.indice_servicios_espaciales.keys())
        }