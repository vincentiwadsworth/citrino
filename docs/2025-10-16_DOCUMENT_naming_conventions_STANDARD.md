# Estándares de Nomenclatura - Proyecto Citrino

**Fecha**: 2025-10-16
**Propósito**: Establecer reglas claras y consistentes para nombrar archivos
**Regla**: Seguir estas convenciones SIEMPRE, sin excepciones

---

## Reglas Generales (BLOQUEANTE)

### 1. PROHIBIDO Absolutamente
❌ **NUNCA** usar estos sufijos en nombres de archivos:
- `_improved`, `_mejorado`, `_mejora`
- `_v2`, `_v3`, `_v1`, `_version2`
- `_backup`, `_bak`, `_old`
- `_temp`, `_tmp`, `_temporary`
- `_copy`, `_copia`, `_dup`
- `_test`, `_testing` (excepto en directorio `tests/` oficial)
- `_new`, `_nuevo`
- `_fix`, `_fixed`, `_fix_temp`
- `_final`, `_definitivo`

### 2. OBLIGATORIO Siempre
✅ **SIEMPRE** seguir estas reglas:
- Usar inglés para nombres de archivos y variables
- Usar `snake_case` (minúsculas con guiones bajos)
- Nombres descriptivos y explícitos
- Una función principal por script
- Verificar primero si ya existe algo similar

---

## Convenciones por Tipo de Archivo

### Scripts Principales (`scripts/`)
```
Formato: <acción>_<entidad>_<especificador>.py

Ejemplos correctos:
✅ migration/scripts/extract_raw_to_intermediate.py
✅ migration/scripts/migration_run_properties.py
✅ scripts/analysis/analyze_data_quality.py
✅ scripts/maintenance/backup_database.py

Ejemplos prohibidos:
❌ scripts/validation/validate_raw_improved.py
❌ scripts/migration/run_migration_v2.py
❌ scripts/analysis/analyze_backup.py
❌ scripts/maintenance/backup_temp.py
```

### Módulos Core (`src/`)
```
Formato: <dominio>_<funcionalidad>.py

Ejemplos correctos:
✅ src/recommendation_engine.py
✅ src/llm_integration.py
✅ src/data_loader.py
✅ src/description_parser.py

Ejemplos prohibidos:
❌ src/recommendation_engine_improved.py
❌ src/llm_integration_fixed.py
❌ src/data_loader_new.py
❌ src/description_parser_v2.py
```

### Tests (`tests/`)
```
Formato: test_<módulo_o_funcionalidad>.py

Ejemplos correctos:
✅ tests/test_recommendation_engine.py
✅ tests/test_llm_integration.py
✅ tests/test_api_endpoints.py
✅ tests/test_validation.py

Ejemplos prohibidos:
❌ tests/test_recommendation_engine_improved.py
❌ tests/test_llm_integration_temp.py
❌ tests/test_api_endpoints_v2.py
```

### Archivos de Configuración
```
Formato: <dominio>_<tipo>.<extensión>

Ejemplos correctos:
✅ docker-compose.yml
✅ .env.example
✅ requirements.txt
✅ pytest.ini
✅ .gitignore

Ejemplos prohibidos:
❌ docker-compose_backup.yml
❌ .env_old
❌ requirements_v2.txt
```

### Documentación (`docs/`)
```
Formato: <TÍTULO_DESCRIPTIVO_EN_MAYÚSCULAS>.md

Ejemplos correctos:
✅ docs/POSTGRESQL_MIGRATION.md
✅ docs/API_DOCUMENTATION.md
✅ docs/TROUBLESHOOTING.md
✅ docs/ARCHITECTURE.md

Ejemplos prohibidos:
❌ docs/POSTGRESQL_MIGRATION_v2.md
❌ docs/API_DOCUMENTATION_old.md
❌ docs/TROUBLESHOOTING_temp.md
```

---

## Nombres por Dominio Funcional

### Validación de Datos
```
Prefijos permitidos:
- validate_    → Para validaciones
- check_       → Para verificaciones rápidas
- verify_      → Para verificaciones completas

Ejemplos:
✅ migration/scripts/extract_raw_to_intermediate.py
✅ scripts/validation/check_coordinates.py
✅ scripts/validation/verify_migration.py
```

### Procesamiento ETL
```
Prefijos permitidos:
- process_     → Para procesamiento principal
- extract_     → Para extracción de datos
- transform_   → Para transformación
- load_        → Para carga de datos

Ejemplos:
✅ scripts/etl/process_raw_properties.py
✅ scripts/etl/extract_features.py
✅ scripts/etl/transform_coordinates.py
✅ scripts/etl/load_to_database.py
```

### Análisis
```
Prefijos permitidos:
- analyze_     → Para análisis completos
- compare_     → Para comparaciones
- report_      → Para generar reportes

Ejemplos:
✅ scripts/analysis/analyze_data_quality.py
✅ scripts/analysis/compare_providers.py
✅ scripts/analysis/report_migration_status.py
```

### Mantenimiento
```
Prefijos permitidos:
- backup_      → Para respaldos
- cleanup_     → Para limpieza
- maintenance_ → Para tareas de mantenimiento

Ejemplos:
✅ scripts/maintenance/backup_database.py
✅ scripts/maintenance/cleanup_temp_files.py
✅ scripts/maintenance/maintenance_monthly.py
```

---

## Variables y Funciones (en código)

### Variables
```python
# Correcto ✅
property_count = 100
coordinate_bounds = {'lat_min': -18.2, 'lat_max': -17.5}
validation_results = []

# Incorrecto ❌
propCount = 100          # CamelCase
coord_bounds = {'min': -18.2}  # Abreviaturas
temp_results = []        # Prefijo prohibido
```

### Funciones
```python
# Correcto ✅
def validate_property_coordinates(property_data):
    """Valida coordenadas de una propiedad."""
    pass

def extract_features_from_description(description):
    """Extrae características de una descripción."""
    pass

# Incorrecto ❌
def validateCoords(prop_data):  # Abreviaturas + CamelCase
def extractFeatures(desc):       # Abreviaturas
def validate_property_v2(data): # Sufijo prohibido
```

### Clases
```python
# Correcto ✅
class PropertyValidator:
    """Clase para validar propiedades."""
    pass

class RecommendationEngine:
    """Motor de recomendaciones."""
    pass

# Incorrecto ❌
class propertyValidator:  # Minúscula inicial
class RecommendationEngineV2:  # Sufijo prohibido
class tempValidator:      # Prefijo prohibido
```

---

## Constantes

### Formato
```python
# Correcto ✅
SANTA_CRUZ_BOUNDS = {
    'lat_min': -18.2,
    'lat_max': -17.5,
    'lng_min': -63.5,
    'lng_max': -63.0
}

DEFAULT_PRECISION = 6
MAX_PROPERTY_COUNT = 10000

# Incorrecto ❌
santaCruzBounds = {}     # CamelCase
TEMP_BOUNDS = {}         # Prefijo prohibido
bounds_v2 = {}          # Sufijo prohibido
```

---

## Estructura de Directorios

### Directorios Permitidos
```
✅ src/                  # Módulos core del sistema
✅ scripts/              # Scripts ejecutables
   ├── validation/       # Scripts de validación
   ├── migration/        # Scripts de migración
   ├── analysis/         # Scripts de análisis
   └── maintenance/      # Scripts de mantenimiento
✅ tests/                # Suite de tests oficial
✅ api/                  # API y endpoints
✅ migration/            # Migraciones de base de datos
   ├── database/         # Scripts DDL
   └── scripts/          # Scripts ETL
✅ docs/                 # Documentación
✅ data/                 # Datos
   ├── raw/             # Datos originales
   ├── processed/       # Datos procesados
   └── final/           # Datos finales
```

### Directorios Prohibidos
```
❌ temp/                 # Usar data/tmp/ si es necesario
❌ backup/               # Usar scripts/maintenance/backup_
❌ old/                  # Usar git para versiones
❌ test/                 # Usar tests/ oficial
❌ improved/             # Prohibido
❌ v2/                   # Prohibido
```

---

## Checklist Antes de Crear Archivo

### Preguntas Obligatorias
1. ¿**Ya existe** un script con esta funcionalidad? Revisar `docs/CATALOGO_SCRIPTS.md`
2. ¿Estoy usando un nombre **descriptivo** y claro?
3. ¿Evité **TODOS** los sufijos prohibidos?
4. ¿Usé **snake_case** correctamente?
5. ¿El nombre sigue las **convenciones** de su dominio?
6. ¿Verificé que no hay **conflicto** con archivos existentes?

### Proceso de Verificación
```bash
# 1. Buscar scripts similares
find . -name "*.py" -type f | grep -E "(keyword|similar)"

# 2. Verificar catálogo
cat docs/CATALOGO_SCRIPTS.md | grep -i "funcionalidad_buscada"

# 3. Buscar conflictos
ls -la directorio/ | grep "nombre_similar"
```

---

## Ejemplos Prácticos

### Escenario: Necesito validar coordenadas
```
❌ MAL: create_coordinate_validator_improved.py
❌ MAL: validate_coords_v2.py
❌ MAL: coord_validation_temp.py

✅ BIEN: Verificar si ya existe:
   → migration/scripts/extract_raw_to_intermediate.py (ya incluye extracción y validación)

✅ BIEN: Si no existe:
   → scripts/validation/validate_coordinates.py
```

### Escenario: Necesito analizar calidad de datos
```
❌ MAL: analyze_data_quality_improved.py
❌ MAL: data_analysis_v2.py
❌ MAL: temp_analysis.py

✅ BIEN: Verificar si ya existe:
   → scripts/analysis/analyze_data_quality.py (ya existe)

✅ BIEN: Si necesito mejoras:
   → Editar scripts/analysis/analyze_data_quality.py
```

### Escenario: Necesito testear LLM
```
❌ MAL: test_llm_improved.py
❌ MAL: llm_test_v2.py
❌ MAL: temp_test.py

✅ BIEN: Verificar si ya existe:
   → tests/test_llm_integration.py (oficial)
   → test_fallback_simple.py (conectividad)

✅ BIEN: Si necesito otro test específico:
   → tests/test_llm_fallback.py
```

---

## Consecuencias de No Seguir Estas Reglas

### Según CLAUDE.md
- **ERROR CRÍTICO**: Crear scripts duplicados
- **BLOQUEANTE**: Usar sufijos prohibidos
- **OBLIGATORIO**: Revisar catálogo antes de crear

### Impacto en el Proyecto
- ❌ Confusión en维护 y desarrollo
- ❌ Dificultad para encontrar código correcto
- ❌ Pérdida de tiempo buscando scripts útiles
- ❌ Código abandonado y desactualizado
- ❌ Problemas de versionamiento

---

**Versión**: 1.0
**Creado**: 2025-10-16
**Próxima actualización**: Cuando se necesiten nuevas convenciones
**Autoridad**: Esta documentación tiene prioridad sobre cualquier preferencia personal