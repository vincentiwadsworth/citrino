#!/usr/bin/env python3
"""
Script para limpiar datos extremos y valores inconsistentes en la base de datos integrada.
"""

import json
import pandas as pd
import os
from typing import Dict, List, Any
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LimpiezaDatosExtremos:
    """Clase para limpiar datos extremos en la base de datos."""

    def __init__(self):
        self.propiedades_originales = []
        self.propiedades_limpias = []
        self.estadisticas_limpieza = {
            'total_original': 0,
            'total_limpias': 0,
            'eliminadas_precio_extremo': 0,
            'eliminadas_superficie_extrema': 0,
            'eliminadas_datos_incompletos': 0,
            'corregidas_precios': 0,
            'corregidas_superficies': 0
        }

    def cargar_datos(self, ruta: str = 'data/bd_integrada/propiedades_integradas.json') -> None:
        """Carga los datos originales."""
        logger.info(f"Cargando datos desde {ruta}...")

        with open(ruta, 'r', encoding='utf-8') as f:
            self.propiedades_originales = json.load(f)

        self.estadisticas_limpieza['total_original'] = len(self.propiedades_originales)
        logger.info(f"Cargadas {self.estadisticas_limpieza['total_original']} propiedades")

    def es_precio_extremo(self, precio: float) -> bool:
        """Verifica si un precio es extremo."""
        # Precios irreales
        if precio <= 0:
            return True
        if precio > 10_000_000:  # Más de 10 millones
            return True
        return False

    def es_superficie_extrema(self, superficie: float) -> bool:
        """Verifica si una superficie es extrema."""
        # Superficies irreales
        if superficie <= 0:
            return True
        if superficie > 5000:  # Más de 5000 m²
            return True
        return False

    def corregir_precio(self, precio: float) -> float:
        """Intenta corregir precios mal formateados."""
        if isinstance(precio, str):
            # Quitar símbolos y formatear
            precio_str = precio.replace('$', '').replace(',', '.').strip()
            try:
                precio_float = float(precio_str)
                if self.es_precio_extremo(precio_float):
                    return 0
                return precio_float
            except:
                return 0
        return precio

    def corregir_superficie(self, superficie: float) -> float:
        """Intenta corregir superficies mal formateadas."""
        if isinstance(superficie, str):
            superficie_str = superficie.replace(',', '.').strip()
            try:
                superficie_float = float(superficie_str)
                if self.es_superficie_extrema(superficie_float):
                    return 0
                return superficie_float
            except:
                return 0
        return superficie

    def limpiar_propiedad(self, propiedad: Dict[str, Any]) -> bool:
        """Limpia una propiedad individual. Devuelve True si debe conservarse."""
        try:
            # Obtener características principales
            caract = propiedad.get('caracteristicas_principales', {})

            # Corregir precio
            precio = caract.get('precio', 0)
            if precio:
                precio_corregido = self.corregir_precio(precio)
                if precio_corregido != precio:
                    caract['precio'] = precio_corregido
                    self.estadisticas_limpieza['corregidas_precios'] += 1

            # Corregir superficie
            superficie = caract.get('superficie_m2', 0)
            if superficie:
                superficie_corregida = self.corregir_superficie(superficie)
                if superficie_corregida != superficie:
                    caract['superficie_m2'] = superficie_corregida
                    self.estadisticas_limpieza['corregidas_superficies'] += 1

            # Validar datos mínimos
            precio_final = caract.get('precio', 0)
            superficie_final = caract.get('superficie_m2', 0)

            # Eliminar propiedades con datos extremos
            if self.es_precio_extremo(precio_final):
                self.estadisticas_limpieza['eliminadas_precio_extremo'] += 1
                return False

            if self.es_superficie_extrema(superficie_final):
                self.estadisticas_limpieza['eliminadas_superficie_extrema'] += 1
                return False

            # Verificar datos mínimos necesarios
            if precio_final <= 0 and superficie_final <= 0:
                self.estadisticas_limpieza['eliminadas_datos_incompletos'] += 1
                return False

            # Actualizar la propiedad
            propiedad['caracteristicas_principales'] = caract

            return True

        except Exception as e:
            logger.error(f"Error limpiando propiedad: {str(e)}")
            return False

    def ejecutar_limpieza(self) -> None:
        """Ejecuta el proceso de limpieza completo."""
        logger.info("Iniciando limpieza de datos...")

        propiedades_filtradas = []

        for propiedad in self.propiedades_originales:
            if self.limpiar_propiedad(propiedad):
                propiedades_filtradas.append(propiedad)

        self.propiedades_limpias = propiedades_filtradas
        self.estadisticas_limpieza['total_limpias'] = len(self.propiedades_limpias)

        logger.info(f"Limpieza completada: {self.estadisticas_limpieza['total_limpias']} propiedades válidas")

    def guardar_datos_limpios(self) -> None:
        """Guarda los datos limpios."""
        logger.info("Guardando datos limpios...")

        # Crear directorio
        os.makedirs('data/bd_final', exist_ok=True)

        # Guardar propiedades limpias
        with open('data/bd_final/propiedades_limpias.json', 'w', encoding='utf-8') as f:
            json.dump(self.propiedades_limpias, f, indent=2, ensure_ascii=False)

        # Guardar estadísticas de limpieza
        with open('data/bd_final/estadisticas_limpieza.json', 'w', encoding='utf-8') as f:
            json.dump(self.estadisticas_limpieza, f, indent=2, ensure_ascii=False)

        logger.info("Datos limpios guardados exitosamente")

    def mostrar_resumen_limpieza(self) -> None:
        """Muestra un resumen de la limpieza realizada."""
        print("\n" + "="*80)
        print("RESUMEN DE LIMPIEZA DE DATOS")
        print("="*80)

        print(f"PROPIEDADES ORIGINALES: {self.estadisticas_limpieza['total_original']:,}")
        print(f"PROPIEDADES LIMPIAS: {self.estadisticas_limpieza['total_limpias']:,}")
        print(f"PROPORCIÓN CONSERVADA: {(self.estadisticas_limpieza['total_limpias']/self.estadisticas_limpieza['total_original']*100):.1f}%")

        print(f"\nELIMINADAS POR:")
        print(f"   • Precio extremo: {self.estadisticas_limpieza['eliminadas_precio_extremo']:,}")
        print(f"   • Superficie extrema: {self.estadisticas_limpieza['eliminadas_superficie_extrema']:,}")
        print(f"   • Datos incompletos: {self.estadisticas_limpieza['eliminadas_datos_incompletos']:,}")

        print(f"\nCORREGIDAS:")
        print(f"   • Precios: {self.estadisticas_limpieza['corregidas_precios']:,}")
        print(f"   • Superficies: {self.estadisticas_limpieza['corregidas_superficies']:,}")

        print(f"\nARCHIVOS GENERADOS:")
        print(f"   • data/bd_final/propiedades_limpias.json")
        print(f"   • data/bd_final/estadisticas_limpieza.json")

        print("="*80)

    def ejecutar_limpieza_completa(self) -> None:
        """Ejecuta el proceso completo de limpieza."""
        logger.info("=== INICIANDO LIMPIEZA DE DATOS EXTREMOS ===")

        self.cargar_datos()
        self.ejecutar_limpieza()
        self.guardar_datos_limpios()
        self.mostrar_resumen_limpieza()

        logger.info("=== LIMPIEZA COMPLETADA ===")

def main():
    """Función principal."""
    limpiador = LimpiezaDatosExtremos()
    limpiador.ejecutar_limpieza_completa()

if __name__ == "__main__":
    main()