#  Arquitectura Actual - Sistema Basado en JSON

**Versión**: 1.8.5 (actual)
**Fecha**: 2025-10-14
**Estado**: En producción (siendo migrado a PostgreSQL)

---

##  Resumen del Sistema Actual

### Arquitectura Centralizada en JSON
El sistema Citrino actualmente utiliza una arquitectura basada en archivos JSON centralizados para el almacenamiento y procesamiento de datos inmobiliarios.

### Componentes Principales
- **Base de datos JSON**: Archivos centrales con propiedades y servicios
- **Motores de recomendación**: Algoritmos Python con procesamiento en memoria
- **API REST**: Flask sirviendo datos desde JSON
- **Geolocalización**: Haversine para cálculos de distancias

---

##  Estructura de Datos Actual

### Archivos Principales
```
data/
 base_datos_relevamiento.json              # 1,588 propiedades
 base_datos_relevamiento_integrado.json    # Dataset integrado
 guia_urbana_municipal_completa.json      # 4,777 servicios urbanos
```

### Esquema de Propiedades (JSON)
```json
{
  "propiedades": [
    {
      "id": "prop_123",
      "titulo": "Departamento en venta en Equipetrol",
      "tipo_propiedad": "departamento",
      "precio": 250000,
      "moneda": "USD",
      "direccion": "Calle Falsa 123",
      "zona": "Equipetrol",
      "unidad_vecinal": "UV 12",
      "manzana": "M3",

      "coordenadas": {
        "latitud": -17.7833,
        "longitud": -63.1821
      },

      "caracteristicas": {
        "superficie_m2": 120,
        "habitaciones": 3,
        "banos": 2,
        "garaje": 1,
        "amoblado": true
      },

      "agente": "Nombre del Agente",
      "telefono": "+591-12345678",
      "correo": "agente@inmobiliaria.com",

      "metadatos": {
        "fecha_scraping": "2025.01.15",
        "codigo_proveedor": "01",
        "url": "https://ejemplo.com/prop/123",
        "activo": true
      }
    }
  ]
}
```

### Esquema de Servicios Urbanos (JSON)
```json
{
  "servicios_consolidados": [
    {
      "id": "serv_456",
      "nombre": "Hospital Japonés",
      "tipo": "salud",
      "subtipo": "hospital público",
      "direccion": "Av. Brasil 1234",
      "coordenadas": {
        "latitud": -17.7950,
        "longitud": -63.1880
      },
      "fuente": "guia_urbana_municipal"
    }
  ]
}
```

---

##  Flujo de Procesamiento Actual

### 1. Carga de Datos
```python
# API Server carga JSON al iniciar
with open('data/base_datos_relevamiento.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    propiedades = data.get('propiedades', [])

# Carga en memoria para motores de recomendación
motor_recomendacion.cargar_propiedades(propiedades)
```

### 2. Consultas Geoespaciales
```python
# Búsqueda actual (O(n×m) - ineficiente)
def buscar_propiedades_cercanas(zona, radio_km):
    resultados = []
    for propiedad in propiedades:
        if propiedad.zona == zona:
            for servicio in servicios_urbanos:
                distancia = haversine(
                    propiedad.coordenadas,
                    servicio.coordenadas
                )
                if distancia <= radio_km:
                    resultados.append(propiedad)
                    break
    return resultados
```

### 3. Motor de Recomendación
```python
# Procesamiento en memoria
class RecommendationEngine:
    def __init__(self):
        self.propiedades = []  # Cargadas desde JSON
        self.pesos = {
            'presupuesto': 0.25,
            'ubicacion': 0.35,
            'servicios': 0.30,
            'caracteristicas': 0.10
        }

    def generar_recomendaciones(self, perfil):
        # Procesamiento O(n) sobre todas las propiedades
        # Cálculo de distancias Haversine para cada consulta
        pass
```

---

##  Limitaciones Críticas Identificadas

### Problemas de Rendimiento
1. **Complejidad Algorítmica**: O(n×m) = 7,585,876 cálculos por búsqueda
   - 1,588 propiedades × 4,777 servicios
   - Recálculo completo por cada consulta

2. **Tiempo de Respuesta**: Segundos por consulta geoespacial
   - Búsqueda en Equipetrol: 2-5 segundos
   - Búsqueda con filtros múltiples: 5-10 segundos

3. **Uso de Memoria**: Todo el dataset cargado en memoria
   - ~50MB en RAM para propiedades
   - ~10MB en RAM para servicios
   - Sin caché persistente

### Problemas de Escalabilidad
1. **Sin Concurrencia**: Un solo usuario a la vez
   - Bloqueos durante escrituras
   - Sin transacciones ACID

2. **Duplicación de Datos**: Agentes repetidos
   - Mismo agente en múltiples propiedades
   - Sin normalización relacional

3. **Actualizaciones Complejas**: Requiere reescribir JSON completo
   - Sin actualizaciones incrementales
   - Riesgo de corrupción de datos

### Problemas de Mantenimiento
1. **Integridad de Datos**: Sin validación automática
   - Coordenadas inválidas pasan desapercibidas
   - Datos inconsistentes sin detección

2. **Version Control**: Dificultad para tracking de cambios
   - Todo el dataset en un archivo
   - Sin historial de cambios individuales

---

##  Componentes del Sistema Actual

### API Server (`api/server.py`)
- **Framework**: Flask 2.3.3
- **Endpoints**: 6 endpoints REST
- **Carga**: JSON → memoria al iniciar
- **Limitación**: Single-thread processing

### Motores de Recomendación
1. **Motor Básico** (`src/recommendation_engine.py`)
   - Filtrado simple por criterios
   - Sin cálculos geoespaciales avanzados

2. **Motor Mejorado** (`src/recommendation_engine_postgis.py`)
   - Geolocalización con Haversine
   - Verificación de servicios cercanos
   - Cache en memoria (limitada)

### Sistema LLM
- **Proveedor Primario**: Z.AI GLM-4.6
- **Fallback**: OpenRouter Qwen2.5 72B
- **Uso**: Extracción de datos del Proveedor 02
- **Performance**: 80% sin necesidad de LLM

---

##  Métricas Actuales del Sistema

### Rendimiento
- **Carga inicial**: 3-5 segundos
- **Consulta simple**: 0.5-1 segundo
- **Consulta geoespacial**: 2-10 segundos
- **Búsqueda compleja**: 10-30 segundos

### Datos
- **Propiedades**: 1,588 registros
- **Servicios Urbanos**: 4,777 registros
- **Agentes Únicos**: ~200 (estimado)
- **Zonas Cobiertas**: 15+ zonas de Santa Cruz

### Uso
- **Usuarios Concurrentes**: 1 (limitación del sistema)
- **Requests por Día**: ~100 (estimado)
- **Tasa de Error**: <5% (principalmente timeouts)

---

##  Procesos de Datos Actuales

### ETL Principal
```python
# scripts/etl/build_relevamiento_dataset.py
def procesar_datos():
    # 1. Leer archivos Excel (múltiples proveedores)
    # 2. Limpiar y normalizar datos
    # 3. Extraer características con LLM (Proveedor 02)
    # 4. Generar JSON consolidado
    # 5. Guardar en data/base_datos_relevamiento.json
```

### Sistema Híbrido de Extracción
- **RegEx**: 80% de datos extraídos automáticamente
- **LLM**: 20% datos complejos (descripciones Proveedor 02)
- **Cache**: Reducción 90% consumo tokens LLM
- **Fallback**: Automático a OpenRouter

---

##  Problemas Críticos que Justifican Migración

### 1. Performance Inaceptable
```
Consulta actual (Equipetrol + colegio + hospital):
- Tiempo: 5-10 segundos
- Cálculos: 7,585,876 por búsqueda
- Experiencia usuario: Pobre

Consulta PostgreSQL esperada:
- Tiempo: <100 milisegundos
- Cálculos: Índice espacial O(log n)
- Experiencia usuario: Excelente
```

### 2. Límite de Crecimiento
```
Escenario: 10x más propiedades (15,880)
- Tiempo actual: 50-100 segundos por consulta
- Memoria requerida: 500MB+
- Sistema: Inutilizable

PostgreSQL con 15,880 propiedades:
- Tiempo: <100ms (índices escalan)
- Memoria: Similar (base de datos gestiona)
- Sistema: Totalmente usable
```

### 3. Riesgo de Pérdida de Datos
```
Actual:
- JSON en disco (sin transacciones)
- Escritura concurrente = corrupción
- Sin backups automáticos

PostgreSQL:
- Transacciones ACID
- Concurrencia segura
- Backups automatizados
- Point-in-time recovery
```

---

##  Lista de Problemas Específicos

### Críticos (Bloquean desarrollo)
1. **Tiempo de respuesta**: >5 segundos para consultas geoespaciales
2. **Sin concurrencia**: Un solo usuario a la vez
3. **Integridad**: Riesgo de corrupción en actualizaciones

### Serios (Afectan)
1. **Memory leaks**: Carga incremental en memoria
2. **No persistencia**: Se pierden cachés al reiniciar
3. **Difícil debugging**: Datos en JSON vs código

### Menores (Inconvenientes operativos)
1. **Deployment**: Requiere copiar archivos JSON
2. **Testing**: Dificil crear datasets de prueba
3. **Monitoring**: Sin métricas de rendimiento detalladas

---

##  Justificación de Migración

### ROI de Migración a PostgreSQL
- **Inversión**: 2-3 días desarrollo
- **Retorno**: Sistema 10x más rápido y escalables
- **Riesgo**: Bajo (rollback automático disponible)
- **Impacto**: Transforma experiencia de usuario

### Beneficios Cuantificables
1. **Performance**: 50-100x más rápido
2. **Scalability**: Soporte 10x más datos
3. **Concurrency**: Múltiples usuarios simultáneos
4. **Reliability**: Transacciones ACID

### Costos de No Migrar
1. **Experiencia Usuario**: Continúa siendo pobre
2. **Límite Crecimiento**: No se puede escalar el negocio
3. **Riesgo Datos**: Corrupción potencial
4. **Competitividad**: Desventaja tecnológica

---

##  Estado Actual de Preparación

###  Listo para Migración
- **Documentación**: Completa y detallada
- **Scripts ETL**: Implementados y probados
- **DDL PostgreSQL**: Definido y optimizado
- **Plan Rollback**: Probado y confiable

###  Próximos Pasos
1. **Commit 4**: Completar documentación arquitectura (actual)
2. **Commit 5**: Crear estructura para nueva arquitectura
3. **Implementación**: Ejecutar migración completa

---

*Última revisión: 2025-10-14*
*Estado: Documentado y listo para migración*
*Prioridad: Alta (impacto directo en experiencia de usuario)*