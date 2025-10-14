# 🚀 Plan de Migración: JSON a PostgreSQL + PostGIS

**Versión**: 1.0
**Fecha**: 2025-10-14
**Basado en**: Investigación Tongyi + Arquitectura Citrino
**Objetivo**: Migración completa con rendimiento optimizado y rollback seguro

---

## 📋 Resumen Ejecutivo

### Migración Estratégica
- **Origen**: Archivos JSON centralizados (1,588 propiedades + 4,777 servicios)
- **Destino**: PostgreSQL 15+ con PostGIS 3.3+
- **Resultado**: Consultas geoespaciales de segundos → milisegundos
- **Seguridad**: Rollback instantáneo disponible

### Beneficios Clave
1. **Performance**: Índices GIST para búsquedas espaciales ultra rápidas
2. **Integridad**: Transacciones ACID y claves foráneas
3. **Escalabilidad**: Soporte para 10x crecimiento de datos
4. **Concurrencia**: Múltiples usuarios sin bloqueos

---

## 🗄️ Esquema Completo de Base de Datos

### DDL Completo (Data Definition Language)

```sql
-- =====================================================
-- MIGRATION: JSON to PostgreSQL + PostGIS for Citrino
-- Basado en investigación Tongyi y arquitectura existente
-- =====================================================

-- Habilitar extensión PostGIS (ejecutar una vez)
CREATE EXTENSION IF NOT EXISTS postgis;

-- =====================================================
-- 1. TABLA DE AGENTES (Normalizada con deduplicación)
-- =====================================================
CREATE TABLE agentes (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    telefono VARCHAR(50),
    email VARCHAR(255) UNIQUE,
    fecha_registro TIMESTAMPTZ DEFAULT now(),

    -- Constraints para integridad
    CONSTRAINT uq_agente_nombre UNIQUE (nombre),
    CONSTRAINT chk_telefono_formato CHECK (telefono ~ '^[0-9\+\-\s\(\)]*$' OR telefono IS NULL),
    CONSTRAINT chk_email_formato CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$' OR email IS NULL)
);

-- =====================================================
-- 2. TABLA DE PROPIEDADES (Principal con coordenadas geoespaciales)
-- =====================================================
CREATE TABLE propiedades (
    id BIGSERIAL PRIMARY KEY,

    -- Relación con agente (clave foránea)
    agente_id BIGINT REFERENCES agentes(id) ON DELETE SET NULL,

    -- Datos básicos de la propiedad
    titulo VARCHAR(255) NOT NULL,
    tipo_propiedad VARCHAR(100),
    precio_usd NUMERIC(12, 2),

    -- Datos de ubicación
    direccion TEXT,
    zona VARCHAR(100),
    uv VARCHAR(50), -- Unidad Vecinal
    manzana VARCHAR(50),

    -- Coordenadas geoespaciales (POSTGIS)
    -- SRID 4326 = WGS84 (estándar GPS)
    coordenadas GEOGRAPHY(POINT, 4326) NOT NULL,

    -- Metadatos del sistema
    fecha_publicacion TIMESTAMPTZ,
    ultima_actualizacion TIMESTAMPTZ DEFAULT now(),
    proveedor_datos VARCHAR(100), -- 01, 02, 03, etc.
    url_origen TEXT,
    archivo_origen VARCHAR(255), -- tracking del archivo original
    uuid_procesamiento UUID DEFAULT gen_random_uuid(),

    -- Constraints de integridad
    CONSTRAINT chk_precio_positivo CHECK (precio_usd > 0 OR precio_usd IS NULL),
    CONSTRAINT chk_coordenadas_validas CHECK (ST_IsValid(coordenadas)),
    CONSTRAINT chk_tipo_propiedad CHECK (tipo_propiedad IN ('casa', 'departamento', 'terreno', 'penthouse', 'oficina', 'galpón', 'edificio') OR tipo_propiedad IS NULL)
);

-- =====================================================
-- 3. TABLA DE SERVICIOS URBANOS (Puntos de interés)
-- =====================================================
CREATE TABLE servicios (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    tipo_servicio VARCHAR(100) NOT NULL,
    subtipo VARCHAR(100), -- colegio primario, hospital público, etc.
    coordenadas GEOGRAPHY(POINT, 4326) NOT NULL,
    direccion TEXT,

    -- Metadatos
    fuente_datos VARCHAR(100), -- guía urbana municipal
    fecha_registro TIMESTAMPTZ DEFAULT now(),

    -- Constraints
    CONSTRAINT chk_coordenadas_servicios CHECK (ST_IsValid(coordenadas)),
    CONSTRAINT chk_tipo_servicio CHECK (tipo_servicio IN ('educacion', 'salud', 'transporte', 'abastecimiento', 'deporte', 'seguridad', 'otros'))
);

-- =====================================================
-- 4. ÍNDICES DE OPTIMIZACIÓN (CRÍTICO PARA RENDIMIENTO)
-- =====================================================

-- Índices espaciales GIST para búsquedas por radio
CREATE INDEX idx_propiedades_coordenadas ON propiedades USING GIST (coordenadas);
CREATE INDEX idx_servicios_coordenadas ON servicios USING GIST (coordenadas);

-- Índices B-Tree para filtros y JOINs
CREATE INDEX idx_propiedades_agente_id ON propiedades(agente_id);
CREATE INDEX idx_propiedades_precio ON propiedades(precio_usd);
CREATE INDEX idx_propiedades_tipo ON propiedades(tipo_propiedad);
CREATE INDEX idx_propiedades_zona ON propiedades(zona);
CREATE INDEX idx_propiedades_proveedor ON propiedades(proveedor_datos);
CREATE INDEX idx_servicios_tipo ON servicios(tipo_servicio);
CREATE INDEX idx_servicios_subtipo ON servicios(subtipo);

-- Índices compuestos para consultas frecuentes
CREATE INDEX idx_propiedades_zona_precio_tipo ON propiedades(zona, precio_usd, tipo_propiedad);
CREATE INDEX idx_propiedades_ultima_actualizacion ON propiedades(ultima_actualizacion DESC);

-- =====================================================
-- 5. VISTAS ÚTILES PARA CONSULTAS COMUNES
-- =====================================================

-- Vista de propiedades con datos completos
CREATE VIEW v_propiedades_completas AS
SELECT
    p.id,
    p.titulo,
    p.tipo_propiedad,
    p.precio_usd,
    p.direccion,
    p.zona,
    p.uv,
    p.manzana,
    ST_Y(p.coordenadas) as latitud,
    ST_X(p.coordenadas) as longitud,
    p.fecha_publicacion,
    p.proveedor_datos,
    a.nombre as nombre_agente,
    a.telefono as telefono_agente,
    a.email as email_agente
FROM propiedades p
LEFT JOIN agentes a ON p.agente_id = a.id;

-- Vista de servicios por categoría
CREATE VIEW v_servicios_por_categoria AS
SELECT
    tipo_servicio,
    COUNT(*) as total_servicios,
    ARRAY_AGG(DISTINCT subtipo) as subtipos_disponibles
FROM servicios
GROUP BY tipo_servicio
ORDER BY total_servicios DESC;
```

---

## 🔄 Proceso ETL Detallado

### Estructura de Directorios de Migración
```
migration/
├── scripts/
│   ├── 01_etl_agentes.py          # Deduplicación de agentes
│   ├── 02_etl_propiedades.py      # Migración de propiedades
│   ├── 03_etl_servicios.py        # Migración de servicios
│   ├── 04_validate_migration.py   # Validación completa
│   └── 05_performance_test.py     # Tests de rendimiento
├── database/
│   ├── 01_create_schema.sql       # DDL completo
│   ├── 02_create_indexes.sql      # Índices
│   ├── 03_create_views.sql        # Vistas útiles
│   └── 04_sample_data.sql         # Datos de prueba
├── config/
│   ├── database_config.py         # Configuración conexión
│   ├── migration_config.py        # Parámetros ETL
│   └── validation_rules.py        # Reglas de validación
└── logs/
    ├── etl_agentes.log
    ├── etl_propiedades.log
    ├── etl_servicios.log
    └── validation.log
```

### Script 1: ETL de Agentes (Deduplicación)
```python
#!/usr/bin/env python3
"""
ETL Script 1: Migración y Deduplicación de Agentes
Basado en arquitectura actual de Citrino
"""

import json
import psycopg2
from psycopg2 import sql, extras
import logging
from typing import Dict, Set, List
from datetime import datetime

# Configuración
from config.database_config import get_db_connection
from config.migration_config import *

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/etl_agentes.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AgentesETL:
    def __init__(self):
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()
        self.agentes_unicos: Set[str] = set()
        self.agentes_map: Dict[str, int] = {}

    def extraer_agentes_de_json(self) -> List[Dict]:
        """Extraer todos los agentes únicos del JSON actual"""
        logger.info("Extrayendo agentes del JSON actual...")

        with open('data/base_datos_relevamiento.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        agentes_encontrados = {}

        for propiedad in data.get('propiedades', []):
            nombre_agente = self.limpiar_texto(propiedad.get('agente', ''))
            if nombre_agente and nombre_agente not in agentes_encontrados:
                agentes_encontrados[nombre_agente] = {
                    'nombre': nombre_agente,
                    'telefono': self.limpiar_texto(propiedad.get('telefono', '')),
                    'email': self.limpiar_texto(propiedad.get('correo', ''))
                }

        logger.info(f"Se encontraron {len(agentes_encontrados)} agentes únicos")
        return list(agentes_encontrados.values())

    def limpiar_texto(self, texto: str) -> str:
        """Limpiar y normalizar texto"""
        if not texto:
            return ''
        return str(texto).strip().replace('\n', ' ').replace('\t', ' ')

    def insertar_agentes(self, agentes: List[Dict]) -> Dict[str, int]:
        """Insertar agentes en PostgreSQL con deduplicación"""
        logger.info("Insertando agentes en PostgreSQL...")

        insert_query = sql.SQL("""
            INSERT INTO agentes (nombre, telefono, email)
            VALUES (%(nombre)s, %(telefono)s, %(email)s)
            ON CONFLICT (nombre) DO NOTHING
            RETURNING id
        """)

        agentes_ids = {}
        insertados = 0

        for agente in agentes:
            try:
                self.cursor.execute(insert_query, agente)
                result = self.cursor.fetchone()

                if result:
                    agentes_ids[agente['nombre']] = result[0]
                    insertados += 1
                else:
                    # Si ya existía, obtener su ID
                    self.cursor.execute(
                        "SELECT id FROM agentes WHERE nombre = %s",
                        (agente['nombre'],)
                    )
                    result = self.cursor.fetchone()
                    if result:
                        agentes_ids[agente['nombre']] = result[0]

            except Exception as e:
                logger.error(f"Error insertando agente {agente['nombre']}: {e}")
                continue

        self.conn.commit()
        logger.info(f"Se insertaron {insertados} agentes nuevos")
        logger.info(f"Total de agentes en BD: {len(agentes_ids)}")

        return agentes_ids

    def run(self) -> Dict[str, int]:
        """Ejecutar proceso completo ETL de agentes"""
        try:
            # 1. Extraer agentes del JSON
            agentes = self.extraer_agentes_de_json()

            # 2. Insertar en PostgreSQL
            agentes_ids = self.insertar_agentes(agentes)

            # 3. Guardar mapa para siguientes ETLs
            self.guardar_mapa_agentes(agentes_ids)

            return agentes_ids

        except Exception as e:
            logger.error(f"Error en ETL de agentes: {e}")
            self.conn.rollback()
            raise
        finally:
            self.cursor.close()
            self.conn.close()

    def guardar_mapa_agentes(self, agentes_ids: Dict[str, int]):
        """Guardar mapa de agentes para usar en otros ETLs"""
        import json

        with open('migration/config/agentes_map.json', 'w', encoding='utf-8') as f:
            json.dump(agentes_ids, f, ensure_ascii=False, indent=2)

        logger.info("Mapa de agentes guardado para siguientes ETLs")

if __name__ == "__main__":
    etl = AgentesETL()
    agentes_map = etl.run()
    print(f"ETL Agentes completado. Procesados {len(agentes_map)} agentes.")
```

### Script 2: ETL de Propiedades
```python
#!/usr/bin/env python3
"""
ETL Script 2: Migración de Propiedades a PostgreSQL + PostGIS
"""

import json
import psycopg2
from psycopg2 import sql, extras
import logging
from typing import Dict, List, Optional
from datetime import datetime
import uuid

class PropiedadesETL:
    def __init__(self):
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()
        self.agentes_map = self.cargar_mapa_agentes()
        self.registros_procesados = 0
        self.registros_omitidos = 0

    def cargar_mapa_agentes(self) -> Dict[str, int]:
        """Cargar mapa de agentes desde ETL anterior"""
        import json

        try:
            with open('migration/config/agentes_map.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("No se encontró mapa de agentes. Ejecutar primero ETL de agentes.")
            raise

    def convertir_coordenadas_postgis(self, lat: Optional[float], lng: Optional[float]) -> Optional[str]:
        """Convertir coordenadas a formato PostGIS"""
        if lat is None or lng is None:
            return None

        # Validar rangos para Santa Cruz, Bolivia
        if not (-18.5 <= lat <= -17.0) or not (-64.0 <= lng <= -63.0):
            logger.warning(f"Coordenadas fuera de rango: {lat}, {lng}")
            return None

        return f"ST_SetSRID(ST_MakePoint({lng}, {lat}), 4326)::geography"

    def procesar_propiedad(self, propiedad: Dict) -> Optional[Dict]:
        """Procesar una propiedad individual"""
        try:
            # Coordenadas
            coords_postgis = self.convertir_coordenadas_postgis(
                propiedad.get('latitud'),
                propiedad.get('longitud')
            )

            if not coords_postgis:
                self.registros_omitidos += 1
                return None

            # ID de agente
            nombre_agente = propiedad.get('agente', '').strip()
            agente_id = self.agentes_map.get(nombre_agente) if nombre_agente else None

            # Estructurar datos para PostgreSQL
            return {
                'agente_id': agente_id,
                'titulo': propiedad.get('titulo', '').strip(),
                'tipo_propiedad': propiedad.get('tipo_propiedad', '').strip(),
                'precio_usd': propiedad.get('precio'),
                'direccion': propiedad.get('direccion', '').strip(),
                'zona': propiedad.get('zona', '').strip(),
                'uv': propiedad.get('unidad_vecinal', '').strip(),
                'manzana': propiedad.get('manzana', '').strip(),
                'coordenadas': coords_postgis,
                'fecha_publicacion': self.parsear_fecha(propiedad.get('fecha_scraping')),
                'proveedor_datos': propiedad.get('codigo_proveedor', ''),
                'url_origen': propiedad.get('url', ''),
                'archivo_origen': propiedad.get('archivo_origen', ''),
                'uuid_procesamiento': str(uuid.uuid4())
            }

        except Exception as e:
            logger.error(f"Error procesando propiedad {propiedad.get('id', 'unknown')}: {e}")
            self.registros_omitidos += 1
            return None

    def parsear_fecha(self, fecha_str: Optional[str]) -> Optional[datetime]:
        """Parsear fecha en formato YYYY.MM.DD"""
        if not fecha_str:
            return None

        try:
            return datetime.strptime(fecha_str, '%Y.%m.%d')
        except ValueError:
            logger.warning(f"Fecha no válida: {fecha_str}")
            return None

    def insertar_propiedades_batch(self, propiedades_procesadas: List[Dict]):
        """Insertar propiedades en lotes para mejor rendimiento"""
        if not propiedades_procesadas:
            return

        # Construir query dinámica para coordenadas
        columns = list(propiedades_procesadas[0].keys())
        values = []

        for prop in propiedades_procesadas:
            value_list = []
            for col in columns:
                if col == 'coordenadas':
                    value_list.append(prop[col])  # Es un string SQL
                else:
                    value_list.append(prop[col])
            values.append(tuple(value_list))

        # Insert con coordenadas especiales
        query = f"""
            INSERT INTO propiedades ({', '.join(columns)})
            VALUES %s
            ON CONFLICT DO NOTHING
        """

        try:
            # Usar execute_values para batch insert
            placeholders = ', '.join(['%s'] * len(columns))
            insert_query = sql.SQL(f"""
                INSERT INTO propiedades ({', '.join(columns)})
                VALUES %s
                ON CONFLICT DO NOTHING
            """)

            # Manejar coordenadas como SQL directo
            formatted_values = []
            for value_tuple in values:
                formatted_list = list(value_tuple)
                formatted_values.append(tuple(formatted_list))

            psycopg2.extras.execute_values(
                self.cursor,
                "INSERT INTO propiedades ({}) VALUES %s ON CONFLICT DO NOTHING".format(
                    ', '.join(columns)
                ),
                formatted_values
            )

            self.registros_procesados += len(propiedades_procesadas)
            logger.info(f"Lote insertado: {len(propiedades_procesadas)} propiedades")

        except Exception as e:
            logger.error(f"Error en insert batch: {e}")
            raise

    def run(self):
        """Ejecutar ETL completo de propiedades"""
        try:
            logger.info("Iniciando ETL de propiedades...")

            # Cargar datos JSON
            with open('data/base_datos_relevamiento.json', 'r', encoding='utf-8') as f:
                data = json.load(f)

            propiedades = data.get('propiedades', [])
            total_propiedades = len(propiedades)
            logger.info(f"Total de propiedades a procesar: {total_propiedades}")

            # Procesar en lotes
            batch_size = 100
            batch_actual = []

            for i, propiedad in enumerate(propiedades):
                procesada = self.procesar_propiedad(propiedad)

                if procesada:
                    batch_actual.append(procesada)

                # Insertar lote
                if len(batch_actual) >= batch_size:
                    self.insertar_propiedades_batch(batch_actual)
                    batch_actual = []
                    logger.info(f"Progreso: {i+1}/{total_propiedades} ({((i+1)/total_propiedades)*100:.1f}%)")

            # Insertar último lote
            if batch_actual:
                self.insertar_propiedades_batch(batch_actual)

            self.conn.commit()

            logger.info(f"ETL Propiedades completado:")
            logger.info(f"  - Procesadas: {self.registros_procesados}")
            logger.info(f"  - Omitidas: {self.registros_omitidos}")
            logger.info(f"  - Total original: {total_propiedades}")

        except Exception as e:
            logger.error(f"Error en ETL de propiedades: {e}")
            self.conn.rollback()
            raise
        finally:
            self.cursor.close()
            self.conn.close()

if __name__ == "__main__":
    etl = PropiedadesETL()
    etl.run()
```

---

## 🧪 Scripts de Validación

### Validación Completa de Migración
```python
#!/usr/bin/env python3
"""
Script de Validación Completa de Migración
Compara datos originales vs migrados
"""

import json
import psycopg2
from typing import Dict, List
import logging
from datetime import datetime

class MigrationValidator:
    def __init__(self):
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()
        self.errores = []

    def validar_conteos(self):
        """Validar que todos los registros migraron correctamente"""
        logger.info("Validando conteos de registros...")

        # Cargar datos originales
        with open('data/base_datos_relevamiento.json', 'r', encoding='utf-8') as f:
            data_original = json.load(f)

        with open('data/guia_urbana_municipal_completa.json', 'r', encoding='utf-8') as f:
            servicios_original = json.load(f)

        # Conteos originales
        propiedades_original = len(data_original.get('propiedades', []))
        servicios_original = len(servicios_original.get('servicios_consolidados', []))

        # Conteos PostgreSQL
        self.cursor.execute("SELECT COUNT(*) FROM propiedades")
        propiedades_pg = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(*) FROM servicios")
        servicios_pg = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(*) FROM agentes")
        agentes_pg = self.cursor.fetchone()[0]

        # Validación
        validaciones = [
            ("Propiedades", propiedades_original, propiedades_pg),
            ("Servicios", servicios_original, servicios_pg)
        ]

        for nombre, original, pg in validaciones:
            if original == pg:
                logger.info(f"✅ {nombre}: {original} == {pg}")
            else:
                error_msg = f"❌ {nombre}: {original} != {pg} (diferencia: {abs(original-pg)})"
                logger.error(error_msg)
                self.errores.append(error_msg)

        logger.info(f"Agentes migrados: {agentes_pg}")

    def validar_integridad_espacial(self):
        """Validar que todas las coordenadas sean válidas"""
        logger.info("Validando integridad espacial...")

        # Coordenadas inválidas en propiedades
        self.cursor.execute("""
            SELECT COUNT(*) FROM propiedades
            WHERE NOT ST_IsValid(coordenadas)
        """)
        invalid_props = self.cursor.fetchone()[0]

        # Coordenadas inválidas en servicios
        self.cursor.execute("""
            SELECT COUNT(*) FROM servicios
            WHERE NOT ST_IsValid(coordenadas)
        """)
        invalid_serv = self.cursor.fetchone()[0]

        if invalid_props == 0 and invalid_serv == 0:
            logger.info("✅ Todas las coordenadas son válidas")
        else:
            error_msg = f"❌ Coordenadas inválidas: {invalid_props} propiedades, {invalid_serv} servicios"
            logger.error(error_msg)
            self.errores.append(error_msg)

    def validar_rendimiento(self):
        """Validar rendimiento de consultas geoespaciales"""
        logger.info("Validando rendimiento de consultas...")

        # Query de prueba: propiedades cerca del centro de Santa Cruz
        query_test = """
        SELECT COUNT(*)
        FROM propiedades
        WHERE ST_DWithin(
            coordenadas,
            ST_MakePoint(-63.182, -17.783)::geography,
            2000
        )
        """

        start_time = datetime.now()
        self.cursor.execute(query_test)
        resultado = self.cursor.fetchone()[0]
        end_time = datetime.now()

        tiempo_ms = (end_time - start_time).total_seconds() * 1000

        if tiempo_ms < 100:  # Menos de 100ms
            logger.info(f"✅ Rendimiento excelente: {tiempo_ms:.2f}ms ({resultado} propiedades)")
        elif tiempo_ms < 500:
            logger.info(f"⚠️ Rendimiento aceptable: {tiempo_ms:.2f}ms")
        else:
            error_msg = f"❌ Rendimiento pobre: {tiempo_ms:.2f}ms (debe ser <100ms)"
            logger.error(error_msg)
            self.errores.append(error_msg)

    def validar_relaciones(self):
        """Validar relaciones entre tablas"""
        logger.info("Validando relaciones...")

        # Propiedades sin agente
        self.cursor.execute("""
            SELECT COUNT(*) FROM propiedades
            WHERE agente_id IS NULL
        """)
        sin_agente = self.cursor.fetchone()[0]

        logger.info(f"Propiedades sin agente: {sin_agente}")

        # Verificar integridad de zona
        self.cursor.execute("""
            SELECT zona, COUNT(*)
            FROM propiedades
            WHERE zona IS NOT NULL AND zona != ''
            GROUP BY zona
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        top_zonas = self.cursor.fetchall()

        logger.info("Top 10 zonas con más propiedades:")
        for zona, count in top_zonas:
            logger.info(f"  - {zona}: {count} propiedades")

    def run(self) -> bool:
        """Ejecutar todas las validaciones"""
        try:
            logger.info("Iniciando validación completa de migración...")

            self.validar_conteos()
            self.validar_integridad_espacial()
            self.validar_rendimiento()
            self.validar_relaciones()

            if self.errores:
                logger.error(f"\n❌ VALIDACIÓN FALLIDA con {len(self.errores)} errores:")
                for error in self.errores:
                    logger.error(f"  - {error}")
                return False
            else:
                logger.info("\n✅ VALIDACIÓN EXITOSA - Todos los tests pasaron")
                return True

        except Exception as e:
            logger.error(f"Error en validación: {e}")
            return False
        finally:
            self.cursor.close()
            self.conn.close()

if __name__ == "__main__":
    validator = MigrationValidator()
    exit_code = 0 if validator.run() else 1
    exit(exit_code)
```

---

## 🔄 Sistema de Configuración y Rollback

### Configuración de Conexión
```python
# migration/config/database_config.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    """Obtener conexión a PostgreSQL con configuración segura"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'citrino'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            cursor_factory=RealDictCursor
        )
        logger.info("Conexión a PostgreSQL establecida")
        return conn
    except Exception as e:
        logger.error(f"Error conectando a PostgreSQL: {e}")
        raise

def test_connection():
    """Probar conexión a la base de datos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        logger.info(f"PostgreSQL conectado: {version}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error en conexión de prueba: {e}")
        return False
```

### Sistema de Switching (JSON ↔ PostgreSQL)
```python
# src/data_source.py
import os
from typing import List, Dict, Any

# Configuración switching
USE_POSTGRES = os.getenv('USE_POSTGRES', 'false').lower() == 'true'

def get_data_source():
    """Factory para seleccionar fuente de datos"""
    if USE_POSTGRES:
        from .postgres_source import PostgresDataSource
        logger.info("Usando PostgreSQL como fuente de datos")
        return PostgresDataSource()
    else:
        from .json_source import JsonDataSource
        logger.info("Usando JSON como fuente de datos")
        return JsonDataSource()

# Uso en la aplicación
data_source = get_data_source()
propiedades = data_source.get_propiedades()
```

---

## 📋 Plan de Ejecución

### Secuencia de Ejecución
1. **Preparación** (30 min)
   - Crear base de datos PostgreSQL
   - Ejecutar DDL completo
   - Configurar variables de entorno

2. **ETL Agentes** (15 min)
   - Ejecutar `01_etl_agentes.py`
   - Validar deduplicación
   - Revisar logs

3. **ETL Propiedades** (45 min)
   - Ejecutar `02_etl_propiedades.py`
   - Monitorear progreso
   - Validar coordenadas

4. **ETL Servicios** (15 min)
   - Ejecutar `03_etl_servicios.py`
   - Verificar categorías

5. **Validación** (30 min)
   - Ejecutar `04_validate_migration.py`
   - Corregir errores si hay
   - Tests de rendimiento

6. **Testing Final** (30 min)
   - Probar aplicación con PostgreSQL
   - Verificar endpoints API
   - Comparar rendimiento

### Comandos de Ejecución
```bash
# 1. Preparar entorno
export DB_HOST=localhost
export DB_NAME=citrino
export DB_USER=postgres
export DB_PASSWORD=your_password

# 2. Crear esquema
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f migration/database/01_create_schema.sql

# 3. Ejecutar ETLs
python migration/scripts/01_etl_agentes.py
python migration/scripts/02_etl_propiedades.py
python migration/scripts/03_etl_servicios.py

# 4. Validar migración
python migration/scripts/04_validate_migration.py

# 5. Test de rendimiento
python migration/scripts/05_performance_test.py

# 6. Activar PostgreSQL en aplicación
export USE_POSTGRES=true
python api/server.py
```

---

## 🛡️ Plan de Rollback

### Procedimiento de Emergencia
1. **Detectar Problema** (Monitoreo 24-48 hrs)
2. **Switch Inmediato**:
   ```bash
   export USE_POSTGRES=false
   python api/server.py
   ```
3. **Investigar Causa** en PostgreSQL sin afectar producción
4. **Decisión** en ventana de 24-48 horas

### Criterios de Rollback
- **Performance**: Consultas >500ms consistentemente
- **Data Loss**: Cualquier pérdida de datos detectada
- **Errors**: Más de 1% de consultas fallando
- **Downtime**: Sistema no disponible >5 min

---

## 📊 Métricas de Éxito

### Métricas Técnicas
- **Migration Success**: 100% registros migrados
- **Query Performance**: <100ms para consultas geoespaciales
- **Data Integrity**: 0 coordenadas inválidas
- **Index Usage**: Queries usando índices GIST/B-Tree

### Métricas de Negocio
- **Response Time**: Reducción >90% vs JSON
- **System Availability**: 99.9% uptime
- **Concurrent Users**: Soporte multiusuario sin bloqueos
- **Data Quality**: Deduplicación automática de agentes

---

*Documentación completa para migración segura y validada a PostgreSQL + PostGIS*

**Última actualización**: 2025-10-14
**Estado**: Listo para implementación
**Riesgo**: Bajo (con rollback plan)