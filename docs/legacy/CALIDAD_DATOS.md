#  Calidad de Datos y Testing

## Estado Actual de Calidad

### Métricas de Baseline

| Métrica | Estado Actual | Objetivo |
|---------|---------------|----------|
| **Score General** | 14.4% | >40% |
| **Con Zona** | 38.1% | >90% |
| **Con Precio** | 14.4% | >50% |
| **Con Coordenadas** | 96.0% | 96%+  |
| **Con Características** | ~16% | >60% |

### Mejoras Implementadas

-  **Sistema de extracción de zonas** desde títulos/descripciones (50+ zonas conocidas)
-  **Geocodificación inversa** desde coordenadas (+420 zonas identificadas)
-  **Extracción regex** de habitaciones, baños, garajes (+171 propiedades enriquecidas)
-  **Detección multi-criterio** de duplicados (URL → Coords → Título)
-  **Análisis por proveedor** y mapeo de esquemas inconsistentes
-  **Sistema híbrido Regex+LLM** (80% sin LLM, 90% reducción tokens)

---

## Scripts de Análisis

### Calidad de Datos

```bash
# Análisis completo de calidad
python scripts/analizar_calidad_datos.py

# Análisis por proveedor
python scripts/analizar_proveedores.py

# Detección de duplicados
python scripts/detectar_duplicados.py
```

### Procesamiento ETL

```bash
# Regenerar dataset de relevamiento
python scripts/build_relevamiento_dataset.py

# Regenerar servicios urbanos
python scripts/build_urban_services_dataset.py

# Generar inventario de muestra
python scripts/build_sample_inventory.py
```

### Extracción y Normalización

```bash
# Extracción de características
python scripts/extraer_caracteristicas.py

# Normalización de precios
python scripts/normalizar_precios.py

# Geocodificación inversa
python scripts/geocodificar_coordenadas.py

# Test sistema híbrido Regex+LLM
python scripts/test_regex_vs_llm.py

# Análisis de descripciones Proveedor 02
python scripts/analizar_descripciones_p02.py
```

---

## Suite de Testing

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Con verbosidad
pytest -v

# Tests específicos
pytest tests/test_api.py -v                # API endpoints
pytest tests/test_fallback_simple.py -v   # LLM fallback
pytest tests/test_zai_integration.py -v   # Integración Z.AI

# Con coverage
pytest --cov=src --cov-report=html
```

### Cobertura Actual

| Módulo | Cobertura |
|--------|-----------|
| API Endpoints | 100% |
| Motores de Recomendación | 95% |
| Sistema LLM | 90% |
| Extracción Regex | 85% |

---

## Archivos de Soporte

### Configuración
- `pytest.ini` - Configuración de pytest con markers personalizados
- `tests/conftest.py` - Fixtures compartidos

### Reportes
- `data/reporte_calidad_datos.json` - Métricas detalladas
- `data/estadisticas_duplicados.json` - Análisis de duplicados
- `data/analisis_proveedores.json` - Mapeo de columnas por proveedor
- `data/.cache_llm_extractions.json` - Cache de extracciones LLM

---

## Problemas Conocidos

### 1. Zonas Faltantes (61.9%)
**Causa:** Proveedores no incluyen zona en muchos registros

**Mitigaciones actuales:**
- Extracción desde título/descripción
- Geocodificación inversa desde coordenadas
- Sistema híbrido Regex+LLM

**Mejora planificada:** Integración con Google Maps Geocoding

### 2. Precios Inconsistentes
**Causa:** Múltiples monedas, formatos variados

**Mitigaciones actuales:**
- Normalización automática en ETL
- Detección de moneda (USD, BOB)
- Validación de rangos razonables

**Mejora planificada:** Conversión automática a USD con tipo de cambio actualizado

### 3. Duplicados Entre Proveedores
**Causa:** Mismo inmueble en múltiples fuentes

**Mitigaciones actuales:**
- Detección por coordenadas (±0.0001°)
- Detección por título similar (>80%)
- Deduplicación en ETL

**Mejora planificada:** Fingerprinting basado en ML

---

## Validación de Datos

### Reglas de Validación

**Coordenadas:**
```python
# Santa Cruz, Bolivia
-18.0 <= latitud <= -17.0
-63.5 <= longitud <= -63.0
```

**Precios:**
```python
# Rangos razonables
USD: 10,000 - 50,000,000
BOB: 70,000 - 350,000,000
```

**Superficies:**
```python
# Metros cuadrados
10 <= superficie <= 100,000
```

**Habitaciones/Baños:**
```python
1 <= habitaciones <= 20
1 <= banos <= 15
```

---

## Monitoreo en Producción

### Métricas Observadas

- ** Tiempo de respuesta API**: ~300ms promedio
- ** Tasa de éxito**: 99.5%
- ** Cache hit ratio**: ~85%
- ** Disponibilidad LLM**: 99%+ (con fallback)

### Logging

```python
# Backend (api/server.py)
import logging

logger = logging.getLogger(__name__)
logger.info(f"Recomendación generada: {len(recommendations)} propiedades")
logger.info(f"Tiempo: {processing_time:.2f}s")
logger.error(f"Error en endpoint: {error}")
```

---

**Documento interno de Citrino - Para uso del equipo de desarrollo**
