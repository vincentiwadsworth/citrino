# PostgreSQL Technical Deep Dive - Sprint 1 Implementation

##  **Table of Contents**
1. [Architecture Overview](#architecture-overview)
2. [Database Schema Design](#database-schema-design)
3. [ETL Pipeline Architecture](#etl-pipeline-architecture)
4. [Spatial Data Processing](#spatial-data-processing)
5. [Performance Optimizations](#performance-optimizations)
6. [Data Quality Management](#data-quality-management)
7. [Error Handling & Recovery](#error-handling--recovery)
8. [Monitoring & Validation](#monitoring--validation)
9. [Security Considerations](#security-considerations)
10. [Scalability Planning](#scalability-planning)

##  **Architecture Overview**

### **System Design Principles**
1. **Separation of Concerns**: Each ETL component has a single responsibility
2. **Data Provenance**: Complete audit trail from source to destination
3. **Graceful Degradation**: System continues operating even with partial failures
4. **Human-in-the-Loop**: Critical validation steps require human review
5. **Incremental Processing**: Supports partial updates and delta processing

### **Component Interaction**
```
        
   Raw Excel           Intermediate          PostgreSQL     
   Files            Excel Files      + PostGIS     
                       (Human Review)                      
        
                                                      
                                                      
        
   Error Logs           Validation           Spatial       
   + Backups            Reports              Indexes       
        
```

##  **Database Schema Design**

### **PostgreSQL Version Requirements**
- **PostgreSQL**: 15.0+ (for performance improvements)
- **PostGIS**: 3.3.0+ (for enhanced spatial functions)
- **Recommended RAM**: 4GB+ (for spatial operations)
- **Storage**: SSD preferred (for spatial index performance)

### **Table Design Philosophy**

#### **1. agentes (Agents)**
```sql
CREATE TABLE agentes (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    telefono VARCHAR(50),
    email VARCHAR(255) UNIQUE,
    empresa VARCHAR(100),
    fecha_registro TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT uq_agente_nombre UNIQUE (nombre),
    CONSTRAINT uq_agente_email UNIQUE (email)
);
```

**Design Decisions:**
- `BIGSERIAL` for scalability (billions of potential agents)
- Unique constraints on `nombre` and `email` for deduplication
- `TIMESTAMPTZ` for accurate timezone handling
- Simple structure focused on contact information

#### **2. propiedades (Properties)**
```sql
CREATE TABLE propiedades (
    id BIGSERIAL PRIMARY KEY,
    agente_id BIGINT REFERENCES agentes(id) ON DELETE SET NULL,

    -- Core property information
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    tipo_propiedad VARCHAR(100),
    estado_propiedad VARCHAR(50),

    -- Financial information
    precio_usd NUMERIC(12, 2),
    precio_usd_m2 NUMERIC(10, 2),
    moneda VARCHAR(10) DEFAULT 'USD',

    -- Location information
    direccion TEXT,
    zona VARCHAR(100),
    uv VARCHAR(50),
    manzana VARCHAR(50),
    lote VARCHAR(50),

    -- Property specifications
    superficie_total NUMERIC(10, 2),
    superficie_construida NUMERIC(10, 2),
    num_dormitorios INTEGER,
    num_banos INTEGER,
    num_garajes INTEGER,

    -- Spatial data
    coordenadas GEOGRAPHY(POINT, 4326),

    -- Metadata
    fecha_publicacion TIMESTAMPTZ,
    fecha_scraping TIMESTAMPTZ DEFAULT now(),
    ultima_actualizacion TIMESTAMPTZ DEFAULT now(),
    proveedor_datos VARCHAR(100),
    codigo_proveedor VARCHAR(100),
    url_origen TEXT,

    -- Data quality flags
    coordenadas_validas BOOLEAN DEFAULT false,
    datos_completos BOOLEAN DEFAULT false
);
```

**Design Decisions:**
- `GEOGRAPHY(POINT, 4326)` for accurate Earth-curvature calculations
- `NUMERIC(12, 2)` for precise financial calculations
- Separate `precio_usd` and `precio_usd_m2` for different analysis needs
- Quality flags (`coordenadas_validas`, `datos_completos`) for filtering
- Comprehensive metadata for data provenance

#### **3. servicios (Services)**
```sql
CREATE TABLE servicios (
    id BIGSERIAL PRIMARY KEY,

    -- Service information
    nombre VARCHAR(255) NOT NULL,
    tipo_servicio VARCHAR(100),
    subtipo_servicio VARCHAR(100),

    -- Location information
    direccion TEXT,
    zona VARCHAR(100),

    -- Spatial data
    coordenadas GEOGRAPHY(POINT, 4326),

    -- Contact information
    telefono VARCHAR(50),
    horario TEXT,

    -- Metadata
    fuente_datos VARCHAR(100),
    fecha_registro TIMESTAMPTZ DEFAULT now(),

    -- Data quality flags
    coordenadas_validas BOOLEAN DEFAULT false
);
```

### **Indexing Strategy**

#### **Spatial Indexes**
```sql
-- Primary spatial indexes
CREATE INDEX idx_propiedades_coordenadas ON propiedades USING GIST (coordenadas);
CREATE INDEX idx_servicios_coordenadas ON servicios USING GIST (coordenadas);
```

**Rationale:**
- GIST (Generalized Search Tree) optimized for spatial data
- Supports `ST_DWithin`, `ST_Intersects`, `ST_Distance` operations
- Automatic R-tree indexing for point data

#### **Composite Indexes**
```sql
-- Query optimization indexes
CREATE INDEX idx_propiedades_zona_precio ON propiedades (zona, precio_usd);
CREATE INDEX idx_propiedades_tipo_zona ON propiedades (tipo_propiedad, zona);
CREATE INDEX idx_propiedades_precio_usd ON propiedades (precio_usd) WHERE precio_usd IS NOT NULL;
CREATE INDEX idx_servicios_tipo_zona ON servicios (tipo_servicio, zona);
CREATE INDEX idx_propiedades_coordenadas_validas ON propiedades (coordenadas_validas) WHERE coordenadas_validas = true;
```

**Rationale:**
- Multi-column indexes for common query patterns
- Partial indexes for frequently filtered data
- Covers most common search scenarios

### **Advanced Database Features**

#### **Triggers for Data Validation**
```sql
-- Coordinate validation trigger
CREATE OR REPLACE FUNCTION validar_coordenadas_trigger()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.coordenadas IS NOT NULL THEN
        NEW.coordenadas_validas = validar_coordenadas_santa_cruz(
            ST_Y(NEW.coordenadas),
            ST_X(NEW.coordenadas)
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Auto-update timestamp trigger
CREATE OR REPLACE FUNCTION actualizar_timestamp_propiedad()
RETURNS TRIGGER AS $$
BEGIN
    NEW.ultima_actualizacion = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

#### **Custom Functions**
```sql
-- Distance calculation function
CREATE OR REPLACE FUNCTION calcular_distancia_metros(
    lat1 NUMERIC, lon1 NUMERIC,
    lat2 NUMERIC, lon2 NUMERIC
) RETURNS NUMERIC AS $$
BEGIN
    RETURN ST_Distance(
        ST_GeographyFromText('SRID=4326;POINT(' || lon1 || ' ' || lat1 || ')'),
        ST_GeographyFromText('SRID=4326;POINT(' || lon2 || ' ' || lat2 || ')')
    );
END;
$$ LANGUAGE plpgsql;
```

#### **Materialized Views for Analytics**
```sql
CREATE MATERIALIZED VIEW cobertura_servicios_zona AS
SELECT
    p.zona,
    COUNT(*) as total_propiedades,
    COUNT(*) FILTER (WHERE p.coordenadas_validas = true) as propiedades_con_coordenadas,
    COUNT(DISTINCT s.id) as servicios_cercanos_500m,
    ROUND(AVG(p.precio_usd)) as precio_promedio_zona
FROM propiedades p
LEFT JOIN servicios s ON ST_DWithin(p.coordenadas, s.coordenadas, 500)
WHERE p.coordenadas_validas = true
GROUP BY p.zona;

-- Refresh strategy
CREATE OR REPLACE FUNCTION refrescar_vistas_analiticas()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY cobertura_servicios_zona;
END;
$$ LANGUAGE plpgsql;
```

##  **ETL Pipeline Architecture**

### **Phase 1: Excel Processing**

#### **etl_excel_to_intermediate.py**
**Core Responsibilities:**
1. **Data Extraction**: Read raw Excel files from multiple sources
2. **Coordinate Detection**: Regex patterns for latitude/longitude extraction
3. **Data Normalization**: Standardize text, numbers, dates
4. **Quality Assessment**: Flag incomplete or invalid records
5. **Multi-sheet Output**: Generate structured Excel for human review

**Key Algorithms:**

**Coordinate Extraction:**
```python
def extraer_coordenadas(self, texto: str) -> Optional[Tuple[float, float]]:
    """Extract coordinates from free text using multiple patterns."""
    patterns = [
        r'(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)',  # lat,lon or lat lon
        r'lat[:\s]+(-?\d+\.?\d*)[,\s]+lon[:\s]+(-?\d+\.?\d*)',  # lat: X, lon: Y
        r'[-+]?\d{1,3}\.\d{6}[,/\s]+[-+]?\d{1,3}\.\d{6}',  # Decimal coordinates
    ]

    for pattern in patterns:
        match = re.search(pattern, texto.lower())
        if match:
            lat, lon = float(match.group(1)), float(match.group(2))
            if self._validate_santa_cruz_bounds(lat, lon):
                return (lat, lon)
    return None
```

**Price Validation:**
```python
def validar_precio(self, texto: str) -> Optional[float]:
    """Extract and validate price in USD."""
    numeros = re.findall(r'\d+', str(texto).lower().replace('$', '').replace(',', ''))
    if numeros:
        precio = float(numeros[0])
        if 1000 <= precio <= 10000000:  # Reasonable range for Santa Cruz
            return precio
    return None
```

**Quality Metrics Calculation:**
```python
def calcular_calidad_datos(self, propiedad: Dict) -> Dict:
    """Calculate data quality score for each property."""
    score = 0
    max_score = 100

    # Title quality (20 points)
    if propiedad['titulo'] and len(propiedad['titulo']) > 10:
        score += 20

    # Price quality (25 points)
    if propiedad['precio_usd']:
        score += 25

    # Coordinates quality (30 points)
    if propiedad['coordenadas_validas']:
        score += 30

    # Location quality (15 points)
    if propiedad['zona'] and propiedad['direccion']:
        score += 15

    # Specifications quality (10 points)
    if propiedad['superficie_total'] or propiedad['num_dormitorios']:
        score += 10

    return {
        'score': score,
        'max_score': max_score,
        'percentage': round(score / max_score * 100, 2)
    }
```

#### **etl_guia_to_intermediate.py**
**Service Classification Algorithm:**
```python
def clasificar_servicio(self, nombre: str, descripcion: str = "") -> Tuple[str, str]:
    """Classify service using keyword matching and context."""
    texto_completo = f"{nombre} {descripcion}".lower()

    for tipo_servicio, config in self.CLASIFICACION_SERVICIOS.items():
        # Primary category matching
        if any(palabra in texto_completo for palabra in config['palabras_clave']):
            # Subtype refinement
            for subtipo, palabras_subtipo in config['subtipos'].items():
                if any(palabra_sub in texto_completo for palabra_sub in palabras_subtipo):
                    return (tipo_servicio, subtipo)
            return (tipo_servicio, tipo_servicio)

    return ('Otros', 'No Clasificado')
```

**Service Categories:**
- **Educación**: Colegios, universidades, academias, bibliotecas
- **Salud**: Hospitales, clínicas, farmacias, laboratorios
- **Comercio**: Supermercados, tiendas, mercados, centros comerciales
- **Servicios**: Bancos, oficinas gubernamentales, servicios privados
- **Transporte**: Terminales, paradas de bus, servicios taxi
- **Recreación**: Parques, plazas, centros deportivos

### **Phase 2: Data Consolidation**

#### **etl_consolidar_agentes.py**
**Deduplication Algorithm:**
```python
def son_mismo_agente(self, agente1: Dict, agente2: Dict) -> bool:
    """Determine if two records represent the same agent using multiple criteria."""

    # 1. Exact email match (strongest signal)
    if agente1['email'] and agente2['email'] and agente1['email'] == agente2['email']:
        return True

    # 2. Exact phone match
    if agente1['telefono'] and agente2['telefono'] and agente1['telefono'] == agente2['telefono']:
        return True

    # 3. Similar name + contact info
    if agente1['nombre'] and agente2['nombre']:
        similarity = self.similitud_nombres(agente1['nombre'], agente2['nombre'])

        if similarity > 0.8:  # High name similarity
            if (agente1['email'] and agente2['email']) or (agente1['telefono'] and agente2['telefono']):
                return True

        if similarity > 0.95:  # Very high name similarity
            return True

    # 4. Similar name + same company
    if (agente1['nombre'] and agente2['nombre'] and
        agente1['empresa'] and agente2['empresa'] and
        agente1['empresa'] == agente2['empresa']):
        if self.similitud_nombres(agente1['nombre'], agente2['nombre']) > 0.7:
            return True

    return False
```

**Information Consolidation:**
```python
def consolidar_informacion_agente(self, agentes_grupo: List[Dict]) -> Dict:
    """Merge information from multiple agent records."""
    # Sort by completeness
    agentes_prioridad = sorted(agentes_grupo,
        key=lambda x: sum([
            1 if x['nombre'] and len(x['nombre']) > 5 else 0,
            1 if x['email'] else 0,
            1 if x['telefono'] else 0,
            1 if x['empresa'] and len(x['empresa']) > 3 else 0
        ]),
        reverse=True
    )

    agente_base = agentes_prioridad[0].copy()

    # Fill gaps from other records
    for agente in agentes_prioridad[1:]:
        if not agente_base['email'] and agente['email']:
            agente_base['email'] = agente['email']
        if not agente_base['telefono'] and agente['telefono']:
            agente_base['telefono'] = agente['telefono']
        if not agente_base['empresa'] and agente['empresa']:
            agente_base['empresa'] = agente['empresa']

    return agente_base
```

### **Phase 3: PostgreSQL Loading**

#### **etl_intermediate_to_postgres.py**
**Batch Processing Strategy:**
```python
def cargar_propiedades_por_lote(self, propiedades: List[Dict], batch_size: int = 1000):
    """Load properties in batches for better performance."""
    for i in range(0, len(propiedades), batch_size):
        lote = propiedades[i:i + batch_size]
        try:
            self._procesar_lote_propiedades(lote)
            self.connection.commit()
            logger.info(f"Lote {i//batch_size + 1} cargado: {len(lote)} propiedades")
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error en lote {i//batch_size + 1}: {e}")
            raise

def _procesar_lote_propiedades(self, lote: List[Dict]):
    """Process a single batch of properties."""
    values = []
    for prop in lote:
        # Convert to PostGIS format
        coordenadas_postgis = None
        if prop.get('coordenadas_validas'):
            coordenadas_postgis = f"ST_GeographyFromText('SRID=4326;POINT({prop['longitud']} {prop['latitud']})')"

        values.append((
            prop['titulo'], prop['descripcion'], prop['tipo_propiedad'],
            prop['precio_usd'], prop['direccion'], prop['zona'],
            coordenadas_postgis, prop['coordenadas_validas']
        ))

    # Execute batch insert
    query = """
    INSERT INTO propiedades (titulo, descripcion, tipo_propiedad, precio_usd,
                           direccion, zona, coordenadas, coordenadas_validas)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    with self.connection.cursor() as cursor:
        cursor.executemany(query, values)
```

**Backup Strategy:**
```python
def crear_respaldo_tabla(self, nombre_tabla: str) -> str:
    """Create table backup before migration."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"backup_{nombre_tabla}_{timestamp}.sql"
    backup_path = self.backups_dir / backup_filename

    # Export data as INSERT statements
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(f"-- Backup of table {nombre_tabla}\n")
        f.write(f"-- Generated: {datetime.now()}\n\n")

        with self.connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {nombre_tabla}")
            rows = cursor.fetchall()

            for row in rows:
                values = ', '.join([f"'{str(v).replace(\"'\", \"''\")}'" if v is not None else 'NULL' for v in row])
                f.write(f"INSERT INTO {nombre_tabla} VALUES ({values});\n")

    return str(backup_path)
```

##  **Spatial Data Processing**

### **Coordinate Validation**
```python
def validar_coordenadas_santa_cruz(self, lat: float, lon: float) -> bool:
    """Validate coordinates within Santa Cruz de la Sierra bounds."""
    SANTA_CRUZ_BOUNDS = {
        'lat_min': -18.5, 'lat_max': -17.5,  # Latitude bounds
        'lon_min': -63.5, 'lon_max': -63.0   # Longitude bounds
    }

    return (SANTA_CRUZ_BOUNDS['lat_min'] <= lat <= SANTA_CRUZ_BOUNDS['lat_max'] and
            SANTA_CRUZ_BOUNDS['lon_min'] <= lon <= SANTA_CRUZ_BOUNDS['lon_max'])
```

### **Spatial Index Performance**
```sql
-- Analyze spatial index performance
EXPLAIN ANALYZE
SELECT p.titulo, s.nombre
FROM propiedades p
JOIN servicios s ON ST_DWithin(p.coordenadas, s.coordenadas, 500)
WHERE p.coordenadas_validas = true;

-- Expected: Index Scan using idx_propiedades_coordenadas (cost=0.00..100.00)
```

### **Advanced Spatial Queries**

#### **Service Coverage Analysis**
```sql
-- Find areas with low service coverage
WITH cobertura AS (
    SELECT
        p.zona,
        COUNT(*) as total_propiedades,
        COUNT(DISTINCT s.id) as servicios_cercanos,
        COUNT(DISTINCT CASE WHEN s.tipo_servicio = 'Educación' THEN s.id END) as centros_educativos,
        COUNT(DISTINCT CASE WHEN s.tipo_servicio = 'Salud' THEN s.id END) as centros_salud
    FROM propiedades p
    LEFT JOIN servicios s ON ST_DWithin(p.coordenadas, s.coordenadas, 1000)  -- 1km radius
    WHERE p.coordenadas_validas = true
    GROUP BY p.zona
)
SELECT zona, total_propiedades, servicios_cercanos,
       CASE
           WHEN servicios_cercanos < 5 THEN 'Baja cobertura'
           WHEN servicios_cercenos < 15 THEN 'Cobertura media'
           ELSE 'Buena cobertura'
       END as nivel_cobertura
FROM cobertura
ORDER BY servicios_cercanos ASC;
```

#### **Property Valuation Analysis**
```sql
-- Spatial correlation analysis for property pricing
WITH estadisticas_zona AS (
    SELECT
        p.zona,
        AVG(p.precio_usd) as precio_promedio,
        STDDEV(p.precio_usd) as desviacion_precio,
        COUNT(DISTINCT s.id) as densidad_servicios,
        AVG(ST_Distance(p.coordenadas, s.coordenadas)) as distancia_promedio_servicios
    FROM propiedades p
    LEFT JOIN servicios s ON ST_DWithin(p.coordenadas, s.coordenadas, 2000)
    WHERE p.coordenadas_validas = true AND p.precio_usd IS NOT NULL
    GROUP BY p.zona
)
SELECT zona, precio_promedio, desviacion_precio,
       ROUND(precio_promedio / desviacion_precio, 2) as indice_variabilidad,
       densidad_servicios
FROM estadisticas_zona
WHERE desviacion_precio IS NOT NULL
ORDER BY indice_variabilidad DESC;
```

##  **Performance Optimizations**

### **PostgreSQL Configuration**
```sql
-- postgresql.conf optimizations for spatial workloads
shared_buffers = 256MB                    -- 25% of RAM
effective_cache_size = 1GB                -- 75% of RAM
maintenance_work_mem = 64MB               -- For index creation
checkpoint_completion_target = 0.9        -- Smooth checkpoints
wal_buffers = 16MB                        -- WAL configuration
default_statistics_target = 100           -- Better query planning
random_page_cost = 1.1                    -- SSD optimization
effective_io_concurrency = 200            -- Parallel IO capacity

-- PostGIS-specific optimizations
postgis.enable_outdb_rasters = on         -- External raster support
postgis.gdal_enabled_drivers = 'ENABLE_ALL'  -- GDAL drivers
```

### **Query Optimization**

#### **Spatial Query Patterns**
```sql
-- Efficient spatial query pattern
EXPLAIN (ANALYZE, BUFFERS)
SELECT p.titulo, p.precio_usd
FROM propiedades p
WHERE p.coordenadas_validas = true
  AND ST_DWithin(
      p.coordenadas,
      ST_GeographyFromText('SRID=4326;POINT(-63.1918 -17.7854)'),  -- Santa Cruz center
      5000  -- 5km radius
  )
ORDER BY p.precio_usd
LIMIT 10;

-- Uses: Index Scan using idx_propiedades_coordenadas
-- Cost: Much lower with spatial index
```

#### **Batch Processing Optimization**
```python
def optimized_batch_insert(self, records: List[Dict], batch_size: int = 1000):
    """Optimized batch insert with prepared statements."""
    # Prepare statement once
    insert_query = """
    INSERT INTO propiedades (titulo, precio_usd, coordenadas, zona)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (codigo_proveedor) DO UPDATE SET
        titulo = EXCLUDED.titulo,
        precio_usd = EXCLUDED.precio_usd,
        ultima_actualizacion = now()
    """

    # Process in batches
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        values = [
            (r['titulo'], r['precio_usd'], r['coordenadas'], r['zona'])
            for r in batch
        ]

        with self.connection.cursor() as cursor:
            cursor.executemany(insert_query, values)

        self.connection.commit()
        logger.info(f"Batch {i//batch_size + 1}: {len(batch)} records")
```

### **Memory Management**
```python
def memory_efficient_processing(self, file_path: str):
    """Process large Excel files with minimal memory footprint."""
    # Use chunked reading for large files
    chunk_size = 1000

    for chunk in pd.read_excel(file_path, chunksize=chunk_size):
        # Process chunk
        processed_chunk = self.process_chunk(chunk)

        # Insert immediately, don't accumulate
        self.insert_chunk(processed_chunk)

        # Clear memory
        del chunk, processed_chunk
        gc.collect()  # Force garbage collection
```

##  **Data Quality Management**

### **Quality Metrics Framework**
```python
class DataQualityManager:
    def __init__(self):
        self.quality_metrics = {
            'completitud': self._medir_completitud,
            'precision': self._medir_precision,
            'consistencia': self._medir_consistencia,
            'validez': self._medir_validez
        }

    def evaluar_calidad_dataset(self, datos: List[Dict]) -> Dict:
        """Comprehensive data quality assessment."""
        resultados = {}

        for metrica, funcion in self.quality_metrics.items():
            resultados[metrica] = funcion(datos)

        # Calculate overall score
        resultado_global = sum(resultados.values()) / len(resultados)
        resultados['puntaje_global'] = round(resultado_global, 2)

        return resultados

    def _medir_completitud(self, datos: List[Dict]) -> float:
        """Measure data completeness."""
        campos_criticos = ['titulo', 'precio_usd', 'zona', 'coordenadas_validas']

        total_campos = len(datos) * len(campos_criticos)
        campos_completos = sum(
            1 for registro in datos
            for campo in campos_criticos
            if registro.get(campo) not in [None, '', False]
        )

        return (campos_completos / total_campos) * 100 if total_campos > 0 else 0

    def _medir_precision(self, datos: List[Dict]) -> float:
        """Measure coordinate precision."""
        registros_con_coords = [
            r for r in datos
            if r.get('coordenadas_validas', False)
        ]

        if not registros_con_coords:
            return 0

        # Check decimal precision (should have at least 6 decimal places)
        precision_aceptable = sum(
            1 for r in registros_con_coords
            if self._tiene_precision_geografica(r)
        )

        return (precision_aceptable / len(registros_con_coords)) * 100
```

### **Anomaly Detection**
```python
def detectar_anomalias_precio(self, datos: List[Dict]) -> List[Dict]:
    """Detect price anomalies using statistical methods."""
    precios = [r['precio_usd'] for r in datos if r.get('precio_usd')]

    if not precios:
        return []

    # Calculate statistics
    q1 = np.percentile(precios, 25)
    q3 = np.percentile(precios, 75)
    iqr = q3 - q1

    # Define anomaly thresholds
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    anomalias = []
    for registro in datos:
        precio = registro.get('precio_usd')
        if precio and (precio < lower_bound or precio > upper_bound):
            anomalias.append({
                **registro,
                'anomalia_tipo': 'precio_atipico',
                'motivo': f'Precio {precio} fuera de rango [{lower_bound:.0f}, {upper_bound:.0f}]'
            })

    return anomalias
```

##  **Error Handling & Recovery**

### **Comprehensive Error Logging**
```python
class MigrationLogger:
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.error_categories = {
            'data_validation': [],
            'database_connection': [],
            'file_processing': [],
            'spatial_operations': []
        }

    def log_error(self, error_type: str, error_details: Dict):
        """Structured error logging with categorization."""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'severity': error_details.get('severity', 'medium'),
            'description': error_details.get('description', ''),
            'context': error_details.get('context', {}),
            'recovery_action': error_details.get('recovery_action', '')
        }

        self.error_categories[error_type].append(error_entry)

        # Log to file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(error_entry, ensure_ascii=False) + '\n')

    def generate_error_report(self) -> Dict:
        """Generate comprehensive error analysis."""
        report = {
            'total_errors': sum(len(errors) for errors in self.error_categories.values()),
            'errors_by_category': {
                category: len(errors)
                for category, errors in self.error_categories.items()
            },
            'critical_errors': [
                error for errors in self.error_categories.values()
                for error in errors
                if error['severity'] == 'critical'
            ],
            'recovery_recommendations': self._generate_recovery_recommendations()
        }

        return report
```

### **Automatic Recovery Mechanisms**
```python
class RecoveryManager:
    def __init__(self, connection):
        self.connection = connection

    def recuperar_de_error_transaccional(self, error_info: Dict):
        """Recover from transactional errors."""
        error_type = error_info.get('error_type')

        if error_type == 'constraint_violation':
            self._manejar_violacion_constraint(error_info)
        elif error_type == 'connection_timeout':
            self._manejar_timeout_conexion(error_info)
        elif error_type == 'disk_space':
            self._manejar_espacio_disco(error_info)

    def _manejar_violacion_constraint(self, error_info: Dict):
        """Handle constraint violations with data correction."""
        # Identify problematic records
        problematic_records = error_info.get('problematic_records', [])

        for record in problematic_records:
            # Try to correct the data
            corrected_record = self._correger_registro(record)
            if corrected_record:
                # Retry insertion with corrected data
                self._reintentar_insercion(correged_record)
            else:
                # Log for manual review
                self._log_para_revision_manual(record)
```

##  **Monitoring & Validation**

### **Real-time Monitoring**
```python
class MigrationMonitor:
    def __init__(self):
        self.metrics = {
            'records_processed': 0,
            'records_successful': 0,
            'records_failed': 0,
            'processing_rate': 0,
            'error_rate': 0,
            'memory_usage': 0
        }
        self.start_time = time.time()

    def update_metrics(self, processed: int, successful: int, failed: int):
        """Update monitoring metrics."""
        self.metrics['records_processed'] += processed
        self.metrics['records_successful'] += successful
        self.metrics['records_failed'] += failed

        elapsed_time = time.time() - self.start_time
        self.metrics['processing_rate'] = self.metrics['records_processed'] / elapsed_time
        self.metrics['error_rate'] = (self.metrics['records_failed'] /
                                    self.metrics['records_processed']) * 100

        # Memory usage
        import psutil
        process = psutil.Process()
        self.metrics['memory_usage'] = process.memory_info().rss / 1024 / 1024  # MB

    def get_health_status(self) -> str:
        """Determine overall health status."""
        if self.metrics['error_rate'] > 10:
            return 'CRITICAL'
        elif self.metrics['error_rate'] > 5:
            return 'WARNING'
        elif self.metrics['processing_rate'] < 10:  # records per second
            return 'SLOW'
        else:
            return 'HEALTHY'
```

### **Comprehensive Validation**
```python
class MigrationValidator:
    def validar_integridad_completa(self) -> Dict:
        """Complete post-migration validation."""
        validaciones = {
            'conteo_registros': self._validar_conteos(),
            'integridad_espacial': self._validar_datos_espaciales(),
            'relaciones_referenciales': self._validar_relaciones(),
            'calidad_datos': self._validar_calidad_datos(),
            'performance_consultas': self._validar_rendimiento()
        }

        # Calculate overall score
        puntuacion_total = sum(
            v.get('puntuacion', 0) for v in validaciones.values()
        ) / len(validaciones)

        validaciones['puntuacion_global'] = round(puntuacion_total, 2)
        validaciones['estado_general'] = self._determinar_estado(puntuacion_total)

        return validaciones

    def _validar_rendimiento(self) -> Dict:
        """Validate query performance."""
        pruebas_rendimiento = [
            self._probar_consulta_espacial(),
            self._probar_busqueda_zona(),
            self._probar_analisis_agrupado()
        ]

        tiempo_promedio = sum(p['tiempo'] for p in pruebas_rendimiento) / len(pruebas_rendimiento)

        return {
            'tiempo_promedio_consultas': round(tiempo_promedio, 3),
            'pruebas_detalle': pruebas_rendimiento,
            'puntuacion': max(0, 100 - (tiempo_promedio * 10))  # Penalty for slow queries
        }
```

##  **Security Considerations**

### **Database Security**
```sql
-- Create dedicated migration user
CREATE ROLE citrino_migration WITH LOGIN PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE citrino TO citrino_migration;
GRANT USAGE ON SCHEMA public TO citrino_migration;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO citrino_migration;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO citrino_migration;

-- Row Level Security (optional)
ALTER TABLE propiedades ENABLE ROW LEVEL SECURITY;
CREATE POLICY citrino_policy ON propiedades
    FOR ALL TO citrino_migration
    USING (proveedor_datos = ANY(ARRAY['excel_validado', 'gui_urbana']));
```

### **Data Encryption**
```python
class SecureDataHandler:
    def __init__(self, encryption_key: str):
        from cryptography.fernet import Fernet
        self.cipher_suite = Fernet(encryption_key.encode())

    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive information like emails, phones."""
        if not data:
            return data

        encrypted_data = self.cipher_suite.encrypt(data.encode())
        return encrypted_data.decode()

    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive information."""
        if not encrypted_data:
            return encrypted_data

        decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode())
        return decrypted_data.decode()
```

##  **Scalability Planning**

### **Horizontal Scaling Preparation**
```sql
-- Partitioning strategy for large datasets
CREATE TABLE propiedades_partitioned (
    LIKE propiedades INCLUDING ALL
) PARTITION BY RANGE (fecha_scraping);

-- Monthly partitions
CREATE TABLE propiedades_2025_01 PARTITION OF propiedades_partitioned
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE propiedades_2025_02 PARTITION OF propiedades_partitioned
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
```

### **Connection Pooling Configuration**
```python
# Connection pool for high-load scenarios
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    'postgresql://user:password@localhost/citrino',
    poolclass=QueuePool,
    pool_size=20,              # Number of connections to maintain
    max_overflow=30,           # Additional connections under load
    pool_timeout=30,           # Wait time for connection
    pool_recycle=3600,         # Recycle connections every hour
    pool_pre_ping=True         # Validate connections before use
)
```

### **Caching Strategy**
```python
import redis
from functools import wraps

class SpatialQueryCache:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis_client = redis.StrictRedis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )
        self.cache_ttl = 3600  # 1 hour

    def cache_spatial_query(self):
        """Decorator for caching spatial query results."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_cache_key(func.__name__, args, kwargs)

                # Try to get from cache
                cached_result = self.redis_client.get(cache_key)
                if cached_result:
                    return json.loads(cached_result)

                # Execute query and cache result
                result = func(*args, **kwargs)
                self.redis_client.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps(result, default=str)
                )

                return result
            return wrapper
        return decorator

    @cache_spatial_query()
    def buscar_propiedades_cercanas(self, lat: float, lon: float, radio: int):
        """Cached spatial search query."""
        # Implementation here
        pass
```

##  **Performance Benchmarks**

### **Expected Performance Improvements**
| Operation | Current (JSON) | Target (PostgreSQL) | Improvement |
|-----------|----------------|-------------------|-------------|
| Spatial Search (500m) | 5-10 seconds | <100ms | 50-100x |
| Zone-based Query | 2-3 seconds | <50ms | 40-60x |
| Coverage Analysis | 15-30 seconds | <500ms | 30-60x |
| Concurrent Users | 1 | 100+ | 100x+ |

### **Benchmark Queries**
```sql
-- Benchmark 1: Spatial proximity search
EXPLAIN ANALYZE
SELECT COUNT(*)
FROM propiedades p
JOIN servicios s ON ST_DWithin(p.coordenadas, s.coordenadas, 500)
WHERE s.tipo_servicio = 'Educación'
  AND p.coordenadas_validas = true;

-- Expected: <50ms with spatial index

-- Benchmark 2: Aggregated spatial analysis
EXPLAIN ANALYZE
SELECT
    p.zona,
    COUNT(*) as total_propiedades,
    COUNT(DISTINCT s.id) as servicios_cercanos,
    AVG(p.precio_usd) as precio_promedio
FROM propiedades p
LEFT JOIN servicios s ON ST_DWithin(p.coordenadas, s.coordenadas, 1000)
WHERE p.zona IS NOT NULL
GROUP BY p.zona
ORDER BY total_propiedades DESC;

-- Expected: <200ms for 10 zones
```

---

##  **Implementation Checklist**

### **Pre-Migration**
- [ ] PostgreSQL 15+ installed with PostGIS 3.3+
- [ ] Database created with proper configuration
- [ ] Backup strategy implemented
- [ ] Connection security configured
- [ ] Performance tuning applied

### **Migration Execution**
- [ ] Raw Excel files validated
- [ ] ETL scripts tested with sample data
- [ ] Error handling verified
- [ ] Monitoring systems active
- [ ] Rollback procedures ready

### **Post-Migration**
- [ ] Data integrity validated
- [ ] Performance benchmarks met
- [ ] Security audit completed
- [ ] Documentation updated
- [ ] Team training completed

### **Monitoring & Maintenance**
- [ ] Automated health checks
- [ ] Performance monitoring dashboards
- [ ] Regular backup schedules
- [ ] Index maintenance procedures
- [ ] Capacity planning established

This technical deep dive provides the foundation for a robust, scalable, and maintainable PostgreSQL migration that will support Citrino's growth and advanced spatial analysis requirements for years to come.