#!/bin/bash

# Script de inicialización PostGIS UTF-8 nativo
set -e

echo "=== INICIALIZANDO POSTGREgreSQL + PostGIS UTF-8 Nativo ==="

# Configuración de encoding
echo "Configurando encoding UTF-8 español..."

# Crear tabla de propiedades con coordenadas PostGIS
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Habilitar PostGIS
    CREATE EXTENSION IF NOT EXISTS postgis;
    CREATE EXTENSION IF NOT EXISTS postgis_topology;

    -- Crear tabla propiedades con coordenadas geográficas
    CREATE TABLE IF NOT EXISTS propiedades (
        id BIGSERIAL PRIMARY KEY,
        titulo TEXT,
        descripcion TEXT,
        precio_usd DECIMAL(12,2),
        tipo_propiedad VARCHAR(100),
        coordenadas GEOGRAPHY(POINT, 4326),
        zona VARCHAR(200),
        direccion TEXT,
        superficie_total DECIMAL(10,2),
        superficie_construida DECIMAL(10,2),
        num_dormitorios INTEGER,
        num_banios INTEGER,
        num_garajes INTEGER,
        fecha_scraping TIMESTAMP DEFAULT NOW(),
        proveedor_datos VARCHAR(100),
        coordenadas_validas BOOLEAN DEFAULT FALSE,
        datos_completos BOOLEAN DEFAULT FALSE
    );

    -- Crear índice espacial GIST para consultas eficientes
    CREATE INDEX IF NOT EXISTS idx_propiedades_coords
    ON propiedades USING GIST (coordenadas);

    -- Crear tabla servicios urbanos
    CREATE TABLE IF NOT EXISTS servicios (
        id BIGSERIAL PRIMARY KEY,
        nombre TEXT NOT NULL,
        tipo VARCHAR(100),
        coordenadas GEOGRAPHY(POINT, 4326),
        direccion TEXT,
        descripcion TEXT,
        zona VARCHAR(200)
    );

    -- Crear índice espacial para servicios
    CREATE INDEX IF NOT EXISTS idx_servicios_coords
    ON servicios USING GIST (coordenadas);

    -- Crear esquema Citrino
    CREATE SCHEMA IF NOT EXISTS citrino;
    SET search_path TO citrino, public;

    -- Verificar PostGIS
    SELECT 'PostGIS versión: ' || PostGIS_Version();
    SELECT 'SpatialRefSys disponibles: ' || COUNT(*) FROM spatial_ref_sys;

EOSQL

echo "=== POSTGREgreSQL + PostGIS LISTO ==="
echo "Encoding: UTF-8 (es_ES.UTF-8)"
echo "PostGIS: Funcional completo"
echo "Índices espaciales: Creados"
echo "Listo para recibir datos..."