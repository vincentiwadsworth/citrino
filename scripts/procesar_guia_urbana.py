#!/usr/bin/env python3
"""
Script para procesar datos de la Guía Urbana y crear servicios georreferenciados.

Este script lee los archivos de guía urbana y extrae información de servicios
como escuelas, hospitales, supermercados, etc. para asociar a las propiedades.
"""

import pandas as pd
import json
import os
from pathlib import Path
import logging
from typing import Dict, List, Any
import re

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def leer_excel_guia_urbana(ruta_archivo: str) -> pd.DataFrame:
    """Lee un archivo Excel de guía urbana y retorna un DataFrame."""
    try:
        # Intentar con diferentes engines
        for engine in ['openpyxl', 'xlrd']:
            try:
                df = pd.read_excel(ruta_archivo, engine=engine)
                logger.info(f"Leído guía urbana {ruta_archivo} con engine {engine}")
                return df
            except Exception as e:
                logger.debug(f"Falló engine {engine} para {ruta_archivo}: {e}")
                continue

        # Si ningún engine funciona, intentar sin especificar engine
        df = pd.read_excel(ruta_archivo)
        logger.info(f"Leído guía urbana {ruta_archivo} con engine automático")
        return df
    except Exception as e:
        logger.error(f"No se pudo leer {ruta_archivo}: {e}")
        return None

def leer_codigo_web(ruta_archivo: str) -> str:
    """Lee el archivo de código web de la guía urbana."""
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"No se pudo leer {ruta_archivo}: {e}")
        return ""

def explorar_guia_urbana(df: pd.DataFrame, nombre_archivo: str):
    """Explora la estructura de un DataFrame de guía urbana."""
    logger.info(f"\n=== Explorando Guía Urbana: {nombre_archivo} ===")
    logger.info(f"Shape: {df.shape}")
    logger.info(f"Columnas: {list(df.columns)}")

    # Mostrar primeras filas
    logger.info("Primeras filas:")
    logger.info(df.head().to_string())

    # Mostrar tipos de datos
    logger.info("\nTipos de datos:")
    logger.info(df.dtypes.to_string())

    # Buscar columnas que puedan contener información de servicios
    # Palabras clave para servicios
    servicios_keywords = [
        'escuela', 'colegio', 'educacion', 'universidad',
        'hospital', 'clinica', 'salud', 'medico',
        'supermercado', 'tienda', 'comercio',
        'farmacia', 'drogueria',
        'banco', 'caja', 'financiero',
        'restaurante', 'comida', 'gastronomia',
        'parque', 'area verde', 'recreacion',
        'transporte', 'bus', 'taxi',
        'seguridad', 'policia', 'bomberos'
    ]

    # Encontrar columnas relevantes
    columnas_relevantes = []
    for col in df.columns:
        col_lower = str(col).lower()
        if any(keyword in col_lower for keyword in servicios_keywords):
            columnas_relevantes.append(col)

    if columnas_relevantes:
        logger.info(f"\nColumnas de servicios encontradas: {columnas_relevantes}")
    else:
        logger.info("\nNo se encontraron columnas obvias de servicios, buscando en datos...")

    # Buscar servicios en los datos
    servicios_encontrados = set()
    for idx, row in df.head(20).iterrows():
        for col in df.columns:
            if pd.notna(row[col]):
                valor = str(row[col]).lower()
                for keyword in servicios_keywords:
                    if keyword in valor:
                        servicios_encontrados.add(keyword)

    if servicios_encontrados:
        logger.info(f"Servicios encontrados en los datos: {list(servicios_encontrados)}")

def extraer_servicios_guia_urbana(df: pd.DataFrame) -> Dict[str, List[Dict[str, Any]]]:
    """Extrae servicios de la guía urbana y los estructura."""
    servicios = {
        'escuela_primaria': [],
        'escuela_secundaria': [],
        'universidad': [],
        'hospital': [],
        'clinica': [],
        'supermercado': [],
        'farmacia': [],
        'restaurante': [],
        'parque': [],
        'transporte': []
    }

    # Mapeo de categorías
    categoria_mapping = {
        'escuela': 'escuela_primaria',
        'colegio': 'escuela_primaria',
        'universidad': 'universidad',
        'hospital': 'hospital',
        'clinica': 'clinica',
        'supermercado': 'supermercado',
        'tienda': 'supermercado',
        'farmacia': 'farmacia',
        'drogueria': 'farmacia',
        'restaurante': 'restaurante',
        'comida': 'restaurante',
        'parque': 'parque',
        'area verde': 'parque',
        'bus': 'transporte',
        'transporte': 'transporte'
    }

    # Buscar servicios en cada fila
    for idx, row in df.iterrows():
        servicio_info = {}

        # Extraer información básica
        for col in df.columns:
            if pd.notna(row[col]):
                valor = str(row[col])
                if len(valor.strip()) > 2:  # Evitar valores vacíos
                    # Determinar el tipo de información
                    col_lower = col.lower()
                    valor_lower = valor.lower()

                    # Buscar coordenadas o direcciones
                    if any(term in col_lower for term in ['direccion', 'ubicacion', 'coordenada', 'lat', 'lng']):
                        servicio_info['ubicacion'] = valor

                    # Buscar nombres
                    elif any(term in col_lower for term in ['nombre', 'establecimiento', 'lugar']):
                        servicio_info['nombre'] = valor

                    # Buscar teléfonos
                    elif any(term in col_lower for term in ['telefono', 'contacto', 'celular']):
                        servicio_info['telefono'] = valor

                    # Buscar categorías en el valor
                    for keyword, categoria in categoria_mapping.items():
                        if keyword in valor_lower:
                            servicio_info['categoria'] = categoria
                            servicio_info['tipo_detectado'] = keyword
                            break

        # Si encontramos suficiente información, agregar al listado
        if 'nombre' in servicio_info and 'categoria' in servicio_info:
            categoria = servicio_info['categoria']
            if categoria in servicios:
                # Agregar información adicional
                servicio_entry = {
                    'nombre': servicio_info['nombre'],
                    'categoria': categoria,
                    'tipo_detectado': servicio_info.get('tipo_detectado', ''),
                }

                # Agregar ubicación si está disponible
                if 'ubicacion' in servicio_info:
                    servicio_entry['direccion'] = servicio_info['ubicacion']

                # Agregar teléfono si está disponible
                if 'telefono' in servicio_info:
                    servicio_entry['telefono'] = servicio_info['telefono']

                # Agregar coordenadas simuladas para el PoC
                # En una implementación real, se extraerían del archivo
                servicio_entry['coordenadas'] = {
                    'lat': -17.783 + (idx * 0.01),  # Coordenadas simuladas SCZ
                    'lng': -63.182 + (idx * 0.01)
                }

                servicios[categoria].append(servicio_entry)

    return servicios

def crear_servicios_ejemplo():
    """Crea servicios de ejemplo basados en Santa Cruz de la Sierra."""
    return {
        'escuela_primaria': [
            {
                'nombre': 'Escuela Americana',
                'direccion': 'Av. Santos Dumont y 4to Anillo',
                'telefono': '+591-3-1234567',
                'coordenadas': {'lat': -17.783, 'lng': -63.182},
                'categoria': 'escuela_primaria',
                'horario': '07:30 - 12:30',
                'nivel': 'primario'
            },
            {
                'nombre': 'Colegio Alemán',
                'direccion': 'Calle España y 3er Anillo',
                'telefono': '+591-3-2345678',
                'coordenadas': {'lat': -17.786, 'lng': -63.185},
                'categoria': 'escuela_primaria',
                'horario': '08:00 - 13:00',
                'nivel': 'primario'
            },
            {
                'nombre': 'Colegio La Salle',
                'direccion': 'Av. Cañoto y Uruguay',
                'telefono': '+591-3-3456789',
                'coordenadas': {'lat': -17.779, 'lng': -63.190},
                'categoria': 'escuela_primaria',
                'horario': '07:45 - 12:45',
                'nivel': 'primario'
            },
            {
                'nombre': 'Escuela Suiza',
                'direccion': 'Calle 21 de Calacoto',
                'telefono': '+591-3-4567890',
                'coordenadas': {'lat': -17.775, 'lng': -63.188},
                'categoria': 'escuela_primaria',
                'horario': '08:00 - 12:30',
                'nivel': 'primario'
            },
            {
                'nombre': 'Colegio Don Bosco',
                'direccion': 'Av. La Salle y 3er Anillo',
                'telefono': '+591-3-5678901',
                'coordenadas': {'lat': -17.788, 'lng': -63.178},
                'categoria': 'escuela_primaria',
                'horario': '07:30 - 12:30',
                'nivel': 'primario'
            }
        ],
        'universidad': [
            {
                'nombre': 'Universidad Autónoma Gabriel René Moreno',
                'direccion': 'Av. Busch entre Venezuela y España',
                'telefono': '+591-3-1234567',
                'coordenadas': {'lat': -17.786, 'lng': -63.181},
                'categoria': 'universidad',
                'tipo': 'pública',
                'facultades': ['Derecho', 'Medicina', 'Ingeniería', 'Economía']
            },
            {
                'nombre': 'Universidad Privada de Santa Cruz',
                'direccion': 'Av. Velasco y 4to Anillo',
                'telefono': '+591-3-2345678',
                'coordenadas': {'lat': -17.784, 'lng': -63.183},
                'categoria': 'universidad',
                'tipo': 'privada',
                'facultades': ['Administración', 'Comunicación', 'Derecho']
            },
            {
                'nombre': 'Universidad Tecnológica',
                'direccion': 'Calle Beni esq. Potosí',
                'telefono': '+591-3-3456789',
                'coordenadas': {'lat': -17.785, 'lng': -63.180},
                'categoria': 'universidad',
                'tipo': 'privada',
                'facultades': ['Sistemas', 'Electrónica', 'Industrial']
            },
            {
                'nombre': 'UPSD - Universidad Privada Domingo Savio',
                'direccion': 'Av. Roca y Coronado',
                'telefono': '+591-3-4567890',
                'coordenadas': {'lat': -17.787, 'lng': -63.179},
                'categoria': 'universidad',
                'tipo': 'privada',
                'facultades': ['Derecho', 'Psicología', 'Arquitectura']
            },
            {
                'nombre': 'Universidad NUR',
                'direccion': 'Av. La Salle y 2do Anillo',
                'telefono': '+591-3-5678901',
                'coordenadas': {'lat': -17.782, 'lng': -63.184},
                'categoria': 'universidad',
                'tipo': 'privada',
                'facultades': ['Medicina', 'Enfermería', 'Nutrición']
            }
        ],
        'hospital': [
            {
                'nombre': 'Clínica Foianini',
                'direccion': 'Av. Irala y 4to Anillo',
                'telefono': '+591-3-1234567',
                'coordenadas': {'lat': -17.781, 'lng': -63.183},
                'categoria': 'hospital',
                'tipo': 'privada',
                'especialidades': ['Cardiología', 'Neurología', 'Pediatría'],
                'emergencias': 24
            },
            {
                'nombre': 'Hospital Japonés',
                'direccion': 'Calle Junín esq. Ecuador',
                'telefono': '+591-3-2345678',
                'coordenadas': {'lat': -17.785, 'lng': -63.181},
                'categoria': 'hospital',
                'tipo': 'privada',
                'especialidades': ['Ginecología', 'Cirugía', 'Traumatología'],
                'emergencias': 24
            },
            {
                'nombre': 'Hospital de la Mujer',
                'direccion': 'Av. Cañoto y Ballivián',
                'telefono': '+591-3-3456789',
                'coordenadas': {'lat': -17.789, 'lng': -63.177},
                'categoria': 'hospital',
                'tipo': 'público',
                'especialidades': ['Ginecología', 'Obstetricia', 'Neonatología'],
                'emergencias': 24
            },
            {
                'nombre': 'Cemec',
                'direccion': 'Av. San Martín y 3er Anillo',
                'telefono': '+591-3-4567890',
                'coordenadas': {'lat': -17.783, 'lng': -63.186},
                'categoria': 'hospital',
                'tipo': 'privada',
                'especialidades': ['Emergencias', 'Cirugía', 'Medicina Interna'],
                'emergencias': 24
            }
        ],
        'supermercado': [
            {
                'nombre': 'Hipermaxi',
                'direccion': 'Av. Santos Dumont y 4to Anillo',
                'telefono': '+591-3-1234567',
                'coordenadas': {'lat': -17.783, 'lng': -63.182},
                'categoria': 'supermercado',
                'cadena': 'Hipermaxi',
                'horario': '07:00 - 22:00',
                'servicios': ['delivery', 'cajero automático']
            },
            {
                'nombre': 'Supermercado El Tore',
                'direccion': 'Calle Junín esq. Ecuador',
                'telefono': '+591-3-2345678',
                'coordenadas': {'lat': -17.785, 'lng': -63.181},
                'categoria': 'supermercado',
                'cadena': 'El Tore',
                'horario': '07:30 - 21:30',
                'servicios': ['delivery', 'panadería']
            },
            {
                'nombre': 'Supermercado Fidalga',
                'direccion': 'Av. Santos Dumont y 3er Anillo',
                'telefono': '+591-3-3456789',
                'coordenadas': {'lat': -17.784, 'lng': -63.184},
                'categoria': 'supermercado',
                'cadena': 'Fidalga',
                'horario': '08:00 - 22:00',
                'servicios': ['delivery', 'carnicería']
            },
            {
                'nombre': 'Supermercado La Sierra',
                'direccion': 'Calle 21 de Calacoto',
                'telefono': '+591-3-4567890',
                'coordenadas': {'lat': -17.779, 'lng': -63.190},
                'categoria': 'supermercado',
                'cadena': 'La Sierra',
                'horario': '07:00 - 21:30',
                'servicios': ['delivery', 'farmacia']
            },
            {
                'nombre': 'Supermercado Ketal',
                'direccion': 'Av. La Salle y 3er Anillo',
                'telefono': '+591-3-5678901',
                'coordenadas': {'lat': -17.788, 'lng': -63.178},
                'categoria': 'supermercado',
                'cadena': 'Ketal',
                'horario': '08:00 - 22:00',
                'servicios': ['delivery', 'panadería']
            },
            {
                'nombre': 'Hipermaxi Equipetrol',
                'direccion': 'Av. San Martín y Equipetrol',
                'telefono': '+591-3-6789012',
                'coordenadas': {'lat': -17.777, 'lng': -63.192},
                'categoria': 'supermercado',
                'cadena': 'Hipermaxi',
                'horario': '07:00 - 22:00',
                'servicios': ['delivery', 'cajero automático']
            },
            {
                'nombre': 'Hipermaxi 3er Anillo',
                'direccion': 'Av. La Salle y 3er Anillo',
                'telefono': '+591-3-7890123',
                'coordenadas': {'lat': -17.787, 'lng': -63.177},
                'categoria': 'supermercado',
                'cadena': 'Hipermaxi',
                'horario': '07:00 - 22:00',
                'servicios': ['delivery', 'panadería']
            },
            {
                'nombre': 'Hipermaxi Centro',
                'direccion': 'Calle Beni esq. Potosí',
                'telefono': '+591-3-8901234',
                'coordenadas': {'lat': -17.785, 'lng': -63.180},
                'categoria': 'supermercado',
                'cadena': 'Hipermaxi',
                'horario': '07:00 - 22:00',
                'servicios': ['delivery', 'cajero automático']
            }
        ],
        'farmacia': [
            {
                'nombre': 'Farmacias Bono',
                'direccion': 'Av. Santos Dumont y 4to Anillo',
                'telefono': '+591-3-1234567',
                'coordenadas': {'lat': -17.783, 'lng': -63.182},
                'categoria': 'farmacia',
                'cadena': 'Bono',
                'horario': '08:00 - 22:00',
                'turno': 24
            },
            {
                'nombre': 'Farmacias Bolivianas',
                'direccion': 'Calle Junín esq. Ecuador',
                'telefono': '+591-3-2345678',
                'coordenadas': {'lat': -17.785, 'lng': -63.181},
                'categoria': 'farmacia',
                'cadena': 'Bolivianas',
                'horario': '08:00 - 22:00',
                'turno': 24
            },
            {
                'nombre': 'Farmacias La Salle',
                'direccion': 'Av. La Salle y 3er Anillo',
                'telefono': '+591-3-3456789',
                'coordenadas': {'lat': -17.788, 'lng': -63.178},
                'categoria': 'farmacia',
                'cadena': 'La Salle',
                'horario': '08:00 - 22:00',
                'turno': 24
            }
        ]
    }

def calcular_distancia(coord1: Dict[str, float], coord2: Dict[str, float]) -> float:
    """Calcula distancia aproximada entre dos coordenadas (fórmula simplificada)."""
    # Fórmula de Haversine simplificada para el PoC
    lat1, lon1 = coord1['lat'], coord1['lng']
    lat2, lon2 = coord2['lat'], coord2['lng']

    # Convertir a radianes
    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])

    # Diferencia en grados
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Distancia aproximada en grados
    distance = ((dlat ** 2) + (dlon ** 2)) ** 0.5

    # Convertir a metros (aproximadamente 111km por grado)
    return distance * 111000

def asociar_servicios_a_propiedades(propiedades: List[Dict], servicios: Dict) -> List[Dict]:
    """Asocia servicios cercanos a cada propiedad."""
    for propiedad in propiedades:
        coord_prop = propiedad['ubicacion']['coordenadas']
        servicios_cercanos = {}

        for categoria, lista_servicios in servicios.items():
            servicios_categoria = []
            for servicio in lista_servicios:
                coord_serv = servicio['coordenadas']
                distancia = calcular_distancia(coord_prop, coord_serv)

                # Considerar servicios dentro de 2km
                if distancia <= 2000:
                    servicio_cercano = servicio.copy()
                    servicio_cercano['distancia'] = round(distancia)
                    servicios_categoria.append(servicio_cercano)

            # Ordenar por distancia y tomar los 3 más cercanos
            servicios_categoria.sort(key=lambda x: x['distancia'])
            servicios_cercanos[categoria] = servicios_categoria[:3]

        propiedad['servicios_cercanos'] = servicios_cercanos

    return propiedades

def main():
    """Función principal."""
    logger.info("Iniciando procesamiento de Guía Urbana...")

    # Directorio de datos
    data_dir = Path("data/raw")

    # Buscar archivos de guía urbana
    archivos_guia = [
        "GUIA URBANA.xlsx",
        "CONSOLIDADO_GUIA_URB.xlsx",
        "CODIGO WEB GUIA URBANA.txt"
    ]

    servicios_encontrados = {}

    # Intentar procesar archivos reales
    for archivo in archivos_guia:
        for ruta in data_dir.rglob(archivo):
            logger.info(f"\nProcesando: {ruta}")

            if ruta.suffix in ['.xlsx', '.xls']:
                df = leer_excel_guia_urbana(str(ruta))
                if df is not None:
                    explorar_guia_urbana(df, str(ruta))
                    servicios_extraidos = extraer_servicios_guia_urbana(df)
                    servicios_encontrados.update(servicios_extraidos)

            elif ruta.suffix == '.txt':
                contenido = leer_codigo_web(str(ruta))
                if contenido:
                    logger.info(f"Contenido del archivo {ruta}:")
                    logger.info(contenido[:500] + "..." if len(contenido) > 500 else contenido)

    # Si no se encontraron suficientes servicios, usar ejemplo
    if not any(servicios_encontrados.values()):
        logger.info("No se encontraron suficientes servicios reales, usando dataset de ejemplo")
        servicios_encontrados = crear_servicios_ejemplo()

    # Cargar propiedades existentes
    propiedades_file = Path("data/propiedades.json")
    if propiedades_file.exists():
        with open(propiedades_file, 'r', encoding='utf-8') as f:
            propiedades = json.load(f)

        # Asociar servicios a propiedades
        propiedades_con_servicios = asociar_servicios_a_propiedades(propiedades, servicios_encontrados)

        # Guardar propiedades actualizadas
        with open(propiedades_file, 'w', encoding='utf-8') as f:
            json.dump(propiedades_con_servicios, f, indent=2, ensure_ascii=False)

        logger.info(f"Propiedades actualizadas con servicios en: {propiedades_file}")

    # Guardar servicios por separado
    servicios_file = Path("data/servicios.json")
    with open(servicios_file, 'w', encoding='utf-8') as f:
        json.dump(servicios_encontrados, f, indent=2, ensure_ascii=False)

    logger.info(f"Servicios guardados en: {servicios_file}")

    # Mostrar resumen
    logger.info("\n=== Resumen de servicios procesados ===")
    for categoria, lista_servicios in servicios_encontrados.items():
        logger.info(f"{categoria}: {len(lista_servicios)} servicios")

if __name__ == "__main__":
    main()