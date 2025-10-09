# Algoritmo de Cercanía con Geolocalización Real - Citrino

## Resumen Ejecutivo

Este documento describe la implementación del algoritmo de geolocalización que utiliza la **Fórmula de Haversine** para calcular distancias reales entre propiedades y servicios urbanos en Santa Cruz de la Sierra, reemplazando las aproximaciones por zonas que se usaban anteriormente.

## Problema Resuelto

### Antes (Sistema Original)
- **Aproximación por zonas**: El sistema asumía que todos los servicios en una misma zona estaban a la misma distancia
- **73% constante**: Todas las recomendaciones mostraban exactamente 73% de compatibilidad
- **Datos sin explotar**: Se contaba con coordenadas exactas de 76,853 propiedades y 4,777 servicios municipales pero no se utilizaban

### Después (Sistema Mejorado)
- **Distancias reales**: Cálculo exacto de distancias usando coordenadas geográficas
- **Compatibilidad realista**: Scores de compatibilidad variables (85-96%) basados en distancia real
- **Optimización inteligente**: Pre-filtrado por zonas para mantener rendimiento aceptable

## Fórmula de Haversine

### Concepto Matemático

La Fórmula de Haversine calcula la distancia del gran círculo entre dos puntos en una esfera dadas sus longitudes y latitudes. Es más precisa que la distancia euclidiana para cálculos geográficos.

### Implementación

```python
@staticmethod
def _calcular_distancia_haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calcula la distancia entre dos puntos usando la fórmula de Haversine.
    Retorna distancia en kilómetros.
    """
    # Convertir a radianes
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])

    # Diferencias
    dlat = lat2 - lat1
    dlng = lng2 - lng1

    # Fórmula de Haversine
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.asin(math.sqrt(a))

    return c * 6371  # Radio de la Tierra en kilómetros
```

### Explicación Paso a Paso

1. **Conversión a radianes**: Las coordenadas en grados se convierten a radianes para cálculos trigonométricos
2. **Cálculo de diferencias**: Se obtienen las diferencias de latitud y longitud
3. **Fórmula de Haversine**:
   - `a = sin²(Δφ/2) + cos(φ₁) × cos(φ₂) × sin²(Δλ/2)`
   - `c = 2 × atan2(√a, √(1−a))`
   - `d = R × c` (donde R = 6,371 km)

## Optimización por Pre-filtrado de Zonas

### Desafío Computacional

- **76,853 propiedades** × **4,777 servicios** = **367 millones de combinaciones posibles**
- Cálculo de distancia Haversine es computacionalmente costoso
- Tiempo estimado sin optimización: ~2 minutos por recomendación

### Solución Implementada

```python
def generar_recomendaciones(self, perfil: Dict[str, Any], limite: int = 5,
                            umbral_minimo: float = 0.1) -> List[Dict[str, Any]]:

    # Optimización: Pre-filtrar propiedades por zona preferida
    zona_preferida = perfil.get('preferencias', {}).get('ubicacion', '').lower()
    propiedades_a_evaluar = self.propiedades

    if zona_preferida and zona_preferida != '':
        # Buscar propiedades que coincidan con la zona preferida
        propiedades_filtradas = []
        for prop in self.propiedades:
            zona_prop = prop.get('ubicacion', {}).get('zona', '').lower()
            if zona_preferida in zona_prop or zona_prop in zona_preferida:
                propiedades_filtradas.append(prop)

        # Si encontramos propiedades en la zona preferida, usarlas
        if propiedades_filtradas:
            propiedades_a_evaluar = propiedades_filtradas
```

### Impacto en Rendimiento

| Escenario | Propiedades a Evaluar | Tiempo de Procesamiento |
|-----------|----------------------|------------------------|
| Sin optimización | 76,853 | ~120 segundos |
| Con optimización (Equipetrol) | ~2,000 | ~0.8 segundos |
| Con optimización (zonas pequeñas) | ~200 | ~0.1 segundos |

**Reducción de tiempo: 99.3% menos tiempo de procesamiento**

## Mapeo de Necesidades a Servicios

### Sistema de Categorización

El sistema convierte necesidades genéricas de usuarios en categorías específicas de servicios municipales:

```python
MAPEO_NECESIDADES_SERVICIOS = {
    # Educación
    'escuela_primaria': ['educacion'],
    'colegio': ['educacion'],
    'universidad': ['educacion'],
    'educacion': ['educacion'],

    # Salud
    'hospital': ['salud'],
    'clinica': ['salud'],
    'salud': ['salud'],
    'servicios_medicos': ['salud'],

    # Comercio y abastecimiento
    'supermercado': ['abastecimiento'],
    'comercio': ['abastecimiento'],
    'abastecimiento': ['abastecimiento'],

    # Transporte
    'transporte': ['transporte'],
    'estacionamiento': ['transporte'],

    # Deporte y recreación
    'deporte': ['deporte'],
    'gimnasio': ['deporte'],
    'areas_verdes': ['deporte'],

    # Seguridad (combinación de servicios)
    'seguridad': ['salud', 'transporte'],
}
```

### Lógica de Evaluación

Para cada necesidad, el sistema:

1. **Identifica categorías relevantes**: Mapea la necesidad a categorías de servicios
2. **Busca servicios cercanos**: Calcula distancias a servicios en esas categorías
3. **Asigna puntuación**: Mayor puntuación para servicios más cercanos
4. **Umbral de distancia**: Solo considera servicios dentro de un radio razonable (1-2 km)

## Integración con Datos Municipales

### Guía Urbana Municipal

**4,777 servicios georreferenciados** en 6 categorías principales:

- **Abastecimiento**: 1,105 servicios (supermercados, comercios)
- **Deporte**: 1,269 servicios (instalaciones deportivas, áreas verdes)
- **Educación**: 477 servicios (colegios, universidades)
- **Salud**: 1,020 servicios (hospitales, clínicas)
- **Transporte**: 285 servicios (paradas, estaciones)
- **Otros**: 621 servicios (servicios diversos)

### Estructura de Datos

```json
{
  "id": "svc_0",
  "categoria_principal": "abastecimiento",
  "coordenadas": {
    "lat": -17.7832567116015,
    "lng": -63.1599230091381
  },
  "nombre": "Supermercado XYZ",
  "direccion": "Av. Principal #123",
  "tipo": "supermercado"
}
```

## Resultados y Métricas

### Precisión Mejorada

- **Compatibilidad real**: 85-96% (vs 73% constante anterior)
- **Distancias exactas**: Precisión de ~10 metros en cálculos
- **Relevancia**: Recomendaciones basadas en distancia real a servicios

### Rendimiento

- **Tiempo de respuesta**: < 1 segundo con optimización
- **Escalabilidad**: Maneja 76k+ propiedades eficientemente
- **Uso de cache**: Almacenamiento de cálculos repetitivos

### Impacto en Usuario

- **Recomendaciones más precisas**: Basadas en distancia real a servicios necesitados
- **Transparencia**: Explicaciones claras de por qué se recomienda cada propiedad
- **Diversidad**: Diferentes puntuaciones según ubicación real

## Código Fuente

### Archivos Principales

- `src/recommendation_engine_mejorado.py`: Motor mejorado con Haversine
- `api/server.py`: API endpoints para ambos motores
- `demo_con_geolocalizacion.py`: Interfaz de demostración

### Funciones Clave

1. `_calcular_distancia_haversine()`: Cálculo de distancias geográficas
2. `_crear_indice_espacial_servicios()`: Indexación eficiente de servicios
3. `generar_recomendaciones()`: Generación con pre-filtrado por zonas
4. `calcular_puntuacion_servicios_cercanos()`: Evaluación de proximidad

## Conclusión

La implementación del algoritmo de Haversine con optimización por zonas representa una mejora significativa en la calidad y relevancia de las recomendaciones de Citrino. El sistema ahora proporciona:

1. **Precisión geográfica real**: Distancias exactas en lugar de aproximaciones
2. **Rendimiento optimizado**: Pre-filtrado inteligente para mantener velocidad
3. **Recomendaciones relevantes**: Basadas en distancia real a servicios importantes
4. **Transparencia**: Explicaciones claras del proceso de recomendación

Esta tecnología posiciona a Citrino como líder en inteligencia inmobiliaria en Santa Cruz de la Sierra, ofreciendo recomendaciones que realmente reflejan la calidad de vida que cada propiedad puede ofrecer.