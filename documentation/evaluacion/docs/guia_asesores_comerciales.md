# Guía Completa para Asesores Comerciales - Citrino

## Introducción

Esta guía está diseñada para maximizar la efectividad de los asesores comerciales de Citrino al trabajar con nuestra base de datos de **76,853 propiedades**. La correcta captación de información y el uso estratégico de nuestros datos permitirá ofrecer recomendaciones altamente personalizadas y aumentar las tasas de conversión.

## 1. Comprensión del Mercado Santa Cruz

### Estadísticas Clave del Mercado
- **Total de propiedades disponibles:** 76,853
- **Rango de precios:** $106,633 - $385,939+ USD
- **Rango de superficies:** 40 - 398+ m²
- **Zonas principales:** Equipetrol, Zona Norte, Centro Histórico, Urubó

### Perfiles de Clientes y Sus Patrones

#### A. Familias con Hijos (35-45% del mercado)
**Características típicas:**
- **Presupuesto:** $180,000 - $250,000 USD
- **Composición:** 2 adultos + 1-3 niños
- **Necesidades críticas:** Seguridad, cercanía a escuelas, espacios familiares
- **Preferencias de zona:** Zona Norte, norte de la ciudad

**Qué preguntar:**
- "¿Qué edad tienen sus hijos y a qué escuela asisten?"
- "¿Es importante para usted tener áreas verdes cercanas?"
- "¿Alguien trabaja desde casa que necesite un espacio tranquilo?"

**Propiedades a recomendar:**
- 3+ habitaciones, 2+ baños
- Zonas con seguridad 24h
- Cercanía a escuelas primarias (Americana, Alemana, La Salle)
- Superficies de 120-200 m²

#### B. Parejas Jóvenes Profesionales (25-30% del mercado)
**Características típicas:**
- **Presupuesto:** $150,000 - $200,000 USD
- **Composición:** 2 adultos, sin hijos planeados a corto plazo
- **Necesidades:** Modernidad, vida urbana, potencial de revalorización
- **Preferencias de zona:** Centro, Equipetrol

**Qué preguntar:**
- "¿Trabajan en una zona específica de la ciudad?"
- "¿Disfrutan de la vida urbana o prefieren tranquilidad?"
- "¿Es importante para ustedes la posibilidad de alquilar en el futuro?"

**Propiedades a recomendar:**
- Departamentos modernos con terraza
- Zonas con buena plusvalía
- Amenidades como gimnasio, piscina
- Superficies de 60-120 m²

#### C. Adultos Mayores (15-20% del mercado)
**Características típicas:**
- **Presupuesto:** $95,000 - $150,000 USD
- **Composición:** 1-2 adultos mayores
- **Necesidades:** Accesibilidad, tranquilidad, servicios médicos cercanos
- **Preferencias de zona:** Equipetrol, zonas tranquilas

**Qué preguntar:**
- "¿Tiene alguna limitación de movilidad que debamos considerar?"
- "¿Es importante tener servicios médicos cercanos?"
- "¿Prefiere un piso bajo o hay ascensor?"

**Propiedades a recomendar:**
- Sin escaleras o con ascensor
- Zonas con buena infraestructura médica
- Superficies manejables (60-100 m²)
- Seguridad 24h

#### D. Inversionistas (10-15% del mercado)
**Características típicas:**
- **Presupuesto:** Variable, enfocado en ROI
- **Necesidades:** Potencial de alquiler, revalorización, liquidez
- **Preferencias:** Zonas con alta demanda estudiantil o profesional

**Qué preguntar:**
- "¿Busca alquiler a estudiantes, familias o profesionales?"
- "¿Qué retorno de inversión espera anualmente?"
- "¿Prefiere liquidez o apreciación a largo plazo?"

**Propiedades a recomendar:**
- Cerca de universidades (UAGRM, UPSA)
- Zonas con alta demanda de alquiler
- Propiedades con potencial de mejora

## 2. Proceso de Captación de Información ESENCIAL

### Fase 1: Contacto Inicial (Primeros 5 minutos)
**Objetivo:** Identificar el tipo de perfil y nivel de urgencia

**Preguntas clave:**
1. "¿Qué tipo de propiedad está buscando?"
2. "¿En qué zona o áreas le gustaría vivir?"
3. "¿Tiene un rango de presupuesto en mente?"
4. "¿Cuándo necesita estar en la nueva propiedad?"

**Red flags a identificar:**
- Presupuesto muy por debajo del mercado
- Expectativas irreales (ej: casa en Equipetrol con $100k)
- Falta de claridad en necesidades básicas

### Fase 2: Profundización (Siguientes 15-20 minutos)
**Objetivo:** Capturar información detallada para recomendaciones precisas

**Composición familiar (CRÍTICO):**
- "Cuénteme sobre su familia, ¿cuántas personas vivirán en la propiedad?"
- "¿Tiene hijos? ¿Qué edad tienen? ¿Asisten a alguna escuela actualmente?"
- "¿Hay adultos mayores o personas con necesidades especiales?"
- "¿Tienen mascotas? ¿Qué tipo y qué tamaño?"

**Necesidades específicas:**
- "¿Alguien trabaja desde casa que necesite un espacio tranquilo?"
- "¿Es importante tener garaje o estacionamiento?"
- "¿Qué actividades hacen regularmente? (ej: deportes, vida social, tranquilo)"
- "¿Hay algún servicio que sea indispensable cerca? (escuelas, hospitales, trabajo)"

**Preferencias de estilo de vida:**
- "¿Prefiere una zona más tranquila o con vida urbana?"
- "¿Disfruta de tener áreas comunes o prefiere privacidad?"
- "¿Es importante para usted tener amenidades como piscina, gimnasio?"

### Fase 3: Detalles Técnicos
**Objetivo:** Capturar información para filtrar propiedades

**Características no negociables:**
- "¿Cuál es el mínimo de habitaciones que necesita?"
- "¿Cuántos baños completos son esenciales?"
- "¿Hay alguna característica que sea imprescindible? (ej: garaje, ascensor)"
- "¿Algún servicio que deba estar a menos de X distancia?"

**Presupuesto real:**
- "¿Cuál es el presupuesto máximo que puede considerar?"
- "¿Tiene financiamiento pre-aprobado? ¿Por cuánto?"
- "¿Está abierto a considerar propiedades que estén un poco sobre presupuesto si son excelentes oportunidades?"

## 3. Uso Estratégico de la Base de Datos Citrino

### A. Filtrado Efectivo por Perfil

#### Para Familias con Hijos:
```python
# Filtros recomendados
filtros = {
    'precio_min': 180000,
    'precio_max': 250000,
    'habitaciones_min': 3,
    'banos_min': 2,
    'tiene_garaje': True,
    'zona': ['Zona Norte', 'Norte', 'Equipetrol'],
    'necesidades_especificas': ['escuelas', 'seguridad', 'areas_verdes']
}
```

#### Para Parejas Jóvenes:
```python
filtros = {
    'precio_min': 150000,
    'precio_max': 200000,
    'habitaciones_min': 2,
    'banos_min': 1,
    'tipo_propiedad': 'departamento',
    'zona': ['Centro', 'Equipetrol'],
    'caracteristicas_deseadas': ['terraza', 'moderno', 'gimnasio']
}
```

#### Para Adultos Mayores:
```python
filtros = {
    'precio_min': 95000,
    'precio_max': 150000,
    'habitaciones_min': 1,
    'banos_min': 1,
    'zona': ['Equipetrol', 'Urubó'],
    'caracteristicas_esenciales': ['ascensor', 'seguridad_24h', 'sin_escaleras']
}
```

### B. Análisis de Plusvalía por Zona

**Zonas con mayor plusvalía:**
1. **Equipetrol**: +8-12% anual
2. **Zona Norte**: +6-10% anual
3. **Urubó**: +5-8% anual
4. **Centro**: +3-6% anual

**Argumentos de venta por zona:**
- "En Equipetrol no solo está comprando una casa, está invirtiendo en una zona que se revalúa un 10% anual"
- "La Zona Norte está en pleno desarrollo, con nuevas infraestructuras que aumentarán el valor de su propiedad"

### C. Uso del Sistema de Recomendación

**El sistema analiza:**
- Compatibilidad de presupuesto (30%)
- Composición familiar vs características de propiedad (25%)
- Servicios cercanos necesarios (20%)
- Demografía de la zona (15%)
- Preferencias personales (10%)

**Cómo presentar recomendaciones:**
- "Basado en su perfil familiar, estas 3 propiedades tienen un 95% de compatibilidad con sus necesidades"
- "El sistema priorizó estas opciones porque están cerca de las escuelas que mencionó y dentro de su presupuesto"

## 4. Técnicas de Cierre Basadas en Datos

### A. Argumentos de Valor Cuantificables

**Por m² comparativo:**
- "Esta propiedad está a $1,200/m² mientras que el promedio en la zona es de $1,400/m²"
- "Está obteniendo 20m² extras por el mismo precio que otras opciones"

**Inversión en educación:**
- "Vivir aquí le ahorra 30 minutos diarios de tráfico a la escuela Americana"
- "La cercanía a 5 universidades aumenta el potencial de alquiler en un 25%"

**Retorno de inversión:**
- "Con el alquiler promedio de esta zona, su retorno anual sería del 6%"
- "La plusvalía histórica muestra que propiedades similares han aumentado 40% en 5 años"

### B. Manejo de Objeciones con Datos

**"Es muy caro":**
- "Comparado con otras propiedades similares en la zona, está 15% abajo del promedio"
- "El valor por m² es de $X, mientras que en [zona similar] es de $Y"

**"No me convence la ubicación":**
- "Esta zona tiene una demanda del 85% según nuestros datos"
- "Hay 5 escuelas y 3 hospitales a menos de 10 minutos"

**"Prefiere esperar":**
- "Las propiedades en esta zona han aumentado 8% en el último año"
- "Hay solo 3 propiedades que cumplen sus criterios actualmente"

## 5. Métricas y Seguimiento

### KPIs para Asesores

**Métricas de efectividad:**
- **Tasa de conversión:** % de prospectos que compran
- **Tiempo promedio de cierre:** Días desde primer contacto a cierre
- **Satisfacción del cliente:** Calificación post-venta
- **Precisión de recomendaciones:** % de propiedades mostradas que coinciden con necesidades reales

**Metas recomendadas:**
- Tasa de conversión mínima: 25%
- Tiempo promedio de cierre: 45-60 días
- Satisfacción del cliente: 4.5/5 mínimo
- Precisión de recomendaciones: 80%+

### Sistema de Seguimiento

**Clasificación de prospectos:**
- **Caliente:** Contacto diario, presupuesto definido, urgencia alta
- **Tibio:** Contacto semanal, explorando opciones
- **Frío:** Contacto quincenal/mensual, solo informándose

**Frecuencia de contacto recomendada:**
- **Prospectos calientes:** 2-3 veces por semana
- **Prospectos tibios:** 1 vez por semana
- **Prospectos fríos:** 2 veces por mes

## 6. Mejores Prácticas

### A. Documentación Rigurosa
- Llenar completamente la plantilla de captación para cada prospecto
- Registrar todas las interacciones y preferencias mencionadas
- Actualizar el perfil del cliente según cambien sus necesidades

### B. Uso del Sistema de Recomendación
- Siempre usar el sistema antes de mostrar propiedades
- Validar las recomendaciones manualmente
- Explicar al cliente el porqué de las recomendaciones

### C. Conocimiento Continuo del Mercado
- Revisar semanalmente nuevas propiedades en zonas clave
- Mantenerse actualizado sobre precios y tendencias
- Compartir insights con el equipo de asesores

### D. Ética Profesional
- Nunca recomendar propiedades que no cumplan los criterios básicos
- Ser transparente sobre las limitaciones de la base de datos
- Priorizar siempre las necesidades del cliente sobre la comisión

## 7. Herramientas y Recursos

### A. Sistema de Recomendación Citrino
- API disponible para integración con herramientas de gestión
- Capacidad de procesar 76,853 propiedades en segundos
- Análisis de compatibilidad con múltiples factores

### B. Base de Datos de Servicios
- 5 escuelas primarias principales con ubicaciones
- 5 universidades con información de demanda
- 4 hospitales principales
- 8 supermercados y centros comerciales

### C. Material de Apoyo
- Plantillas de captación estandarizadas
- Guías por tipo de cliente
- Presentaciones comparativas por zona
- Análisis de mercado actualizados

---

**Nota:** Esta guía debe ser actualizada mensualmente con los últimos datos del mercado y feedback del equipo de asesores.