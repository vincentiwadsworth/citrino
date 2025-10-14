#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de procesamiento con retroalimentación en tiempo real.

Proporciona feedback detallado sobre:
- Progreso de procesamiento por lote
- Calidad de datos extraídos
- Estadísticas de LLM
- Errores y advertencias
- Tiempos de procesamiento
"""

import time
import json
import os
from datetime import datetime
from typing import Dict, Any, List
import logging
from dataclasses import dataclass, asdict
from pathlib import Path

# Importar del procesador incremental
from build_relevamiento_dataset_incremental import ProcesadorIncremental

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MetricasProcesamiento:
    """Métricas detalladas del procesamiento."""
    timestamp: str
    lote_actual: int
    propiedades_en_lote: int
    total_procesadas: int
    total_archivos: int
    archivos_completados: List[str]
    tiempo_procesamiento_lote: float
    tiempo_promedio_propiedad: float

    # Métricas de calidad
    propiedades_con_precio: int
    propiedades_con_ubicacion: int
    propiedades_con_descripcion: int
    propiedades_con_coordenadas: int

    # Métricas LLM
    llamadas_llm: int
    cache_hits_llm: int
    fallback_activado: int
    tokens_estimados: int

    # Errores y advertencias
    errores_count: int
    warnings_count: int
    errores_detalle: List[str]
    warnings_detalle: List[str]

    # Datos por proveedor
    proveedor_stats: Dict[str, Dict[str, int]]

class SistemaFeedback:
    """Sistema de retroalimentación en tiempo real."""

    def __init__(self, output_dir: str = "data"):
        self.output_dir = output_dir
        self.feedback_file = os.path.join(output_dir, 'feedback_procesamiento.json')
        self.log_file = os.path.join(output_dir, 'procesamiento_detailed.log')
        self.inicio_tiempo = time.time()

        # Configurar logger detallado
        self.logger_detalles = logging.getLogger('detalles_procesamiento')
        handler = logging.FileHandler(self.log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger_detalles.addHandler(handler)
        self.logger_detalles.setLevel(logging.INFO)

        # Métricas acumuladas
        self.metricas_acumuladas = {
            'lotes_procesados': 0,
            'propiedades_totales': 0,
            'tiempo_total': 0,
            'errores_totales': 0,
            'warnings_totales': 0,
            'llm_llamadas_totales': 0,
            'llm_cache_hits_totales': 0
        }

    def generar_feedback_lote(self, procesador: ProcesadorIncremental,
                            lote_numero: int, propiedades_lote: List[Dict[str, Any]],
                            tiempo_lote: float) -> MetricasProcesamiento:
        """
        Genera métricas detalladas de un lote procesado.

        Args:
            procesador: Instancia del procesador
            lote_numero: Número del lote
            propiedades_lote: Lista de propiedades del lote
            tiempo_lote: Tiempo de procesamiento del lote

        Returns:
            Métricas detalladas del procesamiento
        """
        timestamp = datetime.now().isoformat()
        total_propiedades = procesador.processed_count

        # Calcular métricas de calidad
        propiedades_con_precio = sum(1 for p in propiedades_lote if p.get('precio'))
        propiedades_con_ubicacion = sum(1 for p in propiedades_lote if p.get('zona'))
        propiedades_con_descripcion = sum(1 for p in propiedades_lote if p.get('descripcion'))
        propiedades_con_coordenadas = sum(1 for p in propiedades_lote
                                       if p.get('latitud') and p.get('longitud'))

        # Obtener estadísticas LLM si están disponibles
        llamadas_llm = 0
        cache_hits_llm = 0
        fallback_activado = 0
        tokens_estimados = 0

        if procesador.description_parser:
            stats = procesador.description_parser.get_stats()
            llamadas_llm = stats.get('total_calls', 0)
            cache_hits_llm = stats.get('cache_hits', 0)
            fallback_activado = stats.get('fallback_count', 0)
            tokens_estimados = stats.get('total_tokens', 0)

        # Analizar errores y advertencias
        errores_detalle = []
        warnings_detalle = []

        for prop in propiedades_lote:
            # Verificar datos críticos faltantes
            if not prop.get('precio') and not (prop.get('latitud') and prop.get('longitud')):
                errores_detalle.append(f"Propiedad {prop['id']}: Sin precio ni coordenadas")

            # Verificar precios fuera de rango
            if prop.get('precio'):
                precio = prop['precio']
                if isinstance(precio, (int, float)):
                    if prop.get('moneda') == 'USD' and precio < 1000:
                        warnings_detalle.append(f"Propiedad {prop['id']}: Precio USD muy bajo ${precio}")
                    elif prop.get('moneda') == 'Bs' and precio < 5000:
                        warnings_detalle.append(f"Propiedad {prop['id']}: Precio Bs muy bajo Bs{precio}")

        # Estadísticas por proveedor
        proveedor_stats = {}
        for prop in propiedades_lote:
            proveedor = prop.get('codigo_proveedor', 'desconocido')
            if proveedor not in proveedor_stats:
                proveedor_stats[proveedor] = {
                    'total': 0,
                    'con_precio': 0,
                    'con_ubicacion': 0,
                    'llm_enriquecidas': 0
                }

            proveedor_stats[proveedor]['total'] += 1
            if prop.get('precio'):
                proveedor_stats[proveedor]['con_precio'] += 1
            if prop.get('zona'):
                proveedor_stats[proveedor]['con_ubicacion'] += 1
            if prop.get('precio_origen') == 'llm_extraction':
                proveedor_stats[proveedor]['llm_enriquecidas'] += 1

        tiempo_promedio = tiempo_lote / len(propiedades_lote) if propiedades_lote else 0

        return MetricasProcesamiento(
            timestamp=timestamp,
            lote_actual=lote_numero,
            propiedades_en_lote=len(propiedades_lote),
            total_procesadas=total_propiedades,
            total_archivos=len(procesador.encontrar_archivos_excel()),
            archivos_completados=procesador.total_processed_files.copy(),
            tiempo_procesamiento_lote=tiempo_lote,
            tiempo_promedio_propiedad=tiempo_promedio,

            propiedades_con_precio=propiedades_con_precio,
            propiedades_con_ubicacion=propiedades_con_ubicacion,
            propiedades_con_descripcion=propiedades_con_descripcion,
            propiedades_con_coordenadas=propiedades_con_coordenadas,

            llamadas_llm=llamadas_llm,
            cache_hits_llm=cache_hits_llm,
            fallback_activado=fallback_activado,
            tokens_estimados=tokens_estimados,

            errores_count=len(errores_detalle),
            warnings_count=len(warnings_detalle),
            errores_detalle=errores_detalle,
            warnings_detalle=warnings_detalle,

            proveedor_stats=proveedor_stats
        )

    def guardar_feedback(self, metricas: MetricasProcesamiento):
        """
        Guarda las métricas en archivo JSON y muestra resumen.

        Args:
            metricas: Métricas del lote procesado
        """
        # Guardar en archivo JSON
        feedback_data = {
            'ultima_actualizacion': metricas.timestamp,
            'metricas_actuales': asdict(metricas),
            'metricas_acumuladas': self.metricas_acumuladas
        }

        os.makedirs(self.output_dir, exist_ok=True)
        with open(self.feedback_file, 'w', encoding='utf-8') as f:
            json.dump(feedback_data, f, ensure_ascii=False, indent=2)

        # Actualizar métricas acumuladas
        self.metricas_acumuladas['lotes_procesados'] += 1
        self.metricas_acumuladas['propiedades_totales'] += metricas.propiedades_en_lote
        self.metricas_acumuladas['tiempo_total'] += metricas.tiempo_procesamiento_lote
        self.metricas_acumuladas['errores_totales'] += metricas.errores_count
        self.metricas_acumuladas['warnings_totales'] += metricas.warnings_count
        self.metricas_acumuladas['llm_llamadas_totales'] += metricas.llamadas_llm
        self.metricas_acumuladas['llm_cache_hits_totales'] += metricas.cache_hits_llm

        # Mostrar resumen en consola
        self.mostrar_resumen_lote(metricas)

        # Guardar en log detallado
        self.logger_detalles.info(f"LOTE {metricas.lote_actual} COMPLETADO")
        self.logger_detalles.info(f"Propiedades: {metricas.propiedades_en_lote}")
        self.logger_detalles.info(f"Tiempo: {metricas.tiempo_procesamiento_lote:.2f}s")
        self.logger_detalles.info(f"Calidad - Precio: {metricas.propiedades_con_precio}/{metricas.propiedades_en_lote}")
        self.logger_detalles.info(f"Calidad - Ubicación: {metricas.propiedades_con_ubicacion}/{metricas.propiedades_en_lote}")

        if metricas.errores_detalle:
            self.logger_detalles.warning(f"ERRORES: {len(metricas.errores_detalle)}")
            for error in metricas.errores_detalle:
                self.logger_detalles.warning(f"  - {error}")

        if metricas.warnings_detalle:
            self.logger_detalles.warning(f"WARNINGS: {len(metricas.warnings_detalle)}")
            for warning in metricas.warnings_detalle:
                self.logger_detalles.warning(f"  - {warning}")

    def mostrar_resumen_lote(self, metricas: MetricasProcesamiento):
        """
        Muestra un resumen claro y conciso del lote procesado.

        Args:
            metricas: Métricas del lote
        """
        print("\n" + "="*60)
        print(f"LOTE {metricas.lote_actual} COMPLETADO - {metricas.timestamp}")
        print("="*60)

        # Progreso general
        progreso = (metricas.total_procesadas / (metricas.total_archivos * 100)) * 100  # Estimado
        print(f"PROGRESO: {metricas.total_procesadas:,} propiedades procesadas")
        print(f"Archivos: {len(metricas.archivos_completados)}/{metricas.total_archivos} completados")

        # Rendimiento
        print(f"\nRENDIMIENTO:")
        print(f"  Tiempo lote: {metricas.tiempo_procesamiento_lote:.1f}s")
        print(f"  Promedio/propiedad: {metricas.tiempo_promedio_propiedad:.2f}s")

        # Calidad de datos
        calidad_precio = (metricas.propiedades_con_precio / metricas.propiedades_en_lote) * 100
        calidad_ubicacion = (metricas.propiedades_con_ubicacion / metricas.propiedades_en_lote) * 100
        calidad_coords = (metricas.propiedades_con_coordenadas / metricas.propiedades_en_lote) * 100

        print(f"\nCALIDAD DE DATOS:")
        print(f"  Con precio: {metricas.propiedades_con_precio}/{metricas.propiedades_en_lote} ({calidad_precio:.1f}%)")
        print(f"  Con ubicación: {metricas.propiedades_con_ubicacion}/{metricas.propiedades_en_lote} ({calidad_ubicacion:.1f}%)")
        print(f"  Con coordenadas: {metricas.propiedades_con_coordenadas}/{metricas.propiedades_en_lote} ({calidad_coords:.1f}%)")

        # Estadísticas LLM
        if metricas.llamadas_llm > 0:
            cache_hit_rate = (metricas.cache_hits_llm / metricas.llamadas_llm) * 100
            print(f"\nESTADÍSTICAS LLM:")
            print(f"  Llamadas: {metricas.llamadas_llm}")
            print(f"  Cache hits: {metricas.cache_hits_llm} ({cache_hit_rate:.1f}%)")
            print(f"  Fallbacks: {metricas.fallback_activado}")
            print(f"  Tokens estimados: {metricas.tokens_estimados:,}")

        # Errores y advertencias
        if metricas.errores_count > 0 or metricas.warnings_count > 0:
            print(f"\nPROBLEMAS DETECTADOS:")
            if metricas.errores_count > 0:
                print(f"  ERRORES: {metricas.errores_count}")
            if metricas.warnings_count > 0:
                print(f"  WARNINGS: {metricas.warnings_count}")

        # Estadísticas por proveedor
        if metricas.proveedor_stats:
            print(f"\nESTADÍSTICAS POR PROVEEDOR:")
            for proveedor, stats in metricas.proveedor_stats.items():
                print(f"  {proveedor}: {stats['total']} propiedades")
                if stats.get('llm_enriquecidas', 0) > 0:
                    print(f"    LLM enriquecidas: {stats['llm_enriquecidas']}")

        print("="*60)

    def mostrar_resumen_final(self):
        """Muestra el resumen final del procesamiento."""
        tiempo_total = time.time() - self.inicio_tiempo

        print("\n" + "="*60)
        print("PROCESAMIENTO FINALIZADO - RESUMEN COMPLETO")
        print("="*60)

        print(f"TIEMPO TOTAL: {tiempo_total/60:.1f} minutos")
        print(f"LOTES PROCESADOS: {self.metricas_acumuladas['lotes_procesados']}")
        print(f"PROPIEDADES TOTALES: {self.metricas_acumuladas['propiedades_totales']:,}")

        if self.metricas_acumuladas['propiedades_totales'] > 0:
            promedio_general = tiempo_total / self.metricas_acumuladas['propiedades_totales']
            print(f"TIEMPO PROMEDIO/PROPIEDAD: {promedio_general:.2f}s")

        print(f"\ERRORES TOTALES: {self.metricas_acumuladas['errores_totales']}")
        print(f"WARNINGS TOTALES: {self.metricas_acumuladas['warnings_totales']}")

        if self.metricas_acumuladas['llm_llamadas_totales'] > 0:
            print(f"\LLM - Llamadas totales: {self.metricas_acumuladas['llm_llamadas_totales']}")
            print(f"LLM - Cache hits: {self.metricas_acumuladas['llm_cache_hits_totales']}")

            cache_rate = (self.metricas_acumuladas['llm_cache_hits_totales'] /
                        self.metricas_acumuladas['llm_llamadas_totales']) * 100
            print(f"LLM - Cache hit rate: {cache_rate:.1f}%")

        print(f"\ARCHIVO DETALLADO: {self.log_file}")
        print(f"ARCHIVO FEEDBACK: {self.feedback_file}")
        print("="*60)


class ProcesadorConFeedback(ProcesadorIncremental):
    """Procesador incremental con sistema de feedback integrado."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sistema_feedback = SistemaFeedback(self.output_dir)
        self.lotes_procesados = []

    def guardar_lote_incremental(self, propiedades_lote: List[Dict[str, Any]],
                                lote_numero: int, es_final: bool = False) -> str:
        """
        Guarda lote con sistema de feedback.

        Args:
            propiedades_lote: Lista de propiedades del lote
            lote_numero: Número del lote
            es_final: Si es el último lote

        Returns:
            Ruta del archivo guardado
        """
        # Medir tiempo de procesamiento
        inicio_lote = time.time()

        # Llamar al método original
        output_file = super().guardar_lote_incremental(propiedades_lote, lote_numero, es_final)

        # Calcular tiempo de procesamiento
        tiempo_lote = time.time() - inicio_lote

        # Generar y guardar feedback
        metricas = self.sistema_feedback.generar_feedback_lote(
            self, lote_numero, propiedades_lote, tiempo_lote
        )
        self.sistema_feedback.guardar_feedback(metricas)

        # Guardar métricas del lote
        self.lotes_procesados.append(metricas)

        return output_file

    def procesar_todos_los_archivos_incremental(self) -> List[Dict[str, Any]]:
        """
        Procesa todos los archivos con feedback y muestra resumen final.

        Returns:
            Lista de todas las propiedades procesadas
        """
        try:
            # Procesar usando el método del padre
            propiedades = super().procesar_todos_los_archivos_incremental()

            # Mostrar resumen final
            self.sistema_feedback.mostrar_resumen_final()

            return propiedades

        except KeyboardInterrupt:
            print("\nPROCESAMIENTO INTERRUMPIDO POR USUARIO")
            self.sistema_feedback.mostrar_resumen_final()
            raise
        except Exception as e:
            print(f"\nERROR EN PROCESAMIENTO: {e}")
            self.sistema_feedback.mostrar_resumen_final()
            raise


def main():
    """Función principal con sistema de feedback."""
    import argparse

    parser = argparse.ArgumentParser(description='Procesamiento con retroalimentación')
    parser.add_argument('--batch-size', type=int, default=20,
                       help='Tamaño de lote (default: 20)')
    parser.add_argument('--max-archivos', type=int,
                       help='Limitar número de archivos')
    parser.add_argument('--max-propiedades', type=int,
                       help='Limitar número de propiedades')

    args = parser.parse_args()

    print("INICIANDO PROCESAMIENTO CON SISTEMA DE FEEDBACK")
    print(f"Tamaño de lote: {args.batch_size} propiedades")

    # Crear procesador con feedback
    procesador = ProcesadorConFeedback(
        batch_size=args.batch_size,
        enable_llm=True
    )

    try:
        # Elegir modo de procesamiento
        if args.max_archivos or args.max_propiedades:
            propiedades = procesador.procesar_archivos_por_bloque(
                max_archivos=args.max_archivos,
                max_propiedades=args.max_propiedades
            )
        else:
            propiedades = procesador.procesar_todos_los_archivos_incremental()

        if propiedades:
            print(f"\nPROCESAMIENTO EXITOSO: {len(propiedades):,} propiedades procesadas")
        else:
            print("\nNo se procesaron propiedades")

    except KeyboardInterrupt:
        print("\nProcesamiento interrumpido. Estado guardado.")
    except Exception as e:
        print(f"\nError en procesamiento: {e}")


if __name__ == "__main__":
    main()