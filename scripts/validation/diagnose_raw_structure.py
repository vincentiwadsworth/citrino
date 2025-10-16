#!/usr/bin/env python3
"""
DIAGNÓSTICO DE ESTRUCTURA DE ARCHIVOS RAW
==========================================

Analiza la estructura de archivos raw para identificar:
1. Nombres reales de columnas de coordenadas
2. Formatos de coordenadas
3. Patrones de datos
4. Problemas de extracción

Uso:
    python scripts/validation/diagnose_raw_structure.py --input "data/raw/relevamiento/2025.08.29 05.xlsx"

Author: Claude Code
Date: 2025-10-15
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from fuzzywuzzy import process
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import argparse
import warnings
warnings.filterwarnings('ignore')

class RawStructureDiagnostic:
    """Diagnóstico de estructura de archivos raw"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = {
            'archivo': '',
            'columnas': [],
            'coordenadas_detectadas': {},
            'problemas': [],
            'recomendaciones': [],
            'muestras_datos': []
        }

    def log(self, message: str):
        """Imprimir mensaje si verbose está activado"""
        if self.verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def detect_coordinate_columns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detectar columnas de coordenadas usando fuzzy matching
        """
        coordinate_keywords = {
            'latitude': ['lat', 'latitude', 'latitud', 'latitud', 'la', 'geo_lat'],
            'longitude': ['lng', 'lon', 'longitude', 'longitud', 'longitud', 'lo', 'geo_lng', 'geo_lon']
        }

        detected = {}

        for coord_type, keywords in coordinate_keywords.items():
            best_match = None
            best_score = 0

            for keyword in keywords:
                # Buscar coincidencias exactas y parciales
                for col in df.columns:
                    # Matching exacto
                    if keyword.lower() == col.lower():
                        score = 100
                        if score > best_score:
                            best_match = col
                            best_score = score
                    # Matching parcial
                    elif keyword.lower() in col.lower():
                        score = 85
                        if score > best_score:
                            best_match = col
                            best_score = score

            # Usar fuzzy matching como fallback
            if not best_match:
                for keyword in keywords:
                    match = process.extractOne(keyword, df.columns, score_cutoff=70)
                    if match and match[1] > best_score:
                        best_match = match[0]
                        best_score = match[1]

            detected[coord_type] = {
                'column': best_match,
                'confidence': best_score
            }

        return detected

    def analyze_coordinate_formats(self, df: pd.DataFrame, coord_cols: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analizar formatos de coordenadas en las columnas detectadas
        """
        analysis = {
            'latitude': {'format': 'unknown', 'range': None, 'null_count': 0, 'sample_values': []},
            'longitude': {'format': 'unknown', 'range': None, 'null_count': 0, 'sample_values': []}
        }

        for coord_type, col_info in coord_cols.items():
            if col_info['column']:
                col = col_info['column']
                if col in df.columns:
                    data = df[col].dropna()

                    if len(data) > 0:
                        # Análisis de valores
                        sample_values = data.head(10).tolist()
                        analysis[coord_type]['sample_values'] = sample_values
                        analysis[coord_type]['null_count'] = df[col].isna().sum()

                        # Detectar formato
                        try:
                            # Intentar convertir a numérico
                            numeric_data = pd.to_numeric(data, errors='coerce').dropna()

                            if len(numeric_data) > 0:
                                analysis[coord_type]['format'] = 'numeric'
                                analysis[coord_type]['range'] = {
                                    'min': float(numeric_data.min()),
                                    'max': float(numeric_data.max())
                                }
                            else:
                                analysis[coord_type]['format'] = 'text'

                        except Exception:
                            analysis[coord_type]['format'] = 'text'

        return analysis

    def check_santa_cruz_validity(self, coord_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verificar si coordenadas están en rango de Santa Cruz
        """
        santa_cruz_bounds = {
            'lat_min': -18.2,
            'lat_max': -17.5,
            'lng_min': -63.5,
            'lng_max': -63.0
        }

        validity = {
            'latitude': {'valid_count': 0, 'invalid_count': 0, 'valid_samples': [], 'invalid_samples': []},
            'longitude': {'valid_count': 0, 'invalid_count': 0, 'valid_samples': [], 'invalid_samples': []}
        }

        # Verificar latitud
        lat_data = coord_analysis['latitude']
        if lat_data['format'] == 'numeric' and lat_data['range']:
            sample_values = [v for v in lat_data['sample_values'] if isinstance(v, (int, float))]

            for val in sample_values:
                if santa_cruz_bounds['lat_min'] <= val <= santa_cruz_bounds['lat_max']:
                    validity['latitude']['valid_count'] += 1
                    validity['latitude']['valid_samples'].append(val)
                else:
                    validity['latitude']['invalid_count'] += 1
                    validity['latitude']['invalid_samples'].append(val)

        # Verificar longitud
        lng_data = coord_analysis['longitude']
        if lng_data['format'] == 'numeric' and lng_data['range']:
            sample_values = [v for v in lng_data['sample_values'] if isinstance(v, (int, float))]

            for val in sample_values:
                if santa_cruz_bounds['lng_min'] <= val <= santa_cruz_bounds['lng_max']:
                    validity['longitude']['valid_count'] += 1
                    validity['longitude']['valid_samples'].append(val)
                else:
                    validity['longitude']['invalid_count'] += 1
                    validity['longitude']['invalid_samples'].append(val)

        return validity

    def extract_data_samples(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Extraer muestras de datos para análisis manual
        """
        samples = []

        # Tomar primeras 5 filas con todos los datos
        for i in range(min(5, len(df))):
            row = df.iloc[i].to_dict()
            # Limpiar valores nulos para mejor visualización
            clean_row = {k: v if pd.notna(v) else None for k, v in row.items()}
            samples.append(clean_row)

        return samples

    def diagnose_file(self, file_path: str) -> Dict[str, Any]:
        """
        Diagnosticar estructura completa de un archivo
        """
        self.log(f"Diagnosticando archivo: {os.path.basename(file_path)}")

        try:
            # Leer archivo
            df = pd.read_excel(file_path)
            self.log(f"Archivo leído: {len(df)} filas, {len(df.columns)} columnas")

            # Guardar info básica
            self.results['archivo'] = os.path.basename(file_path)
            self.results['columnas'] = list(df.columns)
            self.results['total_filas'] = len(df)

            # Detectar columnas de coordenadas
            coord_cols = self.detect_coordinate_columns(df)
            self.results['coordenadas_detectadas'] = coord_cols

            # Analizar formatos de coordenadas
            coord_analysis = self.analyze_coordinate_formats(df, coord_cols)
            self.results['analisis_coordenadas'] = coord_analysis

            # Verificar validez Santa Cruz
            validity = self.check_santa_cruz_validity(coord_analysis)
            self.results['validez_santa_cruz'] = validity

            # Extraer muestras de datos
            samples = self.extract_data_samples(df)
            self.results['muestras_datos'] = samples

            # Identificar problemas
            problems = []
            recommendations = []

            # Problema 1: No se detectaron coordenadas
            if not coord_cols['latitude']['column'] or not coord_cols['longitude']['column']:
                problems.append("No se detectaron columnas de coordenadas")
                recommendations.append("Revisar nombres de columnas manualmente")

            # Problema 2: Baja confianza en detección
            if coord_cols['latitude']['confidence'] < 80 or coord_cols['longitude']['confidence'] < 80:
                problems.append(f"Baja confianza en detección: Lat({coord_cols['latitude']['confidence']}%), Lng({coord_cols['longitude']['confidence']}%)")
                recommendations.append("Verificar nombres de columnas manualmente")

            # Problema 3: Coordenadas no numéricas
            if coord_analysis['latitude']['format'] != 'numeric' or coord_analysis['longitude']['format'] != 'numeric':
                problems.append("Coordenadas no están en formato numérico")
                recommendations.append("Investigar formato de coordenadas")

            # Problema 4: Coordenadas fuera de rango
            if validity['latitude']['invalid_count'] > 0 or validity['longitude']['invalid_count'] > 0:
                problems.append(f"Coordenadas fuera de rango Santa Cruz detectadas")
                recommendations.append("Revisar valores inválidos manualmente")

            # Problema 5: Muchos nulos
            lat_nulls = coord_analysis['latitude']['null_count']
            lng_nulls = coord_analysis['longitude']['null_count']
            total_rows = len(df)

            if lat_nulls > total_rows * 0.5 or lng_nulls > total_rows * 0.5:
                problems.append(f"Muchos valores nulos: Lat({lat_nulls}), Lng({lng_nulls})")
                recommendations.append("Investigar por qué hay tantos nulos")

            self.results['problemas'] = problems
            self.results['recomendaciones'] = recommendations

            return self.results

        except Exception as e:
            error_msg = f"Error diagnosticando archivo: {str(e)}"
            self.log(error_msg)
            self.results['error'] = error_msg
            return self.results

    def generate_report(self, output_dir: str) -> bool:
        """
        Generar reporte de diagnóstico
        """
        try:
            # Generar archivo JSON
            report_file = os.path.join(output_dir, f"diagnostico_{self.results['archivo']}.json")

            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)

            # Generar archivo CSV con muestras
            if self.results['muestras_datos']:
                samples_df = pd.DataFrame(self.results['muestras_datos'])
                csv_file = os.path.join(output_dir, f"muestras_{self.results['archivo']}.csv")
                samples_df.to_csv(csv_file, index=False, encoding='utf-8')

            # Generar resumen textual
            summary_file = os.path.join(output_dir, f"resumen_{self.results['archivo']}.txt")
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"DIAGNÓSTICO DE ESTRUCTURA - {self.results['archivo']}\n")
                f.write("="*60 + "\n\n")

                f.write(f"ARCHIVO: {self.results['archivo']}\n")
                f.write(f"TOTAL FILAS: {self.results.get('total_filas', 0)}\n")
                f.write(f"TOTAL COLUMNAS: {len(self.results.get('columnas', []))}\n\n")

                f.write("COLUMNAS ENCONTRADAS:\n")
                for col in self.results.get('columnas', []):
                    f.write(f"  - {col}\n")
                f.write("\n")

                f.write("DETECCIÓN DE COORDENADAS:\n")
                coord_cols = self.results.get('coordenadas_detectadas', {})
                f.write(f"  - Latitud: {coord_cols.get('latitude', {}).get('column', 'NO DETECTADA')} (confianza: {coord_cols.get('latitude', {}).get('confidence', 0)}%)\n")
                f.write(f"  - Longitud: {coord_cols.get('longitude', {}).get('column', 'NO DETECTADA')} (confianza: {coord_cols.get('longitude', {}).get('confidence', 0)}%)\n\n")

                if self.results.get('problemas'):
                    f.write("PROBLEMAS DETECTADOS:\n")
                    for problem in self.results['problemas']:
                        f.write(f"  - {problem}\n")
                    f.write("\n")

                if self.results.get('recomendaciones'):
                    f.write("RECOMENDACIONES:\n")
                    for rec in self.results['recomendaciones']:
                        f.write(f"  - {rec}\n")
                    f.write("\n")

                validity = self.results.get('validez_santa_cruz', {})
                f.write("VALIDEZ SANTA CRUZ:\n")
                f.write(f"  - Latitud válidas: {validity.get('latitude', {}).get('valid_count', 0)}\n")
                f.write(f"  - Latitud inválidas: {validity.get('latitude', {}).get('invalid_count', 0)}\n")
                f.write(f"  - Longitud válidas: {validity.get('longitude', {}).get('valid_count', 0)}\n")
                f.write(f"  - Longitud inválidas: {validity.get('longitude', {}).get('invalid_count', 0)}\n")

            self.log(f"Reporte generado en: {output_dir}")
            return True

        except Exception as e:
            self.log(f"Error generando reporte: {e}")
            return False


def main():
    """
    Función principal
    """
    parser = argparse.ArgumentParser(description='Diagnosticar estructura de archivo raw')
    parser.add_argument('--input', required=True, help='Ruta al archivo raw')
    parser.add_argument('--output', default='data/processed', help='Directorio de salida')
    parser.add_argument('--verbose', action='store_true', help='Mostrar detalles')

    args = parser.parse_args()

    # Verificar archivo
    if not os.path.exists(args.input):
        print(f"ERROR: Archivo no encontrado: {args.input}")
        return False

    # Crear directorio de salida
    os.makedirs(args.output, exist_ok=True)

    # Ejecutar diagnóstico
    diagnostic = RawStructureDiagnostic(verbose=args.verbose)
    result = diagnostic.diagnose_file(args.input)

    if 'error' in result:
        print(f"ERROR: {result['error']}")
        return False

    # Generar reporte
    success = diagnostic.generate_report(args.output)

    if success:
        print(f"DIAGNÓSTICO COMPLETADO")
        print(f"Reportes generados en: {args.output}")
        print(f"Revisa los archivos para entender la estructura del dataset")
    else:
        print("ERROR GENERANDO REPORTE")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)