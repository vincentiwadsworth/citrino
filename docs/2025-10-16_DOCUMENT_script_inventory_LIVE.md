# Catálogo de Scripts - Proyecto Citrino

**Fecha**: 2025-10-16
**Propósito**: Evitar confusión y duplicación de funcionalidades
**Regla**: ANTES de crear un script nuevo, verificar si ya existe algo similar aquí

---

## Scripts Principales (Flujo de Datos)

### Validación y Procesamiento
| Script | Propósito | Estado | ¿Cuándo usar? |
|--------|-----------|---------|---------------|
| `scripts/validation/validate_raw_to_intermediate.py` | RAW → Intermedio con extracción avanzada | ✅ FUNCIONAL | Siempre que proceses nuevos archivos RAW |
| `scripts/validation/approve_processed_data.py` | Intermedio → Final (aprobación manual) | ✅ FUNCIONAL | Después de validar datos intermedios |
| `scripts/validation/process_all_raw.py` | Batch processing múltiples archivos RAW | ✅ FUNCIONAL | Para procesar directorios completos |

### Migración PostgreSQL
| Script | Propósito | Estado | ¿Cuándo usar? |
|--------|-----------|---------|---------------|
| `migration/scripts/run_migration.py` | Orquestador completo de migración | ✅ FUNCIONAL | Para migración completa |
| `migration/scripts/01_etl_agentes.py` | ETL específico para agentes | ✅ FUNCIONAL | Parte de migración secuencial |
| `migration/scripts/02_etl_propiedades.py` | ETL específico para propiedades + PostGIS | ✅ FUNCIONAL | Parte de migración secuencial |
| `migration/scripts/03_etl_servicios.py` | ETL específico para servicios urbanos | ✅ FUNCIONAL | Parte de migración secuencial |
| `migration/scripts/04_validate_migration.py` | Validación post-migración | ✅ FUNCIONAL | Después de cualquier migración |

### Análisis y Auditoría
| Script | Propósito | Estado | ¿Cuándo usar? |
|--------|-----------|---------|---------------|
| `scripts/analysis/analizar_calidad_datos.py` | Análisis de calidad general | ✅ FUNCIONAL | Para auditorías de datos |
| `scripts/analysis/analizar_por_proveedor.py` | Análisis calidad por fuente/proveedor | ✅ FUNCIONAL | Para identificar problemas por fuente |
| `scripts/analysis/detectar_duplicados.py` | Detección de propiedades duplicadas | ✅ FUNCIONAL | Para limpieza de datos |

### Mantenimiento
| Script | Propósito | Estado | ¿Cuándo usar? |
|--------|-----------|---------|---------------|
| `scripts/maintenance/backup_data.py` | Backup de datos | ✅ FUNCIONAL | Para respaldos periódicos |

---

## Scripts de Validación (Tests)

### Tests de Integración LLM
| Script | Propósito | Estado | ¿Cuándo usar? |
|--------|-----------|---------|---------------|
| `test_fallback_simple.py` | Test básico de fallback LLM | ✅ FUNCIONAL | Para verificar conectividad LLM |
| `tests/test_fallback_simple.py` | Test de integración real con extracción | ✅ FUNCIONAL | Para pruebas completas del sistema |
| `test_zai_simple.py` | Test conexión básica ZAI | ✅ FUNCIONAL | Para verificar API key ZAI |
| `tests/test_zai_integration.py` | Test integración completa ZAI | ✅ FUNCIONAL | Para pruebas completas ZAI |

### Tests del Sistema
| Script | Propósito | Estado | ¿Cuándo usar? |
|--------|-----------|---------|---------------|
| `tests/test_api.py` | Tests endpoints API REST | ✅ FUNCIONAL | Para validar API |
| `tests/test_recommendation.py` | Tests motor de recomendaciones | ✅ FUNCIONAL | Para validar algoritmos |
| `tests/test_validation.py` | Tests validación de datos | ✅ FUNCIONAL | Para validar ETL |

### Tests Específicos
| Script | Propósito | Estado | ¿Cuándo usar? |
|--------|-----------|---------|---------------|
| `scripts/legacy/test_proveedor02_sample.py` | Test extracción texto libre proveedor 02 | ✅ FUNCIONAL | Para análisis específico de proveedor |
| `scripts/analysis/test_geo_validation.py` | Test validación coordenadas Santa Cruz | ✅ FUNCIONAL | Para validar geolocalización |

---

## Scripts de Auditoría y Validación

### Auditoría PostgreSQL
| Script | Propósito | Estado | ¿Cuándo usar? |
|--------|-----------|---------|---------------|
| `scripts/audit_postgresql_migration.py` | Auditoría independiente migración PostgreSQL | ✅ FUNCIONAL | OBLIGATORIO después de cualquier migración |

### Validación de Datos
| Script | Propósito | Estado | ¿Cuándo usar? |
|--------|-----------|---------|---------------|
| `scripts/validation/generate_migration_sql.py` | Generar SQL para migración aprobada | ✅ FUNCIONAL | Para migrar datos validados |
| `scripts/validation/migrate_approved_simple.py` | Migración simple de datos aprobados | ✅ FUNCIONAL | Para migraciones directas |

---

## Scripts de Utilidad

### Depuración
| Script | Propósito | Estado | ¿Cuándo usar? |
|--------|-----------|---------|---------------|
| `deduplicacion_simple.py` | Deduplicación básica de propiedades | ✅ FUNCIONAL | Para limpiar duplicados simples |

---

## Módulos Core (No son scripts ejecutables)

### Módulos Principales
| Módulo | Propósito | Estado |
|--------|-----------|---------|
| `src/recommendation_engine_mejorado.py` | Motor de recomendaciones con Haversine + PostGIS | ✅ FUNCIONAL |
| `src/llm_integration.py` | Sistema LLM híbrido con fallback | ✅ FUNCIONAL |
| `src/description_parser.py` | Parser híbrido Regex + LLM para descripciones | ✅ FUNCIONAL |
| `src/regex_extractor.py` | Motor de extracción de patrones regex | ✅ FUNCIONAL |
| `src/data_loader.py` | Carga de datos Excel/PostgreSQL | ✅ FUNCIONAL |
| `api/server.py` | API REST Flask con CORS + PostgreSQL | ✅ FUNCIONAL |

---

## Scripts PROHIBIDOS de Crear

### Patrones que NO deben repetirse
- ❌ NADA con `_improved`, `_v2`, `_backup`, `_old`, `_temp`, `_copy`
- ❌ Scripts que dupliquen funcionalidad existente
- ❌ Versiones paralelas en vez de corregir las existentes

### Ejemplos de ERRORES PASADOS (NO REPETIR)
- `script_improved.py` ❌ (debería haber editado el original)
- `script_v2.py` ❌ (debería haber editado el original)
- `script_backup.py` ❌ (debería haber usado git)
- `script_temp.py` ❌ (debería haber hecho bien el original)

---

## Flujo de Trabajo Estándar

### Para procesar nuevos datos:
1. `scripts/validation/validate_raw_to_intermediate.py`
2. Revisar manualmente archivos intermedios
3. `scripts/validation/approve_processed_data.py`
4. `migration/scripts/run_migration.py`
5. `scripts/audit_postgresql_migration.py` (OBLIGATORIO)

### Para probar LLM:
1. `test_fallback_simple.py` (conectividad)
2. `tests/test_fallback_simple.py` (integración real)

### Para validar sistema:
1. `scripts/audit_postgresql_migration.py` (auditoría)
2. `tests/test_api.py` (API)
3. `tests/test_validation.py` (ETL)

---

## Reglas de Oro

1. **ANTES de crear un script nuevo**: Buscar en este catálogo
2. **SI encuentras funcionalidad similar**: Edita el script existente
3. **SI necesitas mejoras**: Modifica el script original, no crees `_improved`
4. **SI necesitas versiones**: Usa git, no nombres de archivo
5. **EN DUDA**: Pregunta, no crees scripts duplicados

**Actualizado**: 2025-10-16 por Claude Code
**Próxima revisión**: Cuando se agreguen nuevos scripts