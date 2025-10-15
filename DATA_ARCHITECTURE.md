# 🏗️ Arquitectura de Datos - Migración a PostgreSQL + PostGIS

Documentación completa de la migración desde JSON centralizado a PostgreSQL + PostGIS basada en investigación experta de Tongyi.

---

## 🎯 Resumen Ejecutivo

**Decisión Estratégica**: Migración de archivos JSON a PostgreSQL + PostGIS
**Fuente**: Investigación detallada con Tongyi (LLM especializado)
**Objetivo**: Resolver limitaciones de rendimiento, escalabilidad y consistencia
**Resultado Esperado**: Consultas geoespaciales de segundos → milisegundos

### Beneficios Clave
- **Rendimiento**: Reducción drástica en tiempos de respuesta geoespacial
- **Escalabilidad**: Capacidad para 10x crecimiento sin degradación
- **Integridad**: Consistencia ACID con claves foráneas
- **Capacidades Analíticas**: Consultas complejas relacionales + espaciales

---

## 📊 Estado Actual vs Propuesto

### Arquitectura Actual (JSON)
```
data/
├── base_datos_relevamiento.json    # 1,588 propiedades
└── guia_urbana_municipal_completa.json  # 4,777 servicios
```

**Limitaciones Críticas**:
- Consultas O(n×m): 7,585,876 cálculos por búsqueda
- Sin concurrencia en actualizaciones
- Duplicación de datos de agentes
- Performance: segundos por consulta geoespacial

### Arquitectura Propuesta (PostgreSQL + PostGIS)
```
PostgreSQL Database:
├── agentes (tabla normalizada)
├── propiedades (con coordenadas GEOGRAPHY)
├── servicios (con índices espaciales GIST)
└── Índices optimizados (B-Tree + GIST)
```

**Ventajas**:
- Consultas con índices espaciales: milisegundos
- Integridad referencial completa
- Concurrencia transaccional
- Deduplicación automática

---

## 🗄️ Esquema de Base de Datos (PostgreSQL + PostGIS)

### Estructura de Tablas

```sql
-- Habilitar PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. Tabla de Agentes (Normalizada)
CREATE TABLE agentes (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    telefono VARCHAR(50),
    email VARCHAR(255) UNIQUE,
    fecha_registro TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT uq_agente_nombre UNIQUE (nombre)
);

-- 2. Tabla de Propiedades (Principal)
CREATE TABLE propiedades (
    id BIGSERIAL PRIMARY KEY,
    agente_id BIGINT NOT NULL REFERENCES agentes(id) ON DELETE SET NULL,

    -- Datos descriptivos
    titulo VARCHAR(255) NOT NULL,
    tipo_propiedad VARCHAR(100),
    precio_usd NUMERIC(12, 2),

    -- Datos de ubicación
    direccion TEXT,
    zona VARCHAR(100),
    uv VARCHAR(50),
    manzana VARCHAR(50),

    -- Columna GEOESPACIAL clave
    coordenadas GEOGRAPHY(POINT, 4326) NOT NULL,

    -- Metadatos
    fecha_publicacion TIMESTAMPTZ,
    ultima_actualizacion TIMESTAMPTZ DEFAULT now(),
    proveedor_datos VARCHAR(100),
    url_origen TEXT
);

-- 3. Tabla de Servicios (Puntos de Interés)
CREATE TABLE servicios (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    tipo_servicio VARCHAR(100),
    coordenadas GEOGRAPHY(POINT, 4326) NOT NULL
);
```

### Índices Optimizados (Crítico para Performance)

```sql
-- Índices espaciales GIST para búsquedas por radio
CREATE INDEX idx_propiedades_coordenadas ON propiedades USING GIST (coordenadas);
CREATE INDEX idx_servicios_coordenadas ON servicios USING GIST (coordenadas);

-- Índices B-Tree para filtros y JOINs
CREATE INDEX idx_propiedades_agente_id ON propiedades(agente_id);
CREATE INDEX idx_propiedades_precio ON propiedades(precio_usd);
CREATE INDEX idx_propiedades_tipo ON propiedades(tipo_propiedad);
CREATE INDEX idx_propiedades_zona ON propiedades(zona);
CREATE INDEX idx_servicios_tipo ON servicios(tipo_servicio);
```

---

## 🔄 Transformación de Consultas Críticas

### Consulta Actual (Lógica en Aplicación)
```python
# Rendimiento: O(n×m) = segundos
def buscar_propiedades_georreferenciadas(zona, precio_min, precio_max, radio_km):
    resultados = []
    for propiedad in propiedades:
        if propiedad.zona == zona and precio_min <= propiedad.precio <= precio_max:
            for servicio in servicios_urbanos:
                distancia = haversine(propiedad.coords, servicio.coords)
                if distancia <= radio_km:
                    resultados.append(propiedad)
                    break
    return resultados
```

### Nueva Consulta (PostgreSQL + PostGIS)
```sql
-- Rendimiento: milisegundos con índices
WITH params AS (
    SELECT
        'Equipetrol' AS zona_busqueda,
        200000 AS precio_min,
        300000 AS precio_max,
        'departamento' AS tipo_busqueda,
        2000 AS distancia_max_metros -- 2km
)
SELECT
    p.id,
    p.titulo,
    p.precio_usd,
    p.direccion,
    a.nombre AS nombre_agente,
    a.telefono AS telefono_agente
FROM
    propiedades p
JOIN
    agentes a ON p.agente_id = a.id
WHERE
    p.zona = (SELECT zona_busqueda FROM params)
    AND p.precio_usd BETWEEN (SELECT precio_min FROM params) AND (SELECT precio_max FROM params)
    AND p.tipo_propiedad = (SELECT tipo_busqueda FROM params)
    -- Condición geoespacial: colegio cerca
    AND EXISTS (
        SELECT 1
        FROM servicios s
        WHERE s.tipo_servicio = 'colegio'
          AND ST_DWithin(p.coordenadas, s.coordenadas, (SELECT distancia_max_metros FROM params))
    )
    -- Condición geoespacial: hospital cerca
    AND EXISTS (
        SELECT 1
        FROM servicios s
        WHERE s.tipo_servicio = 'hospital'
          AND ST_DWithin(p.coordenadas, s.coordenadas, (SELECT distancia_max_metros FROM params))
    );
```

---

## 🚀 Plan de Migración (ETL)

### Fase 1: Preparación del Entorno
1. **Aprovisionar PostgreSQL** (RDS, Cloud SQL o local)
2. **Ejecutar DDL** para crear tablas e índices
3. **Configurar conexión** desde aplicación

### Fase 2: Script ETL de Migración

#### Paso 2.1: Migrar Agentes (Deduplicación)
```python
# Extraer agentes únicos del JSON
agentes_unicos = set()
for propiedad in datos_json:
    if propiedad.get('agente'):
        agentes_unicos.add(propiedad['agente'])

# Insertar en PostgreSQL
for agente_nombre in agentes_unicos:
    cursor.execute("""
        INSERT INTO agentes (nombre, telefono, email)
        VALUES (%s, %s, %s)
        ON CONFLICT (nombre) DO NOTHING
    """, (agente_nombre, telefono, email))

# Crear mapa de IDs para referencia rápida
agente_map = {nombre: id for id, nombre in get_agentes_from_db()}
```

#### Paso 2.2: Migrar Propiedades
```python
for propiedad in datos_json:
    # Convertir coordenadas a formato PostGIS
    coords_postgis = f"ST_SetSRID(ST_MakePoint({longitud}, {latitud}), 4326)::geography"

    cursor.execute("""
        INSERT INTO propiedades (
            agente_id, titulo, tipo_propiedad, precio_usd,
            direccion, zona, uv, manzana, coordenadas,
            fecha_publicacion, proveedor_datos, url_origen
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, {coords_postgis}, %s, %s, %s
        )
    """, (
        agente_map.get(propiedad['agente']),
        propiedad['titulo'],
        propiedad['tipo_propiedad'],
        propiedad['precio'],
        propiedad['direccion'],
        propiedad['zona'],
        propiedad['unidad_vecinal'],
        propiedad['manzana'],
        propiedad['fecha_scraping'],
        propiedad['codigo_proveedor'],
        propiedad['url']
    ))
```

#### Paso 2.3: Migrar Servicios
```python
for servicio in servicios_json:
    coords_postgis = f"ST_SetSRID(ST_MakePoint({longitud}, {latitud}), 4326)::geography"

    cursor.execute("""
        INSERT INTO servicios (nombre, tipo_servicio, coordenadas)
        VALUES (%s, %s, {coords_postgis})
    """, (servicio['nombre'], servicio['categoria']))
```

### Fase 3: Validación Post-Migración
```sql
-- Verificar conteos
SELECT COUNT(*) FROM propiedades; -- debe coincidir con JSON
SELECT COUNT(*) FROM servicios; -- debe coincidir con JSON

-- Validar relaciones
SELECT p.titulo, a.nombre
FROM propiedades p
JOIN agentes a ON p.agente_id = a.id
WHERE p.id = 123;

-- Probar consulta geoespacial
SELECT COUNT(*)
FROM propiedades
WHERE ST_DWithin(coordenadas, ST_MakePoint(-63.182, -17.783)::geography, 2000);
```

---

## 🔧 Refactorización de la Aplicación

### Motor de Recomendación Actualizado
```python
class RecommendationEnginePostGIS:
    def __init__(self, db_connection):
        self.db = db_connection

    def buscar_propiedades_georreferenciadas(self, criterios):
        query = """
        WITH params AS (
            SELECT %s AS zona_busqueda, %s AS precio_min,
                   %s AS precio_max, %s AS tipo_busqueda, %s AS distancia_max
        )
        SELECT p.*, a.nombre as agente_nombre
        FROM propiedades p
        JOIN agentes a ON p.agente_id = a.id
        WHERE p.zona = (SELECT zona_busqueda FROM params)
          AND p.precio_usd BETWEEN (SELECT precio_min FROM params) AND (SELECT precio_max FROM params)
          AND p.tipo_propiedad = (SELECT tipo_busqueda FROM params)
        """

        # Agregar condiciones de servicios dinámicamente
        for tipo_servicio in criterios['servicios_requeridos']:
            query += f"""
            AND EXISTS (
                SELECT 1 FROM servicios s
                WHERE s.tipo_servicio = '{tipo_servicio}'
                  AND ST_DWithin(p.coordenadas, s.coordenadas, (SELECT distancia_max FROM params))
            )
            """

        return self.db.execute(query, criterios.values()).fetchall()
```

---

## 🛡️ Plan de Rollback

### Estrategia de Seguridad
1. **Mantener Sistema JSON**: No eliminar archivos originales
2. **Configuración Switchable**: Variable de entorno para cambiar fuente de datos
3. **Ventana de Decisión**: 24-48 horas para validación final
4. **Rollback Instantáneo**: Cambiar configuración y reiniciar aplicación

### Implementación
```python
# config.py
USE_POSTGRES = os.getenv('USE_POSTGRES', 'false').lower() == 'true'

# data_source.py
if USE_POSTGRES:
    from .postgres_source import PostgresDataSource
    data_source = PostgresDataSource()
else:
    from .json_source import JsonDataSource
    data_source = JsonDataSource()
```

---

## 📈 Métricas de Éxito y Validación

### Métricas Técnicas
- **Performance**: Consultas geoespaciales <100ms (vs segundos actuales)
- **Data Integrity**: 100% de registros migrados exitosamente
- **Index Usage**: Queries usando índices GIST y B-Tree
- **Concurrent Users**: Soportar múltiples usuarios sin bloqueos

### Métricas de Negocio
- **Response Time**: Reducción 90% en tiempos de respuesta
- **System Availability**: 99.9% uptime con transacciones ACID
- **Data Quality**: Deduplicación automática de agentes
- **Scalability**: Capacidad para 10x datos sin degradación

### Validación Automatizada
```python
def validate_migration():
    # Comparar conteos
    json_count = len(load_json_properties())
    pg_count = execute_query("SELECT COUNT(*) FROM propiedades")[0][0]
    assert json_count == pg_count, f"Mismatch: {json_count} vs {pg_count}"

    # Probar rendimiento
    start_time = time.time()
    results = execute_test_query()
    end_time = time.time()

    assert (end_time - start_time) < 0.1, "Query too slow: >100ms"

    # Validar integridad espacial
    invalid_coords = execute_query("""
        SELECT COUNT(*) FROM propiedades
        WHERE NOT ST_IsValid(coordenadas)
    """)[0][0]
    assert invalid_coords == 0, f"Invalid coordinates: {invalid_coords}"
```

---

## 📁 Nueva Estructura del Proyecto

```
citrino-clean/
├── docs/
│   ├── CHANGELOG.md ✅
│   ├── SCRUM_BOARD.md ✅
│   ├── COMMITS_PLAN.md ✅
│   ├── WORKFLOW.md ✅
│   ├── DATA_ARCHITECTURE.md ✅ (actualizado)
│   └── MIGRATION_PLAN.md (nuevo)
├── migration/
│   ├── scripts/
│   │   ├── etl_agentes.py
│   │   ├── etl_propiedades.py
│   │   ├── etl_servicios.py
│   │   └── validate_migration.py
│   ├── database/
│   │   ├── 01_create_schema.sql
│   │   ├── 02_create_indexes.sql
│   │   └── 03_sample_queries.sql
│   └── config/
│       └── database_config.py
├── src/
│   ├── recommendation_engine_postgis.py
│   ├── database_connector.py
│   └── [archivos existentes actualizados]
└── data/
    ├── base_datos_relevamiento.json (backup)
    ├── guia_urbana_municipal_completa.json (backup)
    └── archived/ (versiones antiguas)
```

---

## 🎯 Próximos Pasos del Sprint

1. **Commit 1**: Completar documentación actualizada ✓
2. **Commit 2**: Limpieza y preparación para migración
3. **Commit 3**: Implementar scripts ETL básicos
4. **Commit 4**: Crear DDL completo de PostgreSQL
5. **Commit 5**: Refactorizar motor de recomendación
6. **Commit 6**: Ejecutar migración completa
7. **Commit 7**: Configurar sistema de rollback

---

## 🔄 Impacto en el Sistema Actual

### Cambios Inmediatos
- **Recomendation Engine**: Migración de Haversine Python a PostGIS
- **API Server**: Nuevos endpoints para consultas PostgreSQL
- **ETL Process**: Sistema de procesamiento de datos
- **Configuration**: Sistema switching JSON/PostgreSQL

### Beneficios a Largo Plazo
- **Performance**: Mejora exponencial en consultas geoespaciales
- **Scalability**: Preparado para crecimiento 10x
- **Maintainability**: Base de datos relacional vs archivos JSON
- **Analytics**: Capacidades avanzadas de consulta SQL

---

---

## 🤖 Integración con Chatbot UI (v2.1.0)

### Sistema Conversacional
El nuevo chatbot profesional integrado en v2.1.0 utiliza la arquitectura de datos actual (JSON) pero está preparado para migración PostgreSQL:

```python
# api/chatbot_completions.py
class CitrinoChatbotAPI:
    def __init__(self):
        self.propiedades = self._load_properties()  # JSON actual
        self.recommendation_engine = RecommendationEngineMejorado()

    def generate_property_search_response(self, entities):
        # Sistema híbrido actual - pronto migrará a PostgreSQL
        if self.recommendation_engine:
            recomendaciones = self.recommendation_engine.generar_recomendaciones(
                perfil, limite=5, umbral_minimo=0.01
            )
```

### Preparación para Migración
- **Data source abstraction**: Capa de abstracción lista para PostgreSQL
- **API endpoints consistentes**: Mismos endpoints durante y post-migración
- **Performance monitoring**: Métricas actuales baseline vs mejoras PostgreSQL esperadas

### Beneficios Esperados con PostgreSQL
- **Chatbot response time**: De 2s → <200ms con consultas PostGIS
- **Concurrent users**: Soporte multiusuario sin bloqueos
- **Advanced queries**: Búsqueda geoespacial compleja en tiempo real
- **Data freshness**: Actualizaciones incrementales concurrentes

---

*Última actualización: 2025-10-15 (con integración Chatbot UI v2.1.0)*
**Estado actual**: Chatbot UI operativo con JSON, migración PostgreSQL preparada