#!/usr/bin/env python3
"""
EXTRACCIÓN Y TRANSFORMACIÓN DE RAW A INTERMEDIOS
===============================================

Script portátil para procesar archivos raw generando:
1. Archivo Excel intermedio con columnas originales + procesadas
2. Reporte JSON con métricas de calidad
3. Extracción inteligente de características con LLM

Uso:
    python migration/scripts/extract_raw_to_intermediate.py --input "data/raw/relevamiento/2025.08.15 05.xlsx"
    python migration/scripts/extract_raw_to_intermediate.py --input-dir "data/raw/"

Author: Claude Code
Date: 2025-10-16
"""

import os
import sys

# Bloque UTF-8 autoconsciente para portabilidad en Windows
if os.name == 'nt':
    # Reconfigurar la salida estándar para forzar UTF-8 si no está configurada
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
            print("INFO: Se ha forzado la codificación de la consola a UTF-8.")
        except TypeError:
            # Solución alternativa para versiones específicas
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
            print("INFO: Se ha forzado la codificación de la consola a UTF-8 (modo alternativo).")
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
warnings.filterwarnings('ignore')

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
    'lng_max': -63.0
}

# Rangos de precios aceptables
PRECIO_RANGES = {
    'min': 10000,
    'max': 2000000,
    'outlier_factor': 3.0
}

# Tasa de conversión BOB a USD (actualizable)
TASA_CAMBIO_BOB_USD = 6.96  # 1 USD = 6.96 BOB (tasa aproximada)

class RawDataValidator:
    """Validador de archivos raw con generación de archivos intermedios"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
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
            'extracciones_regex': 0,
            'extracciones_llm': 0,
            'conversiones_moneda': 0
        }
        self.errors = []

        # Inicializar parser avanzado de descripciones
        if EXTRACCION_AVAILABLE:
            try:
                self.description_parser = DescriptionParser(use_regex_first=True)
                self.log("Parser LLM inicializado")
            except Exception as e:
                self.log(f"Error inicializando LLM: {e}")
                self.description_parser = None
        else:
            self.description_parser = None
            self.log("DescriptionParser no disponible, usando extracción básica")

    def log(self, message: str):
        """Imprimir mensaje si verbose está activado"""
        if self.verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

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

        return text

    def validate_coordinates(self, lat: Optional[float], lng: Optional[float]) -> Tuple[bool, str]:
        """
        Validar si las coordenadas están dentro del rango de Santa Cruz
        """
        if lat is None or lng is None:
            return False, "Sin coordenadas"

        if not (SANTA_CRUZ_BOUNDS['lat_min'] <= lat <= SANTA_CRUZ_BOUNDS['lat_max']):
            return False, f"Latitud fuera de rango: {lat}"

        if not (SANTA_CRUZ_BOUNDS['lng_min'] <= lng <= SANTA_CRUZ_BOUNDS['lng_max']):
            return False, f"Longitud fuera de rango: {lng}"

        return True, "Coordenadas válidas"

    def validate_price(self, price: float) -> Tuple[bool, str]:
        """
        Validar si el precio está en un rango razonable
        """
        if price <= 0:
            return False, "Precio inválido (<= 0)"

        if price < PRECIO_RANGES['min']:
            return False, f"Precio muy bajo: ${price:,.0f}"

        if price > PRECIO_RANGES['max']:
            return False, f"Precio muy alto: ${price:,.0f}"

        return True, "Precio válido"

    def clean_text(self, text: Any) -> str:
        """
        Limpiar y normalizar texto
        """
        if pd.isna(text) or text is None:
            return ""

        text_str = str(text).strip()
        # Eliminar caracteres problemáticos
        problematic_chars = ['\x00', '\x01', '\x02', '\x03', '\x04', '\x05']
        for char in problematic_chars:
            text_str = text_str.replace(char, '')

        return text_str

    def extract_price(self, price_value: Any) -> Tuple[float, str]:
        """
        Extraer precio numérico de texto con detección de moneda y conversión automática
        """
        if pd.isna(price_value) or price_value is None:
            return 0.0, "Sin precio"

        try:
            price_str = str(price_value).strip()
            moneda_detectada = "USD"

            # Detectar moneda en el texto original
            if any(indicator in price_str.upper() for indicator in ['BOB', 'BS.', 'BS', 'BOLIVIANOS']):
                moneda_detectada = "BOB"
            elif '$' in price_str and 'US' in price_str.upper():
                moneda_detectada = "USD"

            # Limpiar símbolos y texto para extracción numérica
            price_str_limpio = price_str.replace('$', '').replace('USD', '').replace('Usd', '').replace('BOB', '').replace('Bs.', '').replace('BS', '').replace('bolivianos', '').replace(',', '').strip()

            # Extraer número
            price_num = float(price_str_limpio)

            # Convertir a USD si está en BOB
            if moneda_detectada == "BOB":
                price_num_usd = price_num / TASA_CAMBIO_BOB_USD
                self.stats['conversiones_moneda'] += 1
                return price_num_usd, f"Precio BOB convertido: {price_num:,.0f} Bs → {price_num_usd:,.0f} USD"
            else:
                return price_num, f"Precio USD extraído: {price_num:,.0f}"

        except (ValueError, TypeError):
            return 0.0, f"Error extrayendo precio: {price_value}"

    def extract_advanced_features(self, titulo: str, descripcion: str) -> Dict[str, Any]:
        """
        Extrae características del texto usando LLM y regex
        """
        if not self.description_parser:
            return {}

        try:
            # Usar el parser híbrido
            extracted = self.description_parser.extract_from_description(
                descripcion=descripcion,
                titulo=titulo,
                use_cache=True
            )

            # Actualizar estadísticas
            metodo = extracted.get('_extraction_method', 'desconocido')
            if metodo == 'regex_only':
                self.stats['extracciones_regex'] += 1
            elif 'llm' in metodo:
                self.stats['extracciones_llm'] += 1

            self.log(f"  Extraídas características vía {metodo}")

            # Mapear campos a nombres estandarizados
            resultado = {
                'estado_operativo': extracted.get('estado_operativo'),
                'habitaciones_extraidas': extracted.get('habitaciones'),
                'banos_extraidos': extracted.get('banos'),
                'garajes_extraidos': extracted.get('garajes'),
                'superficie_extraida': extracted.get('superficie'),
                'agente_extraido': extracted.get('agente'),
                'contacto_agente': extracted.get('contacto_agente'),
                'zona_extraida': extracted.get('zona'),
                'tipo_propiedad': extracted.get('tipo_propiedad'),
                'amenities_extraidos': extracted.get('caracteristicas', []),
                'informacion_adicional': extracted.get('informacion_adicional'),
                'metodo_extraccion': metodo,
                'proveedor_llm': extracted.get('_llm_provider'),
                'modelo_llm': extracted.get('_llm_model'),
                'fallback_usado': extracted.get('_fallback_usado', False)
            }

            return resultado

        except Exception as e:
            self.log(f"Error extrayendo características: {e}")
            return {}

    def extract_surface(self, surface_value: Any) -> Tuple[float, str]:
        """
        Extraer superficie numérica
        """
        if pd.isna(surface_value) or surface_value is None:
            return 0.0, "Sin superficie"

        try:
            surface_str = str(surface_value)
            # Limpiar unidades
            surface_str = surface_str.replace('m2', '').replace('mt2', '').replace('m²', '').replace(',', '').strip()
            surface_num = float(surface_str)
            return surface_num, "Superficie extraída"

        except (ValueError, TypeError):
            return 0.0, f"Error extrayendo superficie: {surface_value}"

    def normalize_coordinates(self, lat: Any, lng: Any) -> Tuple[Optional[float], Optional[float], str]:
        """
        Normalizar coordenadas que puedan estar en formatos incorrectos
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

        # Caso 2: Coordenadas invertidas (lat/lng intercambiados)
        if (SANTA_CRUZ_BOUNDS['lat_min'] <= lng_float <= SANTA_CRUZ_BOUNDS['lat_max'] and
            SANTA_CRUZ_BOUNDS['lng_min'] <= lat_float <= SANTA_CRUZ_BOUNDS['lng_max']):
            return lng_float, lat_float, "Coordenadas invertidas y corregidas"

        # Caso 3: Coordenadas multiplicadas por factores diferentes
        if abs(lat_float) > 100 or abs(lng_float) > 100:
            # Probar diferentes factores para cada coordenada independientemente
            factors = [10**16, 10**15, 10**14, 10**13, 10**12, 10**11, 10**10, 10**9, 10**8, 10**7, 10**6, 10**5, 10**4, 10**3, 10**2]

            for lat_factor in factors:
                lat_test = lat_float / lat_factor
                if SANTA_CRUZ_BOUNDS['lat_min'] <= lat_test <= SANTA_CRUZ_BOUNDS['lat_max']:
                    # Encontramos el factor correcto para latitud, ahora buscar longitud
                    for lng_factor in factors:
                        lng_test = lng_float / lng_factor
                        if SANTA_CRUZ_BOUNDS['lng_min'] <= lng_test <= SANTA_CRUZ_BOUNDS['lng_max']:
                            return lat_test, lng_test, f"Coordenadas normalizadas (lat/{lat_factor}, lng/{lng_factor})"
                    break  # Si encontramos lat pero no lng, seguimos con siguiente factor

        # Caso 4: Coordenadas con el mismo factor (más simple)
        if abs(lat_float) > 1000 and abs(lng_float) > 1000:
            # Probar factores comunes para ambas coordenadas
            common_factors = [10**16, 10**15, 10**14, 10**13, 10**12, 10**11, 10**10]
            for factor in common_factors:
                lat_test = lat_float / factor
                lng_test = lng_float / factor

                if (SANTA_CRUZ_BOUNDS['lat_min'] <= lat_test <= SANTA_CRUZ_BOUNDS['lat_max'] and
                    SANTA_CRUZ_BOUNDS['lng_min'] <= lng_test <= SANTA_CRUZ_BOUNDS['lng_max']):
                    return lat_test, lng_test, f"Coordenadas normalizadas (divididas por {factor})"

        # Caso 5: Coordenadas en grados decimales pero con signos incorrectos
        lat_abs = abs(lat_float)
        lng_abs = abs(lng_float)

        if (SANTA_CRUZ_BOUNDS['lat_min'] <= -lat_abs <= SANTA_CRUZ_BOUNDS['lat_max'] and
            SANTA_CRUZ_BOUNDS['lng_min'] <= -lng_abs <= SANTA_CRUZ_BOUNDS['lng_max']):
            return -lat_abs, -lng_abs, "Coordenadas con signos corregidos"

        return lat_float, lng_float, "Coordenadas fuera de rango (no se pudo normalizar)"

    def detect_duplicates(self, df: pd.DataFrame) -> List[int]:
        """
        Detectar filas duplicadas basadas en título + precio + coordenadas
        """
        duplicates = []

        for i in range(len(df)):
            for j in range(i + 1, len(df)):
                row_i = df.iloc[i]
                row_j = df.iloc[j]

                # Comparar clave
                title_i = str(row_i.get('Titulo_Limpio', '')).lower().strip()
                title_j = str(row_j.get('Titulo_Limpio', '')).lower().strip()

                price_i = row_i.get('Precio_Normalizado', 0)
                price_j = row_j.get('Precio_Normalizado', 0)

                lat_i = row_i.get('Latitud_Procesada')
                lng_i = row_i.get('Longitud_Procesada')
                lat_j = row_j.get('Latitud_Procesada')
                lng_j = row_j.get('Longitud_Procesada')

                # Criterio de duplicado
                if (title_i == title_j and title_i != "" and
                    abs(price_i - price_j) < 100 and  # Diferencia menor a $100
                    lat_i and lng_i and lat_j and lng_j and
                    abs(lat_i - lat_j) < 0.0001 and abs(lng_i - lng_j) < 0.0001):
                    duplicates.append(j)

        return list(set(duplicates))

    def process_propiedades_file(self, df: pd.DataFrame, filename: str) -> pd.DataFrame:
        """
        Procesar archivo de propiedades
        """
        self.log(f"Procesando {len(df)} filas de propiedades")

        processed_rows = []

        for idx, row in df.iterrows():
            self.stats['total_filas'] += 1

            # Reporte de progreso en tiempo real
            progress = f"({idx+1}/{len(df)})"
            if idx % 50 == 0 or idx == len(df) - 1:  # Reportar cada 50 o al final
                print(f"[PROGRESO] {filename}: {progress} - {((idx+1)/len(df))*100:.1f}%")

            try:
                # Extraer datos básicos
                titulo_original = self.normalize_text(row.get('Título') or row.get('Titulo') or row.get('titulo', ''))
                precio_original = row.get('Precio', 0)
                descripcion_original = self.normalize_text(row.get('Descripción') or row.get('Descripcion', ''))
                agente_original = self.normalize_text(row.get('Agente', ''))
                telefono_original = self.normalize_text(row.get('Teléfono') or row.get('Telefono', ''))

                # Procesar datos
                precio_normalizado, precio_msg = self.extract_price(precio_original)
                titulo_limpio = titulo_original
                descripcion_limpia = descripcion_original

                # EXTRAER CARACTERÍSTICAS AVANZADAS usando DescriptionParser
                caract_avanzadas = self.extract_advanced_features(titulo_original, descripcion_original)

                # Extraer coordenadas
                lat_raw = row.get('Latitud')
                lng_raw = row.get('Longitud')

                # Normalizar coordenadas con la nueva función
                lat_procesada, lng_procesada, coords_msg = self.normalize_coordinates(lat_raw, lng_raw)

                # Validar coordenadas normalizadas
                coords_valid, coords_validation_msg = self.validate_coordinates(lat_procesada, lng_procesada)

                # Combinar mensajes
                if coords_valid:
                    coords_msg = coords_msg
                else:
                    coords_msg = f"{coords_msg} | {coords_validation_msg}"

                # Validar precio
                price_valid, price_msg = self.validate_price(precio_normalizado)

                # Determinar estado general
                estado = "OK"
                observaciones = []

                if not coords_valid:
                    estado = "SIN_COORDENADAS"
                    observaciones.append(coords_msg)
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
                datos_completos = bool(titulo_limpio and precio_normalizado > 0 and (lat_procesada and lng_procesada))

                if not datos_completos:
                    if estado == "OK":
                        estado = "DATOS_INCOMPLETOS"
                    observaciones.append("Datos incompletos")
                    self.stats['datos_incompletos'] += 1
                else:
                    self.stats['datos_completos'] += 1

                # Extraer características adicionales si existen
                habitaciones = row.get('Habitaciones')
                baños = row.get('Baños') or row.get('Baños')
                garajes = row.get('Garajes')
                sup_terreno, sup_terreno_msg = self.extract_surface(row.get('Sup. Terreno'))
                sup_construida, sup_construida_msg = self.extract_surface(row.get('Sup. Construida'))

                # Crear fila procesada con características avanzadas
                processed_row = {
                    # Datos originales (preservados)
                    'Original_Titulo': titulo_original,
                    'Original_Precio': precio_original,
                    'Original_Descripcion': descripcion_original,
                    'Original_Agente': agente_original,
                    'Original_Telefono': telefono_original,

                    # Datos procesados
                    'Titulo_Limpio': titulo_limpio,
                    'Precio_Normalizado': precio_normalizado,
                    'Descripcion_Limpia': descripcion_limpia,
                    'Agente_Limpio': agente_original,
                    'Telefono_Limpio': telefono_original,

                    # Coordenadas
                    'Latitud_Procesada': lat_procesada,
                    'Longitud_Procesada': lng_procesada,

                    # Características básicas (originales)
                    'Habitaciones': habitaciones,
                    'Baños': baños,
                    'Garajes': garajes,
                    'Sup_Terreno': sup_terreno,
                    'Sup_Construida': sup_construida,

                    # CARACTERÍSTICAS AVANZADAS EXTRAÍDAS
                    'Estado_Operativo': caract_avanzadas.get('estado_operativo'),
                    'Habitaciones_Extraidas': caract_avanzadas.get('habitaciones_extraidas'),
                    'Banos_Extraidos': caract_avanzadas.get('banos_extraidos'),
                    'Garajes_Extraidos': caract_avanzadas.get('garajes_extraidos'),
                    'Superficie_Extraida': caract_avanzadas.get('superficie_extraida'),
                    'Agente_Extraido': caract_avanzadas.get('agente_extraido'),
                    'Contacto_Agente_Extraido': caract_avanzadas.get('contacto_agente'),
                    'Zona_Extraida': caract_avanzadas.get('zona_extraida'),
                    'Tipo_Propiedad_Extraido': caract_avanzadas.get('tipo_propiedad'),
                    'Amenities_Extraidos': caract_avanzadas.get('amenities_extraidos', []),
                    'Informacion_Adicional': caract_avanzadas.get('informacion_adicional'),

                    # Metadatos de extracción
                    'Metodo_Extraccion': caract_avanzadas.get('metodo_extraccion'),
                    'Proveedor_LLM': caract_avanzadas.get('proveedor_llm'),
                    'Modelo_LLM': caract_avanzadas.get('modelo_llm'),
                    'Fallback_Usado': caract_avanzadas.get('fallback_usado', False),

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

    def process_servicios_file(self, df: pd.DataFrame, filename: str) -> pd.DataFrame:
        """
        Procesar archivo de servicios urbanos
        """
        self.log(f"Procesando {len(df)} filas de servicios")

        processed_rows = []

        for idx, row in df.iterrows():
            self.stats['total_filas'] += 1

            try:
                # Extraer datos de servicios (estructura específica de GUIA URBANA)
                # La estructura varía según el tipo de fila
                uv = self.clean_text(row.get('Unnamed: 0', ''))
                mz = self.clean_text(row.get('Unnamed: 1', ''))
                subsistema = self.clean_text(row.get('Unnamed: 2', ''))
                nivel = self.clean_text(row.get('Unnamed: 3', ''))
                google_map = self.clean_text(row.get('Unnamed: 4', ''))

                # Coordenadas en diferentes posiciones según el formato
                x_raw = row.get('Unnamed: 15')  # Columna X
                y_raw = row.get('Unnamed: 16')  # Columna Y

                # Intentar diferentes formatos de coordenadas
                lat_procesada, lng_procesada = None, None
                coords_debug = []

                # Método 1: Coordenadas separadas en columnas X,Y (formato UV)
                try:
                    if pd.notna(x_raw) and pd.notna(y_raw) and x_raw != 0 and y_raw != 0:
                        lng_temp = float(x_raw)
                        lat_temp = float(y_raw)

                        coords_debug.append(f"Método1 - X:{lng_temp}, Y:{lat_temp}")

                        # Normalizar por si están multiplicadas
                        lat_norm, lng_norm, norm_msg = self.normalize_coordinates(lat_temp, lng_temp)
                        if lat_norm and lng_norm:
                            lat_procesada, lng_procesada = lat_norm, lng_norm
                            coords_debug.append(norm_msg)
                except (ValueError, TypeError):
                    coords_debug.append("Método1 - Error en conversión X,Y")

                # Método 2: Coordenadas en formato texto en columna GOOGLE_MAP
                if not lat_procesada and not lng_procesada:
                    coord_text = str(google_map).strip()
                    if ',' in coord_text and coord_text.startswith('-'):
                        try:
                            coord_parts = coord_text.strip('"').split(',')
                            if len(coord_parts) == 2:
                                lat_temp = float(coord_parts[0].strip())
                                lng_temp = float(coord_parts[1].strip())

                                coords_debug.append(f"Método2 - Texto:{lat_temp},{lng_temp}")

                                # Validar rango directamente (ya vienen normalizadas)
                                if (SANTA_CRUZ_BOUNDS['lat_min'] <= lat_temp <= SANTA_CRUZ_BOUNDS['lat_max'] and
                                    SANTA_CRUZ_BOUNDS['lng_min'] <= lng_temp <= SANTA_CRUZ_BOUNDS['lng_max']):
                                    lat_procesada, lng_procesada = lat_temp, lng_temp
                                    coords_debug.append("Método2 - Coordenadas válidas")
                        except (ValueError, TypeError):
                            coords_debug.append("Método2 - Error parseando texto")

                # Método 3: Buscar coordenadas en cualquier columna que contenga texto con formato
                if not lat_procesada and not lng_procesada:
                    for col_idx, (col_name, col_value) in enumerate(row.items()):
                        if pd.notna(col_value) and isinstance(col_value, str):
                            if ',' in col_value and '-' in col_value:
                                # Patrón: "-17.7346834076377,-63.1437665345452"
                                try:
                                    coord_parts = col_value.strip('"').split(',')
                                    if len(coord_parts) == 2:
                                        lat_temp = float(coord_parts[0].strip())
                                        lng_temp = float(coord_parts[1].strip())

                                        if (SANTA_CRUZ_BOUNDS['lat_min'] <= lat_temp <= SANTA_CRUZ_BOUNDS['lat_max'] and
                                            SANTA_CRUZ_BOUNDS['lng_min'] <= lng_temp <= SANTA_CRUZ_BOUNDS['lng_max']):
                                            lat_procesada, lng_procesada = lat_temp, lng_temp
                                            coords_debug.append(f"Método3 - Encontrado en {col_name}")
                                            break
                                except (ValueError, TypeError):
                                    continue

                # Validar coordenadas finales
                coords_valid, coords_msg = self.validate_coordinates(lat_procesada, lng_procesada)
                if not coords_valid:
                    coords_debug.append(coords_msg)

                estado = "OK"
                observaciones = []

                if not coords_valid:
                    estado = "SIN_COORDENADAS"
                    observaciones.extend(coords_debug)
                    self.stats['coordenadas_invalidas'] += 1
                else:
                    self.stats['coordenadas_validas'] += 1

                # Determinar nombre del servicio (prioridad según tipo)
                if uv and uv.startswith('UV-'):
                    nombre = uv
                    tipo = "Unidad Vecinal"
                elif subsistema:
                    nombre = subsistema
                    tipo = mz or "Servicio Municipal"
                else:
                    nombre = f"Servicio Fila {idx}"
                    tipo = "No clasificado"

                # Verificar datos completos
                datos_completos = bool(nombre and (lat_procesada and lng_procesada))

                if not datos_completos:
                    if estado == "OK":
                        estado = "DATOS_INCOMPLETOS"
                    observaciones.append("Datos incompletos")
                    self.stats['datos_incompletos'] += 1
                else:
                    self.stats['datos_completos'] += 1

                processed_row = {
                    # Datos originales preservados
                    'Original_UV': uv,
                    'Original_MZ': mz,
                    'Original_Subsistema': subsistema,
                    'Original_Nivel': nivel,
                    'Original_GoogleMap': google_map,
                    'Original_X': x_raw,
                    'Original_Y': y_raw,

                    # Datos procesados
                    'Nombre_Limpio': nombre,
                    'Tipo_Limpio': tipo,
                    'Latitud_Procesada': lat_procesada,
                    'Longitud_Procesada': lng_procesada,

                    # Estado
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

        return pd.DataFrame(processed_rows)

    def generate_excel_output(self, df_processed: pd.DataFrame, filename: str, output_path: str) -> bool:
        """
        Generar archivo Excel intermedio con múltiples hojas
        """
        try:
            base_name = os.path.splitext(os.path.basename(filename))[0]
            output_file = os.path.join(output_path, f"{base_name}_intermedio.xlsx")

            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Hoja 1: Resumen de procesamiento
                summary_data = {
                    'Métrica': [
                        'Total filas',
                        'Filas procesadas',
                        'Errores',
                        'Coordenadas válidas',
                        'Coordenadas inválidas',
                        'Datos completos',
                        'Datos incompletos'
                    ],
                    'Cantidad': [
                        self.stats['total_filas'],
                        self.stats['filas_procesadas'],
                        self.stats['errores'],
                        self.stats['coordenadas_validas'],
                        self.stats['coordenadas_invalidas'],
                        self.stats['datos_completos'],
                        self.stats['datos_incompletos']
                    ]
                }

                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='RESUMEN_PROCESAMIENTO', index=False)

                # Hoja 2: Datos procesados
                df_processed.to_excel(writer, sheet_name='DATOS_PROCESADOS', index=False)

                # Hoja 3: Errores (si hay)
                if self.errors:
                    errors_df = pd.DataFrame({'Error': self.errors})
                    errors_df.to_excel(writer, sheet_name='ERRORES', index=False)

            self.log(f"Archivo Excel generado: {output_file}")
            return True

        except Exception as e:
            self.log(f"Error generando Excel: {e}")
            return False

    def generate_csv_samples(self, df_processed: pd.DataFrame, filename: str, output_path: str) -> bool:
        """
        Generar archivo CSV con muestras para validación manual
        """
        try:
            base_name = os.path.splitext(os.path.basename(filename))[0]
            csv_file = os.path.join(output_path, f"{base_name}_muestras.csv")

            # Tomar primeras 10 filas para muestra
            sample_df = df_processed.head(10)

            # Seleccionar columnas importantes para revisión (incluyendo características avanzadas)
            important_cols = [
                'Original_Titulo', 'Original_Precio', 'Precio_Normalizado',
                'Latitud_Procesada', 'Longitud_Procesada', 'ESTADO', 'OBSERVACIONES',
                'Estado_Operativo', 'Habitaciones_Extraidas', 'Banos_Extraidos',
                'Garajes_Extraidos', 'Superficie_Extraida', 'Zona_Extraida',
                'Tipo_Propiedad_Extraido', 'Agente_Extraido', 'Metodo_Extraccion'
            ]

            # Filtrar solo columnas existentes
            available_cols = [col for col in important_cols if col in sample_df.columns]

            if available_cols:
                sample_df[available_cols].to_csv(csv_file, index=False, encoding='utf-8')
                self.log(f"CSV de muestras generado: {csv_file}")
                return True
            else:
                self.log("No se encontraron columnas importantes para muestra")
                return False

        except Exception as e:
            self.log(f"Error generando CSV de muestras: {e}")
            return False

    def generate_json_report(self, filename: str, output_path: str) -> bool:
        """
        Generar reporte JSON con métricas detalladas
        """
        try:
            base_name = os.path.splitext(os.path.basename(filename))[0]
            report_file = os.path.join(output_path, f"{base_name}_reporte.json")

            # Calcular porcentajes
            total = self.stats['total_filas']
            if total > 0:
                porcentajes = {
                    'coordenadas_validas_pct': (self.stats['coordenadas_validas'] / total) * 100,
                    'datos_completos_pct': (self.stats['datos_completos'] / total) * 100,
                    'errores_pct': (self.stats['errores'] / total) * 100
                }
            else:
                porcentajes = {
                    'coordenadas_validas_pct': 0,
                    'datos_completos_pct': 0,
                    'errores_pct': 0
                }

            report = {
                'archivo_origen': filename,
                'fecha_procesamiento': datetime.now().isoformat(),
                'estadisticas': self.stats,
                'porcentajes': porcentajes,
                'errores_detalle': self.errors,
                'metricas_calidad': {
                    'coordenadas_validas': porcentajes['coordenadas_validas_pct'],
                    'datos_completos': porcentajes['datos_completos_pct'],
                    'tasa_errores': porcentajes['errores_pct']
                },
                'estado_calidad': self._determine_quality_level(porcentajes)
            }

            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            self.log(f"Reporte JSON generado: {report_file}")
            return True

        except Exception as e:
            self.log(f"Error generando reporte JSON: {e}")
            return False

    def _determine_quality_level(self, porcentajes: Dict[str, float]) -> str:
        """
        Determinar nivel de calidad basado en métricas
        """
        coords_ok = porcentajes['coordenadas_validas_pct']
        datos_ok = porcentajes['datos_completos_pct']
        errores_ok = porcentajes['errores_pct']

        if coords_ok >= 95 and datos_ok >= 90 and errores_ok <= 1:
            return "EXCELENTE"
        elif coords_ok >= 80 and datos_ok >= 70 and errores_ok <= 5:
            return "ACEPTABLE"
        elif coords_ok >= 50 and datos_ok >= 50 and errores_ok <= 20:
            return "NECESITA_REVISION"
        else:
            return "PROBLEMAS_GRAVES"

    def process_file(self, input_path: str, output_path: str, file_type: str = 'propiedades') -> bool:
        """
        Procesar archivo individual
        """
        if not os.path.exists(input_path):
            self.log(f"ERROR: Archivo no encontrado: {input_path}")
            return False

        filename = os.path.basename(input_path)
        self.log(f"Iniciando procesamiento de: {filename}")

        try:
            # Leer archivo Excel
            df = pd.read_excel(input_path)
            self.log(f"Archivo leído: {len(df)} filas, {len(df.columns)} columnas")

            # Procesar según tipo
            if file_type == 'servicios':
                df_processed = self.process_servicios_file(df, filename)
            else:
                df_processed = self.process_propiedades_file(df, filename)

            # Detectar duplicados
            if len(df_processed) > 0:
                duplicate_indices = self.detect_duplicates(df_processed)
                self.stats['duplicados'] = len(duplicate_indices)
                if duplicate_indices:
                    self.log(f"Duplicados detectados: {len(duplicate_indices)}")

            # Generar archivos de salida
            excel_success = self.generate_excel_output(df_processed, filename, output_path)
            json_success = self.generate_json_report(filename, output_path)
            csv_success = self.generate_csv_samples(df_processed, filename, output_path)

            if excel_success and json_success and csv_success:
                self.log(f"Procesamiento completado exitosamente")
                return True
            else:
                self.log("Error generando archivos de salida")
                return False

        except Exception as e:
            self.log(f"Error procesando archivo: {e}")
            return False


def process_all_files_in_directory(input_dir: str, output_path: str, file_type: str = 'propiedades', verbose: bool = False) -> bool:
    """
    Procesa TODOS los archivos RAW en un directorio automáticamente
    """
    import glob

    # Buscar todos los archivos Excel en el directorio
    pattern = os.path.join(input_dir, "**", "*.xlsx")
    all_files = glob.glob(pattern, recursive=True)

    if not all_files:
        print(f"ERROR: No se encontraron archivos .xlsx en {input_dir}")
        return False

    print(f"ARCHIVOS ENCONTRADOS: {len(all_files)}")
    for f in all_files:
        print(f"  - {os.path.basename(f)}")

    # Crear directorio de salida
    os.makedirs(output_path, exist_ok=True)

    # Procesar cada archivo
    total_stats = {
        'archivos_procesados': 0,
        'archivos_exitosos': 0,
        'archivos_fallidos': 0,
        'total_propiedades': 0
    }

    for i, input_file in enumerate(all_files, 1):
        filename = os.path.basename(input_file)
        print(f"\n{'='*60}")
        print(f"PROCESANDO ARCHIVO {i}/{len(all_files)}: {filename}")
        print(f"{'='*60}")

        # Crear validator para cada archivo
        validator = RawDataValidator(verbose=verbose)

        # Procesar archivo
        success = validator.process_file(input_file, output_path, file_type)

        # Actualizar estadísticas
        total_stats['archivos_procesados'] += 1
        total_stats['total_propiedades'] += validator.stats['total_filas']

        if success:
            total_stats['archivos_exitosos'] += 1
            print(f"✅ {filename}: {validator.stats['total_filas']} propiedades procesadas")
        else:
            total_stats['archivos_fallidos'] += 1
            print(f"❌ {filename}: ERROR EN PROCESAMIENTO")

    # Resumen final
    print(f"\n{'='*60}")
    print("RESUMEN FINAL DEL PROCESAMIENTO")
    print(f"{'='*60}")
    print(f"Archivos procesados: {total_stats['archivos_procesados']}")
    print(f"Archivos exitosos: {total_stats['archivos_exitosos']}")
    print(f"Archivos fallidos: {total_stats['archivos_fallidos']}")
    print(f"Total propiedades procesadas: {total_stats['total_propiedades']}")
    print(f"Archivos generados en: {output_path}")
    print(f"{'='*60}")

    return total_stats['archivos_fallidos'] == 0


def main():
    """
    Función principal
    """
    parser = argparse.ArgumentParser(description='Validar archivos raw y generar intermedios para revisión')
    parser.add_argument('--input', help='Ruta al archivo raw de entrada (individual)')
    parser.add_argument('--input-dir', help='Directorio con archivos RAW para procesar TODOS automáticamente')
    parser.add_argument('--output', default='data/processed', help='Directorio de salida')
    parser.add_argument('--type', choices=['propiedades', 'servicios'], default='propiedades', help='Tipo de archivo')
    parser.add_argument('--verbose', action='store_true', help='Mostrar detalles del procesamiento')

    args = parser.parse_args()

    # Validar parámetros
    if not args.input and not args.input_dir:
        print("ERROR: Debes especificar --input (archivo individual) o --input-dir (procesar todos)")
        return False

    if args.input and args.input_dir:
        print("ERROR: No puedes especificar ambos --input y --input-dir")
        return False

    # Determinar modo de operación
    if args.input:
        # Modo individual (original)
        if not os.path.exists(args.input):
            print(f"ERROR: Archivo no encontrado: {args.input}")
            return False

        # Crear directorio de salida
        os.makedirs(args.output, exist_ok=True)

        # Iniciar procesamiento
        validator = RawDataValidator(verbose=args.verbose)
        success = validator.process_file(args.input, args.output, args.type)

        if success:
            print(f"PROCESAMIENTO EXITOSO")
            print(f"Archivos generados en: {args.output}")
            print(f"Revisa los archivos intermedios para validación humana")
        else:
            print("PROCESAMIENTO FALLIDO")

        return success

    else:
        # Modo batch (procesar todos los archivos)
        return process_all_files_in_directory(args.input_dir, args.output, args.type, args.verbose)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)