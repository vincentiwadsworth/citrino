-- Esquema completo para Citrino con PostgreSQL + PostGIS
-- Soporte para datos geoespaciales y consultas de alto rendimiento

-- Extensiones necesarias
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Tabla de agentes (deduplicados)
CREATE TABLE agentes (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    telefono VARCHAR(50),
    email VARCHAR(255),
    url_agente VARCHAR(500),
    fuente_origen VARCHAR(100), -- bieninmuebles, portalinmobiliario, etc
    fecha_extracion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence_score DECIMAL(3,2) DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices para agentes
CREATE INDEX idx_agentes_nombre ON agentes(nombre);
CREATE INDEX idx_agentes_telefono ON agentes(telefono);
CREATE INDEX idx_agentes_email ON agentes(email);
CREATE UNIQUE INDEX idx_agentes_unique ON agentes(nombre, COALESCE(telefono, ''), COALESCE(email, ''));

-- Tabla de propiedades con coordenadas PostGIS
CREATE TABLE propiedades (
    id BIGSERIAL PRIMARY KEY,
    url VARCHAR(500) UNIQUE NOT NULL,
    titulo VARCHAR(500) NOT NULL,
    precio_usd DECIMAL(12,2),
    descripcion TEXT,
    habitaciones INTEGER,
    banos INTEGER,
    garajes INTEGER,
    sup_terreno DECIMAL(10,2),
    sup_construida DECIMAL(10,2),
    detalles TEXT,

    -- Campos de geolocalización
    coordenadas GEOGRAPHY(POINT, 4326), -- PostGIS point
    latitud DECIMAL(10,8),
    longitud DECIMAL(11,8),
    direccion TEXT,
    zona VARCHAR(255),
    uv VARCHAR(50),
    manzana VARCHAR(50),

    -- Relaciones
    agente_id BIGINT REFERENCES agentes(id),

    -- Metadatos
    fuente_origen VARCHAR(100),
    fecha_extracion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    coordenadas_validadas BOOLEAN DEFAULT FALSE,
    calidad_datos DECIMAL(3,2) DEFAULT 0.8,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices espaciales y de rendimiento para propiedades
CREATE INDEX idx_propiedades_coordenadas ON propiedades USING GIST(coordenadas);
CREATE INDEX idx_propiedades_precio ON propiedades(precio_usd) WHERE precio_usd IS NOT NULL;
CREATE INDEX idx_propiedades_zona ON propiedades(zona) WHERE zona IS NOT NULL;
CREATE INDEX idx_propiedades_habitaciones ON propiedades(habitaciones) WHERE habitaciones IS NOT NULL;
CREATE INDEX idx_propiedades_agente ON propiedades(agente_id);

-- Tabla de servicios urbanos con PostGIS
CREATE TABLE servicios (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(500) NOT NULL,
    categoria_principal VARCHAR(100),
    subcategoria VARCHAR(100),
    direccion TEXT,

    -- Coordenadas PostGIS
    coordenadas GEOGRAPHY(POINT, 4326),
    latitud DECIMAL(10,8),
    longitud DECIMAL(11,8),

    -- Ubicación específica
    uv VARCHAR(50),
    manzana VARCHAR(50),
    zona_uv VARCHAR(50),

    -- Contacto
    telefono VARCHAR(100),
    horario TEXT,
    email VARCHAR(255),
    web VARCHAR(500),

    -- Metadatos
    fuente_origen VARCHAR(100) DEFAULT 'guia_urbana_municipal',
    fecha_extracion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    coordenadas_validadas BOOLEAN DEFAULT FALSE,
    confidence_calificacion DECIMAL(3,2) DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices espaciales y de búsqueda para servicios
CREATE INDEX idx_servicios_coordenadas ON servicios USING GIST(coordenadas);
CREATE INDEX idx_servicios_categoria ON servicios(categoria_principal);
CREATE INDEX idx_servicios_subcategoria ON servicios(subcategoria);
CREATE INDEX idx_servicios_zona_uv ON servicios(zona_uv);
CREATE INDEX idx_servicios_uv ON servicios(uv);

-- Tabla de categorías de servicios (para análisis)
CREATE TABLE categorias_servicios (
    id SERIAL PRIMARY KEY,
    categoria_principal VARCHAR(100) UNIQUE NOT NULL,
    descripcion TEXT,
    color_hex VARCHAR(7) DEFAULT '#CCCCCC',
    prioridad INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de análisis de proximidad (cache de consultas frecuentes)
CREATE TABLE proximidad_cache (
    id BIGSERIAL PRIMARY KEY,
    propiedad_id BIGINT REFERENCES propiedades(id),
    categoria_servicio VARCHAR(100),
    radio_metros INTEGER,
    cantidad_servicios INTEGER,
    distancia_promedio DECIMAL(8,2),
    servicios_ids BIGINT[], -- Array de IDs de servicios cercanos
    calculado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '7 days')
);

CREATE INDEX idx_proximidad_cache_propiedad ON proximidad_cache(propiedad_id);
CREATE INDEX idx_proximidad_cache_categoria ON proximidad_cache(categoria_servicio);
CREATE INDEX idx_proximidad_cache_expires ON proximidad_cache(expires_at);

-- Funciones de utilidad PostGIS

-- Función para calcular distancia entre punto y servicios dentro de un radio
CREATE OR REPLACE FUNCTION servicios_cercanos(
    punto GEOGRAPHY,
    radio_metros INTEGER,
    categoria VARCHAR DEFAULT NULL
) RETURNS TABLE (
    servicio_id BIGINT,
    nombre VARCHAR,
    categoria_principal VARCHAR,
    distancia_metros DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.id,
        s.nombre,
        s.categoria_principal,
        ST_Distance(punto, s.coordenadas) as distancia_metros
    FROM servicios s
    WHERE s.coordenadas IS NOT NULL
    AND ST_DWithin(punto, s.coordenadas, radio_metros)
    AND (categoria IS NULL OR s.categoria_principal = categoria)
    ORDER BY ST_Distance(punto, s.coordenadas);
END;
$$ LANGUAGE plpgsql;

-- Función para actualizar coordenadas PostGIS desde lat/lon
CREATE OR REPLACE FUNCTION actualizar_coordenadas_propiedades()
RETURNS INTEGER AS $$
DECLARE
    count_actualizadas INTEGER := 0;
BEGIN
    UPDATE propiedades
    SET coordenadas = ST_SetSRID(ST_MakePoint(longitud, latitud), 4326)::geography
    WHERE latitud IS NOT NULL
    AND longitud IS NOT NULL
    AND coordenadas IS NULL;

    GET DIAGNOSTICS count_actualizadas = ROW_COUNT;
    RETURN count_actualizadas;
END;
$$ LANGUAGE plpgsql;

-- Función para actualizar coordenadas de servicios
CREATE OR REPLACE FUNCTION actualizar_coordenadas_servicios()
RETURNS INTEGER AS $$
DECLARE
    count_actualizadas INTEGER := 0;
BEGIN
    UPDATE servicios
    SET coordenadas = ST_SetSRID(ST_MakePoint(longitud, latitud), 4326)::geography
    WHERE latitud IS NOT NULL
    AND longitud IS NOT NULL
    AND coordenadas IS NULL;

    GET DIAGNOSTICS count_actualizadas = ROW_COUNT;
    RETURN count_actualizadas;
END;
$$ LANGUAGE plpgsql;

-- Trigger para actualizar timestamps
CREATE OR REPLACE FUNCTION actualizar_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar triggers a todas las tablas principales
CREATE TRIGGER trigger_propiedades_timestamp BEFORE UPDATE ON propiedades
    FOR EACH ROW EXECUTE FUNCTION actualizar_timestamp();

CREATE TRIGGER trigger_servicios_timestamp BEFORE UPDATE ON servicios
    FOR EACH ROW EXECUTE FUNCTION actualizar_timestamp();

CREATE TRIGGER trigger_agentes_timestamp BEFORE UPDATE ON agentes
    FOR EACH ROW EXECUTE FUNCTION actualizar_timestamp();

-- Vistas útiles para consultas de negocio

-- Vista de propiedades con análisis de servicios cercanos
CREATE VIEW vista_propiedades_con_servicios AS
SELECT
    p.*,
    a.nombre as agente_nombre,
    -- Cálculo de servicios a 500m (caminables)
    (SELECT COUNT(*) FROM servicios_cercanos(p.coordenadas, 500) WHERE categoria_principal = 'educacion') as escuelas_cerca,
    (SELECT COUNT(*) FROM servicios_cercanos(p.coordenadas, 500) WHERE categoria_principal = 'salud') as salud_cerca,
    (SELECT COUNT(*) FROM servicios_cercanos(p.coordenadas, 500) WHERE categoria_principal = 'comercio') as comercio_cerca,
    -- Servicios a 1km (cortos)
    (SELECT COUNT(*) FROM servicios_cercanos(p.coordenadas, 1000) WHERE categoria_principal = 'transporte') as transporte_cerca
FROM propiedades p
LEFT JOIN agentes a ON p.agente_id = a.id
WHERE p.coordenadas IS NOT NULL;

-- Vista de análisis por zona
CREATE VIEW vista_analisis_zonas AS
SELECT
    zona,
    COUNT(*) as total_propiedades,
    AVG(precio_usd) as precio_promedio,
    MIN(precio_usd) as precio_minimo,
    MAX(precio_usd) as precio_maximo,
    AVG(sup_terreno) as sup_terreno_promedio,
    AVG(habitaciones) as habitaciones_promedio,
    -- Densidad de servicios por zona
    (SELECT COUNT(*) FROM servicios s WHERE s.zona_uv = propiedades.zona) as servicios_cerca_zona
FROM propiedades
WHERE zona IS NOT NULL
GROUP BY zona
ORDER BY total_propiedades DESC;

-- Insertar categorías de servicios comunes
INSERT INTO categorias_servicios (categoria_principal, descripcion, color_hex, prioridad) VALUES
('educacion', 'Instituciones educativas', '#2E7D32', 1),
('salud', 'Servicios de salud', '#C62828', 1),
('comercio', 'Establecimientos comerciales', '#1565C0', 2),
('transporte', 'Transporte público', '#6A1B9A', 2),
('seguridad', 'Servicios de seguridad', '#F57C00', 1),
('recreacion', 'Áreas recreativas', '#00838F', 3),
('finanzas', 'Servicios financieros', '#37474F', 2),
('gobierno', 'Oficinas gubernamentales', '#5D4037', 3),
('otros', 'Otros servicios', '#757575', 4)
ON CONFLICT (categoria_principal) DO NOTHING;

-- Comentarios sobre las tablas
COMMENT ON TABLE propiedades IS 'Catálogo de propiedades con coordenadas PostGIS para análisis espacial';
COMMENT ON TABLE servicios IS 'Servicios urbanos con geolocalización para análisis de proximidad';
COMMENT ON TABLE agentes IS 'Agentes inmobiliarios deduplicados';
COMMENT ON TABLE proximidad_cache IS 'Cache de consultas de proximidad para optimizar rendimiento';

-- Estadísticas para mejor rendimiento de consultas
ANALYZE propiedades;
ANALYZE servicios;
ANALYZE agentes;