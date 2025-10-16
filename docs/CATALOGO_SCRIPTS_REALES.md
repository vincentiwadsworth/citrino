# CATÁLOGO DE SCRIPTS REALES - PROYECTO CITRINO

**Fecha**: 2025-10-16
**Propósito**: Inventario honesto y actualizado de scripts existentes
**Regla**: Este documento solo contiene scripts que REALMENTE existen

---

## Scripts ETL y Migración (`migration/scripts/`)

### Scripts Principales ETL
| Script | Propósito | Estado | Comando Ejemplo |
|--------|-----------|---------|------------------|
| `extract_raw_to_intermediate.py` | Extraer y transformar archivos RAW a XLSX intermedios con LLM | ✅ Funcional | `python migration/scripts/extract_raw_to_intermediate.py --input-dir data/raw` |
| `migration_run_properties.py` | Orquestador principal de migración de propiedades | ✅ Funcional | `python migration/scripts/migration_run_properties.py` |
| `02_etl_propiedades.py` | ETL de propiedades desde archivos procesados | ✅ Funcional | `python migration/scripts/02_etl_propiedades.py` |
| `03_etl_servicios.py` | ETL de servicios urbanos | ✅ Funcional | `python migration/scripts/03_etl_servicios.py` |
| `01_etl_agentes.py` | ETL de agentes y deduplicación | ✅ Funcional | `python migration/scripts/01_etl_agentes.py` |

### Scripts de Validación
| Script | Propósito | Estado | Comando Ejemplo |
|--------|-----------|---------|------------------|
| `04_validate_migration.py` | Validación completa de migración | ✅ Funcional | `python migration/scripts/04_validate_migration.py` |
| `validate_migration.py` | Validación adicional de migración | ✅ Funcional | `python migration/scripts/validate_migration.py` |
| `mejorar_deduplicacion.py` | Algoritmos avanzados de deduplicación | ✅ Funcional | `python migration/scripts/mejorar_deduplicacion.py` |
| `etl_servicios_from_excel.py` | ETL de servicios desde Excel | ✅ Funcional | `python migration/scripts/etl_servicios_from_excel.py` |

### Scripts de Testing y Diagnóstico
| Script | Propósito | Estado | Comando Ejemplo |
|--------|-----------|---------|------------------|
| `etl_test_docker.py` | Testing de integración con Docker | ✅ Funcional | `python migration/scripts/etl_test_docker.py` |

---

## Scripts de API (`api/`)

### Servidor Principal
| Script | Propósito | Estado | Comando Ejemplo |
|--------|-----------|---------|------------------|
| `server.py` | Servidor principal FastAPI con PostgreSQL/PostGIS | ✅ Funcional | `python api/server.py` |
| `chatbot_completions.py` | Endpoint para chatbot | ✅ Funcional | `python api/chatbot_completions.py` |
| `setup.py` | Configuración de API | ✅ Funcional | `python api/setup.py` |

---

## Scripts Core (`src/`)

### Módulos Principales
| Script | Propósito | Estado | Uso |
|--------|-----------|---------|-----|
| `recommendation_engine_postgis.py` | Motor de recomendaciones con PostGIS | ✅ Funcional | Importado por API |
| `description_parser.py` | Parser de descripciones con LLM | ✅ Funcional | Usado por ETL |
| `llm_integration.py` | Integración con modelos LLM | ✅ Funcional | Usado por parser |
| `regex_extractor.py` | Extracción de características con regex | ✅ Funcional | Usado por parser |
| `amenities_extractor.py` | Extracción específica de amenities | ✅ Funcional | Importado por otros módulos |

---

## Scripts de Tests (`tests/`)

### Tests de API
| Script | Propósito | Estado | Comando Ejemplo |
|--------|-----------|---------|------------------|
| `test_api.py` | Tests básicos de API | ✅ Funcional | `python tests/test_api.py` |
| `test_api_endpoints_current.py` | Tests de endpoints actuales | ✅ Funcional | `python tests/test_api_endpoints_current.py` |
| `test_api_simple.py` | Tests simples de API | ✅ Funcional | `python tests/test_api_simple.py` |
| `test_api_docker_integration.py` | Tests de integración con Docker | ✅ Funcional | `python tests/test_api_docker_integration.py` |

### Tests de Chatbot
| Script | Propósito | Estado | Comando Ejemplo |
|--------|-----------|---------|------------------|
| `test_chatbot_integration.py` | Tests de integración de chatbot | ✅ Funcional | `python tests/test_chatbot_integration.py` |

### Tests de LLM
| Script | Propósito | Estado | Comando Ejemplo |
|--------|-----------|---------|------------------|
| `test_llm_fallback_basic.py` | Tests básicos de fallback LLM | ✅ Funcional | `python tests/test_llm_fallback_basic.py` |
| `test_llm_zai_connection.py` | Tests de conexión Z.AI | ✅ Funcional | `python tests/test_llm_zai_connection.py` |
| `test_zai_integration.py` | Tests de integración Z.AI | ✅ Funcional | `python tests/test_zai_integration.py` |
| `test_zai_simple.py` | Tests simples de Z.AI | ✅ Funcional | `python tests/test_zai_simple.py` |
| `test_fallback_simple.py` | Tests simples de fallback | ✅ Funcional | `python tests/test_fallback_simple.py` |

### Tests de Datos y ETL
| Script | Propósito | Estado | Comando Ejemplo |
|--------|-----------|---------|------------------|
| `test_data_validation.py` | Tests de validación de datos | ✅ Funcional | `python tests/test_data_validation.py` |
| `test_etl_pipeline.py` | Tests de pipeline ETL | ✅ Funcional | `python tests/test_etl_pipeline.py` |

### Tests de Componentes (movidos desde scripts/)
| Script | Propósito | Estado | Comando Ejemplo |
|--------|-----------|---------|------------------|
| `test_amenities_extractor.py` | Tests de extractor de amenities | ✅ Funcional | `python tests/test_amenities_extractor.py` |
| `test_etl_monitor.py` | Tests de monitor ETL | ✅ Funcional | `python tests/test_etl_monitor.py` |
| `test_llm_config.py` | Tests de configuración LLM | ✅ Funcional | `python tests/test_llm_config.py` |
| `test_price_corrector.py` | Tests de corrector de precios | ✅ Funcional | `python tests/test_price_corrector.py` |

---

## Scripts de Análisis y Validación (`scripts/`)

### Scripts de Auditoría
| Script | Propósito | Estado | Comando Ejemplo |
|--------|-----------|---------|------------------|
| `audit_postgresql_migration_v1.0.py` | Auditoría completa de migración PostgreSQL | ✅ Funcional | `python scripts/audit_postgresql_migration_v1.0.py` |
| `migrate_oracle_to_docker.py` | Migración Oracle a Docker | ✅ Funcional | `python scripts/migrate_oracle_to_docker.py` |

### Scripts de Validación (`scripts/validation/`)
| Script | Propósito | Estado | Comando Ejemplo |
|--------|-----------|---------|------------------|
| `validation_approve_properties_final.py` | Aprobación final de propiedades | ✅ Funcional | `python scripts/validation/validation_approve_properties_final.py` |
| `diagnose_raw_structure.py` | Diagnóstico de estructura RAW | ✅ Funcional | `python scripts/validation/diagnose_raw_structure.py` |
| `generate_migration_sql.py` | Generación de SQL para migración | ✅ Funcional | `python scripts/validation/generate_migration_sql.py` |
| `generate_validation_report.py` | Generación de reportes de validación | ✅ Funcional | `python scripts/validation/generate_validation_report.py` |
| `migrate_approved_simple.py` | Migración simplificada de aprobados | ✅ Funcional | `python scripts/validation/migrate_approved_simple.py` |

---

## Scripts de Debug (`scripts/debug/`)

### Scripts de Diagnóstico
| Script | Propósito | Estado | Comando Ejemplo |
|--------|-----------|---------|------------------|
| `debug_coordenadas_critico.py` | Debug crítico de coordenadas | ✅ Funcional | `python scripts/debug/debug_coordenadas_critico.py` |
| `debug_pipeline_completo.py` | Debug completo de pipeline | ✅ Funcional | `python scripts/debug/debug_pipeline_completo.py` |

---

## Scripts Standalone (Raíz del Proyecto)

### Scripts de Configuración
| Script | Propósito | Estado | Comando Ejemplo |
|--------|-----------|---------|------------------|
| `chatbot/setup.py` | Setup del chatbot | ✅ Funcional | `python chatbot/setup.py` |

---

## Convenciones de Nomenclatura

### Scripts Vivos (existenten y funcionan)
✅ **Prefijos correctos**: `extract_`, `process_`, `validate_`, `test_`, `migrate_`
✅ **Nombres descriptivos**: Sin sufijos prohibidos (`_improved`, `_v2`, `_temp`)
✅ **Ubicación correcta**: ETL en `migration/scripts/`, tests en `tests/`

### Scripts Muertos (eliminados, no existen)
❌ `etl_simple_raw.py` - Eliminado, funcionalidad integrada en `extract_raw_to_intermediate.py`
❌ `etl_propiedades_from_excel.py` - Eliminado, reemplazado por `extract_raw_to_intermediate.py`
❌ `validation_validate_properties_intermediate.py` - Renombrado a `extract_raw_to_intermediate.py`

---

## Flujo de Trabajo Actual

### Procesamiento RAW → Intermediate
```bash
# Extraer y transformar archivos raw (con LLM)
python migration/scripts/extract_raw_to_intermediate.py --input-dir data/raw
```

### Procesamiento Intermediate → PostgreSQL
```bash
# Ejecutar migración completa
python migration/scripts/migration_run_properties.py

# O paso a paso
python migration/scripts/01_etl_agentes.py
python migration/scripts/02_etl_propiedades.py
python migration/scripts/03_etl_servicios.py
```

### Validación
```bash
# Validar migración completa
python migration/scripts/04_validate_migration.py

# Diagnóstico de datos raw
python scripts/validation/diagnose_raw_structure.py
```

---

## Métricas de Scripts

### Scripts Totales por Categoría
- **ETL/Migración**: 9 scripts
- **API**: 3 scripts
- **Core**: 5 scripts
- **Tests**: 18 scripts
- **Validación**: 5 scripts
- **Debug**: 2 scripts

### Scripts Funcionales
- **✅ Funcionales**: 42 scripts
- **❌ Rotos/Obsoletos**: 0 scripts

---

## Notas Importantes

### Características del Script Principal
- **Nombre**: `extract_raw_to_intermediate.py`
- **Ubicación**: `migration/scripts/`
- **Funcionalidad**: Extracción + Transformación con LLM y Regex
- **Portabilidad**: UTF-8 autoconsciente para Windows
- **Entrada`: Archivos RAW en `data/raw/`
- **Salida`: XLSX intermedios en `data/processed/`

### Scripts Portátiles
- `extract_raw_to_intermediate.py` incluye bloque UTF-8 autoconsciente
- Funciona en cualquier entorno Windows sin configuración manual
- Compatible con diferentes configuraciones regionales

---

**Catálogo Mantenido**: 2025-10-16
**Total Scripts Verificados**: 42
**Estado**: Actualizado y sincronizado con realidad del repositorio