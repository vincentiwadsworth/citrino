#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para integrar los datos mejorados del Proveedor 02 al dataset principal.

Este script reemplaza las propiedades del Proveedor 02 en el dataset original
con las versiones mejoradas del ETL, manteniendo intactas las propiedades
de otros proveedores.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List
import logging
from datetime import datetime

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def cargar_dataset_original(ruta: str) -> Dict[str, Any]:
    """Carga el dataset original."""
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error cargando dataset original: {e}")
        raise

def cargar_datos_mejorados(ruta: str) -> Dict[str, Any]:
    """Carga los datos mejorados del Proveedor 02."""
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error cargando datos mejorados: {e}")
        raise

def crear_dataset_integrado(
    dataset_original: Dict[str, Any],
    datos_mejorados: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Crea el dataset integrado reemplazando propiedades del Proveedor 02.

    Args:
        dataset_original: Dataset completo original
        datos_mejorados: Datos mejorados del Proveedor 02

    Returns:
        Dataset integrado con propiedades mejoradas
    """
    logger.info("Creando dataset integrado...")

    # Extraer propiedades
    propiedades_originales = dataset_original.get('propiedades', [])
    propiedades_mejoradas = datos_mejorados.get('propiedades', [])

    # Crear diccionario de propiedades mejoradas por ID
    dict_mejoradas = {prop['id']: prop for prop in propiedades_mejoradas}

    # Filtrar propiedades: mantener todo lo que NO sea Proveedor 02
    # y reemplazar las que SÍ sean Proveedor 02
    propiedades_integradas = []

    for prop_original in propiedades_originales:
        if prop_original.get('codigo_proveedor') == '02':
            # Si es Proveedor 02, usar la versión mejorada si existe
            id_prop = prop_original['id']
            if id_prop in dict_mejoradas:
                propiedades_integradas.append(dict_mejoradas[id_prop])
                logger.debug(f"Propiedad {id_prop} reemplazada con versión mejorada")
            else:
                # Si no tiene versión mejorada, mantener la original
                propiedades_integradas.append(prop_original)
                logger.warning(f"Propiedad {id_prop} no tiene versión mejorada, manteniendo original")
        else:
            # Si no es Proveedor 02, mantener original
            propiedades_integradas.append(prop_original)

    # Actualizar metadata
    metadata_integrada = dataset_original.get('metadata', {}).copy()
    metadata_integrada.update({
        'fecha_ultima_actualizacion': datetime.now().isoformat(),
        'integracion_proveedor02': {
            'fecha': datetime.now().isoformat(),
            'metodo': 'regex_mejorado',
            'propiedades_procesadas': len(propiedades_mejoradas),
            'mejoras_aplicadas': datos_mejorados.get('metadata', {}).get('mejoras_aplicadas', {}),
            'descripcion': 'Integración de propiedades mejoradas del Proveedor 02'
        }
    })

    # Crear dataset final
    dataset_integrado = {
        'metadata': metadata_integrada,
        'propiedades': propiedades_integradas
    }

    # Estadísticas
    total_originales = len(propiedades_originales)
    total_integradas = len(propiedades_integradas)
    total_mejoradas = len([p for p in propiedades_integradas if p.get('_etl_procesada')])

    logger.info(f"Estadísticas de integración:")
    logger.info(f"  Propiedades originales: {total_originales}")
    logger.info(f"  Propiedades integradas: {total_integradas}")
    logger.info(f"  Propiedades mejoradas: {total_mejoradas}")
    logger.info(f"  Proveedor 02 mejoradas: {len(propiedades_mejoradas)}")

    return dataset_integrado

def guardar_dataset_integrado(dataset: Dict[str, Any], ruta_salida: str):
    """Guarda el dataset integrado."""
    try:
        ruta = Path(ruta_salida)
        ruta.parent.mkdir(parents=True, exist_ok=True)

        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)

        logger.info(f"Dataset integrado guardado en: {ruta}")
        return ruta

    except Exception as e:
        logger.error(f"Error guardando dataset integrado: {e}")
        raise

def generar_reporte_integracion(
    dataset_original: Dict[str, Any],
    dataset_integrado: Dict[str, Any],
    datos_mejorados: Dict[str, Any]
) -> str:
    """Genera un reporte de la integración."""

    stats_originales = {
        'total': len(dataset_original.get('propiedades', [])),
        'proveedor02': len([p for p in dataset_original.get('propiedades', []) if p.get('codigo_proveedor') == '02'])
    }

    stats_integradas = {
        'total': len(dataset_integrado.get('propiedades', [])),
        'proveedor02': len([p for p in dataset_integrado.get('propiedades', []) if p.get('codigo_proveedor') == '02']),
        'mejoradas': len([p for p in dataset_integrado.get('propiedades', []) if p.get('_etl_procesada')])
    }

    mejoras = datos_mejorados.get('metadata', {}).get('mejoras_aplicadas', {})

    reporte = f"""
REPORTE DE INTEGRACIÓN - PROVEEDOR 02 MEJORADO
{'='*60}

FECHA Y HORA: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

ESTADÍSTICAS DE DATOS:
• Propiedades originales: {stats_originales['total']}
• Propiedades integradas: {stats_integradas['total']}
• Proveedor 02 original: {stats_originales['proveedor02']}
• Proveedor 02 integradas: {stats_integradas['proveedor02']}
• Propiedades mejoradas: {stats_integradas['mejoradas']}

MEJORAS APLICADAS A PROVEEDOR 02:
• Precio: {mejoras.get('mejoras_precio', 0)} propiedades
• Habitaciones: {mejoras.get('mejoras_habitaciones', 0)} propiedades
• Baños: {mejoras.get('mejoras_banos', 0)} propiedades
• Superficie: {mejoras.get('mejoras_superficie', 0)} propiedades
• Zona: {mejoras.get('mejoras_zona', 0)} propiedades
• Total mejoras: {sum([
    mejoras.get('mejoras_precio', 0),
    mejoras.get('mejoras_habitaciones', 0),
    mejoras.get('mejoras_banos', 0),
    mejoras.get('mejoras_superficie', 0),
    mejoras.get('mejoras_zona', 0)
])}

ESTADO: INTEGRACIÓN COMPLETADA EXITOSAMENTE
ARCHIVO SALIDA: data/base_datos_relevamiento_integrado.json

PRÓXIMO PASO: Modificar chat para responder consultas directas
"""

    return reporte

def main():
    """Función principal."""
    logger.info("INICIANDO INTEGRACIÓN DE DATOS MEJORADOS DEL PROVEEDOR 02")

    # Rutas de archivos
    ruta_original = "data/base_datos_relevamiento.json"
    ruta_mejorados = "data/base_datos_proveedor02_mejorado.json"
    ruta_salida = "data/base_datos_relevamiento_integrado.json"

    # Verificar archivos existen
    if not Path(ruta_original).exists():
        logger.error(f"No existe archivo original: {ruta_original}")
        return 1

    if not Path(ruta_mejorados).exists():
        logger.error(f"No existe archivo mejorado: {ruta_mejorados}")
        return 1

    try:
        # Cargar datos
        logger.info("Cargando datasets...")
        dataset_original = cargar_dataset_original(ruta_original)
        datos_mejorados = cargar_datos_mejorados(ruta_mejorados)

        # Crear dataset integrado
        logger.info("Integrando datos mejorados...")
        dataset_integrado = crear_dataset_integrado(dataset_original, datos_mejorados)

        # Guardar dataset integrado
        logger.info("Guardando dataset integrado...")
        guardar_dataset_integrado(dataset_integrado, ruta_salida)

        # Generar reporte
        reporte = generar_reporte_integracion(dataset_original, dataset_integrado, datos_mejorados)
        print(reporte)

        # Guardar reporte
        with open("docs/reporte_integracion_proveedor02.txt", "w", encoding="utf-8") as f:
            f.write(reporte)

        logger.info("INTEGRACIÓN COMPLETADA EXITOSAMENTE")
        return 0

    except Exception as e:
        logger.error(f"Error en integración: {e}")
        return 1

if __name__ == "__main__":
    exit(main())