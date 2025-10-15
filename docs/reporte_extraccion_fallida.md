# Reporte de Extracción Fallida de Propiedades

**Fecha de generación:** 2025-10-15

## Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| Total registros RAW | 6,952 |
| Propiedades extraídas exitosamente | 1,578 |
| Propiedades fallidas | 5,146 |
| Tasa de éxito general | 22.7% |
| Tasa de fallo general | 74.0% |
| Proveedores procesados | 6 |

## Análisis por Proveedor

| Proveedor | Registros RAW | Extraídas | Fallidas | Tasa Éxito | Tasa Fallo |
|-----------|---------------|-----------|----------|------------|------------|
|  | 4,942 | 0 | 4,942 | 0.0% | 100.0% |
| 01 | 181 | 177 | 4 | 97.8% | 2.2% |
| 02 | 1,593 | 1,202 | 391 | 75.5% | 24.5% |
| 03 | 19 | 13 | 6 | 68.4% | 31.6% |
| 04 | 119 | 95 | 24 | 79.8% | 20.2% |
| 05 | 98 | 91 | 7 | 92.9% | 7.1% |

## Motivos Principales de Fallo

### SIN_DATOS_BASICOS (CRÍTICO)
- **Cantidad:** 5,146 propiedades
- **Porcentaje del total:** 100.0%

### SIN_UBICACION (CRÍTICO)
- **Cantidad:** 5,142 propiedades
- **Porcentaje del total:** 99.9%

### COORDENADAS_INVALIDAS (CRÍTICO)
- **Cantidad:** 4,961 propiedades
- **Porcentaje del total:** 96.4%

### SIN_PRECIO (CRÍTICO)
- **Cantidad:** 4,945 propiedades
- **Porcentaje del total:** 96.1%

### PRECIO_INVALIDO (BAJO)
- **Cantidad:** 96 propiedades
- **Porcentaje del total:** 1.9%

## Análisis Detallado - Proveedor 02

- **Total registros:** 1,593
- **Precios inválidos:** 1,383
- **Sin descripción:** 14
- **Con descripción corta:** 6
- **Con descripción larga:** 1,573

## Recomendaciones

### 1. Revisar y mejorar criterios de extracción (Prioridad 1)
- **Tipo:** MEJORA_ETL_GENERAL
- **Descripción:** La tasa de fallo es del 74.0%, lo que indica problemas sistémicos
- **Acción recomendada:** Relajar criterios de validación o mejorar extracción de datos

### 2. Intervención urgente Proveedor  (Prioridad 2)
- **Tipo:** PROVEEDOR_ESPECIFICO
- **Descripción:** El Proveedor  tiene una tasa de fallo del 100.0%
- **Acción recomendada:** Analizar formato de datos y desarrollar extractor específico

### 3. Implementar sistema de extracción con LLM (Prioridad 3)
- **Tipo:** IMPLEMENTACION_LLM
- **Descripción:** Hay 5146 propiedades que podrían recuperarse con LLM
- **Acción recomendada:** Usar sistema híbrido Regex + LLM para extraer datos de descripciones

---
*Reporte generado automáticamente por el script `reporte_extraccion_fallida.py`*
