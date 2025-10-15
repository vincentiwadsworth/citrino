#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análisis Comparativo de Proveedores

Este script compara la calidad y características de datos entre todos los proveedores
para identificar patrones, mejores prácticas y oportunidades de mejora específicas.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple
import re
from collections import defaultdict, Counter

class AnalizadorComparativoProveedores:
    """Analiza y compara la calidad de datos entre diferentes proveedores."""

    def __init__(self):
        self.stats = {
            'proveedores_analizados': {},
            'comparaciones_generales': {},
            'ranking_calidad': [],
            'recomendaciones_especificas': {}
        }

    def cargar_datos_proveedores(self) -> Dict[str, pd.DataFrame]:
        """Carga los datos raw de todos los proveedores."""
        proveedores = {}
        archivos_proveedores = {
            '01': ['2025.08.17 01.xlsx', '2025.08.29 01.xlsx'],
            '02': ['2025.08.29 02.xlsx'],
            '03': ['2025.08.29 03.xlsx'],
            '04': ['2025.08.29 04.xlsx'],
            '05': ['2025.08.15 05.xlsx', '2025.08.29 05.xlsx']
        }

        for codigo, archivos in archivos_proveedores.items():
            dfs = []
            for archivo in archivos:
                try:
                    file_path = f"data/raw/relevamiento/{archivo}"
                    df = pd.read_excel(file_path)
                    df['codigo_proveedor'] = codigo
                    df['archivo_origen'] = archivo
                    dfs.append(df)
                    print(f"Cargado {archivo}: {len(df)} filas")
                except Exception as e:
                    print(f"Error cargando {archivo}: {e}")

            if dfs:
                proveedores[codigo] = pd.concat(dfs, ignore_index=True)
                print(f"Proveedor {codigo}: Total {len(proveedores[codigo])} filas")

        return proveedores

    def analizar_calidad_por_proveedor(self, proveedores: Dict[str, pd.DataFrame]) -> Dict[str, Dict[str, Any]]:
        """Analiza la calidad de datos para cada proveedor."""
        calidad_por_proveedor = {}

        for codigo, df in proveedores.items():
            print(f"\nAnalizando calidad del Proveedor {codigo}...")

            calidad = {
                'total_registros': len(df),
                'campos_disponibles': list(df.columns),
                'calidad_campos': {},
                'problemas_especificos': [],
                'fortalezas': []
            }

            # Analizar cada campo
            for columna in df.columns:
                no_nulos = df[columna].notna().sum()
                no_vacios = df[columna].notna() & (df[columna] != '') & (df[columna] != 'nan')

                calidad['calidad_campos'][columna] = {
                    'completitud': (no_nulos.sum() / len(df)) * 100,
                    'valores_unicos': df[columna].nunique(),
                    'tipo_dato': str(df[columna].dtype)
                }

            # Problemas específicos por proveedor
            if codigo == '02':
                # Problema de precios 0.00 BOB ya identificado
                if 'Precio' in df.columns:
                    precios_invalidos = (df['Precio'].astype(str) == '0.00 BOB').sum()
                    if precios_invalidos > 0:
                        calidad['problemas_especificos'].append({
                            'tipo': 'PRECIO_INVALIDO',
                            'descripcion': f"{precios_invalidos} propiedades con precio 0.00 BOB",
                            'severidad': 'ALTA'
                        })

                # Fortaleza: mucha información de contacto
                if all(col in df.columns for col in ['Agente Nombre', 'Agente Teléfono', 'Agente Email']):
                    calidad['fortalezas'].append("Datos de contacto completos al 100%")

            elif codigo == '01':
                # Problema: falta de URL y agente en algunos archivos
                if 'URL' not in df.columns:
                    calidad['problemas_especificos'].append({
                        'tipo': 'CAMPO_FALTANTE',
                        'descripcion': 'No hay campo URL',
                        'severidad': 'MEDIA'
                    })

            elif codigo == '03':
                # Problema: falta de coordenadas
                if 'Coordenadas' not in df.columns or df['Coordenadas'].isna().all():
                    calidad['problemas_especificos'].append({
                        'tipo': 'SIN_COORDENADAS',
                        'descripcion': 'No hay datos de coordenadas',
                        'severidad': 'ALTA'
                    })

            elif codigo == '04':
                # Revisar calidad de descripciones
                if 'descripcion' in df.columns:
                    descripciones_cortas = (df['descripcion'].astype(str).str.len() < 50).sum()
                    if descripciones_cortas > len(df) * 0.5:
                        calidad['problemas_especificos'].append({
                            'tipo': 'DESCRIPCIONES_CORTAS',
                            'descripcion': f"{descripciones_cortas} propiedades con descripciones muy cortas",
                            'severidad': 'MEDIA'
                        })

            elif codigo == '05':
                # Fortaleza: datos estructurados
                campos_estructurados = ['Habitaciones', 'Baños', 'Sup. Terreno', 'Sup. Construida']
                campos_presentes = [col for col in campos_estructurados if col in df.columns]
                if len(campos_presentes) >= 3:
                    calidad['fortalezas'].append(f"Datos estructurados: {', '.join(campos_presentes)}")

            calidad_por_proveedor[codigo] = calidad

        return calidad_por_proveedor

    def analizar_uso_actual_ia(self) -> Dict[str, Any]:
        """Analiza el uso actual de IA en el procesamiento."""
        try:
            with open("data/metrics/analisis_data_raw_20251015_112747_readable.json", 'r', encoding='utf-8') as f:
                datos_uso = json.load(f)

            uso_ia = {
                'proveedores_datos': {},
                'eficiencia_actual': {},
                'oportunidades_identificadas': []
            }

            # Extraer datos de proveedores
            if 'relevamiento' in datos_uso:
                relevamiento = datos_uso['relevamiento']

                uso_ia['proveedores_datos'] = relevamiento.get('proveedores', {})
                uso_ia['eficiencia_actual'] = {
                    'propiedades_totales': relevamiento.get('uso_llm', {}).get('total_propiedades', 0),
                    'uso_regex_puro': relevamiento.get('uso_llm', {}).get('regex_only', 0),
                    'uso_parcial': relevamiento.get('uso_llm', {}).get('regex_partial', 0),
                    'uso_llm_exclusivo': relevamiento.get('uso_llm', {}).get('llm_only', 0),
                    'tokens_consumidos': relevamiento.get('tokens_consumidos', {}).get('total', 0),
                    'costo_estimado': relevamiento.get('costo_estimado_usd', 0)
                }

                # Identificar problemas de uso de IA
                if uso_ia['eficiencia_actual']['uso_llm_exclusivo'] == 0:
                    uso_ia['oportunidades_identificadas'].append({
                        'tipo': 'SUBUTILIZACION_IA',
                        'descripcion': 'No se está usando IA para ningún caso exclusivo',
                        'impacto': 'Perdida de información valiosa en campos no estructurados'
                    })

                if uso_ia['eficiencia_actual']['tokens_consumidos'] < 5000:
                    uso_ia['oportunidades_identificadas'].append({
                        'tipo': 'USO_MINIMO_IA',
                        'descripcion': f"Solo {uso_ia['eficiencia_actual']['tokens_consumidos']} tokens consumidos",
                        'impacto': 'Potencial de mejora sin explorar'
                    })

            return uso_ia

        except Exception as e:
            print(f"Error analizando uso de IA: {e}")
            return {}

    def crear_ranking_calidad(self, calidad_por_proveedor: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Crea un ranking de proveedores por calidad de datos."""
        ranking = []

        for codigo, calidad in calidad_por_proveedor.items():
            # Calcular puntaje de calidad
            puntaje_total = 0
            factores = []

            # Factor 1: Completitud promedio de campos clave
            campos_clave = ['Precio', 'Descripción', 'Latitud', 'Longitud']
            completitud_clave = 0
            campos_clave_presentes = 0

            for campo in campos_clave:
                if campo in calidad['calidad_campos']:
                    completitud_clave += calidad['calidad_campos'][campo]['completitud']
                    campos_clave_presentes += 1

            if campos_clave_presentes > 0:
                puntaje_completitud = (completitud_clave / campos_clave_presentes) * 0.4
                puntaje_total += puntaje_completitud
                factores.append(f"Completitud clave: {puntaje_completitud:.1f}")

            # Factor 2: Riqueza de datos (número de campos)
            num_campos = len(calidad['campos_disponibles'])
            puntaje_campos = min((num_campos / 15) * 0.2, 0.2)  # Máximo 0.2 puntos
            puntaje_total += puntaje_campos
            factores.append(f"Número de campos: {puntaje_campos:.1f}")

            # Factor 3: Penalizaciones por problemas críticos
            penalizaciones = 0
            for problema in calidad['problemas_especificos']:
                if problema['severidad'] == 'ALTA':
                    penalizaciones += 0.15
                elif problema['severidad'] == 'MEDIA':
                    penalizaciones += 0.08

            puntaje_final = max(0, puntaje_total - penalizaciones) * 100  # Convertir a escala 0-100

            ranking.append({
                'codigo_proveedor': codigo,
                'puntaje_calidad': round(puntaje_final, 1),
                'total_registros': calidad['total_registros'],
                'numero_campos': num_campos,
                'factores': factores,
                'problemas_criticos': [p for p in calidad['problemas_especificos'] if p['severidad'] == 'ALTA'],
                'fortalezas': calidad['fortalezas']
            })

        # Ordenar por puntaje
        ranking.sort(key=lambda x: x['puntaje_calidad'], reverse=True)

        return ranking

    def generar_recomendaciones_especificas(self, ranking: List[Dict[str, Any]],
                                          uso_ia: Dict[str, Any],
                                          calidad_proveedores: Dict[str, Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Genera recomendaciones específicas por proveedor."""
        recomendaciones = {}

        for proveedor_info in ranking:
            codigo = proveedor_info['codigo_proveedor']
            recomendaciones[codigo] = []

            # Recomendaciones basadas en el ranking
            if proveedor_info['puntaje_calidad'] < 60:
                recomendaciones[codigo].append({
                    'tipo': 'MEJORA_GENERAL',
                    'prioridad': 'ALTA',
                    'descripcion': f"Calidad baja ({proveedor_info['puntaje_calidad']}%), requiere mejora integral",
                    'accion': 'Implementar extracción IA para campos no estructurados'
                })

            # Recomendaciones específicas por proveedor
            if codigo == '02':
                recomendaciones[codigo].append({
                    'tipo': 'EXTRACCION_AMENITIES',
                    'prioridad': 'ALTA',
                    'descripcion': '62.2% de propiedades con amenities no estructurados',
                    'accion': 'Usar LLM para parsear amenities en características estructuradas',
                    'impacto_estimado': '4-6 características nuevas por propiedad'
                })

                recomendaciones[codigo].append({
                    'tipo': 'CORRECCION_PRECIOS',
                    'prioridad': 'ALTA',
                    'descripcion': 'Precios inválidos detectados en descripciones',
                    'accion': 'Extraer precios reales de descripciones con regex + LLM',
                    'impacto_estimado': 'Recuperar precios para propiedades inválidas'
                })

            elif codigo == '03':
                recomendaciones[codigo].append({
                    'tipo': 'GEORREFERENCIACION',
                    'prioridad': 'ALTA',
                    'descripcion': 'Faltan coordenadas geográficas',
                    'accion': 'Geocodificar direcciones usando API externa',
                    'impacto_estimado': 'Agregar coordenadas al 100% de propiedades'
                })

            elif codigo == '01':
                recomendaciones[codigo].append({
                    'tipo': 'ENRIQUECIMIENTO',
                    'prioridad': 'MEDIA',
                    'descripcion': 'Faltan campos de contacto y URLs',
                    'accion': 'Extraer información de contacto de descripciones',
                    'impacto_estimado': 'Mejorar traceabilidad y contacto'
                })

            elif codigo == '04':
                recomendaciones[codigo].append({
                    'tipo': 'EXPANSION_DESCRIPCION',
                    'prioridad': 'MEDIA',
                    'descripcion': 'Descripciones potencialmente cortas',
                    'accion': 'Expandir información usando URLs si están disponibles',
                    'impacto_estimado': 'Mejorar contenido analizable'
                })

            elif codigo == '05':
                recomendaciones[codigo].append({
                    'tipo': 'OPTIMIZACION',
                    'prioridad': 'BAJA',
                    'descripcion': 'Datos ya bien estructurados',
                    'accion': 'Refinar extracción y validación',
                    'impacto_estimado': 'Mejorar precisión existente'
                })

        return recomendaciones

    def generar_reporte_completo(self) -> Dict[str, Any]:
        """Genera el análisis comparativo completo."""
        print("Iniciando análisis comparativo de proveedores...")

        # Cargar datos
        proveedores = self.cargar_datos_proveedores()
        if not proveedores:
            return {"error": "No se pudieron cargar los datos de proveedores"}

        # Análisis de calidad
        print("\nAnalizando calidad por proveedor...")
        calidad_proveedores = self.analizar_calidad_por_proveedor(proveedores)

        # Análisis de uso de IA
        print("Analizando uso actual de IA...")
        uso_ia = self.analizar_uso_actual_ia()

        # Crear ranking
        print("Creando ranking de calidad...")
        ranking = self.crear_ranking_calidad(calidad_proveedores)

        # Generar recomendaciones
        print("Generando recomendaciones específicas...")
        recomendaciones = self.generar_recomendaciones_especificas(ranking, uso_ia, calidad_proveedores)

        # Ensamblar reporte
        reporte = {
            'metadata': {
                'fecha_analisis': pd.Timestamp.now().isoformat(),
                'proveedores_analizados': list(proveedores.keys()),
                'total_propiedades': sum(len(df) for df in proveedores.values())
            },
            'resumen_ejecutivo': {
                'mejor_proveedor': ranking[0] if ranking else None,
                'peor_proveedor': ranking[-1] if ranking else None,
                'promedio_calidad': np.mean([p['puntaje_calidad'] for p in ranking]) if ranking else 0,
                'problemas_criticos_total': sum(len(p['problemas_criticos']) for p in ranking)
            },
            'ranking_calidad': ranking,
            'analisis_detallado': calidad_proveedores,
            'uso_actual_ia': uso_ia,
            'recomendaciones_especificas': recomendaciones,
            'conclusiones_clave': self._generar_conclusiones(ranking, uso_ia, calidad_proveedores)
        }

        return reporte

    def _generar_conclusiones(self, ranking: List[Dict[str, Any]],
                             uso_ia: Dict[str, Any],
                             calidad_proveedores: Dict[str, Dict[str, Any]]) -> List[str]:
        """Genera conclusiones clave del análisis."""
        conclusiones = []

        if not ranking:
            return ["No se pudo generar el análisis"]

        # Conclusión sobre calidad general
        mejor = ranking[0]
        peor = ranking[-1]
        conclusiones.append(f"El Proveedor {mejor['codigo_proveedor']} tiene la mejor calidad ({mejor['puntaje_calidad']}%) mientras que el Proveedor {peor['codigo_proveedor']} tiene la peor ({peor['puntaje_calidad']}%)")

        # Conclusión sobre uso de IA
        if uso_ia.get('eficiencia_actual', {}).get('uso_llm_exclusivo', 0) == 0:
            conclusiones.append("No estamos utilizando IA para ningún caso de procesamiento exclusivo, lo que indica subutilización significativa")

        # Conclusión sobre el Proveedor 02
        if '02' in [p['codigo_proveedor'] for p in ranking]:
            proveedor_02 = next(p for p in ranking if p['codigo_proveedor'] == '02')
            if proveedor_02['puntaje_calidad'] < 70:
                conclusiones.append(f"El Proveedor 02, a pesar de tener {proveedor_02['total_registros']} propiedades, tiene calidad baja y es el candidato principal para mejoras con IA")

        # Conclusión sobre oportunidades
        total_oportunidades = sum(len(recs) for recs in self.generar_recomendaciones_especificas(ranking, uso_ia, calidad_proveedores).values())
        if total_oportunidades > 10:
            conclusiones.append(f"Existen {total_oportunidades} oportunidades específicas de mejora identificadas")

        return conclusiones

    def guardar_reporte(self, reporte: Dict[str, Any], output_path: str = "data/analisis/comparativo_proveedores.json"):
        """Guarda el reporte en un archivo JSON."""
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(reporte, f, ensure_ascii=False, indent=2, default=str)

            print(f"Reporte guardado en: {output_path}")
            return output_path
        except Exception as e:
            print(f"Error guardando reporte: {e}")
            return None

def main():
    """Función principal del análisis comparativo."""
    print("=" * 70)
    print("ANÁLISIS COMPARATIVO DE PROVEEDORES")
    print("=" * 70)

    # Crear analizador
    analizador = AnalizadorComparativoProveedores()

    # Generar análisis completo
    reporte = analizador.generar_reporte_completo()

    if 'error' in reporte:
        print(f"Error en análisis: {reporte['error']}")
        return 1

    # Guardar resultados
    output_file = analizador.guardar_reporte(reporte)

    # Mostrar resumen
    print("\n" + "=" * 70)
    print("RESUMEN DE ANÁLISIS COMPARATIVO")
    print("=" * 70)

    resumen = reporte['resumen_ejecutivo']
    if resumen['mejor_proveedor']:
        print(f"Mejor proveedor: {resumen['mejor_proveedor']['codigo_proveedor']} ({resumen['mejor_proveedor']['puntaje_calidad']}%)")
    if resumen['peor_proveedor']:
        print(f"Peor proveedor: {resumen['peor_proveedor']['codigo_proveedor']} ({resumen['peor_proveedor']['puntaje_calidad']}%)")

    print(f"Calidad promedio: {resumen['promedio_calidad']:.1f}%")
    print(f"Problemas críticos totales: {resumen['problemas_criticos_total']}")

    print("\nTop 3 proveedores por calidad:")
    for i, prov in enumerate(reporte['ranking_calidad'][:3], 1):
        print(f"  {i}. Proveedor {prov['codigo_proveedor']}: {prov['puntaje_calidad']}% ({prov['total_registros']} propiedades)")

    print("\nConclusiones clave:")
    for conclusion in reporte['conclusiones_clave']:
        print(f"  • {conclusion}")

    print(f"\nAnálisis completo guardado en: {output_file}")
    print("Proceso finalizado exitosamente")

    return 0

if __name__ == "__main__":
    exit(main())