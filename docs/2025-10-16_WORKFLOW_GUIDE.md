# WORKFLOW - Guía de Desarrollo y Procesos

##  Índice

1. [Principios de Desarrollo](#principios-de-desarrollo)
2. [Workflow de Commits](#workflow-de-commits)
3. [Lecciones Aprendidas](#lecciones-aprendidas)
4. [Procesos de Validación](#procesos-de-validación)
5. [Debugging y Solución de Problemas](#debugging-y-solución-de-problemas)

---

##  Principios de Desarrollo

###  Reglas Fundamentales

1. **VALIDACIÓN CRÍTICA**: Nunca declarar éxito sin validar funcionalidad core
2. **COORDENADAS PRIMERO**: Las coordenadas son el CORE del sistema geoespacial
3. **TESTING REAL**: Validar con datos reales, no simulaciones
4. **DOCUMENTACIÓN INMEDIATA**: Documentar bugs y soluciones al momento
5. **NO SUPONER**: Siempre verificar suposiciones con datos reales

---

##  Workflow de Commits

### Commit Messages Estándar

```bash
# Formato preferido
feat: añadir funcionalidad X
fix: corregir bug crítico en Y
docs: actualizar documentación de Z
refactor: mejorar estructura de módulo
test: añadir pruebas para componente W
```

### Proceso de Commit

1. **Cambios Locales** → **Testing** → **Commit**
2. **Testing** → **Push** → **Validación en Producción**

---

##  Lecciones Aprendidas (v2.2.1)

### Lección #1: Nunca Confundir Estadísticas con Realidad

** ERROR:** Declarar "sistema listo" con 0 coordenadas válidas
** CORRECCIÓN:** Validar funcionalidad core antes de declarar éxito

```python
# Error: Confundir métricas con funcionalidad
print("Coordenadas válidas: 0")  # Bug en estadísticas
print("Sistema listo")         # ERROR: No es verdad

# Correcto: Validar funcionalidad real
coordenadas_reales = contar_coordenadas_validas(servicios)
print(f"Coordenadas válidas: {coordenadas_reales}")
if coordenadas_reales > 0:
    print("Sistema listo para pruebas")
```

### Lección #2: Debugging Sistemático vs Adivinanza

** ERROR:** Cambiar código sin entender el problema real
** CORRECCIÓN:** Debugging paso a paso con datos reales

```python
# Proceso correcto de debugging:
# 1. Extraer muestras reales
muestras = extraer_coordenadas_reales(excel)
# 2. Testear parser en aislamiento
parser_result = test_parser_actual(muestras)
# 3. Identificar punto exacto de fallo
punto_fallo = encontrar_bug_en_pipeline()
# 4. Corregir específicamente el bug
corregir_bug_especifico(punto_fallo)
```

### Lección #3: El Problema Siempre Está en los Datos

** ERROR:** Asumir que el parser está mal cuando los datos sí existen
** CORRECCIÓN:** Verificar que los datos estén llegando correctamente

```python
# Error común: Cambiar parser sin verificar datos
print("Parser no funciona -> Cambiar regex")  # ERROR

# Correcto: Verificar si los datos llegan primero
print("Verificando que los datos lleguen...")
datos_llegan = verificar_datos_en_pipeline()
if not datos_llegan:
    print("Problema en extracción, no en parser")
else:
    print("Datos llegan, problema en parser")
```

### Lección #4: Las Estadísticas Deben Reflejar Realidad

** ERROR:** Estadísticas inconsistentes con datos reales
** CORRECCIÓN:** Sincronizar estadísticas con procesamiento real

```python
# Error en el código original:
if servicio.get('coordenadas_validadas', False):  # ERROR: Campo no existe
    estadisticas['coordenadas_validas'] += 1

# Corrección:
if servicio.get('metadatos', {}).get('coordenadas_validadas', False):
    estadisticas['coordenadas_validas'] += 1
```

### Lección #5: Validación Extrema de Funcionalidad Core

** ERROR:** Aceptar 99% como "bueno suficiente" para coordenadas
** CORRECCIÓN:** Investigar hasta el 100% de éxito posible

```python
# Proceso de validación completa:
# 1. Test con muestra pequeña
muestra_validacion = test_muestra_aleatoria(servicios, n=50)
# 2. Verificar cada paso
verificar_pasos_completos(muestra_validacion)
# 3. Escalar a producción
validar_producción_completa(todos_los_servicios)
# 4. Confirmar integración con otros componentes
test_integracion_motor_recomendacion()
```

### Lección #6: Validación Humana es Obligatoria (v2.2.2)

** ERROR:** Procesar directamente de raw a producción sin revisión intermedia
** CORRECCIÓN:** Siempre generar archivos intermedios para validación humana

```python
# Error: Procesamiento directo
datos_raw = leer_excel("archivo.xlsx")
datos_procesados = procesar_y_guardar_en_producción(datos_raw)

# Correcto: Pipeline con validación humana
datos_raw = leer_excel("archivo.xlsx")
datos_intermedios = procesar_a_intermedios(datos_raw)
# → REVISIÓN HUMANA AQUÍ ←
if aprobado_por_equipo_citrino(datos_intermedios):
    datos_produccion = mover_a_producción(datos_intermedios)
```

### Lección #7: No Celebrar Métricas Aisladas

** ERROR:** Celebrar 98.9% coordenadas válidas sin validar que los datos tengan sentido
** CORRECCIÓN:** Validar integridad completa de datos, no solo métricas aisladas

```python
# Error: Validar solo coordenadas
coordenadas_validas = 98.9%
print("Excelente: 98.9% coordenadas!")

# Correcto: Validación completa de datos
coordenadas_validas = 98.9%
nombres_especificos = 99.8%
precios_realistas = 100%
estructura_correcta = 100%
datos_tienen_sentido = validar_integridad_completa()
```

---

##  Procesos de Validación

### Checklist de Validación de Coordenadas

```python
def validar_coordenadas_completas():
    """Checklist completa para validación de coordenadas"""

    # 1. ¿Hay datos en el Excel?
    datos_excel = verificar_excel_contiene_coordenadas()

    # 2. ¿El parser extrae correctamente?
    parser_funciona = test_parser_con_muestras_reales()

    # 3. ¿Las estadísticas reflejan realidad?
    stats_correctas = verificar_estadisticas_vs_reales()

    # 4. ¿El motor de recomendación usa coordenadas?
    motor_usa_coords = test_motor_recomendacion_con_coords()

    # 5. ¿Los índices espaciales funcionan?
    indices_funcionan = test_indices_espaciales()

    return all([datos_excel, parser_funciona, stats_correctas,
                motor_usa_coords, indices_funcionan])
```

### Validación de Integración

```python
def test_integracion_completa():
    """Validación de integración completa del sistema"""

    # ETL
    etl = GuiaUrbanaETL()
    servicios = etl.procesar_guia_urbana()
    assert len(servicios) > 4000, "ETL debe procesar >4000 servicios"

    # Motor de Recomendación
    motor = RecommendationEngineMejorado()
    motor.cargar_guias_urbanas()
    assert len(motor.guias_urbanas) > 4000, "Motor debe cargar servicios"

    # Coordenadas Funcionales
    coords_validas = contar_servicios_con_coordenadas(motor.guias_urbanas)
    assert coords_validas > 4000, "Debe haber >4000 coordenadas válidas"

    return True
```

---

##  Debugging y Solución de Problemas

### Metodología de Debugging Estructurado

1. **Reproducir el Problema**
   ```python
   # Crear caso de prueba mínimo que reproduzca el error
   problema_reproducido = reproducir_error_original()
   ```

2. **Aislar el Componente**
   ```python
   # Testear cada componente individualmente
   etl_funciona = test_etl_aislado()
   parser_funciona = test_parser_aislado()
   validacion_funciona = test_validacion_aislada()
   ```

3. **Identificar el Bug Exacto**
   ```python
   # Debug línea por línea si es necesario
   debug_linea_por_linea(pipeline_completo)
   ```

4. **Corregir y Validar**
   ```python
   # Corregir específicamente
   corregir_bug_identificado()

   # Validar corrección
   assert test_reproduccion_error_original() == False
   ```

### Herramientas de Debugging Desarrolladas

```python
# scripts/debug/debug_coordenadas_critico.py
def debug_coordenadas_completas():
    """Debug completo del pipeline de coordenadas"""

    # 1. Extraer muestras reales
    muestras = extraer_muestras_reales()

    # 2. Testear parser actual
    testear_parser_actual(muestras)

    # 3. Testear variaciones
    testear_variaciones_regex(muestras)

    # 4. Analizar rangos
    analizar_rangos_validacion(muestras)
```

---

##  Estándares de Calidad

### Código de Calidad

```python
#  Buen ejemplo: Validación explícita
def procesar_coordenadas(coordenadas_str):
    if not coordenadas_str:
        return None

    try:
        # Procesamiento con validación
        coords = parsear_coordenadas(coordenadas_str)
        if validar_coordenadas_santa_cruz(coords):
            return coords
        else:
            logger.warning(f"Coordenadas fuera de rango: {coords}")
            return None
    except Exception as e:
        logger.error(f"Error procesando coordenadas: {e}")
        return None

#  Mal ejemplo: Sin validación de errores
def procesar_coordenadas_malo(coordenadas_str):
    coords = parsear_coordenadas(coordenadas_str)  # Puede fallar
    return coords  # Retorna None si falla, sin saber por qué
```

### Estándares de Testing

```python
#  Testing con datos reales
def test_etl_con_datos_reales():
    """Test ETL con datos reales del Excel"""
    etl = GuiaUrbanaETL()
    servicios = etl.procesar_guia_urbana()

    # Validar con expectativas reales
    assert len(servicios) >= 4900, "Debe procesar >=4900 servicios"

    # Validar coordenadas
    coords_validas = sum(1 for s in servicios
                        if s.get('metadatos', {}).get('coordenadas_validadas'))
    assert coords_validas >= 4800, "Debe tener >=4800 coordenadas válidas"
```

---

##  Proceso de Entrega

### Pre-Commit Checklist

- [ ] **Funcionalidad Core Validada**: Coordenadas funcionando
- [ ] **Tests Pasando**: Todos los tests automatizados
- [ ] **Documentación Actualizada**: CHANGELOG.md actualizado
- [ ] **Sin Breaking Changes**: Backward compatibility mantenido
- [ ] **Performance Aceptable**: No degradación significativa

### Post-Commit Validación

- [ ] **Producción Funciona**: Deploy exitoso en producción
- [ ] **Métricas Estables**: No regresiones en rendimiento
- [ ] **Usuarios Notificados**: Comunicación de cambios relevantes
- [ ] **Monitoreo Activo**: Sistema siendo monitoreado

---

##  Plantillas Útiles

### Plantilla de Commit Message para Bug Crítico

```bash
fix: corregir bug crítico de coordenadas en ETL guía urbana

PROBLEMA:
- ETL reportaba 0 coordenadas válidas cuando tenía 4,899
- Bug en método extraer_servicios_urbanos, líneas 153 y 163
- Sistema declarado como "funcional" sin validar coordenadas

SOLUCIÓN:
- Línea 153: Agregar self.servicios_procesados.append(servicio)
- Línea 163: Usar servicio.get('metadatos', {}).get('coordenadas_validadas', False)
- Validación completa con 4,899 coordenadas válidas (99.2% éxito)

IMPACTO:
- Sistema 100% funcional con coordenadas reales
- Motor de recomendación integrado con datos geoespaciales
- PostGIS-ready con coordenadas validadas

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

##  Mejora Continua

### Próximos Pasos

1. **Automatización de Validación**: Scripts automáticos para testing
2. **Integración Continua**: CI/CD pipeline con validaciones
3. **Monitoring en Producción**: Alertas para anomalías en coordenadas
4. **Documentación Viva**: Documentación que se actualiza automáticamente

---

**Última Actualización:** 2025-10-15
**Versión:** 2.2.1
**Mantenido por:** Equipo Citrino