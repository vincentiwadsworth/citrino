# 📋 Estado Actual PostgreSQL + PostGIS - Guía de Sesión

**Última actualización:** 16 de Octubre 2025
**Estado:** Sistema funcional pero requiere procedimientos específicos

## ⚠️ ADVERTENCIA: LOOP INFINITO DETECTADO

Cada sesión que se inicia cae en el mismo problema:
1. **Se canta victoria** → "PostgreSQL funcionando perfecto"
2. **Se cierra sesión** → Problemas encoding regresan
3. **Nueva sesión** → Mismo loop de UnicodeDecodeError

## 🔍 PROBLEMAS DETECTADOS

### Problema 1: Encoding Windows vs Docker Linux
- **Windows + psycopg2 directo** = UnicodeDecodeError constante
- **Docker Linux UTF-8 nativo** = Funciona PERO solo dentro del container
- **Conexión desde Windows a Docker** = Vuelve a dar encoding errors

### Problema 2: Conexión psycopg2 Directa NO FUNCIONA
```python
# ESTO NO FUNCIONA DESDE WINDOWS
conn = psycopg2.connect(
    host='localhost',
    port=5433,
    database='citrino',
    user='citrino_app',
    password='citrino123'
)
# ERROR: UnicodeDecodeError: 'utf-8' codec can't decode byte 0xf3
```

### Problema 3: Docker Wrapper SÍ Funciona pero es Limitado
```python
# ESTO SÍ FUNCIONA
from migration.config.database_config import create_connection
conn = create_connection()  # Usa Docker wrapper internamente
```

## ✅ SOLUCIÓN ACTUAL FUNCIONAL

### Sistema Operacional (USAR ESTE)
```bash
# 1. Iniciar Docker PostgreSQL
docker-compose up -d

# 2. Verificar que está corriendo
docker ps
# Debe mostrar citrino-postgresql en puerto 5433

# 3. Usar SOLAMENTE el wrapper de database_config.py
python -c "
from migration.config.database_config import create_connection
conn = create_connection()
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM propiedades')
print('Propiedades:', cursor.fetchone()[0])
conn.close()
"
```

### Configuración Variables de Entorno (.env.docker)
```bash
DB_HOST=localhost
DB_PORT=5433
DB_NAME=citrino
DB_USER=citrino_app
DB_PASSWORD=citrino123
```

## 🚫 LO QUE NO HACER

### No intentar psycopg2 directo
```python
# NO HACER ESTO - Falla con encoding
import psycopg2
conn = psycopg2.connect(host='localhost', port=5433, ...)
```

### No cambiar database_config.py a psycopg2 directo
El archivo `migration/config/database_config.py` está configurado para usar Docker wrapper. No cambiarlo a conexión directa psycopg2.

### No asumir que "ya está arreglado"
El problema encoding Windows NO está resuelto. Solo funciona con el wrapper Docker.

## 📋 CHECKLIST OBLIGATORIO AL INICIAR SESIÓN

### 1. Verificar Docker corriendo
```bash
docker ps | grep citrino-postgresql
# Si no está corriendo: docker-compose up -d
```

### 2. Verificar PostGIS funcionando
```bash
docker exec citrino-postgresql psql -U citrino_app -d citrino -c "SELECT PostGIS_Version();"
# Debe mostrar: 3.3 USE_GEOS=1 USE_PROJ=1 USE_STATS=1
```

### 3. Verificar tablas existentes
```bash
docker exec citrino-postgresql psql -U citrino_app -d citrino -c "\dt"
# Debe mostrar: propiedades, servicios
```

### 4. Probar conexión Python CON WRAPPER
```python
# SOLO ESTA FORMA FUNCIONA
from migration.config.database_config import create_connection
try:
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM propiedades')
    print(f'Propiedades: {cursor.fetchone()[0]}')
    conn.close()
    print('CONEXIÓN FUNCIONANDO')
except Exception as e:
    print(f'ERROR: {e}')
```

## 🔧 COMANDOS DE RECUPERACIÓN

### Si Docker no está corriendo
```bash
docker-compose down
docker-compose up -d
```

### Si PostGIS no funciona
```bash
docker exec citrino-postgresql psql -U citrino_app -d citrino -c "
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
"
```

### Si faltan tablas
```bash
docker exec citrino-postgresql psql -U citrino_app -d citrino -c "
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

CREATE INDEX IF NOT EXISTS idx_propiedades_coords
ON propiedades USING GIST (coordenadas);
"
```

## 🎯 REGLAS DE ORO

1. **NUNCA** usar psycopg2.connect() directo desde Windows
2. **SIEMPRE** usar el wrapper `create_connection()` de database_config.py
3. **NUNCA** cambiar database_config.py a conexión directa
4. **SIEMPRE** verificar Docker corriendo primero
5. **NUNCA** asumir que el encoding está "arreglado para siempre"

## 🔄 FLUJO DE TRABAJO CORRECTO

### Para desarrollo
```bash
# 1. Verificar Docker
docker ps | grep citrino

# 2. Usar wrapper en código Python
from migration.config.database_config import create_connection

# 3. NO intentar conexiones directas psycopg2
```

### Para pruebas
```bash
# 1. Probar con Docker exec (funciona)
docker exec citrino-postgresql psql -U citrino_app -d citrino -c "SELECT COUNT(*) FROM propiedades;"

# 2. Probar con Python wrapper (funciona)
python -c "from migration.config.database_config import create_connection; conn = create_connection(); print('OK')"

# 3. NO probar psycopg2 directo (falla)
```

## 📊 ESTADO ACTUAL VERIFICADO

- ✅ Docker PostgreSQL + PostGIS funcionando
- ✅ Wrapper database_config.py funcionando
- ✅ Coordenadas espaciales operativas
- ✅ Índices GIST creados
- ✅ Consultas ST_X, ST_Y, ST_DWithin funcionando
- ❌ psycopg2 directo desde Windows (UnicodeDecodeError)
- ❌ Conexión directa sin wrapper

## 🚫 ADVERTENCIA FINAL

**NO CANTAR VICTORIA** - El problema encoding Windows NO está resuelto. Solo tenemos un workaround funcional con Docker wrapper.

**SÍ SE PUEDE TRABAJAR** - Pero siguiendo ESTRICTAMENTE estos procedimientos.

**SÍ FALLA** - Volver a este documento y seguir el checklist de recuperación.

---

*Este documento debe ser leído COMPLETAMENTE al inicio de cada sesión para evitar el loop infinito.*