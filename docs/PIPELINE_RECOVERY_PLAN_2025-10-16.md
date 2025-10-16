# PIPELINE RECOVERY PLAN 2025-10-16
## ESTADO CRÍTICO - ACCIÓN INMEDIATA REQUERIDA

**Fecha**: 2025-10-16
**Severidad**: CRITICAL
**Sistema**: Citrino Pipeline completamente roto
**Nivel de urgencia**: MÁXIMO

---

## 🎯 PROBLEMAS INELUDIBLES IDENTIFICADOS

### Problema #1: CONEXIÓN PSYCOPG2 FALLA COMPLETAMENTE (CRÍTICO)
- **Error**: `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xf3 in position 85`
- **Impacto**: 100% de scripts Python rotos, sistema completamente inoperativo
- **Causa raíz**: psycopg2 directo no puede manejar caracteres especiales Windows
- **Solución**: Reemplazar TODAS las conexiones psycopg2 por Docker wrapper
- **Archivos críticos**: `migration/config/database_config.py`

### Problema #2: API ORIGINAL INÚTIL (CRÍTICO)
- **Síntoma**: `/api/health` muestra "sin datos cargados" cuando hay 58 propiedades
- **Impacto**: Sistema sin interfaz funcional para usuarios
- **Causa raíz**: `api/server.py:81` usa `psycopg2.connect()` directo que falla
- **Solución**: Modificar conexión en API principal
- **Archivos críticos**: `api/server.py`

### Problema #3: ETL PRINCIPAL ROTO (CRÍTICO)
- **Scripts afectados**:
  - `migration/scripts/extract_raw_to_intermediate.py`
  - `migration/scripts/01_etl_agentes.py`
  - `migration/scripts/03_etl_servicios.py`
- **Impacto**: No se pueden procesar los ~1,600 propiedades pendientes
- **Solución**: Actualizar scripts ETL para usar Docker wrapper

### Problema #4: COORDENADAS SIN MIGRAR A POSTGIS (ALTO)
- **Estado**: Coordenadas en formato texto, no espacial
- **Impacto**: Sin funcionalidad geoespacial, motor de recomendación inútil
- **Solución**: Convertir a formato `GEOGRAPHY(POINT, 4326)` en ETL
- **Índice requerido**: `CREATE INDEX idx_propiedades_coords ON propiedades USING GIST (coordenadas)`

### Problema #5: PROCESAMIENTO INCOMPLETO DE DATOS (ALTO)
- **Procesado**: 1/8 archivos (60/1600 propiedades)
- **Pendiente**: ~1,540 propiedades + 4,942 servicios urbanos
- **Solución**: Procesar archivos restantes con ETL actualizado

### Problema #6: SERVICIOS URBANOS NO MIGRADOS (ALTO)
- **Archivo**: `data/raw/guia/GUIA URBANA.xlsx` (4,942 servicios)
- **Impacto**: Sistema sin puntos de interés para análisis espacial
- **Solución**: Crear ETL específico para servicios urbanos

### Problema #7: MOTOR DE RECOMENDACIÓN INÚTIL (ALTO)
- **Archivos**: `src/recommendation_engine.py`, `src/recommendation_engine_mejorado.py`
- **Impacto**: Funcionalidad core del sistema sin operar
- **Solución**: Actualizar motores para usar PostgreSQL real

### Problema #8: FRONTEND SIN DATOS REALES (MEDIO)
- **Síntoma**: Interfaces muestran sistema vacío
- **Causa**: APIs improvisadas no conectan a PostgreSQL real
- **Solución**: Debug y arreglar conexión en Flask API context

### Problema #9: VALIDACIÓN DE INTEGRIDAD FALTA (MEDIO)
- **Estado**: No hay pruebas que confirmen que el sistema funcione end-to-end
- **Impacto**: No hay garantía de calidad
- **Solución**: Tests de integración completos

---

## 🚨 ORDEN DE EJECUCIÓN OBLIGATORIO

### FASE 1: CRÍTICA (Base del sistema)
**Plazo**: Inmediato
**Objetivo**: Establecer conexión funcional

1. **Arreglar conexión psycopg2** en `migration/config/database_config.py`
   - Reemplazar `psycopg2.connect()` por Docker wrapper en `create_connection()`
   - Actualizar `get_connection_params()` para usar siempre Docker wrapper
   - Forzar uso de Docker wrapper en todas las conexiones
   - **Validación**: `python -c "from migration.config.database_config import create_connection; conn = create_connection(); conn.close()"`

2. **Actualizar API principal** en `api/server.py`
   - Modificar línea 81: `psycopg2.connect(**db_config)` → `create_connection()`
   - Agregar import: `from migration.config.database_config import create_connection`
   - **Validación**: `curl http://localhost:5001/api/health` debe mostrar `total_propiedades: 58`

3. **Corregir ETL principal**
   - Actualizar `migration/scripts/02_etl_propiedades.py`
   - Reemplazar `psycopg2.connect()` por `create_connection()`
   - **Validación**: Procesar archivo pequeño debe funcionar sin errores

### FASE 2: ESCALABLE (Procesamiento de datos)
**Plazo**: Fase 1 completada
**Objetivo**: Migrar todos los datos y funcionalidad espacial

4. **Migrar coordenadas a PostGIS**
   - Modificar ETL para usar `ST_GeographyFromText('POINT(lon lat)', 4326)`
   - Crear índice espacial GIST para consultas eficientes
   - **Validación**: Verificar que coordenadas estén en formato PostGIS

5. **Procesar archivos restantes**
   - Usar ETL actualizado para procesar 7 archivos restantes
   - Migrar ~1,540 propiedades adicionales
   - **Validación**: Total debe ser >1,600 propiedades

6. **Migrar servicios urbanos**
   - Crear ETL para `data/raw/guia/GUIA URBANA.xlsx`
   - Procesar 4,942 servicios urbanos
   - **Validación**: `SELECT COUNT(*) FROM servicios` debe ser ~5,000

7. **Debug API con datos reales**
   - Asegurar que `create_connection()` funcione en Flask context
   - **Validación**: `/api/health` debe mostrar datos reales cargados

### FASE 3: COMPLETA (Funcionalidad real)
**Plazo**: Fase 2 completada
**Objetivo**: Sistema completamente funcional

8. **Actualizar motores de recomendación**
   - Modificar `src/recommendation_engine.py` y `recommendation_engine_mejorado.py`
   - Usar conexión PostgreSQL real vs. JSON simulado
   - **Validación**: Motor debe retornar propiedades reales de BD

9. **Validar frontend completo**
   - Asegurar que HTML pueda cargar datos reales desde API
   - Testear búsqueda y filtrado con propiedades reales
   - **Validación**: Interfaz debe mostrar propiedades reales

---

## ✅ MÉTRICAS DE ÉXITO REQUERIDAS

### Después de FASE 1:
- ✅ Conexión PostgreSQL: 100% funcional
- ✅ API health endpoint: Muestra 58 propiedades
- ✅ ETL básico: Procesa archivos sin errores

### Después de FASE 2:
- ✅ Propiedades migradas: >1,600 (100% de archivos)
- ✅ Servicios migrados: >5,000 (GUIA URBANA)
- ✅ Coordenadas PostGIS: Formato espacial correcto
- ✅ Consultas espaciales: Funcionales

### Después de FASE 3:
- ✅ Motor de recomendación: Funciona con datos reales
- ✅ Frontend: Muestra y filtra datos reales
- ✅ Tests de integración: Todos pasando
- ✅ Sistema completo: End-to-end funcional

---

## 📋 CHECKLIST DE VALIDACIÓN POR ARCHIVO

### `migration/config/database_config.py`
- [ ] `create_connection()` usa Docker wrapper
- [ ] `get_connection_params()` fuerza Docker wrapper
- [ ] Sin `psycopg2.connect()` directo
- [ ] Test de conexión exitoso

### `api/server.py`
- [ ] Línea 81 usa `create_connection()`
- [ ] Import `migration.config.database_config` agregado
- [ ] Health endpoint muestra datos reales
- [ ] API carga propiedades de PostgreSQL

### Scripts ETL
- [ ] `02_etl_propiedades.py` usa Docker wrapper
- [ ] `01_etl_agentes.py` usa Docker wrapper
- [ ] `03_etl_servicios.py` usa Docker wrapper
- [ ] Todos procesan sin `UnicodeDecodeError`

### Motores de recomendación
- [ ] `recommendation_engine.py` usa PostgreSQL real
- [ ] `recommendation_engine_postgis.py` usa PostgreSQL real
- [ ] Consultas funcionan con datos reales
- [] Resultados consistentes con PostgreSQL

---

## 🚨 ACCIONES INMEDIATAS REQUERIDAS

1. **DETENER TRABAJO EN CUALQUIER OTRA COSA** hasta que FASE 1 esté completa
2. **NO CREAR NINGÚN WORKAROUND ADICIONAL** - Usar soluciones identificadas
3. **VALIDAR CADA PASO** antes de continuar al siguiente
4. **DOCUMENTAR BLOQUEOS** si se encuentran problemas inesperados

---

## 🎯 RESULTADO FINAL ESPERADO

**Estado final del sistema:**
- ✅ Pipeline de datos completamente funcional
- ✅ ~1,600 propiedades migradas con coordenadas PostGIS
- ✅ ~5,000 servicios urbanos procesados
- ✅ API REST completamente operativa
- ✅ Motor de recomendación funcional con datos reales
- ✅ Frontend integrado con datos reales
- ✅ Tests de integración completos pasando

**Sistema Citrino completamente recuperado y listo para producción.**

---

**Prioridad**: CRÍTICA - EJECUTAR INMEDIATAMENTO
**Dueño**: Sin esto el sistema sigue completamente inoperativo
**Responsable**: Equipo de desarrollo Citrino