#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Monitoreo Avanzado para ETL

Este módulo proporciona monitoreo en tiempo real del procesamiento ETL,
métricas de calidad, uso de IA y análisis de rendimiento.
"""

import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from collections import defaultdict, deque
import threading
from dataclasses import dataclass, asdict
import sys

# Agregar path para importar módulos
sys.path.append(str(Path(__file__).parent))

from llm_integration import LLMIntegration

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MetricaRealTime:
    """Métrica en tiempo real del sistema."""
    timestamp: datetime
    propiedad_id: str
    proveedor: str
    operacion: str
    duracion_segundos: float
    estado: str  # 'exito', 'error', 'parcial'
    tokens_usados: int = 0
    costo_usd: float = 0.0
    mejoras_aplicadas: List[str] = None
    errores: List[str] = None

    def __post_init__(self):
        if self.mejoras_aplicadas is None:
            self.mejoras_aplicadas = []
        if self.errores is None:
            self.errores = []

@dataclass
class EstadisticasProveedores:
    """Estadísticas acumuladas por proveedor."""
    proveedor: str
    total_propiedades: int = 0
    propiedades_procesadas: int = 0
    exitos: int = 0
    errores: int = 0
    tiempo_total_segundos: float = 0.0
    tokens_totales: int = 0
    costo_total_usd: float = 0.0
    mejoras_aplicadas: Dict[str, int] = None
    tasa_exito: float = 0.0
    tiempo_promedio_segundos: float = 0.0

    def __post_init__(self):
        if self.mejoras_aplicadas is None:
            self.mejoras_aplicadas = defaultdict(int)

    def actualizar_tasas(self):
        """Actualiza las tasas calculadas."""
        if self.propiedades_procesadas > 0:
            self.tasa_exito = (self.exitos / self.propiedades_procesadas) * 100
            self.tiempo_promedio_segundos = self.tiempo_total_segundos / self.propiedades_procesadas

class ETLMonitor:
    """Sistema de monitoreo avanzado para ETL."""

    def __init__(self):
        self.metricas_recientes = deque(maxlen=1000)  # últimas 1000 métricas
        self.estadisticas_proveedores = {}
        self.llm_stats = {
            'total_tokens': 0,
            'total_costo_usd': 0.0,
            'calls_zai': 0,
            'calls_openrouter': 0,
            'calls_failed': 0,
            'cache_hits': 0
        }
        self.alertas = []
        self.inicio_monitoreo = datetime.now()
        self._lock = threading.Lock()

        # Umbrales para alertas
        self.umbrales_alertas = {
            'tasa_error_maxima': 10.0,  # %
            'tiempo_procesamiento_maximo': 30.0,  # segundos
            'costo_maximo_usd': 50.0,  # por batch
            'tasa_exito_minima': 90.0  # %
        }

    def iniciar_medicion(self, propiedad_id: str, proveedor: str, operacion: str) -> str:
        """Inicia la medición de una operación."""
        medicion_id = f"{propiedad_id}_{int(time.time() * 1000)}"

        with self._lock:
            # Registrar inicio
            self.metricas_recientes.append({
                'medicion_id': medicion_id,
                'timestamp_inicio': datetime.now(),
                'propiedad_id': propiedad_id,
                'proveedor': proveedor,
                'operacion': operacion,
                'estado': 'en_progreso'
            })

        return medicion_id

    def finalizar_medicion(self, medicion_id: str, estado: str = 'exito',
                          mejoras_aplicadas: List[str] = None,
                          errores: List[str] = None,
                          tokens_usados: int = 0,
                          costo_usd: float = 0.0):
        """Finaliza la medición de una operación."""
        with self._lock:
            # Buscar la medición iniciada
            for i, metrica in enumerate(self.metricas_recientes):
                if isinstance(metrica, dict) and metrica.get('medicion_id') == medicion_id:
                    # Calcular duración
                    duracion = (datetime.now() - metrica['timestamp_inicio']).total_seconds()

                    # Crear métrica completa
                    metrica_completa = MetricaRealTime(
                        timestamp=datetime.now(),
                        propiedad_id=metrica['propiedad_id'],
                        proveedor=metrica['proveedor'],
                        operacion=metrica['operacion'],
                        duracion_segundos=duracion,
                        estado=estado,
                        tokens_usados=tokens_usados,
                        costo_usd=costo_usd,
                        mejoras_aplicadas=mejoras_aplicadas or [],
                        errores=errores or []
                    )

                    # Reemplazar métrica incompleta con completa
                    self.metricas_recientes[i] = metrica_completa

                    # Actualizar estadísticas del proveedor
                    self._actualizar_estadisticas_proveedor(metrica_completa)

                    # Actualizar estadísticas de LLM
                    self._actualizar_estadisticas_llm(metrica_completa)

                    # Verificar alertas
                    self._verificar_alertas(metrica_completa)

                    break

    def _actualizar_estadisticas_proveedor(self, metrica: MetricaRealTime):
        """Actualiza estadísticas acumuladas del proveedor."""
        proveedor = metrica.proveedor
        if proveedor not in self.estadisticas_proveedores:
            self.estadisticas_proveedores[proveedor] = EstadisticasProveedores(proveedor=proveedor)
        stats = self.estadisticas_proveedores[proveedor]

        stats.proveedor = proveedor
        stats.propiedades_procesadas += 1
        stats.tiempo_total_segundos += metrica.duracion_segundos
        stats.tokens_totales += metrica.tokens_usados
        stats.costo_total_usd += metrica.costo_usd

        if metrica.estado == 'exito':
            stats.exitos += 1
            for mejora in metrica.mejoras_aplicadas:
                stats.mejoras_aplicadas[mejora] += 1
        else:
            stats.errores += 1

        stats.actualizar_tasas()

    def _actualizar_estadisticas_llm(self, metrica: MetricaRealTime):
        """Actualiza estadísticas de uso de LLM."""
        self.llm_stats['total_tokens'] += metrica.tokens_usados
        self.llm_stats['total_costo_usd'] += metrica.costo_usd

        # Podríamos determinar el proveedor usado basado en el costo/tokens
        # Por ahora, actualizamos genéricamente
        if metrica.tokens_usados > 0:
            self.llm_stats['calls_zai'] += 1  # Asumimos z.ai como primario

    def _verificar_alertas(self, metrica: MetricaRealTime):
        """Verifica si se deben generar alertas."""
        alertas_generadas = []

        # Alerta por tasa de errores alta
        stats_prov = self.estadisticas_proveedores[metrica.proveedor]
        if stats_prov.propiedades_procesadas >= 10:  # Mínimo 10 para tener estadísticas significativas
            if stats_prov.tasa_exito < self.umbrales_alertas['tasa_exito_minima']:
                alerta = {
                    'timestamp': datetime.now(),
                    'tipo': 'TASA_EXITO_BAJA',
                    'proveedor': metrica.proveedor,
                    'descripcion': f"Tasa de éxito {stats_prov.tasa_exito:.1f}% (< {self.umbrales_alertas['tasa_exito_minima']}%)",
                    'nivel': 'ALTO'
                }
                alertas_generadas.append(alerta)

        # Alerta por tiempo de procesamiento largo
        if metrica.duracion_segundos > self.umbrales_alertas['tiempo_procesamiento_maximo']:
            alerta = {
                'timestamp': datetime.now(),
                'tipo': 'TIEMPO_PROCESAMIENTO_ALTO',
                'propiedad_id': metrica.propiedad_id,
                'descripcion': f"Procesamiento {metrica.duracion_segundos:.1f}s (> {self.umbrales_alertas['tiempo_procesamiento_maximo']}s)",
                'nivel': 'MEDIO'
            }
            alertas_generadas.append(alerta)

        # Alerta por costo elevado
        stats_prov = self.estadisticas_proveedores[metrica.proveedor]
        if stats_prov.costo_total_usd > self.umbrales_alertas['costo_maximo_usd']:
            alerta = {
                'timestamp': datetime.now(),
                'tipo': 'COSTO_ELEVADO',
                'proveedor': metrica.proveedor,
                'descripcion': f"Costo acumulado ${stats_prov.costo_total_usd:.2f} USD (> ${self.umbrales_alertas['costo_maximo_usd']} USD)",
                'nivel': 'ALTO'
            }
            alertas_generadas.append(alerta)

        # Agregar alertas a la lista
        self.alertas.extend(alertas_generadas)

        # Mantener solo últimas 100 alertas
        if len(self.alertas) > 100:
            self.alertas = self.alertas[-100:]

    def obtener_dashboard_real_time(self) -> Dict[str, Any]:
        """Genera dashboard en tiempo real."""
        with self._lock:
            # Estadísticas generales
            total_propiedades = sum(stats.propiedades_procesadas for stats in self.estadisticas_proveedores.values())
            total_exitos = sum(stats.exitos for stats in self.estadisticas_proveedores.values())
            tasa_exito_global = (total_exitos / total_propiedades * 100) if total_propiedades > 0 else 0

            # Métricas recientes (última hora)
            hora_atras = datetime.now() - timedelta(hours=1)
            metricas_recientes = [
                m for m in self.metricas_recientes
                if isinstance(m, MetricaRealTime) and m.timestamp > hora_atras
            ]

            # Tiempo de actividad
            tiempo_actividad = datetime.now() - self.inicio_monitoreo

            dashboard = {
                'timestamp': datetime.now().isoformat(),
                'tiempo_actividad_segundos': tiempo_actividad.total_seconds(),
                'resumen_general': {
                    'total_propiedades_procesadas': total_propiedades,
                    'tasa_exito_global': round(tasa_exito_global, 2),
                    'total_tokens_usados': self.llm_stats['total_tokens'],
                    'costo_total_usd': round(self.llm_stats['total_costo_usd'], 4),
                    'llm_calls_exitosos': self.llm_stats['calls_zai'],
                    'llm_calls_fallidos': self.llm_stats['calls_failed']
                },
                'proveedores': {},
                'metricas_recientes_hora': {
                    'total_operaciones': len(metricas_recientes),
                    'tiempo_promedio_segundos': 0,
                    'operaciones_por_minuto': 0,
                    'mejoras_aplicadas': defaultdict(int),
                    'estados': defaultdict(int)
                },
                'alertas_activas': self._filtrar_alertas_activas(),
                'rendimiento_sistema': self._calcular_rendimiento_sistema()
            }

            # Estadísticas por proveedor
            for codigo, stats in self.estadisticas_proveedores.items():
                dashboard['proveedores'][codigo] = {
                    'nombre': self._obtener_nombre_proveedor(codigo),
                    'propiedades_procesadas': stats.propiedades_procesadas,
                    'tasa_exito': round(stats.tasa_exito, 2),
                    'tiempo_promedio_segundos': round(stats.tiempo_promedio_segundos, 2),
                    'tokens_usados': stats.tokens_totales,
                    'costo_usd': round(stats.costo_total_usd, 4),
                    'mejoras_aplicadas': dict(stats.mejoras_aplicadas)
                }

            # Métricas recientes
            if metricas_recientes:
                tiempo_promedio = sum(m.duracion_segundos for m in metricas_recientes) / len(metricas_recientes)
                dashboard['metricas_recientes_hora']['tiempo_promedio_segundos'] = round(tiempo_promedio, 2)

                # Operaciones por minuto
                if metricas_recientes:
                    tiempo_minutos = max(1, (datetime.now() - metricas_recientes[0].timestamp).total_seconds() / 60)
                    dashboard['metricas_recientes_hora']['operaciones_por_minuto'] = round(len(metricas_recientes) / tiempo_minutos, 2)

                # Estados
                for metrica in metricas_recientes:
                    dashboard['metricas_recientes_hora']['estados'][metrica.estado] += 1
                    for mejora in metrica.mejoras_aplicadas:
                        dashboard['metricas_recientes_hora']['mejoras_aplicadas'][mejora] += 1

            return dashboard

    def _obtener_nombre_proveedor(self, codigo: str) -> str:
        """Obtiene el nombre descriptivo del proveedor."""
        nombres = {
            '01': 'UltraCasas',
            '02': 'RE/MAX',
            '03': 'C21',
            '04': 'CapitalCorp',
            '05': 'BienInmuebles'
        }
        return nombres.get(codigo, f'Proveedor {codigo}')

    def _filtrar_alertas_activas(self) -> List[Dict[str, Any]]:
        """Filtra alertas activas (últimas 24 horas)."""
        dia_atras = datetime.now() - timedelta(hours=24)
        return [
            alerta for alerta in self.alertas
            if alerta['timestamp'] > dia_atras
        ]

    def _calcular_rendimiento_sistema(self) -> Dict[str, Any]:
        """Calcula métricas de rendimiento del sistema."""
        metricas = [m for m in self.metricas_recientes if isinstance(m, MetricaRealTime)]

        if not metricas:
            return {
                'estado': 'SIN_DATOS',
                'operaciones_recientes': 0,
                'tiempo_actividad': (datetime.now() - self.inicio_monitoreo).total_seconds()
            }

        # Últimas 100 operaciones
        ultimas_100 = metricas[-100:] if len(metricas) >= 100 else metricas

        # Calcular métricas
        operaciones_ultimo_minuto = len([
            m for m in ultimas_100
            if (datetime.now() - m.timestamp).total_seconds() <= 60
        ])

        # Determinar estado del sistema
        estado = 'EXCELLENTE'
        if operaciones_ultimo_minuto < 5:
            estado = 'LENT'
        elif operaciones_ultimo_minuto > 100:
            estado = 'SOBRECARGA'

        return {
            'estado': estado,
            'operaciones_recientes': len(ultimas_100),
            'operaciones_por_minuto': operaciones_ultimo_minuto,
            'latencia_promedio_segundos': sum(m.duracion_segundos for m in ultimas_100) / len(ultimas_100),
            'uso_memoria_estimado_mb': len(self.metricas_recientes) * 0.1,  # Estimación simple
            'tiempo_actividad_segundos': (datetime.now() - self.inicio_monitoreo).total_seconds()
        }

    def generar_reporte_periodico(self, periodo_horas: int = 24) -> Dict[str, Any]:
        """Genera reporte periódico del rendimiento."""
        periodo_inicio = datetime.now() - timedelta(hours=periodo_horas)

        with self._lock:
            # Filtrar métricas del período
            metricas_periodo = [
                m for m in self.metricas_recientes
                if isinstance(m, MetricaRealTime) and m.timestamp > periodo_inicio
            ]

            # Alertas del período
            alertas_periodo = [
                a for a in self.alertas
                if a['timestamp'] > periodo_inicio
            ]

            if not metricas_periodo:
                return {
                    'periodo': f'Últimas {periodo_horas} horas',
                    'estado': 'SIN_ACTIVIDAD',
                    'timestamp': datetime.now().isoformat()
                }

            # Análisis por proveedor
            analisis_proveedores = {}
            for codigo in set(m.proveedor for m in metricas_periodo):
                metricas_prov = [m for m in metricas_periodo if m.proveedor == codigo]

                exitos = len([m for m in metricas_prov if m.estado == 'exito'])
                errores = len([m for m in metricas_prov if m.estado == 'error'])

                analisis_proveedores[codigo] = {
                    'nombre': self._obtener_nombre_proveedor(codigo),
                    'operaciones': len(metricas_prov),
                    'tasa_exito': round((exitos / len(metricas_prov)) * 100, 2) if metricas_prov else 0,
                    'tiempo_promedio_segundos': round(sum(m.duracion_segundos for m in metricas_prov) / len(metricas_prov), 2) if metricas_prov else 0,
                    'tokens_usados': sum(m.tokens_usados for m in metricas_prov),
                    'costo_usd': round(sum(m.costo_usd for m in metricas_prov), 4),
                    'mejoras_totales': sum(len(m.mejoras_aplicadas) for m in metricas_prov)
                }

            # Análisis de alertas
            alertas_por_tipo = defaultdict(int)
            alertas_por_nivel = defaultdict(int)
            for alerta in alertas_periodo:
                alertas_por_tipo[alerta['tipo']] += 1
                alertas_por_nivel[alerta['nivel']] += 1

            # Tendencias
            operaciones_por_hora = defaultdict(int)
            for metrica in metricas_periodo:
                hora = metrica.timestamp.hour
                operaciones_por_hora[hora] += 1

            # Recomendaciones
            recomendaciones = self._generar_recomendaciones(analisis_proveedores, alertas_periodo)

            return {
                'periodo': f'Últimas {periodo_horas} horas',
                'timestamp': datetime.now().isoformat(),
                'resumen': {
                    'total_operaciones': len(metricas_periodo),
                    'tasa_exito_global': round((len([m for m in metricas_periodo if m.estado == 'exito']) / len(metricas_periodo)) * 100, 2) if metricas_periodo else 0,
                    'tokens_consumidos': sum(m.tokens_usados for m in metricas_periodo),
                    'costo_total_usd': round(sum(m.costo_usd for m in metricas_periodo), 4),
                    'total_alertas': len(alertas_periodo)
                },
                'analisis_proveedores': analisis_proveedores,
                'analisis_alertas': {
                    'total_alertas': len(alertas_periodo),
                    'alertas_por_tipo': dict(alertas_por_tipo),
                    'alertas_por_nivel': dict(alertas_por_nivel)
                },
                'tendencias': {
                    'operaciones_por_hora': dict(operaciones_por_hora),
                    'hora_pico': max(operaciones_por_hora.items(), key=lambda x: x[1])[0] if operaciones_por_hora else None
                },
                'recomendaciones': recomendaciones,
                'estado_sistema': self._evaluar_estado_sistema(metricas_periodo, alertas_periodo)
            }

    def _generar_recomendaciones(self, analisis_proveedores: Dict[str, Any], alertas: List[Dict[str, Any]]) -> List[str]:
        """Genera recomendaciones basadas en el análisis."""
        recomendaciones = []

        # Recomendaciones por proveedor
        for codigo, analisis in analisis_proveedores.items():
            if analisis['tasa_exito'] < 90:
                recomendaciones.append(f"Revisar estrategia del Proveedor {analisis['nombre']} - tasa de éxito baja ({analisis['tasa_exito']}%)")

            if analisis['tiempo_promedio_segundos'] > 20:
                recomendaciones.append(f"Optimizar procesamiento del Proveedor {analisis['nombre']} - tiempo promedio alto ({analisis['tiempo_promedio_segundos']}s)")

        # Recomendaciones por costos
        costo_total = sum(analisis['costo_usd'] for analisis in analisis_proveedores.values())
        if costo_total > 10:  # Más de $10 USD en el período
            recomendaciones.append("Considerar optimizar el uso de IA para reducir costos")

        # Recomendaciones por alertas
        alertas_criticas = [a for a in alertas if a.get('nivel') == 'ALTO']
        if len(alertas_criticas) > 5:
            recomendaciones.append("Investigar causas de alertas críticas frecuentes")

        if not recomendaciones:
            recomendaciones.append("Sistema funcionando dentro de parámetros normales")

        return recomendaciones

    def _evaluar_estado_sistema(self, metricas: List[MetricaRealTime], alertas: List[Dict[str, Any]]) -> str:
        """Evalúa el estado general del sistema."""
        if not metricas:
            return 'INACTIVO'

        tasa_exito = (len([m for m in metricas if m.estado == 'exito']) / len(metricas)) * 100
        alertas_criticas = len([a for a in alertas if a.get('nivel') == 'ALTO'])

        if tasa_exito >= 95 and alertas_criticas == 0:
            return 'EXCELENTE'
        elif tasa_exito >= 90 and alertas_criticas <= 2:
            return 'BUENO'
        elif tasa_exito >= 80 and alertas_criticas <= 5:
            return 'ACEPTABLE'
        else:
            return 'REQUIERE_ATENCION'

    def guardar_dashboard(self, output_path: str = "data/dashboard_etl.json"):
        """Guarda el dashboard actual."""
        try:
            dashboard = self.obtener_dashboard_real_time()

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(dashboard, f, ensure_ascii=False, indent=2, default=str)

            return output_path
        except Exception as e:
            logger.error(f"Error guardando dashboard: {e}")
            return None

    def iniciar_monitoreo_web(self, port: int = 8081):
        """Inicia servidor web para monitoreo en tiempo real."""
        try:
            from flask import Flask, jsonify, render_template_string
            import threading

            app = Flask(__name__)

            @app.route('/')
            def dashboard_web():
                return render_template_string(DASHBOARD_TEMPLATE,
                                            dashboard=self.obtener_dashboard_real_time())

            @app.route('/api/dashboard')
            def api_dashboard():
                return jsonify(self.obtener_dashboard_real_time())

            @app.route('/api/reporte/<int:horas>')
            def api_reporte(horas):
                return jsonify(self.generar_reporte_periodico(horas))

            def run_server():
                app.run(host='0.0.0.0', port=port, debug=False)

            # Iniciar servidor en hilo separado
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()

            logger.info(f"Monitoreo web iniciado en http://localhost:{port}")
            return True

        except ImportError:
            logger.error("Flask no disponible para monitoreo web")
            return False
        except Exception as e:
            logger.error(f"Error iniciando monitoreo web: {e}")
            return False

# Template HTML para dashboard web
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ETL Monitor - Dashboard</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .metricas { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }
        .metrica { background: white; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .alerta { background: #ffebee; border: 1px solid #f44336; padding: 10px; margin: 5px 0; border-radius: 3px; }
        .exito { color: #4caf50; }
        .error { color: #f44336; }
        .warning { color: #ff9800; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .estado-excelente { color: #4caf50; font-weight: bold; }
        .estado-bueno { color: #8bc34a; }
        .estado-aceptable { color: #ff9800; }
        .estado-requiere-atencion { color: #f44336; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>ETL Monitor - Dashboard en Tiempo Real</h1>
        <p>Última actualización: {{ dashboard.timestamp }}</p>
        <p>Tiempo de actividad: {{ "%.1f"|format(dashboard.tiempo_actividad_segundos/3600) }} horas</p>
    </div>

    <div class="header">
        <h2>Resumen General</h2>
        <div class="metricas">
            <div class="metrica">
                <h3>Propiedades Procesadas</h3>
                <p style="font-size: 2em; font-weight: bold;">{{ dashboard.resumen_general.total_propiedades_procesadas }}</p>
            </div>
            <div class="metrica">
                <h3>Tasa de Éxito</h3>
                <p style="font-size: 2em; font-weight: bold;" class="{% if dashboard.resumen_general.tasa_exito_global >= 95 %}exito{% else %}warning{% endif %}">
                    {{ "%.1f"|format(dashboard.resumen_general.tasa_exito_global) }}%
                </p>
            </div>
            <div class="metrica">
                <h3>Tokens Usados</h3>
                <p style="font-size: 2em; font-weight: bold;">{{ dashboard.resumen_general.total_tokens_usados }}</p>
            </div>
            <div class="metrica">
                <h3>Costo Total</h3>
                <p style="font-size: 2em; font-weight: bold;">${{ "%.4f"|format(dashboard.resumen_general.costo_total_usd) }}</p>
            </div>
        </div>
    </div>

    <div class="header">
        <h2>Estado del Sistema:
            <span class="estado-{{ dashboard.rendimiento_sistema.estado|lower }}">
                {{ dashboard.rendimiento_sistema.estado }}
            </span>
        </h2>
        <div class="metricas">
            <div class="metrica">
                <h3>Operaciones/Minuto</h3>
                <p>{{ "%.1f"|format(dashboard.metricas_recientes_hora.operaciones_por_minuto) }}</p>
            </div>
            <div class="metrica">
                <h3>Tiempo Promedio</h3>
                <p>{{ "%.2f"|format(dashboard.metricas_recientes_hora.tiempo_promedio_segundos) }}s</p>
            </div>
            <div class="metrica">
                <h3>Operaciones Recientes (1h)</h3>
                <p>{{ dashboard.metricas_recientes_hora.total_operaciones }}</p>
            </div>
        </div>
    </div>

    <div class="header">
        <h2>Proveedores</h2>
        <table>
            <tr>
                <th>Proveedor</th>
                <th>Procesadas</th>
                <th>Tasa Éxito</th>
                <th>Tiempo Prom</th>
                <th>Tokens</th>
                <th>Costo USD</th>
                <th>Mejoras</th>
            </tr>
            {% for codigo, stats in dashboard.proveedores.items() %}
            <tr>
                <td>{{ stats.nombre }}</td>
                <td>{{ stats.propiedades_procesadas }}</td>
                <td class="{% if stats.tasa_exito >= 95 %}exito{% elif stats.tasa_exito >= 90 %}warning{% else %}error{% endif %}">
                    {{ "%.1f"|format(stats.tasa_exito) }}%
                </td>
                <td>{{ "%.2f"|format(stats.tiempo_promedio_segundos) }}s</td>
                <td>{{ stats.tokens_usados }}</td>
                <td>${{ "%.4f"|format(stats.costo_usd) }}</td>
                <td>{{ stats.mejoras_aplicadas|length }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>

    {% if dashboard.alertas_activas %}
    <div class="header">
        <h2>Alertas Activas (Últimas 24h)</h2>
        {% for alerta in dashboard.alertas_activas %}
        <div class="alerta">
            <strong>{{ alerta.tipo }}:</strong> {{ alerta.descripcion }}
            <br><small>{{ alerta.timestamp }} - Nivel: {{ alerta.nivel }}</small>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <script>
        // Auto-refresh cada 30 segundos
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
"""

def main():
    """Función principal para probar el monitor."""
    print("Probando sistema de monitoreo ETL...")

    monitor = ETLMonitor()

    # Simular algunas métricas de prueba
    print("Generando métricas de prueba...")

    # Iniciar mediciones simuladas
    for i in range(10):
        medicion_id = monitor.iniciar_medicion(f"prop_{i}", "02", "procesamiento")
        time.sleep(0.1)  # Simular procesamiento

        # Finalizar con diferentes resultados
        estado = 'exito' if i % 8 != 0 else 'error'
        mejoras = ['amenities', 'precios'] if i % 3 == 0 else []
        tokens = 100 if i % 2 == 0 else 0
        costo = tokens * 0.0001

        monitor.finalizar_medicion(
            medicion_id,
            estado=estado,
            mejoras_aplicadas=mejoras,
            tokens_usados=tokens,
            costo_usd=costo
        )

    # Obtener dashboard
    dashboard = monitor.obtener_dashboard_real_time()
    print(f"\nDashboard generado:")
    print(f"  Total propiedades: {dashboard['resumen_general']['total_propiedades_procesadas']}")
    print(f"  Tasa éxito: {dashboard['resumen_general']['tasa_exito_global']}%")
    print(f"  Tokens usados: {dashboard['resumen_general']['total_tokens_usados']}")
    print(f"  Costo: ${dashboard['resumen_general']['costo_total_usd']:.4f} USD")
    print(f"  Estado sistema: {dashboard['rendimiento_sistema']['estado']}")

    # Generar reporte periódico
    reporte = monitor.generar_reporte_periodico(1)
    print(f"\nReporte período ({reporte['periodo']}):")
    print(f"  Operaciones: {reporte['resumen']['total_operaciones']}")
    print(f"  Estado: {reporte['estado_sistema']}")
    print(f"  Recomendaciones: {len(reporte['recomendaciones'])}")

    # Guardar dashboard
    output_file = monitor.guardar_dashboard()
    print(f"\nDashboard guardado en: {output_file}")

    print("\nSistema de monitoreo funcionando correctamente")
    return 0

if __name__ == "__main__":
    exit(main())