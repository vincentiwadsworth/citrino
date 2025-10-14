# 🔄 Workflow de Trabajo por Commits

Guía de flujo de trabajo para desarrollo estructurado y mantenible en Citrino.

---

## 🎯 Filosofía del Workflow

### Principios
- **Commits pequeños y enfocados**: Cambios específicos y validables
- **Documentación primero**: Siempre documentar antes de implementar
- **Validación continua**: Verificar funcionalidad en cada paso
- **Trazabilidad clara**: Referencias cruzadas entre documentación y código

### Beneficios
- Manejo eficiente de contexto de Claude Code
- Historial claro y mantenible
- Rollbacks fáciles y seguros
- Colaboración estructurada

---

## 📋 Ciclo de Vida de un Commit

### 1. Planificación 📝
```bash
# Antes de empezar
1. Revisar COMMITS_PLAN.md para el commit actual
2. Entender el objetivo y alcance exacto
3. Identificar archivos que serán modificados
4. Definir criterios de validación
```

### 2. Ejecución 🛠️
```bash
# Durante el desarrollo
1. Realizar cambios específicos del commit
2. Mantenerse enfocado en el objetivo definido
3. No agregar cambios extras no planificados
4. Testear a medida que se avanza
```

### 3. Validación ✅
```bash
# Antes de commitear
1. Ejecutar tests básicos del sistema
2. Verificar que API server inicia correctamente
3. Confirmar que no hay imports rotos
4. Validar cambios específicos del commit
```

### 4. Documentación 📚
```bash
# Actualizar documentación
1. Actualizar CHANGELOG.md con cambios realizados
2. Actualizar SCRUM_BOARD.md con progreso
3. Actualizar COMMITS_PLAN.md si es necesario
4. Revisar que la documentación esté sincronizada
```

### 5. Commit ✨
```bash
# Mensaje de commit estándar
tipo: descripción concisa

- Detalles específicos del cambio
- Impacto y validación realizada
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
- Update CLAUDE.md with new references

Refs: #sprint-1-story-1
```

```bash
cleanup: remove temporary test files

- Remove test_*.json files (7 files)
- Remove debug_*.py scripts (3 files)
- Remove temporary analysis reports

Validated: API server and tests functional
Refs: #sprint-1-story-2
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
```

### Reanudación de Trabajo
```bash
# Al iniciar nueva sesión
1. Revisar COMMITS_PLAN.md para continuar
2. Leer SCRUM_BOARD.md para ver progreso actual
3. Revisar CHANGELOG.md para entender historia reciente
4. Identificar exactamente dónde se quedó el trabajo
```

### Reducción de Contexto
- **Commits atómicos**: Un cambio conceptual por commit
- **Documentación externa**: Mantener estado en archivos MD
- **Progresión incremental**: No hacer cambios grandes de una vez

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
3. Verificar que responses son correctos
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

### ✅ Post-Commit Checklist
- [ ] **Verificación**: `git status` limpio
- [ ] **Progreso actualizado**: SCRUM_BOARD.md al día
- [ ] **Siguiente paso**: COMMITS_PLAN.md claro para siguiente trabajo
- [ ] **Reflexión**: Qué aprendí o qué puedo mejorar

---

*Este workflow asegura trabajo estructurado, mantenible y con contexto manejable para Claude Code*

**Última actualización**: 2025-10-14