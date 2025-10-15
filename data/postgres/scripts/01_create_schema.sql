-- =====================================================
-- Citrino PostgreSQL + PostGIS Database Schema
-- Sprint 1: Migración desde Excel a PostgreSQL
-- =====================================================

-- Habilitar extensión PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- =====================================================
-- TABLA 1: agentes - Agentes Inmobiliarios Normalizados
-- =====================================================

CREATE TABLE IF NOT EXISTS agentes (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    telefono VARCHAR(50),
    email VARCHAR(255) UNIQUE,
    empresa VARCHAR(100),
    fecha_registro TIMESTAMPTZ DEFAULT now(),

    -- Constraints
    CONSTRAINT uq_agente_nombre UNIQUE (nombre),
    CONSTRAINT uq_agente_email UNIQUE (email)
);

-- =====================================================
-- TABLA 2: propiedades - Propiedades con Datos Geoespaciales
-- =====================================================

CREATE TABLE IF NOT EXISTS propiedades (
    id BIGSERIAL PRIMARY KEY,
    agente_id BIGINT REFERENCES agentes(id) ON DELETE SET NULL,

    -- Descriptivos
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    tipo_propiedad VARCHAR(100),
    estado_propiedad VARCHAR(50),

    -- Financieros
    precio_usd NUMERIC(12, 2),
    precio_usd_m2 NUMERIC(10, 2),
    moneda VARCHAR(10) DEFAULT 'USD',

    -- Ubicación
    direccion TEXT,
    zona VARCHAR(100),
    uv VARCHAR(50),
    manzana VARCHAR(50),
    lote VARCHAR(50),

    -- Especificaciones
    superficie_total NUMERIC(10, 2),
    superficie_construida NUMERIC(10, 2),
    num_dormitorios INTEGER,
    num_banos INTEGER,
    num_garajes INTEGER,

    -- Geoespacial (PostGIS)
    coordenadas GEOGRAPHY(POINT, 4326),

    -- Metadatos
    fecha_publicacion TIMESTAMPTZ,
    fecha_scraping TIMESTAMPTZ DEFAULT now(),
    ultima_actualizacion TIMESTAMPTZ DEFAULT now(),
    proveedor_datos VARCHAR(100),
    codigo_proveedor VARCHAR(100),
    url_origen TEXT,

    -- Calidad de datos
    coordenadas_validas BOOLEAN DEFAULT false,
    datos_completos BOOLEAN DEFAULT false
);

-- =====================================================
-- TABLA 3: servicios - Servicios Urbanos (Puntos de Interés)
-- =====================================================

CREATE TABLE IF NOT EXISTS servicios (
    id BIGSERIAL PRIMARY KEY,

    -- Información del servicio
    nombre VARCHAR(255) NOT NULL,
    tipo_servicio VARCHAR(100),
    subtipo_servicio VARCHAR(100),

    -- Ubicación
    direccion TEXT,
    zona VARCHAR(100),

    -- Geoespacial
    coordenadas GEOGRAPHY(POINT, 4326),

    -- Información adicional
    telefono VARCHAR(50),
    horario TEXT,

    -- Metadatos
    fuente_datos VARCHAR(100),
    fecha_registro TIMESTAMPTZ DEFAULT now(),

    -- Calidad
    coordenadas_validas BOOLEAN DEFAULT false
);

-- =====================================================
-- ÍNDICES DE RENDIMIENTO POSTGIS
-- =====================================================

-- Índices espaciales para consultas geográficas
CREATE INDEX IF NOT EXISTS idx_propiedades_coordenadas ON propiedades USING GIST (coordenadas);
CREATE INDEX IF NOT EXISTS idx_servicios_coordenadas ON servicios USING GIST (coordenadas);

-- Índices compuestos para búsquedas comunes
CREATE INDEX IF NOT EXISTS idx_propiedades_zona_precio ON propiedades (zona, precio_usd);
CREATE INDEX IF NOT EXISTS idx_propiedades_tipo_zona ON propiedades (tipo_propiedad, zona);
CREATE INDEX IF NOT EXISTS idx_propiedades_agente_id ON propiedades (agente_id);
CREATE INDEX IF NOT EXISTS idx_servicios_tipo_zona ON servicios (tipo_servicio, zona);

-- Índices para metadatos
CREATE INDEX IF NOT EXISTS idx_propiedades_fecha_scraping ON propiedades (fecha_scraping);
CREATE INDEX IF NOT EXISTS idx_propiedades_proveedor_datos ON propiedades (proveedor_datos);
CREATE INDEX IF NOT EXISTS idx_propiedades_coordenadas_validas ON propiedades (coordenadas_validas);

-- =====================================================
-- FUNCIONES ESPACIALES POSTGIS
-- =====================================================

-- Función para calcular distancia entre dos puntos
CREATE OR REPLACE FUNCTION calcular_distancia_metros(
    lat1 NUMERIC,
    lon1 NUMERIC,
    lat2 NUMERIC,
    lon2 NUMERIC
) RETURNS NUMERIC AS $$
BEGIN
    RETURN ST_Distance(
        ST_GeographyFromText('SRID=4326;POINT(' || lon1 || ' ' || lat1 || ')'),
        ST_GeographyFromText('SRID=4326;POINT(' || lon2 || ' ' || lat2 || ')')
    );
END;
$$ LANGUAGE plpgsql;

-- Función para buscar propiedades cerca de servicios
CREATE OR REPLACE FUNCTION buscar_propiedades_cerca_servicios(
    radio_km NUMERIC DEFAULT 1.0,
    limit_resultados INTEGER DEFAULT 50
) RETURNS TABLE(
    id_propiedad BIGINT,
    titulo VARCHAR(255),
    direccion TEXT,
    zona VARCHAR(100),
    precio_usd NUMERIC,
    tipo_propiedad VARCHAR(100),
    latitud NUMERIC,
    longitud NUMERIC,
    distancia_servicio NUMERIC,
    nombre_servicio VARCHAR(255),
    tipo_servicio VARCHAR(100)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.titulo,
        p.direccion,
        p.zona,
        p.precio_usd,
        p.tipo_propiedad,
        ST_Y(p.coordenadas) as latitud,
        ST_X(p.coordenadas) as longitud,
        ST_Distance(p.coordenadas, s.coordenadas) as distancia_servicio,
        s.nombre,
        s.tipo_servicio
    FROM propiedades p
    CROSS JOIN servicios s
    WHERE p.coordenadas_validas = true
    AND s.coordenadas_validas = true
    AND ST_DWithin(p.coordenadas, s.coordenadas, radio_km * 1000)
    ORDER BY p.precio_usd
    LIMIT limit_resultados;
END;
$$ LANGUAGE plpgsql;

-- Función para validar coordenadas dentro de Santa Cruz de la Sierra
CREATE OR REPLACE FUNCTION validar_coordenadas_santa_cruz(
    lat NUMERIC,
    lon NUMERIC
) RETURNS BOOLEAN AS $$
BEGIN
    -- Bounds aproximados de Santa Cruz de la Sierra
    -- Latitud: -17.5 a -18.5
    -- Longitud: -63.0 a -63.5
    RETURN lat BETWEEN -18.5 AND -17.5
    AND lon BETWEEN -63.5 AND -63.0;
END;
$$ LANGUAGE plpgsql;

-- Función para actualizar estadísticas de cobertura de servicios por zona
CREATE OR REPLACE FUNCTION actualizar_estadisticas_zona(nombre_zona VARCHAR)
RETURNS TABLE(
    total_propiedades INTEGER,
    propiedades_con_coordenadas INTEGER,
    total_servicios INTEGER,
    servicios_cercanos_500m INTEGER,
    precio_promedio NUMERIC,
    densidad_servicios NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) as total_propiedades,
        COUNT(*) FILTER (WHERE coordenadas_validas = true) as propiedades_con_coordenadas,
        (SELECT COUNT(*) FROM servicios WHERE zona = nombre_zona AND coordenadas_validas = true) as total_servicios,
        COUNT(DISTINCT s.id) FILTER (WHERE ST_DWithin(p.coordenadas, s.coordenadas, 500)) as servicios_cercanos_500m,
        ROUND(AVG(p.precio_usd)) as precio_promedio,
        ROUND(COUNT(DISTINCT s.id)::NUMERIC / NULLIF(COUNT(*) FILTER (WHERE coordenadas_validas = true), 0), 2) as densidad_servicios
    FROM propiedades p
    LEFT JOIN servicios s ON ST_DWithin(p.coordenadas, s.coordenadas, 500)
    WHERE p.zona = nombre_zona;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- VISTAS ÚTILES PARA ANÁLISIS
-- =====================================================

-- Vista de propiedades con coordenadas válidas
CREATE OR REPLACE VIEW propiedades_validas AS
SELECT
    id,
    titulo,
    direccion,
    zona,
    precio_usd,
    tipo_propiedad,
    superficie_total,
    num_dormitorios,
    ST_Y(coordenadas) as latitud,
    ST_X(coordenadas) as longitud,
    fecha_scraping,
    proveedor_datos
FROM propiedades
WHERE coordenadas_validas = true;

-- Vista de agentes con número de propiedades
CREATE OR REPLACE VIEW agentes_activos AS
SELECT
    a.id,
    a.nombre,
    a.telefono,
    a.email,
    a.empresa,
    COUNT(p.id) as numero_propiedades,
    AVG(p.precio_usd) as precio_promedio,
    MAX(p.fecha_scraping) as ultima_actualizacion
FROM agentes a
LEFT JOIN propiedades p ON a.id = p.agente_id
GROUP BY a.id, a.nombre, a.telefono, a.email, a.empresa
ORDER BY numero_propiedades DESC;

-- Vista de análisis de cobertura de servicios por zona
CREATE OR REPLACE VIEW cobertura_servicios_zona AS
SELECT
    p.zona,
    COUNT(*) as total_propiedades,
    COUNT(*) FILTER (WHERE p.coordenadas_validas = true) as propiedades_con_coordenadas,
    COUNT(DISTINCT s.id) as servicios_cercanos_500m,
    ROUND(AVG(p.precio_usd)) as precio_promedio_zona,
    ROUND(COUNT(DISTINCT s.id)::NUMERIC / NULLIF(COUNT(*) FILTER (WHERE p.coordenadas_validas = true), 0), 2) as densidad_servicios
FROM propiedades p
LEFT JOIN servicios s ON ST_DWithin(p.coordenadas, s.coordenadas, 500)
WHERE p.coordenadas_validas = true
GROUP BY p.zona
ORDER BY densidad_servicios DESC;

-- =====================================================
-- COMENTARIOS ADICIONALES
-- =====================================================

COMMENT ON TABLE agentes IS 'Agentes inmobiliarios normalizados y deduplicados del sistema Citrino';
COMMENT ON TABLE propiedades IS 'Propiedades inmobiliarias con coordenadas PostGIS para análisis geoespacial';
COMMENT ON TABLE servicios IS 'Servicios urbanos y puntos de interés para análisis de cobertura';
COMMENT ON COLUMN propiedades.coordenadas IS 'Coordenadas geográficas usando PostGIS Geography (SRID 4326)';
COMMENT ON COLUMN servicios.coordenadas IS 'Coordenadas geográficas usando PostGIS Geography (SRID 4326)';
COMMENT ON FUNCTION calcular_distancia_metros IS 'Calcula distancia en metros entre dos coordenadas usando Haversine';
COMMENT ON FUNCTION buscar_propiedades_cerca_servicios IS 'Busca propiedades dentro de un radio de servicios específicos';
COMMENT ON FUNCTION validar_coordenadas_santa_cruz IS 'Valida que coordenadas estén dentro de bounds de Santa Cruz de la Sierra';

-- =====================================================
-- TRIGGERS PARA MANTENIMIENTO AUTOMÁTICO
-- =====================================================

-- Trigger para actualizar timestamp de última_actualización en propiedades
CREATE OR REPLACE FUNCTION actualizar_timestamp_propiedad()
RETURNS TRIGGER AS $$
BEGIN
    NEW.ultima_actualizacion = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_actualizar_timestamp_propiedad
    BEFORE UPDATE ON propiedades
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_timestamp_propiedad();

-- Trigger para validar coordenadas antes de insertar/actualizar
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

CREATE TRIGGER trigger_validar_coordenadas_propiedades
    BEFORE INSERT OR UPDATE ON propiedades
    FOR EACH ROW
    EXECUTE FUNCTION validar_coordenadas_trigger();

CREATE TRIGGER trigger_validar_coordenadas_servicios
    BEFORE INSERT OR UPDATE ON servicios
    FOR EACH ROW
    EXECUTE FUNCTION validar_coordenadas_trigger();

-- =====================================================
-- SCRIPT FINALIZADO
-- =====================================================

-- Verificación de instalación
SELECT 'PostgreSQL + PostGIS schema for Citrino created successfully' as status;