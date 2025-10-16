#!/usr/bin/env python3
"""
VALIDACIÓN DE ARCHIVOS RAW A INTERMEDIOS
=========================================

Procesa UN archivo raw a la vez generando:
1. Archivo Excel intermedio con columnas originales + procesadas
2. Reporte JSON con métricas de calidad
3. Archivo listo para revisión humana por equipo Citrino

Uso:
    python scripts/validation/validate_raw_to_intermediate.py --input "data/raw/relevamiento/2025.08.15 05.xlsx"

Author: Claude Code
Date: 2025-10-15
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
warnings.filterwarnings('ignore')

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
            'duplicados': 0
        }
        self.errors = []

    def log(self, message: str):
        """Imprimir mensaje si verbose está activado"""
        if self.verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

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
        Extraer precio numérico de texto
        """
        if pd.isna(price_value) or price_value is None:
            return 0.0, "Sin precio"

        try:
            price_str = str(price_value)
            # Limpiar símbolos y texto
            price_str = price_str.replace('$', '').replace('USD', '').replace('Usd', '').replace(',', '').strip()

            # Convertir a número
            price_num = float(price_str)
            return price_num, "Precio extraído"

        except (ValueError, TypeError):
            return 0.0, f"Error extrayendo precio: {price_value}"

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

            try:
                # Extraer datos básicos
                titulo_original = self.clean_text(row.get('Título') or row.get('Titulo') or row.get('titulo', ''))
                precio_original = row.get('Precio', 0)
                descripcion_original = self.clean_text(row.get('Descripción') or row.get('Descripcion', ''))
                agente_original = self.clean_text(row.get('Agente', ''))
                telefono_original = self.clean_text(row.get('Teléfono') or row.get('Telefono', ''))

                # Procesar datos
                precio_normalizado, precio_msg = self.extract_price(precio_original)
                titulo_limpio = titulo_original
                descripcion_limpia = descripcion_original

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

                # Crear fila procesada
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

                    # Características
                    'Habitaciones': habitaciones,
                    'Baños': baños,
                    'Garajes': garajes,
                    'Sup_Terreno': sup_terreno,
                    'Sup_Construida': sup_construida,

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

            # Seleccionar columnas importantes para revisión
            important_cols = [
                'Original_Titulo', 'Original_Precio', 'Precio_Normalizado',
                'Latitud_Procesada', 'Longitud_Procesada', 'ESTADO', 'OBSERVACIONES'
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


def main():
    """
    Función principal
    """
    parser = argparse.ArgumentParser(description='Validar archivo raw y generar intermedio para revisión')
    parser.add_argument('--input', required=True, help='Ruta al archivo raw de entrada')
    parser.add_argument('--output', default='data/processed', help='Directorio de salida')
    parser.add_argument('--type', choices=['propiedades', 'servicios'], default='propiedades', help='Tipo de archivo')
    parser.add_argument('--verbose', action='store_true', help='Mostrar detalles del procesamiento')

    args = parser.parse_args()

    # Verificar archivo de entrada
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


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)