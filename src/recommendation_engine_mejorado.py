"""
Motor de recomendación especializado para inversores inmobiliarios
Implementa análisis de oportunidades de inversión con georreferenciación real
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
    """Motor de recomendación especializado para inversores con georreferenciación real."""

    def __init__(self):
        self.propiedades = []
        self.guias_urbanas = []
        self.indice_servicios_espaciales = {}
        self.pesos = {
            'ubicacion': 0.35,      # Proximidad y zona
            'precio': 0.25,         # Rango de precio
            'servicios': 0.20,      # Servicios que impactan valor
            'caracteristicas': 0.15, # Características del inmueble
            'disponibilidad': 0.05   # Disponibilidad en relevamiento
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
        Calcula el porcentaje de compatibilidad para inversores usando georreferenciación real.
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

        # 1. Evaluación de ubicación (35%)
        puntuaciones['ubicacion'] = self._evaluar_ubicacion_inversion(perfil, propiedad)

        # 2. Evaluación de precio/rentabilidad (25%)
        puntuaciones['precio'] = self._evaluar_precio_inversion(perfil, propiedad)

        # 3. Evaluación de servicios que impactan valor (20%)
        puntuaciones['servicios'] = self._evaluar_servicios_inversion(perfil, propiedad)

        # 4. Evaluación de características del inmueble (15%)
        puntuaciones['caracteristicas'] = self._evaluar_caracteristicas_inversion(perfil, propiedad)

        # 5. Evaluación de disponibilidad (5%)
        puntuaciones['disponibilidad'] = self._evaluar_disponibilidad(perfil, propiedad)

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
        """Genera recomendaciones usando el motor mejorado con filtros UV/MZ."""
        if not self.propiedades:
            return []

        # Pre-filtrar propiedades con filtros avanzados
        propiedades_filtradas = self._filtrar_propiedades_avanzado(perfil)

        # Calcular compatibilidad para cada propiedad
        recomendaciones = []
        for propiedad in propiedades_filtradas:
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

    def _filtrar_propiedades_avanzado(self, perfil: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filtra propiedades usando criterios avanzados incluyendo UV/MZ."""
        preferencias = perfil.get('preferencias', {})
        presupuesto = perfil.get('presupuesto', {})

        propiedades_filtradas = self.propiedades

        # 1. Filtro por zona preferida
        zona_preferida = preferencias.get('ubicacion', '').lower()
        if zona_preferida and zona_preferida.strip():
            propiedades_zona = []
            for prop in propiedades_filtradas:
                zona_prop = prop.get('ubicacion', {}).get('zona', '').lower()
                if zona_preferida in zona_prop or zona_prop in zona_preferida:
                    propiedades_zona.append(prop)

            if propiedades_zona:
                propiedades_filtradas = propiedades_zona
                print(f"Filtrado por zona '{zona_preferida}': {len(propiedades_filtradas)} propiedades")

        # 2. Filtro por Unidad Vecinal (UV)
        uv_preferida = preferencias.get('unidad_vecinal', '').strip()
        if uv_preferida:
            propiedades_uv = []
            for prop in propiedades_filtradas:
                uv_prop = str(prop.get('unidad_vecinal', '')).strip().lower()
                if uv_preferida.lower() in uv_prop:
                    propiedades_uv.append(prop)

            if propiedades_uv:
                propiedades_filtradas = propiedades_uv
                print(f"Filtrado por UV '{uv_preferida}': {len(propiedades_filtradas)} propiedades")

        # 3. Filtro por Manzana (MZ)
        mz_preferida = preferencias.get('manzana', '').strip()
        if mz_preferida:
            propiedades_mz = []
            for prop in propiedades_filtradas:
                mz_prop = str(prop.get('manzana', '')).strip().lower()
                if mz_preferida.lower() in mz_prop:
                    propiedades_mz.append(prop)

            if propiedades_mz:
                propiedades_filtradas = propiedades_mz
                print(f"Filtrado por Manzana '{mz_preferida}': {len(propiedades_filtradas)} propiedades")

        # 4. Filtro por tipo de propiedad
        tipo_preferido = preferencias.get('tipo_propiedad', '').strip().lower()
        if tipo_preferido:
            propiedades_tipo = []
            for prop in propiedades_filtradas:
                tipo_prop = str(prop.get('tipo', '')).strip().lower()
                if tipo_preferido in tipo_prop:
                    propiedades_tipo.append(prop)

            if propiedades_tipo:
                propiedades_filtradas = propiedades_tipo
                print(f"Filtrado por tipo '{tipo_preferido}': {len(propiedades_filtradas)} propiedades")

        # 5. Filtro por rango de precio
        presupuesto_min = presupuesto.get('min', 0)
        presupuesto_max = presupuesto.get('max', float('inf'))
        if presupuesto_min > 0 or presupuesto_max < float('inf'):
            propiedades_precio = []
            for prop in propiedades_filtradas:
                precio = prop.get('caracteristicas_principales', {}).get('precio', 0)
                if presupuesto_min <= precio <= presupuesto_max:
                    propiedades_precio.append(prop)

            if propiedades_precio:
                propiedades_filtradas = propiedades_precio
                print(f"Filtrado por precio ${presupuesto_min:,}-${presupuesto_max:,}: {len(propiedades_filtradas)} propiedades")

        # 5b. Filtro por moneda (USD/BOB) - Nuevo filtro para economía bimonetaria
        moneda_preferida = presupuesto.get('moneda', '')
        if moneda_preferida:
            propiedades_moneda = []
            for prop in propiedades_filtradas:
                moneda_prop = prop.get('caracteristicas_principales', {}).get('moneda', 'USD')
                if moneda_prop == moneda_preferida:
                    propiedades_moneda.append(prop)

            if propiedades_moneda:
                propiedades_filtradas = propiedades_moneda
                print(f"Filtrado por moneda {moneda_preferida}: {len(propiedades_filtradas)} propiedades")
            else:
                print(f"ADVERTENCIA: No hay propiedades en {moneda_preferida}, mostrando todas las monedas")

        # 6. Filtro por disponibilidad reciente
        dias_maximos = preferencias.get('disponibilidad_dias', 90)  # Por defecto 90 días
        if dias_maximos > 0:
            propiedades_recientes = []
            for prop in propiedades_filtradas:
                fecha_rel = prop.get('fecha_relevamiento', '')
                if fecha_rel:
                    try:
                        from datetime import datetime
                        fecha_dt = datetime.strptime(fecha_rel, '%Y.%m.%d')
                        dias_desde = (datetime.now() - fecha_dt).days
                        if dias_desde <= dias_maximos:
                            propiedades_recientes.append(prop)
                    except:
                        pass  # Si no puede parsear la fecha, incluir la propiedad

            if propiedades_recientes:
                propiedades_filtradas = propiedades_recientes
                print(f"Filtrado por disponibilidad reciente ({dias_maximos} días): {len(propiedades_filtradas)} propiedades")

        print(f"Total propiedades después de filtros: {len(propiedades_filtradas)}")
        return propiedades_filtradas

    def buscar_por_filtros(self, filtros: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Busca propiedades usando filtros específicos sin perfil de inversor.
        Útil para búsquedas directas por UV, Manzana, zona, etc.
        """
        propiedades_filtradas = self.propiedades

        # Filtro por UV
        if 'unidad_vecinal' in filtros and filtros['unidad_vecinal']:
            uv = filtros['unidad_vecinal'].strip().lower()
            propiedades_filtradas = [
                prop for prop in propiedades_filtradas
                if uv in str(prop.get('unidad_vecinal', '')).lower()
            ]

        # Filtro por Manzana
        if 'manzana' in filtros and filtros['manzana']:
            mz = filtros['manzana'].strip().lower()
            propiedades_filtradas = [
                prop for prop in propiedades_filtradas
                if mz in str(prop.get('manzana', '')).lower()
            ]

        # Filtro por zona
        if 'zona' in filtros and filtros['zona']:
            zona = filtros['zona'].strip().lower()
            propiedades_filtradas = [
                prop for prop in propiedades_filtradas
                if zona in prop.get('ubicacion', {}).get('zona', '').lower()
            ]

        # Filtro por tipo
        if 'tipo_propiedad' in filtros and filtros['tipo_propiedad']:
            tipo = filtros['tipo_propiedad'].strip().lower()
            propiedades_filtradas = [
                prop for prop in propiedades_filtradas
                if tipo in str(prop.get('tipo', '')).lower()
            ]

        # Filtro por precio
        if 'precio_min' in filtros or 'precio_max' in filtros:
            precio_min = filtros.get('precio_min', 0)
            precio_max = filtros.get('precio_max', float('inf'))
            propiedades_filtradas = [
                prop for prop in propiedades_filtradas
                if precio_min <= prop.get('caracteristicas_principales', {}).get('precio', 0) <= precio_max
            ]

        return propiedades_filtradas

    def _generar_justificacion_mejorada(self, perfil: Dict[str, Any], propiedad: Dict[str, Any], compatibilidad: float) -> str:
        """Genera justificación detallada para inversores basada en análisis real."""
        caracteristicas = propiedad.get('caracteristicas_principales', {})
        ubicacion = propiedad.get('ubicacion', {})
        valorizacion = propiedad.get('valorizacion_sector', {})

        presupuesto = perfil.get('presupuesto', {})
        presupuesto_min = presupuesto.get('min', 0)
        presupuesto_max = presupuesto.get('max', float('inf'))
        precio = caracteristicas.get('precio', 0)

        justificacion = []

        # Precio y oportunidad de inversión
        if presupuesto_min <= precio <= presupuesto_max:
            justificacion.append(f"Inversión de ${precio:,} se ajusta al rango presupuestado.")
        elif precio < presupuesto_min:
            justificacion.append(f"Oportunidad por debajo del presupuesto: ${precio:,} vs mínimo ${presupuesto_min:,}.")
        else:
            justificacion.append(f"Inversión de ${precio:,} excede rango máximo de ${presupuesto_max:,}.")

        # Potencial de la zona
        zona = ubicacion.get('zona', 'No especificada')
        demanda = valorizacion.get('demanda_sector', 'No especificada')

        if demanda in ['muy_alta', 'alta']:
            justificacion.append(f"Zona {zona.lower()} con alta demanda y buen potencial.")
        elif demanda == 'media':
            justificacion.append(f"Zona {zona.lower()} con demanda moderada, oportunidades de negociación.")
        else:
            justificacion.append(f"Zona {zona.lower()} en desarrollo.")

        # UV y Manzana si están disponibles
        uv = propiedad.get('unidad_vecinal', '')
        mz = propiedad.get('manzana', '')
        if uv:
            justificacion.append(f"Ubicada en UV {uv}")
            if mz:
                justificacion.append(f", manzana {mz}.")

        # Servicios que impactan el valor
        if self.guias_urbanas:
            servicios_resumen = self._obtener_resumen_servicios_cercanos(perfil, propiedad)
            if servicios_resumen:
                justificacion.append(f"Buen acceso a {servicios_resumen}.")

        # Características atractivas para inversión
        superficie = caracteristicas.get('superficie_m2', 0)
        habitaciones = caracteristicas.get('habitaciones', 0)
        tipo = propiedad.get('tipo', '')

        if superficie >= 100:
            justificacion.append(f"Amplia superficie de {superficie}m².")
        if habitaciones >= 3:
            justificacion.append(f"{habitaciones} habitaciones.")

        # Disponibilidad
        fecha_rel = propiedad.get('fecha_relevamiento', '')
        if fecha_rel:
            justificacion.append(f"Datos actualizados al {fecha_rel}.")

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

    def _evaluar_ubicacion_inversion(self, perfil: Dict[str, Any], propiedad: Dict[str, Any]) -> float:
        """Evalúa la ubicación desde perspectiva de inversión."""
        ubicacion = propiedad.get('ubicacion', {})
        valorizacion = propiedad.get('valorizacion_sector', {})
        preferencias = perfil.get('preferencias', {})

        puntuacion = 0.0
        zona = ubicacion.get('zona', '').lower()

        # 1. Coincidia con zona preferida (40%)
        zona_preferida = preferencias.get('ubicacion', '').lower()
        if zona_preferida and zona_preferida in zona:
            puntuacion += 0.4
        elif zona_preferida:
            # Búsqueda parcial de coincidencia
            if any(palabra in zona for palabra in zona_preferida.split()):
                puntuacion += 0.25

        # 2. Potencial de desarrollo (30%)
        demanda = valorizacion.get('demanda_sector', '').lower()
        if demanda in ['muy_alta', 'alta']:
            puntuacion += 0.3
        elif demanda == 'media':
            puntuacion += 0.15

        # 3. Filtros UV/Manzana (20%)
        uv_preferida = preferencias.get('unidad_vecinal', '').lower()
        mz_preferida = preferencias.get('manzana', '').lower()

        if propiedad.get('unidad_vecinal') and uv_preferida:
            if uv_preferida in str(propiedad.get('unidad_vecinal', '')).lower():
                puntuacion += 0.2

        if propiedad.get('manzana') and mz_preferida:
            if mz_preferida in str(propiedad.get('manzana', '')).lower():
                puntuacion += 0.1

        # 4. Accesibilidad y conectividad (10%)
        if self.guias_urbanas:
            coords = ubicacion.get('coordenadas', {})
            if coords:
                servicios_transporte = self._encontrar_servicios_cercanos(
                    coords, ['transporte'], 2.0
                )
                if len(servicios_transporte) >= 3:
                    puntuacion += 0.1
                elif len(servicios_transporte) >= 1:
                    puntuacion += 0.05

        return min(1.0, puntuacion)

    def _evaluar_precio_inversion(self, perfil: Dict[str, Any], propiedad: Dict[str, Any]) -> float:
        """Evalúa el precio desde perspectiva de inversión."""
        presupuesto = perfil.get('presupuesto', {})
        caracteristicas = propiedad.get('caracteristicas_principales', {})

        presupuesto_min = presupuesto.get('min', 0)
        presupuesto_max = presupuesto.get('max', float('inf'))
        precio = caracteristicas.get('precio', 0)

        if not precio:
            return 0.0

        # 1. Adecuación al rango de inversión (70%)
        if presupuesto_min <= precio <= presupuesto_max:
            puntuacion_precio = 0.7
        elif precio < presupuesto_min:
            # Por debajo del mínimo - podría ser buena oportunidad
            margen = presupuesto_max - presupuesto_min
            diferencia = presupuesto_min - precio
            puntuacion_precio = 0.7 - (diferencia / margen) * 0.3
            puntuacion_precio = max(0.2, puntuacion_precio)
        else:
            # Por encima del máximo
            exceso = precio - presupuesto_max
            margen = presupuesto_max - presupuesto_min
            penalizacion = 0.7 - (exceso / margen) * 0.5
            puntuacion_precio = max(0.1, penalizacion)

        # 2. Potencial de negociación (30%)
        valorizacion = propiedad.get('valorizacion_sector', {})
        demanda = valorizacion.get('demanda_sector', '').lower()

        if demanda == 'media':
            puntuacion_precio += 0.2  # Mayor potencial de negociación
        elif demanda == 'baja':
            puntuacion_precio += 0.3
        elif demanda in ['alta', 'muy_alta']:
            puntuacion_precio += 0.05  # Menor potencial de negociación

        return min(1.0, puntuacion_precio)

    def _evaluar_servicios_inversion(self, perfil: Dict[str, Any], propiedad: Dict[str, Any]) -> float:
        """Evalúa servicios que impactan el valor de inversión."""
        if not self.guias_urbanas:
            return 0.5  # Valor neutro

        ubicacion = propiedad.get('ubicacion', {})
        coords = ubicacion.get('coordenadas', {})

        if not coords:
            return 0.3

        # Servicios que impactan más el valor de inversión
        servicios_valor = ['transporte', 'abastecimiento', 'educacion', 'salud']
        puntuacion = 0.0

        # Buscar servicios en diferentes radios
        for radio in [1.0, 2.0, 3.0]:
            servicios_cercanos = self._encontrar_servicios_cercanos(
                coords, servicios_valor, radio
            )

            if servicios_cercanos:
                # Categorizar servicios
                servicios_por_categoria = {}
                for servicio in servicios_cercanos:
                    categoria = servicio['categoria']
                    if categoria not in servicios_por_categoria:
                        servicios_por_categoria[categoria] = []
                    servicios_por_categoria[categoria].append(servicio)

                # Evaluar diversidad y cantidad
                diversidad = len(servicios_por_categoria) / len(servicios_valor)
                cantidad = len(servicios_cercanos)

                # Ponderar por radio (más cercano = más valor)
                peso_radio = 1.0 / radio
                puntuacion_radio = (diversidad * 0.6 + min(cantidad / 10, 1.0) * 0.4) * peso_radio
                puntuacion = max(puntuacion, puntuacion_radio)

        return min(1.0, puntuacion)

    def _evaluar_caracteristicas_inversion(self, perfil: Dict[str, Any], propiedad: Dict[str, Any]) -> float:
        """Evalúa características del inmueble para inversión."""
        caracteristicas = propiedad.get('caracteristicas_principales', {})
        preferencias = perfil.get('preferencias', {})

        puntuacion = 0.0

        # 1. Tipo de propiedad preferido (40%)
        tipo_preferido = preferencias.get('tipo_propiedad', '').lower()
        tipo_actual = propiedad.get('tipo', '').lower()

        if tipo_preferido and tipo_preferido in tipo_actual:
            puntuacion += 0.4
        elif tipo_preferido:
            # Coincidencias parciales
            if tipo_preferido == 'departamento' and 'departamento' in tipo_actual:
                puntuacion += 0.4
            elif tipo_preferido == 'casa' and 'casa' in tipo_actual:
                puntuacion += 0.4
            elif tipo_preferido == 'terreno' and 'terreno' in tipo_actual:
                puntuacion += 0.4

        # 2. Superficie (30%)
        superficie = caracteristicas.get('superficie_m2', 0)
        if superficie >= 100:  # Superficie generosa
            puntuacion += 0.3
        elif superficie >= 60:
            puntuacion += 0.2
        elif superficie > 0:
            puntuacion += 0.1

        # 3. Características atractivas para inversión (30%)
        detalles = propiedad.get('detalles_construccion', {})
        condominio = propiedad.get('condominio', {})

        caracteristicas_inversion = 0
        if detalles.get('cochera_garaje', False):
            caracteristicas_inversion += 1
        if condominio.get('es_condominio_cerrado', False):
            caracteristicas_inversion += 1
        if detalles.get('amoblado', False):
            caracteristicas_inversion += 1
        if caracteristicas.get('habitaciones', 0) >= 3:
            caracteristicas_inversion += 1

        if caracteristicas_inversion >= 3:
            puntuacion += 0.3
        elif caracteristicas_inversion >= 2:
            puntuacion += 0.2
        elif caracteristicas_inversion >= 1:
            puntuacion += 0.1

        return min(1.0, puntuacion)

    def _evaluar_disponibilidad(self, perfil: Dict[str, Any], propiedad: Dict[str, Any]) -> float:
        """Evalúa disponibilidad y actualidad de la propiedad."""
        # 1. Fecha de relevamiento (60%)
        fecha_relevamiento = propiedad.get('fecha_relevamiento', '')
        if fecha_relevamiento:
            try:
                from datetime import datetime, timedelta
                fecha_dt = datetime.strptime(fecha_relevamiento, '%Y.%m.%d')
                dias_desde_relevamiento = (datetime.now() - fecha_dt).days

                if dias_desde_relevamiento <= 7:
                    puntuacion = 0.6  # Muy reciente
                elif dias_desde_relevamiento <= 30:
                    puntuacion = 0.4  # Reciente
                elif dias_desde_relevamiento <= 90:
                    puntuacion = 0.2  # Moderado
                else:
                    puntuacion = 0.1  # Antiguo
            except:
                puntuacion = 0.3
        else:
            puntuacion = 0.2

        # 2. Estado de disponibilidad (40%)
        estado = propiedad.get('estado', '').lower()
        if estado in ['disponible', 'en_venta', 'venta']:
            puntuacion += 0.4
        elif estado in ['reservado', 'en_negociacion']:
            puntuacion += 0.2
        else:
            puntuacion += 0.1

        return min(1.0, puntuacion)

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