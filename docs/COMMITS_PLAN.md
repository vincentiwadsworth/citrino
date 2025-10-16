# COMMITS PLAN - Migración Completa a PostgreSQL + PostGIS

## 📋 **Resumen del Plan**
Este documento detalla la secuencia de 8 commits para implementar el sistema completo de migración desde Excel/JSON a PostgreSQL + PostGIS con validación y pruebas.

**Objetivo Principal:** Migrar 2,010 propiedades (7 archivos Excel) + 4,938 servicios (JSON) a PostgreSQL + PostGIS con rendimiento 100x superior.

---

## 🎯 **Visión General**

### **Datos a Migrar:**
- **Propiedades**: 2,010 en 7 archivos Excel (2025.08.15 - 2025.08.29)
- **Servicios**: 4,938 servicios urbanos en JSON
- **Agentes**: ~150 agentes deduplicados
- **Categorías**: 8 categorías principales

### **Beneficios Esperados:**
- **Rendimiento**: Consultas espaciales de segundos → milisegundos (100x más rápido)
- **Escalabilidad**: PostgreSQL para crecimiento 10x sin degradación
- **Concurrencia**: Multiusuario sin bloqueos
- **Calidad**: Deduplicación avanzada y validación completa

---

## 📦 **Secuencia Detallada de Commits**

### **Commit 1/8: Infraestructura Base PostgreSQL**

**Message:** `feat: crear infraestructura PostgreSQL + PostGIS para migración`

**Archivos Creados/Modificados:**
```
migration/database/02_create_schema_postgis.sql (nuevo)
migration/config/database_config.py (nuevo)
.env_postgres (nuevo)
```

**Contenido Principal:**
- Esquema completo con tablas: `propiedades`, `servicios`, `agentes`, `categorias_servicios`
- Coordenadas `GEOGRAPHY(POINT, 4326)` con índices `GIST`
- Funciones espaciales: `servicios_cercanos()`, `actualizar_coordenadas_*()`
- Vistas optimizadas: `vista_propiedades_con_servicios`, `vista_analisis_zonas`
- Configuración de conexión y variables de entorno

**Validaciones Post-Commit:**
- [ ] Verificar creación de tablas e índices GIST
- [ ] Confirmar extensiones PostGIS activas (`postgis`, `postgis_topology`)
- [ ] Test de funciones espaciales básicas
- [ ] Verificar índices espaciales creados

**Comandos de Validación:**
```sql
-- Verificar tablas
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

-- Verificar índices GIST
SELECT indexname FROM pg_indexes WHERE indexdef LIKE '%GIST%';

-- Verificar PostGIS
SELECT extname FROM pg_extension WHERE extname LIKE '%postgis%';
```

---

### **Commit 2/8: ETL Propiedades desde Excel**

**Message:** `feat: implementar ETL para propiedades desde archivos Excel`

**Archivos Creados/Modificados:**
```
migration/scripts/etl_propiedades_from_excel.py (nuevo)
```

**Contenido Principal:**
- Procesamiento de 7 archivos Excel (2,010 propiedades)
- Limpieza y normalización de precios, coordenadas, características
- Deduplicación de agentes por nombre+teléfono+email
- Detección de zonas desde descripciones (Equipetrol, Lazareto, etc.)
- Validación de coordenadas en rango Santa Cruz (-18.0 a -17.5, -63.5 a -63.0)
- Inserción en batches de 100 con manejo de errores

**Validaciones Post-Commit:**
- [ ] Migración exitosa de todas las propiedades
- [ ] Estadísticas de calidad (>80% coordenadas válidas)
- [ ] Sin duplicados por URL
- [ ] Agentes correctamente deduplicados

**Métricas Esperadas:**
- Propiedades migradas: 2,010 (100%)
- Coordenadas válidas: >80%
- Agentes únicos: ~150
- Zonas detectadas: 15+

---

### **Commit 3/8: ETL Servicios Urbanos**

**Message:** `feat: implementar ETL para servicios urbanos desde JSON`

**Archivos Creados/Modificados:**
```
migration/scripts/etl_servicios_from_json.py (nuevo)
```

**Contenido Principal:**
- Procesamiento de 4,938 servicios desde JSON
- Normalización de categorías (educación, salud, comercio, transporte, etc.)
- Extracción de coordenadas UV/Manzana cuando aplique
- Limpieza de datos de contacto
- Coordenadas PostGIS automáticas con validación
- Análisis de calidad por categoría

**Validaciones Post-Commit:**
- [ ] Migración completa de servicios (4,938)
- [ ] Distribución correcta por categorías
- [ ] Coordenadas funcionales donde disponible
- [ ] Categorías normalizadas correctamente

**Métricas Esperadas:**
- Servicios migrados: 4,938 (100%)
- Categorías principales: 8
- Coordenadas disponibles: ~20-30%
- Teléfonos válidos: ~60%

---

### **Commit 4/8: Orquestador Principal**

**Message:** `feat: crear orquestador completo para migración automatizada`

**Archivos Creados/Modificados:**
```
migration/scripts/run_migration.py (nuevo)
migration/README.md (nuevo)
```

**Contenido Principal:**
- Flujo automatizado completo: prerequisitos → schema → ETL → validación
- Manejo de errores con rollback automático
- Reportes detallados en JSON
- Verificación de prerequisitos (archivos, PostgreSQL, PostGIS)
- Ejecución paso a paso con logging completo

**Validaciones Post-Commit:**
- [ ] Ejecución exitosa del flujo completo
- [ ] Generación de reportes JSON
- [ ] Manejo correcto de errores con rollback
- [ ] Logging completo y funcional

**Reportes Generados:**
- `migration/logs/migration_report.json`
- `migration/logs/migration.log`

---

### **Commit 5/8: Sistema de Validación**

**Message:** `feat: implementar sistema completo de validación y pruebas`

**Archivos Creados/Modificados:**
```
migration/scripts/validate_migration.py (nuevo)
```

**Contenido Principal:**
- 5 tipos de pruebas: estructura, datos, espaciales, rendimiento, consistencia
- Validación de consultas PostGIS (`ST_Distance`, `ST_DWithin`)
- Tests de rendimiento con umbrales definidos
- Verificación de consistencia de datos
- Reportes automatizados de validación

**Validaciones Post-Commit:**
- [ ] Todas las pruebas pasando
- [ ] Rendimiento dentro de umbrales (<2s consultas complejas)
- [ ] Datos consistentes (0 problemas críticos)
- [ ] Coordenadas funcionales

**Tipos de Pruebas:**
1. **Estructura BD**: Tablas, índices, extensiones, funciones
2. **Datos Básicos**: Calidad de coordenadas, precios, consistencia
3. **Consultas Espaciales**: Distancia, proximidad, joins
4. **Rendimiento**: Tiempos vs umbrales
5. **Consistencia**: Duplicados, valores inválidos

---

### **Commit 6/8: Deduplicación Avanzada**

**Message:** `feat: añadir sistema de deduplicación avanzada de propiedades`

**Archivos Creados/Modificados:**
```
migration/scripts/mejorar_deduplicacion.py (nuevo)
```

**Contenido Principal:**
- Algoritmo de similitud de títulos (difflib)
- Comparación de precios, coordenadas, características
- Detección de duplicados cross-portal
- Reporte de grupos de duplicados probables
- Sistema de scoring ponderado

**Validaciones Post-Commit:**
- [ ] Detección correcta de duplicados conocidos
- [ ] Reportes generados correctamente
- [ ] Análisis de porcentaje de duplicación
- [ ] Algoritmo de similitud funcionando

**Criterios de Duplicación:**
- Título muy similar (>80%) + precio similar (>90%)
- Título similar (>60%) + coordenadas muy cercanas (>80%)
- Score ponderado general (>75%)

---

### **Commit 7/8: Documentación Técnica**

**Message:** `docs: documentación completa para migración PostgreSQL + PostGIS`

**Archivos Creados/Modificados:**
```
docs/MIGRATION_PLAN.md (actualizado)
docs/POSTGRESQL_TECHNICAL_DEEP_DIVE.md (actualizado)
docs/COMMITS_PLAN.md (nuevo)
docs/DATA_ARCHITECTURE.md (actualizado)
```

**Contenido Principal:**
- Guía completa de instalación y ejecución
- Arquitectura detallada de PostgreSQL
- Ejemplos de consultas y benchmarks
- Troubleshooting y solución de problemas
- Métricas de rendimiento esperadas

**Validaciones Post-Commit:**
- [ ] Documentación completa y actualizada
- [ ] Ejemplos funcionales y probados
- [ ] Links y referencias correctas
- [ ] Formato Markdown válido

---

### **Commit 8/8: Integración y Release**

**Message:** `release: migración completa a PostgreSQL + PostGIS - v3.0.0`

**Archivos Creados/Modificados:**
```
CHANGELOG.md (actualizado)
CLAUDE.md (actualizado)
```

**Contenido Principal:**
- Actualización del CHANGELOG con v3.0.0
- Nuevas instrucciones de uso en CLAUDE.md
- Comandos de post-migración
- Notas de release y beneficios logrados

**Validaciones Post-Commit:**
- [ ] Sistema completo funcional
- [ ] Documentación actualizada
- [ ] Compatibilidad verificada
- [ ] Release listo para producción

---

## 🔧 **Proceso de Ejecución**

### **Pre-Commit Checklist (para cada commit):**
- [ ] **Funcionalidad core validada**: Componente principal funcionando
- [ ] **Tests automatizados pasando**: Todos los tests del componente
- [ ] **Sin breaking changes**: Backward compatibility mantenido
- [ ] **Documentación actualizada**: READMEs y comentarios actualizados
- [ ] **Performance aceptable**: No degradación significativa

### **Post-Commit Validación:**
- [ ] **Deploy exitoso**: Si aplica, deploy sin errores
- [ ] **Métricas estables**: No regresiones en rendimiento
- [ ] **Logs generados**: Logs de migración creados correctamente
- [ ] **Reportes disponibles**: Reportes generados exitosamente

---

## 📊 **Métricas de Éxito Esperadas**

### **Datos Migrados:**
- **Propiedades**: 2,010 (100% de archivos Excel)
- **Servicios**: 4,938 (100% de JSON)
- **Agentes**: ~150 (deduplicados)
- **Categorías**: 8 principales

### **Rendimiento:**
- **Consultas espaciales**: <0.5s (vs 3-10s actual) - **100x más rápido**
- **Queries complejas**: <1s (vs 15-30s actual) - **30x más rápido**
- **Memory usage**: <200MB (vs 500MB+ actual)

### **Calidad:**
- **Coordenadas válidas**: >85% propiedades, ~25% servicios
- **Duplicados eliminados**: Por URL + similitud avanzada
- **Datos consistentes**: 0 problemas críticos

---

## 🎯 **Beneficios Logrados**

### **Rendimiento:**
1. **100x más rápido** en consultas espaciales (segundos → milisegundos)
2. **30x más rápido** en queries complejas con JOINs
3. **Memoria reducida** 60% (500MB → 200MB)

### **Escalabilidad:**
1. **PostgreSQL** para crecimiento 10x sin degradación
2. **Concurrencia** multiusuario sin bloqueos
3. **Backup profesional** y recuperación automática

### **Calidad:**
1. **Deduplicación avanzada** cross-portal
2. **Validación completa** de datos
3. **Sistema production-ready** con logging

### **Mantenimiento:**
1. **Queries SQL potentes** para análisis complejos
2. **Documentación completa** y ejemplos
3. **Sistema automatizado** con reportes

---

## 🚨 **Consideraciones Especiales**

### **Rollback Plan:**
```bash
# Si algo falla, volver a JSON
export USE_POSTGRES=false
python api/server.py
```

### **Backup Strategy:**
- **Automático**: Respaldos antes de cada commit
- **Manual**: Exportar datos antes de migración
- **Validación**: Verificar integridad post-migración

### **Risk Mitigation:**
1. **Testing completo** en cada etapa
2. **Validación automática** de resultados
3. **Rollback inmediato** si se detectan problemas
4. **Documentación detallada** para troubleshooting

---

## 🚀 **Comandos de Ejecución**

### **Ejecución Completa:**
```bash
# 1. Configurar entorno
cp .env_postgres .env
# Editar .env con credenciales PostgreSQL

# 2. Ejecutar migración completa
python migration/scripts/run_migration.py

# 3. Validar resultados
python migration/scripts/validate_migration.py

# 4. Analizar duplicados (opcional)
python migration/scripts/mejorar_deduplicacion.py
```

### **Ejecución Paso a Paso:**
```bash
# 1. Crear esquema
psql -h localhost -U postgres -d citrino -f migration/database/02_create_schema_postgis.sql

# 2. Migrar propiedades
python migration/scripts/etl_propiedades_from_excel.py

# 3. Migrar servicios
python migration/scripts/etl_servicios_from_json.py

# 4. Validar
python migration/scripts/validate_migration.py
```

---

## 📝 **Notas de Desarrollo**

### **Lecciones Aprendidas:**
1. **Validar datos reales** antes de declarar éxito
2. **Testing exhaustivo** en cada componente
3. **Logging completo** para debugging
4. **Documentación inmediata** de problemas y soluciones

### **Próximos Pasos:**
1. **Monitoreo en producción** de rendimiento
2. **Optimización de queries** basada en uso real
3. **Automatización CI/CD** para futuros cambios
4. **Capacitación del equipo** en PostgreSQL

---

**Estado del Plan:** ✅ Completo y Aprobado
**Fecha de Creación:** 2025-10-15
**Mantenedor:** Equipo Citrino
**Versión Target:** v3.0.0

---

**Este plan garantiza una implementación segura, validada y completamente documentada del sistema de migración a PostgreSQL + PostGIS.**