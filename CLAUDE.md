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
- **Datos**: JSON con propiedades procesadas de scraping

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
- **JSON format** (implementación actual con datos de scraping)
- **PostgreSQL** planeado para futura migración
- **1.58MB** datos procesados de propiedades de inversión

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

4. **Frontend HTML Moderno** (`index.html`, `chat.html`, `perfil.html`, `results.html`)
   - Interfaz interna para presentar resultados al equipo de Citrino y sus clientes inversores
   - Sistema de captura y revisión de perfiles de inversión
   - Análisis visual de oportunidades a partir de los datos procesados

#### Arquitectura de Datos
```
/data/
├── base_datos_relevamiento.json    # Base de datos de scraping (1,583 propiedades)
├── data/processed/                 # Datos procesados y validados
└── perfiles_inversion/               # Plantillas de perfiles de inversores
```

#### Directorios Clave
- **`api/`** - Servidor REST y endpoints para inversores
- **`src/`** - Motores de recomendación y lógica de inversión
- **`scripts/`** - Procesamiento de datos y análisis de mercado
- **`tests/` - Suite de pruebas para el sistema de inversión
- **`data/`** - Todos los archivos de datos de inversión
- **`assets/`** - CSS y JavaScript del frontend moderno

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
- Emergency meeting instructions in `instrucciones_reunion.txt`

## Future Development

### Planned Enhancements
- PostgreSQL migration for better performance
- LLM integration for natural language queries
- Mobile app for real estate agents
- Advanced analytics dashboard
- WhatsApp integration for notifications

### Data Quality Improvements
- Repair 46.6% of corrupted zones
- Implement automatic validation controls
- Intelligent deduplication between data sources
- Real-time quality monitoring dashboard