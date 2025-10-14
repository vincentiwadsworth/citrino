# Sistema de Actualización de Base de Datos

## Overview

Este documento describe el sistema completo para actualizar la base de datos de propiedades con control granular y retroalimentación en tiempo real.

## Componentes

### 1. Procesamiento Incremental
- **Script**: `scripts/build_relevamiento_dataset_incremental.py`
- **Propósito**: Procesar datos en lotes pequeños con checkpoints
- **Ventajas**: Recuperación ante errores, control de calidad, menor uso de memoria

### 2. Sistema de Feedback
- **Script**: `scripts/procesamiento_con_feedback.py`
- **Propósito**: Proporcionar retroalimentación detallada en tiempo real
- **Ventajas**: Métricas de calidad, rendimiento, estadísticas LLM, detección de problemas

### 3. Scripts de Apoyo
- `scripts/procesamiento_controlado_simple.py` - Guía de uso
- `scripts/demo_feedback.py` - Demostración del sistema

## Comandos de Uso

### Procesamiento Incremental Basico

```bash
# Lote pequeño de prueba
python scripts/build_relevamiento_dataset_incremental.py --batch-size 10 --max-propiedades 10

# Procesar 2 archivos
python scripts/build_relevamiento_dataset_incremental.py --batch-size 15 --max-archivos 2

# Lote mediano controlado
python scripts/build_relevamiento_dataset_incremental.py --batch-size 25 --max-propiedades 50

# Continuar desde donde se quedo
python scripts/build_relevamiento_dataset_incremental.py --continuar
```

### Procesamiento con Feedback

```bash
# Procesamiento con retroalimentación detallada
python scripts/procesamiento_con_feedback.py --batch-size 20

# Feedback con limite de propiedades
python scripts/procesamiento_con_feedback.py --batch-size 15 --max-propiedades 30

# Feedback para archivos específicos
python scripts/procesamiento_con_feedback.py --batch-size 20 --max-archivos 2
```

### Demostraciones

```bash
# Demo del sistema de feedback
python scripts/demo_feedback.py

# Guía de procesamiento controlado
python scripts/procesamiento_controlado_simple.py
```

## Salidas Generadas

### Archivos de Datos
- `data/base_datos_relevamiento.json` - Base final (cuando completa)
- `data/base_datos_relevamiento_lote_N.json` - Lotes intermedios
- `data/base_datos_relevamiento_lote_N_backup.json` - Backups de lotes

### Archivos de Feedback
- `data/feedback_procesamiento.json` - Métricas en tiempo real
- `data/procesamiento_detailed.log` - Log detallado de procesamiento

### Archivos de Control
- `data/.procesamiento_checkpoint.json` - Estado para reanudar

## Métricas de Feedback

### Indicadores de Calidad
- **Con precio**: Propiedades que tienen precio definido
- **Con ubicación**: Propiedades con zona geográfica
- **Con coordenadas**: Propiedades con latitud/longitud
- **Con descripción**: Propiedades con texto descriptivo

### Indicadores de Rendimiento
- **Tiempo por lote**: Duración del procesamiento del lote
- **Tiempo promedio/propiedad**: Velocidad de procesamiento
- **Throughput**: Propiedades por minuto/hora

### Estadísticas LLM
- **Llamadas totales**: Peticiones al LLM
- **Cache hits**: Resultados desde caché
- **Fallbacks**: Cambios a proveedor secundario
- **Tokens estimados**: Consumo de tokens

### Detección de Problemas
- **Errores**: Problemas críticos que afectan procesamiento
- **Warnings**: Problemas de calidad de datos
- **Detalles**: Descripción específica de cada problema

## Flujo de Trabajo Recomendado

### 1. Prueba Inicial
```bash
python scripts/procesamiento_con_feedback.py --batch-size 5 --max-propiedades 5
```

### 2. Verificar Resultados
- Revisar `data/feedback_procesamiento.json`
- Revisar `data/procesamiento_detailed.log`
- Verificar calidad de datos en el lote

### 3. Escalar Progresivamente
```bash
python scripts/procesamiento_con_feedback.py --batch-size 20 --max-propiedades 100
```

### 4. Procesamiento Completo
```bash
python scripts/procesamiento_con_feedback.py --batch-size 20
```

## Características Avanzadas

### Checkpoints Automáticos
- El sistema guarda estado cada lote
- Permite reanudar si hay interrupciones
- Archivo: `data/.procesamiento_checkpoint.json`

### Recuperación ante Errores
- Si falla el procesamiento, usa `--continuar`
- No pierde propiedades ya procesadas
- Mantiene integridad de datos

### Control Granular
- `--batch-size`: Controla tamaño de lotes
- `--max-propiedades`: Limita propiedades totales
- `--max-archivos`: Limita archivos a procesar

### Monitoreo en Tiempo Real
- Feedback por lote en consola
- Métricas acumuladas
- Detección temprana de problemas

## Configuración de Lotes

### Lotes Pequeños (5-10)
- **Ventaja**: Control máximo, feedback rápido
- **Uso**: Pruebas iniciales, depuración
- **Riesgo**: Mayor overhead por lote

### Lotes Medianos (15-25)
- **Ventaja**: Balance velocidad/control
- **Uso**: Producción estándar
- **Riesgo**: Tiempo de recuperación moderado

### Lotes Grandes (50+)
- **Ventaja**: Máxima velocidad
- **Uso**: Datos confiables, procesamiento rápido
- **Riesgo**: Mayor pérdida si falla

## Troubleshooting

### Problemas Comunes

#### Rate Limit LLM
- **Síntoma**: Muchos mensajes "fallback activado"
- **Solución**: Esperar o reducir tamaño de lote

#### Calidad de Datos Baja
- **Síntoma**: Bajo porcentaje de precio/ubicación
- **Solución**: Revisar fuente de datos, ajustar extractores

#### Errores de Procesamiento
- **Síntoma**: Errores count > 0
- **Solución**: Revisar log detallado, corregir datos fuente

#### Memoria Insuficiente
- **Síntoma**: Crashes al procesar
- **Solución**: Reducir batch-size, usar --max-propiedades

### Logs Útiles

#### Feedback JSON
```json
{
  "metricas_actuales": {
    "propiedades_con_precio": 150,
    "propiedades_con_ubicacion": 200,
    "llamadas_llm": 50,
    "errores_count": 2
  }
}
```

#### Log Detallado
```
2025-10-09 18:30:14 - INFO - LOTE 1 COMPLETADO
2025-10-09 18:30:14 - INFO - Propiedades: 10
2025-10-09 18:30:14 - INFO - Tiempo: 0.00s
2025-10-09 18:30:14 - WARNING - ERRORES: 1
```

## Integración con Sistema Existente

### Compatibilidad
- Totalmente compatible con scripts existentes
- No afecta procesamiento normal
- Puede usarse junto con sistema original

### Migración
1. **Prueba**: Usar sistema feedback con datos de muestra
2. **Validación**: Comparar resultados con sistema original
3. **Transición**: Reemplazar gradualmente

### Coexistencia
- Sistema original: `build_relevamiento_dataset.py`
- Sistema incremental: `build_relevamiento_dataset_incremental.py`
- Sistema feedback: `procesamiento_con_feedback.py`

## Best Practices

### Antes del Procesamiento
1. Verificar archivos en `data/raw/`
2. Revisar configuración LLM (`.env`)
3. Hacer backup de base de datos existente

### Durante el Procesamiento
1. Monitorear feedback en tiempo real
2. Revisar métricas de calidad
3. Atender a errores y warnings

### Después del Procesamiento
1. Validar base de datos final
2. Comparar con versión anterior
3. Archivar logs de procesamiento

### Mantenimiento
1. Limpiar archivos temporales (lotes, backups)
2. Revisar y actualizar extractores regex
3. Optimizar tamaño de lotes según experiencia

## Ejemplos de Casos de Uso

### Caso 1: Actualización Diaria
```bash
# Procesar nuevos archivos del día
python scripts/procesamiento_con_feedback.py --batch-size 20 --max-archivos 2
```

### Caso 2: Recuperación de Datos
```bash
# Continuar procesamiento interrumpido
python scripts/procesamiento_con_feedback.py --continuar
```

### Caso 3: Validación de Calidad
```bash
# Procesar muestra pequeña y revisar calidad
python scripts/procesamiento_con_feedback.py --batch-size 10 --max-propiedades 50
```

### Caso 4: Procesamiento Completo
```bash
# Procesar todos los archivos con monitoreo
python scripts/procesamiento_con_feedback.py --batch-size 25
```

## Conclusión

El sistema de actualización con feedback proporciona:
- **Control total** sobre el proceso de actualización
- **Visibilidad completa** de métricas y calidad
- **Recuperación automática** ante errores
- **Optimización continua** basada en datos

Recomendación: Usar lotes de 20 propiedades para balance óptimo entre velocidad y seguridad.