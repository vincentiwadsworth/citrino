-- =====================================================
-- Performance Indexes for Citrino PostgreSQL Database
-- Optimized for geospatial queries and business operations
-- =====================================================

-- =====================================================
-- CRITICAL: GIST Spatial Indexes for PostGIS
-- These enable fast geospatial queries (milliseconds vs seconds)
-- =====================================================

-- Primary spatial index for properties (most critical for performance)
CREATE INDEX IF NOT EXISTS idx_propiedades_coordenadas
ON propiedades USING GIST (coordenadas);

-- Spatial index for services/points of interest
CREATE INDEX IF NOT EXISTS idx_servicios_coordenadas
ON servicios USING GIST (coordenadas);

-- =====================================================
-- B-Tree Indexes for Common Query Filters
-- =====================================================

-- Property search indexes
CREATE INDEX IF NOT EXISTS idx_propiedades_precio
ON propiedades (precio_usd) WHERE precio_usd IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_propiedades_tipo
ON propiedades (tipo_propiedad) WHERE tipo_propiedad IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_propiedades_zona
ON propiedades (zona) WHERE zona IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_propiedades_estado
ON propiedades (estado_propiedad) WHERE estado_propiedad IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_propiedades_proveedor
ON propiedades (proveedor_datos) WHERE proveedor_datos IS NOT NULL;

-- Composite indexes for common search patterns
CREATE INDEX IF NOT EXISTS idx_propiedades_zona_precio_tipo
ON propiedades (zona, precio_usd, tipo_propiedad)
WHERE zona IS NOT NULL AND precio_usd IS NOT NULL AND tipo_propiedad IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_propiedades_dormitorios_banos
ON propiedades (num_dormitorios, num_banos)
WHERE num_dormitorios IS NOT NULL AND num_banos IS NOT NULL;

-- =====================================================
-- Foreign Key Indexes (automatically created by PostgreSQL in most cases)
-- =====================================================

-- Agent relationship index
CREATE INDEX IF NOT EXISTS idx_propiedades_agente_id
ON propiedades (agente_id) WHERE agente_id IS NOT NULL;

-- =====================================================
-- Services Indexes
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_servicios_tipo
ON servicios (tipo_servicio) WHERE tipo_servicio IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_servicios_zona
ON servicios (zona) WHERE zona IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_servicios_tipo_zona
ON servicios (tipo_servicio, zona)
WHERE tipo_servicio IS NOT NULL AND zona IS NOT NULL;

-- =====================================================
-- Metadata and Time-based Indexes
-- =====================================================

-- For tracking data freshness and updates
CREATE INDEX IF NOT EXISTS idx_propiedades_fecha_actualizacion
ON propiedades (ultima_actualizacion);

CREATE INDEX IF NOT EXISTS idx_propiedades_fecha_publicacion
ON propiedades (fecha_publicacion) WHERE fecha_publicacion IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_servicios_fecha_registro
ON servicios (fecha_registro);

-- For migration tracking
CREATE INDEX IF NOT EXISTS idx_migration_log_fecha
ON migration_log (fecha_ejecucion);

CREATE INDEX IF NOT EXISTS idx_migration_log_tabla
ON migration_log (tabla_migrada);

-- =====================================================
-- Partial Indexes for Quality Control
-- =====================================================

-- Only index valid coordinates (for spatial queries)
CREATE INDEX IF NOT EXISTS idx_propiedades_coordenadas_validas
ON propiedades USING GIST (coordenadas)
WHERE coordenadas_validas = true;

CREATE INDEX IF NOT EXISTS idx_servicios_coordenadas_validas
ON servicios USING GIST (coordenadas)
WHERE coordenadas_validas = true;

-- Index for complete data sets (used in analytics)
CREATE INDEX IF NOT EXISTS idx_propiedades_datos_completos
ON propiedades (zona, precio_usd, tipo_propiedad)
WHERE datos_completos = true AND coordenadas_validas = true;

-- =====================================================
-- Specialized Indexes for Common Business Queries
-- =====================================================

-- Index for price range searches (common in property recommendations)
CREATE INDEX IF NOT EXISTS idx_propiedades_precio_rango
ON propiedades (precio_usd)
WHERE precio_usd BETWEEN 50000 AND 1000000;

-- Index for specific zones (Santa Cruz de la Sierra key areas)
CREATE INDEX IF NOT EXISTS idx_propiedades_zonas_principales
ON propiedades (zona, precio_usd, tipo_propiedad)
WHERE zona IN ('Equipetrol', 'Santa Mónica', 'Pampa de la Isla', 'Urbari', 'Sarco');

-- Index for services by type (schools, hospitals, etc.)
CREATE INDEX IF NOT EXISTS idx_servicios_educacion
ON servicios USING GIST (coordenadas)
WHERE tipo_servicio IN ('colegio', 'universidad', 'academia') AND coordenadas_validas = true;

CREATE INDEX IF NOT EXISTS idx_servicios_salud
ON servicios USING GIST (coordenadas)
WHERE tipo_servicio IN ('hospital', 'clínica', 'farmacia') AND coordenadas_validas = true;

CREATE INDEX IF NOT EXISTS idx_servicios_comercio
ON servicios USING GIST (coordenadas)
WHERE tipo_servicio IN ('supermercado', 'tienda', 'centro comercial') AND coordenadas_validas = true;

-- =====================================================
-- Performance Monitoring Indexes
-- =====================================================

-- Index for tracking data provider performance
CREATE INDEX IF NOT EXISTS idx_propiedades_proveedor_fecha
ON propiedades (proveedor_datos, fecha_scraping);

-- =====================================================
-- Index Usage Analysis Query
-- =====================================================

-- Query to check index usage after implementation:
/*
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
*/

-- =====================================================
-- Index Maintenance Notes
-- =====================================================

/*
1. REINDEX operations should be scheduled during low-traffic periods
2. ANALYZE should be run after major data imports
3. VACUUM (or autovacuum) will maintain index efficiency
4. Monitor index usage with pg_stat_user_indexes
5. Consider dropping unused indexes to save space and improve write performance

Example maintenance:
REINDEX INDEX idx_propiedades_coordenadas;
ANALYZE propiedades;
VACUUM ANALYZE propiedades;
*/

-- =====================================================
-- Expected Performance Improvements
-- =====================================================

/*
Spatial queries with ST_DWithin:
- Before: O(n×m) operations, seconds per query
- After: Index lookup, milliseconds per query

Price range queries:
- Before: Full table scan, linear time
- After: B-tree lookup, logarithmic time

Zone-based filtering:
- Before: String comparison across all records
- After: Index lookup, constant time for indexed zones
*/