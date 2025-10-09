#!/usr/bin/env python3
"""
Script para procesar datos de relevamiento de mercado inmobiliario.
Procesa archivos Excel de data/raw/ y genera una base de datos unificada.
"""

import pandas as pd
import json
import os
import glob
from datetime import datetime
from typing import List, Dict, Any
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProcesadorDatosRelevamiento:
    """Clase para procesar datos de relevamiento de mercado."""

    def __init__(self, raw_data_dir: str = "data/raw", output_dir: str = "data"):
        self.raw_data_dir = raw_data_dir
        self.output_dir = output_dir
        self.properties_data = []
        self.processed_files = []

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

            # Extraer fecha del nombre de archivo si está disponible
            fecha_relevamiento = self.extraer_fecha_desde_filename(filename)

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
                propiedad = self.procesar_propiedad(row, fecha_relevamiento, filename)
                if propiedad:
                    propiedades.append(propiedad)

            logger.info(f"Se procesaron {len(propiedades)} propiedades de {filename}")
            return propiedades

        except Exception as e:
            logger.error(f"Error procesando {filepath}: {str(e)}")
            return []

    def extraer_fecha_desde_filename(self, filename: str) -> str:
        """Extrae fecha del nombre del archivo si está en formato YYYY.MM.DD"""
        try:
            # Formato esperado: YYYY.MM.DD XX.xlsx
            partes = filename.split()
            if len(partes) >= 1 and '.' in partes[0]:
                fecha_str = partes[0]
                # Validar formato
                datetime.strptime(fecha_str, '%Y.%m.%d')
                return fecha_str
        except:
            pass
        return None

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

    def procesar_propiedad(self, row: pd.Series, fecha_relevamiento: str, source_file: str) -> Dict[str, Any]:
        """Procesa una fila de propiedad y la convierte al formato estándar."""
        try:
            # Extraer tipo de propiedad desde el título si no está disponible
            titulo = self.limpiar_texto(str(row.get('titulo', '')))
            tipo_propiedad = self.limpiar_texto(str(row.get('tipo_propiedad', '')))

            if not tipo_propiedad and titulo:
                tipo_propiedad = self.extraer_tipo_propiedad_desde_titulo(titulo)

            # Extraer datos básicos
            propiedad = {
                'id': f"{source_file}_{row.name}",
                'titulo': titulo,
                'tipo_propiedad': tipo_propiedad,
                'precio': self.limpiar_precio(row.get('precio')),
                'zona': self.limpiar_texto(str(row.get('zona', ''))),
                'direccion': self.limpiar_texto(str(row.get('direccion', ''))),
                'latitud': self.limpiar_coordenada(row.get('latitud')),
                'longitud': self.limpiar_coordenada(row.get('longitud')),
                'superficie': self.limpiar_numero(row.get('superficie')),
                'superficie_terreno': self.limpiar_numero(row.get('superficie_terreno')),
                'superficie_construida': self.limpiar_numero(row.get('superficie_construida')),
                'habitaciones': self.limpiar_numero(row.get('habitaciones')),
                'banos': self.limpiar_numero(row.get('banos')),
                'garajes': self.limpiar_numero(row.get('garajes')),
                'descripcion': self.limpiar_texto(str(row.get('descripcion', ''))),
                'fecha_relevamiento': fecha_relevamiento,
                'fuente': source_file,
                'url': self.limpiar_texto(str(row.get('url', ''))),
                'agente': self.limpiar_texto(str(row.get('agente', ''))),
                'telefono': self.limpiar_texto(str(row.get('telefono', ''))),
                'correo': self.limpiar_texto(str(row.get('correo', ''))),
                'detalles': self.limpiar_texto(str(row.get('detalles', ''))),
                'unidad_vecinal': self.extraer_uv(row),
                'manzana': self.extraer_manzana(row)
            }

            # Validar datos mínimos requeridos
            if not self.validar_propiedad(propiedad):
                return None

            return propiedad

        except Exception as e:
            logger.warning(f"Error procesando propiedad {row.name}: {e}")
            return None

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
        """Limpia y convierte a entero."""
        if pd.isna(numero):
            return None

        try:
            num_str = str(numero).replace(',', '').replace('.', '')
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