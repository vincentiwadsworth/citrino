#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Orquestador de Mejora de Extracción de Relevamiento

Este script aplica todas las mejoras implementadas para aumentar la tasa de extracción
de propiedades de data/raw/relevamiento del 79% actual al 95%+ objetivo.

Fases:
1. Reprocesar todos los archivos RAW con validaciones mejoradas
2. Integrar mejoras del Proveedor 02 con LLM
3. Generar reporte de mejoras y nuevas estadísticas

Autor: Claude Code
Fecha: 2025-10-15
"""

import json
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import logging

# Agregar paths para imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts' / 'etl'))

# El ETL se ejecutará directamente con subprocess

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OrquestadorMejoraExtraccion:
    """Orquestador principal para aplicar todas las mejoras de extracción."""

    def __init__(self):
        self.backup_dir = "data/backup"
        self.output_dir = "data"
        self.stats = {
            'estado_inicial': {},
            'estado_final': {},
            'mejoras_aplicadas': [],
            'propiedades_recuperadas': 0,
            'tiempo_procesamiento': 0
        }

    def crear_backup(self) -> bool:
        """Crea backup del dataset actual."""
        try:
            logger.info("Creando backup del dataset actual...")

            # Crear directorio de backup
            Path(self.backup_dir).mkdir(parents=True, exist_ok=True)

            # Timestamp para el backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{self.backup_dir}/base_datos_relevamiento_backup_{timestamp}.json"

            # Copiar archivo actual
            if os.path.exists("data/base_datos_relevamiento.json"):
                shutil.copy2("data/base_datos_relevamiento.json", backup_file)
                logger.info(f"Backup creado en: {backup_file}")
                return True
            else:
                logger.warning("No existe el archivo actual para hacer backup")
                return False

        except Exception as e:
            logger.error(f"Error creando backup: {e}")
            return False

    def cargar_estado_actual(self) -> Dict[str, Any]:
        """Carga el estado actual del dataset."""
        try:
            with open("data/base_datos_relevamiento.json", 'r', encoding='utf-8') as f:
                data = json.load(f)

            propiedades = data.get('propiedades', [])

            # Análisis por proveedor
            por_proveedor = {}
            for prop in propiedades:
                prov = prop.get('codigo_proveedor', 'desconocido')
                if prov not in por_proveedor:
                    por_proveedor[prov] = 0
                por_proveedor[prov] += 1

            estado = {
                'total_propiedades': len(propiedades),
                'por_proveedor': por_proveedor,
                'metadata': data.get('metadata', {}),
                'fecha_procesamiento': data.get('metadata', {}).get('fecha_procesamiento', 'desconocido')
            }

            logger.info(f"Estado actual: {estado['total_propiedades']} propiedades")
            for prov, count in estado['por_proveedor'].items():
                logger.info(f"  Proveedor {prov}: {count} propiedades")

            return estado

        except Exception as e:
            logger.error(f"Error cargando estado actual: {e}")
            return {}

    def ejecutar_etl_mejorado(self) -> Dict[str, Any]:
        """Ejecuta el ETL mejorado con las nuevas validaciones."""
        try:
            logger.info("Ejecutando ETL mejorado...")

            # Importar el procesador mejorado
            import subprocess
            import sys

            # Ejecutar el ETL principal directamente con subprocess
            etl_script = Path(__file__).parent.parent / 'etl' / 'build_relevamiento_dataset.py'

            result = subprocess.run([
                sys.executable, str(etl_script)
            ], capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)

            if result.returncode != 0:
                logger.error(f"Error ejecutando ETL: {result.stderr}")
                return {'success': False, 'error': result.stderr, 'propiedades': []}

            # Cargar los resultados generados
            try:
                with open("data/base_datos_relevamiento.json", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                propiedades = data.get('propiedades', [])
            except Exception as e:
                logger.error(f"Error cargando resultados: {e}")
                return {'success': False, 'error': f'Error cargando resultados: {e}', 'propiedades': []}

            resultado = {
                'success': True,
                'propiedades': propiedades,
                'output_file': "data/base_datos_relevamiento.json",
                'total_procesadas': len(propiedades)
            }

            logger.info(f"ETL mejorado completado: {len(propiedades)} propiedades procesadas")
            return resultado

        except Exception as e:
            logger.error(f"Error en ETL mejorado: {e}")
            return {'success': False, 'error': str(e), 'propiedades': []}

    def analizar_mejoras(self, estado_inicial: Dict[str, Any], estado_final: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza las mejoras obtenidas."""
        try:
            total_inicial = estado_inicial.get('total_propiedades', 0)
            total_final = estado_final.get('total_propiedades', 0)

            propiedades_recuperadas = total_final - total_inicial
            porcentaje_mejora = (propiedades_recuperadas / total_inicial * 100) if total_inicial > 0 else 0

            # Análisis por proveedor
            mejora_por_proveedor = {}
            proveedores_inicial = estado_inicial.get('por_proveedor', {})
            proveedores_final = estado_final.get('por_proveedor', {})

            todos_proveedores = set(proveedores_inicial.keys()) | set(proveedores_final.keys())

            for prov in todos_proveedores:
                inicial = proveedores_inicial.get(prov, 0)
                final = proveedores_final.get(prov, 0)
                mejora = final - inicial
                porc_mejora = (mejora / inicial * 100) if inicial > 0 else 0

                mejora_por_proveedor[prov] = {
                    'inicial': inicial,
                    'final': final,
                    'mejora': mejora,
                    'porcentaje_mejora': porc_mejora
                }

            analisis = {
                'total_inicial': total_inicial,
                'total_final': total_final,
                'propiedades_recuperadas': propiedades_recuperadas,
                'porcentaje_mejora_total': porcentaje_mejora,
                'mejora_por_proveedor': mejora_por_proveedor,
                'tasa_exito_final': (total_final / 2010 * 100) if total_final > 0 else 0,  # 2010 = total raw relevamiento
                'meta_alcanzada': total_final >= 1909  # 95% de 2010
            }

            return analisis

        except Exception as e:
            logger.error(f"Error analizando mejoras: {e}")
            return {}

    def generar_reporte_mejoras(self, analisis: Dict[str, Any]) -> str:
        """Genera un reporte detallado de las mejoras."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            reporte = f"""
# REPORTE DE MEJORA DE EXTRACCIÓN DE RELEVAMIENTO

**Fecha de generación:** {timestamp}
**Script:** mejorar_extraccion_relevamiento.py

## Resumen Ejecutivo

| Métrica | Valor Antes | Valor Después | Mejora |
|---------|-------------|---------------|--------|
| Total propiedades | {analisis['total_inicial']:,} | {analisis['total_final']:,} | +{analisis['propiedades_recuperadas']:,} |
| Tasa de éxito | {(analisis['total_inicial']/2010*100):.1f}% | {analisis['tasa_exito_final']:.1f}% | +{analisis['porcentaje_mejora_total']:.1f}% |
| Meta 95% (1909+) | {'❌' if analisis['total_inicial'] < 1909 else '✅'} | {'✅' if analisis['meta_alcanzada'] else '❌'} | {'LOGRADA' if analisis['meta_alcanzada'] else 'NO ALCANZADA'} |

## Análisis por Proveedor

"""

            for prov, datos in sorted(analisis['mejora_por_proveedor'].items()):
                if prov == '':  # Saltar entradas vacías
                    continue

                status = '📈' if datos['mejora'] > 0 else '➡️'
                reporte += f"### Proveedor {prov} {status}\n"
                reporte += f"- **Antes:** {datos['inicial']:,} propiedades\n"
                reporte += f"- **Después:** {datos['final']:,} propiedades\n"
                reporte += f"- **Mejora:** +{datos['mejora']:,} ({datos['porcentaje_mejora']:+.1f}%)\n\n"

            reporte += f"""
## Mejoras Aplicadas

1. **Validaciones de coordenadas expandidas**: Rango aumentado de (-18.0, -17.0) a (-19.0, -16.0) para latitud y (-63.5, -63.0) a (-65.0, -62.0) para longitud

2. **Validación de propiedades mejorada**: Nueva lógica que permite propiedades con:
   - Título O descripción larga (>50 caracteres)
   - Y precio O coordenadas
   - Más flexible que la validación anterior

3. **Extracción de precios mejorada**:
   - Manejo de formatos decimales europeos (1.234,56)
   - Detección de precios inválidos "0.00 BOB"
   - Soporte para múltiples símbolos de moneda
   - Validación de rangos razonables (1-10M)

4. **Integración LLM para Proveedor 02**:
   - Extracción de datos de descripciones cuando faltan campos
   - Sistema híbrido Regex + LLM
   - Recuperación de precios, ubicación, características

## Conclusiones

- **Propiedades recuperadas:** {analisis['propiedades_recuperadas']:,}
- **Porcentaje de mejora:** {analisis['porcentaje_mejora_total']:.1f}%
- **Meta alcanzada:** {'SÍ ✅' if analisis['meta_alcanzada'] else 'NO ❌'}
- **Próximos pasos:** {'Continuar con optimización de LLM' if not analisis['meta_alcanzada'] else 'Mantener monitoreo y ajustar según sea necesario'}

---
*Reporte generado automáticamente por el orquestador de mejoras*
"""

            return reporte

        except Exception as e:
            logger.error(f"Error generando reporte: {e}")
            return "Error generando reporte"

    def guardar_reporte(self, reporte: str, analisis: Dict[str, Any]) -> str:
        """Guarda el reporte en formato Markdown y JSON."""
        try:
            # Guardar reporte Markdown
            md_path = "docs/reporte_mejoras_extraccion.md"
            Path("docs").mkdir(parents=True, exist_ok=True)

            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(reporte)

            # Guardar datos completos en JSON
            json_path = "docs/reporte_mejoras_extraccion.json"

            datos_completos = {
                'metadata': {
                    'fecha_generacion': datetime.now().isoformat(),
                    'script': 'mejorar_extraccion_relevamiento.py',
                    'version': '1.0'
                },
                'estado_inicial': self.stats['estado_inicial'],
                'estado_final': self.stats['estado_final'],
                'analisis_mejoras': analisis,
                'reporte_markdown': reporte
            }

            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(datos_completos, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"Reportes guardados:")
            logger.info(f"  Markdown: {md_path}")
            logger.info(f"  JSON: {json_path}")

            return md_path

        except Exception as e:
            logger.error(f"Error guardando reporte: {e}")
            return ""

    def ejecutar_mejoras_completas(self) -> Dict[str, Any]:
        """Ejecuta el proceso completo de mejoras."""
        inicio_tiempo = datetime.now()

        logger.info("=" * 80)
        logger.info("INICIANDO PROCESO COMPLETO DE MEJORAS")
        logger.info("=" * 80)

        # 1. Crear backup
        if not self.crear_backup():
            logger.warning("No se pudo crear backup, continuando...")

        # 2. Cargar estado inicial
        logger.info("Cargando estado inicial...")
        estado_inicial = self.cargar_estado_actual()
        self.stats['estado_inicial'] = estado_inicial

        if not estado_inicial:
            logger.error("No se pudo cargar estado inicial, abortando...")
            return {'success': False, 'error': 'No se pudo cargar estado inicial'}

        # 3. Ejecutar ETL mejorado
        resultado_etl = self.ejecutar_etl_mejorado()

        if not resultado_etl['success']:
            logger.error(f"Error en ETL mejorado: {resultado_etl.get('error', 'Error desconocido')}")
            return {'success': False, 'error': resultado_etl.get('error')}

        # 4. Cargar estado final
        logger.info("Cargando estado final...")
        estado_final = self.cargar_estado_actual()
        self.stats['estado_final'] = estado_final

        # 5. Analizar mejoras
        logger.info("Analizando mejoras...")
        analisis = self.analizar_mejoras(estado_inicial, estado_final)

        # 6. Generar reporte
        logger.info("Generando reporte de mejoras...")
        reporte = self.generar_reporte_mejoras(analisis)
        reporte_path = self.guardar_reporte(reporte, analisis)

        # 7. Calcular tiempo total
        fin_tiempo = datetime.now()
        tiempo_total = (fin_tiempo - inicio_tiempo).total_seconds()
        self.stats['tiempo_procesamiento'] = tiempo_total

        # 8. Mostrar resumen final
        logger.info("=" * 80)
        logger.info("RESUMEN FINAL DE MEJORAS")
        logger.info("=" * 80)
        logger.info(f"Propiedades iniciales: {estado_inicial.get('total_propiedades', 0):,}")
        logger.info(f"Propiedades finales: {estado_final.get('total_propiedades', 0):,}")
        logger.info(f"Propiedades recuperadas: {analisis.get('propiedades_recuperadas', 0):,}")
        logger.info(f"Porcentaje mejora: {analisis.get('porcentaje_mejora_total', 0):.1f}%")
        logger.info(f"Tasa éxito final: {analisis.get('tasa_exito_final', 0):.1f}%")
        logger.info(f"Meta 95% alcanzada: {'SÍ' if analisis.get('meta_alcanzada', False) else 'NO'}")
        logger.info(f"Tiempo procesamiento: {tiempo_total:.1f} segundos")
        logger.info(f"Reporte guardado en: {reporte_path}")

        resultado_final = {
            'success': True,
            'estado_inicial': estado_inicial,
            'estado_final': estado_final,
            'analisis': analisis,
            'reporte_path': reporte_path,
            'tiempo_procesamiento': tiempo_total
        }

        return resultado_final

def main():
    """Función principal."""
    print("=" * 80)
    print("ORQUESTADOR DE MEJORA DE EXTRACCIÓN DE RELEVAMIENTO")
    print("=" * 80)

    # Crear orquestador
    orquestador = OrquestadorMejoraExtraccion()

    try:
        # Ejecutar mejoras completas
        resultado = orquestador.ejecutar_mejoras_completas()

        if resultado['success']:
            print("\n[OK] Proceso de mejoras completado exitosamente")
            print(f"[INFO] Propiedades recuperadas: {resultado['analisis']['propiedades_recuperadas']:,}")
            print(f"[INFO] Porcentaje de mejora: {resultado['analisis']['porcentaje_mejora_total']:.1f}%")
            print(f"[INFO] Meta 95% alcanzada: {'SI' if resultado['analisis']['meta_alcanzada'] else 'NO'}")
            print(f"[INFO] Reporte disponible en: {resultado['reporte_path']}")
            return 0
        else:
            print(f"\n[ERROR] Error en el proceso: {resultado.get('error', 'Error desconocido')}")
            return 1

    except Exception as e:
        logger.error(f"Error en el proceso principal: {e}")
        print(f"\n[ERROR] Error critico: {e}")
        return 1

if __name__ == "__main__":
    exit(main())