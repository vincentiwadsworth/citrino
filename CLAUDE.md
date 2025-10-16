**Citrino** - Sistema de análisis de inversión inmobiliaria para Santa Cruz, Bolivia.

## Quick Start

```bash
# Iniciar sistema completo
python api/server.py &                    # API en puerto 5001
python -m http.server 8080                # Frontend en puerto 8080

# Validar datos nuevos (workflow principal)
python scripts/validation/validate_raw_to_intermediate.py --input "data/raw/relevamiento/ARCHIVO.xlsx"
# → Revisar output en data/processed/ARCHIVO_intermedio.xlsx
# → Aprobar: python scripts/validation/approve_processed_data.py --input "data/processed/ARCHIVO_intermedio.xlsx"

# Testing
pytest                                     # Suite completa
```

---

## Arquitectura Core

### Stack Tecnológico

**Backend**
- Python 3.x + Flask 2.3.3 (REST API)
- PostgreSQL + PostGIS 3.3+ (datos geoespaciales)
- Pandas 2.0.3 + NumPy 1.24.3 (procesamiento)

**Frontend**
- HTML5 + Bootstrap 5 + JavaScript moderno
- Interfaces: `citrino-reco.html` (recomendaciones) + `chat.html` (consultas)

**LLM System**
- **Primario**: Z.AI GLM-4.6
- **Fallback automático**: OpenRouter (Qwen2.5 72B free)
- **Sistema híbrido**: 80% Regex, 20% LLM (90% reducción tokens)
- **Uso**: Extracción de datos del Proveedor 02 (1,579 propiedades texto libre)

### Componentes Principales

```
api/server.py                    → REST API con CORS
src/recommendation_engine_mejorado.py → Motor con Haversine + geolocalización
src/llm_integration.py          → Sistema LLM con fallback
src/description_parser.py       → Extracción híbrida Regex+LLM
migration/                      → PostgreSQL + PostGIS setup
```

### Flujo de Datos

```
Excel RAW → Validación → Intermedio (revisión humana) → PostgreSQL → API
   ↓            ↓              ↓                           ↓          ↓
raw/    processed/    *_intermedio.xlsx              propiedades   /api/recommend
guia/   *_reporte.json                              servicios
```

---

## Workflows Críticos

### 1. Procesamiento de Datos Nuevos

**⚠️ NUNCA procesar raw → producción directo. SIEMPRE pasar por validación humana.**

```bash
# Paso 1: Generar intermedio
python scripts/validation/validate_raw_to_intermediate.py \
  --input "data/raw/relevamiento/2025.08.15 05.xlsx"
# Output: data/processed/2025.08.15 05_intermedio.xlsx + reporte.json

# Paso 2: VALIDACIÓN MANUAL OBLIGATORIA
# - Abrir Excel intermedio
# - Verificar coordenadas en rango Santa Cruz (-17.5/-18.2, -63.0/-63.5)
# - Validar precios realistas ($10k-$2M)
# - Revisar columna ESTADO y OBSERVACIONES
# - Confirmar >90% coordenadas válidas, <2% errores críticos

# Paso 3: Aprobar solo si pasa validación
python scripts/validation/approve_processed_data.py \
  --input "data/processed/2025.08.15 05_intermedio.xlsx"
```

**Batch processing:**
```bash
python scripts/validation/process_all_raw.py \
  --input-dir "data/raw/" --output-dir "data/processed/"
```

### 2. Migración PostgreSQL

```bash
# Setup inicial
export DB_HOST=localhost DB_NAME=citrino DB_USER=postgres
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f migration/database/01_create_schema.sql

# ETL secuencial
python migration/scripts/01_etl_agentes.py      # Deduplicación agentes
python migration/scripts/02_etl_propiedades.py  # Propiedades + PostGIS
python migration/scripts/03_etl_servicios.py    # Servicios urbanos

# Validación
python migration/scripts/04_validate_migration.py

# Activar
export USE_POSTGRES=true
python api/server.py
```

### 3. Sistema LLM con Fallback

```bash
# Test fallback automático
python test_fallback_simple.py

# Análisis por proveedor
python scripts/analysis/analizar_por_proveedor.py

# Test extracción Proveedor 02
python scripts/legacy/test_proveedor02_sample.py
```

**Configuración `.env` requerida:**
```bash
# Primario
ZAI_API_KEY=tu_clave
LLM_PROVIDER=zai
LLM_MODEL=glm-4.6

# Fallback
OPENROUTER_FALLBACK_ENABLED=true
OPENROUTER_API_KEY=tu_clave
OPENROUTER_MODEL=qwen/qwen-2.5-72b-instruct:free

# Config
LLM_MAX_TOKENS=8000
LLM_TEMPERATURE=0.1
```

---

## API Endpoints

### Principales
```
POST /api/recommend              → Recomendaciones básicas
POST /api/recommend/enhanced     → Recomendaciones con Haversine
POST /api/search                 → Búsqueda con filtros
GET  /api/health                 → Estado del sistema
GET  /api/stats                  → Métricas detalladas
```

### Ponderaciones del Motor
- Ubicación: 35%
- Precio: 25%
- Servicios cercanos: 20%
- Características: 15%
- Disponibilidad: 5%

---

## Estructura de Directorios

```
api/                    → REST API Flask
src/                    → Lógica de negocio
  ├── recommendation_engine_mejorado.py  → Motor principal
  ├── llm_integration.py                 → Sistema LLM
  └── description_parser.py              → Extracción híbrida

scripts/
  ├── validation/       → Procesamiento raw → intermedio
  ├── etl/             → Migración PostgreSQL
  ├── analysis/        → Análisis de calidad
  └── maintenance/     → Utilidades

migration/
  ├── database/        → DDL PostgreSQL + PostGIS
  └── scripts/         → ETL scripts

data/
  ├── raw/             → Excel ORIGINALES (no modificar)
  ├── processed/       → Intermedios para revisión
  └── final/           → Aprobados para producción

docs/                  → Documentación técnica
tests/                 → Suite de pruebas
```

---

## Reglas de Calidad NO NEGOCIABLES

### 1. Código Limpio
- **❌ PROHIBIDO**: Emojis en código/comentarios/logs/docs
- **✓ USAR**: Texto plano descriptivo siempre
- **RAZÓN**: Desperdicio de tokens, viola mejores prácticas

### 2. Validación Obligatoria
- **❌ PROHIBIDO**: Declarar éxito sin validación manual
- **✓ REQUERIDO**: Inspección humana de datos procesados
- **CHECKLIST**:
  - [ ] Coordenadas en rango Santa Cruz
  - [ ] Precios realistas para zona
  - [ ] >90% coordenadas válidas
  - [ ] <2% errores críticos

### 3. Rangos Geográficos Santa Cruz
```
Centro: -17.7833°, -63.1833°
Rango válido: Lat [-17.5, -18.2], Lng [-63.0, -63.5]
Validación mínima: 95% dentro de rango
```

### 4. Métricas Mínimas Exigidas
```
Coordenadas válidas:  >90% (obligatorio)
Datos completos:      >80% (obligatorio)
Errores críticos:     <2% (obligatorio)
```

**Si no cumple → REPROCESAR inmediatamente**

---

## Development Guidelines

### Nuevas Features
1. Implementar en `src/` siguiendo módulos existentes
2. Usar type hints en todas las funciones
3. Manejar errores explícitamente
4. Thread-safety para datos cacheados

### Testing
```bash
pytest                              # Suite completa
pytest tests/test_api.py -v        # API específica
pytest -k "test_recommendation"    # Tests de recomendación
```

### Performance
- Caché LRU para cálculos costosos
- Pre-filtrado por zona antes de Haversine
- Índices GIST para PostGIS
- Paginación en queries grandes

---

## Documentación Adicional

```
docs/CHANGELOG.md           → Historial de versiones
docs/SCRUM_BOARD.md        → Sprint actual
docs/COMMITS_PLAN.md       → Planificación detallada
docs/WORKFLOW.md           → Flujo por commits
docs/DATA_ARCHITECTURE.md  → Arquitectura PostgreSQL
docs/MIGRATION_PLAN.md     → Plan migración completo
```

---

## Troubleshooting

### API no responde
```bash
# Verificar procesos
ps aux | grep "python api/server.py"
lsof -i :5001

# Reiniciar
pkill -f "api/server.py"
python api/server.py &
```

### LLM fallback no funciona
```bash
# Verificar keys en .env
grep -E "(ZAI_API_KEY|OPENROUTER_API_KEY)" .env

# Test directo
python test_fallback_simple.py
```

### Coordenadas fuera de rango
```bash
# Analizar calidad
python scripts/analysis/analizar_calidad_datos.py

# Detectar duplicados
python scripts/analysis/detectar_duplicados.py
```

---

## Notas de Contexto

**Usuarios**: Equipo interno Citrino (analistas, consultores, comerciales)  
**Propósito**: Herramienta de trabajo para atención a clientes inversores  
**Datos**: 1,588 propiedades + 4,777 servicios urbanos en Santa Cruz  
**Estado**: Migración PostgreSQL en progreso, Excel RAW como fuente actual  

**Próximos hitos**:
- [ ] Completar migración PostgreSQL + PostGIS
- [ ] Optimizar queries geoespaciales (segundos → milisegundos)
- [ ] Dashboard tiempo real con SQL espacial
- [ ] Sistema actualizaciones incrementales