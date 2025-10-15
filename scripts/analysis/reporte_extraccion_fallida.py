#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reporte de Extracción Fallida de Propiedades

Este script analiza todas las propiedades en data/raw que no pudieron ser
extraídas exitosamente, generando estadísticas completas por proveedor y
motivos de fallo.

Autor: Claude Code
Fecha: 2025-10-15
"""

import json
import pandas as pd
import numpy as np
import os
import glob
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
import logging
from collections import Counter, defaultdict

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ReporteExtraccionFallida:
    """Generador de reporte de extracción fallida de propiedades."""

    def __init__(self):
        self.raw_data_dir = "data/raw"
        self.output_dir = "docs"
        self.stats = {
            'total_registros_raw': 0,
            'total_propiedades_extraidas': 0,
            'total_propiedades_fallidas': 0,
            'porcentaje_exito': 0,
            'porcentaje_fallo': 0,
            'analisis_por_proveedor': {},
            'motivos_fallo': defaultdict(int),
            'ejemplos_fallo': []
        }
        self.detalles_fallo = []

    def encontrar_archivos_raw(self) -> List[str]:
        """Encuentra todos los archivos Excel en data/raw."""
        pattern = os.path.join(self.raw_data_dir, "**", "*.xlsx")
        files = glob.glob(pattern, recursive=True)
        # Excluir archivos temporales de Excel
        files = [f for f in files if not os.path.basename(f).startswith('~$')]
        logger.info(f"Se encontraron {len(files)} archivos Excel en data/raw")
        return sorted(files)

    def extraer_fecha_y_proveedor(self, filename: str) -> Tuple[str, str]:
        """Extrae fecha y código de proveedor del nombre del archivo."""
        # Formato: YYYY.MM.DD NN.xlsx
        pattern = r'(\d{4}\.\d{2}\.\d{2})\s+(\d{2})\.xlsx'
        match = re.search(pattern, filename)

        if match:
            return match.group(1), match.group(2)
        return "", ""

    def leer_excel_raw(self, filepath: str) -> Tuple[pd.DataFrame, str, str]:
        """Lee un archivo Excel y extrae metadata."""
        try:
            filename = os.path.basename(filepath)
            fecha, proveedor = self.extraer_fecha_y_proveedor(filename)

            # Intentar leer primera hoja
            df = pd.read_excel(filepath, engine='openpyxl')

            if df.empty:
                # Intentar con otras hojas
                excel_file = pd.ExcelFile(filepath, engine='openpyxl')
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(filepath, sheet_name=sheet_name)
                    if not df.empty:
                        logger.info(f"Usando hoja: {sheet_name} para {filename}")
                        break

            logger.info(f"Leído {filename}: {len(df)} registros, proveedor: {proveedor}")
            return df, fecha, proveedor

        except Exception as e:
            logger.error(f"Error leyendo {filepath}: {e}")
            return pd.DataFrame(), "", ""

    def cargar_datos_extraidos(self) -> Dict[str, Any]:
        """Carga los datos que fueron extraídos exitosamente."""
        try:
            # Intentar cargar el dataset principal
            with open("data/base_datos_relevamiento.json", 'r', encoding='utf-8') as f:
                data = json.load(f)

            propiedades = data.get('propiedades', [])
            logger.info(f"Cargadas {len(propiedades)} propiedades extraídas exitosamente")

            # Agrupar por proveedor
            por_proveedor = defaultdict(list)
            for prop in propiedades:
                prov = prop.get('codigo_proveedor', 'desconocido')
                por_proveedor[prov].append(prop)

            return {
                'total': len(propiedades),
                'por_proveedor': dict(por_proveedor),
                'metadata': data.get('metadata', {})
            }

        except FileNotFoundError:
            logger.warning("No se encontró el dataset de propiedades extraídas")
            return {'total': 0, 'por_proveedor': {}, 'metadata': {}}
        except Exception as e:
            logger.error(f"Error cargando datos extraídos: {e}")
            return {'total': 0, 'por_proveedor': {}, 'metadata': {}}

    def analizar_registros_raw(self) -> Dict[str, Any]:
        """Analiza todos los registros en archivos raw."""
        archivos = self.encontrar_archivos_raw()
        analisis_raw = {
            'total_registros': 0,
            'por_proveedor': defaultdict(int),
            'por_archivo': {},
            'proveedores_encontrados': set()
        }

        for filepath in archivos:
            filename = os.path.basename(filepath)
            df, fecha, proveedor = self.leer_excel_raw(filepath)

            if not df.empty:
                registros_archivo = len(df)
                analisis_raw['total_registros'] += registros_archivo
                analisis_raw['por_proveedor'][proveedor] += registros_archivo
                analisis_raw['proveedores_encontrados'].add(proveedor)

                analisis_raw['por_archivo'][filename] = {
                    'registros': registros_archivo,
                    'proveedor': proveedor,
                    'fecha': fecha,
                    'columnas': list(df.columns),
                    'ruta': filepath
                }

        # Convertir sets a lists para JSON
        analisis_raw['proveedores_encontrados'] = list(analisis_raw['proveedores_encontrados'])
        analisis_raw['por_proveedor'] = dict(analisis_raw['por_proveedor'])

        logger.info(f"Análisis RAW completado: {analisis_raw['total_registros']} registros totales")
        return analisis_raw

    def simular_proceso_extraccion(self, analisis_raw: Dict[str, Any]) -> Dict[str, Any]:
        """Simula el proceso de extracción para identificar fallos potenciales."""
        simulacion = {
            'propiedades_simuladas': [],
            'fallos_simulados': [],
            'motivos_fallo': defaultdict(int)
        }

        for filename, info in analisis_raw['por_archivo'].items():
            try:
                df, _, _ = self.leer_excel_raw(info['ruta'])

                for idx, row in df.iterrows():
                    resultado_simulacion = self.simular_extraccion_propiedad(row, filename, idx)

                    if resultado_simulacion['exito']:
                        simulacion['propiedades_simuladas'].append(resultado_simulacion)
                    else:
                        simulacion['fallos_simulados'].append(resultado_simulacion)
                        for motivo in resultado_simulacion['motivos']:
                            simulacion['motivos_fallo'][motivo] += 1

            except Exception as e:
                logger.error(f"Error simulando extracción para {filename}: {e}")

        logger.info(f"Simulación completada: {len(simulacion['propiedades_simuladas'])} exitosas, {len(simulacion['fallos_simulados'])} fallidas")
        return simulacion

    def simular_extraccion_propiedad(self, row: pd.Series, filename: str, idx: int) -> Dict[str, Any]:
        """Simula la extracción de una propiedad individual."""
        resultado = {
            'exito': True,
            'motivos': [],
            'archivo': filename,
            'fila': idx,
            'datos_disponibles': {}
        }

        # Verificar campos críticos
        tiene_precio = False
        tiene_ubicacion = False
        tiene_datos_basicos = False

        # Analizar precio
        precio = row.get('Precio', row.get('precio', ''))
        if pd.notna(precio) and str(precio).strip() not in ['0', '0.00', '0,00', '']:
            try:
                precio_limpio = str(precio).replace('$', '').replace('USD', '').replace('BOB', '').replace(',', '').replace(' ', '')
                float(precio_limpio)
                tiene_precio = True
                resultado['datos_disponibles']['precio'] = True
            except:
                resultado['motivos'].append('PRECIO_INVALIDO')
        else:
            resultado['motivos'].append('SIN_PRECIO')

        # Analizar ubicación
        ubicacion = row.get('Ubicación', row.get('ubicacion', row.get('zona', '')))
        if pd.notna(ubicacion) and str(ubicacion).strip():
            tiene_ubicacion = True
            resultado['datos_disponibles']['ubicacion'] = True
        else:
            resultado['motivos'].append('SIN_UBICACION')

        # Analizar coordenadas
        lat = row.get('Latitud', row.get('latitud', ''))
        lng = row.get('Longitud', row.get('longitud', ''))
        if pd.notna(lat) and pd.notna(lng):
            try:
                float(lat) and float(lng)
                tiene_ubicacion = True
                resultado['datos_disponibles']['coordenadas'] = True
            except:
                resultado['motivos'].append('COORDENADAS_INVALIDAS')

        # Analizar datos básicos (título/tipo)
        titulo = row.get('Título', row.get('titulo', ''))
        tipo = row.get('Tipo', row.get('tipo_propiedad', ''))
        if (pd.notna(titulo) and str(titulo).strip()) or (pd.notna(tipo) and str(tipo).strip()):
            tiene_datos_basicos = True
            resultado['datos_disponibles']['datos_basicos'] = True
        else:
            resultado['motivos'].append('SIN_DATOS_BASICOS')

        # Evaluar éxito según criterios del ETL original
        # El ETL requiere precio o coordenadas, y algunos datos básicos
        if not (tiene_precio or (pd.notna(lat) and pd.notna(lng))):
            resultado['exito'] = False

        if not tiene_datos_basicos:
            resultado['exito'] = False

        # Si tiene descripción pero no otros datos, podría ser recuperable con LLM
        descripcion = row.get('Descripción', row.get('descripcion', ''))
        if pd.notna(descripcion) and str(descripcion).strip() and len(str(descripcion)) > 50:
            resultado['datos_disponibles']['descripcion'] = True
            resultado['recuperable_con_llm'] = True
        else:
            resultado['recuperable_con_llm'] = False

        return resultado

    def analizar_proveedor_02_detalles(self) -> Dict[str, Any]:
        """Análisis detallado específico para el Proveedor 02."""
        try:
            # Buscar archivo del Proveedor 02
            archivos_proveedor02 = [f for f in self.encontrar_archivos_raw()
                                  if '02.xlsx' in f]

            if not archivos_proveedor02:
                return {"error": "No se encontraron archivos del Proveedor 02"}

            archivo_proveedor02 = archivos_proveedor02[0]
            df, _, _ = self.leer_excel_raw(archivo_proveedor02)

            analisis = {
                'total_registros': len(df),
                'precios_invalidos': 0,
                'sin_descripcion': 0,
                'con_descripcion_corta': 0,
                'con_descripcion_larga': 0,
                'problemas_comunes': defaultdict(int),
                'ejemplos_problemas': []
            }

            # Analizar precios
            if 'Precio' in df.columns:
                precios_str = df['Precio'].astype(str)
                analisis['precios_invalidos'] = (
                    precios_str.str.contains(r'0\.00|0,00|NaN|nan', na=False) |
                    (precios_str == '0')
                ).sum()

            # Analizar descripciones
            if 'Descripción' in df.columns:
                descripciones = df['Descripción'].dropna()
                analisis['sin_descripcion'] = len(df) - len(descripciones)

                for desc in descripciones:
                    desc_str = str(desc)
                    if len(desc_str) < 50:
                        analisis['con_descripcion_corta'] += 1
                    else:
                        analisis['con_descripcion_larga'] += 1

            # Ejemplos de problemas
            ejemplos_filas = df.head(5).iterrows()
            for idx, row in ejemplos_filas:
                ejemplo = {
                    'fila': int(idx),
                    'precio': str(row.get('Precio', 'N/A')),
                    'tipo': str(row.get('Tipo', 'N/A')),
                    'ubicacion': str(row.get('Ubicación', 'N/A')),
                    'descripcion_preview': str(row.get('Descripción', 'N/A'))[:100] + '...' if len(str(row.get('Descripción', ''))) > 100 else str(row.get('Descripción', 'N/A'))
                }
                analisis['ejemplos_problemas'].append(ejemplo)

            return analisis

        except Exception as e:
            logger.error(f"Error analizando Proveedor 02: {e}")
            return {"error": str(e)}

    def generar_reporte_completo(self) -> Dict[str, Any]:
        """Genera el reporte completo de extracción fallida."""
        logger.info("Iniciando generación de reporte completo...")

        # 1. Analizar registros RAW
        analisis_raw = self.analizar_registros_raw()
        self.stats['total_registros_raw'] = analisis_raw['total_registros']

        # 2. Cargar datos extraídos
        datos_extraidos = self.cargar_datos_extraidos()
        self.stats['total_propiedades_extraidas'] = datos_extraidos['total']

        # 3. Simular proceso de extracción
        simulacion = self.simular_proceso_extraccion(analisis_raw)

        # 4. Calcular estadísticas finales
        self.stats['total_propiedades_fallidas'] = simulacion['motivos_fallo']['total'] = len(simulacion['fallos_simulados'])

        if self.stats['total_registros_raw'] > 0:
            self.stats['porcentaje_exito'] = (self.stats['total_propiedades_extraidas'] / self.stats['total_registros_raw']) * 100
            self.stats['porcentaje_fallo'] = (self.stats['total_propiedades_fallidas'] / self.stats['total_registros_raw']) * 100

        # 5. Análisis por proveedor
        for proveedor in analisis_raw['proveedores_encontrados']:
            registros_raw_proveedor = analisis_raw['por_proveedor'].get(proveedor, 0)
            registros_extraidos_proveedor = len(datos_extraidos['por_proveedor'].get(proveedor, []))

            if registros_raw_proveedor > 0:
                self.stats['analisis_por_proveedor'][proveedor] = {
                    'registros_raw': registros_raw_proveedor,
                    'propiedades_extraidas': registros_extraidos_proveedor,
                    'propiedades_fallidas': registros_raw_proveedor - registros_extraidos_proveedor,
                    'tasa_exito': (registros_extraidos_proveedor / registros_raw_proveedor) * 100,
                    'tasa_fallo': ((registros_raw_proveedor - registros_extraidos_proveedor) / registros_raw_proveedor) * 100
                }

        # 6. Análisis detallado del Proveedor 02
        analisis_proveedor02 = self.analizar_proveedor_02_detalles()

        # 7. Compilar reporte final
        reporte = {
            'metadata': {
                'fecha_generacion': datetime.now().isoformat(),
                'script_version': '1.0',
                'descripcion': 'Reporte completo de extracción fallida de propiedades'
            },
            'resumen_ejecutivo': {
                'total_registros_raw': self.stats['total_registros_raw'],
                'total_propiedades_extraidas': self.stats['total_propiedades_extraidas'],
                'total_propiedades_fallidas': self.stats['total_propiedades_fallidas'],
                'tasa_exito_general': round(self.stats['porcentaje_exito'], 2),
                'tasa_fallo_general': round(self.stats['porcentaje_fallo'], 2),
                'proveedores_procesados': len(analisis_raw['proveedores_encontrados'])
            },
            'analisis_raw': analisis_raw,
            'datos_extraidos': datos_extraidos,
            'simulacion_extraccion': {
                'total_simulado': len(simulacion['propiedades_simuladas']) + len(simulacion['fallos_simulados']),
                'exitosos_simulados': len(simulacion['propiedades_simuladas']),
                'fallidos_simulados': len(simulacion['fallos_simulados']),
                'motivos_fallo': dict(simulacion['motivos_fallo'])
            },
            'analisis_por_proveedor': self.stats['analisis_por_proveedor'],
            'analisis_detallado_proveedor02': analisis_proveedor02,
            'motivos_principales_fallo': self._analizar_motivos_principales(simulacion['motivos_fallo']),
            'recomendaciones': self._generar_recomendaciones(),
            'estadisticas_finales': self.stats
        }

        return reporte

    def _analizar_motivos_principales(self, motivos_fallo: Dict[str, int]) -> List[Dict[str, Any]]:
        """Analiza y ordena los motivos principales de fallo."""
        # Excluir 'total' si existe
        motivos_filtrados = {k: v for k, v in motivos_fallo.items() if k != 'total'}

        motivos_ordenados = sorted(motivos_filtrados.items(), key=lambda x: x[1], reverse=True)

        top_motivos = []
        for motivo, count in motivos_ordenados[:10]:  # Top 10
            porcentaje = (count / self.stats['total_propiedades_fallidas']) * 100 if self.stats['total_propiedades_fallidas'] > 0 else 0
            top_motivos.append({
                'motivo': motivo,
                'cantidad': count,
                'porcentaje_total_fallos': round(porcentaje, 2),
                'severidad': self._clasificar_severidad(porcentaje)
            })

        return top_motivos

    def _clasificar_severidad(self, porcentaje: float) -> str:
        """Clasifica la severidad de un motivo de fallo."""
        if porcentaje >= 30:
            return 'CRÍTICO'
        elif porcentaje >= 15:
            return 'ALTO'
        elif porcentaje >= 5:
            return 'MEDIO'
        else:
            return 'BAJO'

    def _generar_recomendaciones(self) -> List[Dict[str, Any]]:
        """Genera recomendaciones basadas en el análisis."""
        recomendaciones = []

        # Recomendaciones basadas en la tasa de fallo general
        if self.stats['porcentaje_fallo'] > 50:
            recomendaciones.append({
                'prioridad': 1,
                'tipo': 'MEJORA_ETL_GENERAL',
                'titulo': 'Revisar y mejorar criterios de extracción',
                'descripcion': f'La tasa de fallo es del {self.stats["porcentaje_fallo"]:.1f}%, lo que indica problemas sistémicos',
                'accion': 'Relajar criterios de validación o mejorar extracción de datos'
            })

        # Recomendaciones específicas por proveedor
        for proveedor, analisis in self.stats['analisis_por_proveedor'].items():
            if analisis['tasa_fallo'] > 70:
                recomendaciones.append({
                    'prioridad': 2,
                    'tipo': 'PROVEEDOR_ESPECIFICO',
                    'titulo': f'Intervención urgente Proveedor {proveedor}',
                    'descripcion': f'El Proveedor {proveedor} tiene una tasa de fallo del {analisis["tasa_fallo"]:.1f}%',
                    'accion': 'Analizar formato de datos y desarrollar extractor específico'
                })

        # Recomendación para LLM si hay muchas descripciones
        if self.stats['total_propiedades_fallidas'] > 100:
            recomendaciones.append({
                'prioridad': 3,
                'tipo': 'IMPLEMENTACION_LLM',
                'titulo': 'Implementar sistema de extracción con LLM',
                'descripcion': f'Hay {self.stats["total_propiedades_fallidas"]} propiedades que podrían recuperarse con LLM',
                'accion': 'Usar sistema híbrido Regex + LLM para extraer datos de descripciones'
            })

        return recomendaciones

    def guardar_reporte_json(self, reporte: Dict[str, Any]) -> str:
        """Guarda el reporte en formato JSON."""
        output_path = os.path.join(self.output_dir, 'reporte_extraccion_fallida.json')

        # Asegurar que el directorio existe
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(reporte, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"Reporte JSON guardado en: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error guardando reporte JSON: {e}")
            return None

    def generar_reporte_markdown(self, reporte: Dict[str, Any]) -> str:
        """Genera una versión legible del reporte en Markdown."""
        output_path = os.path.join(self.output_dir, 'reporte_extraccion_fallida.md')

        # Asegurar que el directorio existe
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

        try:
            contenido_md = self._formatear_reporte_markdown(reporte)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(contenido_md)

            logger.info(f"Reporte Markdown guardado en: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error guardando reporte Markdown: {e}")
            return None

    def _formatear_reporte_markdown(self, reporte: Dict[str, Any]) -> str:
        """Formatea el reporte en Markdown."""
        resumen = reporte['resumen_ejecutivo']

        md = f"""# Reporte de Extracción Fallida de Propiedades

**Fecha de generación:** {reporte['metadata']['fecha_generacion'][:10]}

## Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| Total registros RAW | {resumen['total_registros_raw']:,} |
| Propiedades extraídas exitosamente | {resumen['total_propiedades_extraidas']:,} |
| Propiedades fallidas | {resumen['total_propiedades_fallidas']:,} |
| Tasa de éxito general | {resumen['tasa_exito_general']:.1f}% |
| Tasa de fallo general | {resumen['tasa_fallo_general']:.1f}% |
| Proveedores procesados | {resumen['proveedores_procesados']} |

"""

        # Análisis por proveedor
        md += "## Análisis por Proveedor\n\n"
        md += "| Proveedor | Registros RAW | Extraídas | Fallidas | Tasa Éxito | Tasa Fallo |\n"
        md += "|-----------|---------------|-----------|----------|------------|------------|\n"

        for proveedor, analisis in sorted(reporte['analisis_por_proveedor'].items()):
            md += f"| {proveedor} | {analisis['registros_raw']:,} | {analisis['propiedades_extraidas']:,} | {analisis['propiedades_fallidas']:,} | {analisis['tasa_exito']:.1f}% | {analisis['tasa_fallo']:.1f}% |\n"

        # Motivos principales de fallo
        md += "\n## Motivos Principales de Fallo\n\n"
        for motivo in reporte['motivos_principales_fallo'][:10]:
            md += f"### {motivo['motivo']} ({motivo['severidad']})\n"
            md += f"- **Cantidad:** {motivo['cantidad']:,} propiedades\n"
            md += f"- **Porcentaje del total:** {motivo['porcentaje_total_fallos']:.1f}%\n\n"

        # Análisis detallado Proveedor 02
        if 'analisis_detallado_proveedor02' in reporte and 'error' not in reporte['analisis_detallado_proveedor02']:
            analisis_p02 = reporte['analisis_detallado_proveedor02']
            md += "## Análisis Detallado - Proveedor 02\n\n"
            md += f"- **Total registros:** {analisis_p02['total_registros']:,}\n"
            md += f"- **Precios inválidos:** {analisis_p02['precios_invalidos']:,}\n"
            md += f"- **Sin descripción:** {analisis_p02['sin_descripcion']:,}\n"
            md += f"- **Con descripción corta:** {analisis_p02['con_descripcion_corta']:,}\n"
            md += f"- **Con descripción larga:** {analisis_p02['con_descripcion_larga']:,}\n\n"

        # Recomendaciones
        md += "## Recomendaciones\n\n"
        for i, rec in enumerate(reporte['recomendaciones'], 1):
            md += f"### {i}. {rec['titulo']} (Prioridad {rec['prioridad']})\n"
            md += f"- **Tipo:** {rec['tipo']}\n"
            md += f"- **Descripción:** {rec['descripcion']}\n"
            md += f"- **Acción recomendada:** {rec['accion']}\n\n"

        md += "---\n"
        md += f"*Reporte generado automáticamente por el script `reporte_extraccion_fallida.py`*\n"

        return md

def main():
    """Función principal."""
    print("=" * 80)
    print("REPORTE DE EXTRACCIÓN FALLIDA DE PROPIEDADES")
    print("=" * 80)

    # Crear generador de reporte
    generador = ReporteExtraccionFallida()

    try:
        # Generar reporte completo
        print("Generando reporte completo...")
        reporte = generador.generar_reporte_completo()

        # Guardar reporte JSON
        print("Guardando reporte JSON...")
        json_path = generador.guardar_reporte_json(reporte)

        # Generar reporte Markdown
        print("Generando reporte Markdown...")
        md_path = generador.generar_reporte_markdown(reporte)

        # Mostrar resumen en consola
        resumen = reporte['resumen_ejecutivo']
        print("\n" + "=" * 80)
        print("RESUMEN DE RESULTADOS")
        print("=" * 80)
        print(f"Total registros RAW: {resumen['total_registros_raw']:,}")
        print(f"Propiedades extraídas: {resumen['total_propiedades_extraidas']:,}")
        print(f"Propiedades fallidas: {resumen['total_propiedades_fallidas']:,}")
        print(f"Tasa de éxito: {resumen['tasa_exito_general']:.1f}%")
        print(f"Tasa de fallo: {resumen['tasa_fallo_general']:.1f}%")
        print(f"Proveedores procesados: {resumen['proveedores_procesados']}")

        if json_path:
            print(f"\n[OK] Reporte JSON guardado en: {json_path}")
        if md_path:
            print(f"[OK] Reporte Markdown guardado en: {md_path}")

        print("\nAnálisis completado exitosamente.")
        return 0

    except Exception as e:
        logger.error(f"Error en la generación del reporte: {e}")
        print(f"\n[ERROR] {e}")
        return 1

if __name__ == "__main__":
    exit(main())