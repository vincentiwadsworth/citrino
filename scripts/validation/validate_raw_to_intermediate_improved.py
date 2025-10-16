#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VALIDACIÓN MEJORADA DE ARCHIVOS RAW A INTERMEDIOS
====================================================

Versión mejorada que integra extracción inteligente de características
usando sistema híbrido LLM + Regex para procesamiento de datos.

Mejoras clave:
- Extracción inteligente de características de texto libre
- Normalización robusta de mayúsculas/minúsculas
- Integración completa con LLM para descripciones
- Manejo mejorado de encoding y caracteres especiales
- Validación mejorada de coordenadas y precios

Uso:
    python scripts/validation/validate_raw_to_intermediate_improved.py --input "data/raw/relevamiento/2025.08.15 05.xlsx"

Author: Claude Code
Date: 2025-10-16
Version: 2.0 - Extracción Inteligente
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import argparse
import warnings
import re
import unicodedata
from pathlib import Path

# Cargar variables de entorno desde .env
def load_env_file():
    """Carga variables de entorno desde archivo .env"""
    env_file = Path(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env_file()

# Agregar el directorio src al path para importar módulos
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

warnings.filterwarnings('ignore')

# Importar módulos de extracción
try:
    import description_parser
    import llm_integration
    DescriptionParser = description_parser.DescriptionParser
    LLMIntegration = llm_integration.LLMIntegration
    EXTRACCION_AVAILABLE = True
    print("Módulos LLM cargados exitosamente")
except ImportError as e:
    print(f"ADVERTENCIA: Módulos de extracción no disponibles: {e}")
    EXTRACCION_AVAILABLE = False

# Configuración de coordenadas Santa Cruz (corregido)
SANTA_CRUZ_BOUNDS = {
    'lat_min': -18.2,
    'lat_max': -17.5,
    'lng_min': -63.5,
    'lng_max': -63.0,
    'centro': (-17.7833, -63.1833)
}

# Rangos de precios aceptables
PRECIO_RANGES = {
    'min': 10000,
    'max': 2000000,
    'outlier_factor': 3.0
}

# Mapeo de columnas comunes para diferentes proveedores
COLUMN_MAPPINGS = {
    'titulo': ['Título', 'Titulo', 'titulo', 'TITLE', 'Title', 'nombre'],
    'descripcion': ['Descripción', 'Descripcion', 'descripción', 'DESCRIPTION', 'Description', 'Personalizado.Descripcion', 'Personalizado.Detalles'],
    'precio': ['Precio', 'precio', 'PRECIO', 'PRICE', 'Price', 'Moneda'],
    'moneda': ['Moneda', 'moneda', 'MONEDA', 'CURRENCY'],
    'habitaciones': ['Habitaciones', 'habitaciones', 'Dormitorios', 'dormitorios', 'HABITACIONES', 'BEDROOMS', 'Bedrooms'],
    'baños': ['Baños', 'Baños', 'Baños', 'baños', 'BATHROOMS', 'Bathrooms'],
    'garajes': ['Garajes', 'garajes', 'GARAGES', 'Garage', 'estacionamientos'],
    'superficie': ['Sup. Construida', 'Sup. Terreno', 'Superficie', 'superficie', 'Área', 'area'],
    'agente': ['Agente', 'agente', 'AGENTE', 'AGENT', 'Agent'],
    'telefono': ['Teléfono', 'Telefono', 'telefono', 'TELÉFONO', 'PHONE', 'Phone'],
    'latitud': ['Latitud', 'latitud', 'LATITUD', 'LAT', 'Lat'],
    'longitud': ['Longitud', 'longitud', 'LONGITUD', 'LNG', 'Lng', 'Lon']
}

class ImprovedDataValidator:
    """Validador mejorado con extracción inteligente de características"""

    def __init__(self, verbose: bool = False, use_llm: bool = True):
        self.verbose = verbose
        self.use_llm = use_llm and EXTRACCION_AVAILABLE
        self.stats = {
            'total_filas': 0,
            'filas_procesadas': 0,
            'errores': 0,
            'coordenadas_validas': 0,
            'coordenadas_invalidas': 0,
            'precios_validos': 0,
            'precios_invalidos': 0,
            'datos_completos': 0,
            'datos_incompletos': 0,
            'duplicados': 0,
            'caracteristicas_extraidas': 0,
            'textos_normalizados': 0
        }
        self.errors = []

        # Inicializar parser de descripciones si está disponible
        if self.use_llm:
            try:
                self.description_parser = DescriptionParser(use_regex_first=True)
                self.log("Parser LLM inicializado")
            except Exception as e:
                self.log(f"Error inicializando LLM: {e}")
                self.use_llm = False
                self.description_parser = None
        else:
            self.description_parser = None

    def log(self, message: str):
        """Imprimir mensaje si verbose está activado"""
        if self.verbose:
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[{timestamp}] {message}")

    def normalize_text(self, text: Any) -> str:
        """
        Normaliza texto de manera robusta:
        - Corrige encoding
        - Estandariza mayúsculas/minúsculas
        - Elimina caracteres problemáticos
        - Preserva acentos y caracteres españoles
        """
        if pd.isna(text) or text is None:
            return ""

        # Convertir a string si no lo es
        if not isinstance(text, str):
            text = str(text)

        # Paso 1: Normalizar Unicode (NFC para preservar acentos)
        text = unicodedata.normalize('NFC', text)

        # Paso 2: Corregir problemas de encoding comunes
        encoding_fixes = {
            'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú',
            'Ã±': 'ñ', 'Ã¼': 'ü', 'Â¿': '¿', 'Â¡': '¡',
            'Ã': 'í', 'Ã': 'ó', 'Ã': 'á', 'Ã': 'é', 'Ã': 'ú',
            'Ã': 'Ñ', 'Ã': 'Ü',
            'Ã¡': 'Á', 'Ã©': 'É', 'Ã­': 'Í', 'Ã³': 'Ó', 'Ãº': 'Ú'
        }

        for wrong, correct in encoding_fixes.items():
            text = text.replace(wrong, correct)

        # Paso 3: Eliminar caracteres de control excepto saltos de línea
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')

        # Paso 4: Estandarizar espacios en blanco
        text = re.sub(r'\s+', ' ', text.strip())

        # Paso 5: Aplicar reglas de capitalización inteligentes
        # Nombres propios y lugares mantienen mayúsculas iniciales
        # El resto está en minúsculas excepto inicio de oración

        # Dividir en oraciones
        sentences = re.split(r'[.!?]+', text)
        normalized_sentences = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Capitalizar primera letra
            if sentence:
                sentence = sentence[0].upper() + sentence[1:]

            # Corregir nombres propios conocidos en Santa Cruz
            proper_names = {
                'equipetrol': 'Equipetrol',
                'urubó': 'Urubó', 'urubo': 'Urubó',
                'santa mónica': 'Santa Mónica', 'santa monica': 'Santa Mónica',
                'urbari': 'Urbari',
                'pampa de la isla': 'Pampa de la Isla',
                'el valle': 'El Valle',
                'las brisas': 'Las Brisas',
                'el palmar': 'El Palmar',
                'villa 1ro de mayo': 'Villa 1ro de Mayo',
                'plan 3000': 'Plan 3000',
                'el cristo': 'El Cristo',
                'la recoleta': 'La Recoleta'
            }

            for name, correct in proper_names.items():
                sentence = re.sub(r'\b' + re.escape(name) + r'\b', correct, sentence, flags=re.IGNORECASE)

            normalized_sentences.append(sentence)

        normalized_text = '. '.join(normalized_sentences)

        # Contar para estadísticas
        if normalized_text != text:
            self.stats['textos_normalizados'] += 1

        return normalized_text

    def find_column_mapping(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Encuentra el mapeo correcto de columnas para el dataset actual
        """
        mapping = {}
        available_columns = list(df.columns)

        for standard_name, possible_names in COLUMN_MAPPINGS.items():
            for col_name in available_columns:
                # Búsqueda exacta primero
                if col_name in possible_names:
                    mapping[standard_name] = col_name
                    break
                # Búsqueda parcial (case insensitive)
                elif any(possible.lower() in col_name.lower() for possible in possible_names):
                    mapping[standard_name] = col_name
                    break

        self.log(f"Mapeo de columnas encontrado: {mapping}")
        return mapping

    def extract_price_improved(self, price_value: Any, moneda_value: Any = None) -> Tuple[float, str, str]:
        """
        Extraer precio numérico con manejo mejorado de monedas
        """
        if pd.isna(price_value) or price_value is None or price_value == "":
            return 0.0, "Sin precio", "USD"

        try:
            # Limpiar texto de precio
            price_str = str(price_value).strip()

            # Detectar moneda explícita
            moneda_detected = "USD"  # Default

            if moneda_value and not pd.isna(moneda_value):
                moneda_str = str(moneda_value).upper()
                if 'BS' in moneda_str or 'BOB' in moneda_str:
                    moneda_detected = "BOB"
                elif 'US' in moneda_str or '$' in moneda_str:
                    moneda_detected = "USD"

            # Patrones de moneda en el texto del precio
            if any(indicator in price_str.upper() for indicator in ['BS', 'BOB', 'BOLIVIANOS']):
                moneda_detected = "BOB"
            elif any(indicator in price_str.upper() for indicator in ['USD', 'US$', '$']):
                moneda_detected = "USD"

            # Extraer número
            # Eliminar símbolos y texto
            price_clean = re.sub(r'[^\d.,]', '', price_str)

            # Manear diferentes formatos de número
            if ',' in price_clean and '.' in price_clean:
                # Ambos separadores presentes, asumir formato boliviano: 1.234,56
                if price_clean.rfind(',') > price_clean.rfind('.'):
                    price_clean = price_clean.replace('.', '').replace(',', '.')
                else:
                    # Formato inglés: 1,234.56
                    price_clean = price_clean.replace(',', '')
            elif ',' in price_clean:
                # Solo comas, podría ser separador decimal o de miles
                if price_clean.count(',') == 1 and len(price_clean.split(',')[1]) <= 2:
                    # Probablemente separador decimal
                    price_clean = price_clean.replace(',', '.')
                else:
                    # Probablemente separador de miles
                    price_clean = price_clean.replace(',', '')

            price_num = float(price_clean)

            # Validar rango según moneda
            if moneda_detected == "BOB":
                if not (70000 <= price_num <= 350000000):  # 70k - 350M Bs
                    return price_num, f"Precio fuera de rango (Bs): {price_num:,.0f}", moneda_detected
            else:  # USD
                if not (10000 <= price_num <= 50000000):  # 10k - 50M USD
                    return price_num, f"Precio fuera de rango (USD): {price_num:,.0f}", moneda_detected

            return price_num, "Precio válido", moneda_detected

        except (ValueError, TypeError) as e:
            return 0.0, f"Error extrayendo precio: {price_value}", "USD"

    def extract_surface_improved(self, surface_value: Any) -> Tuple[float, str]:
        """
        Extraer superficie numérica con manejo mejorado de formatos
        """
        if pd.isna(surface_value) or surface_value is None or surface_value == "":
            return 0.0, "Sin superficie"

        try:
            surface_str = str(surface_value).strip()

            # Extraer número usando regex
            match = re.search(r'([\d,.]+)', surface_str)
            if not match:
                return 0.0, f"No se encontró número en: {surface_value}"

            surface_clean = match.group(1)

            # Limpiar separadores
            if ',' in surface_clean and '.' in surface_clean:
                if surface_clean.rfind(',') > surface_clean.rfind('.'):
                    surface_clean = surface_clean.replace('.', '').replace(',', '.')
                else:
                    surface_clean = surface_clean.replace(',', '')
            elif ',' in surface_clean:
                if surface_clean.count(',') == 1 and len(surface_clean.split(',')[1]) <= 2:
                    surface_clean = surface_clean.replace(',', '.')
                else:
                    surface_clean = surface_clean.replace(',', '')

            surface_num = float(surface_clean)

            # Validar rango razonable (10 m² - 100,000 m²)
            if not (10 <= surface_num <= 100000):
                return surface_num, f"Superficie fuera de rango: {surface_num} m²"

            return surface_num, "Superficie válida"

        except (ValueError, TypeError) as e:
            return 0.0, f"Error extrayendo superficie: {surface_value}"

    def normalize_coordinates(self, lat: Any, lng: Any) -> Tuple[Optional[float], Optional[float], str]:
        """
        Normalizar coordenadas con manejo mejorado de formatos
        """
        if pd.isna(lat) or pd.isna(lng) or lat == 0 or lng == 0:
            return None, None, "Coordenadas vacías o cero"

        try:
            lat_float = float(lat)
            lng_float = float(lng)
        except (ValueError, TypeError):
            return None, None, "Error convirtiendo a número"

        # Caso 1: Coordenadas ya en rango correcto
        if (SANTA_CRUZ_BOUNDS['lat_min'] <= lat_float <= SANTA_CRUZ_BOUNDS['lat_max'] and
            SANTA_CRUZ_BOUNDS['lng_min'] <= lng_float <= SANTA_CRUZ_BOUNDS['lng_max']):
            return lat_float, lng_float, "Coordenadas válidas"

        # Caso 2: Coordenadas invertidas
        if (SANTA_CRUZ_BOUNDS['lat_min'] <= lng_float <= SANTA_CRUZ_BOUNDS['lat_max'] and
            SANTA_CRUZ_BOUNDS['lng_min'] <= lat_float <= SANTA_CRUZ_BOUNDS['lng_max']):
            return lng_float, lat_float, "Coordenadas invertidas y corregidas"

        # Caso 3: Coordenadas multiplicadas por factores grandes
        if abs(lat_float) > 100 or abs(lng_float) > 100:
            # Probar factores comunes para GPS
            factors = [10**8, 10**7, 10**6, 10**5, 10**4, 10**3, 10**2]

            for factor in factors:
                lat_test = lat_float / factor
                lng_test = lng_float / factor

                if (SANTA_CRUZ_BOUNDS['lat_min'] <= lat_test <= SANTA_CRUZ_BOUNDS['lat_max'] and
                    SANTA_CRUZ_BOUNDS['lng_min'] <= lng_test <= SANTA_CRUZ_BOUNDS['lng_max']):
                    return lat_test, lng_test, f"Coordenadas normalizadas (divididas por {factor})"

        return lat_float, lng_float, "Coordenadas fuera de rango (no se pudo normalizar)"

    def extract_characteristics_from_text(self, title: str, description: str) -> Dict[str, Any]:
        """
        Extrae características del texto usando LLM y regex
        """
        if not self.description_parser:
            return {}

        try:
            # Combinar título y descripción
            full_text = f"{title} {description}"

            # Usar el parser híbrido
            extracted = self.description_parser.extract_from_description(
                descripcion=description,
                titulo=title,
                use_cache=True
            )

            # Contar características extraídas
            caract_count = sum(1 for k, v in extracted.items()
                             if k not in ['_extraction_method', '_llm_provider', '_llm_model', '_fallback_usado']
                             and v is not None and v != "" and v != [])

            if caract_count > 0:
                self.stats['caracteristicas_extraidas'] += 1
                self.log(f"  Extraídas {caract_count} características: {extracted.get('_extraction_method')}")

            return extracted

        except Exception as e:
            self.log(f"Error extrayendo características: {e}")
            return {}

    def process_propiedades_file(self, df: pd.DataFrame, filename: str) -> pd.DataFrame:
        """
        Procesa archivo de propiedades con extracción inteligente
        """
        self.log(f"Procesando {len(df)} filas de propiedades")

        # Encontrar mapeo de columnas
        column_mapping = self.find_column_mapping(df)
        self.log(f"Columnas mapeadas: {column_mapping}")

        processed_rows = []

        for idx, row in df.iterrows():
            self.stats['total_filas'] += 1

            try:
                # Extraer datos usando mapeo de columnas
                titulo_original = self.normalize_text(row.get(column_mapping.get('titulo', 'Título'), ''))
                precio_original = row.get(column_mapping.get('precio', 'Precio'), 0)
                moneda_original = row.get(column_mapping.get('moneda', 'Moneda'), None)
                descripcion_original = self.normalize_text(row.get(column_mapping.get('descripcion', 'Descripción'), ''))
                agente_original = self.normalize_text(row.get(column_mapping.get('agente', 'Agente'), ''))
                telefono_original = self.normalize_text(row.get(column_mapping.get('telefono', 'Teléfono'), ''))

                # Extraer características existentes si están disponibles
                habitaciones_original = row.get(column_mapping.get('habitaciones', 'Habitaciones'))
                baños_original = row.get(column_mapping.get('baños', 'Baños'))
                garajes_original = row.get(column_mapping.get('garajes', 'Garajes'))
                superficie_original = row.get(column_mapping.get('superficie', 'Superficie'))

                # Procesar datos numéricos
                precio_normalizado, precio_msg, moneda = self.extract_price_improved(precio_original, moneda_original)
                sup_terreno, sup_terreno_msg = self.extract_surface_improved(superficie_original)

                # Extraer coordenadas
                lat_raw = row.get(column_mapping.get('latitud', 'Latitud'))
                lng_raw = row.get(column_mapping.get('longitud', 'Longitud'))
                lat_procesada, lng_procesada, coords_msg = self.normalize_coordinates(lat_raw, lng_raw)

                # Validar coordenadas
                coords_valid, coords_validation_msg = self.validate_coordinates(lat_procesada, lng_procesada)

                # Combinar mensajes de coordenadas
                if coords_valid:
                    coords_msg_final = coords_msg
                else:
                    coords_msg_final = f"{coords_msg} | {coords_validation_msg}"

                # Extraer características del texto con LLM/Regex
                extracted_characteristics = {}
                if descripcion_original and self.use_llm:
                    extracted_characteristics = self.extract_characteristics_from_text(titulo_original, descripcion_original)

                # Combinar características existentes con extraídas
                # Prioridad: características extraídas > características originales
                habitaciones = extracted_characteristics.get('habitaciones', habitaciones_original)
                baños = extracted_characteristics.get('banos', baños_original)
                garajes = garajes_original  # Generalmente no viene en descripciones
                sup_construida = extracted_characteristics.get('superficie_construida')

                # Si no hay superficie construida pero sí terreno, usar esa como referencia
                if not sup_construida and sup_terreno > 0:
                    sup_construida = sup_terreno
                elif not sup_construida and extracted_characteristics.get('superficie'):
                    sup_construida = extracted_characteristics['superficie']

                # Validar precio
                price_valid, price_msg = self.validate_price(precio_normalizado)

                # Determinar estado general
                estado = "OK"
                observaciones = []

                if not coords_valid:
                    estado = "SIN_COORDENADAS"
                    observaciones.append(coords_msg_final)
                    self.stats['coordenadas_invalidas'] += 1
                else:
                    self.stats['coordenadas_validas'] += 1

                if not price_valid:
                    if estado == "OK":
                        estado = "ERROR_PRECIO"
                    observaciones.append(price_msg)
                    self.stats['precios_invalidos'] += 1
                else:
                    self.stats['precios_validos'] += 1

                # Verificar datos completos
                datos_completos = bool(
                    titulo_original and
                    precio_normalizado > 0 and
                    (lat_procesada and lng_procesada)
                )

                if not datos_completos:
                    if estado == "OK":
                        estado = "DATOS_INCOMPLETOS"
                    observaciones.append("Datos incompletos")
                    self.stats['datos_incompletos'] += 1
                else:
                    self.stats['datos_completos'] += 1

                # Crear fila procesada mejorada
                processed_row = {
                    # Datos originales (preservados)
                    'Original_Titulo': titulo_original,
                    'Original_Precio': precio_original,
                    'Original_Moneda': moneda_original,
                    'Original_Descripcion': descripcion_original,
                    'Original_Agente': agente_original,
                    'Original_Telefono': telefono_original,
                    'Original_Habitaciones': habitaciones_original,
                    'Original_Baños': baños_original,
                    'Original_Garajes': garajes_original,
                    'Original_Superficie': superficie_original,

                    # Datos procesados y normalizados
                    'Titulo_Limpio': titulo_original,
                    'Precio_Normalizado': precio_normalizado,
                    'Moneda_Detectada': moneda,
                    'Descripcion_Limpia': descripcion_original,
                    'Agente_Limpio': agente_original,
                    'Telefono_Limpio': telefono_original,

                    # Coordenadas
                    'Latitud_Procesada': lat_procesada,
                    'Longitud_Procesada': lng_procesada,

                    # Características (combinadas)
                    'Habitaciones': habitaciones,
                    'Baños': baños,
                    'Garajes': garajes,
                    'Sup_Terreno': sup_terreno,
                    'Sup_Construida': sup_construida,

                    # Datos extraídos por LLM/Regex
                    'Zona_Extraida': extracted_characteristics.get('zona'),
                    'Tipo_Propiedad_Extraido': extracted_characteristics.get('tipo_propiedad'),
                    'Caracteristicas_Extraidas': extracted_characteristics.get('caracteristicas', []),
                    'Amenities_Extraidas': extracted_characteristics.get('amenities', []),
                    'Metodo_Extraccion': extracted_characteristics.get('_extraction_method', 'none'),
                    'LLM_Provider': extracted_characteristics.get('_llm_provider', 'none'),

                    # Estado y observaciones
                    'ESTADO': estado,
                    'OBSERVACIONES': ' | '.join(observaciones) if observaciones else '',

                    # Metadatos
                    'Fuente_Archivo': filename,
                    'Fecha_Procesamiento': datetime.now().isoformat()
                }

                processed_rows.append(processed_row)
                self.stats['filas_procesadas'] += 1

            except Exception as e:
                self.stats['errores'] += 1
                error_msg = f"Error procesando fila {idx}: {str(e)}"
                self.errors.append(error_msg)
                self.log(error_msg)

                # Agregar fila de error
                error_row = {
                    'ESTADO': 'ERROR',
                    'OBSERVACIONES': error_msg,
                    'Fuente_Archivo': filename,
                    'Fecha_Procesamiento': datetime.now().isoformat()
                }
                processed_rows.append(error_row)

        return pd.DataFrame(processed_rows)

    def validate_coordinates(self, lat: Optional[float], lng: Optional[float]) -> Tuple[bool, str]:
        """Validar si las coordenadas están dentro del rango de Santa Cruz"""
        if lat is None or lng is None:
            return False, "Sin coordenadas"

        if not (SANTA_CRUZ_BOUNDS['lat_min'] <= lat <= SANTA_CRUZ_BOUNDS['lat_max']):
            return False, f"Latitud fuera de rango: {lat}"

        if not (SANTA_CRUZ_BOUNDS['lng_min'] <= lng <= SANTA_CRUZ_BOUNDS['lng_max']):
            return False, f"Longitud fuera de rango: {lng}"

        return True, "Coordenadas válidas"

    def validate_price(self, price: float) -> Tuple[bool, str]:
        """Validar si el precio está en un rango razonable"""
        if price <= 0:
            return False, "Precio inválido (<= 0)"

        if price < PRECIO_RANGES['min']:
            return False, f"Precio muy bajo: ${price:,.0f}"

        if price > PRECIO_RANGES['max']:
            return False, f"Precio muy alto: ${price:,.0f}"

        return True, "Precio válido"

    def generate_excel_output(self, df_processed: pd.DataFrame, filename: str, output_path: str) -> bool:
        """Generar archivo Excel intermedio mejorado"""
        try:
            base_name = os.path.splitext(os.path.basename(filename))[0]
            output_file = os.path.join(output_path, f"{base_name}_intermedio.xlsx")

            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Hoja 1: Resumen mejorado
                summary_data = {
                    'Métrica': [
                        'Total filas',
                        'Filas procesadas',
                        'Errores',
                        'Coordenadas válidas',
                        'Coordenadas inválidas',
                        'Datos completos',
                        'Datos incompletos',
                        'Características extraídas con LLM/Regex',
                        'Textos normalizados',
                        'Duplicados detectados'
                    ],
                    'Cantidad': [
                        self.stats['total_filas'],
                        self.stats['filas_procesadas'],
                        self.stats['errores'],
                        self.stats['coordenadas_validas'],
                        self.stats['coordenadas_invalidas'],
                        self.stats['datos_completos'],
                        self.stats['datos_incompletos'],
                        self.stats['caracteristicas_extraidas'],
                        self.stats['textos_normalizados'],
                        self.stats['duplicados']
                    ]
                }

                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='RESUMEN_PROCESAMIENTO', index=False)

                # Hoja 2: Datos procesados
                df_processed.to_excel(writer, sheet_name='DATOS_PROCESADOS', index=False)

                # Hoja 3: Estadísticas de extracción
                if self.stats['caracteristicas_extraidas'] > 0:
                    extraction_stats = {
                        'Métrica': [
                            'Propiedades con características extraídas',
                            'Método de extracción usado',
                            'LLM Provider utilizado',
                            'Textos normalizados (encoding/capitalización)'
                        ],
                        'Valor': [
                            self.stats['caracteristicas_extraidas'],
                            'LLM + Regex (híbrido)',
                            'Configurado automáticamente',
                            self.stats['textos_normalizados']
                        ]
                    }
                    extraction_df = pd.DataFrame(extraction_stats)
                    extraction_df.to_excel(writer, sheet_name='EXTRACCION_INTELIGENTE', index=False)

                # Hoja 4: Errores
                if self.errors:
                    errors_df = pd.DataFrame({'Error': self.errors})
                    errors_df.to_excel(writer, sheet_name='ERRORES', index=False)

            self.log(f"Archivo Excel mejorado generado: {output_file}")
            return True

        except Exception as e:
            self.log(f"Error generando Excel: {e}")
            return False

    def generate_json_report(self, filename: str, output_path: str) -> bool:
        """Generar reporte JSON mejorado"""
        try:
            base_name = os.path.splitext(os.path.basename(filename))[0]
            report_file = os.path.join(output_path, f"{base_name}_reporte.json")

            # Calcular porcentajes
            total = self.stats['total_filas']
            if total > 0:
                porcentajes = {
                    'coordenadas_validas_pct': (self.stats['coordenadas_validas'] / total) * 100,
                    'datos_completos_pct': (self.stats['datos_completos'] / total) * 100,
                    'errores_pct': (self.stats['errores'] / total) * 100,
                    'caracteristicas_extraidas_pct': (self.stats['caracteristicas_extraidas'] / total) * 100,
                    'textos_normalizados_pct': (self.stats['textos_normalizados'] / total) * 100
                }
            else:
                porcentajes = {key: 0 for key in ['coordenadas_validas_pct', 'datos_completos_pct', 'errores_pct', 'caracteristicas_extraidas_pct', 'textos_normalizados_pct']}

            report = {
                'archivo_origen': filename,
                'fecha_procesamiento': datetime.now().isoformat(),
                'version_script': '2.0 - Extracción Inteligente',
                'estadisticas': self.stats,
                'porcentajes': porcentajes,
                'errores_detalle': self.errors,
                'metricas_calidad': {
                    'coordenadas_validas': porcentajes['coordenadas_validas_pct'],
                    'datos_completos': porcentajes['datos_completos_pct'],
                    'tasa_errores': porcentajes['errores_pct'],
                    'extraccion_inteligente': porcentajes['caracteristicas_extraidas_pct'],
                    'normalizacion_texto': porcentajes['textos_normalizados_pct']
                },
                'caracteristicas_procesamiento': {
                    'usa_llm': self.use_llm,
                    'extraccion_hibrida': True,
                    'normalizacion_encoding': True,
                    'mapeo_columnas': True,
                    'validacion_mejorada': True
                },
                'estado_calidad': self._determine_quality_level(porcentajes)
            }

            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            self.log(f"Reporte JSON mejorado generado: {report_file}")
            return True

        except Exception as e:
            self.log(f"Error generando reporte JSON: {e}")
            return False

    def _determine_quality_level(self, porcentajes: Dict[str, float]) -> str:
        """Determinar nivel de calidad basado en métricas mejoradas"""
        coords_ok = porcentajes['coordenadas_validas_pct']
        datos_ok = porcentajes['datos_completos_pct']
        errores_ok = porcentajes['errores_pct']
        extraccion_ok = porcentajes['caracteristicas_extraidas_pct']

        # Criterios más estrictos para esta versión mejorada
        if coords_ok >= 95 and datos_ok >= 90 and errores_ok <= 1 and extraccion_ok >= 50:
            return "EXCELENTE"
        elif coords_ok >= 80 and datos_ok >= 70 and errores_ok <= 5 and extraccion_ok >= 30:
            return "BUENO"
        elif coords_ok >= 60 and datos_ok >= 50 and errores_ok <= 15 and extraccion_ok >= 10:
            return "ACEPTABLE"
        elif coords_ok >= 40 and datos_ok >= 30 and errores_ok <= 25:
            return "NECESITA_MEJORAS"
        else:
            return "PROBLEMAS_GRAVES"

    def process_file(self, input_path: str, output_path: str, file_type: str = 'propiedades') -> bool:
        """Procesar archivo individual con mejoras inteligentes"""
        if not os.path.exists(input_path):
            self.log(f"ERROR: Archivo no encontrado: {input_path}")
            return False

        filename = os.path.basename(input_path)
        self.log(f"Iniciando procesamiento mejorado de: {filename}")

        try:
            # Leer archivo Excel
            df = pd.read_excel(input_path)
            self.log(f"Archivo leído: {len(df)} filas, {len(df.columns)} columnas")

            # Procesar según tipo
            if file_type == 'servicios':
                # Para servicios, usar el método original (no hay características que extraer)
                from scripts.validation.validate_raw_to_intermediate import RawDataValidator
                original_validator = RawDataValidator(verbose=self.verbose)
                df_processed = original_validator.process_servicios_file(df, filename)
            else:
                # Para propiedades, usar el procesamiento mejorado
                df_processed = self.process_propiedades_file(df, filename)

            # Generar archivos de salida mejorados
            excel_success = self.generate_excel_output(df_processed, filename, output_path)
            json_success = self.generate_json_report(filename, output_path)

            if excel_success and json_success:
                self.log(f"Procesamiento mejorado completado exitosamente")

                # Mostrar resumen de mejoras
                if self.stats['caracteristicas_extraidas'] > 0:
                    print(f"\nMEJORAS IMPLEMENTADAS:")
                    print(f"   • Características extraídas: {self.stats['caracteristicas_extraidas']} propiedades")
                    print(f"   • Textos normalizados: {self.stats['textos_normalizados']} propiedades")
                    print(f"   • Método: LLM + Regex (híbrido)")
                    print(f"   • Encoding y capitalización corregidos")

                return True
            else:
                self.log("Error generando archivos de salida")
                return False

        except Exception as e:
            self.log(f"Error procesando archivo: {e}")
            return False


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Validar archivo raw y generar intermedio mejorado con extracción inteligente')
    parser.add_argument('--input', required=True, help='Ruta al archivo raw de entrada')
    parser.add_argument('--output', default='data/processed', help='Directorio de salida')
    parser.add_argument('--type', choices=['propiedades', 'servicios'], default='propiedades', help='Tipo de archivo')
    parser.add_argument('--verbose', action='store_true', help='Mostrar detalles del procesamiento')
    parser.add_argument('--no-llm', action='store_true', help='Desactivar extracción con LLM (solo regex)')

    args = parser.parse_args()

    # Verificar archivo de entrada
    if not os.path.exists(args.input):
        print(f"ERROR: Archivo no encontrado: {args.input}")
        return False

    # Crear directorio de salida
    os.makedirs(args.output, exist_ok=True)

    # Iniciar procesamiento mejorado
    validator = ImprovedDataValidator(
        verbose=args.verbose,
        use_llm=not args.no_llm
    )

    success = validator.process_file(args.input, args.output, args.type)

    if success:
        print(f"\nPROCESAMIENTO MEJORADO EXITOSO")
        print(f"Archivos generados en: {args.output}")
        print(f"Revisa los archivos intermedios para validación humana")
        print(f"Las características ahora se extraen automáticamente del texto")
    else:
        print("PROCESAMIENTO FALLIDO")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)