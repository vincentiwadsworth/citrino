#!/usr/bin/env python3
"""
Script para procesar los datos de Citrino y crear el dataset para el PoC.

Este script lee los archivos Excel de Citrino y extrae 5 propiedades
representativas para el sistema de recomendación.
"""

import pandas as pd
import json
import os
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def leer_archivo_excel(ruta_archivo):
    """Lee un archivo Excel y retorna un DataFrame."""
    try:
        # Intentar leer con diferentes engines
        for engine in ['openpyxl', 'xlrd']:
            try:
                df = pd.read_excel(ruta_archivo, engine=engine)
                logger.info(f"Leído {ruta_archivo} con engine {engine}")
                return df
            except Exception as e:
                logger.debug(f"Falló engine {engine} para {ruta_archivo}: {e}")
                continue

        # Si ningún engine funciona, intentar sin especificar engine
        df = pd.read_excel(ruta_archivo)
        logger.info(f"Leído {ruta_archivo} con engine automático")
        return df
    except Exception as e:
        logger.error(f"No se pudo leer {ruta_archivo}: {e}")
        return None

def explorar_estructura_datos(df, nombre_archivo):
    """Explora la estructura de un DataFrame."""
    logger.info(f"\n=== Explorando {nombre_archivo} ===")
    logger.info(f"Shape: {df.shape}")
    logger.info(f"Columnas: {list(df.columns)}")

    # Mostrar primeras filas
    logger.info("Primeras filas:")
    logger.info(df.head().to_string())

    # Mostrar tipos de datos
    logger.info("\nTipos de datos:")
    logger.info(df.dtypes.to_string())

def extraer_propiedades_representativas():
    """Extrae 5 propiedades representativas de los datos de Citrino."""

    # Directorio de datos
    data_dir = Path("data/raw/Citrino - Scz")

    # Lista de archivos a explorar
    archivos_explorar = [
        "Muestras Mensuales  de la Oferta Scz/Copia de Consolidado de Relevamientos Mensuales Oferta Scz.xlsx",
        "Muestras Mensuales  de la Oferta Scz/Copia de Relevamiento Mensual de oferta Alquileres y Reventa - Scz.xlsx",
    ]

    propiedades_encontradas = []

    for archivo_rel in archivos_explorar:
        ruta_completa = data_dir / archivo_rel
        if ruta_completa.exists():
            logger.info(f"\nProcesando: {ruta_completa}")

            df = leer_archivo_excel(ruta_completa)
            if df is not None:
                explorar_estructura_datos(df, archivo_rel)

                # Buscar columnas que puedan contener información de propiedades
                # Columnas comunes en datos inmobiliarios
                columnas_potenciales = [
                    'proyecto', 'nombre', 'titulo', 'inmueble', 'propiedad',
                    'precio', 'valor', 'monto', 'costo',
                    'dormitorios', 'habitaciones', 'ambientes', 'dorms',
                    'baños', 'banos', 'baths',
                    'superficie', 'metros', 'm2', 'area',
                    'ubicacion', 'zona', 'barrio', 'direccion',
                    'tipo', 'categoria', 'clase'
                ]

                # Encontrar columnas que existen en el DataFrame
                columnas_existentes = [col for col in columnas_potenciales
                                     if col.lower() in [c.lower() for c in df.columns]]

                if columnas_existentes:
                    logger.info(f"Columnas relevantes encontradas: {columnas_existentes}")

                    # Extraer algunas filas como ejemplo
                    for idx, row in df.head(10).iterrows():
                        prop = {}

                        # Extraer información básica
                        for col in columnas_existentes:
                            # Encontrar la columna real (case insensitive)
                            col_real = None
                            for c in df.columns:
                                if c.lower() == col.lower():
                                    col_real = c
                                    break

                            if col_real and pd.notna(row[col_real]):
                                prop[col] = row[col_real]

                        if len(prop) >= 3:  # Si tenemos suficiente información
                            propiedades_encontradas.append(prop)
                            if len(propiedades_encontradas) >= 5:
                                break

                if len(propiedades_encontradas) >= 5:
                    break
        else:
            logger.warning(f"No se encontró: {ruta_completa}")

    return propiedades_encontradas

def crear_dataset_ejemplo():
    """Crea un dataset de ejemplo basado en los patrones encontrados."""

    # Si no encontramos suficientes propiedades reales, crear un dataset de ejemplo
    # basado en los patrones típicos de Santa Cruz de la Sierra

    propiedades_ejemplo = [
        {
            "id": "prop_001",
            "nombre": "Altos del Golf - Departamento 2D",
            "tipo": "Departamento",
            "caracteristicas": {
                "precio": 185000,
                "habitaciones": 3,
                "banos": 2,
                "superficie": 120,
                "piso": 2,
                "amoblado": False
            },
            "ubicacion": {
                "direccion": "Av. Santos Dumont y 4to Anillo",
                "barrio": "Zona Norte",
                "coordenadas": {"lat": -17.783, "lng": -63.182},
                "zona": "Norte"
            },
            "servicios_cercanos": {
                "escuela_primaria": [
                    {"nombre": "Escuela Americana", "distancia": 500},
                    {"nombre": "Colegio Alemán", "distancia": 800}
                ],
                "supermercado": [
                    {"nombre": "Hipermaxi", "distancia": 300},
                    {"nombre": "Supermercado Fidalga", "distancia": 600}
                ],
                "hospital": [
                    {"nombre": "Clinica Foianini", "distancia": 1200}
                ],
                "universidad": [
                    {"nombre": "Universidad Autónoma Gabriel René Moreno", "distancia": 2000}
                ]
            },
            "demografia_area": {
                "nivel_socioeconomico": "alto",
                "composicion_familiar_típica": "parejas con hijos",
                "seguridad": "alta",
                "densidad_poblacional": "media"
            }
        },
        {
            "id": "prop_002",
            "nombre": "Golden Tower - Studio 15A",
            "tipo": "Departamento",
            "caracteristicas": {
                "precio": 95000,
                "habitaciones": 1,
                "banos": 1,
                "superficie": 45,
                "piso": 15,
                "amoblado": True
            },
            "ubicacion": {
                "direccion": "Calle Junín esq. Ecuador",
                "barrio": "Centro",
                "coordenadas": {"lat": -17.786, "lng": -63.181},
                "zona": "Centro"
            },
            "servicios_cercanos": {
                "universidad": [
                    {"nombre": "Universidad Privada de Santa Cruz", "distancia": 400},
                    {"nombre": "Universidad Tecnológica", "distancia": 600}
                ],
                "supermercado": [
                    {"nombre": "Supermercado El Tore", "distancia": 200},
                    {"nombre": "Hipermaxi Centro", "distancia": 350}
                ],
                "hospital": [
                    {"nombre": "Hospital Japonés", "distancia": 800}
                ],
                "escuela_primaria": [
                    {"nombre": "Escuela Bolivia", "distancia": 600}
                ]
            },
            "demografia_area": {
                "nivel_socioeconomico": "medio-alto",
                "composicion_familiar_típica": "jóvenes profesionales",
                "seguridad": "media",
                "densidad_poblacional": "alta"
            }
        },
        {
            "id": "prop_003",
            "nombre": "Villa Magna - Casa 3B",
            "tipo": "Casa",
            "caracteristicas": {
                "precio": 320000,
                "habitaciones": 4,
                "banos": 3,
                "superficie": 180,
                "piso": 0,
                "jardin": True,
                "garage": 2
            },
            "ubicacion": {
                "direccion": "Calle 21 de Calacoto",
                "barrio": "Equipetrol",
                "coordenadas": {"lat": -17.779, "lng": -63.190},
                "zona": "Este"
            },
            "servicios_cercanos": {
                "escuela_primaria": [
                    {"nombre": "Colegio La Salle", "distancia": 400},
                    {"nombre": "Escuela Suiza", "distancia": 700}
                ],
                "supermercado": [
                    {"nombre": "Supermercado La Sierra", "distancia": 500},
                    {"nombre": "Hipermaxi Equipetrol", "distancia": 800}
                ],
                "hospital": [
                    {"nombre": "Clinica Foianini", "distancia": 1500}
                ],
                "universidad": [
                    {"nombre": "Universidad NUR", "distancia": 1800}
                ]
            },
            "demografia_area": {
                "nivel_socioeconomico": "alto",
                "composicion_familiar_típica": "familias con hijos",
                "seguridad": "alta",
                "densidad_poblacional": "baja"
            }
        },
        {
            "id": "prop_004",
            "nombre": "Avanti Condominio - Dúplex 7C",
            "tipo": "Dúplex",
            "caracteristicas": {
                "precio": 145000,
                "habitaciones": 2,
                "banos": 2,
                "superficie": 85,
                "piso": 1,
                "terraza": True
            },
            "ubicacion": {
                "direccion": "Av. La Salle y 3er Anillo",
                "barrio": "3er Anillo",
                "coordenadas": {"lat": -17.788, "lng": -63.178},
                "zona": "Sur"
            },
            "servicios_cercanos": {
                "escuela_primaria": [
                    {"nombre": "Colegio Don Bosco", "distancia": 300},
                    {"nombre": "Escuela San Vicente", "distancia": 600}
                ],
                "supermercado": [
                    {"nombre": "Supermercado Ketal", "distancia": 250},
                    {"nombre": "Hipermaxi 3er Anillo", "distancia": 450}
                ],
                "hospital": [
                    {"nombre": "Hospital de la Mujer", "distancia": 1000}
                ],
                "universidad": [
                    {"nombre": "UPSD", "distancia": 1500}
                ]
            },
            "demografia_area": {
                "nivel_socioeconomico": "medio",
                "composicion_familiar_típica": "parejas jóvenes",
                "seguridad": "media",
                "densidad_poblacional": "media"
            }
        },
        {
            "id": "prop_005",
            "nombre": "Inmoba Tower - Penthouse 20A",
            "tipo": "Penthouse",
            "caracteristicas": {
                "precio": 450000,
                "habitaciones": 3,
                "banos": 3,
                "superficie": 200,
                "piso": 20,
                "terraza": True,
                "vista_panoramica": True
            },
            "ubicacion": {
                "direccion": "Calle Beni esq. Potosí",
                "barrio": "Centro",
                "coordenadas": {"lat": -17.785, "lng": -63.180},
                "zona": "Centro"
            },
            "servicios_cercanos": {
                "universidad": [
                    {"nombre": "Universidad Autónoma Gabriel René Moreno", "distancia": 600},
                    {"nombre": "Universidad Privada", "distancia": 800}
                ],
                "supermercado": [
                    {"nombre": "Supermercado El Tore", "distancia": 300},
                    {"nombre": "Hipermaxi Centro", "distancia": 400}
                ],
                "hospital": [
                    {"nombre": "Hospital Japonés", "distancia": 700}
                ],
                "escuela_primaria": [
                    {"nombre": "Colegio San Ignacio", "distancia": 500}
                ]
            },
            "demografia_area": {
                "nivel_socioeconomico": "alto",
                "composicion_familiar_típica": "profesionales exitosos",
                "seguridad": "alta",
                "densidad_poblacional": "alta"
            }
        }
    ]

    return propiedades_ejemplo

def main():
    """Función principal."""
    logger.info("Iniciando procesamiento de datos de Citrino...")

    # Intentar extraer propiedades de los archivos reales
    propiedades_reales = extraer_propiedades_representativas()

    if len(propiedades_reales) >= 5:
        logger.info(f"Se encontraron {len(propiedades_reales)} propiedades reales")
        propiedades = propiedades_reales[:5]
    else:
        logger.info("No se encontraron suficientes propiedades reales, usando dataset de ejemplo")
        propiedades = crear_dataset_ejemplo()

    # Crear directorio de datos si no existe
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    # Guardar el dataset
    output_file = data_dir / "propiedades.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(propiedades, f, indent=2, ensure_ascii=False)

    logger.info(f"Dataset guardado en: {output_file}")
    logger.info(f"Total de propiedades: {len(propiedades)}")

    # Mostrar resumen
    logger.info("\n=== Resumen de propiedades ===")
    for i, prop in enumerate(propiedades, 1):
        caract = prop.get('caracteristicas', {})
        ubic = prop.get('ubicacion', {})

        logger.info(f"{i}. {prop.get('nombre', 'Sin nombre')}")
        logger.info(f"   Precio: ${caract.get('precio', 0):,.0f}")
        logger.info(f"   Habitaciones: {caract.get('habitaciones', 0)}")
        logger.info(f"   Ubicación: {ubic.get('barrio', 'N/A')}")
        logger.info("")

if __name__ == "__main__":
    main()