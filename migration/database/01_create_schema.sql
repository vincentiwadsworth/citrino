-- =====================================================
-- Citrino Database Schema - PostgreSQL + PostGIS
-- Migration from JSON-based system to relational database
-- =====================================================

-- Enable PostGIS extension for geospatial capabilities
CREATE EXTENSION IF NOT EXISTS postgis;

-- =====================================================
-- 1. AGENTES TABLE (Normalized)
-- =====================================================
CREATE TABLE IF NOT EXISTS agentes (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    telefono VARCHAR(50),
    email VARCHAR(255) UNIQUE,
    empresa VARCHAR(100),
    fecha_registro TIMESTAMPTZ DEFAULT now(),

    -- Constraints and uniqueness
    CONSTRAINT uq_agente_nombre UNIQUE (nombre),
    CONSTRAINT uq_agente_email UNIQUE (email)
);

-- =====================================================
-- 2. PROPIEDADES TABLE (Main entity)
-- =====================================================
CREATE TABLE IF NOT EXISTS propiedades (
    id BIGSERIAL PRIMARY KEY,
    agente_id BIGINT REFERENCES agentes(id) ON DELETE SET NULL,

    -- Descriptive fields
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
    uv VARCHAR(50),  -- Unidad Vecinal
    manzana VARCHAR(50),
    lote VARCHAR(50),

    -- Property specifications
    superficie_total NUMERIC(10, 2),
    superficie_construida NUMERIC(10, 2),
    num_dormitorios INTEGER,
    num_banos INTEGER,
    num_garajes INTEGER,

    -- Geospatial column (PostGIS Geography for accurate distance calculations)
    coordenadas GEOGRAPHY(POINT, 4326),

    -- Metadata
    fecha_publicacion TIMESTAMPTZ,
    fecha_scraping TIMESTAMPTZ DEFAULT now(),
    ultima_actualizacion TIMESTAMPTZ DEFAULT now(),
    proveedor_datos VARCHAR(100),
    codigo_proveedor VARCHAR(100),
    url_origen TEXT,

    -- Quality flags
    coordenadas_validas BOOLEAN DEFAULT false,
    datos_completos BOOLEAN DEFAULT false
);

-- =====================================================
-- 3. SERVICIOS TABLE (Points of Interest)
-- =====================================================
CREATE TABLE IF NOT EXISTS servicios (
    id BIGSERIAL PRIMARY KEY,

    -- Service information
    nombre VARCHAR(255) NOT NULL,
    tipo_servicio VARCHAR(100),
    subtipo_servicio VARCHAR(100),

    -- Location
    direccion TEXT,
    zona VARCHAR(100),

    -- Geospatial data
    coordenadas GEOGRAPHY(POINT, 4326),

    -- Additional info
    telefono VARCHAR(50),
    horario TEXT,

    -- Metadata
    fuente_datos VARCHAR(100),
    fecha_registro TIMESTAMPTZ DEFAULT now(),

    -- Quality flags
    coordenadas_validas BOOLEAN DEFAULT false
);

-- =====================================================
-- 4. PROVEEDORES DATOS TABLE (Data sources tracking)
-- =====================================================
CREATE TABLE IF NOT EXISTS proveedores_datos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL,
    descripcion TEXT,
    url_base TEXT,
    fecha_ultima_sincronizacion TIMESTAMPTZ,
    estado VARCHAR(20) DEFAULT 'activo'
);

-- =====================================================
-- 5. MIGRATION_LOG TABLE (Migration tracking)
-- =====================================================
CREATE TABLE IF NOT EXISTS migration_log (
    id SERIAL PRIMARY KEY,
    fecha_ejecucion TIMESTAMPTZ DEFAULT now(),
    tabla_migrada VARCHAR(50),
    registros_procesados INTEGER,
    registros_exitosos INTEGER,
    registros_errores INTEGER,
    detalles_error TEXT,
    execution_time_ms INTEGER
);

-- =====================================================
-- Comments for documentation
-- =====================================================

COMMENT ON TABLE agentes IS 'Tabla normalizada de agentes inmobiliarios';
COMMENT ON TABLE propiedades IS 'Tabla principal de propiedades con datos geoespaciales';
COMMENT ON TABLE servicios IS 'Tabla de servicios urbanos y puntos de interés';
COMMENT ON TABLE proveedores_datos IS 'Catálogo de fuentes de datos';
COMMENT ON TABLE migration_log IS 'Log de procesos de migración';

COMMENT ON COLUMN propiedades.coordenadas IS 'Coordenadas geográficas en formato PostGIS Geography (SRID 4326)';
COMMENT ON COLUMN servicios.coordenadas IS 'Coordenadas geográficas en formato PostGIS Geography (SRID 4326)';
COMMENT ON COLUMN propiedades.precio_usd IS 'Precio en dólares estadounidenses';
COMMENT ON COLUMN propiedades.precio_usd_m2 IS 'Precio por metro cuadrado en USD';

-- =====================================================
-- Initial data setup
-- =====================================================

-- Insert known data providers
INSERT INTO proveedores_datos (nombre, descripcion, url_base) VALUES
('Proveedor 01', 'Scraping directo de portales inmobiliarios', 'https://portal1.com'),
('Proveedor 02', 'API de datos inmobiliarios', 'https://api.proveedor2.com'),
('Municipalidad', 'Guía urbana municipal', 'https://municipalidad.sc.gov.bo')
ON CONFLICT (nombre) DO NOTHING;