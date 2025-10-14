# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Citrino es una herramienta interna que el equipo de la empresa utiliza para analizar y recomendar propiedades de inversión en Santa Cruz de la Sierra, Bolivia. El sistema combina análisis de datos, geolocalización precisa y los algoritmos implementados en este repositorio para apoyar el trabajo de consultoría con los clientes de Citrino.

### Enfoque Principal
- **Objetivo**: Herramienta de trabajo para el equipo de Citrino al atender a sus clientes inversores (no orientada al público general)
- **Datos procesados**: Conjuntos JSON mantenidos por Citrino con propiedades y servicios urbanos actualizados
- **Usuarios internos**: Analistas de datos, consultores de inversión y equipo comercial de Citrino
- **Criterios de análisis**: Ponderaciones configurables, cobertura de servicios cercanos y cálculos basados en distancias Haversine

### Tecnología Principal
- **Backend**: Python 3.x con Flask 2.3.3 para REST API
- **Frontend**: HTML5 + Bootstrap 5 + JavaScript moderno
- **Procesamiento**: Pandas + NumPy para análisis de datos de mercado
- **Geolocalización**: Algoritmo Haversine para cálculos precisos
- **LLM Primario**: Z.AI GLM-4.6 para análisis y extracción de datos
- **LLM Fallback**: OpenRouter con Qwen2.5 72B (gratuito, 2025)
- **Extracción Híbrida**: Sistema Regex + LLM (80% sin LLM, 90% reducción tokens)
- **Datos**: JSON con 1,583 propiedades + 4,777 servicios urbanos

## Technology Stack

### Backend
- **Python 3.x** with Flask 2.3.3 for REST API
- **Pandas 2.0.3** and **NumPy 1.24.3** for data processing
- **Geospatial processing**: Custom Haversine distance calculation
- **openpyxl 3.1.2** for Excel file handling
- **flask-cors 4.0.0** for cross-origin requests

### Frontend & Demo
- **Streamlit** for web demo application
- **Typer + Rich** for CLI interface
- Responsive design with professional UI

### Data Storage
- **JSON format** (implementación actual - siendo migrada)
- **PostgreSQL + PostGIS** (en proceso de migración - ver `MIGRATION_PLAN.md`)
- **1,588 propiedades** + **4,777 servicios urbanos** (escala actual)

### Arquitectura del Sistema

#### Componentes Principales

1. **API Server** (`api/server.py`)
   - Flask REST API con CORS para inversores
   - Endpoints especializados en análisis de inversión
   - Integración con datos de scraping actualizados
   - Sistema de caché para análisis de mercado

2. **Motores de Recomendación**
   - **Motor de Inversión** (`src/recommendation_engine.py`): Filtrado y puntuación de propiedades según criterios del perfil
   - **Motor Mejorado** (`src/recommendation_engine_mejorado.py`): Georreferenciación con distancias Haversine y verificación de servicios cercanos
   - **Sistema de Ponderación**: Pesos configurables (ubicación 35%, precio 25%, servicios 20%, características 15%, disponibilidad 5%) definidos en el código

3. **Sistema Geoespacial**
   - **Algoritmo Haversine**: Cálculo de distancias precisas
   - **Análisis de Zonas**: Evaluación de servicios y cobertura por área
   - **Optimización de Rendimiento**: Índices espaciales para consultas eficientes

4. **Frontend HTML Moderno** (`index.html`, `citrino-reco.html`, `chat.html`)
   - Interfaz interna con enfoque en Citrino Reco (notas + recomendaciones) y Citrino Chat (conversaciones sobre datos)
   - Flujo integrado para registrar hallazgos, obtener coincidencias y profundizar con consultas libres
   - Preparado para conectar una capa LLM (suscripción planificada a z.ai)

#### Arquitectura de Datos
```
/data/
├── base_datos_relevamiento.json          # JSON actual (siendo migrado)
├── guia_urbana_municipal_completa.json   # Servicios urbanos (4,777)
└── perfiles_inversion/                   # Plantillas de perfiles

# Nueva estructura en migración:
/migration/
├── scripts/           # Scripts ETL para PostgreSQL
├── database/          # DDL y esquemas SQL
└── config/           # Configuración conexión

# PostgreSQL (target):
- agentes (tabla normalizada)
- propiedades (con coordenadas GEOGRAPHY + PostGIS)
- servicios (con índices espaciales GIST)
```

#### Directorios Clave
- **`api/`** - Servidor REST y endpoints
- **`src/`** - Motores de recomendación, lógica de negocio e integración LLM
  - `llm_integration.py` - Sistema LLM con fallback automático a OpenRouter
  - `description_parser.py` - Sistema híbrido Regex + LLM para extracción
  - `recommendation_engine_mejorado.py` - Motor con geolocalización Haversine
- **`scripts/`** - ETL, procesamiento y análisis de datos
  - `build_relevamiento_dataset.py` - ETL con sistema híbrido de extracción
- **`migration/`** - Scripts y configuración para migración PostgreSQL
  - `scripts/etl_*.py` - Scripts ETL para agentes, propiedades, servicios
  - `database/01_create_schema.sql` - DDL PostgreSQL + PostGIS
- **`tests/`** - Suite de pruebas completa
- **`data/`** - Datos JSON actuales (en proceso de migración)
- **`assets/`** - CSS y JavaScript del frontend
- **`docs/`** - Documentación técnica organizada
  - `CHANGELOG.md` - Historial de versiones (nuevo)
  - `SCRUM_BOARD.md` - Gestión de sprint actual (nuevo)
  - `COMMITS_PLAN.md` - Planificación detallada de commits (nuevo)
  - `WORKFLOW.md` - Guía de flujo por commits (nuevo)
  - `DATA_ARCHITECTURE.md` - Arquitectura y migración PostgreSQL (actualizado)
  - `MIGRATION_PLAN.md` - Plan detallado de migración (nuevo)

## Comandos de Desarrollo

### Inicio Rápido (Recomendado)
```bash
# Ejecutar pruebas rápidas
pytest

# Iniciar sistema completo (API + Frontend)
# Nota: Los scripts individuales están abajo si necesitas control manual

# Acceso: http://localhost:8080/ (UI HTML para inversores)
```

### Desarrollo Manual
```bash
# Iniciar API para inversores (port 5001)
python -c "import sys; sys.path.append('api'); from server import app; app.run(debug=False, host='0.0.0.0', port=5001)"

# Iniciar frontend HTML (port 8080)
python -m http.server 8080

# Acceso: http://localhost:8080/ (HTML moderno para inversores)
```

### Procesamiento de Datos
```bash
# Construir dataset de relevamiento (Excel -> JSON)
python scripts/build_relevamiento_dataset.py

# Construir dataset de servicios urbanos
python scripts/build_urban_services_dataset.py

# Generar inventario de ejemplo para demostraciones
python scripts/build_sample_inventory.py
```

### CLI para Inversores
```bash
# Acceder a ayuda CLI
python src/cli.py --help

# Consultar propiedades de inversión
python src/cli.py query --zona "Equipetrol" --tipo-inversion "desarrollo" --presupuesto-max 500000

# Análisis de lenguaje natural para inversores
python src/cli.py natural-query "busco propiedad con potencial de plusvalía en zona norte"
```

### Sistema LLM con Fallback Automático (2025)
```bash
# Test del sistema de fallback
python test_fallback_simple.py

# Test de extracción con muestras del Proveedor 02
python scripts/test_proveedor02_sample.py

# Análisis de calidad de datos por proveedor
python scripts/analizar_por_proveedor.py
```

**Configuración requerida en `.env`:**
```bash
# Proveedor primario (Z.AI)
ZAI_API_KEY=tu_clave_zai_aqui
LLM_PROVIDER=zai
LLM_MODEL=glm-4.6

# Fallback automático (OpenRouter)
OPENROUTER_FALLBACK_ENABLED=true
OPENROUTER_API_KEY=tu_clave_openrouter_aqui
OPENROUTER_MODEL=qwen/qwen-2.5-72b-instruct:free

# Configuración general
LLM_MAX_TOKENS=8000
LLM_TEMPERATURE=0.1
```

**Modelos gratuitos recomendados 2025:**
- `qwen/qwen-2.5-72b-instruct:free` - Optimizado para JSON (recomendado)
- `deepseek/deepseek-r1:free` - Razonamiento superior
- `meta-llama/llama-4-maverick:free` - Multimodal, 400B parámetros
- `meta-llama/llama-4-scout:free` - Contexto masivo (512K tokens)

## Architecture Overview

### Core Components

1. **API Server** (`api/server.py`)
   - Flask REST API with CORS support
   - Health check endpoints
   - Integration with both recommendation engines
   - Real-time property loading and caching

2. **Recommendation Engines**
   - **Original Engine** (`src/recommendation_engine.py`): Basic matching algorithm
   - **Enhanced Engine** (`src/recommendation_engine_mejorado.py`): Advanced geospatial recommendations with Haversine distance calculation
   - **Weight System**: Budget (25%), Family (20%), Services (30%), Demographics (15%), Preferences (10%)

3. **LLM Integration System** (`src/llm_integration.py`, `src/description_parser.py`)
   - **Primary Provider**: Z.AI GLM-4.6 for data extraction and analysis
   - **Automatic Fallback**: OpenRouter with Qwen2.5 72B (free) on rate limits/errors
   - **Error Detection**: Automatic detection of 429 (rate limit), 500/502/503 (server errors)
   - **Smart Extraction**: Parses free-text descriptions into structured JSON fields
   - **Cache System**: LRU caching to reduce API costs and improve performance
   - **Statistics Tracking**: Monitors provider usage, fallback rate, cache hits
   - **Use Cases**: 
     - Provider 02 data extraction (1,579 properties in free-text)
     - ETL processing with high-volume LLM queries
     - Resilience against API limitations

3. **Geospatial System**
   - **Haversine Algorithm**: Real-distance calculation between coordinates
   - **Spatial Indexing**: Efficient service proximity lookup
   - **Performance Considerations**: Pre-filtrado por zona para reducir cálculos innecesarios

4. **Demo Application** (`demo_stable.py`)
   - Professional welcome screen with 6 prospect profiles
   - Real-time API integration
   - Meeting tools and emergency procedures

### Data Architecture

```
/data/
├── base_datos_citrino_limpios.json    # Main database (76,853 properties)
├── guia_urbana_municipal_completa.json # 4,777 urban services
├── bd_final/                          # Cleaned final datasets
├── bd_franz/                          # Franz database exports
├── bd_integrada/                      # Integrated datasets
└── perfiles/                          # User profile templates
```

### Key Directories

- **`api/`** - REST API server and endpoints
- **`src/`** - Core recommendation engines and business logic
- **`scripts/`** - Data processing, validation, and evaluation tools
- **`tests/`** - Test suite for API and recommendation engines
- **`data/`** - All data files and databases
- **`documentation/`** - Technical documentation and evaluation reports

## API Endpoints

### Health & Status
- `GET /api/health` - System health check with property count
- `GET /api/stats` - Detailed system statistics

### Property Operations
- `POST /api/search` - Search properties with filters
- `POST /api/recommend` - Get property recommendations
- `POST /api/recommend/enhanced` - Get enhanced geo-based recommendations

### Data Management
- `GET /api/zones` - List available zones
- `GET /api/property/:id` - Get specific property details

## Testing

### Test Structure
- **`test_api.py`** - Comprehensive API endpoint testing
- **`test_api_simple.py`** - Basic API smoke checks (manual helper)

### Running Tests
```bash
# Run all tests
pytest

# Test specific components
pytest tests/test_api.py -v
pytest tests/test_api_simple.py -v
```

## Performance Optimization

### Caching Strategy
- LRU caching for distance calculations
- Thread-safe cache with locks
- Spatial indexing for service lookups
- Zone pre-filtering to avoid unnecessary operations

### Monitoring
- Real-time performance metrics in `stats` dictionary
- Cache hit ratios and calculation counts
- Response time tracking
- Memory usage optimization

## Data Processing Workflows

### ETL Pipeline
1. **Raw Data Import** - Excel and JSON files from multiple sources
2. **Data Cleaning** - Unicode normalization, extreme value handling
3. **Geolocation Processing** - Coordinate validation and spatial indexing
4. **Integration** - Combining Franz database with municipal data
5. **Validation** - Quality checks and deduplication

### Key Processing Scripts
- **`build_relevamiento_dataset.py`** - Main data processing pipeline (scraping Excel → JSON)
- **`build_urban_services_dataset.py`** - Municipal urban guide integration
- **`build_sample_inventory.py`** - Sample inventory generator for demos/tests

## Development Guidelines

### Code Organization
- Follow existing module structure in `src/`
- Use type hints for all function signatures
- Implement proper error handling and logging
- Maintain thread safety for cached data

### CRITICAL: PROHIBICIÓN ABSOLUTA DE EMOJIS
**ESTRICTAMENTE PROHIBIDO usar emojis en cualquier código, comentarios, logs o documentación.**
- **MOTIVO**: Los emojis consumen una cantidad excesiva e innecesaria de tokens y violan las mejores prácticas
- **REGLA**: Texto plano únicamente. Sin caracteres Unicode innecesarios bajo NINGUNA circunstancia
- **CONSECUENCIA**: Violación GRAVE de las mejores prácticas de desarrollo - NUNCA usar emojis
- **ALTERNATIVAS**: Use texto descriptivo en lugar de símbolos SIEMPRE
  - ERROR: "Error" (NUNCA usar emojis)
  - SUCCESS: "Success" (NUNCA usar emojis)
  - WARNING: "Warning" (NUNCA usar emojis)
  - FILE: "File" (NUNCA usar emojis)
- **IMPORTANTE**: Esta regla es INFLEXIBLE y se aplica a TODO el código, comentarios, logs y documentación

### Data Handling
- Always validate coordinates before distance calculations
- Use the Haversine formula for geographic distances
- Implement proper UTF-8 encoding for Spanish text
- Cache expensive calculations to improve performance

### API Development
- Use Flask-CORS for all endpoints
- Implement proper JSON responses with error codes
- Validate input parameters before processing
- Return consistent response formats

### Testing Requirements
- Write unit tests for new recommendation algorithms
- Test API endpoints with various input combinations
- Validate data processing scripts with sample data
- Performance test with large datasets

## Meeting & Demo Procedures

### Emergency Commands
```bash
# Manual recovery steps
python api/server.py &          # Start API in background
streamlit run demo_stable.py    # Start demo interface
```

### Demo Features
- 6 perfiles de referencia preparados por el equipo de Citrino
- Consultas directas a la API de recomendaciones
- Pantalla de bienvenida y UI alineadas con los flujos internos

## Migration to PostgreSQL + PostGIS (2025)

### Current Status: In Progress
- **Target**: PostgreSQL 15+ con PostGIS 3.3+
- **Source**: 1,588 propiedades + 4,777 servicios urbanos
- **Goal**: Queries geoespaciales de segundos → milisegundos
- **Based on**: Investigación experta con Tongyi

### Nueva Arquitectura de Datos
```sql
-- Tablas principales con PostGIS
CREATE TABLE propiedades (
    id BIGSERIAL PRIMARY KEY,
    coordenadas GEOGRAPHY(POINT, 4326) NOT NULL,
    -- Indices GIST para búsquedas espaciales
);

CREATE TABLE servicios (
    id BIGSERIAL PRIMARY KEY,
    coordenadas GEOGRAPHY(POINT, 4326) NOT NULL,
    -- Optimizado para ST_DWithin queries
);
```

### Scripts de Migración
- `migration/scripts/01_etl_agentes.py` - Deduplicación de agentes
- `migration/scripts/02_etl_propiedades.py` - Migración con coordenadas PostGIS
- `migration/scripts/03_etl_servicios.py` - Servicios urbanos con índices
- `migration/scripts/04_validate_migration.py` - Validación completa

### Plan de Ejecución
```bash
# 1. Preparar PostgreSQL
export DB_HOST=localhost DB_NAME=citrino DB_USER=postgres
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f migration/database/01_create_schema.sql

# 2. Ejecutar ETLs
python migration/scripts/01_etl_agentes.py
python migration/scripts/02_etl_propiedades.py
python migration/scripts/03_etl_servicios.py

# 3. Validar
python migration/scripts/04_validate_migration.py

# 4. Activar nuevo sistema
export USE_POSTGRES=true
python api/server.py
```

### Documentación Completa
- **`DATA_ARCHITECTURE.md`** - Arquitectura completa y transformación de queries
- **`MIGRATION_PLAN.md`** - DDL completo, scripts ETL y validación
- **`COMMITS_PLAN.md`** - Plan detallado de implementación por commits

## Future Development

### Post-Migration Enhancements
- Motor de recomendación optimizado para PostGIS
- Capacidades analíticas avanzadas con SQL espacial
- Dashboard en tiempo real con consultas complejas
- Sistema de actualizaciones incrementales concurrentes

### Data Quality Improvements
- Deduplicación automática con algoritmos mejorados
- Validación de coordenadas geoespaciales
- Sistema de confianza por proveedor de datos
- Monitoreo de calidad en tiempo real