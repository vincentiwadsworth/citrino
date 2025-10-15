#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Prueba para ETL Monitor

Prueba el sistema de monitoreo avanzado con datos simulados.
"""

import json
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Agregar path para importar módulos
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from etl_monitor import ETLMonitor

def generar_datos_simulados(monitor, cantidad_operaciones=100):
    """Genera datos simulados para probar el monitor."""
    print(f"Generando {cantidad_operaciones} operaciones simuladas...")

    proveedores = ['01', '02', '03', '04', '05']
    operaciones = ['procesamiento', 'amenities_extraccion', 'precio_correccion', 'contacto_normalizacion']
    estados = ['exito', 'exito', 'exito', 'error']  # 75% tasa de éxito
    mejoras_posibles = [
        ['amenities'],
        ['precios'],
        ['contacto'],
        ['amenities', 'precios'],
        ['coordenadas'],
        []
    ]

    for i in range(cantidad_operaciones):
        # Seleccionar datos aleatorios
        proveedor = random.choice(proveedores)
        operacion = random.choice(operaciones)
        estado = random.choice(estados)
        mejoras = random.choice(mejoras_posibles)

        # Simular tiempo de procesamiento (variable según operación)
        if operacion == 'amenities_extraccion':
            duracion = random.uniform(0.5, 3.0)
            tokens = random.randint(50, 200)
        elif operacion == 'precio_correccion':
            duracion = random.uniform(0.2, 1.5)
            tokens = random.randint(0, 100)
        else:
            duracion = random.uniform(0.1, 0.8)
            tokens = random.randint(0, 50)

        # Calcular costo (simulado)
        costo = tokens * 0.0001  # $0.0001 por token

        # Iniciar y finalizar medición
        medicion_id = monitor.iniciar_medicion(f"prop_sim_{i}", proveedor, operacion)

        # Simular procesamiento
        time.sleep(random.uniform(0.01, 0.05))  # Pequeña pausa para simulación

        # Errores simulados
        errores = []
        if estado == 'error':
            errores = [f"Error simulado tipo {random.randint(1, 3)}"]

        # Finalizar medición
        monitor.finalizar_medicion(
            medicion_id,
            estado=estado,
            mejoras_aplicadas=mejoras if estado == 'exito' else [],
            errores=errores,
            tokens_usados=tokens if estado == 'exito' else tokens // 2,
            costo_usd=costo if estado == 'exito' else costo / 2
        )

        # Progress logging
        if (i + 1) % 20 == 0:
            print(f"  Generadas {i + 1}/{cantidad_operaciones} operaciones")

def main():
    """Función principal de prueba."""
    print("=" * 60)
    print("PRUEBA DE SISTEMA DE MONITOREO ETL")
    print("=" * 60)

    # Crear monitor
    monitor = ETLMonitor()
    print("Sistema de monitoreo inicializado")

    # Generar datos simulados
    generar_datos_simulados(monitor, 200)
    print("Datos simulados generados")

    # Obtener dashboard en tiempo real
    print("\n" + "=" * 40)
    print("DASHBOARD EN TIEMPO REAL")
    print("=" * 40)

    dashboard = monitor.obtener_dashboard_real_time()

    # Mostrar resumen general
    resumen = dashboard['resumen_general']
    print(f"Propiedades procesadas: {resumen['total_propiedades_procesadas']}")
    print(f"Tasa de éxito global: {resumen['tasa_exito_global']}%")
    print(f"Tokens consumidos: {resumen['total_tokens_usados']}")
    print(f"Costo total: ${resumen['costo_total_usd']:.4f} USD")
    print(f"LLM calls exitosos: {resumen['llm_calls_exitosos']}")

    # Mostrar métricas recientes
    metricas_hora = dashboard['metricas_recientes_hora']
    print(f"\nMétricas última hora:")
    print(f"  Total operaciones: {metricas_hora['total_operaciones']}")
    print(f"  Tiempo promedio: {metricas_hora['tiempo_promedio_segundos']:.2f}s")
    print(f"  Operaciones/minuto: {metricas_hora['operaciones_por_minuto']:.1f}")
    print(f"  Mejoras aplicadas: {sum(metricas_hora['mejoras_aplicadas'].values())}")

    # Mostrar estado por proveedor
    print(f"\nEstado por proveedor:")
    for codigo, stats in dashboard['proveedores'].items():
        print(f"  {stats['nombre']} (Proveedor {codigo}):")
        print(f"    Procesadas: {stats['propiedades_procesadas']}")
        print(f"    Tasa éxito: {stats['tasa_exito']}%")
        print(f"    Costo: ${stats['costo_usd']:.4f}")
        print(f"    Mejoras: {len(stats['mejoras_aplicadas'])} tipos")

    # Mostrar rendimiento del sistema
    rendimiento = dashboard['rendimiento_sistema']
    print(f"\nRendimiento del sistema:")
    print(f"  Estado: {rendimiento['estado']}")
    print(f"  Operaciones recientes: {rendimiento['operaciones_recientes']}")
    print(f"  Ops/minuto: {rendimiento['operaciones_por_minuto']:.1f}")
    print(f"  Latencia promedio: {rendimiento['latencia_promedio_segundos']:.2f}s")

    # Mostrar alertas
    alertas = dashboard['alertas_activas']
    if alertas:
        print(f"\nAlertas activas ({len(alertas)}):")
        for alerta in alertas[:5]:  # Mostrar solo primeras 5
            print(f"  [{alerta['nivel']}] {alerta['tipo']}: {alerta['descripcion']}")
    else:
        print(f"\n✅ Sin alertas activas")

    # Generar reporte periódico
    print(f"\n" + "=" * 40)
    print("REPORTE PERIÓDICO (Últimas 24h)")
    print("=" * 40)

    reporte = monitor.generar_reporte_periodico(24)
    print(f"Estado del sistema: {reporte['estado_sistema']}")
    print(f"Total operaciones: {reporte['resumen']['total_operaciones']}")
    print(f"Tokens consumidos: {reporte['resumen']['tokens_consumidos']}")
    print(f"Costo total: ${reporte['resumen']['costo_total_usd']:.4f} USD")
    print(f"Alertas totales: {reporte['analisis_alertas']['total_alertas']}")

    print(f"\nRecomendaciones ({len(reporte['recomendaciones'])}):")
    for i, rec in enumerate(reporte['recomendaciones'], 1):
        print(f"  {i}. {rec}")

    # Guardar dashboard
    output_file = monitor.guardar_dashboard()
    if output_file:
        print(f"\nDashboard guardado en: {output_file}")
        print("Puedes verlo en un navegador web abriendo el archivo")

    # Simular actualizaciones continuas
    print(f"\n" + "=" * 40)
    print("SIMULACIÓN DE ACTUALIZACIONES CONTINUAS")
    print("=" * 40)
    print("Generando 50 operaciones adicionales...")

    generar_datos_simulados(monitor, 50)

    # Obtener dashboard actualizado
    dashboard_actualizado = monitor.obtener_dashboard_real_time()
    resumen_actualizado = dashboard_actualizado['resumen_general']

    print(f"\nDashboard actualizado:")
    print(f"  Total operaciones: {resumen_actualizado['total_propiedades_procesadas']}")
    print(f"  Tasa éxito: {resumen_actualizado['tasa_exito_global']}%")
    print(f"  Tokens: {resumen_actualizado['total_tokens_usados']}")
    print(f"  Costo: ${resumen_actualizado['costo_total_usd']:.4f} USD")

    # Guardar dashboard final
    final_file = monitor.guardar_dashboard("data/dashboard_etl_final.json")
    print(f"\nDashboard final guardado en: {final_file}")

    print(f"\n" + "=" * 60)
    print("✅ PRUEBA DE MONITOREO COMPLETADA EXITOSAMENTE")
    print("El sistema de monitoreo funciona correctamente")
    print("=" * 60)

    return 0

if __name__ == "__main__":
    exit(main())