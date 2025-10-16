-- Importar propiedades desde CSV
COPY propiedades (titulo, descripcion, precio_usd, url, latitud, longitud, zona, tipo_propiedad, proveedor_datos, codigo_proveedor, coordenadas_validas)
FROM 'C:\Users\nicol\OneDrive\Documentos\trabajo\citrino\citrino-clean\propiedades_procesadas.csv'
DELIMITER ','
CSV HEADER;

-- Actualizar coordenadas PostGIS
UPDATE propiedades
SET coordenadas = ST_GeographyFromText('SRID=4326;POINT(' || longitud || ' ' || latitud || ')')
WHERE latitud IS NOT NULL AND longitud IS NOT NULL AND coordenadas IS NULL;
