# Instrucciones para Cherry Studio - Citrino Real Estate

## Resumen Rápido

1. **Iniciar servidor API**: `python api/server.py`
2. **Base URL**: `http://localhost:5000`
3. **Base de datos**: 76,853 propiedades reales de Santa Cruz

## Configuración en Cherry Studio

### 1. Instalar dependencias
```bash
pip install requests
```

### 2. Ejemplo de uso en Cherry Studio

```python
import requests
import json

# Configuración
API_URL = "http://localhost:5000"

# Ejemplo 1: Buscar propiedades en Equipetrol
def buscar_equipetrol():
    data = {
        "zona": "Equipetrol",
        "precio_min": 150000,
        "precio_max": 300000,
        "habitaciones_min": 2,
        "banos_min": 2,
        "tiene_garaje": True,
        "limite": 10
    }

    response = requests.post(f"{API_URL}/api/buscar", json=data)
    return response.json()

# Ejemplo 2: Obtener recomendaciones para familia
def recomendar_para_familia():
    data = {
        "presupuesto_min": 200000,
        "presupuesto_max": 350000,
        "adultos": 2,
        "ninos": [8, 12],
        "zona_preferida": "Las Palmas",
        "tipo_propiedad": "casa",
        "necesidades": ["seguridad", "areas_comunes", "estacionamiento"],
        "limite": 5
    }

    response = requests.post(f"{API_URL}/api/recomendar", json=data)
    return response.json()

# Ejemplo 3: Obtener estadísticas generales
def obtener_estadisticas():
    response = requests.get(f"{API_URL}/api/estadisticas")
    return response.json()

# Ejemplo 4: Ver zonas disponibles
def obtener_zonas():
    response = requests.get(f"{API_URL}/api/zonas")
    return response.json()
```

## Endpoints Disponibles

### 1. Health Check
- **URL**: `GET /api/health`
- **Descripción**: Verifica que el API esté funcionando

### 2. Búsqueda de Propiedades
- **URL**: `POST /api/buscar`
- **Parámetros**:
  - `zona`: string (ej: "Equipetrol", "Las Palmas")
  - `precio_min`: number (opcional)
  - `precio_max`: number (opcional)
  - `superficie_min`: number (opcional)
  - `superficie_max`: number (opcional)
  - `habitaciones_min`: number (opcional)
  - `banos_min`: number (opcional)
  - `tiene_garaje`: boolean (opcional)
  - `limite`: number (default: 20)

### 3. Recomendaciones Personalizadas
- **URL**: `POST /api/recomendar`
- **Parámetros**:
  - `presupuesto_min`: number
  - `presupuesto_max`: number
  - `adultos`: number
  - `ninos`: array de edades (opcional)
  - `adultos_mayores`: number (opcional)
  - `zona_preferida`: string (opcional)
  - `tipo_propiedad`: string (opcional)
  - `necesidades`: array de strings (opcional)
  - `limite`: number (default: 10)
  - `umbral_minimo`: number (default: 0.3)

### 4. Estadísticas Generales
- **URL**: `GET /api/estadisticas`
- **Descripción**: Obtiene estadísticas de toda la base de datos

### 5. Zonas Disponibles
- **URL**: `GET /api/zonas`
- **Descripción**: Lista todas las zonas disponibles

## Ejemplos Prácticos

### Búsqueda simple
```python
# Buscar departamentos en Equipetrol entre $200k y $300k
response = requests.post("http://localhost:5000/api/buscar", json={
    "zona": "Equipetrol",
    "precio_min": 200000,
    "precio_max": 300000,
    "limite": 10
})

resultados = response.json()
for propiedad in resultados['propiedades']:
    print(f"{propiedad['nombre']} - ${propiedad['precio']:,}")
```

### Recomendación para pareja joven
```python
# Recomendar para pareja joven sin hijos
response = requests.post("http://localhost:5000/api/recomendar", json={
    "presupuesto_min": 150000,
    "presupuesto_max": 250000,
    "adultos": 2,
    "ninos": [],
    "zona_preferida": "Equipetrol",
    "tipo_propiedad": "departamento",
    "necesidades": ["seguridad", "estacionamiento", "gimnasio"],
    "limite": 5
})

recomendaciones = response.json()
for rec in recomendaciones['recomendaciones']:
    print(f"{rec['nombre']} - {rec['compatibilidad']}% compatible")
```

### Análisis de mercado
```python
# Obtener estadísticas del mercado
response = requests.get("http://localhost:5000/api/estadisticas")
stats = response.json()['estadisticas']

print(f"Total propiedades: {stats['total_propiedades']:,}")
print(f"Precio promedio: ${stats['precio_promedio']:,.0f}")
print(f"Superficie promedio: {stats['superficie_promedio']:.1f} m²")
```

## Flujo de Trabajo Recomendado

1. **Iniciar el servidor API**
   ```bash
   cd "C:\Users\nicol\OneDrive\Documentos\trabajo\citrino\citrino-poc"
   python api/server.py
   ```

2. **Verificar conexión**
   ```python
   response = requests.get("http://localhost:5000/api/health")
   print(response.json())
   ```

3. **Explorar zonas disponibles**
   ```python
   response = requests.get("http://localhost:5000/api/zonas")
   zonas = response.json()['zonas']
   print("Zonas disponibles:", zonas[:10])
   ```

4. **Realizar búsquedas o recomendaciones**
   - Usar los ejemplos anteriores como base
   - Ajustar parámetros según necesidades

5. **Analizar resultados**
   - Los resultados incluyen información completa de propiedades
   - Las recomendaciones incluyen porcentaje de compatibilidad

## Consideraciones

- El servidor debe estar corriendo para hacer consultas
- La primera carga puede tardar unos segundos (carga 76,853 propiedades)
- El motor de recomendación procesa múltiples factores para dar resultados precisos
- Todos los datos son reales de Santa Cruz de la Sierra

## Soporte

Si encuentras problemas:
1. Verifica que el servidor esté corriendo
2. Revisa los logs del servidor
3. Prueba con el script `test_api.py`
4. Verifica la conexión a `http://localhost:5000`