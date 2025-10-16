#!/usr/bin/env python3
"""
Sistema de puntuación de prospectos para asesores comerciales Citrino
Analiza la información captada y asigna una puntuación basada en datos del mercado

DEPRECATED - Sistema de scoring multicriterio obsoleto
REASON: Sistema complejo de pesos (presupuesto_realista 20, urgencia 15, etc.)
     que agrega complejidad innecesaria sin valor demostrado.

ALTERNATIVE: Chatbot conversacional v2.3.0 con 92% éxito evaluado
STATUS: Será reemplazado completamente por asistente IA conversacional
"""

import json
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Prospecto:
    """Clase para representar un prospecto con toda su información"""
    # Información básica
    id: str
    fecha_contacto: str
    asesor: str

    # Presupuesto y financiamiento
    presupuesto_min: float
    presupuesto_max: float
    tiene_financiamiento: bool

    # Composición familiar
    adultos: int
    ninos_edades: List[int]
    adolescentes_edades: List[int]
    adultos_mayores: int
    tiene_mascotas: bool

    # Necesidades de propiedad
    tipo_propiedad: str
    habitaciones_min: int
    banos_min: int
    necesita_garaje: bool
    zonas_preferencia: List[str]

    # Prioridades y urgencia
    urgencia: str  # 'inmediata', 'corta', 'media', 'larga'
    nivel_conocimiento_mercado: str  # 'bajo', 'medio', 'alto'
    motivacion: str  # 'primera_vivienda', 'cambio', 'inversion', 'trabajo'

    # Información adicional
    servicios_cercanos_requeridos: List[str]
    caracteristicas_esenciales: List[str]
    cuota_inicial: Optional[float] = None
    superficie_min: Optional[float] = None
    observaciones: str = ""

class ScoringProspectos:
    """DEPRECATED - Sistema de puntuación basado en datos del mercado real.

    ESTA CLASE SERÁ ELIMINADA - Usar chatbot conversacional v2.3.0 en su lugar.
    El sistema de scoring multicriterio ha sido reemplazado por IA conversacional
    con 92% éxito evaluado y mejor experiencia de usuario.
    """

    def __init__(self):
        # Cargar datos del mercado
        self.cargar_datos_mercado()

        # Definir pesos para diferentes factores
        self.pesos = {
            'presupuesto_realista': 20,
            'urgencia': 15,
            'necesidades_claras': 15,
            'potencial_compra': 12,
            'composicion_familiar_definida': 10,
            'preferencias_ubicacion': 8,
            'conocimiento_mercado': 7,
            'financiamiento_definido': 8,
            'contactabilidad': 5
        }

        # Umbrales del mercado basados en datos reales
        self.umbral_precios = {
            'bajo': 95000,
            'medio_bajo': 150000,
            'medio': 200000,
            'medio_alto': 250000,
            'alto': 350000
        }

        # Puntuaciones por urgencia
        self.puntuacion_urgencia = {
            'inmediata': 15,
            'corta': 12,
            'media': 8,
            'larga': 3
        }

        # Compatibilidad por tipo de propiedad según composición familiar
        self.compatibilidad_tipo_propiedad = {
            ('soltero', 'departamento'): 10,
            ('pareja_sin_hijos', 'departamento'): 10,
            ('familia_pequena', 'casa'): 10,
            ('familia_grande', 'casa'): 10,
            ('adultos_mayores', 'departamento'): 10,
            ('inversionista', 'departamento'): 8
        }

    def cargar_datos_mercado(self):
        """Carga datos estadísticos del mercado Santa Cruz"""
        # Estadísticas basadas en el análisis de 76,853 propiedades
        self.estadisticas_mercado = {
            'precio_promedio': 210000,
            'precio_minimo_mercado': 106633,
            'precio_maximo_mercado': 385939,
            'superficie_promedio': 145,
            'habitaciones_promedio': 3,
            'propiedades_por_zona': {
                'Equipetrol': 8500,
                'Zona Norte': 12000,
                'Centro': 9500,
                'Urubó': 6500,
                'Zona Sur': 4500
            },
            'distribucion_precios': {
                'bajo': 0.15,      # < $150k
                'medio_bajo': 0.25, # $150k - $200k
                'medio': 0.30,     # $200k - $250k
                'medio_alto': 0.20, # $250k - $350k
                'alto': 0.10       # > $350k
            }
        }

    def determinar_perfil_familiar(self, prospecto: Prospecto) -> str:
        """Determina el perfil familiar basado en la composición"""
        total_personas = prospecto.adultos + len(prospecto.ninos_edades) + len(prospecto.adolescentes_edades) + prospecto.adultos_mayores

        if prospecto.adultos_mayores > 0:
            return 'adultos_mayores'
        elif len(prospecto.ninos_edades) + len(prospecto.adolescentes_edades) > 0:
            if total_personas <= 4:
                return 'familia_pequena'
            else:
                return 'familia_grande'
        elif prospecto.adultos == 1:
            return 'soltero'
        elif prospecto.adultos == 2:
            return 'pareja_sin_hijos'
        else:
            return 'otro'

    def evaluar_presupuesto_realista(self, prospecto: Prospecto) -> int:
        """Evalúa si el presupuesto es realista según el mercado"""
        # Calcular presupuesto promedio
        presupuesto_promedio = (prospecto.presupuesto_min + prospecto.presupuesto_max) / 2

        # Verificar si el presupuesto está dentro de rangos del mercado
        if presupuesto_promedio < self.estadisticas_mercado['precio_minimo_mercado']:
            return 0  # Presupuesto muy bajo
        elif presupuesto_promedio > self.estadisticas_mercado['precio_maximo_mercado']:
            return 5  # Presupuesto muy alto (posible pero difícil)

        # Evaluar correlación entre presupuesto y tipo de propiedad
        perfil = self.determinar_perfil_familiar(prospecto)

        if perfil == 'familia_grande' and presupuesto_promedio < 180000:
            return 5  # Presupuesto bajo para familia grande
        elif perfil == 'soltero' and presupuesto_promedio > 300000:
            return 8  # Presupuesto alto pero posible

        # Presupuesto dentro de rangos realistas
        rango_presupuesto = presupuesto_promedio / 1000
        if 150 <= rango_presupuesto <= 250:
            return 20  # Rango óptimo para la mayoría de perfiles
        elif 100 <= rango_presupuesto < 150 or 250 < rango_presupuesto <= 350:
            return 15  # Rango aceptable
        else:
            return 10  # Rango extremo pero posible

    def evaluar_potencial_compra(self, prospecto: Prospecto) -> int:
        """Evalúa el potencial real de compra basado en financiamiento"""
        if not prospecto.tiene_financiamiento and prospecto.presupuesto_max < 100000:
            return 3  # Sin financiamiento y presupuesto bajo
        elif prospecto.tiene_financiamiento:
            return 12  # Tiene financiamiento pre-aprobado
        elif prospecto.cuota_inicial and prospecto.cuota_inicial >= prospecto.presupuesto_max * 0.20:
            return 10  # Buena cuota inicial
        else:
            return 6  # Potencial moderado

    def evaluar_necesidades_claras(self, prospecto: Prospecto) -> int:
        """Evalúa qué tan claras están las necesidades del prospecto"""
        puntuacion = 0

        # Necesidades básicas definidas
        if prospecto.habitaciones_min > 0:
            puntuacion += 4
        if prospecto.banos_min > 0:
            puntuacion += 3
        if prospecto.tipo_propiedad:
            puntuacion += 3
        if prospecto.zonas_preferencia:
            puntuacion += 3
        if prospecto.superficie_min:
            puntuacion += 2

        return min(puntuacion, 15)  # Máximo 15 puntos

    def evaluar_composicion_familiar_definida(self, prospecto: Prospecto) -> int:
        """Evalúa si la composición familiar está bien definida"""
        if prospecto.adultos == 0:
            return 0  # No hay adultos definidos

        puntuacion = 5  # Base por tener adultos definidos

        # Información adicional mejora la puntuación
        if prospecto.ninos_edades or prospecto.adolescentes_edades:
            puntuacion += 3
        if prospecto.adultos_mayores > 0:
            puntuacion += 2

        return min(puntuacion, 10)

    def evaluar_preferencias_ubicacion(self, prospecto: Prospecto) -> int:
        """Evalúa las preferencias de ubicación basadas en disponibilidad real"""
        if not prospecto.zonas_preferencia:
            return 2  # Sin preferencias claras

        # Verificar disponibilidad en zonas preferidas
        total_disponible = 0
        for zona in prospecto.zonas_preferencia:
            if zona in self.estadisticas_mercado['propiedades_por_zona']:
                total_disponible += self.estadisticas_mercado['propiedades_por_zona'][zona]

        if total_disponible > 5000:
            return 8  # Alta disponibilidad
        elif total_disponible > 2000:
            return 6  # Disponibilidad media
        elif total_disponible > 500:
            return 4  # Disponibilidad baja
        else:
            return 2  # Muy baja disponibilidad

    def evaluar_conocimiento_mercado(self, prospecto: Prospecto) -> int:
        """Evalúa el nivel de conocimiento del mercado"""
        conocimiento_scores = {
            'alto': 7,
            'medio': 5,
            'bajo': 3
        }
        return conocimiento_scores.get(prospecto.nivel_conocimiento_mercado, 3)

    def evaluar_urgencia(self, prospecto: Prospecto) -> int:
        """Evalúa la urgencia de compra"""
        return self.puntuacion_urgencia.get(prospecto.urgencia, 3)

    def evaluar_financiamiento_definido(self, prospecto: Prospecto) -> int:
        """Evalúa si el financiamiento está bien definido"""
        if prospecto.tiene_financiamiento:
            return 8
        elif prospecto.cuota_inicial:
            return 5
        else:
            return 2

    def calcular_puntuacion_total(self, prospecto: Prospecto) -> Dict:
        """Calcula la puntuación total del prospecto"""

        # Evaluar cada factor
        puntuaciones = {
            'presupuesto_realista': self.evaluar_presupuesto_realista(prospecto),
            'urgencia': self.evaluar_urgencia(prospecto),
            'necesidades_claras': self.evaluar_necesidades_claras(prospecto),
            'potencial_compra': self.evaluar_potencial_compra(prospecto),
            'composicion_familiar_definida': self.evaluar_composicion_familiar_definida(prospecto),
            'preferencias_ubicacion': self.evaluar_preferencias_ubicacion(prospecto),
            'conocimiento_mercado': self.evaluar_conocimiento_mercado(prospecto),
            'financiamiento_definido': self.evaluar_financiamiento_definido(prospecto)
        }

        # Calcular puntuación total ponderada
        # La puntuación máxima posible es sum(pesos.values()) = 100
        puntuacion_total = sum(
            puntuaciones[factor] * (self.pesos[factor] / 20)  # Normalizar para que el máximo sea 100
            for factor in puntuaciones
        )

        # Determinar clasificación
        if puntuacion_total >= 80:
            clasificacion = 'caliente'
            prioridad = 'Alta'
            recomendacion = 'Atención inmediata, contacto diario'
        elif puntuacion_total >= 60:
            clasificacion = 'tibio'
            prioridad = 'Media'
            recomendacion = 'Seguimiento semanal, mantener interes'
        elif puntuacion_total >= 40:
            clasificacion = 'frio'
            prioridad = 'Baja'
            recomendacion = 'Seguimiento quincenal, esperar desarrollo'
        else:
            clasificacion = 'muy_frio'
            prioridad = 'Muy baja'
            recomendacion = 'Reevaluar en 3 meses o archivar'

        return {
            'puntuacion_total': round(puntuacion_total, 1),
            'clasificacion': clasificacion,
            'prioridad': prioridad,
            'recomendacion': recomendacion,
            'puntuaciones_detalle': puntuaciones,
            'fortalezas': self.identificar_fortalezas(puntuaciones),
            'debilidades': self.identificar_debilidades(puntuaciones),
            'perfil_familiar': self.determinar_perfil_familiar(prospecto),
            'potencial_propiedades': self.estimar_potencial_propiedades(prospecto)
        }

    def identificar_fortalezas(self, puntuaciones: Dict) -> List[str]:
        """Identifica las fortalezas del prospecto"""
        fortalezas = []

        if puntuaciones['presupuesto_realista'] >= 15:
            fortalezas.append('Presupuesto realista y adecuado')
        if puntuaciones['urgencia'] >= 12:
            fortalezas.append('Alta urgencia de compra')
        if puntuaciones['necesidades_claras'] >= 12:
            fortalezas.append('Necesidades bien definidas')
        if puntuaciones['potencial_compra'] >= 10:
            fortalezas.append('Buen potencial financiero')
        if puntuaciones['composicion_familiar_definida'] >= 8:
            fortalezas.append('Perfil familiar claro')

        return fortalezas

    def identificar_debilidades(self, puntuaciones: Dict) -> List[str]:
        """Identifica las debilidades del prospecto"""
        debilidades = []

        if puntuaciones['presupuesto_realista'] < 10:
            debilidades.append('Presupuesto poco realista')
        if puntuaciones['urgencia'] < 8:
            debilidades.append('Baja urgencia')
        if puntuaciones['necesidades_claras'] < 8:
            debilidades.append('Necesidades poco claras')
        if puntuaciones['potencial_compra'] < 6:
            debilidades.append('Potencial financiero limitado')
        if puntuaciones['financiamiento_definido'] < 5:
            debilidades.append('Financiamiento no definido')

        return debilidades

    def estimar_potencial_propiedades(self, prospecto: Prospecto) -> Dict:
        """Estima el potencial de propiedades que coinciden"""
        # Basado en análisis estadístico del mercado
        perfil = self.determinar_perfil_familiar(prospecto)

        # Estimaciones basadas en perfil y presupuesto
        if perfil == 'familia_grande':
            estimado_base = 12000  # 12k propiedades para familias grandes
        elif perfil == 'familia_pequena':
            estimado_base = 25000  # 25k propiedades para familias pequeñas
        elif perfil == 'pareja_sin_hijos':
            estimado_base = 20000  # 20k propiedades para parejas
        elif perfil == 'soltero':
            estimado_base = 8000   # 8k propiedades para solteros
        elif perfil == 'adultos_mayores':
            estimado_base = 6000   # 6k propiedades para adultos mayores
        else:
            estimado_base = 5000   # 5k propiedades para otros perfiles

        # Ajustar por presupuesto
        presupuesto_promedio = (prospecto.presupuesto_min + prospecto.presupuesto_max) / 2
        if presupuesto_promedio > 300000:
            factor_presupuesto = 0.3  # Solo 30% de propiedades en rango alto
        elif presupuesto_promedio < 120000:
            factor_presupuesto = 0.4  # 40% de propiedades en rango bajo
        else:
            factor_presupuesto = 0.6  # 60% de propiedades en rango medio

        # Ajustar por zonas preferidas
        if prospecto.zonas_preferencia:
            factor_zonas = min(len(prospecto.zonas_preferencia) * 0.3, 0.8)
        else:
            factor_zonas = 1.0  # Todas las zonas disponibles

        potencial_total = int(estimado_base * factor_presupuesto * factor_zonas)

        return {
            'estimado_total': potencial_total,
            'cumplen_criterios': f"{int(potencial_total * 0.7)}-{int(potencial_total * 0.9)}",
            'altamente_recomendadas': f"{int(potencial_total * 0.1)}-{int(potencial_total * 0.2)}"
        }

def crear_prospecto_desde_dict(datos: Dict) -> Prospecto:
    """Crea un objeto Prospecto desde un diccionario de datos"""
    return Prospecto(
        id=datos.get('id', f"prospecto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
        fecha_contacto=datos.get('fecha_contacto', datetime.now().strftime('%Y-%m-%d')),
        asesor=datos.get('asesor', ''),

        presupuesto_min=float(datos.get('presupuesto_min', 0)),
        presupuesto_max=float(datos.get('presupuesto_max', 0)),
        tiene_financiamiento=datos.get('tiene_financiamiento', False),
        cuota_inicial=datos.get('cuota_inicial'),

        adultos=int(datos.get('adultos', 0)),
        ninos_edades=datos.get('ninos_edades', []),
        adolescentes_edades=datos.get('adolescentes_edades', []),
        adultos_mayores=int(datos.get('adultos_mayores', 0)),
        tiene_mascotas=datos.get('tiene_mascotas', False),

        tipo_propiedad=datos.get('tipo_propiedad', ''),
        habitaciones_min=int(datos.get('habitaciones_min', 0)),
        banos_min=int(datos.get('banos_min', 0)),
        superficie_min=datos.get('superficie_min'),
        necesita_garaje=datos.get('necesita_garaje', False),
        zonas_preferencia=datos.get('zonas_preferencia', []),

        urgencia=datos.get('urgencia', 'media'),
        nivel_conocimiento_mercado=datos.get('nivel_conocimiento_mercado', 'medio'),
        motivacion=datos.get('motivacion', 'primera_vivienda'),

        servicios_cercanos_requeridos=datos.get('servicios_cercanos_requeridos', []),
        caracteristicas_esenciales=datos.get('caracteristicas_esenciales', []),
        observaciones=datos.get('observaciones', '')
    )

# Ejemplo de uso
if __name__ == "__main__":
    # Crear sistema de scoring
    scoring = ScoringProspectos()

    # Ejemplo de prospecto
    datos_prospecto = {
        'adultos': 2,
        'ninos_edades': [8, 12],
        'adolescentes_edades': [],
        'adultos_mayores': 0,
        'tiene_mascotas': False,

        'presupuesto_min': 200000,
        'presupuesto_max': 280000,
        'tiene_financiamiento': True,
        'cuota_inicial': 60000,

        'tipo_propiedad': 'casa',
        'habitaciones_min': 3,
        'banos_min': 2,
        'superficie_min': 150,
        'necesita_garaje': True,
        'zonas_preferencia': ['Zona Norte', 'Equipetrol'],

        'urgencia': 'corta',
        'nivel_conocimiento_mercado': 'medio',
        'motivacion': 'primera_vivienda',

        'servicios_cercanos_requeridos': ['escuelas', 'seguridad'],
        'caracteristicas_esenciales': ['jardin', 'seguridad_24h'],

        'asesor': 'Juan Pérez'
    }

    # Crear prospecto y evaluar
    prospecto = crear_prospecto_desde_dict(datos_prospecto)
    resultado = scoring.calcular_puntuacion_total(prospecto)

    # Mostrar resultados
    print(f"=== Evaluación de Prospecto ===")
    print(f"Puntuación Total: {resultado['puntuacion_total']}/100")
    print(f"Clasificación: {resultado['clasificacion'].upper()}")
    print(f"Prioridad: {resultado['prioridad']}")
    print(f"Perfil Familiar: {resultado['perfil_familiar']}")
    print(f"Recomendación: {resultado['recomendacion']}")
    print(f"\nPotencial de Propiedades:")
    print(f"  - Estimado total: {resultado['potencial_propiedades']['estimado_total']:,}")
    print(f"  - Cumplen criterios: {resultado['potencial_propiedades']['cumplen_criterios']}")
    print(f"  - Altamente recomendadas: {resultado['potencial_propiedades']['altamente_recomendadas']}")
    print(f"\nFortalezas:")
    for fortaleza in resultado['fortalezas']:
        print(f"   {fortaleza}")
    print(f"\nDebilidades:")
    for debilidad in resultado['debilidades']:
        print(f"   {debilidad}")