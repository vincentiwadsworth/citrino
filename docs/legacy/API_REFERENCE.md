# 🔌 API Reference de Citrino

## Base URL

```
Desarrollo: http://localhost:5000/api
Producción:  https://citrino-api.render.com/api
```

## Endpoints Disponibles

### Health & Monitoring

#### GET /api/health
Verifica el estado del sistema.

**Response:**
```json
{
    "status": "healthy",
    "properties_count": 1583,
    "services_count": 4777,
    "uptime": "2d 4h 32m"
}
```

#### GET /api/stats
Estadísticas detalladas del sistema.

**Response:**
```json
{
    "total_properties": 1583,
    "zones": 50,
    "cache_hits": 245,
    "cache_misses": 12,
    "avg_response_time_ms": 287
}
```

---

### Property Operations

#### POST /api/search
Búsqueda básica de propiedades con filtros.

**Request Body:**
```json
{
    "zona": "Equipetrol",
    "precio_min": 80000,
    "precio_max": 150000,
    "tipo_propiedad": "departamento",
    "habitaciones_min": 2,
    "banos_min": 1
}
```

**Response:**
```json
{
    "total_results": 12,
    "properties": [
        {
            "id": "prop_123",
            "titulo": "Departamento en Equipetrol",
            "precio": 125000,
            "zona": "Equipetrol",
            "habitaciones": 3,
            "banos": 2,
            "superficie": 120,
            "latitud": -17.7836,
            "longitud": -63.1812
        }
    ]
}
```

---

#### POST /api/recommend
Recomendaciones estándar (sin geolocalización).

**Request Body:**
```json
{
    "presupuesto_min": 80000,
    "presupuesto_max": 150000,
    "zona_preferida": "Equipetrol",
    "tipo_propiedad": "departamento"
}
```

**Response:**
```json
{
    "recommendations": [...],
    "total_matches": 8
}
```

---

#### POST /api/recommend/enhanced
Recomendaciones avanzadas con geolocalización Haversine.

**Request Body:**
```json
{
    "presupuesto_min": 80000,
    "presupuesto_max": 150000,
    "adultos": 2,
    "ninos": [8, 12],
    "zona_preferida": "Equipetrol",
    "tipo_propiedad": "departamento",
    "necesidades": ["escuela_primaria", "hospital"],
    "caracteristicas_deseadas": ["garaje", "piscina"]
}
```

**Response:**
```json
{
    "recommendations": [
        {
            "propiedad": {...},
            "score": 0.87,
            "justificacion": "Excelente ubicación cerca de...",
            "servicios_cercanos": {
                "escuela_primaria": {
                    "nombre": "Colegio Santa Cruz",
                    "distancia_km": 0.8
                },
                "hospital": {
                    "nombre": "Hospital Municipal",
                    "distancia_km": 1.2
                }
            }
        }
    ],
    "total_matches": 8,
    "processing_time_ms": 245
}
```

---

### Data & References

#### GET /api/zones
Lista de zonas disponibles en el sistema.

**Response:**
```json
{
    "zones": [
        "Equipetrol",
        "Urubó",
        "Zona Norte",
        "Zona Sur",
        "Plan 3000",
        ...
    ],
    "total": 50
}
```

---

#### GET /api/property/:id
Detalles completos de una propiedad específica.

**Response:**
```json
{
    "id": "prop_123",
    "titulo": "Departamento en Equipetrol",
    "tipo_propiedad": "departamento",
    "precio": 125000,
    "moneda": "USD",
    "zona": "Equipetrol",
    "direccion": "Calle Los Lirios #456",
    "latitud": -17.7836,
    "longitud": -63.1812,
    "superficie": 120,
    "habitaciones": 3,
    "banos": 2,
    "garajes": 1,
    "descripcion": "Hermoso departamento...",
    "caracteristicas": ["piscina", "gym", "seguridad 24/7"],
    "fecha_scraping": "2025.08.29",
    "codigo_proveedor": "02"
}
```

---

## Códigos de Respuesta

| Código | Significado |
|--------|-------------|
| 200 | Success |
| 400 | Bad Request - Parámetros inválidos |
| 404 | Not Found - Recurso no existe |
| 500 | Internal Server Error |
| 503 | Service Unavailable - Sistema temporalmente fuera |

## Rate Limiting

**Desarrollo:** Sin límites
**Producción:** 100 requests/minuto por IP

## Autenticación

Actualmente sin autenticación (herramienta interna).

En futuras versiones:
```http
Authorization: Bearer <token>
```

## Ejemplos de Uso

### JavaScript (Fetch API)

```javascript
// Búsqueda simple
async function buscarPropiedades() {
    const response = await fetch('http://localhost:5000/api/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            zona: 'Equipetrol',
            precio_max: 200000
        })
    });
    
    const data = await response.json();
    console.log(`Encontradas: ${data.total_results}`);
    return data.properties;
}

// Recomendaciones avanzadas
async function obtenerRecomendaciones() {
    const response = await fetch('http://localhost:5000/api/recommend/enhanced', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            presupuesto_min: 100000,
            presupuesto_max: 200000,
            zona_preferida: 'Equipetrol',
            necesidades: ['escuela_primaria']
        })
    });
    
    return await response.json();
}
```

### Python (requests)

```python
import requests

# Búsqueda
response = requests.post('http://localhost:5000/api/search', json={
    'zona': 'Equipetrol',
    'precio_max': 200000
})

data = response.json()
print(f"Encontradas: {data['total_results']}")

# Recomendaciones
response = requests.post('http://localhost:5000/api/recommend/enhanced', json={
    'presupuesto_min': 100000,
    'presupuesto_max': 200000,
    'zona_preferida': 'Equipetrol'
})

recomendaciones = response.json()
```

### cURL

```bash
# Health check
curl http://localhost:5000/api/health

# Búsqueda
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "zona": "Equipetrol",
    "precio_max": 200000
  }'

# Recomendaciones
curl -X POST http://localhost:5000/api/recommend/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "presupuesto_min": 100000,
    "presupuesto_max": 200000,
    "zona_preferida": "Equipetrol"
  }'
```

---

## Webhooks (Futuro)

Planificado para Q2 2025:
- Notificaciones de nuevas propiedades
- Alertas de cambios de precio
- Updates de disponibilidad

---

**Para más detalles sobre arquitectura, ver [ARQUITECTURA_TECNICA.md](ARQUITECTURA_TECNICA.md)**
