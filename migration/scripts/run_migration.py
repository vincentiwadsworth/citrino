#!/usr/bin/env python3
"""
Script principal para ejecutar la migración completa a PostgreSQL + PostGIS
Orquesta todo el proceso desde la configuración inicial hasta la validación final
"""

import os
import sys
import subprocess
import psycopg2
import logging
from pathlib import Path
from datetime import datetime
import json

# Agregar directorios al path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from etl_propiedades_from_excel import ETLPropiedades
from etl_servicios_from_excel import ETLServicios

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration/logs/migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MigrationManager:
    """Manager principal para la migración completa"""

    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'citrino'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password'),
            'port': os.getenv('DB_PORT', '5432')
        }
        self.start_time = datetime.now()

        # Crear directorios necesarios
        os.makedirs('migration/logs', exist_ok=True)
        os.makedirs('migration/backups', exist_ok=True)

    def verificar_prerequisitos(self):
        """Verificar que todos los prerequisitos están cumplidos"""
        logger.info("Verificando prerequisitos...")

        # Verificar variables de entorno
        if not os.getenv('DB_PASSWORD'):
            logger.warning("DB_PASSWORD no está configurada, usando valor por defecto")

        # Verificar archivos de datos
        archivos_requeridos = [
            'data/raw/relevamiento',
            'data/raw/guia/GUIA URBANA.xlsx',
            'migration/database/02_create_schema_postgis.sql'
        ]

        for archivo in archivos_requeridos:
            if not os.path.exists(archivo):
                raise FileNotFoundError(f"Archivo requerido no encontrado: {archivo}")

        # Verificar que existan archivos Excel
        archivos_excel = list(Path('data/raw/relevamiento').glob("*.xlsx"))
        if not archivos_excel:
            raise FileNotFoundError("No se encontraron archivos Excel en data/raw/relevamiento")

        logger.info(f"Encontrados {len(archivos_excel)} archivos Excel")

        # Verificar conexión a PostgreSQL
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=self.db_config['host'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                port=self.db_config['port']
            )
            conn.close()
            logger.info("Conexión a PostgreSQL verificada")
        except Exception as e:
            logger.error(f"No se puede conectar a PostgreSQL: {e}")
            raise

        logger.info("Todos los prerequisitos verificados ")

    def crear_esquema_db(self):
        """Crear esquema completo de base de datos"""
        logger.info("Creando esquema de base de datos...")

        schema_file = 'migration/database/02_create_schema_postgis.sql'

        try:
            # Ejecutar script SQL con Docker
            cmd = [
                'docker', 'exec', '-i', 'citrino-postgres-new',
                'psql', '-U', self.db_config['user'], '-d', self.db_config['database'],
                '-f', f'/tmp/schema.sql'
            ]

            # Copiar schema file al contenedor
            copy_cmd = [
                'docker', 'cp', schema_file, 'citrino-postgres-new:/tmp/schema.sql'
            ]
            subprocess.run(copy_cmd, check=True)

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("Esquema creado exitosamente ")
            else:
                logger.error(f"Error creando esquema: {result.stderr}")
                raise Exception(f"Error ejecutando script SQL: {result.stderr}")

        except Exception as e:
            logger.error(f"Error creando esquema de base de datos: {e}")
            raise

    def ejecutar_etl_propiedades(self):
        """Ejecutar ETL de propiedades"""
        logger.info("Iniciando ETL de propiedades...")

        try:
            etl = ETLPropiedades(self.db_config)
            etl.conectar_db()

            directorio_excel = 'data/raw/relevamiento'
            propiedades = etl.procesar_todos_los_archivos(directorio_excel)

            etl.cerrar_conexion()

            logger.info(f"ETL de propiedades completado: {len(propiedades)} propiedades migradas ")
            return propiedades

        except Exception as e:
            logger.error(f"Error en ETL de propiedades: {e}")
            raise

    def ejecutar_etl_servicios(self):
        """Ejecutar ETL de servicios"""
        logger.info("Iniciando ETL de servicios urbanos...")

        try:
            etl = ETLServicios(self.db_config)
            etl.conectar_db()

            archivo_excel = 'data/raw/guia/GUIA URBANA.xlsx'
            servicios = etl.procesar_servicios_completos(archivo_excel)

            etl.cerrar_conexion()

            logger.info(f"ETL de servicios completado: {len(servicios)} servicios migrados ")
            return servicios

        except Exception as e:
            logger.error(f"Error en ETL de servicios: {e}")
            raise

    def validar_migracion(self):
        """Validar que la migración se completó correctamente"""
        logger.info("Validando migración...")

        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # Verificar tablas principales
            cursor.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            tablas = [row[0] for row in cursor.fetchall()]

            tablas_esperadas = ['agentes', 'propiedades', 'servicios', 'categorias_servicios']
            for tabla in tablas_esperadas:
                if tabla not in tablas:
                    raise Exception(f"Falta tabla requerida: {tabla}")

            # Verificar datos
            cursor.execute("SELECT COUNT(*) FROM propiedades")
            total_propiedades = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM servicios")
            total_servicios = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM agentes")
            total_agentes = cursor.fetchone()[0]

            # Verificar coordenadas PostGIS
            cursor.execute("SELECT COUNT(*) FROM propiedades WHERE coordenadas IS NOT NULL")
            propiedades_con_coordenadas = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM servicios WHERE coordenadas IS NOT NULL")
            servicios_con_coordenadas = cursor.fetchone()[0]

            # Verificar índices espaciales
            cursor.execute("""
                SELECT indexname FROM pg_indexes
                WHERE tablename IN ('propiedades', 'servicios')
                AND indexdef LIKE '%GIST%'
            """)
            indices_espaciales = [row[0] for row in cursor.fetchall()]

            cursor.close()
            conn.close()

            # Mostrar resultados
            logger.info("=== RESULTADOS DE LA MIGRACIÓN ===")
            logger.info(f"Propiedades migradas: {total_propiedades}")
            logger.info(f"Propiedades con coordenadas: {propiedades_con_coordenadas} ({propiedades_con_coordenadas/total_propiedades*100:.1f}%)")
            logger.info(f"Servicios migrados: {total_servicios}")
            logger.info(f"Servicios con coordenadas: {servicios_con_coordenadas} ({servicios_con_coordenadas/total_servicios*100:.1f}%)")
            logger.info(f"Agentes únicos: {total_agentes}")
            logger.info(f"Índices espaciales creados: {len(indices_espaciales)}")

            # Validaciones mínimas
            if total_propiedades == 0:
                raise Exception("No se migraron propiedades")

            if total_servicios == 0:
                raise Exception("No se migraron servicios")

            if propiedades_con_coordenadas == 0:
                logger.warning("No hay propiedades con coordenadas válidas")

            if len(indices_espaciales) < 2:
                raise Exception("No se crearon suficientes índices espaciales")

            logger.info("Migración validada exitosamente ")

            # Guardar reporte
            reporte = {
                'fecha': datetime.now().isoformat(),
                'duracion_segundos': (datetime.now() - self.start_time).total_seconds(),
                'estadisticas': {
                    'propiedades_total': total_propiedades,
                    'propiedades_con_coordenadas': propiedades_con_coordenadas,
                    'servicios_total': total_servicios,
                    'servicios_con_coordenadas': servicios_con_coordenadas,
                    'agentes_total': total_agentes,
                    'indices_espaciales': len(indices_espaciales)
                },
                'tablas_creadas': tablas,
                'indices_espaciales': indices_espaciales
            }

            with open('migration/logs/migration_report.json', 'w') as f:
                json.dump(reporte, f, indent=2, ensure_ascii=False)

            return reporte

        except Exception as e:
            logger.error(f"Error en validación: {e}")
            raise

    def ejecutar_pruebas_rendimiento(self):
        """Ejecutar pruebas básicas de rendimiento"""
        logger.info("Ejecutando pruebas de rendimiento...")

        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            import time

            # Prueba 1: Búsqueda por zona
            start_time = time.time()
            cursor.execute("""
                SELECT COUNT(*) FROM propiedades
                WHERE zona = 'Equipetrol'
            """)
            count_zona = cursor.fetchone()[0]
            tiempo_zona = time.time() - start_time

            # Prueba 2: Búsqueda espacial (servicios cerca de propiedad)
            start_time = time.time()
            cursor.execute("""
                SELECT COUNT(*) FROM servicios s
                WHERE EXISTS (
                    SELECT 1 FROM propiedades p
                    WHERE p.coordenadas IS NOT NULL
                    AND ST_DWithin(p.coordenadas, s.coordenadas, 500)
                    LIMIT 1
                )
            """)
            count_cercanos = cursor.fetchone()[0]
            tiempo_espacial = time.time() - start_time

            # Prueba 3: Query compleja con JOIN espacial
            start_time = time.time()
            cursor.execute("""
                SELECT p.zona, COUNT(*) as total_propiedades,
                       AVG(p.precio_usd) as precio_promedio
                FROM propiedades p
                WHERE p.coordenadas IS NOT NULL
                AND EXISTS (
                    SELECT 1 FROM servicios s
                    WHERE s.categoria_principal = 'educacion'
                    AND ST_DWithin(p.coordenadas, s.coordenadas, 1000)
                )
                GROUP BY p.zona
                ORDER BY total_propiedades DESC
                LIMIT 5
            """)
            resultados_query = cursor.fetchall()
            tiempo_query = time.time() - start_time

            cursor.close()
            conn.close()

            logger.info("=== PRUEBAS DE RENDIMIENTO ===")
            logger.info(f"Búsqueda por zona: {count_zona} resultados en {tiempo_zona:.3f}s")
            logger.info(f"Búsqueda espacial: {count_cercanos} servicios cercanos en {tiempo_espacial:.3f}s")
            logger.info(f"Query compleja: {len(resultados_query)} zonas en {tiempo_query:.3f}s")

            # Evaluar rendimiento
            if tiempo_zona > 0.1:
                logger.warning(f"Búsqueda por zona lenta: {tiempo_zona:.3f}s")

            if tiempo_espacial > 1.0:
                logger.warning(f"Búsqueda espacial lenta: {tiempo_espacial:.3f}s")

            if tiempo_query > 2.0:
                logger.warning(f"Query compleja lenta: {tiempo_query:.3f}s")

            if tiempo_zona < 0.05 and tiempo_espacial < 0.5 and tiempo_query < 1.0:
                logger.info("Rendimiento excelente ")
            else:
                logger.info("Rendimiento aceptable ")

        except Exception as e:
            logger.error(f"Error en pruebas de rendimiento: {e}")
            raise

    def ejecutar_migracion_completa(self):
        """Ejecutar todo el proceso de migración"""
        logger.info("Iniciando migración completa a PostgreSQL + PostGIS")
        logger.info(f"Tiempo de inicio: {self.start_time}")

        try:
            # Paso 1: Verificar prerequisitos
            self.verificar_prerequisitos()

            # Paso 2: Crear esquema
            self.crear_esquema_db()

            # Paso 3: Migrar datos
            propiedades = self.ejecutar_etl_propiedades()
            servicios = self.ejecutar_etl_servicios()

            # Paso 4: Validar migración
            reporte = self.validar_migracion()

            # Paso 5: Probar rendimiento
            self.ejecutar_pruebas_rendimiento()

            # Resumen final
            duracion_total = (datetime.now() - self.start_time).total_seconds()
            logger.info("=== MIGRACIÓN COMPLETADA EXITOSAMENTE ===")
            logger.info(f"Duración total: {duracion_total:.1f} segundos")
            logger.info(f"Propiedades: {len(propiedades)}")
            logger.info(f"Servicios: {len(servicios)}")
            logger.info(f"Reporte guardado en: migration/logs/migration_report.json")

            return reporte

        except Exception as e:
            logger.error(f"Error en migración: {e}")
            raise

def main():
    """Función principal"""
    manager = MigrationManager()

    try:
        reporte = manager.ejecutar_migracion_completa()
        logger.info("¡Migración completada exitosamente!")
        return 0

    except Exception as e:
        logger.error(f"Migración fallida: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())