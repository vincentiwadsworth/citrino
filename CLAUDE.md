# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Citrino is an advanced real estate recommendation system for Santa Cruz de la Sierra, Bolivia, that uses AI, precise geolocation, and municipal data to provide intelligent property recommendations. The system processes 76,853 properties with exact coordinates and 4,777 urban services to achieve 85-96% recommendation accuracy.

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
- **JSON format** (current implementation)
- **PostgreSQL** planned for future migration
- **128MB main database** (4.6M lines)

## Development Commands

### Quick Start (Recommended for Demos)
```bash
# Verify system status
python verificar_servicios.py

# Start everything automatically
./iniciar_demo.bat

# Access demo at: http://localhost:8501
```

### Manual Development Setup
```bash
# Install dependencies
pip install -r requirements_api.txt

# Start API server (port 5000)
python api/server.py

# Start Streamlit demo (port 8501)
streamlit run demo_stable.py

# Run tests
python -m pytest tests/

# Test API endpoints
python tests/test_api.py
```

### Data Processing Commands
```bash
# Process property data
python scripts/procesar_datos_citrino.py

# Validate datasets
python scripts/validar_dataset_mejorado.py

# Evaluate system performance
python scripts/evaluacion_completa_sistema.py

# Benchmark recommendation engine
python scripts/benchmar_rendimiento.py
```

### CLI Operations
```bash
# Access CLI help
python src/cli.py --help

# Query properties using CLI
python src/cli.py query --zona "Equipetrol" --precio-max 300000

# Process natural language queries
python src/cli.py natural-query "busco casa familiar en santa cruz"
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
   - **Performance Optimization**: 99.3% improvement with zone pre-filtering

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
- **`test_api_simple.py`** - Basic API functionality tests
- **`test_motor_enriquecido.py`** - Enhanced recommendation engine tests
- **`test_prospectos_enriquecidos.py`** - Lead scoring system tests

### Running Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Test specific components
python tests/test_api.py
python tests/test_motor_enriquecido.py

# Run API integration tests
python tests/test_api_simple.py
```

## Performance Optimization

### Caching Strategy
- LRU caching for distance calculations
- Thread-safe cache with locks
- Spatial indexing for service lookups
- Zone pre-filtering for 99.3% performance improvement

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
- **`procesar_datos_citrino.py`** - Main data processing pipeline
- **`integrar_guia_urbana.py`** - Municipal urban guide integration
- **`validar_dataset_mejorado.py`** - Data quality validation
- **`evaluacion_completa_sistema.py`** - System performance evaluation

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
# Quick system verification
python verificar_servicios.py

# Auto-start demo (includes API server)
./iniciar_demo.bat

# Manual recovery steps
python api/server.py &          # Start API in background
streamlit run demo_stable.py    # Start demo interface
```

### Demo Features
- 6 predefined prospect profiles (families, investors, professionals)
- Real-time recommendation processing
- Professional welcome screen and UI
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