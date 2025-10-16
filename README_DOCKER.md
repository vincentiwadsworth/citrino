# 🐳 Docker PostgreSQL + PostGIS UTF-8 Nativo

**Solución DEFINITIVA al loop de encoding Windows + Oracle Cloud PostGIS roto**

---

## 🎯 **PROBLEMA RESUELTO**

### ❌ **Antes (Loop Infinito)**
- Windows + PostgreSQL + UTF-8 = **Encoding corrupto**
- Oracle Cloud + PostGIS = **No soportado, coordenadas NULL**
- psycopg2 directo = **UnicodeDecodeError constante**
- Wrappers Docker = **Solución temporal, parsing roto**

### ✅ **Ahora (Solución Definitiva)**
- **Ubuntu 22.04 + UTF-8 nativo** = Sin problemas de encoding
- **PostgreSQL 15 + PostGIS 3.3 completo** = Todas las funciones espaciales
- **psycopg2-binary nativo** = Sin wrappers, conexión directa
- **Coordenadas GEOGRAPHY reales** = ST_X, ST_Y funcionando

---

## 🚀 **INSTRUCCIONES (5 minutos)**

### 1. **Iniciar Docker PostgreSQL**
```bash
# Construir y levantar todo
docker-compose up -d

# Verificar estado
docker-compose ps
```

### 2. **Verificar Sistema Funcional**
```bash
# Test PostGIS y encoding
docker exec -it citrino-postgresql psql -U citrino_app -d citrino -c "SELECT PostGIS_Version();"

# Verificar coordenadas funcionando
docker exec -it citrino-postgresql psql -U citrino_app -d citrino -c "
    SELECT ST_X(ST_GeographyFromText('POINT(-63.1833 -17.7833)', 4326)::geometry) as lng,
           ST_Y(ST_GeographyFromText('POINT(-63.1833 -17.7833)', 4326)::geometry) as lat;
"
```

### 3. **Migrar Datos (Opcional)**
```bash
# Copiar datos desde Oracle Cloud
python scripts/migrate_oracle_to_docker.py
```

### 4. **Iniciar API**
```bash
# Usando variables Docker
source .env.docker
python api/server.py
```

### 5. **Verificar API**
```bash
curl http://localhost:5001/api/health
# Debe mostrar propiedades con coordenadas reales
```

---

## 📊 **RESULTADOS ESPERADOS**

### **PostGIS Funcional Completo**
- ✅ `ST_X(coordenadas::geometry)` - Funciona
- ✅ `ST_Y(coordenadas::geometry)` - Funciona
- ✅ `ST_DWithin()` - Funciona
- ✅ Índices GIST - Creados
- ✅ Coordenadas reales - No NULL

### **Encoding Perfecto**
- ✅ Títulos: "Oportunidad de inversión" (no "inversi�n")
- ✅ UTF-8 español nativo (á, é, í, ó, ú, ñ)
- ✅ Sin caracteres corruptos
- ✅ psycopg2 directo funciona

### **Sistema Completo**
- ✅ 58+ propiedades con coordenadas
- ✅ Motor de recomendación geoespacial
- ✅ API REST funcional
- ✅ Sin wrappers ni workarounds

---

## 🔧 **CONFIGURACIÓN**

### **Variables de Entorno (`.env.docker`)**
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=citrino
DB_USER=citrino_app
DB_PASSWORD=citrino123

# UTF-8 nativo
PYTHONIOENCODING=utf-8
LANG=es_ES.UTF-8
LC_ALL=es_ES.UTF-8
```

### **Conexión psycopg2 Directa**
```python
import psycopg2
import os

# Cargar .env.docker
from dotenv import load_dotenv
load_dotenv('.env.docker')

# Conexión directa (SIN WRAPPERS!)
conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)

# Queries PostGIS funcionando
cursor = conn.cursor()
cursor.execute("""
    SELECT titulo, ST_X(coordenadas::geometry), ST_Y(coordenadas::geometry)
    FROM propiedades
    WHERE coordenadas IS NOT NULL
    LIMIT 5
""")
```

---

## 📋 **CHECKLIST DE VALIDACIÓN**

### **PostgreSQL + PostGIS**
- [ ] Container `citrino-postgresql` corriendo
- [ ] PostGIS versión 3.3+ instalada
- [ ] Extensión `postgis` habilitada
- [ ] Funciones espaciales funcionando

### **Datos y Coordenadas**
- [ ] Tabla `propiedades` creada con columna `coordenadas GEOGRAPHY`
- [ ] Índice GIST creado
- [ ] Coordenadas reales (no NULL)
- [ ] Queries espaciales funcionando

### **Encoding y Caracteres**
- [ ] UTF-8 español nativo
- [ ] Caracteres especiales: ñ, á, é, í, ó, ú
- [ ] Sin caracteres corruptos
- [ ] Títulos y descripciones legibles

### **API y Sistema**
- [ ] API conecta a PostgreSQL
- [ ] `/api/health` muestra datos reales
- [ ] Motor de recomendación operacional
- [ ] Frontend muestra propiedades

---

## 🔄 **MIGRACIÓN DESDE ORACLE CLOUD**

Si tienes datos en Oracle Cloud:

```bash
# 1. Configurar conexión Oracle Cloud (variables temporales)
export ORACLE_DB_HOST=tu_oracle_host
export ORACLE_DB_USER=tu_usuario
export ORACLE_DB_PASSWORD=tu_password

# 2. Ejecutar migración
python scripts/migrate_oracle_to_docker.py

# 3. Verificar resultados
docker exec -it citrino-postgresql psql -U citrino_app -d citrino -c "
    SELECT COUNT(*) as propiedades_migradas,
           COUNT(*) FILTER (WHERE coordenadas IS NOT NULL) as con_coordenadas
    FROM propiedades;
"
```

---

## 🎯 **FIN DEL LOOP**

**Problemas eliminados:**
- ❌ UnicodeDecodeError
- ❌ Coordenadas NULL
- ❌ PostGIS roto
- ❌ Encoding corrupto
- ❌ Wrappers temporales

**Sistema estable:**
- ✅ Ubuntu + UTF-8 nativo
- ✅ PostgreSQL + PostGIS completo
- ✅ psycopg2 directo
- ✅ Coordenadas reales
- ✅ Sin workarounds

**Listo para producción.**