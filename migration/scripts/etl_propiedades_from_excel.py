#!/usr/bin/env python3
"""
ETL completo para migrar propiedades desde archivos Excel a PostgreSQL + PostGIS
Procesa todos los archivos Excel de relevamiento y los migra a la base de datos
"""

import os
import pandas as pd
import numpy as np
import sys
from datetime import datetime
import json
import logging
from typing import Dict, List, Tuple, Optional
import re
from pathlib import Path

# Agregar path para importar configuración de base de datos
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database_config import create_connection

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/etl_propiedades.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ETLPropiedades:
    """Clase principal para ETL de propiedades desde Excel a PostgreSQL"""

    def __init__(self, db_config: Dict = None):
        self.db_config = db_config
        self.conn = None
        self.agentes_cache = {}  # Cache para deduplicación de agentes
        self.processed_urls = set()  # Evitar duplicados

    def conectar_db(self):
        """Establecer conexión con PostgreSQL usando Docker wrapper"""
        try:
            self.conn = create_connection(self.db_config)
            logger.info("Conexión exitosa a PostgreSQL via Docker")
        except Exception as e:
            logger.error(f"Error conectando a PostgreSQL: {e}")
            raise

    def limpiar_precio(self, precio: str) -> Optional[float]:
        """Limpiar y normalizar precios"""
        if pd.isna(precio) or precio is None:
            return None

        precio_str = str(precio).strip()

        # Extraer números
        numeros = re.findall(r'[0-9,]+', precio_str)
        if not numeros:
            return None

        # Tomar el primer número encontrado y limpiar
        precio_limpio = numeros[0].replace(',', '')

        try:
            return float(precio_limpio)
        except ValueError:
            logger.warning(f"No se pudo convertir precio: {precio}")
            return None

    def limpiar_superficie(self, sup: str) -> Optional[float]:
        """Limpiar valores de superficie"""
        if pd.isna(sup) or sup is None:
            return None

        sup_str = str(sup).strip().upper()

        # Extraer números
        numeros = re.findall(r'[0-9,]+', sup_str)
        if not numeros:
            return None

        sup_limpia = numeros[0].replace(',', '')

        try:
            return float(sup_limpia)
        except ValueError:
            return None

    def limpiar_coordenadas(self, lat: any, lon: any) -> Tuple[Optional[float], Optional[float]]:
        """Validar y limpiar coordenadas"""
        if pd.isna(lat) or pd.isna(lon):
            return None, None

        try:
            lat_float = float(lat)
            lon_float = float(lon)

            # Validar rango Santa Cruz, Bolivia
            if -18.0 <= lat_float <= -17.5 and -63.5 <= lon_float <= -63.0:
                return lat_float, lon_float
            else:
                logger.warning(f"Coordenadas fuera de rango: {lat_float}, {lon_float}")
                return None, None

        except (ValueError, TypeError):
            return None, None

    def extraer_zona_desde_descripcion(self, descripcion: str, titulo: str) -> Optional[str]:
        """Extraer zona desde descripción o título usando patrones conocidos"""
        texto_completo = f"{titulo} {descripcion}".lower()

        # Zonas conocidas en Santa Cruz
        zonas_conocidas = [
            'equipetrol', 'santos', 'urbar', 'la paz', 'san pedro', 'las brisas',
            'lazareto', 'pampa de la islena', 'sauces', 'el porvenir',
            'villarroel', 'banegas', 'camiri', 'abrams', 'grigota',
            '1er anillo', '2do anillo', '3er anillo', '4to anillo', '5to anillo',
            '6to anillo', '7mo anillo', '8vo anillo',
            'norte', 'sur', 'este', 'oeste', 'centro'
        ]

        for zona in zonas_conocidas:
            if zona in texto_completo:
                # Capitalizar zona
                return zona.title()

        return None

    def procesar_agente(self, agente_data: Dict) -> Optional[int]:
        """Procesar o insertar agente con deduplicación"""
        if not agente_data or pd.isna(agente_data.get('nombre')):
            return None

        nombre = str(agente_data['nombre']).strip()
        if not nombre or nombre.lower() in ['nan', 'none', 'sin datos']:
            return None

        # Crear clave única para deduplicación
        telefono = str(agente_data.get('telefono', '')).strip()
        email = str(agente_data.get('email', '')).strip()

        # Limpiar valores
        telefono = telefono if telefono.lower() not in ['nan', 'none'] else ''
        email = email if email.lower() not in ['nan', 'none'] else ''

        cache_key = f"{nombre}_{telefono}_{email}"

        if cache_key in self.agentes_cache:
            return self.agentes_cache[cache_key]

        try:
            cursor = self.conn.cursor()

            # Buscar agente existente
            cursor.execute("""
                SELECT id FROM agentes
                WHERE LOWER(nombre) = LOWER(%s)
                AND COALESCE(telefono, '') = COALESCE(%s, '')
                AND COALESCE(email, '') = COALESCE(%s, '')
            """, (nombre, telefono, email))

            result = cursor.fetchone()

            if result:
                agente_id = result[0]
            else:
                # Insertar nuevo agente
                cursor.execute("""
                    INSERT INTO agentes (nombre, telefono, email, fuente_origen)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (nombre, telefono, email, 'excel_relevamiento'))

                agente_id = cursor.fetchone()[0]
                logger.info(f"Nuevo agente insertado: {nombre}")

            self.agentes_cache[cache_key] = agente_id
            cursor.close()

            return agente_id

        except Exception as e:
            logger.error(f"Error procesando agente {nombre}: {e}")
            return None

    def procesar_archivo_excel(self, archivo_path: str) -> List[Dict]:
        """Procesar un archivo Excel individual y extraer propiedades"""
        logger.info(f"Procesando archivo: {archivo_path}")

        try:
            # Leer Excel
            df = pd.read_excel(archivo_path)
            logger.info(f"Leídas {len(df)} filas de {archivo_path}")

            # Estandarizar columnas (manejar caracteres especiales)
            columnas_map = {
                'URL': 'url',
                'Título': 'titulo',
                'Precio': 'precio',
                'Descripción': 'descripcion',
                'Agente': 'agente_nombre',
                'Teléfono': 'agente_telefono',
                'Correo': 'agente_email',
                'Latitud': 'latitud',
                'Longitud': 'longitud',
                'Habitaciones': 'habitaciones',
                'Baños': 'banos',
                'Garajes': 'garajes',
                'Sup. Terreno': 'sup_terreno',
                'Sup. Construida': 'sup_construida',
                'Detalles': 'detalles',
                'Características - Ubicación': 'ubicacion_caracteristicas',
                'Características - Servicios': 'servicios_caracteristicas',
                'Características - Interior': 'interior_caracteristicas',
                'Características - Exterior': 'exterior_caracteristicas',
                'Características - General': 'general_caracteristicas'
            }

            # Renombrar columnas si existen
            df_renamed = df.rename(columns=columnas_map)

            propiedades = []
            duplicados = 0

            for _, row in df_renamed.iterrows():
                # Validar URL única
                url = row.get('url', '')
                if pd.isna(url) or not url or url in self.processed_urls:
                    duplicados += 1
                    continue

                self.processed_urls.add(url)

                # Procesar precio
                precio = self.limpiar_precio(row.get('precio'))
                if not precio:
                    logger.warning(f"Propiedad sin precio válido: {url}")
                    continue

                # Procesar coordenadas
                lat, lon = self.limpiar_coordenadas(row.get('latitud'), row.get('longitud'))

                # Extraer zona
                titulo = str(row.get('titulo', ''))
                descripcion = str(row.get('descripcion', ''))
                zona = self.extraer_zona_desde_descripcion(descripcion, titulo)

                # Procesar agente
                agente_data = {
                    'nombre': row.get('agente_nombre'),
                    'telefono': row.get('agente_telefono'),
                    'email': row.get('agente_email')
                }
                agente_id = self.procesar_agente(agente_data)

                # Limpiar valores numéricos
                habitaciones = int(row.get('habitaciones')) if not pd.isna(row.get('habitaciones')) and row.get('habitaciones') > 0 else None
                banos = int(row.get('banos')) if not pd.isna(row.get('banos')) and row.get('banos') > 0 else None
                garajes = int(row.get('garajes')) if not pd.isna(row.get('garajes')) and row.get('garajes') > 0 else None

                sup_terreno = self.limpiar_superficie(row.get('sup_terreno'))
                sup_construida = self.limpiar_superficie(row.get('sup_construida'))

                # Construir propiedad
                propiedad = {
                    'url': url,
                    'titulo': titulo,
                    'precio_usd': precio,
                    'descripcion': descripcion,
                    'habitaciones': habitaciones,
                    'banos': banos,
                    'garajes': garajes,
                    'sup_terreno': sup_terreno,
                    'sup_construida': sup_construida,
                    'detalles': str(row.get('detalles', '')),
                    'latitud': lat,
                    'longitud': lon,
                    'direccion': None,  # Se podría extraer de descripción en el futuro
                    'zona': zona,
                    'agente_id': agente_id,
                    'fuente_origen': os.path.basename(archivo_path),
                    'coordenadas_validadas': lat is not None and lon is not None
                }

                propiedades.append(propiedad)

            logger.info(f"Extraídas {len(propiedades)} propiedades válidas de {archivo_path}")
            if duplicados > 0:
                logger.info(f"Omitidas {duplicados} propiedades duplicadas")

            return propiedades

        except Exception as e:
            logger.error(f"Error procesando archivo {archivo_path}: {e}")
            return []

    def insertar_propiedades_batch(self, propiedades: List[Dict], batch_size: int = 100):
        """Insertar propiedades en batch para mejor rendimiento"""
        if not propiedades:
            return

        logger.info(f"Insertando {len(propiedades)} propiedades en batches de {batch_size}")

        try:
            cursor = self.conn.cursor()

            for i in range(0, len(propiedades), batch_size):
                batch = propiedades[i:i + batch_size]

                # Preparar datos para inserción
                values = []
                for prop in batch:
                    values.append((
                        prop['url'],
                        prop['titulo'],
                        prop['precio_usd'],
                        prop['descripcion'],
                        prop['habitaciones'],
                        prop['banos'],
                        prop['garajes'],
                        prop['sup_terreno'],
                        prop['sup_construida'],
                        prop['detalles'],
                        prop['latitud'],
                        prop['longitud'],
                        prop['direccion'],
                        prop['zona'],
                        prop['agente_id'],
                        prop['fuente_origen'],
                        prop['coordenadas_validadas']
                    ))

                # Insertar batch individualmente (Docker wrapper no soporta execute_values)
                for value in values:
                    cursor.execute(
                        """
                        INSERT INTO propiedades (
                            url, titulo, precio_usd, descripcion, habitaciones,
                            banos, garajes, sup_terreno, sup_construida, detalles,
                            latitud, longitud, direccion, zona, agente_id,
                            fuente_origen, coordenadas_validadas
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (url) DO UPDATE SET
                            titulo = EXCLUDED.titulo,
                            precio_usd = EXCLUDED.precio_usd,
                            descripcion = EXCLUDED.descripcion,
                            updated_at = CURRENT_TIMESTAMP
                        """,
                        value
                    )

                logger.info(f"Insertado batch {i//batch_size + 1}/{(len(propiedades)-1)//batch_size + 1}")

            # Actualizar coordenadas PostGIS
            cursor.execute("SELECT actualizar_coordenadas_propiedades()")
            actualizadas = cursor.fetchone()[0]
            logger.info(f"Actualizadas {actualizadas} coordenadas PostGIS")

            cursor.close()
            self.conn.commit()

        except Exception as e:
            logger.error(f"Error insertando propiedades: {e}")
            self.conn.rollback()
            raise

    def procesar_todos_los_archivos(self, directorio_excel: str):
        """Procesar todos los archivos Excel de propiedades"""
        logger.info(f"Buscando archivos Excel en: {directorio_excel}")

        # Encontrar todos los archivos Excel
        archivos_excel = list(Path(directorio_excel).glob("*.xlsx"))
        logger.info(f"Encontrados {len(archivos_excel)} archivos Excel")

        todas_propiedades = []

        for archivo in archivos_excel:
            propiedades_archivo = self.procesar_archivo_excel(str(archivo))
            todas_propiedades.extend(propiedades_archivo)

        logger.info(f"Total de propiedades extraídas: {len(todas_propiedades)}")

        # Insertar en base de datos
        if todas_propiedades:
            self.insertar_propiedades_batch(todas_propiedades)

            # Estadísticas finales
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM propiedades")
            total_db = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM propiedades WHERE coordenadas_validadas = true")
            con_coordenadas = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM agentes")
            total_agentes = cursor.fetchone()[0]

            cursor.close()

            logger.info(f"=== ESTADÍSTICAS FINALES ===")
            logger.info(f"Propiedades en BD: {total_db}")
            logger.info(f"Propiedades con coordenadas: {con_coordenadas}")
            logger.info(f"Agentes únicos: {total_agentes}")
            logger.info(f"Tasa de coordenadas válidas: {con_coordenadas/total_db*100:.1f}%")

        return todas_propiedades

    def cerrar_conexion(self):
        """Cerrar conexión a base de datos"""
        if self.conn:
            self.conn.close()

def main():
    """Función principal del ETL"""
    # Usar configuración desde database_config
    from database_config import load_database_config
    db_config = None  # Dejar que database_config cargue desde variables de entorno

    # Crear directorio de logs si no existe
    os.makedirs('logs', exist_ok=True)

    # Inicializar ETL
    etl = ETLPropiedades(db_config)

    try:
        # Conectar a base de datos
        etl.conectar_db()

        # Procesar todos los archivos
        directorio_excel = 'data/raw/relevamiento'
        propiedades = etl.procesar_todos_los_archivos(directorio_excel)

        logger.info("ETL de propiedades completado exitosamente")

    except Exception as e:
        logger.error(f"Error en ETL: {e}")
        raise
    finally:
        etl.cerrar_conexion()

if __name__ == "__main__":
    main()