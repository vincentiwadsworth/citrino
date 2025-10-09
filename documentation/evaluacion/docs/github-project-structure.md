# Estructura para GitHub Projects - Citrino PoC

## Información del Proyecto
- **Nombre**: Sistema de Recomendación Inmobiliaria - PoC
- **Descripción**: Sistema de recomendación de propiedades para asesores comerciales basado en perfil de prospectos
- **Repositorio**: vincentiwadsworth/citrino-poc
- **Tipo**: Kanban

## Columnas del Proyecto

### 📋 Backlog
- Especificación completa del sistema
- Plan técnico de implementación
- Desglose de tareas por commits
- Preparación de datos iniciales

### ACTUALIZANDO: En Progreso
- [Epic] Fase 1: Preparación de Datos (Commits 1-4)
- [Epic] Fase 2: Motor de Recomendación (Commits 5-8)
- [Epic] Fase 3: Interfaz de Usuario (Commits 9-12)
- [Epic] Fase 4: Validación y Demo (Commits 13-16)

### 👀 En Revisión
- Validación con equipo de Citrino
- Pruebas de integración
- Revisión de código y arquitectura

### OK: Completado
- Constitución del proyecto
- Especificación de requisitos
- Configuración inicial de repositorio

## Epics (Tareas Principales)

### Epic 1: Fase 1 - Preparación de Datos
**Descripción**: Estructurar el proyecto y preparar los datasets iniciales
**Tareas**:
- [ ] Crear estructura de directorios y archivos base
- [ ] Preparar dataset de 5 propiedades en JSON
- [ ] Obtener y formatear datos de servicios (guía urbana)
- [ ] Recopilar datos demográficos por zona
- [ ] Crear 3 perfiles de prospecto ejemplo
- [ ] Documentar estructura de datos

### Epic 2: Fase 2 - Motor de Recomendación
**Descripción**: Implementar el algoritmo core de matching y LLM integration
**Tareas**:
- [ ] Implementar función de cálculo de compatibilidad
- [ ] Desarrollar sistema de ponderación por factores
- [ ] Crear motor de recomendación principal
- [ ] Implementar generador de justificaciones
- [ ] Integrar OpenRouter/OpenAI para lenguaje natural
- [ ] Desarrollar parser de lenguaje natural

### Epic 3: Fase 3 - Interfaz de Usuario
**Descripción**: Crear CLI para consulta conversacional
**Tareas**:
- [ ] Crear script CLI con Typer
- [ ] Implementar comando de consulta básico
- [ ] Integrar LLM para consultas en lenguaje natural
- [ ] Añadir utilidades y opciones de filtrado
- [ ] Implementar manejo de errores y logging

### Epic 4: Fase 4 - Validación y Demo
**Descripción**: Probar el sistema completo y preparar demostración
**Tareas**:
- [ ] Realizar pruebas de integración completas
- [ ] Validar tiempos de respuesta (< 3 segundos)
- [ ] Crear documentación para asesores
- [ ] Preparar demostración funcional
- [ ] Recopilar feedback del equipo
- [ ] Documentar lecciones aprendidas

## Hitos (Milestones)

### Hito 1: OBJETIVO: MVP Funcional
- Motor de recomendación básico funcionando
- CLI para consultas estructuradas
- Dataset de 5 propiedades con servicios
- **Fecha estimada**: Commit 8

### Hito 2: 🤖 Consultas en Lenguaje Natural
- Integración con LLM completa
- Consultas conversacionales funcionales
- Parser de lenguaje natural estable
- **Fecha estimada**: Commit 12

### Hito 3: 📋 Demo Lista para Presentar
- Sistema completo y probado
- Documentación para usuarios
- Demostración grabada
- **Fecha estimada**: Commit 16

## Labels para Clasificación

### Prioridad
- 🔴 Alta: Crítico para el MVP
- 🟡 Media: Importante pero no bloqueante
- 🟢 Baja: Mejoras y documentación

### Tipo
- 🐛 Bug: Errores y correcciones
- NUEVO: Feature: Nueva funcionalidad
- DOC: Documentation: Documentación y guías
- 🧪 Test: Pruebas y validación
- 🏗️ Infrastructure: Configuración y estructura

### Fase
- GRAFICO: Datos: Tareas relacionadas con datos
- ⚙️ Motor: Lógica del algoritmo
- 🖥️ UI: Interfaz de usuario
- OK: QA: Calidad y pruebas

## Notas de Configuración

### Automatización sugerida:
1. **Mover tarjetas automáticamente**: Cuando se hace commit con mensaje específico
2. **Alertas de progreso**: Notificaciones cuando se completa un epic
3. **Reportes semanales**: Resumen de progreso para stakeholders

### Integración con repositorio:
- Vincular commits a tarjetas específicas
- Automatizar movimiento de tareas basado en palabras clave
- Sincronizar estado de PRs con el proyecto

---

**Creado**: 20 de septiembre de 2025
**Próxima revisión**: Después de completar Fase 1
**Stakeholders**: Equipo de desarrollo, Julio (CEO), Equipo Citrino