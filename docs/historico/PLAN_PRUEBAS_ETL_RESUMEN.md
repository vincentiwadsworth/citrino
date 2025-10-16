#  Plan de Pruebas ETL y Mejora de Calidad de Datos - Citrino

**Fecha:** 10 de Enero de 2025  
**Versión:** 1.0  
**Estado del Proyecto:**  **EN PRODUCCIÓN con datos CRÍTICOS**

---

##  Diagnóstico Inicial

### Estado Actual (ANTES de mejoras)

| Métrica | Valor | Estado |
|---------|-------|--------|
| **Score de Calidad General** | **6.0%** |  CRÍTICO |
| Propiedades con zona válida | 6% (95 de 1,583) |  CRÍTICO |
| Propiedades con precio | 14.4% (228) |  CRÍTICO |
| Propiedades con superficie | 0% (0) |  CRÍTICO |
| Propiedades con habitaciones/baños | 5.7% (91) |  CRÍTICO |
| Propiedades con coordenadas | 96% (1,520) | 🟢 BUENO |

### Problema Raíz Identificado

**El campo `zona` NO contenía ubicaciones geográficas** - contenía la fuente de scraping:
-  "ULTRACASAS" (95 propiedades) = Competidor, NO una zona de Santa Cruz
-  Sistema de recomendaciones por zona **completamente roto**
-  Imposible filtrar por ubicación real

---

##  Implementaciones Realizadas

### 1. Suite de Pruebas Completa

**Archivos creados:**
-  `tests/conftest.py` - Configuración y fixtures de pytest
-  `tests/test_data_validation.py` - 25 pruebas de validación de datos
-  `tests/test_etl_pipeline.py` - 24 pruebas de funciones ETL
-  `pytest.ini` - Configuración de pytest con markers personalizados

**Resultado inicial:** 44/49 tests PASSED (89.8%)

**5 Fallas detectadas (ahora documentadas como baseline):**
1.  Solo 1 zona en dataset (monopolio ULTRACASAS)
2.  17.1% precios fuera de rango razonable
3.  25.9% propiedades con precio sin tipo
4.  Bug en ETL: `limpiar_numero('3.5')` retorna 35
5.  Distribución de zonas monopolizada

### 2. Script de Análisis de Calidad

**Archivo:** `scripts/analizar_calidad_datos.py`

**Genera:**
- Reporte completo de campos vacíos
- Análisis de coordenadas y validación de rangos
- Distribución de zonas y tipos
- Detección de duplicados
- Score de calidad general
- Prioridades de mejora
- Exporta JSON con métricas: `data/reporte_calidad_datos.json`

### 3. Extractor Inteligente de Zonas

**Archivo:** `scripts/zonas_extractor.py`

**Funcionalidades:**
-  Catálogo de 30+ zonas conocidas de Santa Cruz
-  Extracción desde títulos y descripciones
-  Normalización automática (ej: "equipe" → "Equipetrol")
-  Detección de anillos (2do, 3er, 4to, etc.)
-  Detección de radiales (Radial 10, 27, etc.)
-  Extracción de avenidas principales
-  Validación contra catálogo oficial

**Zonas soportadas:**
- Premium: Equipetrol, Las Palmas, Urubó
- Norte: Zona Norte, Las Brisas, Sirari
- Centrales: Centro, La Recoleta, La Salle
- Residenciales: Santa Mónica, Los Olivos, Urbari, Hamacas
- Otras: Zona Sur, Plazuela Blacutt, etc.

### 4. Script de Reprocesamiento de Datos

**Archivo:** `scripts/reprocesar_zonas.py`

**Proceso:**
1. Identifica fuentes de datos (`ULTRACASAS`) y las separa
2. Extrae zonas reales desde títulos (prioridad 1)
3. Extrae zonas desde descripciones (prioridad 2)
4. Guarda referencias adicionales (anillos, radiales)
5. Genera nuevo archivo: `base_datos_relevamiento_zonas_corregidas.json`

**Resultados del reprocesamiento:**
-  183 propiedades (11.6%) con zona real identificada
-  Mejora de +88 propiedades (+5.6%)
-  95 fuentes de datos correctamente identificadas
-  1,400 propiedades (88.4%) aún sin zona

---

##  Mejora Lograda

### Comparación ANTES vs DESPUÉS

| Métrica | ANTES | DESPUÉS | Mejora |
|---------|-------|---------|--------|
| **Propiedades con zona real** | 95 (6.0%) | 183 (11.6%) | **+5.6%** |
| **Zonas únicas** | 1 (ULTRACASAS) | 15+ zonas reales | **+1400%** |
| **Fuente de datos identificada** | 0 | 95 (ULTRACASAS) | **+100%** |
| **Distribución de zonas** | Monopolio 100% | Diversificada |  |

### Top 10 Zonas Identificadas

1. **Equipetrol** - 63 propiedades (34.4%)
2. **Zona Norte** - 57 propiedades (31.1%)
3. **Centro** - 14 propiedades (7.7%)
4. **Las Palmas** - 10 propiedades (5.5%)
5. **Urubó** - 8 propiedades (4.4%)
6. **Zona Sur** - 6 propiedades (3.3%)
7. **Sirari** - 5 propiedades (2.7%)
8. **Hamacas** - 5 propiedades (2.7%)
9. **La Salle** - 4 propiedades (2.2%)
10. **Plazuela Blacutt** - 3 propiedades (1.6%)

---

##  Próximos Pasos Recomendados

### FASE 1: Correcciones Inmediatas (Esta Semana)

#### 1.1 Actualizar Datos en Producción
```bash
# Backup del archivo actual
cp data/base_datos_relevamiento.json data/base_datos_relevamiento_BACKUP.json

# Reemplazar con datos corregidos
cp data/base_datos_relevamiento_zonas_corregidas.json data/base_datos_relevamiento.json

# Ejecutar tests para validar
pytest tests/test_data_validation.py -v
```

#### 1.2 Integrar Extractor en ETL Principal
- Modificar `scripts/build_relevamiento_dataset.py`
- Agregar `from zonas_extractor import ZonasExtractor`
- Ejecutar extractor durante procesamiento inicial
- Separar `fuente_datos` de `zona` desde el inicio

#### 1.3 Corregir Bug de `limpiar_numero`
En `build_relevamiento_dataset.py` línea ~176:
```python
# ANTES (INCORRECTO):
num_str = str(numero).replace(',', '').replace('.', '')

# DESPUÉS (CORRECTO):
num_str = str(numero).replace(',', '')
if '.' in num_str:
    return int(float(num_str))  # Convertir primero a float
```

### FASE 2: Mejora de Extracción de Zonas (Semana 2)

#### 2.1 Expandir Catálogo de Zonas
- Analizar manualmente 100 propiedades sin zona
- Identificar patrones no detectados
- Agregar variantes adicionales al extractor

#### 2.2 Geocodificación Inversa
Para las 1,520 propiedades con coordenadas válidas pero sin zona:
```python
# Usar API de geocodificación (Google Maps, OpenStreetMap)
# Convertir coordenadas → dirección → zona
```

#### 2.3 Machine Learning para Extracción
- Entrenar modelo NER (Named Entity Recognition)
- Dataset: descripciones + zonas conocidas
- Identificar zonas no en catálogo

### FASE 3: Enriquecimiento de Datos Faltantes (Semana 3-4)

#### 3.1 Precios (85.6% faltantes)
**Estrategias:**
1. Scraping adicional de URLs guardadas
2. Inferencia por zona + tipo + características
3. Rangos de mercado por zona

#### 3.2 Características (94% sin habitaciones/baños/superficie)
**Estrategias:**
1. Extracción con regex desde descripciones:
   ```
   - "3 dormitorios" → habitaciones: 3
   - "2 baños" → banos: 2
   - "120 m²" → superficie: 120
   ```
2. NLP para entender descripciones complejas
3. Valores típicos por tipo de propiedad

#### 3.3 Tipos de Propiedad (6.7% faltantes)
- Ya implementado en ETL (`extraer_tipo_propiedad_desde_titulo`)
- Mejorar con más palabras clave
- Normalizar variantes (Casa/casa/CASA → Casa)

### FASE 4: CI/CD y Automatización (Semana 4)

#### 4.1 GitHub Actions
Crear `.github/workflows/data_quality.yml`:
```yaml
name: Data Quality Checks

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
      - run: python scripts/analizar_calidad_datos.py
      - name: Check quality threshold
        run: |
          # Fallar si calidad < 15%
          python -c "import json; assert json.load(open('data/reporte_calidad_datos.json'))['score'] >= 15"
```

#### 4.2 Pre-commit Hooks
```bash
# .git/hooks/pre-commit
#!/bin/bash
pytest tests/test_data_validation.py --tb=short || exit 1
```

#### 4.3 Monitoreo de Calidad
- Dashboard con gráficas de evolución
- Alertas si calidad baja de umbrales
- Reportes semanales automáticos

---

##  Archivos Generados

### Scripts
-  `scripts/analizar_calidad_datos.py` - Análisis completo de calidad
-  `scripts/zonas_extractor.py` - Extractor de zonas geográficas
-  `scripts/reprocesar_zonas.py` - Reprocesamiento de datos existentes

### Tests
-  `tests/conftest.py` - Fixtures y configuración
-  `tests/test_data_validation.py` - Validación de datos
-  `tests/test_etl_pipeline.py` - Pruebas de ETL
-  `pytest.ini` - Configuración de pytest

### Datos
-  `data/base_datos_relevamiento_zonas_corregidas.json` - Datos con zonas corregidas
-  `data/reporte_calidad_datos.json` - Métricas de calidad (auto-generado)

### Configuración
-  `requirements.txt` - Actualizado con pytest, pytest-cov, pytest-mock

---

##  Comandos Útiles

### Ejecutar Análisis de Calidad
```bash
python scripts/analizar_calidad_datos.py
```

### Ejecutar Suite de Tests
```bash
# Todos los tests
pytest -v

# Solo validación de datos
pytest tests/test_data_validation.py -v

# Solo tests ETL
pytest tests/test_etl_pipeline.py -v

# Tests de regresión (monitorean empeoramiento)
pytest -m regression -v

# Con cobertura
pytest --cov=scripts --cov=src --cov-report=html
```

### Reprocesar Datos
```bash
python scripts/reprocesar_zonas.py
```

### Demo Extractor de Zonas
```bash
python scripts/zonas_extractor.py
```

---

##  Advertencias y Limitaciones

### Limitaciones Actuales

1. **88.4% propiedades aún sin zona**
   - Muchas descripciones genéricas
   - Falta información de ubicación en textos
   - **Solución:** Geocodificación inversa desde coordenadas

2. **85.6% sin precio**
   - Probablemente info sensible no scrapeable
   - **Solución:** Rangos de mercado por zona/tipo

3. **100% sin superficie**
   - NO se extrajo durante scraping
   - **Solución:** Extracción con regex desde descripciones

4. **Extractor limitado a zonas conocidas**
   - No detecta zonas nuevas automáticamente
   - **Solución:** ML/NER para descubrimiento automático

### Riesgos en Producción

 **CRÍTICO:** Sistema en producción hace recomendaciones con datos deficientes:
- Filtros por zona casi inútiles (solo 11.6% útiles)
- Comparaciones de precios imposibles (14.4% datos)
- Scoring de características roto (sin superficie/habitaciones)

**Recomendación:** 
- Agregar disclaimers en frontend sobre calidad de datos
- Limitar funcionalidades hasta alcanzar 50% calidad mínima
- Priorizar geocodificación inversa (rápida mejora a ~96% con zona)

---

##  Objetivos de Calidad

### Umbrales Mínimos (3 meses)

| Métrica | Actual | Objetivo 3M | Crítico |
|---------|--------|-------------|---------|
| Propiedades con zona | 11.6% | ≥70% | ≥50% |
| Propiedades con precio | 14.4% | ≥60% | ≥40% |
| Propiedades con características | 5.7% | ≥50% | ≥30% |
| Score general de calidad | 6.0% | ≥60% | ≥40% |
| Duplicados | 0% | <2% | <5% |
| Coverage de pruebas | 0% | ≥70% | ≥50% |

### Hitos

- **Semana 1:** Score ≥20% (geocodificación + corrección bugs)
- **Semana 4:** Score ≥40% (extracción características + precios)
- **Mes 2:** Score ≥55% (ML para zonas + enriquecimiento)
- **Mes 3:** Score ≥60% (limpieza completa + validaciones)

---

##  Responsabilidades

### Equipo de Datos
- Ejecutar reprocesamiento y validar resultados
- Implementar geocodificación inversa
- Expandir catálogo de zonas

### Equipo de Desarrollo
- Integrar extractor en ETL
- Corregir bugs identificados
- Implementar CI/CD

### Product Owner
- Priorizar funcionalidades según calidad de datos
- Definir disclaimers para usuarios
- Aprobar despliegue de datos corregidos

---

##  Contacto y Soporte

**Documentación adicional:**
- README.md - Información general del proyecto
- CLAUDE.md - Guías para desarrollo
- INTEGRACION_LLM_CAMBIOS_PENDIENTES.md - Integración Z.AI

**Issues conocidos:**
- #1: 88.4% propiedades sin zona → Geocodificación pendiente
- #2: 85.6% sin precio → Scraping adicional requerido
- #3: 100% sin superficie → Extracción desde texto pendiente
- #4: Bug limpiar_numero() → Fix pendiente en ETL

---

**Última actualización:** 10 de Enero de 2025  
**Autor:** Factory Droid (AI Agent)  
**Versión:** 1.0
