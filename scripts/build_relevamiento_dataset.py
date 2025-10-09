#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para procesar datos de relevamiento de mercado inmobiliario.
Procesa archivos Excel de data/raw/ y genera una base de datos unificada.

Formato de archivos: YYYY.MM.DD NN.xlsx
  - YYYY.MM.DD: Fecha de scraping
  - NN: Código de proveedor (01, 02, 03, etc.)
"""

import pandas as pd
import json
import os
import glob
import re
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging

# Agregar path para importar extractor de zonas y parser LLM
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
try:
    from zonas_extractor import ZonasExtractor
    ZONAS_EXTRACTOR_DISPONIBLE = True
except ImportError:
    ZONAS_EXTRACTOR_DISPONIBLE = False
    logging.warning("ZonasExtractor no disponible, zonas no serán extraídas")

try:
    from description_parser import DescriptionParser
    DESCRIPTION_PARSER_DISPONIBLE = True
except ImportError:
    DESCRIPTION_PARSER_DISPONIBLE = False
    logging.warning("DescriptionParser no disponible, extracción LLM desactivada")

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProcesadorDatosRelevamiento:
    """Clase para procesar datos de relevamiento de mercado."""

    def __init__(self, raw_data_dir: str = "data/raw", output_dir: str = "data", enable_llm: bool = True):
        self.raw_data_dir = raw_data_dir
        self.output_dir = output_dir
        self.properties_data = []
        self.processed_files = []
        self.enable_llm = enable_llm
        
        # Inicializar extractor de zonas si está disponible
        self.zonas_extractor = ZonasExtractor() if ZONAS_EXTRACTOR_DISPONIBLE else None
        
        # Inicializar parser LLM si está disponible y habilitado
        self.description_parser = None
        if DESCRIPTION_PARSER_DISPONIBLE and enable_llm:
            try:
                self.description_parser = DescriptionParser()
                logger.info("Parser LLM inicializado correctamente")
            except Exception as e:
                logger.warning(f"No se pudo inicializar parser LLM: {e}")
        
        # Patrón para extraer fecha y proveedor del nombre de archivo
        # Formato: YYYY.MM.DD NN.xlsx
        self.filename_pattern = re.compile(r'(\d{4}\.\d{2}\.\d{2})\s+(\d{2})\.xlsx')

    def encontrar_archivos_excel(self) -> List[str]:
        """Encuentra todos los archivos Excel en el directorio raw."""
        pattern = os.path.join(self.raw_data_dir, "*.xlsx")
        files = glob.glob(pattern)
        logger.info(f"Se encontraron {len(files)} archivos Excel")
        return sorted(files)

    def procesar_archivo(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Procesa un archivo Excel de relevamiento.

        Args:
            filepath: Ruta al archivo Excel

        Returns:
            Lista de propiedades procesadas
        """
        try:
            filename = os.path.basename(filepath)
            logger.info(f"Procesando archivo: {filename}")

            # Extraer fecha y código de proveedor del nombre de archivo
            fecha_relevamiento, codigo_proveedor = self.extraer_fecha_y_proveedor_desde_filename(filename)
            
            if not fecha_relevamiento:
                logger.warning(f"No se pudo extraer fecha/proveedor de {filename}")
            else:
                logger.info(f"  Fecha: {fecha_relevamiento}, Proveedor: {codigo_proveedor}")

            # Leer Excel (intentar diferentes hojas)
            df = self.leer_excel(filepath)
            if df is None or df.empty:
                logger.warning(f"No se pudieron leer datos de {filename}")
                return []

            # Estandarizar columnas
            df = self.estandarizar_columnas(df)

            # Procesar cada propiedad
            propiedades = []
            for index, row in df.iterrows():
                propiedad = self.procesar_propiedad(
                    row, 
                    fecha_relevamiento, 
                    codigo_proveedor,
                    filename
                )
                if propiedad:
                    propiedades.append(propiedad)

            logger.info(f"Se procesaron {len(propiedades)} propiedades de {filename}")
            return propiedades

        except Exception as e:
            logger.error(f"Error procesando {filepath}: {str(e)}")
            return []

    def extraer_fecha_y_proveedor_desde_filename(self, filename: str) -> Tuple[Optional[str], Optional[str]]:
        """Extrae fecha y código de proveedor del nombre del archivo.
        
        Formato esperado: YYYY.MM.DD NN.xlsx
        - YYYY.MM.DD: Fecha de scraping
        - NN: Código de proveedor (01, 02, 03, etc.)
        
        Returns:
            Tuple (fecha_str, codigo_proveedor) o (None, None) si no se puede extraer
        """
        try:
            match = self.filename_pattern.match(filename)
            if match:
                fecha_str = match.group(1)
                codigo_proveedor = match.group(2)
                
                # Validar formato de fecha
                datetime.strptime(fecha_str, '%Y.%m.%d')
                
                return fecha_str, codigo_proveedor
        except Exception as e:
            logger.debug(f"No se pudo extraer fecha/proveedor de {filename}: {e}")
            
        return None, None
    
    def extraer_fecha_desde_filename(self, filename: str) -> str:
        """Extrae solo la fecha (mantener compatibilidad)."""
        fecha, _ = self.extraer_fecha_y_proveedor_desde_filename(filename)
        return fecha

    def leer_excel(self, filepath: str) -> pd.DataFrame:
        """Intenta leer el archivo Excel con diferentes configuraciones."""
        try:
            # Intentar leer primera hoja
            df = pd.read_excel(filepath, engine='openpyxl')
            return df
        except Exception as e:
            logger.warning(f"No se pudo leer {filepath} directamente: {e}")

        try:
            # Intentar con todas las hojas
            excel_file = pd.ExcelFile(filepath, engine='openpyxl')
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(filepath, sheet_name=sheet_name)
                if not df.empty:
                    logger.info(f"Se usó la hoja: {sheet_name}")
                    return df
        except Exception as e:
            logger.error(f"No se pudo leer ninguna hoja de {filepath}: {e}")

        return None

    def estandarizar_columnas(self, df: pd.DataFrame) -> pd.DataFrame:
        """Estandariza nombres de columnas comunes."""
        # Mapeo de columnas comunes a nombres estándar
        column_mapping = {
            # Columnas de precio
            'precio': 'precio',
            'precio_usd': 'precio',
            'price': 'precio',
            'valor': 'precio',
            'monto': 'precio',
            'precio_venta': 'precio',

            # Columnas de tipo (extraído del título)
            'título': 'titulo',
            'titulo': 'titulo',
            'tipo': 'tipo_propiedad',
            'tipo_propiedad': 'tipo_propiedad',
            'property_type': 'tipo_propiedad',
            'categoria': 'tipo_propiedad',

            # Columnas de ubicación
            'zona': 'zona',
            'barrio': 'zona',
            'ubicacion': 'zona',
            'location': 'zona',
            'sector': 'zona',
            'características_-_ubicación': 'ubicacion_caracteristicas',

            # Columnas de dirección
            'direccion': 'direccion',
            'address': 'direccion',
            'ubicacion_exacta': 'direccion',

            # Columnas de coordenadas
            'latitud': 'latitud',
            'latitude': 'latitud',
            'lat': 'latitud',
            'longitud': 'longitud',
            'longitude': 'longitud',
            'lng': 'longitud',
            'lon': 'longitud',

            # Columnas de superficie
            'superficie': 'superficie',
            'area': 'superficie',
            'm2': 'superficie',
            'metros_cuadrados': 'superficie',
            'surface': 'superficie',
            'sup._terreno': 'superficie_terreno',
            'sup._construida': 'superficie_construida',

            # Columnas de habitaciones
            'habitaciones': 'habitaciones',
            'habitacion': 'habitaciones',
            'dormitorios': 'habitaciones',
            'bedrooms': 'habitaciones',
            'rooms': 'habitaciones',

            # Columnas de baños
            'baños': 'banos',
            'banos': 'banos',
            'bathrooms': 'banos',
            'baths': 'banos',

            # Columnas adicionales
            'garajes': 'garajes',
            'url': 'url',
            'agente': 'agente',
            'teléfono': 'telefono',
            'correo': 'correo',
            'detalles': 'detalles',
            'características_-_servicios': 'servicios_caracteristicas',
            'características_-_interior': 'interior_caracteristicas',
            'características_-_exterior': 'exterior_caracteristicas',
            'características_-_general': 'general_caracteristicas',

            # Columnas de descripción
            'descripcion': 'descripcion',
            'descripción': 'descripcion',  # Con acento
            'description': 'descripcion',
            'observaciones': 'descripcion'
        }

        # Convertir nombres de columnas a minúsculas y sin espacios
        df.columns = [col.lower().strip().replace(' ', '_') for col in df.columns]

        # Renombrar columnas según el mapeo
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df = df.rename(columns={old_col: new_col})

        return df

    def procesar_propiedad(self, row: pd.Series, fecha_relevamiento: str, codigo_proveedor: str, source_file: str) -> Dict[str, Any]:
        """Procesa una fila de propiedad y la convierte al formato estándar."""
        try:
            # Extraer tipo de propiedad desde el título si no está disponible
            titulo = self.limpiar_texto(str(row.get('titulo', '')))
            tipo_propiedad = self.limpiar_texto(str(row.get('tipo_propiedad', '')))

            if not tipo_propiedad and titulo:
                tipo_propiedad = self.extraer_tipo_propiedad_desde_titulo(titulo)

            # Extraer zona inicial (puede contener fuente de datos)
            zona_original = self.limpiar_texto(str(row.get('zona', '')))
            descripcion = self.limpiar_texto(str(row.get('descripcion', '')))
            
            # Separar fuente de datos vs zona geográfica
            fuente_datos = None
            zona_geografica = ''
            
            # Si zona está en mayúsculas o parece ser nombre de proveedor, es fuente
            if zona_original and (zona_original.isupper() or zona_original in ['ULTRACASAS', 'INFOCASAS']):
                fuente_datos = zona_original
            else:
                zona_geografica = zona_original
            
            # Extraer zona geográfica real usando extractor
            if self.zonas_extractor and not zona_geografica:
                # Intentar desde título primero
                zona_extraida = self.zonas_extractor.extraer_zona_principal(titulo)
                if not zona_extraida:
                    # Si no, desde descripción
                    zona_extraida = self.zonas_extractor.extraer_zona_principal(descripcion)
                
                if zona_extraida:
                    zona_geografica = zona_extraida
            
            # Extraer datos básicos
            propiedad = {
                'id': f"{source_file}_{row.name}",
                'titulo': titulo,
                'tipo_propiedad': tipo_propiedad,
                'precio': self.limpiar_precio(row.get('precio')),
                'zona': zona_geografica,  # Zona geográfica real
                'direccion': self.limpiar_texto(str(row.get('direccion', ''))),
                'latitud': self.limpiar_coordenada(row.get('latitud')),
                'longitud': self.limpiar_coordenada(row.get('longitud')),
                'superficie': self.limpiar_numero(row.get('superficie')),
                'superficie_terreno': self.limpiar_numero(row.get('superficie_terreno')),
                'superficie_construida': self.limpiar_numero(row.get('superficie_construida')),
                'habitaciones': self.limpiar_numero(row.get('habitaciones')),
                'banos': self.limpiar_numero(row.get('banos')),
                'garajes': self.limpiar_numero(row.get('garajes')),
                'descripcion': descripcion,
                'fecha_scraping': fecha_relevamiento,  # Renombrado para claridad
                'codigo_proveedor': codigo_proveedor,  # Nuevo: código del proveedor
                'fuente_datos': fuente_datos,  # Nuevo: nombre del proveedor si aplica
                'archivo_origen': source_file,  # Renombrado para claridad
                'url': self.limpiar_texto(str(row.get('url', ''))),
                'agente': self.limpiar_texto(str(row.get('agente', ''))),
                'telefono': self.limpiar_texto(str(row.get('telefono', ''))),
                'correo': self.limpiar_texto(str(row.get('correo', ''))),
                'detalles': self.limpiar_texto(str(row.get('detalles', ''))),
                'unidad_vecinal': self.extraer_uv(row),
                'manzana': self.extraer_manzana(row)
            }
            
            # Agregar referencias de ubicación si el extractor está disponible
            if self.zonas_extractor and zona_geografica:
                texto_completo = f"{titulo} {descripcion}"
                referencias = self.zonas_extractor.extraer_referencias_ubicacion(texto_completo)
                if referencias['anillos'] or referencias['radiales']:
                    propiedad['referencias_ubicacion'] = referencias

            # Enriquecer con LLM si es proveedor 02 y hay descripción
            if codigo_proveedor == '02' and descripcion and self.description_parser:
                propiedad = self.enriquecer_con_llm(propiedad, descripcion, titulo)

            # Validar datos mínimos requeridos
            if not self.validar_propiedad(propiedad):
                return None

            return propiedad

        except Exception as e:
            logger.warning(f"Error procesando propiedad {row.name}: {e}")
            return None

    def enriquecer_con_llm(self, propiedad: Dict[str, Any], descripcion: str, titulo: str = "") -> Dict[str, Any]:
        """
        Enriquece los datos de una propiedad usando LLM para extraer de la descripción.

        Args:
            propiedad: Diccionario con los datos básicos de la propiedad
            descripcion: Texto de la descripción
            titulo: Título de la propiedad

        Returns:
            Diccionario de propiedad enriquecido
        """
        # Para proveedor 02, siempre intentar enriquecer si hay descripción
        # porque sabemos que los datos están en texto libre

        try:
            logger.info(f"Enriqueciendo propiedad {propiedad['id']} con LLM...")
            extracted_data = self.description_parser.extract_from_description(descripcion, titulo)

            # Actualizar solo los campos que están vacíos
            if not propiedad.get('precio') and extracted_data.get('precio'):
                propiedad['precio'] = extracted_data['precio']
                propiedad['moneda'] = extracted_data.get('moneda', 'USD')
                propiedad['precio_origen'] = 'llm_extraction'

            if not propiedad.get('habitaciones') and extracted_data.get('habitaciones'):
                propiedad['habitaciones'] = extracted_data['habitaciones']

            if not propiedad.get('banos') and extracted_data.get('banos'):
                propiedad['banos'] = extracted_data['banos']

            if not propiedad.get('superficie') and extracted_data.get('superficie'):
                propiedad['superficie'] = extracted_data['superficie']

            if not propiedad.get('superficie_terreno') and extracted_data.get('superficie_terreno'):
                propiedad['superficie_terreno'] = extracted_data['superficie_terreno']

            if not propiedad.get('superficie_construida') and extracted_data.get('superficie_construida'):
                propiedad['superficie_construida'] = extracted_data['superficie_construida']

            if not propiedad.get('zona') and extracted_data.get('zona'):
                propiedad['zona'] = extracted_data['zona']
                propiedad['zona_origen'] = 'llm_extraction'

            if not propiedad.get('tipo_propiedad') and extracted_data.get('tipo_propiedad'):
                propiedad['tipo_propiedad'] = extracted_data['tipo_propiedad']

            if extracted_data.get('caracteristicas'):
                propiedad['caracteristicas_llm'] = extracted_data['caracteristicas']

            logger.info(f"Propiedad {propiedad['id']} enriquecida exitosamente")

        except Exception as e:
            logger.warning(f"Error enriqueciendo con LLM: {e}")

        return propiedad

    def limpiar_texto(self, texto: str) -> str:
        """Limpia y normaliza texto."""
        if pd.isna(texto) or texto == 'nan':
            return ''
        return str(texto).strip()

    def limpiar_precio(self, precio) -> float:
        """Limpia y convierte precio a número."""
        if pd.isna(precio):
            return None

        try:
            # Remover símbolos y texto
            precio_str = str(precio)
            precio_str = precio_str.replace('$', '').replace('USD', '').replace('US$', '')
            precio_str = precio_str.replace(',', '').replace('.', '').replace(' ', '')

            # Convertir a número
            precio_num = float(precio_str)
            return precio_num
        except:
            return None

    def limpiar_coordenada(self, coord) -> float:
        """Limpia y valida coordenada."""
        if pd.isna(coord):
            return None

        try:
            coord_num = float(coord)
            # Validar rangos para Santa Cruz, Bolivia
            # Latitud: entre -18.0 y -17.0
            # Longitud: entre -63.5 y -63.0
            if not (-18.0 <= coord_num <= -17.0) and not (-63.5 <= coord_num <= -63.0):
                return None
            return coord_num
        except:
            return None

    def limpiar_numero(self, numero) -> int:
        """Limpia y convierte a entero.
        
        CORRECCIÓN DE BUG: Ahora maneja correctamente decimales.
        Ejemplo: '3.5' → 3 (trunca), no 35 como antes.
        """
        if pd.isna(numero):
            return None

        try:
            # Remover separadores de miles
            num_str = str(numero).replace(',', '')
            
            # Convertir a float primero (para manejar decimales), luego a int
            return int(float(num_str))
        except:
            return None

    def extraer_uv(self, row: pd.Series) -> str:
        """Extrae información de Unidad Vecinal de la propiedad."""
        # Buscar en diferentes campos posibles
        uv_fields = ['uv', 'unidad_vecinal', 'sector_uv', 'unidad_vecinal_uv']

        for field in uv_fields:
            if field in row and not pd.isna(row[field]):
                return str(row[field]).strip()

        return ''

    def extraer_manzana(self, row: pd.Series) -> str:
        """Extrae información de Manzana de la propiedad."""
        # Buscar en diferentes campos posibles
        mz_fields = ['mz', 'manzana', 'manzano', 'lote']

        for field in mz_fields:
            if field in row and not pd.isna(row[field]):
                return str(row[field]).strip()

        return ''

    def extraer_tipo_propiedad_desde_titulo(self, titulo: str) -> str:
        """Extrae el tipo de propiedad desde el título."""
        if not titulo:
            return ''

        titulo_lower = titulo.lower()

        # Palabras clave para diferentes tipos de propiedades
        tipos_propiedad = {
            'casa': ['casa', 'chalet', 'casa familiar', 'casa de campo', 'residencia'],
            'departamento': ['departamento', 'apartamento', 'depto', 'apto', 'monoambiente', 'studio', 'suite'],
            'penthouse': ['penthouse', 'ph', 'dúplex', 'duplex', 'ático', 'attic'],
            'terreno': ['terreno', 'lote', 'solar', 'parcela'],
            'oficina': ['oficina', 'local comercial', 'local', 'consultorio'],
            'galpón': ['galpón', 'galpon', 'depósito', 'bodega', 'almacén'],
            'edificio': ['edificio', 'torre', 'conjunto', 'complejo']
        }

        # Buscar palabras clave en el título
        for tipo, palabras in tipos_propiedad.items():
            for palabra in palabras:
                if palabra in titulo_lower:
                    return tipo

        # Si no se encuentra ningún tipo específico, intentar inferir
        if any(palabra in titulo_lower for palabra in ['venta', 'alquiler', 'alquilar']):
            return 'propiedad'  # Genérico pero válido

        return ''

    def validar_propiedad(self, propiedad: Dict[str, Any]) -> bool:
        """Valida que la propiedad tenga datos mínimos requeridos."""
        # Requerir al menos precio o coordenadas
        if not propiedad.get('precio') and not (propiedad.get('latitud') and propiedad.get('longitud')):
            return False

        # El tipo de propiedad se puede extraer del título, así que no es obligatorio aquí
        return True

    def procesar_todos_los_archivos(self) -> List[Dict[str, Any]]:
        """Procesa todos los archivos Excel del directorio raw."""
        archivos = self.encontrar_archivos_excel()

        todas_las_propiedades = []

        for archivo in archivos:
            propiedades = self.procesar_archivo(archivo)
            todas_las_propiedades.extend(propiedades)
            self.processed_files.append(archivo)

        # Eliminar duplicados basados en coordenadas o dirección
        propiedades_unicas = self.eliminar_duplicados(todas_las_propiedades)

        logger.info(f"Proceso completado: {len(propiedades_unicas)} propiedades únicas de {len(todas_las_propiedades)} totales")

        return propiedades_unicas

    def eliminar_duplicados(self, propiedades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Elimina propiedades duplicadas basadas en coordenadas o dirección."""
        vistos = set()
        propiedades_unicas = []

        for prop in propiedades:
            # Crear clave única basada en coordenadas o dirección
            if prop.get('latitud') and prop.get('longitud'):
                clave = (round(prop['latitud'], 6), round(prop['longitud'], 6))
            elif prop.get('direccion'):
                clave = prop['direccion'].lower().strip()
            else:
                clave = prop['id']

            if clave not in vistos:
                vistos.add(clave)
                propiedades_unicas.append(prop)

        return propiedades_unicas

    def guardar_datos(self, propiedades: List[Dict[str, Any]]) -> str:
        """Guarda los datos procesados en formato JSON."""
        output_file = os.path.join(self.output_dir, 'base_datos_relevamiento.json')

        # Guardar caché de LLM si existe
        if self.description_parser:
            self.description_parser.save_cache()
            stats = self.description_parser.get_stats()
            logger.info(f"Estadísticas LLM: {stats}")

        # Crear metadata
        metadata = {
            'fecha_procesamiento': datetime.now().isoformat(),
            'total_propiedades': len(propiedades),
            'archivos_procesados': self.processed_files,
            'descripcion': 'Base de datos de propiedades de relevamiento de mercado'
        }

        # Estructura final
        datos_completos = {
            'metadata': metadata,
            'propiedades': propiedades
        }

        # Guardar en JSON
        os.makedirs(self.output_dir, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(datos_completos, f, ensure_ascii=False, indent=2)

        logger.info(f"Datos guardados en: {output_file}")
        return output_file


def main():
    """Función principal del script."""
    logger.info("Iniciando procesamiento de datos de relevamiento...")

    # Crear procesador
    procesador = ProcesadorDatosRelevamiento()

    # Procesar todos los archivos
    propiedades = procesador.procesar_todos_los_archivos()

    if propiedades:
        # Guardar resultados
        output_file = procesador.guardar_datos(propiedades)
        logger.info(f"Procesamiento completado exitosamente: {len(propiedades)} propiedades procesadas")
        logger.info(f"Archivo de salida: {output_file}")
    else:
        logger.warning("No se procesaron propiedades. Revisar los archivos de entrada.")


if __name__ == "__main__":
    main()