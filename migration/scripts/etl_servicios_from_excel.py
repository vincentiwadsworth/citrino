#!/usr/bin/env python3
"""
ETL para migrar servicios urbanos desde Excel a PostgreSQL + PostGIS
Procesa el archivo Excel de servicios urbanos y los migra con coordenadas PostGIS
"""

import os
import pandas as pd
import sys
from datetime import datetime
import logging
from typing import Dict, List, Optional, Tuple
import re

# Agregar path para importar configuración de base de datos
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database_config import create_connection

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/etl_servicios.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ETLServicios:
    """Clase principal para ETL de servicios urbanos a PostgreSQL"""

    def __init__(self, db_config: Dict = None):
        self.db_config = db_config
        self.conn = None

    def conectar_db(self):
        """Establecer conexión con PostgreSQL usando Docker wrapper"""
        try:
            self.conn = create_connection(self.db_config)
            logger.info("Conexión exitosa a PostgreSQL via Docker")
        except Exception as e:
            logger.error(f"Error conectando a PostgreSQL: {e}")
            raise

    def procesar_coordenadas_desde_uv(self, ubicacion: Dict) -> Tuple[Optional[float], Optional[float]]:
        """Extraer coordenadas desde datos de UV/Manzana cuando no hay lat/lon directas"""
        if not ubicacion:
            return None, None

        # Intentar extraer coordenadas desde campos de ubicación
        coordenadas = ubicacion.get('coordenadas', {})
        if coordenadas and isinstance(coordenadas, dict):
            lat = coordenadas.get('lat')
            lon = coordenadas.get('lon')
            if lat and lon:
                try:
                    return float(lat), float(lon)
                except (ValueError, TypeError):
                    pass

        # Intentar desde UV (si tiene coordenadas implícitas)
        uv = ubicacion.get('uv', '')
        manzana = ubicacion.get('manzana', '')

        # Aquí se podría agregar lógica para mapear UV/Manzana a coordenadas
        # Por ahora, retornar None si no hay coordenadas directas

        return None, None

    def normalizar_categoria(self, categoria: str, subcategoria: str) -> str:
        """Normalizar categorías a valores estándar"""
        if not categoria:
            return 'otros'

        categoria_lower = categoria.lower()

        # Mapeo de categorías
        mapeo_categorias = {
            # Educación
            'educacion': 'educacion',
            'educación': 'educacion',
            'colegio': 'educacion',
            'escuela': 'educacion',
            'universidad': 'educacion',
            'instituto': 'educacion',

            # Salud
            'salud': 'salud',
            'hospital': 'salud',
            'clinica': 'salud',
            'clínica': 'salud',
            'farmacia': 'salud',
            'centro médico': 'salud',

            # Comercio
            'comercio': 'comercio',
            'tienda': 'comercio',
            'supermercado': 'comercio',
            'mercado': 'comercio',
            'negocio': 'comercio',

            # Transporte
            'transporte': 'transporte',
            'parada': 'transporte',
            'terminal': 'transporte',
            'buses': 'transporte',

            # Seguridad
            'seguridad': 'seguridad',
            'policía': 'seguridad',
            'policia': 'seguridad',
            'seguridad ciudadana': 'seguridad',

            # Recreación
            'recreacion': 'recreacion',
            'recreación': 'recreacion',
            'parque': 'recreacion',
            'plaza': 'recreacion',
            'deporte': 'recreacion',

            # Finanzas
            'finanzas': 'finanzas',
            'banco': 'finanzas',
            'cajero': 'finanzas',
            'atm': 'finanzas',

            # Gobierno
            'gobierno': 'gobierno',
            'municipal': 'gobierno',
            'oficina': 'gobierno',
            'gubernamental': 'gobierno'
        }

        # Buscar coincidencia exacta o parcial
        for clave, valor in mapeo_categorias.items():
            if clave in categoria_lower or categoria_lower in clave:
                return valor

        # Si no encuentra coincidencia, usar subcategoría
        if subcategoria:
            subcategoria_lower = subcategoria.lower()
            for clave, valor in mapeo_categorias.items():
                if clave in subcategoria_lower or subcategoria_lower in clave:
                    return valor

        return 'otros'

    def limpiar_direccion(self, direccion: str, ubicacion: Dict) -> Optional[str]:
        """Limpiar y construir dirección completa"""
        if not direccion and not ubicacion:
            return None

        partes_direccion = []

        # Agregar dirección principal
        if direccion and direccion.strip():
            partes_direccion.append(direccion.strip())

        # Agregar información de UV/Manzana
        if ubicacion:
            uv = ubicacion.get('uv', '').strip()
            manzana = ubicacion.get('manzana', '').strip()
            zona_uv = ubicacion.get('zona_uv', '').strip()

            if uv and uv.lower() not in ['nan', 'none', 'uv']:
                partes_direccion.append(f"UV {uv}")

            if manzana and manzana.lower() not in ['nan', 'none', 'mz']:
                partes_direccion.append(f"MZ {manzana}")

            if zona_uv and zona_uv.lower() not in ['nan', 'none']:
                partes_direccion.append(zona_uv)

        return ', '.join(partes_direccion) if partes_direccion else None

    def limpiar_datos_contacto(self, contacto: Dict) -> Dict[str, str]:
        """Limpiar y normalizar datos de contacto"""
        if not contacto:
            return {'telefono': '', 'horario': '', 'email': '', 'web': ''}

        telefono = str(contacto.get('telefono', '')).strip()
        horario = str(contacto.get('horario', '')).strip()
        email = str(contacto.get('email', '')).strip()
        web = str(contacto.get('web', '')).strip()

        # Limpiar valores nulos
        telefono = telefono if telefono.lower() not in ['nan', 'none', 'sin datos'] else ''
        horario = horario if horario.lower() not in ['nan', 'none', 'sin datos'] else ''
        email = email if email.lower() not in ['nan', 'none', 'sin datos'] else ''
        web = web if web.lower() not in ['nan', 'none', 'sin datos'] else ''

        return {
            'telefono': telefono,
            'horario': horario,
            'email': email,
            'web': web
        }

    def procesar_servicio(self, servicio: Dict) -> Optional[Dict]:
        """Procesar un servicio individual y extraer datos limpios"""
        try:
            # Datos básicos
            servicio_id = servicio.get('id', '')
            nombre = servicio.get('nombre', '').strip()

            if not nombre or nombre.lower() in ['nan', 'none', 'sin nombre']:
                return None

            # Procesar categorías
            categoria = self.normalizar_categoria(
                servicio.get('categoria_principal', ''),
                servicio.get('subcategoria', '')
            )

            # Procesar ubicación
            ubicacion = servicio.get('ubicacion', {})
            direccion = self.limpiar_direccion(
                ubicacion.get('direccion', ''),
                ubicacion
            )

            # Coordenadas
            lat, lon = self.procesar_coordenadas_desde_uv(ubicacion)

            # Datos de UV/Manzana
            uv = ubicacion.get('uv', '').strip()
            manzana = ubicacion.get('manzana', '').strip()
            zona_uv = ubicacion.get('zona_uv', '').strip()

            # Limpiar valores
            uv = uv if uv.lower() not in ['nan', 'none', 'uv'] else None
            manzana = manzana if manzana.lower() not in ['nan', 'none', 'mz'] else None
            zona_uv = zona_uv if zona_uv.lower() not in ['nan', 'none'] else None

            # Datos de contacto
            contacto = self.limpiar_datos_contacto(servicio.get('contacto', {}))

            # Metadatos
            metadatos = servicio.get('metadatos', {})
            coordenadas_validadas = metadatos.get('coordenadas_validadas', False)
            confidence_calificacion = metadatos.get('confidence_calificacion', 0.5)

            # Construir servicio limpio
            servicio_procesado = {
                'id_original': servicio_id,
                'nombre': nombre,
                'categoria_principal': categoria,
                'subcategoria': servicio.get('subcategoria', ''),
                'direccion': direccion,
                'latitud': lat,
                'longitud': lon,
                'uv': uv,
                'manzana': manzana,
                'zona_uv': zona_uv,
                'telefono': contacto['telefono'],
                'horario': contacto['horario'],
                'email': contacto['email'],
                'web': contacto['web'],
                'coordenadas_validadas': coordenadas_validadas and (lat is not None and lon is not None),
                'confidence_calificacion': confidence_calificacion
            }

            return servicio_procesado

        except Exception as e:
            logger.warning(f"Error procesando servicio {servicio.get('id', 'unknown')}: {e}")
            return None

    def cargar_servicios_desde_excel(self, archivo_excel: str) -> List[Dict]:
        """Cargar y procesar servicios desde archivo Excel"""
        logger.info(f"Cargando servicios desde: {archivo_excel}")

        try:
            # Leer Excel
            df = pd.read_excel(archivo_excel)
            logger.info(f"Leídas {len(df)} filas de {archivo_excel}")

            # Mapear columnas según estructura del Excel
            columnas_map = {
                # Columnas esperadas del Excel de servicios
                'Nombre': 'nombre',
                'Categoría': 'categoria_principal',
                'Subcategoría': 'subcategoria',
                'Dirección': 'direccion',
                'Teléfono': 'telefono',
                'Email': 'email',
                'Web': 'web',
                'UV': 'uv',
                'Manzana': 'manzana',
                'Zona UV': 'zona_uv',
                'Coordenada X': 'longitud',
                'Coordenada Y': 'latitud'
            }

            # Renombrar columnas si existen
            df = df.rename(columns=columnas_map)

            servicios_procesados = []
            for _, row in df.iterrows():
                # Crear estructura similar a la del JSON
                servicio = {
                    'id': f"servicio_excel_{len(servicios_procesados)}",
                    'nombre': row.get('nombre', ''),
                    'categoria_principal': row.get('categoria_principal', ''),
                    'subcategoria': row.get('subcategoria', ''),
                    'direccion': row.get('direccion', ''),
                    'telefono': row.get('telefono', ''),
                    'email': row.get('email', ''),
                    'web': row.get('web', ''),
                    'uv': row.get('uv', ''),
                    'manzana': row.get('manzana', ''),
                    'zona_uv': row.get('zona_uv', ''),
                    'latitud': row.get('latitud'),
                    'longitud': row.get('longitud')
                }

                # Procesar servicio
                servicio_procesado = self.procesar_servicio(servicio)
                if servicio_procesado:
                    servicios_procesados.append(servicio_procesado)

            logger.info(f"Procesados {len(servicios_procesados)} servicios válidos")

            # Estadísticas por categoría
            categorias_count = {}
            for servicio in servicios_procesados:
                cat = servicio['categoria_principal']
                categorias_count[cat] = categorias_count.get(cat, 0) + 1

            logger.info("Distribución por categoría:")
            for cat, count in sorted(categorias_count.items()):
                logger.info(f"  {cat}: {count} servicios")

            return servicios_procesados

        except Exception as e:
            logger.error(f"Error cargando archivo Excel: {e}")
            raise

    def insertar_servicios_batch(self, servicios: List[Dict], batch_size: int = 200):
        """Insertar servicios en batch para mejor rendimiento"""
        if not servicios:
            return

        logger.info(f"Insertando {len(servicios)} servicios en batches de {batch_size}")

        try:
            cursor = self.conn.cursor()

            for i in range(0, len(servicios), batch_size):
                batch = servicios[i:i + batch_size]

                # Preparar datos para inserción
                values = []
                for serv in batch:
                    values.append((
                        serv['nombre'],
                        serv['categoria_principal'],
                        serv['subcategoria'],
                        serv['direccion'],
                        serv['latitud'],
                        serv['longitud'],
                        serv['uv'],
                        serv['manzana'],
                        serv['zona_uv'],
                        serv['telefono'],
                        serv['horario'],
                        serv['email'],
                        serv['web'],
                        serv['coordenadas_validadas'],
                        serv['confidence_calificacion']
                    ))

                # Insertar batch individualmente (Docker wrapper no soporta execute_values)
                for value in values:
                    cursor.execute(
                        """
                        INSERT INTO servicios (
                            nombre, categoria_principal, subcategoria, direccion,
                            latitud, longitud, uv, manzana, zona_uv,
                            telefono, horario, email, web,
                            coordenadas_validadas, confidence_calificacion
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        value
                    )

                logger.info(f"Insertado batch {i//batch_size + 1}/{(len(servicios)-1)//batch_size + 1}")

            # Actualizar coordenadas PostGIS
            cursor.execute("SELECT actualizar_coordenadas_servicios()")
            actualizadas = cursor.fetchone()[0]
            logger.info(f"Actualizadas {actualizadas} coordenadas PostGIS para servicios")

            cursor.close()
            self.conn.commit()

        except Exception as e:
            logger.error(f"Error insertando servicios: {e}")
            self.conn.rollback()
            raise

    def analizar_calidad_datos(self):
        """Analizar calidad de los datos migrados"""
        try:
            cursor = self.conn.cursor()

            # Estadísticas generales
            cursor.execute("SELECT COUNT(*) FROM servicios")
            total_servicios = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM servicios WHERE coordenadas_validadas = true")
            con_coordenadas = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM servicios WHERE latitud IS NOT NULL AND longitud IS NOT NULL")
            con_coordenadas_numericas = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM servicios WHERE telefono IS NOT NULL AND telefono != ''")
            con_telefono = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM servicios WHERE email IS NOT NULL AND email != ''")
            con_email = cursor.fetchone()[0]

            # Distribución por categoría
            cursor.execute("""
                SELECT categoria_principal, COUNT(*) as count
                FROM servicios
                GROUP BY categoria_principal
                ORDER BY count DESC
            """)
            distribucion_categorias = cursor.fetchall()

            # Distribución por zona
            cursor.execute("""
                SELECT zona_uv, COUNT(*) as count
                FROM servicios
                WHERE zona_uv IS NOT NULL
                GROUP BY zona_uv
                ORDER BY count DESC
                LIMIT 10
            """)
            top_zonas = cursor.fetchall()

            cursor.close()

            logger.info("=== ANÁLISIS DE CALIDAD DE DATOS ===")
            logger.info(f"Total servicios: {total_servicios}")
            logger.info(f"Con coordenadas validadas: {con_coordenadas}")
            logger.info(f"Con coordenadas numéricas: {con_coordenadas_numericas}")
            logger.info(f"Con teléfono: {con_telefono}")
            logger.info(f"Con email: {con_email}")
            logger.info(f"Tasa de coordenadas: {con_coordenadas_numericas/total_servicios*100:.1f}%")

            logger.info("\nTop 10 categorías:")
            for cat, count in distribucion_categorias:
                logger.info(f"  {cat}: {count}")

            logger.info("\nTop 10 zonas:")
            for zona, count in top_zonas:
                logger.info(f"  {zona}: {count}")

        except Exception as e:
            logger.error(f"Error en análisis de calidad: {e}")

    def procesar_servicios_completos(self, archivo_excel: str):
        """Proceso completo de ETL para servicios"""
        logger.info("Iniciando ETL completo para servicios urbanos")

        # Cargar y procesar servicios
        servicios = self.cargar_servicios_desde_excel(archivo_excel)

        if servicios:
            # Insertar en base de datos
            self.insertar_servicios_batch(servicios)

            # Analizar calidad
            self.analizar_calidad_datos()

            logger.info("ETL de servicios completado exitosamente")
        else:
            logger.warning("No se encontraron servicios para procesar")

        return servicios

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
    etl = ETLServicios(db_config)

    try:
        # Conectar a base de datos
        etl.conectar_db()

        # Procesar servicios
        archivo_excel = 'data/raw/guia/GUIA URBANA.xlsx'
        servicios = etl.procesar_servicios_completos(archivo_excel)

    except Exception as e:
        logger.error(f"Error en ETL de servicios: {e}")
        raise
    finally:
        etl.cerrar_conexion()

if __name__ == "__main__":
    main()