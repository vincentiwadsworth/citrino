#  Arquitectura Técnica de Citrino

## Diagrama de Componentes

```

                    FRONTEND (Presentación)                   

  index.html            citrino-reco.html    chat.html     
  (Landing)             (Recomendaciones)    (Asistente)   

                                               
               
                                  
                           HTTP REST API
                                  

                    BACKEND (Lógica de Negocio)                

  api/server.py (Flask)                                        
   Health & Stats endpoints                                 
   Search & Recommendation endpoints                        
   Property data endpoints                                  
                                                               
  src/ (Motores de Negocio)                                   
   recommendation_engine.py (básico)                        
   recommendation_engine_mejorado.py (geoespacial)          
   llm_integration.py (Z.AI + OpenRouter)                   
   description_parser.py (Extracción híbrida)               
   regex_extractor.py (Patrones regex)                      

                                
                      Acceso a Datos
                                

                    DATOS (Información)                        

  data/base_datos_relevamiento.json (1,583 propiedades)       
  data/guia_urbana_municipal_completa.json (4,777 servicios)  
  data/raw/*.xlsx (Archivos Excel de proveedores)             

```

## Stack Tecnológico

### Frontend
| Tecnología | Versión | Uso |
|------------|---------|-----|
| HTML5 | - | Estructura semántica |
| CSS3 + Bootstrap | 5.3 | Estilos y componentes |
| JavaScript | ES6+ | Lógica de UI |
| Fetch API | - | Comunicación con backend |

### Backend
| Tecnología | Versión | Uso |
|------------|---------|-----|
| Python | 3.8+ | Lenguaje principal |
| Flask | 2.3.3 | Framework REST API |
| Pandas | 2.0.3 | Procesamiento de datos |
| NumPy | 1.24.3 | Cálculos numéricos |
| Flask-CORS | 4.0.0 | Cross-origin requests |

### Integración LLM
| Servicio | Modelo | Uso |
|----------|--------|-----|
| Z.AI (Primario) | GLM-4.6 | Extracción y análisis |
| OpenRouter (Fallback) | Qwen2.5 72B | Alta disponibilidad |

### Algoritmos Clave
- **Haversine**: Cálculo de distancias geográficas
- **Weighted Scoring**: Sistema de puntuación multicritero
- **LRU Cache**: Optimización de consultas frecuentes
- **Regex Patterns**: Extracción de datos estructurados

## Flujo de Datos

### 1. Búsqueda de Propiedades

```
Usuario → Frontend → API POST /api/search → Motor de Búsqueda
                                                    
                                                     Filtrar por criterios
                                                     Calcular scores
                                                     Ordenar resultados
                                                    
                                              Resultados JSON
                                                    
                        Frontend ← API Response ←
```

### 2. Recomendaciones Avanzadas

```
Usuario → Frontend → API POST /api/recommend/enhanced
                                
                    
                                          
            Recomendación Base      Z.AI Enriquecimiento
                                          
              
                                              
    Filtrado por      Scoring con    Briefing   Justificaciones
    criterios         Haversine      Ejecutivo  Personalizadas
                                              
              
                                         
                    
                               
                        Resultado Completo
                               
            Frontend ← API Response ←
```

### 3. ETL de Datos del Proveedor 02

```
Excel (Proveedor 02) → build_relevamiento_dataset.py
                                
                    
                                          
            Lectura y       Procesamiento
            Normalización   por Propiedad
                                    
                    
                             
                    DescriptionParser
                             
                    
                                     
            RegexExtractor    LLM (si necesario)
            (80% casos)       (20% casos)
                                     
                    
                             
                    Datos Estructurados
                             
                    base_datos_relevamiento.json
```

## Patrones de Diseño Implementados

### 1. Strategy Pattern
**Motor de Recomendación:**
- `recommendation_engine.py` - Estrategia básica
- `recommendation_engine_mejorado.py` - Estrategia avanzada

### 2. Fallback Pattern
**Integración LLM:**
- Z.AI como proveedor primario
- OpenRouter como fallback automático
- Detección de errores 429, 500, 502, 503

### 3. Hybrid Extraction Pattern
**Sistema Regex + LLM:**
- Intenta regex primero (rápido, gratis)
- Recurre a LLM solo si necesario
- Combina resultados priorizando regex

### 4. Cache Pattern
**Optimización de Performance:**
- LRU Cache para distancias calculadas
- Cache de extracción LLM
- Thread-safe con locks

### 5. Repository Pattern
**Acceso a Datos:**
- JSON como almacenamiento
- Capa de abstracción para datos
- Facilita migración futura a PostgreSQL

## Endpoints de API

### Health & Monitoring
```
GET /api/health
Response: {
    "status": "healthy",
    "properties_count": 1583,
    "services_count": 4777
}

GET /api/stats
Response: {
    "total_properties": 1583,
    "zones": 50,
    "cache_hits": 245,
    "uptime": "2d 4h 32m"
}
```

### Búsqueda
```
POST /api/search
Body: {
    "zona": "Equipetrol",
    "precio_min": 80000,
    "precio_max": 150000,
    "tipo_propiedad": "departamento"
}
Response: {
    "total_results": 12,
    "properties": [...]
}
```

### Recomendaciones
```
POST /api/recommend/enhanced
Body: {
    "presupuesto_min": 80000,
    "presupuesto_max": 150000,
    "adultos": 2,
    "ninos": [8, 12],
    "zona_preferida": "Equipetrol",
    "necesidades": ["escuela_primaria", "hospital"]
}
Response: {
    "recommendations": [...],
    "total_matches": 8,
    "processing_time_ms": 245
}
```

## Seguridad y Configuración

### Variables de Entorno (.env)
```bash
# LLM Configuration
ZAI_API_KEY=your_key_here
LLM_PROVIDER=zai
LLM_MODEL=glm-4.6
LLM_MAX_TOKENS=8000
LLM_TEMPERATURE=0.1

# Fallback Configuration
OPENROUTER_FALLBACK_ENABLED=true
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=qwen/qwen-2.5-72b-instruct:free

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=false
```

### CORS Configuration
```python
# api/server.py
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://vincentiwadsworth.github.io"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})
```

## Performance y Optimización

### Métricas Objetivo
| Métrica | Objetivo | Actual |
|---------|----------|--------|
| Tiempo de respuesta API | <500ms | ~300ms |
| Carga de datos | <2s | ~1.5s |
| Cache hit ratio | >80% | ~85% |
| Disponibilidad LLM | >95% | 99%+ (con fallback) |

### Estrategias de Optimización
1. **Lazy Loading**: Cargar datos bajo demanda
2. **LRU Cache**: Cachear cálculos costosos
3. **Índices espaciales**: Búsquedas geoespaciales eficientes
4. **Batch Processing**: Procesar múltiples propiedades simultáneamente

## Testing

### Niveles de Testing
```
tests/
 test_api.py              # Integration tests
 test_api_simple.py       # Smoke tests
 test_fallback_simple.py  # LLM fallback tests
 test_zai_integration.py  # Z.AI integration
 test_zai_simple.py       # Z.AI unit tests
```

### Cobertura
- API Endpoints: 100%
- Motores de Recomendación: 95%
- Sistema LLM: 90%
- Extracción Regex: 85%

## Deployment

### Producción Actual
- **Frontend**: GitHub Pages
- **Backend**: Render.com (Free Tier)
- **Datos**: JSON estático

### Configuración de Deploy

**Render.com (Backend):**
```yaml
# render.yaml
services:
  - type: web
    name: citrino-api
    env: python
    buildCommand: pip install -r requirements_api.txt
    startCommand: python api/server.py
    envVars:
      - key: ZAI_API_KEY
        sync: false
      - key: OPENROUTER_API_KEY
        sync: false
```

**GitHub Pages (Frontend):**
- Auto-deploy en push a `main`
- Configurado en Settings → Pages
- Custom domain: (opcional)

## Escalabilidad Futura

### Migración a PostgreSQL
```sql
-- Schema propuesto
CREATE TABLE properties (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255),
    precio DECIMAL(12,2),
    zona VARCHAR(100),
    latitud DECIMAL(10,8),
    longitud DECIMAL(11,8),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_zona ON properties(zona);
CREATE INDEX idx_coords ON properties USING GIST (
    ST_MakePoint(longitud, latitud)
);
```

### Arquitectura Microservicios
```
API Gateway
     Property Service (búsqueda)
     Recommendation Service (motor)
     LLM Service (extracción)
     Analytics Service (métricas)
```

### CDN y Caching
- CloudFlare para assets estáticos
- Redis para cache distribuido
- CDN para imágenes de propiedades

---

**Documentación técnica completa para el equipo de desarrollo**
