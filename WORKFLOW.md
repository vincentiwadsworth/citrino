# 🔄 Workflow de Trabajo por Commits

Guía de flujo de trabajo para desarrollo estructurado y mantenible en Citrino.

---

## 🎯 Filosofía del Workflow

### Principios
- **Excel RAW como fuente**: Datos ORIGINALES exclusivamente en data/raw/
- **Validación humana obligatoria**: Revisión manual antes de producción
- **Commits pequeños y enfocados**: Cambios específicos y validables
- **Documentación primero**: Siempre documentar antes de implementar
- **Validación continua**: Verificar funcionalidad en cada paso
- **Trazabilidad clara**: Seguimiento completo desde archivo original

### Beneficios
- Calidad de datos garantizada por revisión humana
- Manejo eficiente de contexto de Claude Code
- Historial claro y mantenible
- Rollbacks fáciles y seguros
- Colaboración estructurada
- Flujo de datos transparente y validado

---

## 📋 Ciclo de Vida de un Commit

### 1. Planificación 📝
```bash
# Antes de empezar
1. Revisar COMMITS_PLAN.md para el commit actual
2. Entender el objetivo y alcance exacto
3. Identificar archivos que serán modificados
4. Definir criterios de validación
5. Verificar impacto en flujo Excel RAW → PostgreSQL
```

### 2. Ejecución 🛠️
```bash
# Durante el desarrollo
1. Realizar cambios específicos del commit
2. Mantenerse enfocado en el objetivo definido
3. No agregar cambios extras no planificados
4. Preservar integridad de archivos Excel RAW
5. Testear a medida que se avanza
```

### 3. Validación ✅
```bash
# Antes de commitear
1. Ejecutar tests básicos del sistema
2. Verificar que API server inicia correctamente
3. Confirmar que no hay imports rotos
4. Validar cambios específicos del commit
5. Verificar flujo de datos PostgreSQL funciona
```

### 4. Documentación 📚
```bash
# Actualizar documentación
1. Actualizar CHANGELOG.md con cambios realizados
2. Actualizar SCRUM_BOARD.md con progreso
3. Actualizar COMMITS_PLAN.md si es necesario
4. Revisar que la documentación esté sincronizada
5. Actualizar DATA_ARCHITECTURE.md si hay cambios en flujo
```

### 5. Commit ✨
```bash
# Mensaje de commit estándar
tipo: descripción concisa

- Detalles específicos del cambio
- Impacto en flujo Excel RAW → PostgreSQL
- Validación realizada
- Referencias a documentación

Refs: #sprint-x-story-y
```

---

## 🏗️ Estructura de Commits

### Tipos de Commits
- **feat**: Nueva funcionalidad
- **docs**: Cambios en documentación
- **refactor**: Reorganización de código (no cambia funcionalidad)
- **cleanup**: Limpieza de archivos o código
- **fix**: Corrección de bugs
- **test**: Cambios en tests
- **chore**: Mantenimiento general

### Formato de Mensaje
```bash
<tipo>: <descripción>

<cuerpo detallado>

<referencias>
```

### Ejemplos
```bash
docs: create structured documentation system

- Add CHANGELOG.md for version history
- Add SCRUM_BOARD.md for sprint management
- Update CLAUDE.md with Excel RAW → PostgreSQL flow
- Update DATA_ARCHITECTURE.md with validation workflow

Refs: #sprint-1-story-1
```

```bash
feat: implement Excel RAW validation workflow

- Add validate_raw_to_intermediate.py for individual file processing
- Add process_all_raw.py for batch processing
- Add approve_processed_data.py for human approval
- Generate intermediate Excel files for team review

Validated: API server and PostgreSQL connection functional
Refs: #sprint-1-story-2
```

```bash
etl: migrate validated properties to PostgreSQL

- Process approved files from data/final/
- Insert properties with PostGIS coordinates
- Maintain archivo_origen tracking
- Update agentes with deduplication

Validated: All properties migrated successfully
Refs: #sprint-1-story-3
```

---

## 🔄 Gestión de Contexto

### Manejo de Sesiones
```bash
# Al finalizar cada sesión
1. Completar el commit actual si está listo
2. Dejar el repositorio en estado limpio
3. Actualizar documentación de progreso
4. Documentar siguiente paso en COMMITS_PLAN.md
5. Verificar que archivos Excel RAW no fueron modificados
```

### Reanudación de Trabajo
```bash
# Al iniciar nueva sesión
1. Revisar COMMITS_PLAN.md para continuar
2. Leer SCRUM_BOARD.md para ver progreso actual
3. Revisar CHANGELOG.md para entender historia reciente
4. Identificar exactamente dónde se quedó el trabajo
5. Verificar estado de archivos procesados vs aprobados
```

### Reducción de Contexto
- **Commits atómicos**: Un cambio conceptual por commit
- **Documentación externa**: Mantener estado en archivos MD
- **Progresión incremental**: No hacer cambios grandes de una vez
- **Validación humana**: Cada paso del flujo validado por equipo Citrino

---

## 📊 Validación por Tipo de Cambio

### Cambios en Scripts/Python
```bash
# Validación básica
python script_nombre.py --help
python -c "import script_nombre; print('OK')"

# Para scripts principales
python api/server.py &
python src/recommendation_engine_mejorado.py

# Para scripts de validación Excel RAW
python scripts/validation/validate_raw_to_intermediate.py --input "data/raw/test.xlsx"
python scripts/validation/process_all_raw.py --input-dir "data/raw/" --dry-run
```

### Cambios en Documentación
```bash
# Validación
1. Revisar que los links funcionan
2. Verificar coherencia entre documentos
3. Confirmar que no hay información contradictoria
```

### Cambios en Estructura
```bash
# Validación
1. Verificar que todos los imports funcionan
2. Confirmar que scripts principales ejecutan
3. Testear movimientos de archivos
```

### Cambios en API
```bash
# Validación
1. Iniciar server: python api/server.py
2. Testear endpoints principales
3. Verificar respuestas PostgreSQL
4. Probar consultas geoespaciales
5. Confirmar tiempos de respuesta <100ms
```

### Cambios en Validación Excel RAW
```bash
# Validación
1. Verificar que archivos Excel RAW no se modifican
2. Confirmar generación de archivos intermedios
3. Validar estructura de archivos *_intermedio.xlsx
4. Revisar reportes JSON de calidad
5. Verificar tracking de archivo_origen
```

### Cambios en Migración PostgreSQL
```bash
# Validación
1. Testear conexión PostgreSQL
2. Verificar scripts ETL con datos de prueba
3. Confirmar índices espaciales creados
4. Validar trazabilidad completa
5. Probar consultas PostGIS optimizadas
```

---

## 🚨 Manejo de Errores y Rollbacks

### Si Algo Sale Mal
```bash
# Opción 1: Abortar commit actual
git status
git restore [archivos afectados]
# Volver a COMMITS_PLAN.md para replanificar

# Opción 2: Commit parcial
git add [archivos listos]
git commit -m "feat: partial implementation of [feature]"
# Dejar resto para siguiente commit

# Opción 3: Rollback completo
git reset --soft HEAD~1
# Rehacer completamente el commit
```

### Prevención de Errores
- **Cambios pequeños**: Menos probabilidad de errores
- **Validación frecuente**: Detectar problemas temprano
- **Backups implícitos**: Cada commit es un punto de restauración

---

## 📈 Métricas y Seguimiento

### Por Sprint
- **Commits completados**: Total vs planeado
- **Story points**: Progreso vs estimación
- **Tiempo real**: Tiempo tomado vs estimado
- **Errores**: Commits que necesitaron rollback

### Por Commit
- **Tiempo de ejecución**: Desde inicio hasta commit final
- **Archivos modificados**: Cantidad y tipo
- **Errores de validación**: Si hubo que corregir algo
- **Documentation updates**: Si se actualizó correctamente

---

## 🎯 Mejores Prácticas

### Antes de Escribir Código
1. **Leer el plan**: Entender exactamente qué se debe hacer
2. **Revisar dependencias**: Entender qué puede afectar
3. **Definir éxito**: Saber cuándo está terminado

### Durante el Desarrollo
1. **Mantener el foco**: No desviarse por otras ideas
2. **Testear continuamente**: No esperar al final
3. **Documentar mientras se avanza**: No dejar para el final

### Antes del Commit
1. **Validación completa**: Ejecutar todas las validaciones
2. **Documentación actualizada**: Siempre al día
3. **Estado limpio**: No dejar archivos temporales

### Después del Commit
1. **Actualizar progreso**: SCRUM_BOARD.md
2. **Preparar siguiente**: COMMITS_PLAN.md
3. **Reflexionar**: Qué se puede mejorar

---

## 🔄 Herramientas y Comandos Útiles

### Git Commands
```bash
# Ver estado actual
git status

# Ver historia de commits
git log --oneline -10

# Ver cambios específicos
git diff [archivo]

# Deshacer cambios locales
git restore [archivo]

# Cambiar último commit message
git commit --amend -m "nuevo mensaje"
```

### Python Validation
```bash
# Sintaxis básica
python -m py_compile script.py

# Import testing
python -c "import module; print('OK')"

# Run tests
pytest
python -m unittest
```

### Documentation Links
```bash
# Verificar que archivos existen
ls -la docs/
cat docs/CHANGELOG.md

# Buscar referencias
grep -r "REFS:" .
```

---

## 📋 Checklist Final por Commit

### ✅ Pre-Commit Checklist
- [ ] **Objetivo claro**: Sé exactamente qué estoy commiteando
- [ ] **Cambios específicos**: Solo lo planificado
- [ ] **Validación completa**: Tests y verificaciones funcionan
- [ ] **Documentación actualizada**: CHANGELOG, SCRUM_BOARD, COMMITS_PLAN
- [ ] **Estado limpio**: No hay archivos temporales o basura
- [ ] **Mensaje claro**: Título, cuerpo y referencias correctas
- [ ] **Excel RAW intactos**: Archivos originales no modificados
- [ ] **Flujo validado**: Excel RAW → PostgreSQL funciona

### ✅ Post-Commit Checklist
- [ ] **Verificación**: `git status` limpio
- [ ] **Progreso actualizado**: SCRUM_BOARD.md al día
- [ ] **Siguiente paso**: COMMITS_PLAN.md claro para siguiente trabajo
- [ ] **Reflexión**: Qué aprendí o qué puedo mejorar
- [ ] **Datos seguros**: Archivos RAW preservados y trazables

---

*Este workflow asegura trabajo estructurado, mantenible y con contexto manejable para Claude Code*

**Última actualización**: 2025-10-14