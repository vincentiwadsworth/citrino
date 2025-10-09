"""
Motor de recomendación principal para el sistema inmobiliario.

Este módulo contiene la lógica para calcular compatibilidad entre
perfiles de prospectos y propiedades disponibles.
"""

from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
from functools import lru_cache
import time
import threading


class RecommendationEngine:
    """Motor de recomendación basado en matching de perfiles."""

    def __init__(self):
        self.propiedades = []
        self.pesos = {
            'presupuesto': 0.30,
            'composicion_familiar': 0.25,
            'servicios': 0.20,
            'demografia': 0.15,
            'preferencias': 0.10
        }
        # Cache para cálculos repetitivos
        self._cache_puntuaciones = {}
        self._cache_compatibility = {}
        self._cache_lock = threading.Lock()
        # Estadísticas de rendimiento
        self.stats = {
            'calculos_realizados': 0,
            'cache_hits': 0,
            'tiempo_total': 0.0
        }

    def cargar_propiedades(self, propiedades: List[Dict[str, Any]]):
        """Carga las propiedades disponibles en el motor."""
        self.propiedades = propiedades
        # Limpiar cache cuando se cargan nuevas propiedades
        self._limpiar_cache()

    def _limpiar_cache(self):
        """Limpia el cache de cálculos."""
        with self._cache_lock:
            self._cache_puntuaciones.clear()
            self._cache_compatibility.clear()

    def _generar_cache_key(self, perfil: Dict[str, Any], propiedad: Dict[str, Any], funcion: str) -> str:
        """Genera una clave única para el cache."""
        # Usar IDs o hashes para crear clave única
        perfil_id = str(hash(str(sorted(perfil.items()))))
        propiedad_id = propiedad.get('id', str(hash(str(sorted(propiedad.items())))))
        return f"{funcion}:{perfil_id}:{propiedad_id}"

    @lru_cache(maxsize=1000)
    def _evaluar_presupuesto_cache(self, presupuesto_min: int, presupuesto_max: int, precio_propiedad: int) -> float:
        """Versión cacheada de evaluación de presupuesto."""
        if presupuesto_min <= precio_propiedad <= presupuesto_max:
            return 1.0
        elif precio_propiedad < presupuesto_min:
            return 0.5
        else:
            exceso = precio_propiedad - presupuesto_max
            margen = presupuesto_max - presupuesto_min
            penalizacion = max(0, 1 - (exceso / margen))
            return max(0.2, penalizacion)

    def calcular_compatibilidad(self, perfil: Dict[str, Any], propiedad: Dict[str, Any]) -> float:
        """
        Calcula el porcentaje de compatibilidad entre un perfil y una propiedad.

        Args:
            perfil: Diccionario con información del prospecto
            propiedad: Diccionario con información de la propiedad

        Returns:
            Porcentaje de compatibilidad (0-100)
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

        # 1. Evaluación de presupuesto (30%) - optimizada con cache
        presupuesto = perfil.get('presupuesto', {})
        if presupuesto:
            presupuesto_min = presupuesto.get('min', 0)
            presupuesto_max = presupuesto.get('max', float('inf'))
            precio_propiedad = propiedad.get('caracteristicas_principales', {}).get('precio', 0)
            puntuaciones['presupuesto'] = self._evaluar_presupuesto_cache(
                presupuesto_min, presupuesto_max, precio_propiedad
            )
        else:
            puntuaciones['presupuesto'] = 0.0

        # 2. Evaluación de composición familiar (25%)
        puntuaciones['composicion_familiar'] = self._evaluar_composicion_familiar(perfil, propiedad)

        # 3. Evaluación de servicios cercanos (20%)
        puntuaciones['servicios'] = self._evaluar_servicios(perfil, propiedad)

        # 4. Evaluación demográfica (15%)
        puntuaciones['demografia'] = self._evaluar_demografia(perfil, propiedad)

        # 5. Evaluación de preferencias (10%)
        puntuaciones['preferencias'] = self._evaluar_preferencias(perfil, propiedad)

        # Cálculo final con ponderación
        compatibilidad = sum(puntuaciones[area] * peso for area, peso in self.pesos.items())
        resultado = round(compatibilidad, 2)

        # Guardar en cache
        with self._cache_lock:
            self._cache_compatibility[cache_key] = resultado

        self.stats['tiempo_total'] += time.time() - inicio_tiempo
        return resultado

    def _evaluar_presupuesto(self, perfil: Dict[str, Any], propiedad: Dict[str, Any]) -> float:
        """Evalúa si la propiedad está dentro del presupuesto del prospecto usando estructura mejorada."""
        presupuesto = perfil.get('presupuesto', {})
        caracteristicas = propiedad.get('caracteristicas_principales', {})
        precio_propiedad = caracteristicas.get('precio', 0)

        if not presupuesto or precio_propiedad == 0:
            return 0.0

        presupuesto_min = presupuesto.get('min', 0)
        presupuesto_max = presupuesto.get('max', float('inf'))

        # Usar la versión cacheada para mejor rendimiento
        return self._evaluar_presupuesto_cache(presupuesto_min, presupuesto_max, precio_propiedad)

    def _evaluar_composicion_familiar(self, perfil: Dict[str, Any], propiedad: Dict[str, Any]) -> float:
        """Evalúa si la propiedad se adecua a la composición familiar usando campos determinantes."""
        composicion = perfil.get('composicion_familiar', {})
        caracteristicas = propiedad.get('caracteristicas_principales', {})
        detalles = propiedad.get('detalles_construccion', {})
        condominio = propiedad.get('condominio', {})

        total_personas = composicion.get('adultos', 0) + len(composicion.get('ninos', [])) + composicion.get('adultos_mayores', 0)
        habitaciones = caracteristicas.get('habitaciones', 0)
        dormitorios = caracteristicas.get('dormitorios', 0)
        banos_completos = caracteristicas.get('banos_completos', 0)
        banos_medios = caracteristicas.get('banos_medios', 0)
        superficie = caracteristicas.get('superficie_m2', 0)
        cochera_garaje = caracteristicas.get('cochera_garaje', False)

        if total_personas == 0:
            return 0.0

        puntuacion = 0.0

        # 1. Evaluación de habitaciones (40% del peso)
        if habitaciones > 0:
            # Regla mejorada: considerar tipo de familia
            if composicion.get('ninos'):
                # Familias con niños necesitan más espacio
                habitaciones_necesarias = max(2, (total_personas + 1) // 2)
            else:
                # Parejas o individuos
                habitaciones_necesarias = max(1, (total_personas + 1) // 2)

            if habitaciones >= habitaciones_necesarias:
                puntuacion += 0.4
            else:
                puntuacion += max(0.1, (habitaciones / habitaciones_necesarias) * 0.4)

        # 2. Evaluación de baños (25% del peso)
        banos_totales = banos_completos + (banos_medios * 0.5)
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

    def _evaluar_servicios(self, perfil: Dict[str, Any], propiedad: Dict[str, Any]) -> float:
        """Evalúa la proximidad a servicios necesarios usando estructura mejorada."""
        necesidades = perfil.get('necesidades', [])
        ubicacion = propiedad.get('ubicacion', {})
        valorizacion = propiedad.get('valorizacion_sector', {})

        if not necesidades:
            return 0.7  # Valor por defecto si no hay necesidades específicas

        puntuacion = 0.0
        servicios_encontrados = 0

        # Evaluar cada necesidad basada en características de la zona
        for necesidad in necesidades:
            servicio_encontrado = False

            # Escuelas - zonas familiares con buena seguridad
            if necesidad in ['escuela_primaria', 'colegio']:
                if valorizacion.get('seguridad_zona') in ['alta', 'media']:
                    servicio_encontrado = True
                # Zonas premium suelen tener buenas escuelas
                zona = ubicacion.get('zona', '')
                if zona in ['Equipetrol', 'Las Palmas', 'Urubó']:
                    servicio_encontrado = True

            # Universidades - zonas con demanda estudiantil
            elif necesidad == 'universidad':
                if valorizacion.get('demanda_sector') in ['alta', 'muy_alta']:
                    servicio_encontrado = True
                # Zonas norte suelen tener acceso a universidades
                if 'norte' in ubicacion.get('zona', '').lower():
                    servicio_encontrado = True

            # Supermercados y comercio - zonas con alta demanda
            elif necesidad in ['supermercado', 'comercio']:
                if valorizacion.get('demanda_sector') in ['alta', 'muy_alta']:
                    servicio_encontrado = True
                # Zonas premium suelen tener buen acceso a comercio
                zona = ubicacion.get('zona', '')
                if zona in ['Equipetrol', 'Las Palmas', 'Urubó']:
                    servicio_encontrado = True

            # Hospitales y salud - zonas seguras con buena infraestructura
            elif necesidad in ['hospital', 'clinica', 'salud']:
                if valorizacion.get('seguridad_zona') == 'alta':
                    servicio_encontrado = True
                if valorizacion.get('demanda_sector') in ['alta', 'muy_alta']:
                    servicio_encontrado = True

            if servicio_encontrado:
                servicios_encontrados += 1

        if necesidades:
            puntuacion = servicios_encontrados / len(necesidades)
            # Bonificación adicional si todos los servicios están disponibles
            if servicios_encontrados == len(necesidades):
                puntuacion = min(1.0, puntuacion + 0.1)

        return puntuacion

    def _evaluar_demografia(self, perfil: Dict[str, Any], propiedad: Dict[str, Any]) -> float:
        """Evalúa la compatibilidad demográfica del área usando estructura mejorada."""
        composicion = perfil.get('composicion_familiar', {})
        valorizacion = propiedad.get('valorizacion_sector', {})

        if not valorizacion:
            return 0.7  # Valor por defecto si no hay datos de valorización

        puntuacion = 0.0

        # Evaluar compatibilidad de nivel socioeconómico
        perfil_socioeconomico = self._determinar_nivel_socioeconomico(perfil)
        propiedad_socioeconomico = valorizacion.get('nivel_socioeconomico', '')

        if perfil_socioeconomico and propiedad_socioeconomico:
            if perfil_socioeconomico == propiedad_socioeconomico:
                puntuacion += 0.5
            elif self._son_niveles_compatibles(perfil_socioeconomico, propiedad_socioeconomico):
                puntuacion += 0.3

        # Evaluar seguridad de la zona
        seguridad = valorizacion.get('seguridad_zona', '')
        if seguridad:
            if seguridad == 'alta':
                puntuacion += 0.3
            elif seguridad == 'media':
                puntuacion += 0.15

        # Evaluar demanda del sector (indicador de calidad)
        demanda = valorizacion.get('demanda_sector', '')
        if demanda:
            if demanda == 'muy_alta':
                puntuacion += 0.2
            elif demanda == 'alta':
                puntuacion += 0.1

        # Evaluar plusvalía (indicador de buena inversión)
        plusvalia = valorizacion.get('plusvalia_tendencia', '')
        if plusvalia == 'creciente':
            puntuacion += 0.1

        return min(1.0, puntuacion)

    def _determinar_nivel_socioeconomico(self, perfil: Dict[str, Any]) -> str:
        """Determina el nivel socioeconómico basado en el presupuesto."""
        presupuesto = perfil.get('presupuesto', {})
        presupuesto_max = presupuesto.get('max', 0)

        if presupuesto_max >= 300000:
            return 'alto'
        elif presupuesto_max >= 180000:
            return 'medio_alto'
        elif presupuesto_max >= 120000:
            return 'medio'
        else:
            return 'bajo'

    def _son_niveles_compatibles(self, nivel1: str, nivel2: str) -> bool:
        """Verifica si dos niveles socioeconómicos son compatibles."""
        niveles_compatibles = {
            'alto': ['medio_alto', 'alto'],
            'medio_alto': ['alto', 'medio_alto', 'medio'],
            'medio': ['medio_alto', 'medio', 'bajo'],
            'bajo': ['medio', 'bajo']
        }

        return nivel2 in niveles_compatibles.get(nivel1, [])

    def _evaluar_preferencias(self, perfil: Dict[str, Any], propiedad: Dict[str, Any]) -> float:
        """Evalúa las preferencias de ubicación y estilo de vida usando estructura mejorada."""
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
            barrio_actual = ubicacion.get('barrio', '').lower() if ubicacion.get('barrio') else ''

            if ubicacion_preferida in barrio_actual or ubicacion_preferida in zona_actual:
                puntuacion += 0.35
            elif 'norte' in ubicacion_preferida and 'norte' in zona_actual:
                puntuacion += 0.25
            elif 'centro' in ubicacion_preferida and 'centro' in barrio_actual:
                puntuacion += 0.25
            elif any(zona in ubicacion_preferida for zona in ['equipetrol', 'las palmas', 'urubó']):
                if any(zona in zona_actual for zona in ['equipetrol', 'las palmas', 'urubó']):
                    puntuacion += 0.2

        # 2. Preferencia de tipo de propiedad (0.25 puntos)
        if 'tipo_propiedad' in preferencias and preferencias['tipo_propiedad']:
            tipo_preferido = preferencias['tipo_propiedad'].lower()
            tipo_propiedad = propiedad.get('tipo', '').lower() if propiedad.get('tipo') else ''

            if tipo_preferido in tipo_propiedad:
                puntuacion += 0.25

        # 3. Características específicas (0.2 puntos)
        caracteristicas_deseadas = preferencias.get('caracteristicas_deseadas', [])
        caracteristicas_disponibles = []

        # Verificar características determinantes
        if caracteristicas.get('cochera_garaje', False):
            caracteristicas_disponibles.append('garaje')
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

        # Contar coincidencias
        coincidencias = 0
        for deseada in caracteristicas_deseadas:
            if any(deseada in disponible for disponible in caracteristicas_disponibles):
                coincidencias += 1

        if caracteristicas_deseadas:
            puntuacion += (coincidencias / len(caracteristicas_deseadas)) * 0.2

        # 4. Nivel de seguridad (0.15 puntos)
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
        """
        Genera recomendaciones ordenadas por compatibilidad.

        Args:
            perfil: Perfil del prospecto
            limite: Número máximo de recomendaciones a retornar
            umbral_minimo: Compatibilidad mínima para considerar (0-1)

        Returns:
            Lista de propiedades recomendadas con su compatibilidad
        """
        inicio_tiempo = time.time()

        # Pre-filtrado rápido para reducir cálculos
        propiedades_filtradas = self._pre_filtrar_propiedades(perfil, umbral_minimo)

        recomendaciones = []

        # Calcular compatibilidad solo para propiedades pre-filtradas
        for propiedad in propiedades_filtradas:
            compatibilidad = self.calcular_compatibilidad(perfil, propiedad)
            if compatibilidad >= umbral_minimo:
                recomendaciones.append({
                    'propiedad': propiedad,
                    'compatibilidad': compatibilidad,
                    'justificacion': self._generar_justificacion(perfil, propiedad, compatibilidad)
                })

        # Ordenar por compatibilidad (descendente) - usar numpy para mejor rendimiento
        if recomendaciones:
            compatibilidades = [rec['compatibilidad'] for rec in recomendaciones]
            indices_ordenados = np.argsort(compatibilidades)[::-1]  # Descendente
            recomendaciones = [recomendaciones[i] for i in indices_ordenados]

        tiempo_total = time.time() - inicio_tiempo
        if hasattr(self, 'stats'):
            self.stats['tiempo_total'] += tiempo_total

        return recomendaciones[:limite]

    def _pre_filtrar_propiedades(self, perfil: Dict[str, Any], umbral_minimo: float) -> List[Dict[str, Any]]:
        """
        Realiza un pre-filtrado rápido de propiedades basado en criterios básicos usando estructura mejorada.
        Esto reduce el número de cálculos de compatibilidad completos.
        """
        propiedades_filtradas = []

        presupuesto = perfil.get('presupuesto', {})
        presupuesto_min = presupuesto.get('min', 0)
        presupuesto_max = presupuesto.get('max', float('inf'))

        composicion = perfil.get('composicion_familiar', {})
        total_personas = composicion.get('adultos', 0) + len(composicion.get('ninos', [])) + composicion.get('adultos_mayores', 0)

        preferencias = perfil.get('preferencias', {})
        ubicacion_preferida = preferencias.get('ubicacion', '').lower() if preferencias.get('ubicacion') else ''

        for propiedad in self.propiedades:
            # Filtro rápido de presupuesto
            caracteristicas = propiedad.get('caracteristicas_principales', {})
            precio = caracteristicas.get('precio', 0)
            if precio > presupuesto_max * 1.5:  # Permitir hasta 50% sobre el máximo
                continue

            # Filtro rápido de habitaciones básico
            habitaciones = caracteristicas.get('habitaciones', 0)
            if total_personas > 0 and habitaciones == 0:
                continue

            # Filtro rápido de superficie mínima
            superficie = caracteristicas.get('superficie_m2', 0)
            if superficie > 0 and total_personas > 0:
                superficie_minima_requerida = total_personas * 15  # 15m² por persona como mínimo
                if superficie < superficie_minima_requerida:
                    continue

            # Filtro rápido de ubicación si se especifica
            if ubicacion_preferida:
                ubicacion = propiedad.get('ubicacion', {})
                zona = ubicacion.get('zona', '').lower() if ubicacion.get('zona') else ''
                barrio = ubicacion.get('barrio', '').lower() if ubicacion.get('barrio') else ''

                # Si se prefiere una ubicación específica, filtrar otras zonas
                ubicaciones_excluyentes = {
                    'norte': ['sur', 'centro'],
                    'sur': ['norte'],
                    'centro': ['norte', 'sur']
                }

                for preferida, excluyentes in ubicaciones_excluyentes.items():
                    if preferida in ubicacion_preferida:
                        if any(excluyente in zona or excluyente in barrio for excluyente in excluyentes):
                            continue

            propiedades_filtradas.append(propiedad)

        return propiedades_filtradas

    def _generar_justificacion(self, perfil: Dict[str, Any], propiedad: Dict[str, Any], compatibilidad: float) -> str:
        """Genera una justificación detallada usando campos determinantes."""
        composicion = perfil.get('composicion_familiar', {})
        presupuesto = perfil.get('presupuesto', {})
        caracteristicas = propiedad.get('caracteristicas_principales', {})
        detalles = propiedad.get('detalles_construccion', {})
        condominio = propiedad.get('condominio', {})
        ubicacion = propiedad.get('ubicacion', {})
        valorizacion = propiedad.get('valorizacion_sector', {})

        justificaciones = []

        # Justificación por presupuesto
        if caracteristicas.get('precio') and presupuesto.get('max'):
            precio = caracteristicas['precio']
            presupuesto_max = presupuesto['max']
            if precio <= presupuesto_max * 0.9:
                justificaciones.append(f"Precio de ${precio:,.0f} está dentro del presupuesto (${presupuesto_max:,.0f})")
            elif precio <= presupuesto_max:
                justificaciones.append(f"Precio de ${precio:,.0f} se ajusta al presupuesto máximo")

        # Justificación por composición familiar
        total_personas = composicion.get('adultos', 0) + len(composicion.get('ninos', [])) + composicion.get('adultos_mayores', 0)
        habitaciones = caracteristicas.get('habitaciones', 0)
        if habitaciones >= total_personas:
            justificaciones.append(f"{habitaciones} habitaciones adecuadas para {total_personas} personas")
        elif habitaciones > 0:
            justificaciones.append(f"{habitaciones} habitaciones disponibles")

        # Justificación por superficie
        superficie = caracteristicas.get('superficie_m2', 0)
        if superficie > 0:
            area_por_persona = superficie / max(total_personas, 1)
            if area_por_persona >= 25:
                justificaciones.append(f"Superficie generosa: {superficie}m² ({area_por_persona:.1f}m² por persona)")
            else:
                justificaciones.append(f"Superficie de {superficie}m²")

        # Justificación por baños
        banos_completos = caracteristicas.get('banos_completos', 0)
        banos_medios = caracteristicas.get('banos_medios', 0)
        if banos_completos > 0:
            if banos_completos >= total_personas / 2:
                justificaciones.append(f"{banos_completos} baños completos (adecuado para {total_personas} personas)")
            else:
                justificaciones.append(f"{banos_completos} baños completos")

        # Justificación por garaje
        if caracteristicas.get('cochera_garaje'):
            espacios = caracteristicas.get('numero_espacios_garaje', 1)
            justificaciones.append(f"Cuenta con {espacios} espacio{'s' if espacios > 1 else ''} de garaje")

        # Justificación por zona premium
        zona = ubicacion.get('zona', '')
        if zona in ['Equipetrol', 'Las Palmas', 'Urubó', 'Zona Norte']:
            justificaciones.append(f"Ubicada en zona premium: {zona}")

        # Justificación por condominio
        if condominio.get('es_condominio_cerrado'):
            justificaciones.append("Condominio cerrado con seguridad 24h")
            amenidades = condominio.get('amenidades', [])
            if amenidades:
                justificaciones.append(f"Amenidades: {', '.join(amenidades[:2])}")

        # Justificación por estado
        estado = detalles.get('estado_conservacion', '')
        if estado:
            justificaciones.append(f"Estado de conservación: {estado}")

        # Justificación por valorización
        if valorizacion.get('plusvalia_tendencia') == 'creciente':
            justificaciones.append("Zona con plusvalía creciente")
        if valorizacion.get('seguridad_zona') == 'alta':
            justificaciones.append("Zona con alta seguridad")

        # Si no hay justificaciones específicas, dar una general
        if not justificaciones:
            justificaciones.append("Propiedad que cumple con requisitos básicos")

        return ". ".join(justificaciones) + "."

    def obtener_estadisticas_rendimiento(self) -> Dict[str, Any]:
        """
        Retorna estadísticas de rendimiento del motor de recomendación.
        """
        stats = self.stats.copy()
        if stats['calculos_realizados'] > 0:
            stats['tiempo_promedio'] = stats['tiempo_total'] / stats['calculos_realizados']
            stats['cache_hit_rate'] = stats['cache_hits'] / stats['calculos_realizados']
        else:
            stats['tiempo_promedio'] = 0.0
            stats['cache_hit_rate'] = 0.0

        stats['cache_size'] = len(self._cache_compatibility)
        return stats

    def limpiar_cache_completo(self):
        """
        Limpia completamente el cache y resetea estadísticas.
        """
        self._limpiar_cache()
        self.stats = {
            'calculos_realizados': 0,
            'cache_hits': 0,
            'tiempo_total': 0.0
        }
        # Limpiar cache LRU también
        self._evaluar_presupuesto_cache.cache_clear()