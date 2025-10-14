# 📋 Plan Detallado de Commits - Sprint 1

**Workflow**: Trabajo por commits con documentación y validación
**Sprint**: Organización y Limpieza del Repositorio

---

## 🎯 Metodología de Trabajo

### Flujo por Commit
1. **Planificación** → Documentar en COMMITS_PLAN.md
2. **Ejecución** → Realizar cambios específicos y enfocados
3. **Validación** → Tests y verificación de funcionalidad
4. **Documentación** → Actualizar CHANGELOG.md y SCRUM_BOARD.md
5. **Commit** → Mensaje claro con referencia a documentación

### Gestión de Contexto
- Commits pequeños y específicos
- Documentación externa para mantener estado
- Progresión incremental para evitar sobrecarga de contexto

---

## 📝 Commits Planificados

### ✅ Commit 1: Sistema de Documentación Estructurada

**Status**: 🔄 In Progress (2/6 tareas completadas)

**Objetivo**: Crear base documental para gestión estructurada del proyecto

**Archivos a Crear/Modificar**:
- [x] `CHANGELOG.md` ✅ Registro histórico de versiones
- [x] `SCRUM_BOARD.md` ✅ Tablero de trabajo sprint
- [ ] `COMMITS_PLAN.md` 🔄 Planificación detallada (actual)
- [ ] `WORKFLOW.md` 📖 Guía de flujo por commits
- [ ] `DATA_ARCHITECTURE.md` 🏗️ Plan transición arquitectura
- [ ] `CLAUDE.md` ✏️ Actualizar con nuevas referencias

**Validación**:
- [ ] Estructura de docs/ funcional
- [ ] Links internos funcionando
- [ ] Documentación coherente

**Mensaje de Commit Propuesto**:
```
docs: create structured documentation system

- Add CHANGELOG.md for version history tracking
- Add SCRUM_BOARD.md for sprint management
- Add COMMITS_PLAN.md for detailed commit planning
- Add WORKFLOW.md for commit workflow guide
- Add DATA_ARCHITECTURE.md for architecture transition plan
- Update CLAUDE.md with references to new documentation

Refs: #sprint-1-story-1
```

---

### 📋 Commit 2: Limpieza de Archivos Temporales

**Status**: 📋 To Do

**Objetivo**: Eliminar archivos temporales, pruebas y debug que contaminan el repositorio

**Archivos a Eliminar**:
```bash
# Test JSON files
test_chat.json
test_chat2.json
test_chat3.json
test_reco.json
test_reco2.json
test_reco3.json
test_search.json

# Test and debug Python files
test_chat_completo.py
test_sistema_simple.py
test_zai_simple.py
debug_busqueda.py
debug_chat_llm.py
debug_recomendaciones.py

# Temporary documentation
REPORTE_CHAT_ANALYSIS.md
docs/reporte_integracion_proveedor02.txt
```

**Validación**:
- [ ] Verificar que `pytest` sigue funcionando
- [ ] Confirmar que `api/server.py` inicia correctamente
- [ ] Validar que no hay imports rotos

**Mensaje de Commit Propuesto**:
```
cleanup: remove temporary test and debug files

- Remove test JSON files (chat, recommendation, search)
- Remove debug Python scripts
- Remove temporary analysis reports
- Clean repository of experimental files

Validated: API server and tests still functional
Refs: #sprint-1-story-2
```

---

### 📋 Commit 3: Reorganización de Directorios

**Status**: 📋 To Do

**Objetivo**: Crear estructura lógica de directorios para mejor mantenibilidad

**Nueva Estructura**:
```
scripts/
├── etl/                    # Procesamiento de datos
│   ├── build_relevamiento_dataset.py
│   ├── build_urban_services_dataset.py
│   └── integrar_datos_proveedor02.py
├── analysis/               # Análisis y reporting
│   ├── analizar_por_proveedor.py
│   ├── test_regex_vs_llm.py
│   └── demo_feedback.py
├── maintenance/            # Mantenimiento y utilidades
│   └── build_sample_inventory.py
└── legacy/                 # Código obsoleto a archivar
    └── [scripts viejos]

docs/
├── legacy/                 # Documentación histórica
│   └── [docs viejas]
└── data/                   # Arquitectura de datos
    └── [especificaciones]
```

**Tareas**:
- [ ] Crear nueva estructura de directorios
- [ ] Mover scripts a categorías apropiadas
- [ ] Actualizar imports en archivos afectados
- [ ] Mover documentación obsoleta
- [ ] Actualizar referencias en CLAUDE.md

**Validación**:
- [ ] Todos los imports funcionan
- [ ] Scripts principales ejecutan correctamente
- [ ] CLAUDE.md actualizado con nuevas rutas

**Mensaje de Commit Propuesto**:
```
refactor: reorganize directory structure for better maintainability

- Create scripts/ subdirectories (etl/, analysis/, maintenance/, legacy/)
- Move scripts to appropriate categories
- Create docs/legacy/ for historical documentation
- Update all import references
- Update CLAUDE.md with new structure

Validated: All scripts functional with new paths
Refs: #sprint-1-story-3
```

---

### 📋 Commit 4: Documentación de Arquitectura

**Status**: 📋 To Do

**Objetivo**: Documentar estado actual y plan de transición de arquitectura de datos

**Contenido**:
- [ ] Documentar arquitectura actual (JSON centralizado)
- [ ] Identificar problemas y limitaciones
- [ ] Especificar solución propuesta (procesamiento por lotes)
- [ ] Incluir prompt detallado para Tongyi
- [ ] Crear guía de migración

**Validación**:
- [ ] Documentación completa y clara
- [ ] Prompt Tongyi listo para usar
- [ ] Especificaciones técnicas detalladas

**Mensaje de Commit Propuesto**:
```
docs: add comprehensive architecture documentation

- Document current JSON-based architecture
- Identify limitations and improvement opportunities
- Specify batch processing solution with intermediate files
- Add detailed Tongyi prompt for database investigation
- Create migration guide and technical specifications

Refs: #sprint-1-story-4
```

---

### 📋 Commit 5: Preparación para Nueva Arquitectura

**Status**: 📋 To Do

**Objetivo**: Crear estructura base para implementación futura de nueva arquitectura

**Directorios a Crear**:
```
data/
├── processed/              # Archivos intermedios por proveedor/fecha
│   └── template/
│       ├── metadata.json
│       ├── records.json
│       ├── transformations.json
│       └── quality_report.json
├── consolidated/           # Datos consolidados
│   └── template/
│       ├── properties_index.json
│       └── duplicates_analysis.json
└── providers/              # Datos específicos por proveedor
    └── README.md           # Instrucciones de uso
```

**Tareas**:
- [ ] Crear estructura de directorios para nueva arquitectura
- [ ] Crear archivos template con especificaciones
- [ ] Documentar formato de metadatos
- [ ] Preparar especificaciones para UUIDs

**Validación**:
- [ ] Estructura creada correctamente
- [ ] Templates con formato válido
- [ ] Documentación clara

**Mensaje de Commit Propuesto**:
```
feat: prepare base structure for new data architecture

- Create data/processed/ for intermediate files by provider/date
- Create data/consolidated/ for consolidated datasets
- Add template files with format specifications
- Document metadata structure and UUID requirements
- Prepare infrastructure for batch processing implementation

Refs: #sprint-1-story-5
```

---

## 🔄 Progreso del Sprint

### Commits Completados
- **Commit 1**: 🔄 En progreso (2/6 tareas)

### Próximos Pasos
1. **Hoy**: Completar Commit 1 (documentación)
2. **Mañana**: Commit 2 (limpieza de archivos temporales)
3. **Siguiente**: Commit 3 (reorganización de directorios)

---

## 📋 Checklist de Validación por Commit

### Antes de cada Commit:
- [ ] **Funcionalidad**: Tests pasan correctamente
- [ ] **API**: Server inicia sin errores
- [ ] **Imports**: No hay referencias rotas
- [ ] **Documentación**: CHANGELOG y SCRUM_BOARD actualizados
- [ ] **Limpieza**: No hay archivos innecesarios agregados

### Después de cada Commit:
- [ ] **Verificación**: Git status limpio
- [ ] **Registro**: Actualizar progreso en SCRUM_BOARD.md
- [ ] **Siguiente**: Preparar tareas del siguiente commit

---

## 🎯 Criterios de Éxito del Sprint

- [ ] **5 commits** completados con validación
- [ ] **Repositorio limpio** de archivos temporales
- [ ] **Documentación completa** y estructurada
- [ ] **Base preparada** para nueva arquitectura
- [ ] **CLAUDE.md actualizado** con nueva estructura

---

*Última actualización: 2025-10-14*
*Progreso: 1/5 commits iniciados*