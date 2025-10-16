#!/usr/bin/env python3
"""
Script de validación completa para la migración PostgreSQL + PostGIS
Ejecuta pruebas funcionales y de rendimiento para validar que todo funciona correctamente
"""

import os
import sys
import psycopg2
import psycopg2.extras
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple
import math

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration/logs/validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MigrationValidator:
    """Clase principal para validar la migración"""

    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.conn = None
        self.test_results = {}

    def conectar_db(self):
        """Establecer conexión con PostgreSQL"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.conn.autocommit = False
            logger.info("Conexión exitosa a PostgreSQL")
        except Exception as e:
            logger.error(f"Error conectando a PostgreSQL: {e}")
            raise

    def test_estructura_bd(self) -> Dict:
        """Validar estructura de base de datos"""
        logger.info("Validando estructura de base de datos...")

        results = {
            'tablas_esperadas': ['agentes', 'propiedades', 'servicios', 'categorias_servicios'],
            'tablas_encontradas': [],
            'indices_espaciales': [],
            'extensiones': [],
            'funciones': [],
            'vistas': []
        }

        try:
            cursor = self.conn.cursor()

            # Verificar tablas
            cursor.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            results['tablas_encontradas'] = [row[0] for row in cursor.fetchall()]

            # Verificar extensiones PostGIS
            cursor.execute("""
                SELECT extname FROM pg_extension WHERE extname IN ('postgis', 'postgis_topology')
            """)
            results['extensiones'] = [row[0] for row in cursor.fetchall()]

            # Verificar índices espaciales
            cursor.execute("""
                SELECT indexname, tablename FROM pg_indexes
                WHERE tablename IN ('propiedades', 'servicios')
                AND indexdef LIKE '%GIST%'
                ORDER BY tablename, indexname
            """)
            results['indices_espaciales'] = [
                {'nombre': row[0], 'tabla': row[1]}
                for row in cursor.fetchall()
            ]

            # Verificar funciones geográficas
            cursor.execute("""
                SELECT proname FROM pg_proc
                WHERE proname IN ('servicios_cercanos', 'actualizar_coordenadas_propiedades', 'actualizar_coordenadas_servicios')
            """)
            results['funciones'] = [row[0] for row in cursor.fetchall()]

            # Verificar vistas
            cursor.execute("""
                SELECT table_name FROM information_schema.views
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            results['vistas'] = [row[0] for row in cursor.fetchall()]

            cursor.close()

            # Validar resultados
            faltantes = set(results['tablas_esperadas']) - set(results['tablas_encontradas'])
            if faltantes:
                raise Exception(f"Faltan tablas: {faltantes}")

            if len(results['extensiones']) < 2:
                raise Exception(f"Faltan extensiones PostGIS: {results['extensiones']}")

            if len(results['indices_espaciales']) < 2:
                raise Exception("Faltan índices espaciales")

            logger.info("Estructura de BD validada ✓")
            return results

        except Exception as e:
            logger.error(f"Error validando estructura: {e}")
            raise

    def test_datos_basicos(self) -> Dict:
        """Validar datos básicos y calidad"""
        logger.info("Validando datos básicos...")

        results = {
            'propiedades_total': 0,
            'propiedades_con_coordenadas': 0,
            'propiedades_con_precio': 0,
            'servicios_total': 0,
            'servicios_con_coordenadas': 0,
            'agentes_total': 0,
            'categorias_servicios': 0
        }

        try:
            cursor = self.conn.cursor()

            # Propiedades
            cursor.execute("SELECT COUNT(*) FROM propiedades")
            results['propiedades_total'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM propiedades WHERE coordenadas IS NOT NULL")
            results['propiedades_con_coordenadas'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM propiedades WHERE precio_usd IS NOT NULL AND precio_usd > 0")
            results['propiedades_con_precio'] = cursor.fetchone()[0]

            # Servicios
            cursor.execute("SELECT COUNT(*) FROM servicios")
            results['servicios_total'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM servicios WHERE coordenadas IS NOT NULL")
            results['servicios_con_coordenadas'] = cursor.fetchone()[0]

            # Agentes
            cursor.execute("SELECT COUNT(*) FROM agentes")
            results['agentes_total'] = cursor.fetchone()[0]

            # Categorías
            cursor.execute("SELECT COUNT(*) FROM categorias_servicios")
            results['categorias_servicios'] = cursor.fetchone()[0]

            cursor.close()

            # Validaciones mínimas
            if results['propiedades_total'] == 0:
                raise Exception("No hay propiedades en la base de datos")

            if results['servicios_total'] == 0:
                raise Exception("No hay servicios en la base de datos")

            # Calcular porcentajes
            if results['propiedades_total'] > 0:
                results['porcentaje_coordenadas_propiedades'] = (
                    results['propiedades_con_coordenadas'] / results['propiedades_total'] * 100
                )
                results['porcentaje_precio_valido'] = (
                    results['propiedades_con_precio'] / results['propiedades_total'] * 100
                )

            if results['servicios_total'] > 0:
                results['porcentaje_coordenadas_servicios'] = (
                    results['servicios_con_coordenadas'] / results['servicios_total'] * 100
                )

            logger.info(f"Propiedades: {results['propiedades_total']} ({results.get('porcentaje_coordenadas_propiedades', 0):.1f}% con coordenadas)")
            logger.info(f"Servicios: {results['servicios_total']} ({results.get('porcentaje_coordenadas_servicios', 0):.1f}% con coordenadas)")
            logger.info("Datos básicos validados ✓")

            return results

        except Exception as e:
            logger.error(f"Error validando datos básicos: {e}")
            raise

    def test_consultas_espaciales(self) -> Dict:
        """Probar consultas espaciales"""
        logger.info("Probando consultas espaciales...")

        results = {
            'distancia_entre_puntos': [],
            'servicios_cerca_propiedad': [],
            'propiedades_en_radio': [],
            'tiempos_ejecucion': {}
        }

        try:
            cursor = self.conn.cursor()

            # Test 1: Calcular distancia entre dos propiedades
            start_time = time.time()
            cursor.execute("""
                SELECT
                    p1.titulo as propiedad1,
                    p2.titulo as propiedad2,
                    ST_Distance(p1.coordenadas, p2.coordenadas) as distancia_metros
                FROM propiedades p1, propiedades p2
                WHERE p1.coordenadas IS NOT NULL
                AND p2.coordenadas IS NOT NULL
                AND p1.id < p2.id
                LIMIT 5
            """)
            resultados_distancia = cursor.fetchall()
            results['tiempos_ejecucion']['distancia'] = time.time() - start_time
            results['distancia_entre_puntos'] = [
                {
                    'propiedad1': row[0],
                    'propiedad2': row[1],
                    'distancia_metros': float(row[2]) if row[2] else None
                }
                for row in resultados_distancia
            ]

            # Test 2: Servicios cerca de una propiedad (500m)
            start_time = time.time()
            cursor.execute("""
                SELECT
                    p.titulo as propiedad,
                    s.nombre as servicio,
                    s.categoria_principal,
                    ST_Distance(p.coordenadas, s.coordenadas) as distancia
                FROM propiedades p
                JOIN servicios s ON ST_DWithin(p.coordenadas, s.coordenadas, 500)
                WHERE p.coordenadas IS NOT NULL
                AND s.coordenadas IS NOT NULL
                ORDER BY p.id, distancia
                LIMIT 10
            """)
            resultados_cercanos = cursor.fetchall()
            results['tiempos_ejecucion']['cercanos'] = time.time() - start_time
            results['servicios_cerca_propiedad'] = [
                {
                    'propiedad': row[0],
                    'servicio': row[1],
                    'categoria': row[2],
                    'distancia': float(row[3]) if row[3] else None
                }
                for row in resultados_cercanos
            ]

            # Test 3: Propiedades en radio de servicios específicos
            start_time = time.time()
            cursor.execute("""
                SELECT
                    s.categoria_principal,
                    COUNT(DISTINCT p.id) as propiedades_cerca,
                    AVG(ST_Distance(p.coordenadas, s.coordenadas)) as distancia_promedio
                FROM servicios s
                JOIN propiedades p ON ST_DWithin(s.coordenadas, p.coordenadas, 1000)
                WHERE s.coordenadas IS NOT NULL
                AND p.coordenadas IS NOT NULL
                GROUP BY s.categoria_principal
                ORDER BY propiedades_cerca DESC
            """)
            resultados_radio = cursor.fetchall()
            results['tiempos_ejecucion']['radio'] = time.time() - start_time
            results['propiedades_en_radio'] = [
                {
                    'categoria': row[0],
                    'propiedades_cerca': row[1],
                    'distancia_promedio': float(row[2]) if row[2] else None
                }
                for row in resultados_radio
            ]

            cursor.close()

            # Validar resultados
            if not resultados_distancia:
                logger.warning("No se pudieron calcular distancias entre propiedades")

            if not resultados_cercanos:
                logger.warning("No se encontraron servicios cercanos a propiedades")

            logger.info(f"Tiempos de ejecución: {results['tiempos_ejecucion']}")
            logger.info("Consultas espaciales validadas ✓")

            return results

        except Exception as e:
            logger.error(f"Error en consultas espaciales: {e}")
            raise

    def test_rendimiento(self) -> Dict:
            """Probar rendimiento de consultas típicas"""
            logger.info("Probando rendimiento de consultas...")

            results = {
                'consultas': [],
                'umbral_maximo_segundos': 2.0
            }

            consultas_test = [
                {
                    'nombre': 'Búsqueda por zona',
                    'sql': """
                        SELECT COUNT(*) FROM propiedades
                        WHERE zona IS NOT NULL
                        GROUP BY zona
                        ORDER BY COUNT(*) DESC
                        LIMIT 5
                    """,
                    'umbral': 0.1
                },
                {
                    'nombre': 'Búsqueda por precio',
                    'sql': """
                        SELECT COUNT(*) FROM propiedades
                        WHERE precio_usd BETWEEN 100000 AND 300000
                    """,
                    'umbral': 0.1
                },
                {
                    'nombre': 'JOIN espacial complejo',
                    'sql': """
                        SELECT
                            p.zona,
                            COUNT(*) as total_propiedades,
                            COUNT(DISTINCT s.id) as servicios_cerca,
                            AVG(p.precio_usd) as precio_promedio
                        FROM propiedades p
                        LEFT JOIN servicios s ON ST_DWithin(p.coordenadas, s.coordenadas, 500)
                        WHERE p.coordenadas IS NOT NULL
                        AND p.zona IS NOT NULL
                        GROUP BY p.zona
                        HAVING COUNT(*) > 0
                        ORDER BY total_propiedades DESC
                        LIMIT 5
                    """,
                    'umbral': 1.0
                },
                {
                    'nombre': 'Búsqueda espacial por categoría',
                    'sql': """
                        SELECT COUNT(*) FROM propiedades p
                        WHERE EXISTS (
                            SELECT 1 FROM servicios s
                            WHERE s.categoria_principal = 'educacion'
                            AND ST_DWithin(p.coordenadas, s.coordenadas, 1000)
                        )
                        AND p.precio_usd < 250000
                    """,
                    'umbral': 0.5
                },
                {
                    'nombre': 'Análisis por agente',
                    'sql': """
                        SELECT
                            a.nombre,
                            COUNT(p.id) as total_propiedades,
                            AVG(p.precio_usd) as precio_promedio,
                            COUNT(DISTINCT p.zona) as zonas_distintas
                        FROM agentes a
                        LEFT JOIN propiedades p ON a.id = p.agente_id
                        GROUP BY a.id, a.nombre
                        HAVING COUNT(p.id) > 0
                        ORDER BY total_propiedades DESC
                        LIMIT 10
                    """,
                    'umbral': 0.3
                }
            ]

            try:
                cursor = self.conn.cursor()

                for consulta in consultas_test:
                    start_time = time.time()

                    cursor.execute(consulta['sql'])
                    resultados = cursor.fetchall()

                    tiempo_ejecucion = time.time() - start_time

                    resultado_test = {
                        'nombre': consulta['nombre'],
                        'tiempo_segundos': tiempo_ejecucion,
                        'resultados_obtenidos': len(resultados),
                        'umbral_segundos': consulta['umbral'],
                        'exitoso': tiempo_ejecucion <= consulta['umbral'],
                        'sql': consulta['sql'].strip()
                    }

                    results['consultas'].append(resultado_test)

                    if resultado_test['exitoso']:
                        logger.info(f"✓ {consulta['nombre']}: {tiempo_ejecucion:.3f}s ({len(resultados)} resultados)")
                    else:
                        logger.warning(f"⚠ {consulta['nombre']}: {tiempo_ejecucion:.3f}s (umbral: {consulta['umbral']}s)")

                cursor.close()

                # Evaluar rendimiento general
                consultas_exitosas = sum(1 for c in results['consultas'] if c['exitoso'])
                total_consultas = len(results['consultas'])
                porcentaje_exito = consultas_exitosas / total_consultas * 100

                results['porcentaje_exito'] = porcentaje_exito
                results['consultas_exitosas'] = consultas_exitosas
                results['total_consultas'] = total_consultas

                if porcentaje_exito >= 80:
                    logger.info(f"Rendimiento excelente: {porcentaje_exito:.1f}% consultas exitosas ✓")
                elif porcentaje_exito >= 60:
                    logger.info(f"Rendimiento aceptable: {porcentaje_exito:.1f}% consultas exitosas ⚠")
                else:
                    logger.warning(f"Rendimiento bajo: {porcentaje_exito:.1f}% consultas exitosas")

                return results

            except Exception as e:
                logger.error(f"Error en pruebas de rendimiento: {e}")
                raise

    def test_consistencia_datos(self) -> Dict:
        """Validar consistencia de datos"""
        logger.info("Validando consistencia de datos...")

        results = {
            'propiedades_sin_agente': 0,
            'servicios_sin_categoria': 0,
            'coordenadas_invalidas': 0,
            'precios_extremos': 0,
            'duplicados_urls': 0
        }

        try:
            cursor = self.conn.cursor()

            # Propiedades sin agente
            cursor.execute("""
                SELECT COUNT(*) FROM propiedades
                WHERE agente_id IS NULL
                AND agente_id NOT IN (SELECT id FROM agentes)
            """)
            results['propiedades_sin_agente'] = cursor.fetchone()[0]

            # Servicios sin categoría válida
            cursor.execute("""
                SELECT COUNT(*) FROM servicios
                WHERE categoria_principal IS NULL
                OR categoria_principal NOT IN (SELECT categoria_principal FROM categorias_servicios)
            """)
            results['servicios_sin_categoria'] = cursor.fetchone()[0]

            # Coordenadas inválidas (fuera de rango Santa Cruz)
            cursor.execute("""
                SELECT COUNT(*) FROM propiedades
                WHERE (latitud < -18.5 OR latitud > -17.0
                OR longitud < -64.0 OR longitud > -62.5)
                AND latitud IS NOT NULL AND longitud IS NOT NULL
            """)
            results['coordenadas_invalidas'] = cursor.fetchone()[0]

            # Precios extremos
            cursor.execute("""
                SELECT COUNT(*) FROM propiedades
                WHERE precio_usd IS NOT NULL
                AND (precio_usd < 10000 OR precio_usd > 10000000)
            """)
            results['precios_extremos'] = cursor.fetchone()[0]

            # URLs duplicadas
            cursor.execute("""
                SELECT COUNT(*) FROM (
                    SELECT url, COUNT(*) as cnt FROM propiedades
                    GROUP BY url HAVING COUNT(*) > 1
                ) as duplicados
            """)
            results['duplicados_urls'] = cursor.fetchone()[0]

            cursor.close()

            # Evaluar consistencia
            problemas = 0
            if results['propiedades_sin_agente'] > 0:
                logger.warning(f"{results['propiedades_sin_agente']} propiedades sin agente válido")
                problemas += 1

            if results['servicios_sin_categoria'] > 0:
                logger.warning(f"{results['servicios_sin_categoria']} servicios sin categoría válida")
                problemas += 1

            if results['coordenadas_invalidas'] > 0:
                logger.warning(f"{results['coordenadas_invalidas']} propiedades con coordenadas inválidas")
                problemas += 1

            if results['precios_extremos'] > 0:
                logger.warning(f"{results['precios_extremos']} propiedades con precios extremos")
                problemas += 1

            if results['duplicados_urls'] > 0:
                logger.error(f"{results['duplicados_urls']} URLs duplicadas")
                problemas += 1

            if problemas == 0:
                logger.info("Datos consistentes ✓")
            else:
                logger.warning(f"Se encontraron {problemas} tipos de problemas de consistencia")

            results['problemas_encontrados'] = problemas
            results['consistente'] = problemas == 0

            return results

        except Exception as e:
            logger.error(f"Error validando consistencia: {e}")
            raise

    def ejecutar_validacion_completa(self) -> Dict:
        """Ejecutar todas las validaciones"""
        logger.info("Iniciando validación completa de migración")
        start_time = datetime.now()

        try:
            self.conectar_db()

            # Ejecutar todas las pruebas
            resultados = {
                'fecha_inicio': start_time.isoformat(),
                'test_estructura_bd': self.test_estructura_bd(),
                'test_datos_basicos': self.test_datos_basicos(),
                'test_consultas_espaciales': self.test_consultas_espaciales(),
                'test_rendimiento': self.test_rendimiento(),
                'test_consistencia_datos': self.test_consistencia_datos(),
                'fecha_fin': datetime.now().isoformat(),
                'duracion_segundos': (datetime.now() - start_time).total_seconds()
            }

            # Resumen final
            duracion = resultados['duracion_segundos']
            estructura_ok = len(resultados['test_estructura_bd']['tablas_encontradas']) >= 4
            datos_ok = resultados['test_datos_basicos']['propiedades_total'] > 0
            rendimiento_ok = resultados['test_rendimiento']['porcentaje_exito'] >= 60
            consistencia_ok = resultados['test_consistencia_datos']['problemas_encontrados'] <= 1

            resultados['resumen'] = {
                'estructura_ok': estructura_ok,
                'datos_ok': datos_ok,
                'rendimiento_ok': rendimiento_ok,
                'consistencia_ok': consistencia_ok,
                'general_exitosa': estructura_ok and datos_ok and rendimiento_ok and consistencia_ok
            }

            if resultados['resumen']['general_exitosa']:
                logger.info("=== VALIDACIÓN COMPLETADA EXITOSAMENTE ===")
                logger.info(f"Duración: {duracion:.1f} segundos")
                logger.info("Todos los tests pasaron ✓")
            else:
                logger.warning("=== VALIDACIÓN COMPLETADA CON OBSERVACIONES ===")
                logger.info(f"Duración: {duracion:.1f} segundos")
                logger.info(f"Estructura: {'✓' if estructura_ok else '✗'}")
                logger.info(f"Datos: {'✓' if datos_ok else '✗'}")
                logger.info(f"Rendimiento: {'✓' if rendimiento_ok else '✗'}")
                logger.info(f"Consistencia: {'✓' if consistencia_ok else '✗'}")

            # Guardar resultados
            with open('migration/logs/validation_results.json', 'w') as f:
                json.dump(resultados, f, indent=2, ensure_ascii=False, default=str)

            return resultados

        except Exception as e:
            logger.error(f"Error en validación: {e}")
            raise
        finally:
            if self.conn:
                self.conn.close()

def main():
    """Función principal"""
    # Configuración de base de datos
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'citrino'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'password'),
        'port': os.getenv('DB_PORT', '5432')
    }

    # Crear directorio de logs si no existe
    os.makedirs('migration/logs', exist_ok=True)

    validator = MigrationValidator(db_config)

    try:
        resultados = validator.ejecutar_validacion_completa()

        if resultados['resumen']['general_exitosa']:
            logger.info("¡Validación exitosa!")
            return 0
        else:
            logger.warning("Validación completada con advertencias")
            return 1

    except Exception as e:
        logger.error(f"Validación fallida: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())