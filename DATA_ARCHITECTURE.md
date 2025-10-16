# 🏗️ Arquitectura de Datos - Excel RAW a PostgreSQL + PostGIS

Documentación completa del flujo de datos desde archivos Excel RAW hasta PostgreSQL + PostGIS. Los datos ORIGINALES provienen EXCLUSIVAMENTE de archivos Excel en data/raw/.

---

## 🎯 Resumen Ejecutivo

**Decisión Estratégica**: Flujo Excel RAW → PostgreSQL + PostGIS
**Fuente de Datos**: Exclusivamente archivos Excel en data/raw/ (NO JSON)
**Objetivo**: Validación estructurada y base de datos relacional optimizada
**Resultado Esperado**: Consultas geoespaciales de segundos → milisegundos

### Beneficios Clave
- **Rendimiento**: Reducción drástica en tiempos de respuesta geoespacial
- **Validación**: Proceso estructurado con archivos intermedios para revisión humana
- **Escalabilidad**: Capacidad para 10x crecimiento sin degradación
- **Integridad**: Consistencia ACID con claves foráneas
- **Capacidades Analíticas**: Consultas complejas relacionales + espaciales

---

## 📊 Estado Actual vs Propuesto

### Arquitectura Actual (Excel RAW → PostgreSQL)
```
data/
├── raw/                           # Archivos Excel ORIGINALES
│   ├── relevamiento/*.xlsx        # Propiedades
│   └── guia/GUIA URBANA.xlsx     # Servicios urbanos
├── processed/                     # Archivos intermedios
│   ├── *_intermedio.xlsx         # Para revisión humana
│   └── *_reporte.json           # Reportes de calidad
└── final/                        # Datos listos para PostgreSQL

PostgreSQL (base de datos principal):
├── agentes (tabla normalizada)
├── propiedades (con PostGIS)
└── servicios (con índices espaciales)
```

**Ventajas Actuales**:
- Validación estructurada con revisión humana
- Base de datos relacional con integridad ACID
- Índices espaciales para consultas optimizadas
- Performance: milisegundos por consulta geoespacial

### Flujo de Datos Completo
```
Excel RAW (data/raw/)
        ↓
Validación Individual (scripts/validation/)
        ↓
Archivos Intermedios (data/processed/)
        ↓
Revisión Humana (Equipo Citrino)
        ↓
Aprobación (scripts/validation/approve_processed_data.py)
        ↓
Migración PostgreSQL (migration/scripts/)
        ↓
Base de Datos Principal (PostgreSQL + PostGIS)
        ↓
API REST (api/server.py)
```

**Ventajas del Flujo**:
- Datos ORIGINALES siempre preservados en Excel
- Validación estructurada con revisión humana obligatoria
- Base de datos relacional con índices espaciales optimizados
- Trazabilidad completa desde archivo original hasta producción

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

## 🔄 Flujo ETL Completo (Excel RAW → PostgreSQL)

### Fase 1: Validación de Archivos Excel RAW
1. **Procesamiento Individual**: Cada archivo Excel se procesa por separado
2. **Archivos Intermedios**: Se genera Excel con columnas procesadas + reporte JSON
3. **Revisión Humana**: Equipo Citrino valida coordenadas, precios y datos extraídos

```bash
# Ejemplo de procesamiento
python scripts/validation/validate_raw_to_intermediate.py \
  --input "data/raw/relevamiento/2025.08.15 05.xlsx"
```

### Fase 2: Migración a PostgreSQL

#### Paso 2.1: Migrar Agentes (Deduplicación)
```python
# Extraer agentes de archivos procesados
for archivo_procesado in archivos_aprobados:
    df = pd.read_excel(archivo_procesado)
    agentes_unicos.update(df['nombre_agente'].unique())

# Insertar en PostgreSQL con deduplicación
for agente_nombre in agentes_unicos:
    cursor.execute("""
        INSERT INTO agentes (nombre, telefono, email)
        VALUES (%s, %s, %s)
        ON CONFLICT (nombre) DO NOTHING
    """, (agente_nombre, telefono, email))
```

#### Paso 2.2: Migrar Propiedades
```python
# Procesar archivos aprobados
for archivo_aprobado in archivos_aprobados:
    df = pd.read_excel(archivo_aprobado)

    for _, row in df.iterrows():
        # Convertir coordenadas a formato PostGIS
        if pd.notna(row['latitud']) and pd.notna(row['longitud']):
            coords_postgis = f"ST_SetSRID(ST_MakePoint({row['longitud']}, {row['latitud']}), 4326)::geography"

            cursor.execute("""
                INSERT INTO propiedades (
                    agente_id, titulo, tipo_propiedad, precio_usd,
                    direccion, zona, uv, manzana, coordenadas,
                    archivo_origen, fecha_procesamiento
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, {coords_postgis}, %s, %s
                )
            """, (
                agente_map.get(row['nombre_agente']),
                row['titulo'],
                row['tipo_propiedad'],
                row['precio'],
                row['direccion'],
                row['zona'],
                row['uv'],
                row['manzana'],
                archivo_aprobado.name,
                datetime.now()
            ))
```

#### Paso 2.3: Migrar Servicios
```python
# Migrar servicios urbanos desde guía urbana
df_servicios = pd.read_excel('data/raw/guia/GUIA URBANA.xlsx')

for _, row in df_servicios.iterrows():
    if pd.notna(row['latitud']) and pd.notna(row['longitud']):
        coords_postgis = f"ST_SetSRID(ST_MakePoint({row['longitud']}, {row['latitud']}), 4326)::geography"

        cursor.execute("""
            INSERT INTO servicios (nombre, tipo_servicio, coordenadas, direccion)
            VALUES (%s, %s, {coords_postgis}, %s)
        """, (row['nombre'], row['categoria'], row['direccion']))
```

### Fase 3: Validación Post-Migración
```sql
-- Verificar conteos vs archivos procesados
SELECT COUNT(*) FROM propiedades; -- debe coincidir con total archivos aprobados
SELECT COUNT(*) FROM servicios; -- debe coincidir con guía urbana

-- Validar relaciones
SELECT p.titulo, a.nombre, p.archivo_origen
FROM propiedades p
JOIN agentes a ON p.agente_id = a.id
WHERE p.id = 123;

-- Probar consulta geoespacial
SELECT COUNT(*)
FROM propiedades
WHERE ST_DWithin(coordenadas, ST_MakePoint(-63.182, -17.783)::geography, 2000);

-- Verificar trazabilidad
SELECT archivo_origen, COUNT(*) as propiedades_por_archivo
FROM propiedades
GROUP BY archivo_origen
ORDER BY propiedades_por_archivo DESC;
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
1. **Mantener Excel RAW**: Nunca modificar archivos originales en data/raw/
2. **Validación Humana**: Revisión obligatoria antes de migrar a PostgreSQL
3. **Configuración Switchable**: Variable de entorno para cambiar fuente de datos
4. **Ventana de Decisión**: 24-48 horas para validación final
5. **Rollback Instantáneo**: Cambiar configuración y reiniciar aplicación

### Implementación
```python
# config.py
USE_POSTGRES = os.getenv('USE_POSTGRES', 'false').lower() == 'true'

# data_source.py
if USE_POSTGRES:
    from .postgres_source import PostgresDataSource
    data_source = PostgresDataSource()
else:
    from .excel_source import ExcelDataSource  # Carga desde archivos procesados
    data_source = ExcelDataSource()
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
    # Comparar conteos vs archivos procesados
    processed_count = count_approved_properties()
    pg_count = execute_query("SELECT COUNT(*) FROM propiedades")[0][0]
    assert processed_count == pg_count, f"Mismatch: {processed_count} vs {pg_count}"

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

    # Validar trazabilidad
    missing_source = execute_query("""
        SELECT COUNT(*) FROM propiedades
        WHERE archivo_origen IS NULL OR archivo_origen = ''
    """)[0][0]
    assert missing_source == 0, f"Missing source tracking: {missing_source}"
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
    ├── raw/                           # Archivos Excel ORIGINALES (nunca modificados)
    ├── processed/                     # Archivos intermedios para validación
    └── final/                         # Datos aprobados para migración
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
- **ETL Process**: Sistema de validación Excel RAW → PostgreSQL
- **Configuration**: Sistema switching Excel/PostgreSQL

### Beneficios a Largo Plazo
- **Performance**: Mejora exponencial en consultas geoespaciales
- **Scalability**: Preparado para crecimiento 10x
- **Maintainability**: Base de datos relacional vs archivos Excel
- **Analytics**: Capacidades avanzadas de consulta SQL
- **Data Quality**: Validación estructurada con revisión humana obligatoria

---

---

## 🤖 Integración con Chatbot UI (v2.1.0)

### Sistema Conversacional
El chatbot profesional integrado utiliza PostgreSQL como base de datos principal con datos migrados desde archivos Excel RAW:

```python
# api/chatbot_completions.py
class CitrinoChatbotAPI:
    def __init__(self):
        self.propiedades = self._load_properties_from_postgres()
        self.recommendation_engine = RecommendationEnginePostGIS()

    def generate_property_search_response(self, entities):
        # Sistema optimizado con PostGIS
        if self.recommendation_engine:
            recomendaciones = self.recommendation_engine.buscar_propiedades_georreferenciadas(
                criterios, limite=5
            )
```

### Arquitectura de Datos
- **Excel RAW**: Fuente original de datos en data/raw/
- **Validación**: Proceso estructurado con archivos intermedios
- **PostgreSQL**: Base de datos principal con PostGIS
- **API endpoints**: Respuesta en milisegundos con índices espaciales

### Beneficios con PostgreSQL
- **Chatbot response time**: <200ms con consultas PostGIS optimizadas
- **Concurrent users**: Soporte multiusuario sin bloqueos
- **Advanced queries**: Búsqueda geoespacial compleja en tiempo real
- **Data freshness**: Actualizaciones incrementales concurrentes
- **Data quality**: Validación humana obligatoria antes de producción

---

*Última actualización: 2025-10-16*
**Estado actual**: PostgreSQL como base de datos principal, flujo Excel RAW validado