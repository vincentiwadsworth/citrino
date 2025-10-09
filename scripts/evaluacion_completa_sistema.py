#!/usr/bin/env python3
"""
Prueba completa del sistema de recomendación con 10 prospectos ficticios
Analiza el rendimiento real del sistema antes y después de incluir datos municipales
"""

import json
import os
import sys
from typing import Dict, List, Any
from datetime import datetime
import logging
import random

# Agregar el directorio src al path para importar los módulos
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from recommendation_engine import RecommendationEngine
from sistema_enriquecimiento_avanzado import SistemaEnriquecimientoAvanzado

class EvaluadorSistemaRecomendacion:
    """Evaluador completo del sistema de recomendación"""

    def __init__(self):
        self.motor_recomendacion = RecommendationEngine()
        self.sistema_enriquecimiento = SistemaEnriquecimientoAvanzado()
        self.cargar_base_datos()
        self.resultados = []

    def cargar_base_datos(self):
        """Carga la base de datos de propiedades"""
        ruta_bd = os.path.join(os.path.dirname(__file__), '..', 'data', 'bd_final', 'propiedades_limpias.json')
        try:
            with open(ruta_bd, 'r', encoding='utf-8') as f:
                propiedades = json.load(f)
            self.motor_recomendacion.cargar_propiedades(propiedades)
            logger.info(f"Base de datos cargada: {len(propiedades)} propiedades")
        except Exception as e:
            logger.error(f"Error cargando base de datos: {e}")

    def generar_prospectos_ficticios(self) -> List[Dict[str, Any]]:
        """Genera 10 prospectos ficticios con diferentes perfiles"""

        prospectos = [
            {
                "id": "prospecto_001",
                "nombre": "Familia García López",
                "tipo": "familia_joven",
                "presupuesto_max": 200000,
                "presupuesto_min": 120000,
                "necesidades": ["seguridad", "colegios", "areas verdes", "supermercado", "tranquilidad"],
                "preferencias_ubicacion": ["Equipetrol", "Las Palmas", "Zona Norte"],
                "caracteristicas_deseadas": {
                    "habitaciones_min": 3,
                    "banos_min": 2,
                    "superficie_min": 120,
                    "cochera": True,
                    "seguridad_24h": True
                },
                "notas_reunion": "Buscan primera vivienda para su familia con 2 niños. Valoran seguridad y educación. Trabajan ambos en centro."
            },
            {
                "id": "prospecto_002",
                "nombre": "Inversor Martínez",
                "tipo": "inversor",
                "presupuesto_max": 350000,
                "presupuesto_min": 250000,
                "necesidades": ["plusvalía", "rentabilidad", "buen estado", "ubicación estratégica"],
                "preferencias_ubicacion": ["Equipetrol", "Urubó", "Zona Norte"],
                "caracteristicas_deseadas": {
                    "superficie_min": 150,
                    "antiguedad_max": 10,
                    "estado_conservacion": "excelente",
                    "potencial_rentabilidad": True
                },
                "notas_reunion": "Inversor experientado busca propiedades con alto potencial de plusvalía para rental mediano plazo."
            },
            {
                "id": "prospecto_003",
                "nombre": "Profesional Soltero",
                "tipo": "profesional_joven",
                "presupuesto_max": 120000,
                "presupuesto_min": 80000,
                "necesidades": ["acceso facil", "vida urbana", "seguridad", "transporte"],
                "preferencias_ubicacion": ["Centro", "Equipetrol", "2do anillo"],
                "caracteristicas_deseadas": {
                    "habitaciones_min": 1,
                    "banos_min": 1,
                    "superficie_min": 50,
                    "tipo_preferido": "departamento"
                },
                "notas_reunion": "Joven profesional que trabaja en centro. Busca departamento moderno cerca de su trabajo y zonas de entretenimiento."
            },
            {
                "id": "prospecto_004",
                "nombre": "Parejas Jóvenes",
                "tipo": "pareja_sin_hijos",
                "presupuesto_max": 180000,
                "presupuesto_min": 100000,
                "necesidades": ["seguridad", "acceso facil", "supermercado", "restaurantes"],
                "preferencias_ubicacion": ["Equipetrol", "Las Palmas", "3er anillo"],
                "caracteristicas_deseadas": {
                    "habitaciones_min": 2,
                    "banos_min": 1,
                    "superficie_min": 80,
                    "balcon": True,
                    "aire_acondicionado": True
                },
                "notas_reunion": "Pareja recién casada buscan su primera vivienda. Valoran diseño moderno y acceso a servicios."
            },
            {
                "id": "prospecto_005",
                "nombre": "Familia Extendida",
                "tipo": "familia_grande",
                "presupuesto_max": 400000,
                "presupuesto_min": 280000,
                "necesidades": ["espacio", "seguridad", "colegios", "hospital", "tranquilidad"],
                "preferencias_ubicacion": ["Urubó", "Las Palmas", "Zona Norte"],
                "caracteristicas_deseadas": {
                    "habitaciones_min": 5,
                    "banos_min": 3,
                    "superficie_min": 250,
                    "jardin_privado": True,
                    "cochera_multiple": True
                },
                "notas_reunion": "Familia con abuelos y 3 niños. Necesitan espacio amplio y buena ubicación para todos."
            },
            {
                "id": "prospecto_006",
                "nombre": "Ejecutivo Internacional",
                "tipo": "ejecutivo",
                "presupuesto_max": 500000,
                "presupuesto_min": 350000,
                "necesidades": ["lujo", "seguridad", "privacidad", "exclusividad", "buen estado"],
                "preferencias_ubicacion": ["Equipetrol", "Urubó", "Las Palmas"],
                "caracteristicas_deseadas": {
                    "superficie_min": 200,
                    "estado_conservacion": "nuevo",
                    "amenidades_premium": True,
                    "vista_panoramica": True
                },
                "notas_reunion": "Ejecutivo internacional busca residencia de lujo para estancia prolongada en Santa Cruz."
            },
            {
                "id": "prospecto_007",
                "nombre": "Estudiante Universitario",
                "tipo": "estudiante",
                "presupuesto_max": 60000,
                "presupuesto_min": 30000,
                "necesidades": ["economico", "transporte", "acceso facile", "seguridad"],
                "preferencias_ubicacion": ["Centro", "2do anillo", "3er anillo"],
                "caracteristicas_deseadas": {
                    "habitaciones_min": 1,
                    "superficie_min": 30,
                    "tipo_preferido": "departamento",
                    "precio_mensual_max": 800
                },
                "notas_reunion": "Estudiante universitario busca departamento económico cerca de universidades y transporte."
            },
            {
                "id": "prospecto_008",
                "nombre": "Emprendedor Digital",
                "tipo": "profesional_remoto",
                "presupuesto_max": 220000,
                "presupuesto_min": 150000,
                "necesidades": ["espacio_trabajo", "internet", "tranquilidad", "supermercado", "cafe"],
                "preferencias_ubicacion": ["Equipetrol", "Las Palmas", "Zona Norte"],
                "caracteristicas_deseadas": {
                    "habitaciones_min": 2,
                    "superficie_min": 100,
                    "area_trabajo": True,
                    "buena_conexion": True,
                    "jardin": True
                },
                "notas_reunion": "Emprendedor digital trabaja desde casa. Necesita espacio para oficina y buena calidad de vida."
            },
            {
                "id": "prospecto_009",
                "nombre": "Pensionados",
                "tipo": "adultos_mayores",
                "presupuesto_max": 160000,
                "presupuesto_min": 100000,
                "necesidades": ["tranquilidad", "seguridad", "hospital", "farmacia", "acceso facile"],
                "preferencias_ubicacion": ["Equipetrol", "Las Palmas", "3er anillo"],
                "caracteristicas_deseadas": {
                    "habitaciones_min": 2,
                    "banos_min": 1,
                    "superficie_min": 80,
                    "planta_baja": True,
                    "seguridad_24h": True
                },
                "notas_reunion": "Pareja de adultos mayores busca vivienda tranquila y segura cerca de servicios médicos."
            },
            {
                "id": "prospecto_010",
                "nombre": "Familia Monoparental",
                "tipo": "familia_monoparental",
                "presupuesto_max": 140000,
                "presupuesto_min": 90000,
                "necesidades": ["seguridad", "colegios", "supermercado", "transporte", "areas verdes"],
                "preferencias_ubicacion": ["Equipetrol", "2do anillo", "3er anillo"],
                "caracteristicas_deseadas": {
                    "habitaciones_min": 2,
                    "banos_min": 1,
                    "superficie_min": 70,
                    "seguridad_24h": True,
                    "area_ninos": True
                },
                "notas_reunion": "Madre soltera con 2 hijos busca vivienda segura y accesible cerca de colegios y servicios."
            }
        ]

        return prospectos

    def evaluar_prospecto(self, prospecto: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa un prospecto con el sistema de recomendación"""

        print(f"\n{'='*60}")
        print(f"Evaluando prospecto: {prospecto['nombre']}")
        print(f"Tipo: {prospecto['tipo']}")
        print(f"Presupuesto: ${prospecto['presupuesto_min']:,.0f} - ${prospecto['presupuesto_max']:,.0f}")
        print(f"Necesidades: {', '.join(prospecto['necesidades'])}")
        print(f"Notas reunión: {prospecto['notas_reunion']}")

        # Crear perfil para el motor de recomendación
        perfil = {
            'id': prospecto['id'],
            'nombre': prospecto['nombre'],
            'presupuesto': {
                'min': prospecto['presupuesto_min'],
                'max': prospecto['presupuesto_max']
            },
            'composicion_familiar': self.obtener_composicion_familiar(prospecto['tipo']),
            'preferencias': {
                'ubicacion': prospecto['preferencias_ubicacion'][0] if prospecto['preferencias_ubicacion'] else 'Equipetrol',
                'tipo_propiedad': self.obtener_tipo_preferido(prospecto)
            },
            'necesidades': prospecto['necesidades']
        }

        # Generar recomendaciones
        try:
            recomendaciones = self.motor_recomendacion.generar_recomendaciones(
                perfil, limite=10, umbral_minimo=0.3
            )

            # Enriquecer con datos municipales
            if recomendaciones:
                for rec in recomendaciones:
                    propiedad = rec['propiedad']
                    zona = propiedad.get('ubicacion', {}).get('zona', 'Desconocida')

                    # Obtener análisis de mercado
                    analisis_mercado = self.sistema_enriquecimiento.obtener_analisis_mercado_zona(zona)

                    # Obtener enriquecimiento de servicios
                    enriquecimiento = self.sistema_enriquecimiento.enriquecer_recomendacion_avanzada(
                        propiedad, prospecto['necesidades']
                    )

                    # Agregar datos municipales a la recomendación
                    rec['analisis_mercado'] = analisis_mercado
                    rec['enriquecimiento_municipal'] = enriquecimiento

            # Analizar resultados
            analisis = self.analizar_resultados_recomendacion(recomendaciones, prospecto)

            return {
                'prospecto': prospecto,
                'recomendaciones': recomendaciones,
                'perfil': perfil,
                'analisis': analisis
            }

        except Exception as e:
            logger.error(f"Error evaluando prospecto {prospecto['nombre']}: {e}")
            return {
                'prospecto': prospecto,
                'recomendaciones': [],
                'perfil': perfil,
                'analisis': {
                    'total_recomendaciones': 0,
                    'puntuacion_promedio': 0,
                    'presupuesto_ajustado': 0,
                    'cubrio_necesidades': False,
                    'analisis_municipal_incluido': False,
                    'calidad_recomendaciones': [],
                    'mejores_opciones': [],
                    'error': str(e)
                }
            }

    def obtener_composicion_familiar(self, tipo: str) -> Dict[str, Any]:
        """Obtiene composición familiar según el tipo de prospecto"""
        composiciones = {
            'familia_joven': {'adultos': 2, 'ninos': [1], 'adultos_mayores': 0},
            'inversor': {'adultos': 1, 'ninos': [], 'adultos_mayores': 0},
            'profesional_joven': {'adultos': 1, 'ninos': [], 'adultos_mayores': 0},
            'pareja_sin_hijos': {'adultos': 2, 'ninos': [], 'adultos_mayores': 0},
            'familia_grande': {'adultos': 2, 'ninos': [1, 2, 3], 'adultos_mayores': 1},
            'ejecutivo': {'adultos': 2, 'ninos': [1], 'adultos_mayores': 0},
            'estudiante': {'adultos': 1, 'ninos': [], 'adultos_mayores': 0},
            'profesional_remoto': {'adultos': 1, 'ninos': [], 'adultos_mayores': 0},
            'adultos_mayores': {'adultos': 2, 'ninos': [], 'adultos_mayores': 2},
            'familia_monoparental': {'adultos': 1, 'ninos': [1, 2], 'adultos_mayores': 0}
        }
        return composiciones.get(tipo, {'adultos': 1, 'ninos': [], 'adultos_mayores': 0})

    def obtener_tipo_preferido(self, prospecto: Dict[str, Any]) -> str:
        """Obtiene tipo de propiedad preferido según características"""
        if 'tipo_preferido' in prospecto['caracteristicas_deseadas']:
            return prospecto['caracteristicas_deseadas']['tipo_preferido']

        tipo = prospecto['tipo']
        if tipo in ['estudiante', 'profesional_joven']:
            return 'departamento'
        elif tipo in ['familia_grande', 'ejecutivo']:
            return 'casa'
        else:
            return 'cualquiera'

    def analizar_resultados_recomendacion(self, recomendaciones: List[Dict[str, Any]], prospecto: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza los resultados de la recomendación"""

        analisis = {
            'total_recomendaciones': len(recomendaciones),
            'puntuacion_promedio': 0,
            'presupuesto_ajustado': 0,
            'cubrio_necesidades': False,
            'analisis_municipal_incluido': False,
            'calidad_recomendaciones': [],
            'mejores_opciones': [],
            'puntuaciones_detalle': []
        }

        # Analizar cada recomendación
        if recomendaciones:
            puntuaciones = [rec.get('compatibilidad', 0) for rec in recomendaciones]
            analisis['puntuacion_promedio'] = sum(puntuaciones) / len(puntuaciones)
            analisis['puntuaciones_detalle'] = puntuaciones

            # Verificar ajuste de presupuesto
            precios_en_rango = 0
            for rec in recomendaciones:
                precio = rec['propiedad'].get('caracteristicas_principales', {}).get('precio', 0)
                if prospecto['presupuesto_min'] <= precio <= prospecto['presupuesto_max']:
                    precios_en_rango += 1

            analisis['presupuesto_ajustado'] = precios_en_rango / len(recomendaciones) if recomendaciones else 0

            # Verificar si incluye análisis municipal
            con_municipal = sum(1 for rec in recomendaciones if 'analisis_mercado' in rec and rec['analisis_mercado'].get('existe_datos', False))
            analisis['analisis_municipal_incluido'] = con_municipal > 0

            # Analizar cobertura de necesidades (simplificado)
            necesidades_cubiertas = 0
            for necesidad in prospecto['necesidades']:
                for rec in recomendaciones:
                    if 'enriquecimiento_municipal' in rec:
                        servicios = rec['enriquecimiento_municipal'].get('servicios_destacados', [])
                        if any(necesidad in serv.get('categoria', '').lower() for serv in servicios):
                            necesidades_cubiertas += 1
                            break

            analisis['cubrio_necesidades'] = necesidades_cubiertas / len(prospecto['necesidades']) if prospecto['necesidades'] else 0

            # Seleccionar mejores opciones
            analisis['mejores_opciones'] = sorted(recomendaciones,
                                                key=lambda x: x.get('compatibilidad', 0),
                                                reverse=True)[:3]

        return analisis

    def ejecutar_prueba_completa(self) -> Dict[str, Any]:
        """Ejecuta la prueba completa con los 10 prospectos"""

        print("=== PRUEBA COMPLETA DEL SISTEMA DE RECOMENDACIÓN ===")
        print("Evaluando impacto de datos municipales en el rendimiento")

        prospectos = self.generar_prospectos_ficticios()
        resultados_completos = []

        # Evaluar cada prospecto
        for i, prospecto in enumerate(prospectos, 1):
            print(f"\n{'='*80}")
            print(f"PROSPECTO {i}/10: {prospecto['nombre']}")
            print(f"{'='*80}")

            try:
                resultado = self.evaluar_prospecto(prospecto)
                resultados_completos.append(resultado)

                # Mostrar resumen
                analisis = resultado['analisis']
                print(f"\nRESUMEN DE RESULTADOS:")
                print(f"  - Total recomendaciones: {analisis['total_recomendaciones']}")
                print(f"  - Puntuación promedio: {analisis['puntuacion_promedio']:.2f}")
                print(f"  - Ajuste de presupuesto: {analisis['presupuesto_ajustado']*100:.1f}%")
                print(f"  - Cobertura necesidades: {analisis['cubrio_necesidades']*100:.1f}%")
                print(f"  - Incluye análisis municipal: {'SÍ' if analisis['analisis_municipal_incluido'] else 'NO'}")

                if analisis['mejores_opciones']:
                    print(f"\nMEJORES OPCIONES:")
                    for j, opcion in enumerate(analisis['mejores_opciones'][:2], 1):
                        precio = opcion['propiedad'].get('caracteristicas_principales', {}).get('precio', 0)
                        nombre = opcion['propiedad'].get('nombre', 'Sin nombre')
                        puntuacion = opcion.get('compatibilidad', 0)
                        zona = opcion['propiedad'].get('ubicacion', {}).get('zona', 'Desconocida')
                        print(f"  {j}. {nombre} - ${precio:,.0f} (Puntuación: {puntuacion:.2f}) - {zona}")

                        # Mostrar análisis municipal si está disponible
                        if 'analisis_mercado' in opcion and opcion['analisis_mercado'].get('existe_datos', False):
                            mercado = opcion['analisis_mercado']
                            print(f"      * Mercado: {mercado.get('total_proyectos', 0)} proyectos, "
                                  f"${mercado.get('precio_m2_promedio', 0):,.0f}/m², "
                                  f"Demanda: {mercado.get('nivel_demanda', 'desconocida')}")

            except Exception as e:
                logger.error(f"Error evaluando prospecto {prospecto['nombre']}: {e}")
                continue

        # Generar análisis global
        analisis_global = self.generar_analisis_global(resultados_completos)

        return {
            'resultados_individuales': resultados_completos,
            'analisis_global': analisis_global,
            'fecha_evaluacion': datetime.now().isoformat(),
            'total_prospectos_evaluados': len(resultados_completos)
        }

    def generar_analisis_global(self, resultados: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Genera análisis global de todos los resultados"""

        if not resultados:
            return {'error': 'No hay resultados para analizar'}

        # Métricas globales
        total_recomendaciones = sum(r['analisis']['total_recomendaciones'] for r in resultados)
        puntuaciones_promedio = [r['analisis']['puntuacion_promedio'] for r in resultados if r['analisis']['puntuacion_promedio'] > 0]
        ajuste_presupuesto = [r['analisis']['presupuesto_ajustado'] for r in resultados]
        cobertura_necesidades = [r['analisis']['cubrio_necesidades'] for r in resultados]
        analisis_municipal_incluido = sum(1 for r in resultados if r['analisis']['analisis_municipal_incluido'])

        analisis = {
            'metricas_globales': {
                'total_prospectos': len(resultados),
                'total_recomendaciones': total_recomendaciones,
                'promedio_recomendaciones_por_prospecto': total_recomendaciones / len(resultados),
                'puntuacion_promedio_global': sum(puntuaciones_promedio) / len(puntuaciones_promedio) if puntuaciones_promedio else 0,
                'ajuste_presupuesto_promedio': sum(ajuste_presupuesto) / len(ajuste_presupuesto) if ajuste_presupuesto else 0,
                'cobertura_necesidades_promedio': sum(cobertura_necesidades) / len(cobertura_necesidades) if cobertura_necesidades else 0,
                'porcentaje_con_analisis_municipal': (analisis_municipal_incluido / len(resultados)) * 100
            },
            'efectividad_por_tipo': self.analizar_efectividad_por_tipo(resultados),
            'impacto_municipal': self.analizar_impacto_municipal(resultados),
            'recomendaciones_principales': self.extraer_recomendaciones_principales(resultados)
        }

        return analisis

    def analizar_efectividad_por_tipo(self, resultados: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza efectividad por tipo de prospecto"""

        tipos = {}
        for resultado in resultados:
            tipo = resultado['prospecto']['tipo']
            if tipo not in tipos:
                tipos[tipo] = {
                    'count': 0,
                    'puntuaciones': [],
                    'ajustes_presupuesto': [],
                    'coberturas_necesidades': []
                }

            tipos[tipo]['count'] += 1
            tipos[tipo]['puntuaciones'].append(resultado['analisis']['puntuacion_promedio'])
            tipos[tipo]['ajustes_presupuesto'].append(resultado['analisis']['presupuesto_ajustado'])
            tipos[tipo]['coberturas_necesidades'].append(resultado['analisis']['cubrio_necesidades'])

        # Calcular promedios por tipo
        for tipo, datos in tipos.items():
            datos['puntuacion_promedio'] = sum(datos['puntuaciones']) / len(datos['puntuaciones']) if datos['puntuaciones'] else 0
            datos['ajuste_presupuesto_promedio'] = sum(datos['ajustes_presupuesto']) / len(datos['ajustes_presupuesto']) if datos['ajustes_presupuesto'] else 0
            datos['cobertura_necesidades_promedio'] = sum(datos['coberturas_necesidades']) / len(datos['coberturas_necesidades']) if datos['coberturas_necesidades'] else 0

        return tipos

    def analizar_impacto_municipal(self, resultados: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza el impacto específico de los datos municipales"""

        con_municipal = [r for r in resultados if r['analisis']['analisis_municipal_incluido']]
        sin_municipal = [r for r in resultados if not r['analisis']['analisis_municipal_incluido']]

        impacto = {
            'prospectos_con_datos_municipales': len(con_municipal),
            'prospectos_sin_datos_municipales': len(sin_municipal),
            'porcentaje_cobertura_municipal': (len(con_municipal) / len(resultados)) * 100 if resultados else 0
        }

        if con_municipal and sin_municipal:
            # Comparar rendimiento
            puntuaciones_con = [r['analisis']['puntuacion_promedio'] for r in con_municipal if r['analisis']['puntuacion_promedio'] > 0]
            puntuaciones_sin = [r['analisis']['puntuacion_promedio'] for r in sin_municipal if r['analisis']['puntuacion_promedio'] > 0]

            impacto['puntuacion_promedio_con_municipal'] = sum(puntuaciones_con) / len(puntuaciones_con) if puntuaciones_con else 0
            impacto['puntuacion_promedio_sin_municipal'] = sum(puntuaciones_sin) / len(puntuaciones_sin) if puntuaciones_sin else 0
            impacto['mejora_puntuacion_porcentual'] = ((impacto['puntuacion_promedio_con_municipal'] - impacto['puntuacion_promedio_sin_municipal']) / impacto['puntuacion_promedio_sin_municipal'] * 100) if impacto['puntuacion_promedio_sin_municipal'] > 0 else 0

        return impacto

    def extraer_recomendaciones_principales(self, resultados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extrae las recomendaciones principales más frecuentes"""

        todas_las_recomendaciones = []
        for resultado in resultados:
            todas_las_recomendaciones.extend(resultado['analisis']['mejores_opciones'])

        # Agrupar por propiedad y contar frecuencia
        frecuencia = {}
        for rec in todas_las_recomendaciones:
            id_prop = rec.get('id', 'unknown')
            if id_prop not in frecuencia:
                frecuencia[id_prop] = {
                    'propiedad': rec,
                    'frecuencia': 0,
                    'puntuacion_total': 0
                }
            frecuencia[id_prop]['frecuencia'] += 1
            frecuencia[id_prop]['puntuacion_total'] += rec.get('puntuacion_total', 0)

        # Ordenar por frecuencia y puntuación
        top_recomendaciones = sorted(frecuencia.values(),
                                  key=lambda x: (x['frecuencia'], x['puntuacion_total']),
                                  reverse=True)[:10]

        return top_recomendaciones

def main():
    """Función principal para ejecutar la prueba completa"""

    print("=== EVALUACIÓN COMPLETA DEL SISTEMA DE RECOMENDACIÓN CITRINO ===")
    print("Con datos municipales avanzados (8,623 puntos de información)")

    evaluador = EvaluadorSistemaRecomendacion()
    resultados_completos = evaluador.ejecutar_prueba_completa()

    # Mostrar análisis global
    analisis_global = resultados_completos['analisis_global']

    print(f"\n{'='*80}")
    print("ANÁLISIS GLOBAL DE RESULTADOS")
    print(f"{'='*80}")

    metricas = analisis_global['metricas_globales']
    print(f"\nMÉTRICAS GLOBALES:")
    print(f"  - Total prospectos evaluados: {metricas['total_prospectos']}")
    print(f"  - Total recomendaciones generadas: {metricas['total_recomendaciones']}")
    print(f"  - Promedio recomendaciones por prospecto: {metricas['promedio_recomendaciones_por_prospecto']:.1f}")
    print(f"  - Puntuación promedio global: {metricas['puntuacion_promedio_global']:.2f}")
    print(f"  - Ajuste de presupuesto promedio: {metricas['ajuste_presupuesto_promedio']*100:.1f}%")
    print(f"  - Cobertura de necesidades promedio: {metricas['cobertura_necesidades_promedio']*100:.1f}%")
    print(f"  - Porcentaje con análisis municipal: {metricas['porcentaje_con_analisis_municipal']:.1f}%")

    # Impacto municipal
    impacto = analisis_global['impacto_municipal']
    print(f"\nIMPACTO DE DATOS MUNICIPALES:")
    print(f"  - Prospectos con datos municipales: {impacto['prospectos_con_datos_municipales']}")
    print(f"  - Prospectos sin datos municipales: {impacto['prospectos_sin_datos_municipales']}")
    print(f"  - Cobertura municipal: {impacto['porcentaje_cobertura_municipal']:.1f}%")

    if 'puntuacion_promedio_con_municipal' in impacto:
        print(f"  - Puntuación promedio con municipal: {impacto['puntuacion_promedio_con_municipal']:.2f}")
        print(f"  - Puntuación promedio sin municipal: {impacto['puntuacion_promedio_sin_municipal']:.2f}")
        print(f"  - Mejora porcentual: {impacto['mejora_puntuacion_porcentual']:.1f}%")

    # Efectividad por tipo
    print(f"\nEFECTIVIDAD POR TIPO DE PROSPECTO:")
    for tipo, datos in analisis_global['efectividad_por_tipo'].items():
        print(f"  - {tipo}:")
        print(f"    * Puntuación promedio: {datos['puntuacion_promedio']:.2f}")
        print(f"    * Ajuste presupuesto: {datos['ajuste_presupuesto_promedio']*100:.1f}%")
        print(f"    * Cobertura necesidades: {datos['cobertura_necesidades_promedio']*100:.1f}%")
        print(f"    * Cantidad: {datos['count']}")

    # Guardar resultados completos
    ruta_resultados = os.path.join(os.path.dirname(__file__), '..', 'data', 'evaluacion_completa_sistema.json')
    with open(ruta_resultados, 'w', encoding='utf-8') as f:
        json.dump(resultados_completos, f, indent=2, ensure_ascii=False)

    print(f"\nResultados guardados en: {ruta_resultados}")
    print(f"\n{'='*80}")
    print("EVALUACIÓN COMPLETADA")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()