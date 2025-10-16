# 🚨 LEER ANTES DE TRABAJAR - Guía de Reinicio de Sesión

## ⚠️ PROBLEMA CRÍTICO: Loop Infinito de Encoding

Cada vez que se inicia una nueva sesión, el sistema PostgreSQL presenta los mismos problemas de encoding. Este documento detalla el procedimiento OBLIGATORIO para evitar repetir errores.

## 🔍 DIAGNÓSTICO RÁPIDO (2 minutos)

### Paso 1: Verificar Docker
```bash
docker ps | grep citrino-postgresql
```
**Si no aparece:** Ejecutar `docker-compose up -d`

### Paso 2: Verificar Conexión
```bash
docker exec citrino-postgresql psql -U citrino_app -d citrino -c "SELECT COUNT(*) FROM propiedades;"
```
**Si da error:** El sistema no está inicializado

### Paso 3: Verificar Python Wrapper
```bash
python -c "from migration.config.database_config import create_connection; conn = create_connection(); print('Wrapper OK'); conn.close()"
```
**Si da UnicodeDecodeError:** El wrapper está roto

## 🛠️ PROCEDIMIENTO DE RECUPERACIÓN ESTÁNDAR

### Opción A: Sistema Funciona (3 minutos)
Si los 3 pasos anteriores funcionan:
1. ✅ Usar `create_connection()` de database_config.py
2. ✅ NUNCA usar psycopg2 directo
3. ✅ Continuar trabajando normalmente

### Opción B: Sistema Roto (5-10 minutos)
Si alguno de los pasos falla:

#### B1: Reiniciar Docker
```bash
docker-compose down
docker-compose up -d
docker ps | grep citrino-postgresql
```

#### B2: Recrear Base de Datos
```bash
docker exec citrino-postgresql psql -U citrino_app -d citrino -c "
DROP TABLE IF EXISTS propiedades CASCADE;
DROP TABLE IF EXISTS servicios CASCADE;

CREATE TABLE propiedades (
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

CREATE INDEX idx_propiedades_coords ON propiedades USING GIST (coordenadas);
"
```

#### B3: Verificar Wrapper Funciona
```bash
python -c "
from migration.config.database_config import create_connection
try:
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM propiedades')
    print(f'Wrapper funciona: {cursor.fetchone()[0]} propiedades')
    conn.close()
except Exception as e:
    print(f'ERROR CRÍTICO: {e}')
    print('Revisar documentation/POSTGRES_SESSION_STATE.md')
"
```

## 🚫 ERRORES COMUNES A EVITAR

### Error #1: "Voy a usar psycopg2 directo"
```python
# ❌ NUNCA HACER ESTO
import psycopg2
conn = psycopg2.connect(host='localhost', port=5433, ...)  # UnicodeDecodeError
```

### Error #2: "Voy a modificar database_config.py"
```python
# ❌ NUNCA CAMBIAR ESTO
def get_connection_params(self):
    return {'host': self.host, ...}  # Esto rompe el wrapper
```

### Error #3: "Asumir que ya está arreglado"
El problema encoding Windows es PERMANENTE. Solo funciona con el wrapper Docker.

## ✅ FORMAS CORRECTAS DE TRABAJAR

### Consultas SQL (Usar Docker exec)
```bash
# ✅ Forma segura
docker exec citrino-postgresql psql -U citrino_app -d citrino -c "SELECT * FROM propiedades;"
```

### Consultas Python (Usar wrapper)
```python
# ✅ Única forma que funciona
from migration.config.database_config import create_connection

conn = create_connection()
cursor = conn.cursor()
cursor.execute("SELECT * FROM propiedades;")
results = cursor.fetchall()
conn.close()
```

### Datos de Prueba
```bash
# ✅ Insertar datos seguros
docker exec citrino-postgresql psql -U citrino_app -d citrino -c "
INSERT INTO propiedades (titulo, precio_usd, coordenadas, zona) VALUES
('Casa Test', 150000, ST_GeogFromText('POINT(-63.1833 -17.7833)'), 'Centro');
"
```

## 📋 CHECKLIST FINAL ANTES DE TRABAJAR

- [ ] Docker corriendo (`docker ps | grep citrino`)
- [ ] PostGIS activo (`docker exec ... SELECT PostGIS_Version();`)
- [ ] Wrapper funciona (`python -c "from migration.config.database_config import create_connection; ..."`)
- [ ] Tablas existen (`docker exec ... \dt`)
- [ ] NO intentar psycopg2 directo
- [ ] Usar SIEMPRE `create_connection()`

## 🆘 SI TODO FALLA

### Comando de Último Recurso
```bash
# Reset completo del sistema
docker-compose down -v
docker-compose up -d
# Esperar 30 segundos
docker exec citrino-postgresql psql -U citrino_app -d citrino -c "SELECT PostGIS_Version();"
```

### Documentación de Referencia
- `docs/POSTGRES_SESSION_STATE.md` - Estado detallado del sistema
- `migration/config/database_config.py` - Wrapper funcional
- `docker-compose.yml` - Configuración Docker

## 🎯 REGLA DE ORO

**Si no estás seguro, usa Docker exec. Siempre funciona.**
**Si necesitas Python, usa el wrapper. Nunca falla.**
**NUNCA intentes psycopg2 directo. Siempre falla.**

---

*Leer este documento COMPLETO antes de trabajar con PostgreSQL en cada sesión.*