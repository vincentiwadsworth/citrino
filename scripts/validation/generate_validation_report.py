#!/usr/bin/env python3
"""
GENERADOR DE REPORTE CONSOLIDADO DE VALIDACIÓN
==============================================

Lee todos los reportes JSON generados y crea un reporte consolidado
para el equipo Citrino con métricas agregadas y estado general.

Uso:
    python scripts/validation/generate_validation_report.py --input-dir "data/processed"

Author: Claude Code
Date: 2025-10-15
"""

import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
import argparse

class ValidationReportGenerator:
    """Generador de reportes consolidados de validación"""

    def __init__(self):
        self.reports = []
        self.total_stats = {
            'total_archivos': 0,
            'total_filas': 0,
            'total_filas_procesadas': 0,
            'total_errores': 0,
            'total_coordenadas_validas': 0,
            'total_coordenadas_invalidas': 0,
            'total_datos_completos': 0,
            'total_datos_incompletos': 0
        }

    def load_reports(self, input_dir: str) -> bool:
        """
        Cargar todos los reportes JSON del directorio
        """
        if not os.path.exists(input_dir):
            print(f"ERROR: Directorio no encontrado: {input_dir}")
            return False

        report_files = [f for f in os.listdir(input_dir) if f.endswith('_reporte.json')]

        if not report_files:
            print(f"ERROR: No se encontraron reportes JSON en: {input_dir}")
            return False

        print(f"Cargando {len(report_files)} reportes...")

        for report_file in report_files:
            try:
                with open(os.path.join(input_dir, report_file), 'r', encoding='utf-8') as f:
                    report = json.load(f)
                    self.reports.append(report)
                    print(f"  - {report_file}: {report['archivo_origen']}")
            except Exception as e:
                print(f"Error cargando {report_file}: {e}")

        if self.reports:
            self.calculate_totals()
            return True
        else:
            print("ERROR: No se pudo cargar ningún reporte")
            return False

    def calculate_totals(self):
        """
        Calcular estadísticas totales
        """
        self.total_stats['total_archivos'] = len(self.reports)

        for report in self.reports:
            stats = report.get('estadisticas', {})
            for key in self.total_stats:
                if key in stats:
                    self.total_stats[key] += stats[key]

    def generate_html_report(self, output_path: str) -> bool:
        """
        Generar reporte HTML detallado
        """
        try:
            html_content = self._build_html_report()

            output_file = os.path.join(output_path, 'validacion_consolidada.html')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"Reporte HTML generado: {output_file}")
            return True

        except Exception as e:
            print(f"Error generando reporte HTML: {e}")
            return False

    def generate_excel_summary(self, output_path: str) -> bool:
        """
        Generar resumen Excel
        """
        try:
            output_file = os.path.join(output_path, 'resumen_validacion.xlsx')

            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Hoja 1: Resumen General
                summary_data = {
                    'Métrica': [
                        'Total archivos procesados',
                        'Total filas',
                        'Total filas procesadas',
                        'Total errores',
                        'Total coordenadas válidas',
                        'Total coordenadas inválidas',
                        'Total datos completos',
                        'Total datos incompletos'
                    ],
                    'Cantidad': [
                        self.total_stats['total_archivos'],
                        self.total_stats['total_filas'],
                        self.total_stats['total_filas_procesadas'],
                        self.total_stats['total_errores'],
                        self.total_stats['total_coordenadas_validas'],
                        self.total_stats['total_coordenadas_invalidas'],
                        self.total_stats['total_datos_completos'],
                        self.total_stats['total_datos_incompletos']
                    ]
                }

                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='RESUMEN_GENERAL', index=False)

                # Hoja 2: Detalle por Archivo
                details = []
                for report in self.reports:
                    stats = report.get('estadisticas', {})
                    metrics = report.get('metricas_calidad', {})
                    details.append({
                        'Archivo': report.get('archivo_origen', ''),
                        'Fecha Procesamiento': report.get('fecha_procesamiento', ''),
                        'Total Filas': stats.get('total_filas', 0),
                        'Filas Procesadas': stats.get('filas_procesadas', 0),
                        'Errores': stats.get('errores', 0),
                        'Coordenadas Válidas': stats.get('coordenadas_validas', 0),
                        'Coordenadas Válidas %': f"{metrics.get('coordenadas_validas', 0):.1f}%",
                        'Datos Completos': stats.get('datos_completos', 0),
                        'Datos Completos %': f"{metrics.get('datos_completos', 0):.1f}%",
                        'Estado Calidad': report.get('estado_calidad', '')
                    })

                details_df = pd.DataFrame(details)
                details_df.to_excel(writer, sheet_name='DETALLE_ARCHIVOS', index=False)

            print(f"Resumen Excel generado: {output_file}")
            return True

        except Exception as e:
            print(f"Error generando resumen Excel: {e}")
            return False

    def _build_html_report(self) -> str:
        """
        Construir contenido HTML del reporte
        """
        # Calcular porcentajes generales
        total = self.total_stats['total_filas']
        if total > 0:
            coords_pct = (self.total_stats['total_coordenadas_validas'] / total) * 100
            datos_pct = (self.total_stats['total_datos_completos'] / total) * 100
            errores_pct = (self.total_stats['total_errores'] / total) * 100
        else:
            coords_pct = datos_pct = errores_pct = 0

        html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte de Validación Consolidado - Citrino</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #34495e;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .summary-card {{
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #3498db;
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
        .summary-card .number {{
            font-size: 2em;
            font-weight: bold;
            color: #3498db;
        }}
        .quality-excelente {{
            border-left-color: #27ae60;
        }}
        .quality-aceptable {{
            border-left-color: #f39c12;
        }}
        .quality-problemas {{
            border-left-color: #e74c3c;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #34495e;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .status-excelente {{
            color: #27ae60;
            font-weight: bold;
        }}
        .status-aceptable {{
            color: #f39c12;
            font-weight: bold;
        }}
        .status-problemas {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .footer {{
            margin-top: 40px;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Reporte de Validación Consolidado</h1>
        <p style="text-align: center; color: #7f8c8d;">
            Generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} |
            Equipo Citrino - Procesamiento de Datos Raw
        </p>

        <h2>Resumen General</h2>
        <div class="summary-grid">
            <div class="summary-card">
                <h3>Archivos Procesados</h3>
                <div class="number">{self.total_stats['total_archivos']}</div>
            </div>
            <div class="summary-card">
                <h3>Total Filas</h3>
                <div class="number">{self.total_stats['total_filas']:,}</div>
            </div>
            <div class="summary-card">
                <h3>Coordenadas Válidas</h3>
                <div class="number">{coords_pct:.1f}%</div>
                <small>{self.total_stats['total_coordenadas_validas']:,} filas</small>
            </div>
            <div class="summary-card">
                <h3>Datos Completos</h3>
                <div class="number">{datos_pct:.1f}%</div>
                <small>{self.total_stats['total_datos_completos']:,} filas</small>
            </div>
            <div class="summary-card">
                <h3>Tasa de Errores</h3>
                <div class="number">{errores_pct:.1f}%</div>
                <small>{self.total_stats['total_errores']:,} errores</small>
            </div>
        </div>

        <h2>Detalle por Archivo</h2>
        <table>
            <thead>
                <tr>
                    <th>Archivo</th>
                    <th>Total Filas</th>
                    <th>Coordenadas Válidas %</th>
                    <th>Datos Completos %</th>
                    <th>Estado Calidad</th>
                    <th>Fecha Procesamiento</th>
                </tr>
            </thead>
            <tbody>
"""

        # Agregar filas de la tabla
        for report in self.reports:
            stats = report.get('estadisticas', {})
            metrics = report.get('metricas_calidad', {})
            estado = report.get('estado_calidad', 'DESCONOCIDO')

            # Clase CSS según estado
            estado_class = f"status-{estado.lower()}" if estado.lower() in ['excelente', 'aceptable', 'problemas_graves'] else "status-problemas"

            html += f"""
                <tr>
                    <td>{report.get('archivo_origen', '')}</td>
                    <td>{stats.get('total_filas', 0):,}</td>
                    <td>{metrics.get('coordenadas_validas', 0):.1f}%</td>
                    <td>{metrics.get('datos_completos', 0):.1f}%</td>
                    <td class="{estado_class}">{estado.upper()}</td>
                    <td>{report.get('fecha_procesamiento', '').split('T')[0]}</td>
                </tr>
"""

        html += f"""
            </tbody>
        </table>

        <h2>Observaciones para el Equipo Citrino</h2>
        <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 5px; margin-top: 20px;">
            <h3 style="margin-top: 0; color: #856404;">Próximos Pasos:</h3>
            <ol>
                <li>Revisar archivos Excel intermedios en <code>data/processed/</code></li>
                <li>Validar coordenadas geográficas manualmente</li>
                <li>Verificar rangos de precios por zona</li>
                <li>Documentar patrones de error encontrados</li>
                <li>Aprobar archivos que cumplan estándares de calidad</li>
            </ol>
            <p><strong>Archivos listos para revisión:</strong></p>
            <ul>
"""

        # Listar archivos generados
        for report in self.reports:
            filename = report.get('archivo_origen', '')
            if filename:
                base_name = os.path.splitext(filename)[0]
                html += f"                <li><code>{base_name}_intermedio.xlsx</code></li>\n"

        html += f"""
            </ul>
        </div>

        <div class="footer">
            <p>Reporte generado automáticamente por el sistema de validación de Citrino</p>
            <p>Para preguntas o soporte, contactar al equipo de desarrollo</p>
        </div>
    </div>
</body>
</html>
"""

        return html

    def generate_report(self, input_dir: str, output_dir: str) -> bool:
        """
        Generar reporte completo
        """
        print("Generando reporte consolidado de validación...")

        # Cargar reportes
        if not self.load_reports(input_dir):
            return False

        print(f"Reportes cargados: {len(self.reports)}")
        print(f"Total filas procesadas: {self.total_stats['total_filas']:,}")

        # Crear directorio de salida
        os.makedirs(output_dir, exist_ok=True)

        # Generar reporte HTML
        html_success = self.generate_html_report(output_dir)

        # Generar resumen Excel
        excel_success = self.generate_excel_summary(output_dir)

        if html_success and excel_success:
            print("Reporte consolidado generado exitosamente")
            return True
        else:
            print("Error generando reporte consolidado")
            return False


def main():
    """
    Función principal
    """
    parser = argparse.ArgumentParser(description='Generar reporte consolidado de validación')
    parser.add_argument('--input-dir', default='data/processed', help='Directorio con reportes JSON')
    parser.add_argument('--output-dir', default='reports', help='Directorio de salida para reportes')

    args = parser.parse_args()

    generator = ValidationReportGenerator()
    success = generator.generate_report(args.input_dir, args.output_dir)

    if success:
        print("REPORTE GENERADO EXITOSAMENTE")
        print(f"Revisa los archivos en: {args.output_dir}/")
    else:
        print("ERROR GENERANDO REPORTE")

    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)