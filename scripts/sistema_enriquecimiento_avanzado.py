#!/usr/bin/env python3
"""
Sistema avanzado de enriquecimiento con datos completos de la Guía Urbana
Utiliza 5,261 servicios + 353 proyectos con análisis de mercado
"""

import json
import os
import math
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SistemaEnriquecimientoAvanzado:
    """Sistema avanzado de enriquecimiento con datos municipales completos"""

    def __init__(self):
        self.datos_municipales = {}
        self.proyectos_mercado = {}
        self.indices_servicios = {}
        self.indices_proyectos = {}
        self.cargar_datos_completos()

    def cargar_datos_completos(self):
        """Carga los datos completos de la guía urbana"""
        ruta_datos = os.path.join(os.path.dirname(__file__), '..', 'data', 'guia_urbana_municipal_completa.json')

        if not os.path.exists(ruta_datos):
            logger.warning("No se encontraron los datos completos de guía urbana")
            return

        try:
            with open(ruta_datos, 'r', encoding='utf-8') as f:
                datos = json.load(f)

            self.datos_municipales = datos.get('servicios_consolidados', [])
            self.proyectos_mercado = datos.get('proyectos_mercado', [])
            self.datos_tematicos = datos.get('servicios_tematicos', {})

            self.crear_indices_avanzados()
            logger.info(f"Guía urbana avanzada cargada:")
            logger.info(f"  - {len(self.datos_municipales)} servicios consolidados")
            logger.info(f"  - {len(self.proyectos_mercado)} proyectos de mercado")
            logger.info(f"  - {len(self.datos_tematicos)} categorías temáticas")

        except Exception as e:
            logger.error(f"Error cargando datos completos: {e}")

    def crear_indices_avanzados(self):
        """Crea índices avanzados para búsquedas rápidas"""
        # Índice de servicios por categoría y zona
        self.indices_servicios = {
            'abastecimiento': {},
            'salud': {},
            'educacion': {},
            'deporte': {},
            'cultura': {},
            'transporte': {},
            'otros': {}
        }

        # Indexar servicios consolidados
        for servicio in self.datos_municipales:
            categoria = servicio.get('categoria_principal', 'otros')
            zona_key = self.obtener_zona_key(servicio)

            if zona_key not in self.indices_servicios[categoria]:
                self.indices_servicios[categoria][zona_key] = []

            self.indices_servicios[categoria][zona_key].append({
                'nombre': servicio['nombre'],
                'coordenadas': servicio['coordenadas'],
                'nivel': servicio.get('nivel', 'desconocido'),
                'distancia_estimada': self.calcular_distancia_estimada(servicio)
            })

        # Índice de proyectos por zona
        self.indices_proyectos = {}
        for proyecto in self.proyectos_mercado:
            zona = proyecto.get('zona', 'Desconocida')
            if zona not in self.indices_proyectos:
                self.indices_proyectos[zona] = []

            self.indices_proyectos[zona].append(proyecto)

    def obtener_zona_key(self, servicio: Dict) -> str:
        """Obtiene una clave de zona para indexación"""
        distrito = str(servicio.get('distrito', '')) if servicio.get('distrito') is not None else ''
        uv = str(servicio.get('unidad_vecinal', '')) if servicio.get('unidad_vecinal') is not None else ''
        barrio = str(servicio.get('barrio', '')) if servicio.get('barrio') is not None else ''

        if barrio and barrio != 'Sin barrio':
            return barrio.lower()
        elif uv:
            return f"uv_{uv}"
        elif distrito:
            return f"distrito_{distrito}"
        else:
            return 'otra'

    def calcular_distancia_estimada(self, servicio: Dict) -> float:
        """Calcula distancia estimada basada en distritos"""
        # Lógica simplificada - en producción usaría fórmula de Haversine
        return 500  # metros estimados

    def calcular_puntuacion_servicios_avanzada(self, zona: str, necesidades: List[str]) -> Dict[str, Any]:
        """Calcula puntuación avanzada de servicios para una zona"""
        zona_key = zona.lower()

        resultado = {
            'puntuacion_total': 0.0,
            'detalle_por_categoria': {},
            'servicios_encontrados': 0,
            'recomendaciones': []
        }

        categorias_necesidad = self.mapear_necesidades_a_categorias(necesidades)
        total_categorias = len(categorias_necesidad) or 1
        puntuacion_acumulada = 0.0

        for necesidad, categorias in categorias_necesidad.items():
            mejor_puntuacion_categoria = 0.0
            servicios_categoria = []

            for categoria in categorias:
                if categoria in self.indices_servicios:
                    # Buscar servicios en zonas similares
                    servicios_encontrados = self.buscar_servicios_por_zona_similar(categoria, zona_key)

                    if servicios_encontrados:
                        # Calcular puntuación basada en cantidad y cercanía
                        cantidad = len(servicios_encontrados)
                        distancia_promedio = sum(s['distancia_estimada'] for s in servicios_encontrados) / cantidad

                        # Puntuación: más servicios y más cercanos = mejor
                        puntuacion = min(1.0, (cantidad * 0.3) + (1000 - distancia_promedio) / 1000 * 0.7)
                        mejor_puntuacion_categoria = max(mejor_puntuacion_categoria, puntuacion)

                        servicios_categoria.extend(servicios_encontrados[:3])  # Top 3

            resultado['detalle_por_categoria'][necesidad] = {
                'puntuacion': mejor_puntuacion_categoria,
                'servicios': servicios_categoria
            }

            puntuacion_acumulada += mejor_puntuacion_categoria

        resultado['puntuacion_total'] = puntuacion_acumulada / total_categorias
        resultado['servicios_encontrados'] = sum(len(v['servicios']) for v in resultado['detalle_por_categoria'].values())

        return resultado

    def mapear_necesidades_a_categorias(self, necesidades: List[str]) -> Dict[str, List[str]]:
        """Mapea necesidades de usuario a categorías de servicios"""
        mapeo = {
            'seguridad': ['otros'],  # No tenemos datos directos de seguridad
            'colegios': ['educacion'],
            'escuelas': ['educacion'],
            'educacion': ['educacion'],
            'areas verdes': ['deporte'],
            'parques': ['deporte'],
            'supermercado': ['abastecimiento'],
            'compras': ['abastecimiento'],
            'hospital': ['salud'],
            'medico': ['salud'],
            'salud': ['salud'],
            'farmacia': ['salud'],
            'gimnasio': ['deporte'],
            'restaurantes': ['otros'],
            'vida urbana': ['cultura', 'otros'],
            'transporte': ['transporte'],
            'tranquilidad': ['otros'],
            'acceso facil': ['transporte', 'otros']
        }

        resultado = {}
        for necesidad in necesidades:
            necesidad_lower = necesidad.lower()
            for key, categorias in mapeo.items():
                if key in necesidad_lower:
                    resultado[necesidad] = categorias
                    break

        return resultado

    def buscar_servicios_por_zona_similar(self, categoria: str, zona_key: str) -> List[Dict]:
        """Busca servicios en zonas similares o coincidentes"""
        servicios = []

        # Búsqueda exacta primero
        if zona_key in self.indices_servicios[categoria]:
            servicios.extend(self.indices_servicios[categoria][zona_key])

        # Búsqueda por coincidencia parcial
        for zona_idx, servicios_zona in self.indices_servicios[categoria].items():
            if zona_key in zona_idx or zona_idx in zona_key:
                servicios.extend(servicios_zona)

        # Si no hay resultados, buscar en toda la ciudad
        if not servicios and self.indices_servicios[categoria]:
            for servicios_zona in self.indices_servicios[categoria].values():
                servicios.extend(servicios_zona[:5])  # Limitar para no saturar

        return servicios

    def obtener_analisis_mercado_zona(self, zona: str) -> Dict[str, Any]:
        """Obtiene análisis de mercado para una zona específica"""
        if zona not in self.indices_proyectos:
            return {'existe_datos': False}

        proyectos = self.indices_proyectos[zona]
        if not proyectos:
            return {'existe_datos': False}

        # Analizar tendencias de mercado
        precios_m2 = [p.get('precio_m2_venta', 0) for p in proyectos if p.get('precio_m2_venta', 0) > 0]
        porcentajes_vendidos = [p.get('porcentaje_vendido', 0) for p in proyectos]

        analisis = {
            'existe_datos': True,
            'total_proyectos': len(proyectos),
            'precio_m2_promedio': sum(precios_m2) / len(precios_m2) if precios_m2 else 0,
            'precio_m2_min': min(precios_m2) if precios_m2 else 0,
            'precio_m2_max': max(precios_m2) if precios_m2 else 0,
            'ventas_promedio': sum(porcentajes_vendidos) / len(porcentajes_vendidos) if porcentajes_vendidos else 0,
            'unidades_disponibles': sum(p.get('unidades_disponibles', 0) for p in proyectos),
            'nivel_demanda': self.calcular_nivel_demanda(proyectos),
            'tendencia_precios': self.analizar_tendencia_precios(proyectos)
        }

        return analisis

    def calcular_nivel_demanda(self, proyectos: List[Dict]) -> str:
        """Calcula nivel de demanda basado en velocidad de ventas"""
        ritmos_venta = [p.get('indicadores_mercado', {}).get('ritmo_venta', 0) for p in proyectos]
        ritmo_promedio = sum(ritmos_venta) / len(ritmos_venta) if ritmos_venta else 0

        if ritmo_promedio >= 10:
            return 'muy_alta'
        elif ritmo_promedio >= 5:
            return 'alta'
        elif ritmo_promedio >= 2:
            return 'media'
        else:
            return 'baja'

    def analizar_tendencia_precios(self, proyectos: List[Dict]) -> str:
        """Analiza tendencia de precios basada en márgenes"""
        margenes = [p.get('margen_comparativo', 0) for p in proyectos if p.get('margen_comparativo', 0) != 0]
        if not margenes:
            return 'estable'

        margen_promedio = sum(margenes) / len(margenes)

        if margen_promedio > 20:
            return 'creciente'
        elif margen_promedio > 0:
            return 'estable_alza'
        else:
            return 'estable'

    def enriquecer_recomendacion_avanzada(self, propiedad: Dict[str, Any], necesidades: List[str]) -> Dict[str, Any]:
        """Enriquece una recomendación con datos avanzados"""

        # Extraer información básica
        ubicacion = propiedad.get('ubicacion', {})
        zona = ubicacion.get('zona', 'Desconocida')

        # Obtener análisis de servicios y mercado
        analisis_servicios = self.calcular_puntuacion_servicios_avanzada(zona, necesidades)
        analisis_mercado = self.obtener_analisis_mercado_zona(zona)

        # Calcular factores de enriquecimiento
        factor_servicios = 1.0 + (analisis_servicios['puntuacion_total'] * 0.2)  # Hasta +20%
        factor_mercado = 1.0

        if analisis_mercado['existe_datos']:
            # Ajustar según condiciones de mercado
            if analisis_mercado['nivel_demanda'] in ['alta', 'muy_alta']:
                factor_mercado += 0.1
            if analisis_mercado['tendencia_precios'] == 'creciente':
                factor_mercado += 0.05

        factor_total = factor_servicios * factor_mercado

        # Generar justificación enriquecida
        justificacion = self.generar_justificacion_avanzada(
            zona, analisis_servicios, analisis_mercado, necesidades
        )

        return {
            'factor_enriquecimiento': round(factor_total, 3),
            'puntuacion_servicios': round(analisis_servicios['puntuacion_total'] * 100, 1),
            'analisis_servicios': analisis_servicios,
            'analisis_mercado': analisis_mercado,
            'justificacion_adicional': justificacion,
            'servicios_destacados': self.obtener_servicios_destacados_avanzados(analisis_servicios)
        }

    def generar_justificacion_avanzada(self, zona: str, analisis_servicios: Dict,
                                      analisis_mercado: Dict, necesidades: List[str]) -> str:
        """Genera justificación avanzada con datos de mercado"""
        justificacion = ""

        # Análisis de servicios
        if analisis_servicios['puntuacion_total'] >= 0.8:
            justificacion += "Excelente accesibilidad a servicios esenciales. "
        elif analisis_servicios['puntuacion_total'] >= 0.6:
            justificacion += "Buena cobertura de servicios cercanos. "
        elif analisis_servicios['servicios_encontrados'] > 0:
            justificacion += f"Se encontraron {analisis_servicios['servicios_encontrados']} servicios relevantes. "

        # Análisis de mercado
        if analisis_mercado['existe_datos']:
            justificacion += f"Zona con {analisis_mercado['total_proyectos']} proyectos. "

            if analisis_mercado['nivel_demanda'] == 'muy_alta':
                justificacion += "Demanda muy alta en la zona. "
            elif analisis_mercado['nivel_demanda'] == 'alta':
                justificacion += "Alta demanda inmobiliaria. "

            if analisis_mercado['tendencia_precios'] == 'creciente':
                justificacion += "Tendencia de precios creciente. "

            if analisis_mercado['precio_m2_promedio'] > 0:
                justificacion += f"Valor promedio de ${analisis_mercado['precio_m2_promedio']:,.0f}/m². "

        return justificacion.strip()

    def obtener_servicios_destacados_avanzados(self, analisis_servicios: Dict) -> List[Dict[str, Any]]:
        """Obtiene servicios destacados del análisis"""
        servicios_destacados = []

        for necesidad, datos in analisis_servicios['detalle_por_categoria'].items():
            if datos['servicios']:
                # Tomar el servicio mejor calificado para cada necesidad
                mejor_servicio = datos['servicios'][0]
                servicios_destacados.append({
                    'categoria': necesidad,
                    'nombre': mejor_servicio['nombre'],
                    'distancia': mejor_servicio['distancia_estimada'],
                    'nivel': mejor_servicio.get('nivel', 'desconocido')
                })

        return servicios_destacados[:5]  # Máximo 5 servicios destacados

def probar_sistema_avanzado():
    """Prueba el sistema avanzado de enriquecimiento"""
    print("=== PRUEBA DE SISTEMA DE ENRIQUECIMIENTO AVANZADO ===")

    sistema = SistemaEnriquecimientoAvanzado()

    # Propiedad de ejemplo
    propiedad_ejemplo = {
        'id': 'franz_a261494d',
        'nombre': 'Casa en Equipetrol',
        'ubicacion': {
            'zona': 'Equipetrol',
            'direccion': 'Av. Principal y Calle Secundaria'
        }
    }

    # Necesidades de ejemplo
    necesidades = ['seguridad', 'colegios', 'areas verdes', 'supermercado']

    print("1. Enriquecimiento avanzado para familia:")
    resultado = sistema.enriquecer_recomendacion_avanzada(propiedad_ejemplo, necesidades)
    print(f"   - Factor de enriquecimiento: {resultado['factor_enriquecimiento']:.3f}")
    print(f"   - Puntuación de servicios: {resultado['puntuacion_servicios']}%")
    print(f"   - Justificación: {resultado['justificacion_adicional']}")

    if resultado['analisis_mercado']['existe_datos']:
        mercado = resultado['analisis_mercado']
        print(f"   - Análisis de mercado:")
        print(f"     * Proyectos en zona: {mercado['total_proyectos']}")
        print(f"     * Precio m² promedio: ${mercado['precio_m2_promedio']:,.0f}")
        print(f"     * Nivel demanda: {mercado['nivel_demanda']}")
        print(f"     * Tendencia: {mercado['tendencia_precios']}")

    print(f"\n2. Servicios destacados:")
    for serv in resultado['servicios_destacados']:
        print(f"   - {serv['categoria']}: {serv['nombre']} ({serv['distancia']}m)")

    print(f"\n=== SISTEMA AVANZADO LISTO ===")

if __name__ == "__main__":
    probar_sistema_avanzado()