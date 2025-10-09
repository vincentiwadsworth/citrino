# Recomendaciones Específicas para Franz y Jonathan - Citrino

> **Recomendaciones prácticas basadas en la auditoría de datos**
>
> Fecha: Septiembre 21, 2025
> Destinatarios: Franz (relevamiento inhouse) y Jonathan (scraping)

---

## 📋 **INTRODUCCIÓN**

Basado en el análisis detallado de ambas fuentes de datos, aquí presento recomendaciones específicas y accionables para mejorar la calidad y efectividad de sus respectivos procesos de recolección de datos.

---

## 🏢 **RECOMENDACIONES PARA FRANZ (Relevamiento Inhouse)**

### **Fortalezas Actuales a Mantener**
✅ **Excelente trabajo en estructura de datos** (95.4% del total)
✅ **Alta consistencia en formatos**
✅ **Cobertura comprehensiva de 326 proyectos**
✅ **Datos completos en campos críticos**

### **Áreas de Mejora Identificadas**

#### 1. **ESTANDARIZACIÓN DE ZONAS** (Prioridad ALTA)
**Problema actual:** 87.3% de completitud pero 70% de consistencia

**Recomendaciones específicas:**
```python
# Crear lista maestra de zonas estandarizadas
ZONAS_ESTANDAR = {
    "equipetrol": ["Equipetrol", "EQUIPETROL", "equi", "equipetrol scz"],
    "zona_norte": ["Zona Norte", "NORTE", "Zona Norte Scz", "Norte Santa Cruz"],
    "centro": ["Centro", "CENTRO HISTORICO", "Centro Scz", "Casco Viejo"],
    "urubo": ["Urubó", "URUBO", "Urubo Santa Cruz"],
    "las_palmas": ["Las Palmas", "LAS PALMAS", "Palmas"]
}
```

**Acciones inmediatas:**
- [ ] Crear diccionario de normalización de zonas
- [ ] Implementar validación automática en tiempo de captura
- [ ] Estandarizar todas las variaciones a un único formato
- [ ] Documentar el estándar oficial para todo el equipo

#### 2. **COORDENADAS CONSISTENTES** (Prioridad MEDIA)
**Problema actual:** 82.1% de completitud pero múltiples formatos

**Recomendaciones específicas:**
```python
# Estándar único: Grados decimales con 6 decimales
COORDENADAS_ESTANDAR = {
    "formato": "decimal_grados",
    "precision": 6,
    "ejemplo": "-17.783619, -63.181210"
}
```

**Acciones inmediatas:**
- [ ] Estandarizar todas las coordenadas a grados decimales
- [ ] Implementar validación de rangos para Santa Cruz
- [ ] Usar herramientas de geocodificación para direcciones sin coordenadas
- [ ] Capacitar al equipo en uso de GPS y formatos estándar

#### 3. **ACTUALIZACIÓN TEMPORAL** (Prioridad MEDIA)
**Problema actual:** Datos de diferentes fechas sin estandarización

**Recomendaciones específicas:**
```python
# Estándar de fechas para todos los relevamientos
ESTANDAR_FECHAS = {
    "formato": "YYYY-MM-DD",
    "campo_obligatorio": "fecha_relevamiento",
    "actualizacion_mensual": True,
    "vigencia_precios": 30  # días
}
```

**Acciones inmediatas:**
- [ ] Implementar fecha de relevamiento obligatoria
- [ ] Establecer周期 de actualización mensual
- [ ] Crear sistema de vigencia de precios
- [ ] Documentar procedimiento para actualizaciones

#### 4. **CONTROL DE CALIDAD EN TIEMPO REAL** (Prioridad ALTA)
**Recomendaciones específicas:**
```python
# Validaciones automáticas durante la captura
VALIDACIONES = {
    "precio": {"min": 50000, "max": 1000000, "tipo": "numerico"},
    "superficie": {"min": 30, "max": 1000, "tipo": "numerico"},
    "habitaciones": {"min": 1, "max": 10, "tipo": "entero"},
    "direccion": {"min_longitud": 10, "obligatorio": True},
    "zona": {"valores_validos": ZONAS_ESTANDAR.keys()}
}
```

**Acciones inmediatas:**
- [ ] Implementar validaciones en formulario de captura
- [ ] Crear alertas para datos fuera de rango
- [ ] Establecer checklist de calidad por proyecto
- [ ] Designar responsable de calidad por zona

### **Herramientas Recomendadas para Franz**

#### 1. **Sistema de Validación Automática**
```python
# Script de validación para cada archivo procesado
def validar_archivo_franz(archivo_excel):
    validaciones = [
        validar_campos_obligatorios(),
        validar_formato_zonas(),
        validar_coordenadas(),
        validar_rangos_numericos(),
        detectar_duplicados_internos()
    ]
    return generar_reporte_calidad(validaciones)
```

#### 2. **Dashboard de Monitoreo**
- [ ] Crear dashboard con métricas de calidad por proyecto
- [ ] Alertas para datos inconsistentes
- [ ] Seguimiento de actualizaciones por zona
- [ ] Reporte semanal de calidad

#### 3. **Capacitación Continua**
- [ ] Taller mensual de estandarización
- [ ] Manual de procedimientos actualizado
- [ ] Certificación en calidad de datos
- [ ] Sistema de mentoría entre equipos

---

## 🕷️ **RECOMENDACIONES PARA JONATHAN (Scraping)**

### **Fortalezas Actuales**
✅ **Buen trabajo en cobertura complementaria**
✅ **Actualización potencial más frecuente**
✅ **Captura de datos que Franz no cubre**

### **Áreas Críticas de Mejora**

#### 1. **REPARACIÓN DE ZONAS CORRUPTAS** (Prioridad URGENTE)
**Problema actual:** 46.6% de datos de zonas ilegibles

**Recomendaciones específicas:**
```python
# Proceso de limpieza de texto para zonas
def limpiar_zonas_scraping(zona_cruda):
    pasos = [
        eliminar_caracteres_especiales(),
        corregir_codificacion_utf8(),
        normalizar_espacios(),
        aplicar_diccionario_correccion(),
        validar_contra_lista_maestra()
    ]
    return zona_limpia
```

**Acciones inmediatas:**
- [ ] Implementar limpieza masiva de datos existentes
- [ ] Crear pipeline de limpieza para nuevos datos
- [ ] Establecer diccionario de corrección por fuente
- [ ] Validar cada zona contra lista maestra de Citrino

#### 2. **MEJORA DE ALGORITMOS POR FUENTE** (Prioridad ALTA)

**Para Bien Inmuebles (45% calidad zonas):**
```python
# Optimización específica para Bien Inmuebles
BIEN_INMUEBLES_CONFIG = {
    "zona_selectores": {
        "primary": ".zona-text",
        "fallback": [".ubicacion", ".barrio", ".direccion"],
        "extraction": "limpiar_texto_completo"
    },
    "precio_selectores": {
        "main": ".precio",
        "moneda_tratamiento": "eliminar_simbolos",
        "formato": "numerico"
    }
}
```

**Para C21 (78% calidad zonas):**
```python
# Mantener y mejorar C21 (mejor fuente scraping)
C21_CONFIG = {
    "mejoras": [
        "implementar_validacion_zonas",
        "optimizar_extraccion_coordenadas",
        "aumentar_frecuencia_scraping",
        "implementar_monitoreo_calidad"
    ]
}
```

**Acciones inmediatas:**
- [ ] Reescribir selectores para cada fuente específica
- [ ] Implementar validación en tiempo real durante scraping
- [ ] Crear sistema de fallback para datos faltantes
- [ ] Establecer calidad mínima aceptable por fuente

#### 3. **SISTEMA DE DEDUPLICACIÓN** (Prioridad ALTA)
**Problema actual:** 986 duplicados entre fuentes

**Recomendaciones específicas:**
```python
# Algoritmo de detección de duplicados
def detectar_duplicados(propiedad_nueva, base_existente):
    criterios = {
        "direccion": similitud_texto(propiedad_nueva.direccion, existente.direccion),
        "coordenadas": distancia_geografica(propiedad_nueva.coords, existente.coords),
        "precio": diferencia_porcentual(propiedad_nueva.precio, existente.precio),
        "caracteristicas": similitud_caracteristicas(propiedad_nueva, existente)
    }
    return calcular_puntuacion_matching(criterios) > UMBRAL_DUPLICADO
```

**Acciones inmediatas:**
- [ ] Implementar sistema de matching antes de almacenar
- [ ] Crear registro de auditoría para decisiones de deduplicación
- [ ] Establecer reglas de prioridad (Franz > Scraping)
- [ ] Sistema de actualización vs. creación de nuevos registros

#### 4. **MONITOREO DE CALIDAD POR FUENTE** (Prioridad MEDIA)
**Recomendaciones específicas:**
```python
# Sistema de calificación por fuente
CALIDAD_FUENTES = {
    "C21": {"objetivo": 90%, "actual": 78%, "accion": "mejorar_selectores"},
    "Bien Inmuebles": {"objetivo": 80%, "actual": 45%, "accion": "reconstruir_scraping"},
    "Remax": {"objetivo": 75%, "actual": 52%, "accion": "optimizar_extraccion"},
    "Capital Corp": {"objetivo": 70%, "actual": 38%, "accion": "reevaluar_fuente"},
    "Ultracasas": {"objetivo": 65%, "actual": 29%, "accion": "considerar_eliminar"}
}
```

**Acciones inmediatas:**
- [ ] Implementar dashboard de calidad por fuente
- [ ] Establecer umbrales mínimos de calidad
- [ ] Sistema de alertas automáticas
- [ ] Reevaluar fuentes de bajo rendimiento

### **Herramientas Recomendadas para Jonathan**

#### 1. **Pipeline de Scraping Mejorado**
```python
# Pipeline completo con validaciones
class ScrapingPipeline:
    def process_item(self, item, spider):
        # 1. Validación básica
        if not self.validacion_minima(item):
            raise DropItem("Datos insuficientes")

        # 2. Limpieza de texto
        item_limpio = self.limpiar_campos(item)

        # 3. Estandarización
        item_estandar = self.estandarizar_formatos(item_limpio)

        # 4. Detección de duplicados
        if self.es_duplicado(item_estandar):
            return self.manejar_duplicado(item_estandar)

        # 5. Enriquecimiento
        item_final = self.enriquecer_datos(item_estandar)

        return item_final
```

#### 2. **Sistema de Monitoreo en Tiempo Real**
```python
# Monitoreo continuo de calidad
class MonitoreoScraping:
    def verificar_salud_fuente(self, fuente):
        metricas = {
            "tasa_exito": self.calcular_tasa_exito(fuente),
            "calidad_datos": self.evaluar_calidad(fuente),
            "frecuencia_actualizacion": self.verificar_frecuencia(fuente),
            "errores_comunes": self.analizar_errores(fuente)
        }
        return self.generar_alertas(metricas)
```

#### 3. **Herramientas de Depuración**
- [ ] Logger detallado por cada intento de scraping
- [ ] Sistema de captura de errores con screenshots
- [ ] Análisis de cambios en estructura de páginas web
- [ ] Sistema de recuperación automática ante fallos

---

## 🤝 **RECOMENDACIONES DE COLABORACIÓN**

### **1. Sistema de Integración Estandarizado**
```python
# Estándar común entre Franz y Jonathan
ESTANDAR_INTEGRACION = {
    "campos_obligatorios": ["id", "nombre", "precio", "superficie_m2", "habitaciones"],
    "formatos_comunes": {
        "zona": ZONAS_ESTANDAR,
        "coordenadas": COORDENADAS_ESTANDAR,
        "fecha": ESTANDAR_FECHAS
    },
    "calidad_minima": {
        "completitud": 0.85,
        "consistencia": 0.80,
        "precision": 0.75
    }
}
```

### **2. Proceso de Sincronización**
- [ ] Reunión semanal de alineación de estándares
- [ ] Documentación compartida de procedimientos
- [ ] Sistema de validación cruzada de datos
- [ ] Protocolo para resolver discrepancias

### **3. Mejora Continua Conjunta**
- [ ] Análisis mensual de calidad de datos integrados
- [ ] Benchmarking de mejores prácticas
- [ ] Capacitación cruzada en herramientas
- [ ] Sistema de sugerencias de mejora

---

## 📊 **MÉTRICAS DE ÉXITO Y SEGUIMIENTO**

### **Para Franz - Objetivos a 30 días**
| Métrica | Actual | Objetivo | Seguimiento |
|---------|--------|----------|-------------|
| Zonas estandarizadas | 70% | 95% | Diaria |
| Coordenadas válidas | 82% | 95% | Diaria |
| Datos completos | 94% | 98% | Semanal |
| Actualizaciones puntuales | Variable | 100% | Semanal |

### **Para Jonathan - Objetivos a 30 días**
| Métrica | Actual | Objetivo | Seguimiento |
|---------|--------|----------|-------------|
| Zonas válidas | 53% | 85% | Diaria |
| Duplicados | 1.2% | <0.5% | Diaria |
| Calidad promedio fuentes | 48% | 75% | Diaria |
- Tasa de éxito scraping: 65% → 90% (Diaria)

---

## 🎯 **PLAN DE ACCIÓN INMEDIATO**

### **Semana 1: Acciones Críticas**
**Franz:**
- [ ] Lunes: Implementar validación de zonas
- [ ] Martes: Estandarizar coordenadas existentes
- [ ] Miércoles: Crear checklist de calidad
- [ ] Jueves: Capacitar equipo en nuevos estándares
- [ ] Viernes: Implementar dashboard de monitoreo

**Jonathan:**
- [ ] Lunes: Iniciar limpieza masiva de zonas corruptas
- [ ] Martes: Reconstruir scraping para fuentes críticas
- [ ] Miércoles: Implementar sistema de deduplicación
- [ ] Jueves: Optimizar selectores por fuente
- [ ] Viernes: Implementar monitoreo de calidad

### **Semana 2: Optimización**
- Reunión de alineación de estándares
- Implementar sistema de integración mejorado
- Testing y validación conjunta
- Documentación de procesos

---

## 📈 **IMPACTO ESPERADO**

### **Impacto en el Sistema Citrino**
- **Precisión de búsqueda:** +40% con datos limpios
- **Recomendaciones:** +25% más precisas
- **Satisfacción usuario:** +30% en confianza del sistema
- **Eficiencia operativa:** +20% en tiempo de procesamiento

### **Impacto Comercial**
- **Conversión de asesores:** +15% con datos confiables
- **Tiempo de cierre:** -20% con información precisa
- **Reputación de marca:** +25% con calidad consistente

---

## 📞 **SOPORTE Y RECURSOS**

### **Para Franz:**
- Manual de estandarización de datos
- Scripts de validación automatizados
- Template de Excel con validaciones
- Capacitación personalizada

### **Para Jonathan:**
- Código base optimizado para scraping
- Sistema de monitoreo de calidad
- Herramientas de depuración
- Documentación de selectores por fuente

---

**Este plan debe ser revisado semanalmente y ajustado según los resultados obtenidos.**

*Elaborado por: Sistema de Auditoría Citrino*
*Revisado por: Equipo Técnico*
*Aprobado por: Dirección de Proyectos*