#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnóstico Profundo del Proveedor 02

Este script realiza un análisis exhaustivo de los datos del Proveedor 02
para identificar patrones, problemas y oportunidades de mejora.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple
import re
from collections import Counter, defaultdict

class DiagnosticadorProveedor02:
    """Herramienta especializada para diagnosticar problemas del Proveedor 02."""

    def __init__(self):
        self.stats = {
            'total_propiedades': 0,
            'campos_analizados': {},
            'problemas_identificados': [],
            'oportunidades_mejora': [],
            'patrones_encontrados': {}
        }

    def cargar_datos_raw(self) -> pd.DataFrame:
        """Carga los datos raw del Proveedor 02."""
        try:
            file_path = "data/raw/relevamiento/2025.08.29 02.xlsx"
            df = pd.read_excel(file_path)
            print(f"Cargados {len(df)} registros del archivo raw del Proveedor 02")
            return df
        except Exception as e:
            print(f"Error cargando datos raw: {e}")
            return pd.DataFrame()

    def cargar_datos_procesados(self) -> Dict[str, Any]:
        """Carga los datos ya procesados del Proveedor 02."""
        try:
            with open("data/base_datos_proveedor02_mejorado.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"Cargadas {data['metadata']['total_propiedades']} propiedades procesadas")
            return data
        except Exception as e:
            print(f"Error cargando datos procesados: {e}")
            return {}

    def analizar_calidad_campos(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analiza la calidad de cada campo en el dataset."""
        calidad = {}
        total_registros = len(df)

        for columna in df.columns:
            no_vacios = df[columna].notna().sum()
            no_nulos = df[columna].notna() & (df[columna] != '') & (df[columna] != 'nan')
            no_cero = df[columna].notna() & (df[columna] != 0) & (df[columna] != '0')

            calidad[columna] = {
                'total_registros': total_registros,
                'no_vacios': no_vacios,
                'no_nulos': no_nulos.sum(),
                'no_cero': no_cero.sum() if df[columna].dtype in ['int64', 'float64'] else None,
                'completitud': (no_nulos.sum() / total_registros) * 100,
                'tipo_dato': str(df[columna].dtype),
                'valores_unicos': df[columna].nunique(),
                'muestra_valores': df[columna].dropna().head(10).tolist()
            }

        return calidad

    def analizar_problemas_precios(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analiza específicamente los problemas con los precios."""
        problemas = {
            'total_registros': len(df),
            'precios_cero': 0,
            'precios_invalidos': 0,
            'precios_con_moneda': 0,
            'distribucion_monedas': {},
            'patrones_invalidos': [],
            'ejemplos_problemas': []
        }

        if 'Precio' in df.columns:
            # Contar precios inválidos
            precios_str = df['Precio'].astype(str)
            problemas['precios_cero'] = (precios_str == '0.00 BOB').sum()
            problemas['precios_invalidos'] = (
                precios_str.str.contains(r'0\.00|0,00|NaN', na=False) |
                (precios_str == '0')
            ).sum()

            # Analizar monedas
            monedas = precios_str.str.extract(r'(BOB|USD|Bs|\$)')[0].value_counts()
            problemas['distribucion_monedas'] = monedas.to_dict()
            problemas['precios_con_moneda'] = (~precios_str.str.contains(r'(BOB|USD|Bs|\$)', na=False)).sum()

            # Encontrar patrones problemáticos
            patrones_invalidos = [
                '0.00 BOB',
                '0,00 BOB',
                '0 BOB',
                'NaN',
                'nan'
            ]

            for patron in patrones_invalidos:
                count = (precios_str == patron).sum()
                if count > 0:
                    problemas['patrones_invalidos'].append({
                        'patron': patron,
                        'ocurrencias': count,
                        'porcentaje': (count / len(df)) * 100
                    })

            # Ejemplos de problemas
            ejemplos_indices = df[df['Precio'].astype(str).isin(['0.00 BOB', '0,00 BOB', '0 BOB'])].index[:5]
            for idx in ejemplos_indices:
                ejemplo = df.iloc[idx].to_dict()
                problemas['ejemplos_problemas'].append({
                    'fila': int(idx),
                    'precio': str(ejemplo.get('Precio', 'N/A')),
                    'tipo': str(ejemplo.get('Tipo', 'N/A')),
                    'ubicacion': str(ejemplo.get('Ubicación', 'N/A')),
                    'descripcion': str(ejemplo.get('Descripción', 'N/A'))[:100] + '...'
                })

        return problemas

    def analizar_campos_subutilizados(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identifica campos con información valiosa que no estamos usando."""
        campos_utilidad = {}

        # Campos potencialmente útiles
        campos_interes = ['Amenities', 'Agencia', 'Agente Nombre', 'Agente Teléfono',
                         'Agente Email', 'URL', 'Operacion']

        for campo in campos_interes:
            if campo in df.columns:
                no_vacios = df[campo].notna().sum()
                valores_unicos = df[campo].nunique()
                muestra_valores = df[campo].dropna().head(5).tolist()

                # Analizar el contenido
                if campo == 'Amenities':
                    # Extraer keywords de amenities
                    texto_completo = ' '.join(df[campo].dropna().astype(str))
                    palabras_comunes = Counter(re.findall(r'\b\w+\b', texto_completo.lower())).most_common(20)

                    campos_utilidad[campo] = {
                        'completitud': (no_vacios / len(df)) * 100,
                        'valores_unicos': valores_unicos,
                        'potencial_extraccion': 'ALTO' if no_vacios > 0 else 'NINGUNO',
                        'tipo_contenido': 'texto_estructurado',
                        'palabras_comunes': dict(palabras_comunes),
                        'muestra_valores': muestra_valores
                    }
                elif campo in ['Agente Nombre', 'Agencia']:
                    campos_utilidad[campo] = {
                        'completitud': (no_vacios / len(df)) * 100,
                        'valores_unicos': valores_unicos,
                        'potencial_extraccion': 'MEDIO',
                        'tipo_contenido': 'contacto',
                        'muestra_valores': muestra_valores
                    }
                else:
                    campos_utilidad[campo] = {
                        'completitud': (no_vacios / len(df)) * 100,
                        'valores_unicos': valores_unicos,
                        'potencial_extraccion': 'BAJO',
                        'tipo_contenido': 'general',
                        'muestra_valores': muestra_valores
                    }

        return campos_utilidad

    def buscar_patrones_descripciones(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Busca patrones útiles en las descripciones."""
        patrones = {
            'total_con_descripcion': 0,
            'longitudes': [],
            'keywords_ubicacion': [],
            'keywords_caracteristicas': [],
            'patrones_precio': [],
            'ejemplos_utiles': []
        }

        if 'Descripción' in df.columns:
            descripciones = df['Descripción'].dropna()
            patrones['total_con_descripcion'] = len(descripciones)

            # Analizar longitudes
            longitudes = descripciones.astype(str).str.len()
            patrones['longitudes'] = {
                'promedio': longitudes.mean(),
                'maximo': longitudes.max(),
                'minimo': longitudes.min(),
                'median': longitudes.median()
            }

            # Buscar keywords de ubicación
            keywords_ubicacion = [
                'equipetrol', 'santa cruz', 'piso', 'planta', 'avenida', 'calle',
                'zona', 'anillo', 'centro', 'norte', 'sur', 'este', 'oeste'
            ]

            ubicacion_counter = Counter()
            for desc in descripciones.astype(str):
                desc_lower = desc.lower()
                for keyword in keywords_ubicacion:
                    if keyword in desc_lower:
                        ubicacion_counter[keyword] += 1

            patrones['keywords_ubicacion'] = dict(ubicacion_counter.most_common(10))

            # Buscar patrones de precios en descripciones
            patrones_precio_regex = [
                r'\$\s*[\d,\.]+',
                r'[\d,\.]+\s*usd',
                r'[\d,\.]+\s*dólares',
                r'[\d,\.]+\s*bolivianos',
                r'bs\s*[\d,\.]+'
            ]

            precios_encontrados = []
            for desc in descripciones.astype(str):
                for regex in patrones_precio_regex:
                    matches = re.findall(regex, desc.lower())
                    if matches:
                        precios_encontrados.extend(matches)

            patrones['patrones_precio'] = Counter(precios_encontrados).most_common(10)

            # Ejemplos útiles
            ejemplos_con_dato = descripciones[descripciones.astype(str).str.len() > 50].head(3)
            for idx, desc in ejemplos_con_dato.items():
                patrones['ejemplos_utiles'].append({
                    'fila': int(idx),
                    'descripcion': str(desc)[:200] + '...',
                    'datos_adicionales': df.iloc[idx][['Tipo', 'Ubicación', 'Agente Nombre']].to_dict()
                })

        return patrones

    def generar_diagnostico_completo(self) -> Dict[str, Any]:
        """Genera un diagnóstico completo del Proveedor 02."""
        print("Iniciando diagnóstico completo del Proveedor 02...")

        # Cargar datos
        df_raw = self.cargar_datos_raw()
        if df_raw.empty:
            return {"error": "No se pudieron cargar los datos raw"}

        # Análisis básico
        self.stats['total_propiedades'] = len(df_raw)
        print(f"Analizando {len(df_raw)} propiedades...")

        # Análisis de calidad
        print("Analizando calidad de campos...")
        calidad = self.analizar_calidad_campos(df_raw)

        # Análisis de problemas de precios
        print("Analizando problemas de precios...")
        problemas_precios = self.analizar_problemas_precios(df_raw)

        # Análisis de campos subutilizados
        print("Identificando campos subutilizados...")
        campos_subutilizados = self.analizar_campos_subutilizados(df_raw)

        # Análisis de patrones en descripciones
        print("Buscando patrones en descripciones...")
        patrones_descripciones = self.buscar_patrones_descripciones(df_raw)

        # Identificar problemas críticos
        problemas_criticos = []

        if problemas_precios['precios_cero'] > 0:
            problemas_criticos.append({
                'tipo': 'PRECIO_INVALIDO',
                'severidad': 'CRITICO',
                'descripcion': f"{problemas_precios['precios_cero']} propiedades con precio 0.00 BOB",
                'impacto': 'Imposible valorar propiedades',
                'solucion_sugerida': 'Extraer precios de descripciones o URLs con IA'
            })

        if patrones_descripciones['total_con_descripcion'] < len(df_raw) * 0.3:
            problemas_criticos.append({
                'tipo': 'FALTA_DESCRIPCION',
                'severidad': 'ALTO',
                'descripcion': f"Solo {patrones_descripciones['total_con_descripcion']} propiedades tienen descripción",
                'impacto': 'Poca información para extracción de datos',
                'solucion_sugerida': 'Extraer datos de URLs y otros campos'
            })

        # Oportunidades de mejora
        oportunidades = []

        if campos_subutilizados.get('Amenities', {}).get('completitud', 0) > 20:
            oportunidades.append({
                'tipo': 'EXTRACCION_AMENITIES',
                'potencial': 'ALTO',
                'descripcion': f"{campos_subutilizados['Amenities']['completitud']:.1f}% de propiedades con amenities",
                'accion': 'Usar LLM para parsear amenities en características estructuradas'
            })

        if len(patrones_descripciones['patrones_precio']) > 0:
            oportunidades.append({
                'tipo': 'EXTRACCION_PRECIOS_DESCRIPCION',
                'potencial': 'MEDIO',
                'descripcion': f"{len(patrones_descripciones['patrones_precio'])} patrones de precios encontrados en descripciones",
                'accion': 'Extraer precios de descripciones con regex + LLM'
            })

        # Ensamblar diagnóstico final
        diagnostico = {
            'metadata': {
                'fecha_analisis': pd.Timestamp.now().isoformat(),
                'total_propiedades_analizadas': len(df_raw),
                'proveedor': '02',
                'archivo_origen': '2025.08.29 02.xlsx'
            },
            'resumen_calidad': {
                'campos_completitud': calidad,
                'completitud_general': np.mean([c['completitud'] for c in calidad.values()])
            },
            'problemas_identificados': {
                'precios': problemas_precios,
                'criticos': problemas_criticos
            },
            'oportunidades_mejora': {
                'campos_subutilizados': campos_subutilizados,
                'patrones_descripciones': patrones_descripciones,
                'oportunidades': oportunidades
            },
            'recomendaciones_prioritarias': self._generar_recomendaciones(
                problemas_precios, campos_subutilizados, patrones_descripciones
            )
        }

        return diagnostico

    def _generar_recomendaciones(self, problemas_precios: Dict, campos_subutilizados: Dict,
                                patrones_desc: Dict) -> List[Dict[str, Any]]:
        """Genera recomendaciones prioritarias basadas en el análisis."""
        recomendaciones = []

        # Prioridad 1: Precios
        if problemas_precios['precios_cero'] > 100:
            recomendaciones.append({
                'prioridad': 1,
                'titulo': 'Corregir Precios Inválidos',
                'descripcion': f"Corregir {problemas_precios['precios_cero']} propiedades con precio 0.00 BOB",
                'metodo': 'LLM + Regex',
                'campos_a_utilizar': ['Descripción', 'URL', 'Amenities'],
                'estimacion_mejora': f"{problemas_precios['precios_cero']} propiedades"
            })

        # Prioridad 2: Amenities
        if campos_subutilizados.get('Amenities', {}).get('completitud', 0) > 10:
            recomendaciones.append({
                'prioridad': 2,
                'titulo': 'Extraer Amenities',
                'descripcion': f"Parsear amenities de {campos_subutilizados['Amenities']['completitud']:.1f}% propiedades",
                'metodo': 'LLM Estructurado',
                'campos_a_utilizar': ['Amenities'],
                'estimacion_mejora': f"{int(len(campos_subutilizados['Amenities']['muestra_valores']) * 0.8)} características nuevas"
            })

        # Prioridad 3: Datos de Agente
        if campos_subutilizados.get('Agente Nombre', {}).get('completitud', 0) > 50:
            recomendaciones.append({
                'prioridad': 3,
                'titulo': 'Estandarizar Datos de Agente',
                'descripcion': f"Normalizar {campos_subutilizados['Agente Nombre']['completitud']:.1f}% datos de contacto",
                'metodo': 'Regex + Validación',
                'campos_a_utilizar': ['Agente Nombre', 'Agencia', 'Agente Teléfono'],
                'estimacion_mejora': "Mejor traceabilidad y contacto"
            })

        # Prioridad 4: Ubicación desde descripciones
        if len(patrones_desc['keywords_ubicacion']) > 0:
            recomendaciones.append({
                'prioridad': 4,
                'titulo': 'Extraer Ubicación de Descripciones',
                'descripcion': f"Usar {len(patrones_desc['keywords_ubicacion'])} keywords de ubicación encontradas",
                'metodo': 'LLM de Entidades',
                'campos_a_utilizar': ['Descripción'],
                'estimacion_mejora': f"Mejorar ubicación en 20-30% propiedades"
            })

        return recomendaciones

    def guardar_diagnostico(self, diagnostico: Dict[str, Any], output_path: str = "data/diagnosticos/diagnostico_proveedor02.json"):
        """Guarda el diagnóstico en un archivo JSON."""
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(diagnostico, f, ensure_ascii=False, indent=2, default=str)

            print(f"Diagnóstico guardado en: {output_path}")
            return output_path
        except Exception as e:
            print(f"Error guardando diagnóstico: {e}")
            return None

def main():
    """Función principal del diagnóstico."""
    print("=" * 60)
    print("DIAGNÓSTICO PROFUNDO - PROVEEDOR 02")
    print("=" * 60)

    # Crear diagnosticador
    diagnosticador = DiagnosticadorProveedor02()

    # Generar diagnóstico completo
    diagnostico = diagnosticador.generar_diagnostico_completo()

    if 'error' in diagnostico:
        print(f"Error en diagnóstico: {diagnostico['error']}")
        return 1

    # Guardar resultados
    output_file = diagnosticador.guardar_diagnostico(diagnostico)

    # Mostrar resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE DIAGNÓSTICO")
    print("=" * 60)

    resumen = diagnostico['resumen_calidad']
    print(f"Completitud general: {resumen['completitud_general']:.1f}%")

    problemas = diagnostico['problemas_identificados']
    print(f"Precios inválidos: {problemas['precios']['precios_cero']}")
    print(f"Problemas críticos: {len(problemas['criticos'])}")

    oportunidades = diagnostico['oportunidades_mejora']
    print(f"Oportunidades identificadas: {len(oportunidades['oportunidades'])}")

    print("\nRecomendaciones prioritarias:")
    for rec in diagnostico['recomendaciones_prioritarias'][:3]:
        print(f"  {rec['prioridad']}. {rec['titulo']}: {rec['descripcion']}")

    print(f"\nDiagnóstico completo guardado en: {output_file}")
    print("Análisis finalizado exitosamente")

    return 0

if __name__ == "__main__":
    exit(main())