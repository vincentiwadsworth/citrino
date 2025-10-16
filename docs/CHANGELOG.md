# CHANGELOG - Citrino

Todos los cambios notables del proyecto Citrino se documentarán en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/)
y este proyecto se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [2.2.2] - 2025-10-16

### Añadido
- **SISTEMA DE VALIDACIÓN RAW**: Pipeline completo de validación de archivos raw → intermedios
  - **scripts/validation/validate_raw_to_intermediate.py**: Procesamiento individual con archivos intermedios
  - **scripts/validation/generate_validation_report.py**: Reportes consolidados HTML/Excel
  - **scripts/validation/diagnose_raw_structure.py**: Diagnóstico automático de estructura
- **VALIDACIÓN HUMANA**: Flujo completo para revisión por equipo Citrino antes de producción
- **ARCHIVOS INTERMEDIOS**: Excel con datos originales + procesados para validación manual
- **REPORTES DE CALIDAD**: Métricas detalladas por archivo y consolidado general

### Cambiado
- **ETL PIPELINE**: Ahora incluye fase de validación humana obligatoria
- **COORDENADAS GUIA URBANA**: Corregido detección (0% → 98.9% coordenadas válidas)
- **NORMALIZACIÓN DE COORDENADAS**: Manejo automático de coordenadas multiplicadas (10^15, 10^16)
- **FLUJO DE TRABAJO**: Raw → Intermedio (validación humana) → Producción

### Arreglado
- **COORDENADAS MULTIPLICADAS**: Detección y corrección automática de coordenadas con factores
- **ESTRUCTURA GUIA URBANA**: Manejo correcto de columnas "Unnamed" y múltiples formatos
- **DETECCIÓN DE SERVICIOS**: Lógica mejorada para identificar diferentes tipos de servicios urbanos

### Métricas de Validación
- **PROPIEDADES**: 60 propiedades procesadas (85% coordenadas, 93.3% precios válidos)
- **SERVICIOS**: 4,942 servicios urbanos (98.9% coordenadas válidas)
- **CALIDAD GENERAL**: 3 archivos EXCELENTE, 1 archivo ACEPTABLE
- **RANGOS GEOGRÁFICOS**: Santa Cruz validado (-17.66 a -17.93, -63.06 a -63.25)

---

## [2.2.1] - 2025-10-15

### Arreglado
- **BUG CRÍTICO DE COORDENADAS**: Corrección de error en estadísticas del ETL `extraer_servicios_urbanos`
  - **Línea 153**: Faltaba `self.servicios_procesados.append(servicio)`
  - **Línea 163**: `servicio.get('coordenadas_validadas', False)` → `servicio.get('metadatos', {}).get('coordenadas_validadas', False)`
- **VALIDACIÓN DE COORDENADAS**: Sistema ahora procesa 4,899 coordenadas válidas (99.2% éxito)
- **INTEGRACIÓN COMPLETA**: Motor de recomendación funcionando con coordenadas reales

### Cambiado
- **ETL Guía Urbana**: Procesamiento de 4,938 servicios urbanos con coordenadas funcionales
- **Sistema de Recomendación**: Integración con 4,899 coordenadas georreferenciadas reales
- **Índices Espaciales**: 8 categorías con datos geoespaciales indexados
- **PostGIS Compatibility**: Sistema listo para migración con coordenadas validadas

### Añadido
- **Debug Tools**: Scripts especializados para debugging de coordenadas
- **Validación Extensiva**: Tests paso a paso del pipeline ETL completo
- **Documentación de Bugs**: Análisis detallado del problema y solución implementada

---

## [2.2.0] - 2025-10-15

### Añadido
- **ETL Mejorado v2.2.0**: Reconstrucción completa de base de datos desde archivos fuente
- **Limpieza Integral**: Eliminación de archivos intermedios y reportes antiguos
- **Validación Controlada**: Proceso ETL con monitoreo y validación continua
- **Reportes de Calidad**: Documentación detallada del proceso ETL y análisis de datos

### Cambiado
- **Base de Datos**: Actualizada a 1,578 propiedades (reducción desde 1,588)
- **Metadata**: Nueva fecha de procesamiento 2025-10-15T13:22:28.350845
- **Archivos Procesados**: Ahora incluye guía urbana municipal (8 archivos totales)
- **Distribución Proveedores**: Optimizada con estrategias específicas por fuente

### Arreglado
- **Calidad de Datos**: Mejora en la consistencia y estructuración de información
- **Procesamiento**: Corrección de errores en extracción de datos complejos
- **Documentación**: Actualización de referencias y enlaces internos

### Eliminado
- **Archivos Intermedios**: Limpieza de backups y reportes temporales
- **Metadata Anterior**: Remoción de información desactualizada

---

## [2.1.0] - 2025-10-14

### Añadido
- **ETL Mejorado**: Sistema híbrido Regex + LLM con 90% eficiencia
- **Sistema de Reportes**: Dashboard en tiempo real con métricas detalladas
- **Estrategias por Proveedor**: Tratamiento específico para cada fuente de datos
- **Análisis de Calidad**: Validación automática y control de calidad
- **Optimización de Costos**: Reducción del 70-80% en uso de tokens LLM

### Cambiado
- **Procesamiento**: Migración de LLM puro a sistema híbrido
- **Extracción de Datos**: Mejora en la calidad y consistencia
- **Reportes**: Nueva estructura de documentación técnica

---

## [2.0.0] - 2025-10-10

### Añadido
- **PostgreSQL + PostGIS**: Arquitectura completa para migración de base de datos
- **Scripts ETL Production-Ready**: Sistema completo de migración JSON → PostgreSQL
- **Índices GIST**: Optimización para búsquedas geoespaciales ultra rápidas
- **Sistema de Validación**: Pruebas de rendimiento y validación integral
- **Switching Automático**: Sistema JSON ↔ PostgreSQL con rollback instantáneo

### Cambiado
- **Arquitectura de Datos**: Preparación para 10x crecimiento sin degradación
- **Consultas Geoespaciales**: Mejora de segundos → milisegundos

---

## [1.4.0] - 2025-10-08

### Añadido
- **Chatbot UI Profesional**: Interfaz conversacional OpenAI-compatible
- **Sistema de Búsqueda Natural**: Consultas en lenguaje conversacional
- **Integración Docker**: Environment de desarrollo listo para producción
- **API Endpoint**: `/v1/chat/completions` compatible con Chatbot UI
- **Métricas de Eficiencia**: 37.7% procesado sin LLM, costo $0.002 USD total

### Cambiado
- **Experiencia de Usuario**: Nueva interfaz conversacional
- **Análisis de Datos**: Integración con chatbot para consultas naturales

---

## [1.3.0] - 2025-10-05

### Añadido
- **Sistema Híbrido de Extracción**: 80% propiedades procesadas sin LLM
- **Fallback Automático**: Cambio automático Z.AI → OpenRouter
- **Reducción de Costos**: 90% reducción en uso de tokens (~$0.63 ahorrados)
- **Reporte de Errores LLM**: Clasificación automática y debug avanzado

### Arreglado
- **Disponibilidad del Sistema**: 99.9% uptime con fallback automático
- **Procesamiento de Errores**: Manejo inteligente de rate limits y fallos

---

## [1.2.0] - 2025-09-30

### Añadido
- **Filtro de Monedas**: Soporte para mercado bimonetario USD/BOB
- **Estadísticas de Oferta**: Análisis por moneda en Citrino Reco
- **Badges de Moneda**: Identificación visual en perfiles guardados

### Cambiado
- **Mercado Boliviano**: Adaptación completa para sistema bimonetario

---

## [1.1.0] - 2025-09-15

### Añadido
- **Motor de Recomendación Inteligente**: Scoring multicritero ponderado
- **Análisis Geográfico**: Fórmula de Haversine para distancias precisas
- **Índice Espacial**: Búsquedas optimizadas por zona
- **Filtros Avanzados**: UV/Manzana para segmentación detallada

### Cambiado
- **Algoritmos de Recomendación**: Evaluación multifactor mejorada
- **Procesamiento Geográfico**: Cálculos de distancia más precisos

---

## [1.0.0] - 2025-09-01

### Añadido
- **Sistema Base**: Primera versión completa de Citrino
- **Procesamiento de Datos**: Sistema ETL inicial
- **Frontend Web**: Interface para análisis de propiedades
- **API Backend**: REST API para consultas y análisis
- **Base de Datos JSON**: Almacenamiento inicial de propiedades

---

## Notas de la Versión

### Versión 2.2.0 - ETL Reconstruido
Esta versión representa una reconstrucción completa del sistema de procesamiento ETL:

- **Limpieza**: Eliminación completa de datos procesados anteriormente
- **Reconstrucción**: Proceso desde cero con validación controlada
- **Calidad**: Mejora en la consistencia y estructura de datos
- **Documentación**: Reportes detallados del proceso y resultados

### Versión 2.0.0 - Arquitectura PostgreSQL
Hitó importante en la arquitectura del sistema:

- **Escalabilidad**: Preparación para 10x crecimiento
- **Rendimiento**: Mejora drástica en consultas geoespaciales
- **Concurrencia**: Soporte multiusuario sin bloqueos
- **Resiliencia**: Backup automático y recuperación

### Roadmap Futuro

**Próximas versiones planeadas:**
- **2.3.0**: Geocodificación avanzada (<15% propiedades sin zona)
- **2.4.0**: Optimización UI/UX para mayor adopción interna
- **3.0.0**: Migración completa a PostgreSQL en producción

---

**Mantenido por el equipo de Citrino**
Santa Cruz de la Sierra, Bolivia