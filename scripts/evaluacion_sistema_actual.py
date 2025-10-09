#!/usr/bin/env python3
"""
Evaluación completa del sistema actual de Citrino con 10 prospectos ficticios
Analiza el rendimiento real y el impacto de los datos municipales
"""

import json
import os
import sys
from typing import Dict, List, Any
from datetime import datetime
import logging

# Agregar los directorios src y scripts al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from recommendation_engine import RecommendationEngine
from sistema_consulta import SistemaConsultaCitrino
from sistema_enriquecimiento_avanzado import SistemaEnriquecimientoAvanzado

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EvaluadorSistemaActual:
    """Evaluador del sistema actual de Citrino"""

    def __init__(self):
        self.sistema_consulta = SistemaConsultaCitrino()
        self.motor_recomendacion = RecommendationEngine()
        self.sistema_enriquecimiento = SistemaEnriquecimientoAvanzado()
        self.cargar_sistemas()

    def cargar_sistemas(self):
        """Carga todos los sistemas necesarios"""
        try:
            # Cargar base de datos principal
            ruta_bd = os.path.join(os.path.dirname(__file__), '..', 'data', 'bd_final', 'propiedades_limpias.json')
            self.sistema_consulta.cargar_base_datos(ruta_bd)
            self.motor_recomendacion.cargar_propiedades(self.sistema_consulta.propiedades)
            logger.info(f"Sistemas cargados: {len(self.sistema_consulta.propiedades)} propiedades")
        except Exception as e:
            logger.error(f"Error cargando sistemas: {e}")

    def generar_prospectos_ficticios(self) -> List[Dict[str, Any]]:
        """Genera 10 prospectos ficticios con diferentes perfiles"""

        return [
            {
                "id": "prospecto_001",
                "nombre": "Familia García López",
                "tipo": "familia_joven",
                "presupuesto_min": 120000,
                "presupuesto_max": 200000,
                "adultos": 2,
                "ninos": [1],
                "adultos_mayores": 0,
                "zona_preferida": "Equipetrol",
                "tipo_propiedad": "cualquiera",
                "necesidades": ["seguridad", "colegios", "areas verdes", "supermercado"],
                "notas_reunion": "Familia joven con 1 niño busca primera vivienda. Valoran seguridad y educación. Trabajan ambos en centro."
            },
            {
                "id": "prospecto_002",
                "nombre": "Inversor Martínez",
                "tipo": "inversor",
                "presupuesto_min": 250000,
                "presupuesto_max": 350000,
                "adultos": 1,
                "ninos": [],
                "adultos_mayores": 0,
                "zona_preferida": "Equipetrol",
                "tipo_propiedad": "cualquiera",
                "necesidades": ["plusvalía", "rentabilidad", "buen estado"],
                "notas_reunion": "Inversor experientado busca propiedades con alto potencial de plusvalía para rental mediano plazo."
            },
            {
                "id": "prospecto_003",
                "nombre": "Profesional Soltero",
                "tipo": "profesional_joven",
                "presupuesto_min": 80000,
                "presupuesto_max": 120000,
                "adultos": 1,
                "ninos": [],
                "adultos_mayores": 0,
                "zona_preferida": "Centro",
                "tipo_propiedad": "departamento",
                "necesidades": ["acceso facil", "vida urbana", "seguridad"],
                "notas_reunion": "Joven profesional que trabaja en centro. Busca departamento moderno cerca de su trabajo."
            },
            {
                "id": "prospecto_004",
                "nombre": "Parejas Jóvenes",
                "tipo": "pareja_sin_hijos",
                "presupuesto_min": 100000,
                "presupuesto_max": 180000,
                "adultos": 2,
                "ninos": [],
                "adultos_mayores": 0,
                "zona_preferida": "Equipetrol",
                "tipo_propiedad": "departamento",
                "necesidades": ["seguridad", "acceso facil", "supermercado"],
                "notas_reunion": "Pareja recién casada buscan su primera vivienda. Valoran diseño moderno y acceso a servicios."
            },
            {
                "id": "prospecto_005",
                "nombre": "Familia Extendida",
                "tipo": "familia_grande",
                "presupuesto_min": 280000,
                "presupuesto_max": 400000,
                "adultos": 2,
                "ninos": [1, 2, 3],
                "adultos_mayores": 1,
                "zona_preferida": "Urubó",
                "tipo_propiedad": "casa",
                "necesidades": ["espacio", "seguridad", "colegios", "hospital"],
                "notas_reunion": "Familia con abuelos y 3 niños. Necesitan espacio amplio y buena ubicación para todos."
            },
            {
                "id": "prospecto_006",
                "nombre": "Ejecutivo Internacional",
                "tipo": "ejecutivo",
                "presupuesto_min": 350000,
                "presupuesto_max": 500000,
                "adultos": 2,
                "ninos": [1],
                "adultos_mayores": 0,
                "zona_preferida": "Equipetrol",
                "tipo_propiedad": "casa",
                "necesidades": ["lujo", "seguridad", "privacidad", "exclusividad"],
                "notas_reunion": "Ejecutivo internacional busca residencia de lujo para estancia prolongada en Santa Cruz."
            },
            {
                "id": "prospecto_007",
                "nombre": "Estudiante Universitario",
                "tipo": "estudiante",
                "presupuesto_min": 30000,
                "presupuesto_max": 60000,
                "adultos": 1,
                "ninos": [],
                "adultos_mayores": 0,
                "zona_preferida": "Centro",
                "tipo_propiedad": "departamento",
                "necesidades": ["economico", "transporte", "acceso facile"],
                "notas_reunion": "Estudiante universitario busca departamento económico cerca de universidades y transporte."
            },
            {
                "id": "prospecto_008",
                "nombre": "Emprendedor Digital",
                "tipo": "profesional_remoto",
                "presupuesto_min": 150000,
                "presupuesto_max": 220000,
                "adultos": 1,
                "ninos": [],
                "adultos_mayores": 0,
                "zona_preferida": "Las Palmas",
                "tipo_propiedad": "casa",
                "necesidades": ["espacio_trabajo", "tranquilidad", "supermercado", "cafe"],
                "notas_reunion": "Emprendedor digital trabaja desde casa. Necesita espacio para oficina y buena calidad de vida."
            },
            {
                "id": "prospecto_009",
                "nombre": "Pensionados",
                "tipo": "adultos_mayores",
                "presupuesto_min": 100000,
                "presupuesto_max": 160000,
                "adultos": 2,
                "ninos": [],
                "adultos_mayores": 2,
                "zona_preferida": "Equipetrol",
                "tipo_propiedad": "departamento",
                "necesidades": ["tranquilidad", "seguridad", "hospital", "farmacia"],
                "notas_reunion": "Pareja de adultos mayores busca vivienda tranquila y segura cerca de servicios médicos."
            },
            {
                "id": "prospecto_010",
                "nombre": "Familia Monoparental",
                "tipo": "familia_monoparental",
                "presupuesto_min": 90000,
                "presupuesto_max": 140000,
                "adultos": 1,
                "ninos": [1, 2],
                "adultos_mayores": 0,
                "zona_preferida": "2do anillo",
                "tipo_propiedad": "departamento",
                "necesidades": ["seguridad", "colegios", "supermercado", "transporte"],
                "notas_reunion": "Madre soltera con 2 hijos busca vivienda segura y accesible cerca de colegios y servicios."
            }
        ]

    def evaluar_prospecto(self, prospecto: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa un prospecto con el sistema actual"""

        print(f"\n{'='*60}")
        print(f"Evaluando prospecto: {prospecto['nombre']}")
        print(f"Tipo: {prospecto['tipo']}")
        print(f"Presupuesto: ${prospecto['presupuesto_min']:,.0f} - ${prospecto['presupuesto_max']:,.0f}")
        print(f"Necesidades: {', '.join(prospecto['necesidades'])}")
        print(f"Notas reunión: {prospecto['notas_reunion']}")

        try:
            # Generar recomendaciones usando el motor actual
            perfil = {
                'id': prospecto['id'],
                'nombre': prospecto['nombre'],
                'presupuesto': {
                    'min': prospecto['presupuesto_min'],
                    'max': prospecto['presupuesto_max']
                },
                'composicion_familiar': {
                    'adultos': prospecto['adultos'],
                    'ninos': prospecto['ninos'],
                    'adultos_mayores': prospecto['adultos_mayores']
                },
                'preferencias': {
                    'ubicacion': prospecto['zona_preferida'],
                    'tipo_propiedad': prospecto['tipo_propiedad']
                },
                'necesidades': prospecto['necesidades']
            }

            recomendaciones = self.motor_recomendacion.generar_recomendaciones(
                perfil, limite=10, umbral_minimo=0.3
            )

            # Enriquecer con datos municipales si hay recomendaciones
            if recomendaciones:
                for rec in recomendaciones:
                    propiedad = rec['propiedad']
                    zona = propiedad.get('ubicacion', {}).get('zona', 'Desconocida')

                    # Obtener análisis de mercado del sistema avanzado
                    analisis_mercado = self.sistema_enriquecimiento.obtener_analisis_mercado_zona(zona)

                    # Enriquecer la recomendación con datos municipales
                    rec['datos_municipales'] = {
                        'analisis_mercado': analisis_mercado,
                        'tiene_datos_municipales': analisis_mercado.get('existe_datos', False)
                    }

            # Analizar resultados
            analisis = self.analizar_resultados_recomendacion(recomendaciones, prospecto)

            return {
                'prospecto': prospecto,
                'perfil': perfil,
                'recomendaciones': recomendaciones,
                'analisis': analisis,
                'exito': len(recomendaciones) > 0
            }

        except Exception as e:
            logger.error(f"Error evaluando prospecto {prospecto['nombre']}: {e}")
            return {
                'prospecto': prospecto,
                'perfil': perfil,
                'recomendaciones': [],
                'analisis': {
                    'total_recomendaciones': 0,
                    'puntuacion_promedio': 0,
                    'presupuesto_ajustado': 0,
                    'cubrio_necesidades': False,
                    'analisis_municipal_incluido': False,
                    'error': str(e)
                },
                'exito': False
            }

    def analizar_resultados_recomendacion(self, recomendaciones: List[Dict[str, Any]], prospecto: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza los resultados de la recomendación"""

        analisis = {
            'total_recomendaciones': len(recomendaciones),
            'puntuacion_promedio': 0,
            'presupuesto_ajustado': 0,
            'cubrio_necesidades': False,
            'analisis_municipal_incluido': False,
            'mejores_opciones': [],
            'tiene_datos_municipales': False
        }

        if recomendaciones:
            # Calcular puntuación promedio
            puntuaciones = [rec.get('compatibilidad', 0) for rec in recomendaciones]
            analisis['puntuacion_promedio'] = sum(puntuaciones) / len(puntuaciones)

            # Verificar ajuste de presupuesto
            precios_en_rango = 0
            for rec in recomendaciones:
                precio = rec['propiedad'].get('caracteristicas_principales', {}).get('precio', 0)
                if prospecto['presupuesto_min'] <= precio <= prospecto['presupuesto_max']:
                    precios_en_rango += 1

            analisis['presupuesto_ajustado'] = precios_en_rango / len(recomendaciones) if recomendaciones else 0

            # Verificar si tiene datos municipales
            con_municipal = sum(1 for rec in recomendaciones
                              if rec.get('datos_municipales', {}).get('tiene_datos_municipales', False))
            analisis['analisis_municipal_incluido'] = con_municipal > 0
            analisis['tiene_datos_municipales'] = con_municipal > 0

            # Analizar cobertura de necesidades (basado en justificaciones)
            necesidades_cubiertas = set()
            for rec in recomendaciones:
                justificacion = rec.get('justificacion', '').lower()
                for necesidad in prospecto['necesidades']:
                    if any(palabra in justificacion for palabra in necesidad.split()):
                        necesidades_cubiertas.add(necesidad)

            analisis['cubrio_necesidades'] = len(necesidades_cubiertas) / len(prospecto['necesidades']) if prospecto['necesidades'] else 0

            # Seleccionar mejores opciones
            analisis['mejores_opciones'] = sorted(recomendaciones,
                                                key=lambda x: x.get('compatibilidad', 0),
                                                reverse=True)[:3]

        return analisis

    def ejecutar_prueba_completa(self) -> Dict[str, Any]:
        """Ejecuta la prueba completa con los 10 prospectos"""

        print("=== EVALUACIÓN COMPLETA DEL SISTEMA ACTUAL DE CITRINO ===")
        print("Analizando impacto de datos municipales avanzados (8,623 puntos)")

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
                print(f"  - Tiene datos municipales: {'SÍ' if analisis['tiene_datos_municipales'] else 'NO'}")

                if analisis['mejores_opciones']:
                    print(f"\nMEJORES OPCIONES:")
                    for j, opcion in enumerate(analisis['mejores_opciones'][:2], 1):
                        precio = opcion['propiedad'].get('caracteristicas_principales', {}).get('precio', 0)
                        nombre = opcion['propiedad'].get('nombre', 'Sin nombre')
                        puntuacion = opcion.get('compatibilidad', 0)
                        zona = opcion['propiedad'].get('ubicacion', {}).get('zona', 'Desconocida')
                        print(f"  {j}. {nombre} - ${precio:,.0f} (Puntuación: {puntuacion:.2f}) - {zona}")

                        # Mostrar datos municipales si están disponibles
                        if opcion.get('datos_municipales', {}).get('tiene_datos_municipales', False):
                            mercado = opcion['datos_municipales']['analisis_mercado']
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
        puntuaciones = [r['analisis']['puntuacion_promedio'] for r in resultados if r['analisis']['puntuacion_promedio'] > 0]
        ajuste_presupuesto = [r['analisis']['presupuesto_ajustado'] for r in resultados]
        cobertura_necesidades = [r['analisis']['cubrio_necesidades'] for r in resultados]
        con_datos_municipales = sum(1 for r in resultados if r['analisis']['tiene_datos_municipales'])
        exitosos = sum(1 for r in resultados if r['exito'])

        analisis = {
            'metricas_globales': {
                'total_prospectos': len(resultados),
                'total_recomendaciones': total_recomendaciones,
                'promedio_recomendaciones_por_prospecto': total_recomendaciones / len(resultados),
                'puntuacion_promedio_global': sum(puntuaciones) / len(puntuaciones) if puntuaciones else 0,
                'ajuste_presupuesto_promedio': sum(ajuste_presupuesto) / len(ajuste_presupuesto) if ajuste_presupuesto else 0,
                'cobertura_necesidades_promedio': sum(cobertura_necesidades) / len(cobertura_necesidades) if cobertura_necesidades else 0,
                'tasa_exito_global': (exitosos / len(resultados)) * 100,
                'porcentaje_con_datos_municipales': (con_datos_municipales / len(resultados)) * 100
            },
            'efectividad_por_tipo': self.analizar_efectividad_por_tipo(resultados),
            'impacto_municipal': self.analizar_impacto_municipal(resultados),
            'top_propiedades_recomendadas': self.extraer_top_propiedades(resultados)
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
                    'exitosos': 0,
                    'puntuaciones': [],
                    'ajustes_presupuesto': [],
                    'coberturas_necesidades': [],
                    'con_municipal': 0
                }

            tipos[tipo]['count'] += 1
            if resultado['exito']:
                tipos[tipo]['exitosos'] += 1

            tipos[tipo]['puntuaciones'].append(resultado['analisis']['puntuacion_promedio'])
            tipos[tipo]['ajustes_presupuesto'].append(resultado['analisis']['presupuesto_ajustado'])
            tipos[tipo]['coberturas_necesidades'].append(resultado['analisis']['cubrio_necesidades'])
            if resultado['analisis']['tiene_datos_municipales']:
                tipos[tipo]['con_municipal'] += 1

        # Calcular promedios por tipo
        for tipo, datos in tipos.items():
            datos['tasa_exito'] = (datos['exitosos'] / datos['count']) * 100
            datos['puntuacion_promedio'] = sum(datos['puntuaciones']) / len(datos['puntuaciones']) if datos['puntuaciones'] else 0
            datos['ajuste_presupuesto_promedio'] = sum(datos['ajustes_presupuesto']) / len(datos['ajustes_presupuesto']) if datos['ajustes_presupuesto'] else 0
            datos['cobertura_necesidades_promedio'] = sum(datos['coberturas_necesidades']) / len(datos['coberturas_necesidades']) if datos['coberturas_necesidades'] else 0
            datos['porcentaje_con_municipal'] = (datos['con_municipal'] / datos['count']) * 100

        return tipos

    def analizar_impacto_municipal(self, resultados: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza el impacto específico de los datos municipales"""

        con_municipal = [r for r in resultados if r['analisis']['tiene_datos_municipales']]
        sin_municipal = [r for r in resultados if not r['analisis']['tiene_datos_municipales']]

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

    def extraer_top_propiedades(self, resultados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extrae las propiedades más recomendadas"""

        todas_las_recomendaciones = []
        for resultado in resultados:
            todas_las_recomendaciones.extend(resultado['recomendaciones'])

        # Agrupar por propiedad y contar frecuencia
        frecuencia = {}
        for rec in todas_las_recomendaciones:
            id_prop = rec['propiedad'].get('id', 'unknown')
            if id_prop not in frecuencia:
                frecuencia[id_prop] = {
                    'propiedad': rec['propiedad'],
                    'frecuencia': 0,
                    'puntuacion_total': 0,
                    'compatibilidad_promedio': 0
                }
            frecuencia[id_prop]['frecuencia'] += 1
            frecuencia[id_prop]['puntuacion_total'] += rec.get('compatibilidad', 0)

        # Calcular compatibilidad promedio
        for id_prop, datos in frecuencia.items():
            datos['compatibilidad_promedio'] = datos['puntuacion_total'] / datos['frecuencia']

        # Ordenar por frecuencia y compatibilidad
        top_propiedades = sorted(frecuencia.values(),
                                key=lambda x: (x['frecuencia'], x['compatibilidad_promedio']),
                                reverse=True)[:10]

        return top_propiedades

def main():
    """Función principal para ejecutar la prueba completa"""

    print("=== EVALUACIÓN COMPLETA DEL SISTEMA DE RECOMENDACIÓN CITRINO ===")
    print("Con datos municipales avanzados (8,623 puntos de información)")

    evaluador = EvaluadorSistemaActual()
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
    print(f"  - Tasa de éxito global: {metricas['tasa_exito_global']:.1f}%")
    print(f"  - Porcentaje con datos municipales: {metricas['porcentaje_con_datos_municipales']:.1f}%")

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
        print(f"    * Tasa éxito: {datos['tasa_exito']:.1f}% ({datos['exitosos']}/{datos['count']})")
        print(f"    * Puntuación promedio: {datos['puntuacion_promedio']:.2f}")
        print(f"    * Ajuste presupuesto: {datos['ajuste_presupuesto_promedio']*100:.1f}%")
        print(f"    * Cobertura necesidades: {datos['cobertura_necesidades_promedio']*100:.1f}%")
        print(f"    * Con datos municipales: {datos['porcentaje_con_municipal']:.1f}%")

    # Top propiedades
    print(f"\nTOP 5 PROPIEDADES MÁS RECOMENDADAS:")
    for i, prop in enumerate(analisis_global['top_propiedades_recomendadas'][:5], 1):
        propiedad = prop['propiedad']
        precio = propiedad.get('caracteristicas_principales', {}).get('precio', 0)
        nombre = propiedad.get('nombre', 'Sin nombre')
        zona = propiedad.get('ubicacion', {}).get('zona', 'Desconocida')
        print(f"  {i}. {nombre} - ${precio:,.0f} - {zona}")
        print(f"     Recomendado {prop['frecuencia']} veces, compatibilidad promedio: {prop['compatibilidad_promedio']:.2f}")

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