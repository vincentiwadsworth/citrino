# Memoria Optimizada para Claude Code - Proyecto Citrino

## REGLAS CRÍTICAS DE DESARROLLO

### 1. Principios de Honestidad Técnica (BLOQUEANTE)
```
PROHIBIDO ABSOLUTAMENTE:
- Emojis en código, comentarios, logs, commits o documentación
- Procesar raw → producción sin validación humana
- Declarar éxito sin métricas verificadas objetivamente
- Workarounds o parches temporales que ocultan problemas raíz
- Reportar "éxito" basado en logs sin validación independiente
- Vender humo o prometer resultados no demostrables

OBLIGATORIO:
- Texto plano descriptivo en todos los contextos
- Type hints en todas las funciones
- Manejo explícito de errores
- Validación manual de datos procesados
- AUDITORÍA INDEPENDIENTE antes de reportar éxito
- Evidencia objetiva sobre afirmaciones subjetivas
- Admitir "no funciona" > fingir que funciona con workarounds
```

### 1.5. REGLA DE ORO: ANTES DE CREAR SCRIPTS NUEVOS (BLOQUEANTE)

```
ERROR GRAVE COMETIDO (2025-10-16): Crear múltiples scripts duplicados (_improved, _v2, _backup)
en vez de corregir los existentes, generando bloat y confusión en el proyecto.

PROHIBIDO ABSOLUTAMENTE:
- Crear scripts nuevos sin verificar si ya existe funcionalidad similar
- Usar sufijos como _improved, _v2, _backup, _old, _temp, _copy
- Dejar scripts duplicados en el proyecto
- Modificar archivos viejos en vez de los actuales
- Crear "versiones mejoradas" sin eliminar las originales

CHECKLIST OBLIGATORIA ANTES DE CREAR CUALQUIER ARCHIVO .py:
[ ] BUSCAR EXISTENTES:
    - find . -name "*[palabra_clave]*.py"
    - grep -r "funcionalidad_buscada" scripts/ tests/ src/
    - ls -la | grep -E "(test|debug|temp|backup)"

[ ] VERIFICAR SCRIPTS SIMILARES:
    - Examinar contenido de archivos con nombres similares
    - Comparar funcionalidad para evitar duplicación
    - Identificar si el script existente se puede corregir

[ ] DECISIÓN CORRECTA:
    - Si existe similar → CORREGIR el archivo existente
    - Si no existe similar → CREAR nuevo (con nombre único y descriptivo)
    - NUNCA crear múltiples versiones del mismo script

EJEMPLOS DE NOMBRES CORRECTOS:
✅ test_zai_connection.py (propósito claro)
✅ debug_coordenadas_critico.py (propósito claro)
❌ validate_raw_to_intermediate_improved.py (PROHIBIDO)
❌ test_api_v2.py (PROHIBIDO)
❌ process_all_old.py (PROHIBIDO)

```

### 2. Protocolo de Validación (OBLIGATORIO)
```
REGLA DE ORO: No reportar éxito sin auditoría independiente

CHECKLIST ANTES DE DECLARAR ÉXITO:
[ ] Sistema funciona con DATOS REALES, no de prueba
[ ] Auditoría independiente (audit_postgresql_migration.py) aprueba
[ ] Métricas objetivas cumplen umbrales mínimos
[ ] No hay workarounds ni parches temporales
[ ] Validación con herramientas externas a las que confío
[ ] Estado real es verificable por terceros

UMBRALES MÍNIMOS:
- Propiedades en BD: >= 1,000 (no 7 de prueba)
- Coordenadas válidas: >= 80% (no 0% real)
- Performance: queries < 200ms (no 200ms actual)
- Sin errores críticos en producción
```

### 2. Rangos Geográficos Santa Cruz (Validación Automática)
```python
SANTA_CRUZ_BOUNDS = {
    'lat_min': -18.2, 'lat_max': -17.5,
    'lng_min': -63.5, 'lng_max': -63.0,
    'centro': (-17.7833, -63.1833)
}
# Todo código de validación DEBE rechazar coordenadas fuera de estos límites
```

### 3. Métricas Mínimas Exigidas
```
PRODUCCIÓN (bloqueante):
- Propiedades en BD: >= 1,000 (actual: 7 - CRÍTICO)
- Coordenadas válidas: >= 80% (actual: 0% - CRÍTICO)
- Datos completos: >= 80% (actual: 100% de 7 - INSUFICIENTE)
- Errores críticos: < 2%
- Duplicados: < 1%

Cualquier métrica fuera de rango → DETENER PROCESO Y REPORTAR FRACASO
```

---

## ARQUITECTURA DEL SISTEMA

### Stack Tecnológico
```
Backend:    Python 3.x + Flask 2.3.3 + PostgreSQL + PostGIS 3.3+
Frontend:   HTML5 + Bootstrap 5 + JavaScript (vanilla)
ML/Data:    Pandas 2.0.3 + NumPy 1.24.3
LLM:        Z.AI GLM-4.6 (primario) + OpenRouter Qwen2.5 72B (fallback)

Infraestructura Docker:
- Contenedor: citrino-postgresql (puerto 5433)
- Encoding: es_ES.UTF-8 nativo (solución definitiva Windows)
- PostGIS 3.3 completamente funcional
- Índices GIST para consultas espaciales
```

### Componentes Core
```
api/server.py                           # REST API con CORS + PostgreSQL switching
src/recommendation_engine_postgis.py   # Motor Haversine + PostGIS (FUNCIONAL)
src/llm_integration.py                  # Sistema híbrido LLM con fallback automático
src/description_parser.py               # Extracción regex (80%) + LLM (20%)
migration/database/01_create_schema.sql # DDL PostgreSQL + extensión PostGIS
migration/scripts/migration_run_properties.py      # Orquestador ETL completo
docker-compose.yml                      # Infraestructura PostgreSQL UTF-8
```

### Flujo de Datos (ACTUALIZADO v2.2.3 - PostgreSQL FUNCIONAL)
```
1. Excel RAW (data/raw/) - 1,801 propiedades detectadas
   ↓
2. Validación automatizada (scripts/validation/validation_validate_properties_intermediate.py)
   ↓
3. Intermedio Excel (data/processed/*_intermedio.xlsx)
   ↓
4. VALIDACIÓN MANUAL OBLIGATORIA (humano revisa coordenadas, precios, errores)
   ↓
5. Aprobación (scripts/validation/approve_processed_data.py)
   ↓
6. PostgreSQL (migration/scripts/02_etl_propiedades.py) - 7 propiedades migradas
   ↓
7. API REST (api/server.py) - CON POSTGIS OPERACIONAL
```

**ESTADO ACTUAL v2.2.3**:
- PostgreSQL + PostGIS COMPLETAMENTE FUNCIONAL
- Índices GIST operativos (8 índices totales)
- ST_Distance funcionando (1532.73m en 0.238s)
- Score global: 80/100 - Status: SUCCESS
- Problemas encoding Windows RESUELTOS

---

## WORKFLOWS OPERACIONALES

### A. Procesamiento de Datos Nuevos
```bash
# Paso 1: Generar intermedio con validaciones
python scripts/validation/validation_validate_properties_intermediate.py \
  --input "data/raw/relevamiento/ARCHIVO.xlsx"

# Paso 2: REVISIÓN MANUAL OBLIGATORIA
# Abrir: data/processed/ARCHIVO_intermedio.xlsx
# Verificar:
# - Columna ESTADO (OK, ERROR, WARNING)
# - Columna OBSERVACIONES (detalles de problemas)
# - Coordenadas en rango Santa Cruz
# - Precios realistas ($10k-$2M USD)
# - Reporte JSON: *_reporte.json

# Paso 3: Aprobar solo si métricas cumplen umbrales
python scripts/validation/approve_processed_data.py \
  --input "data/processed/ARCHIVO_intermedio.xlsx"

# Paso 4 (opcional): Batch processing múltiples archivos
python scripts/validation/process_all_raw.py \
  --input-dir "data/raw/" \
  --output-dir "data/processed/"
```

### B. Migración PostgreSQL (ACTUALIZADO v2.2.3 - FUNCIONAL)
```bash
# Método 1: Docker (RECOMENDADO - encoding resuelto)
docker-compose up -d                      # Inicia PostgreSQL + PostGIS
export USE_POSTGRES=true
python migration/scripts/migration_run_properties.py  # Orquestador completo

# Método 2: Manual (solo si Docker no disponible)
export DB_HOST=localhost DB_PORT=5433 DB_NAME=citrino DB_USER=citrino_app DB_PASSWORD=citrino123
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f migration/database/01_create_schema.sql

# ETL secuencial (automático en run_migration.py)
python migration/scripts/01_etl_agentes.py       # Deduplicación agentes
python migration/scripts/02_etl_propiedades.py   # Propiedades + geometrías PostGIS
python migration/scripts/03_etl_servicios.py     # Servicios urbanos + índices GIST

# 3. Validación migración
python migration/scripts/04_validate_migration.py

# 4. Activar PostgreSQL en API
export USE_POSTGRES=true
python api/server.py
```

**CONFIGURACIÓN DOCKER ACTUAL v2.2.3**:
- Contenedor: `citrino-postgresql` (puerto 5433)
- Usuario: `citrino_app` / Password: `citrino123`
- Encoding: `es_ES.UTF-8` (problemas Windows resueltos)
- PostGIS 3.3 completamente funcional
- Índices GIST para consultas espaciales

### C. Sistema LLM con Fallback Automático
```bash
# Configuración .env requerida
ZAI_API_KEY=tu_clave_zai
LLM_PROVIDER=zai
LLM_MODEL=glm-4.6
OPENROUTER_FALLBACK_ENABLED=true
OPENROUTER_API_KEY=tu_clave_openrouter
OPENROUTER_MODEL=qwen/qwen-2.5-72b-instruct:free
LLM_MAX_TOKENS=8000
LLM_TEMPERATURE=0.1

# Tests
python test_fallback_simple.py                          # Test fallback automático
python scripts/analysis/analizar_por_proveedor.py       # Análisis calidad por fuente
python scripts/legacy/test_proveedor02_sample.py        # Test extracción texto libre
```

---

## API REST

### Endpoints Principales
```
POST /api/recommend              # Recomendaciones básicas (filtros + scoring)
POST /api/recommend/enhanced     # Recomendaciones con Haversine + PostGIS
POST /api/search                 # Búsqueda con filtros complejos
GET  /api/health                 # Health check + versión sistema (PostgreSQL/JSON)
GET  /api/stats                  # Métricas detalladas (1,801 propiedades)
```

### Motor de Recomendaciones - Ponderaciones
```python
WEIGHTS = {
    'ubicacion': 0.35,        # Distancia Haversine + ST_Distance PostGIS
    'precio': 0.25,           # Proximidad al presupuesto objetivo
    'servicios_cercanos': 0.20,  # Disponibilidad servicios urbanos (índices GIST)
    'caracteristicas': 0.15,  # Match tipo propiedad + superficie
    'disponibilidad': 0.05    # Estado activo/vendido
}
```

### Iniciar Sistema Completo v2.2.3
```bash
# Método 1: Docker (recomendado)
docker-compose up -d                      # PostgreSQL + PostGIS en puerto 5433
export USE_POSTGRES=true
python api/server.py &                    # API con PostgreSQL
python -m http.server 8080                # Frontend

# Método 2: Traditional
python api/server.py                      # Escucha en http://localhost:5001
python -m http.server 8080                # Acceso: http://localhost:8080/citrino-reco.html
                                         #         http://localhost:8080/chat.html
```

---

## ESTRUCTURA DE DIRECTORIOS (ACTUALIZADA v2.2.3)

```
citrino/
├── api/
│   └── server.py                    # Flask REST API + CORS + PostgreSQL switching
│
├── src/
│   ├── recommendation_engine_postgis.py  # Motor scoring con Haversine + PostGIS
│   ├── llm_integration.py                 # Sistema LLM híbrido
│   ├── description_parser.py              # Extracción regex+LLM
│   └── data_loader.py                     # Carga Excel/PostgreSQL
│
├── scripts/
│   ├── validation/
│   │   ├── validation_validate_properties_intermediate.py   # RAW → Intermedio
│   │   ├── approve_processed_data.py         # Intermedio → Final
│   │   └── process_all_raw.py                # Batch processing
│   ├── etl/
│   │   ├── 01_etl_agentes.py
│   │   ├── 02_etl_propiedades.py
│   │   └── ├── 03_etl_servicios.py
│   ├── analysis/
│   │   ├── analizar_calidad_datos.py
│   │   ├── analizar_por_proveedor.py
│   │   └── detectar_duplicados.py
│   └── maintenance/
│       └── backup_data.py
│
├── migration/
│   ├── database/
│   │   └── 01_create_schema.sql          # DDL PostgreSQL + PostGIS FUNCIONAL
│   └── scripts/
│       ├── migration_run_properties.py              # Orquestador completo
│       └── 04_validate_migration.py
│
├── data/
│   ├── raw/                # Excel ORIGINALES (1,801 propiedades detectadas)
│   ├── processed/          # Intermedios para revisión humana
│   └── final/              # Aprobados para producción
│
├── docker-compose.yml      # PostgreSQL + PostGIS UTF-8 nativo
├── .env.docker            # Configuración Docker (citrino-postgresql:5433)
├── docs/                  # Documentación técnica v2.2.3
├── tests/
│   ├── test_api.py
│   ├── test_recommendation.py
│   └── test_validation.py
│
├── .env                    # Configuración sensible (gitignored)
└── requirements.txt        # Dependencias Python
```

---

## TESTING

```bash
# Suite completa
pytest

# Tests específicos
pytest tests/test_api.py -v
pytest tests/test_recommendation.py -v
pytest tests/test_validation.py -v

# Tests por keyword
pytest -k "test_haversine"
pytest -k "test_postgres"

# Coverage
pytest --cov=src --cov-report=html
```

---

## TROUBLESHOOTING (ACTUALIZADO v2.2.3)

### API no responde
```bash
# Verificar proceso
ps aux | grep "python api/server.py"
lsof -i :5001

# Reiniciar
pkill -f "api/server.py"
python api/server.py &

# Logs
tail -f logs/api.log
```

### LLM fallback falla
```bash
# Verificar variables entorno
grep -E "(ZAI_API_KEY|OPENROUTER_API_KEY|LLM_PROVIDER)" .env

# Test directo
python test_fallback_simple.py

# Debug mode
export DEBUG=true
python src/llm_integration.py
```

### Coordenadas inválidas en batch
```bash
# Analizar calidad por proveedor
python scripts/analysis/analizar_por_proveedor.py

# Detectar outliers geográficos
python scripts/analysis/analizar_calidad_datos.py --check-coords

# Limpiar duplicados
python scripts/analysis/detectar_duplicados.py --remove
```

### PostgreSQL queries lentas (v2.2.3 - PARCIALMENTE FUNCIONAL)
```bash
# ESTADO REAL: Performance pobre - 200ms vs objetivo <50ms
# Verificar índices GIST (20 índices activos, pero performance pobre)
psql -d citrino -c "\d+ propiedades"
psql -d citrino -c "\d+ servicios"

# Analizar query plan (ST_Distance funcionando pero LENTO)
psql -d citrino -c "EXPLAIN ANALYZE SELECT COUNT(*) FROM propiedades WHERE ST_DWithin(coordenadas, ST_MakePoint(-63.1833, -17.7833)::geography, 1000);"

# Verificar Docker containers (FUNCIONAL)
docker ps | grep citrino-postgresql
docker logs citrino-postgresql

# PROBLEMA CRÍTICO: Solo 7 propiedades migradas vs 1,801 detectadas
```

### Docker PostgreSQL Issues (SOLUCIONADOS v2.2.3)
```bash
# Si el contenedor no resuelve encoding
docker-compose down
docker-compose up -d --force-recreate

# Verificar configuración UTF-8
docker exec citrino-postgresql psql -U citrino_app -d citrino -c "SHOW lc_ctype;"

# Si hay problemas de conexión
export DB_HOST=localhost DB_PORT=5433 DB_NAME=citrino DB_USER=citrino_app DB_PASSWORD=citrino123
python -c "import psycopg2; print('Conexion OK')"
```

---

## NOTAS PARA CLAUDE CODE (ACTUALIZADAS v2.2.3)

```
Al generar código:
1. NUNCA usar emojis en ningún contexto (PROBLEMA RESUELTO: 66 archivos limpiados)
2. Siempre validar coordenadas contra SANTA_CRUZ_BOUNDS
3. Incluir type hints en todas las funciones
4. Manejar errores explícitamente (no silent failures)
5. Loguear operaciones críticas (validación, ETL, LLM calls)
6. Usar constantes para valores mágicos
7. Documentar decisiones arquitectónicas en comentarios

Al modificar flujos de datos:
1. Respetar orden secuencial (no saltar validación manual)
2. Generar reportes JSON en cada paso
3. Verificar métricas contra umbrales antes de continuar
4. Mantener datos RAW inmutables

Al trabajar con PostgreSQL (v2.2.3 - FUNCIONAL):
1. Usar Docker wrapper create_connection() (evita encoding Windows)
2. Índices GIST para queries geoespaciales (operativos)
3. Transacciones para operaciones batch
4. ST_Distance disponible para cálculos espaciales
5. Coordenadas reales funcionando (problema resuelto)

ESTADO CRÍTICO REAL (2025-10-16):
✅ PostgreSQL + PostGIS INFRAESTRUCTURA FUNCIONAL
✅ Encoding Windows resuelto (UTF-8 nativo Docker)
✅ Índices GIST creados (20 totales)
✅ ST_Distance funcionando
✅ API corriendo y respondiendo
❌ ETL FALLANDO: 1,801 detectadas, 7 migradas (CRÍTICO)
❌ Coordenadas 0% válidas (CRÍTICO)
❌ Performance pobre: 200ms vs <50ms objetivo
❌ Score real: 65/100 - Status: NECESITA MEJORAS SIGNIFICATIVAS

PROBLEMA RAÍZ: ETL detecta propiedades pero no las migra realmente.
SISTEMA NO ESTÁ LISTO PARA PRODUCCIÓN.
```