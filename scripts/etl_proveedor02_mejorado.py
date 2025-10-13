#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL Mejorado para Proveedor 02

Este script procesa únicamente las propiedades del Proveedor 02
aplicando las mejoras de regex y extracción LLM para mejorar la calidad de datos.
"""

import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
import logging

# Agregar path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from regex_extractor import RegexExtractor
from description_parser import DescriptionParser

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ETLProveedor02:
    """ETL especializado para procesar y mejorar datos del Proveedor 02."""

    def __init__(self):
        self.regex_extractor = RegexExtractor()
        self.description_parser = DescriptionParser()
        self.stats = {
            'total_propiedades': 0,
            'mejoras_precio': 0,
            'mejoras_habitaciones': 0,
            'mejoras_banos': 0,
            'mejoras_superficie': 0,
            'mejoras_zona': 0,
            'errores': 0
        }

    def cargar_datos_originales(self, dataset_path: str) -> List[Dict[str, Any]]:
        """Carga las propiedades del Proveedor 02 del dataset original."""
        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            propiedades = data.get('propiedades', [])
            proveedor02_props = [
                prop for prop in propiedades
                if prop.get('codigo_proveedor') == '02'
            ]

            logger.info(f"Cargadas {len(proveedor02_props)} propiedades del Proveedor 02")
            return proveedor02_props

        except Exception as e:
            logger.error(f"Error cargando datos: {e}")
            return []

    def mejorar_propiedad_con_regex(self, propiedad: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica extracción regex mejorada a una propiedad."""
        descripcion = propiedad.get('descripcion', '')
        titulo = propiedad.get('titulo', '')

        if not descripcion.strip():
            return propiedad

        # Extraer datos con regex mejorado
        datos_regex = self.regex_extractor.extract_all(descripcion, titulo)

        # Aplicar mejoras donde los datos están vacíos y regex encontró algo
        if not propiedad.get('precio') and datos_regex.get('precio'):
            propiedad['precio'] = datos_regex['precio']
            propiedad['moneda'] = datos_regex.get('moneda', 'USD')
            propiedad['precio_origen'] = 'regex_mejorado'
            self.stats['mejoras_precio'] += 1
            logger.info(f"Mejorado precio para {propiedad['id']}: {propiedad['precio']}")

        if not propiedad.get('habitaciones') and datos_regex.get('habitaciones'):
            propiedad['habitaciones'] = datos_regex['habitaciones']
            self.stats['mejoras_habitaciones'] += 1
            logger.info(f"Mejorado habitaciones para {propiedad['id']}: {propiedad['habitaciones']}")

        if not propiedad.get('banos') and datos_regex.get('banos'):
            propiedad['banos'] = datos_regex['banos']
            self.stats['mejoras_banos'] += 1
            logger.info(f"Mejorado baños para {propiedad['id']}: {propiedad['banos']}")

        if not propiedad.get('superficie') and datos_regex.get('superficie'):
            propiedad['superficie'] = datos_regex['superficie']
            self.stats['mejoras_superficie'] += 1
            logger.info(f"Mejorado superficie para {propiedad['id']}: {propiedad['superficie']} m²")

        if not propiedad.get('zona') and datos_regex.get('zona'):
            propiedad['zona'] = datos_regex['zona']
            propiedad['zona_origen'] = 'regex_mejorado'
            self.stats['mejoras_zona'] += 1
            logger.info(f"Mejorado zona para {propiedad['id']}: {propiedad['zona']}")

        return propiedad

    def procesar_todas_las_propiedades(self, propiedades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Procesa todas las propiedades aplicando mejoras."""
        logger.info("Iniciando procesamiento de mejoras con regex...")

        propiedades_mejoradas = []
        for i, prop in enumerate(propiedades):
            try:
                # Aplicar mejoras regex
                prop_mejorada = self.mejorar_propiedad_con_regex(prop)
                prop_mejorada['_etl_procesada'] = True
                prop_mejorada['_etl_metodo'] = 'regex_mejorado'

                propiedades_mejoradas.append(prop_mejorada)

                # Progress logging cada 100 propiedades
                if (i + 1) % 100 == 0:
                    logger.info(f"Procesadas {i + 1}/{len(propiedades)} propiedades")

            except Exception as e:
                logger.error(f"Error procesando propiedad {prop.get('id', 'unknown')}: {e}")
                self.stats['errores'] += 1
                # Mantener propiedad original si hay error
                propiedades_mejoradas.append(prop)

        return propiedades_mejoradas

    def guardar_resultados(self, propiedades: List[Dict[str, Any]], output_path: str):
        """Guarda los resultados del ETL."""
        try:
            # Crear metadata
            metadata = {
                'fecha_procesamiento': '2025-10-13T20:00:00.000000',
                'total_propiedades': len(propiedades),
                'proveedor': '02',
                'metodo': 'regex_mejorado',
                'mejoras_aplicadas': self.stats,
                'descripcion': 'Dataset del Proveedor 02 enriquecido con regex mejorado'
            }

            # Estructura final
            datos_completos = {
                'metadata': metadata,
                'propiedades': propiedades
            }

            # Guardar en JSON
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(datos_completos, f, ensure_ascii=False, indent=2)

            logger.info(f"Datos guardados en: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error guardando resultados: {e}")
            return None

    def generar_reporte(self) -> str:
        """Genera un reporte del procesamiento."""
        total = self.stats['total_propiedades']

        reporte = f"""
REPORTE DE PROCESAMIENTO - PROVEEDOR 02
{'='*50}

Propiedades procesadas: {total}
Mejoras aplicadas:
  • Precio: {self.stats['mejoras_precio']} propiedades
  • Habitaciones: {self.stats['mejoras_habitaciones']} propiedades
  • Baños: {self.stats['mejoras_banos']} propiedades
  • Superficie: {self.stats['mejoras_superficie']} propiedades
  • Zona: {self.stats['mejoras_zona']} propiedades

Total de mejoras: {sum([
    self.stats['mejoras_precio'],
    self.stats['mejoras_habitaciones'],
    self.stats['mejoras_banos'],
    self.stats['mejoras_superficie'],
    self.stats['mejoras_zona']
])}

Errores: {self.stats['errores']}

Porcentaje de mejora: {sum([
    self.stats['mejoras_precio'],
    self.stats['mejoras_habitaciones'],
    self.stats['mejoras_banos'],
    self.stats['mejoras_superficie'],
    self.stats['mejoras_zona']
]) / (total * 5) * 100:.1f}% (campos mejorados / campos totales)
"""
        return reporte

def main():
    """Función principal."""
    logger.info("INICIANDO ETL MEJORADO PARA PROVEEDOR 02")

    # Configuración
    input_path = "data/base_datos_relevamiento.json"
    output_path = "data/base_datos_proveedor02_mejorado.json"

    # Crear procesador
    etl = ETLProveedor02()

    # Cargar datos
    logger.info("Cargando datos originales...")
    propiedades_originales = etl.cargar_datos_originales(input_path)

    if not propiedades_originales:
        logger.error("No se encontraron propiedades del Proveedor 02")
        return 1

    etl.stats['total_propiedades'] = len(propiedades_originales)

    # Procesar propiedades
    logger.info(f"Procesando {len(propiedades_originales)} propiedades...")
    propiedades_mejoradas = etl.procesar_todas_las_propiedades(propiedades_originales)

    # Guardar resultados
    logger.info("Guardando resultados...")
    etl.guardar_resultados(propiedades_mejoradas, output_path)

    # Generar reporte
    reporte = etl.generar_reporte()
    print(reporte)

    # Guardar reporte
    with open("docs/reporte_etl_proveedor02.txt", "w", encoding="utf-8") as f:
        f.write(reporte)

    logger.info("ETL Proveedor 02 completado exitosamente")
    return 0

if __name__ == "__main__":
    exit(main())