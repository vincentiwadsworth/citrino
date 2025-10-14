# 🔄 Changelog de Citrino

Historial de versiones y cambios del sistema de análisis inmobiliario.

## [Upcoming] v2.0.0 - Reestructuración y Nueva Arquitectura (Planeado)

### 🏗️ Cambios Mayores
- **Nueva arquitectura de datos**: Migración desde JSON centralizado a sistema procesado por lotes
- **Sistema de documentación**: Implementación de CHANGELOG, SCRUM_BOARD y gestión por commits
- **Limpieza integral del repositorio**: Eliminación de archivos temporales y reorganización

### 📁 Estructura de Archivos
- Nuevo directorio `docs/` con documentación estructurada
- Reorganización de `scripts/` por funcionalidad (ETL, análisis, mantenimiento)
- Directorio `legacy/` para código obsoleto
- Directorio `archive/` para documentación histórica

### 🔄 Mejoras de Proceso
- Workflow estructurado por commits
- Documentación de transición de arquitectura
- Plan de migración a base de datos optimizada

### Limpieza de Repositorio
- Eliminados archivos JSON temporales (test_*.json)
- Removidos scripts de debug (debug_*.py)
- Limpiada documentación temporal obsoleta
- Validado funcionamiento del sistema post-limpieza

---

## v1.8.5 - 2025-10-14

### 🐛 Bugs Fixeados
- Corrección en procesamiento de coordenadas geográficas
- Fix en cálculo de distancias Haversine

### ✨ Mejoras
- Optimización de cache en motor de recomendación
- Mejoras en logging de ETL

---

## v1.8.0 - 2025-10-09

### ✨ Nuevas Funcionalidades
- **Sistema de extracción híbrido**: Regex + LLM para Proveedor 02
- **Fallback automático**: OpenRouter como backup de Z.AI
- **Cache LLM**: Reducción del 90% en consumo de tokens

### 📊 Métricas
- 1,588 propiedades procesadas
- 4,777 servicios urbanos indexados
- 80% de extracción sin necesidad de LLM

### 🔧 Mejoras Técnicas
- Integración con DescriptionParser para extracción inteligente
- Sistema de monitoreo de proveedores LLM
- Optimización de procesamiento por lotes

---

## v1.7.0 - 2025-08-29

### 📈 Actualización de Datos
- Procesamiento de múltiples proveedores (01-05)
- Actualización de base de datos con 1,583 propiedades

### 🗺️ Mejoras Geoespaciales
- Mejora en precisión de coordenadas
- Nuevos patrones de extracción de zonas

### 🔍 Sistema de Búsqueda
- Búsqueda por UV y Manzana implementada
- Filtros avanzados de ubicación

---

## v1.6.0 - 2025-08-17

### 🤖 Integración LLM
- Implementación inicial con Z.AI GLM-4.6
- Sistema de extracción de descripciones
- Procesamiento de lenguaje natural

### 📊 Análisis de Datos
- Motor de recomendación mejorado
- Evaluación de compatibilidad inversor-propiedad

---

## v1.5.0 - 2025-08-15

### 🏢 Sistema de Consultoría
- Interfaz para inversores internos
- Sistema de recomendación por perfil
- Análisis de oportunidades de inversión

### 🌐 Frontend Modernizado
- UI responsiva con Bootstrap 5
- Integración con API REST
- Sistema de notas y hallazgos

---

## v1.0.0 - 2025-07-XX (Versión Inicial)

### 🚀 Lanzamiento Inicial
- API REST básica con Flask
- Motor de recomendación simple
- Base de datos JSON inicial
- Interfaz HTML básica

### 📋 Funcionalidades Principales
- Búsqueda de propiedades
- Filtros básicos
- Sistema de coordenadas geográficas
- Integración con guía urbana municipal

---

## 📝 Notas de Versión

### Convenciones
- **🚀 Nuevas Funcionalidades**: Características completamente nuevas
- **✨ Mejoras**: Mejoras a funcionalidades existentes
- **🐛 Bugs Fixeados**: Corrección de errores
- **📊 Métricas**: Datos estadísticos y de rendimiento
- **🔧 Mejoras Técnicas**: Cambios técnicos internos
- **📁 Estructura**: Cambios en organización de archivos
- **🔄 Proceso**: Mejoras en flujos de trabajo

### Siguientes Pasos Planeados
1. **Sistema de Procesamiento por Lote**: Documentos intermedios con UUIDs
2. **Migración de Base de Datos**: Evaluación PostgreSQL vs Neo4j vs Híbrido
3. **Sistema de Duplicados**: Detección inteligente entre proveedores
4. **Automatización**: CI/CD para actualizaciones de datos

---

*Última actualización: 2025-10-14*