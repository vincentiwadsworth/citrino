# 💰 Citrino - Plataforma de Inteligencia de Inversión Inmobiliaria

**Plataforma interna de Citrino para apoyar a inversores en Santa Cruz de la Sierra, Bolivia** que utiliza análisis de datos, geolocalización precisa y los algoritmos implementados en este repositorio (Haversine, scoring ponderado, caché LRU) para identificar oportunidades con base en la información disponible.

Esta herramienta se emplea exclusivamente por el equipo de Citrino para estudiar el portafolio de propiedades y generar recomendaciones para sus clientes, no es una plataforma de cara al público general.

## 📊 Estado Actual del Proyecto

✅ **PRODUCCIÓN LISTA** - Versión 1.0 completa y funcional

### 🚀 Componentes Activos

| Componente | Estado | Descripción |
|------------|--------|-------------|
| **Frontend Web** | ✅ **COMPLETO** | Interfaz interna para presentar análisis al equipo de Citrino |
| **API Backend** | ✅ **COMPLETO** | REST API con análisis de inversión |
| **Motor de Recomendación** | ✅ **COMPLETO** | Ponderación multifactor y distancias Haversine implementadas en `src/` |
| **Asistente Virtual** | ✅ **COMPLETO** | Chat para recopilar criterios y consultar resultados desde la API |
| **Datos de Mercado** | ✅ **COMPLETO** | Propiedades de relevamiento y 4,777 servicios urbanos |

### 📈 Métricas del Sistema

- **🏘️ Propiedades de Relevamiento**: Actualizadas continuamente con coordenadas exactas
- **🏢 Servicios Urbanos**: 4,777 (impactan valor y plusvalía)
- **📍 Cobertura Geográfica**: 100% Santa Cruz de la Sierra y áreas metropolitanas
- **🛠️ Uso interno**: Operado por el equipo de Citrino para ofrecer recomendaciones personalizadas a sus clientes

## 🎯 Características Principales

### 🤖 Inteligencia Artificial para Inversores
- **Motor de recomendación especializado** en análisis de oportunidades
- **Factores de evaluación** basados en potencial de la zona
- **Análisis de ubicación** mediante coordenadas precisas
- **Filtros por Unidad Vecinal y Manzana** para segmentación detallada

### 🗺️ Geolocalización para Inversión
- **Fórmula de Haversine** para cálculo de distancias reales
- **Índice espacial** para búsquedas optimizadas por zona
- **Coordenadas exactas** para propiedades de relevamiento
- **Filtros UV/Manzana** para análisis por ubicación precisa
- **Cálculo de proximidad** a servicios que impactan plusvalía

### 💬 Experiencias Asistidas con IA
- **Citrino Reco** centraliza notas de exploración y devuelve recomendaciones al instante
- **Citrino Chat** permite "chatear con la información" sin restricciones temáticas
- **Extracción automática de criterios** desde conversaciones y formularios
- **Arquitectura preparada** para integrar z.ai y enriquecer los prompts del LLM

### 💻 Panel de Inversor
- **Diseño responsive** para visualización de propiedades
- **Bootstrap 5** con componentes funcionales
- **Filtros avanzados** por zona, precio y características
- **Comparativas detalladas** de propiedades seleccionadas

## 🏗️ Arquitectura del Sistema

### Frontend (Capa de Presentación)
```
Frontend Web/
├── index.html              # Página principal y marketing
├── citrino-reco.html       # Notas de exploración + recomendaciones inline
├── chat.html               # Citrino Chat para consultas multi-fuente
└── assets/
    ├── css/custom.css      # Estilos personalizados
    ├── js/main.js          # Lógica principal de UI
    └── js/api.js           # Comunicación con backend
```

### Backend (Capa de Negocio)
```
API Backend/
├── api/server.py           # Servidor Flask REST API
├── src/
│   ├── recommendation_engine.py      # Motor básico de recomendación
│   ├── recommendation_engine_mejorado.py  # Motor avanzado con geolocalización
│   ├── scoring_prospectos.py         # Sistema de calificación de clientes
│   └── llm_integration.py            # Integración con LLM
└── tests/                  # Suite de pruebas completo
```

### Datos (Capa de Información)
```
Procesamiento/
├── scripts/
│   ├── build_relevamiento_dataset.py       # ETL de datos de mercado
│   ├── build_urban_services_dataset.py     # Integración municipal
│   └── build_sample_inventory.py           # Inventario de muestra para demos/tests
└── data/
    ├── raw/                                 # Datos de relevamiento Excel
    ├── base_datos_relevamiento.json        # Propiedades de mercado
    └── guia_urbana_municipal_completa.json  # 4,777 servicios urbanos
```

## 🛠️ Tecnologías Utilizadas

### Frontend
- **HTML5** - Semántico y accesible
- **CSS3** - Flexbox, Grid, Animaciones con Bootstrap 5
- **JavaScript ES6+** - Módulos, async/await
- **Bootstrap Icons** - Iconos vectoriales
- **Web APIs** - Speech Recognition, LocalStorage, Geolocation

### Backend
- **Python 3.x** - Lenguaje principal
- **Flask 2.3.3** - Framework REST API
- **Pandas 2.0.3** - Procesamiento de datos
- **NumPy 1.24.3** - Cálculos numéricos
- **Flask-CORS 4.0.0** - Soporte para cross-origin requests

### Algoritmos de Procesamiento
- **Fórmula de Haversine** - Cálculo de distancias geográficas
- **Índice espacial** - Optimización por UV/Manzana
- **LRU Caching** - Memoria caché para consultas frecuentes
- **Weighted Scoring** - Sistema de calificación por múltiples factores
- **Procesamiento geoespacial** - Análisis por coordenadas

## 🚀 Instalación y Configuración

### Prerrequisitos

- **Python 3.8+** para el backend
- **Navegador moderno** (Chrome 90+, Firefox 88+, Safari 14+)
- **Git** para clonar el repositorio

### 1. Clonar el Repositorio

```bash
git clone https://github.com/vincentiwadsworth/citrino.git
cd citrino
```

### 2. Instalar Dependencias del Backend

```bash
pip install -r requirements_api.txt
```

### 3. Iniciar el Servidor Backend

```bash
python api/server.py
```

El API estará disponible en: **http://localhost:5000**

### 4. Acceder al Frontend

Opción A - **GitHub Pages (Recomendado)**:
- El frontend está desplegado automáticamente en: https://vincentiwadsworth.github.io/citrino/

Opción B - **Servidor Local**:
```bash
# Desde la raíz del proyecto
python -m http.server 8080
# Acceder a: http://localhost:8080
```

### 5. Verificar Instalación

```bash
pytest
```

Deberías ver:
```
======================== 6 passed ========================
```

## 🎮 Uso del Sistema

### Flujo Principal de Usuario

1. **Inicio** → `index.html`
   - Explora las características del sistema
   - Elige entre "Crear Perfil" o "Asistente Virtual"

2. **Citrino Reco** → `citrino-reco.html`
   - Registra notas de exploración sin exponer datos sensibles
   - Define presupuestos, zonas y contexto de negocio
   - Añade instrucciones específicas para el futuro LLM
   - Obtén recomendaciones inline y exporta JSON

3. **Citrino Chat** → `chat.html`
   - Consulta el inventario, la guía urbana y el censo inmobiliario
   - Cruza datasets, genera prompts e insights conversacionales
   - Visualiza recomendaciones dentro del chat
   - Comparte respuestas con el equipo o vuelve a Citrino Reco

### Ejemplos de Consultas de Inversión

```
• "Busco propiedades en zonas con buen desarrollo urbano"
• "Necesito opciones de inversión en el rango de $150,000 a $300,000"
• "Me interesan terrenos en áreas de expansión de la ciudad"
• "Busco departamentos cerca de zonas comerciales"
• "Quiero analizar oportunidades en Unidades Vecinales específicas"
```

## ⚙️ Configuración Avanzada

### Personalización del API Backend

Edita `assets/js/api.js`:

```javascript
const baseURL = 'http://localhost:5000/api'; // URL del backend
```

### Configuración del Motor de Recomendación

En `src/recommendation_engine_mejorado.py`:

```python
# Pesos del algoritmo (ajustables según criterios de inversión)
weights = {
    'ubicacion': 0.35,     # Proximidad y zona
    'precio': 0.25,        # Rango de precio
    'servicios': 0.20,     # Servicios cercanos
    'caracteristicas': 0.15, # Características del inmueble
    'disponibilidad': 0.05  # Disponibilidad en relevamiento
}
```

### Datos del Sistema

Los datos principales están excluidos del repositorio por su tamaño:
- **Propiedades**: 76,853 registros (123MB)
- **Servicios Urbanos**: 4,777 registros (307MB)

Para obtener los datos completos, contacta al equipo de Citrino.

## 🔌 API Endpoints

### Health y Estado
- `GET /api/health` - Verificación de salud del sistema
- `GET /api/stats` - Estadísticas detalladas del sistema

### Búsqueda y Recomendación
- `POST /api/search` - Búsqueda básica de propiedades
- `POST /api/recommend` - Recomendaciones estándar
- `POST /api/recommend/enhanced` - Recomendaciones avanzadas con geolocalización

### Datos y Referencias
- `GET /api/zones` - Lista de zonas disponibles
- `GET /api/property/:id` - Detalles de propiedad específica

### Ejemplo de Uso del API

```javascript
// Recomendaciones avanzadas
const response = await fetch('/api/recommend/enhanced', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        presupuesto_min: 80000,
        presupuesto_max: 150000,
        adultos: 2,
        ninos: [8, 12],
        zona_preferida: 'Equipetrol',
        tipo_propiedad: 'departamento',
        necesidades: ['escuela_primaria', 'hospital'],
        caracteristicas_deseadas: ['garaje', 'piscina']
    })
});

const data = await response.json();
console.log(`Encontradas ${data.total_results} propiedades`);
```

## 🧪 Testing

### Suite de Pruebas Completa

```bash
# Ejecutar todas las pruebas
pytest

# Pruebas específicas
pytest tests/test_api.py -v           # API endpoints
pytest tests/test_api_simple.py -v    # Smoke tests manuales
```

### Validación del Sistema

```bash
# Regenerar dataset de relevamiento (Excel -> JSON)
python scripts/build_relevamiento_dataset.py

# Regenerar dataset de servicios urbanos
python scripts/build_urban_services_dataset.py

# Generar inventario de ejemplo para demos/pruebas
python scripts/build_sample_inventory.py
```

## 🚀 Despliegue en Producción

### Frontend - GitHub Pages

El frontend está configurado para despliegue automático:

1. **GitHub Pages**: https://vincentiwadsworth.github.io/citrino/
2. **Activación automática** con cada push a `main`
3. **Dominio personalizado** configurable

### Backend - Opciones

**Opción A - Heroku/Render:**
```bash
# Despliegue en Heroku
heroku create citrino-api
git push heroku main
```

**Opción B - AWS Lambda:**
- Usar Serverless Framework
- Configurar API Gateway
- Desplegar funciones Lambda

**Opción C - VPS/Docker:**
```bash
# Build de imagen Docker
docker build -t citrino-api .
docker run -p 5000:5000 citrino-api
```

## 📊 Monitorización y Métricas

### Métricas del Sistema

- **📈 Rendimiento**: tiempos de respuesta de la API observados por el equipo de Citrino
- **🎯 Calidad**: revisión manual de resultados generados por los motores de recomendación
- **💾 Caching**: estado del caché LRU incluido en el motor mejorado
- **🌐 Disponibilidad**: monitoreo del estado de los servicios desplegados internamente

### Logging

```python
# Logs estructurados en el backend
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"Recomendación generada: {len(recommendations)} propiedades")
logger.info(f"Tiempo de procesamiento: {processing_time:.2f}s")
```

## 🔧 Personalización y Extensión

### Modificación de Pesos del Algoritmo

Edita `src/recommendation_engine_mejorado.py`:

```python
# Personalización de pesos según negocio
weights = {
    'budget': 0.30,        # Más peso al presupuesto
    'family': 0.25,        # Más peso a la familia
    'services': 0.20,      # Menos peso a servicios
    'demographics': 0.15,  # Mantener demográficos
    'preferences': 0.10    # Mantener preferencias
}
```

### Nuevos Servicios Urbanos

Agrega nuevos tipos de servicios en `data/guia_urbana_municipal_completa.json`:

```json
{
    "nombre": "Nuevo Servicio",
    "categoria": "salud",
    "coordenadas": [-17.7836, -63.1812],
    "direccion": "Calle Nueva #123",
    "horarios": "Lun-Vie 8:00-18:00"
}
```

## 🐛 Troubleshooting

### Problemas Comunes y Soluciones

#### API No Responde
```bash
# Verificar puerto
netstat -an | grep 5000

# Reiniciar servidor
python api/server.py
```

#### Frontend No Conecta
- Verificar CORS en `api/server.py`
- Confirmar URL en `assets/js/api.js`
- Revisar consola del navegador

#### Rendimiento Lento
- Verificar logs del backend (`api/server.py`) para identificar cuellos de botella
- Asegurarse de que los datasets estén actualizados (`build_relevamiento_dataset.py`, `build_urban_services_dataset.py`)
- Confirmar que el cache interno del motor no se esté invalidando continuamente

### Debug Mode

```javascript
// Activar debug en frontend
localStorage.setItem('debug', 'true');

// Ver logs en consola
console.log('API Response:', data);
console.log('Cache Status:', cacheStats);
```

## 📄 Licencia

MIT License - ver archivo LICENSE para detalles.

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Por favor sigue las siguientes pautas:

### Proceso de Contribución

1. **Fork** el repositorio
2. **Crear rama de feature** (`git checkout -b feature/AmazingFeature`)
3. **Realizar cambios** y pruebas
4. **Commit** cambios (`git commit -m 'Add AmazingFeature'`)
5. **Push** a la rama (`git push origin feature/AmazingFeature`)
6. **Abrir Pull Request**

### Código de Conducta

- Respeto y colaboración mutua
- Código documentado y testeado
- Seguir las convenciones del proyecto
- Reportar bugs con detalles y ejemplos

### Guía de Estilo

- **Python**: PEP 8, type hints, docstrings
- **JavaScript**: ES6+, async/await, comentarios
- **CSS**: Variables CSS, Bootstrap 5 naming
- **HTML**: Semántico, accesible, SEO-friendly

## 📞 Soporte y Comunidad

### Soporte Técnico

- **🐛 Reportar Bugs**: [GitHub Issues](https://github.com/vincentiwadsworth/citrino/issues)
- **💬 Discusiones**: [GitHub Discussions](https://github.com/vincentiwadsworth/citrino/discussions)
- **📧 Email**: soporte@citrino.com
- **📱 WhatsApp**: +591 XXX XXXXX (soporte prioritario)

### Documentación

- **📖 Wiki del Proyecto**: [GitHub Wiki](https://github.com/vincentiwadsworth/citrino/wiki)
- **🎥 Tutoriales**: YouTube Channel (próximamente)
- **📑 API Reference**: [Documentación de API](https://vincentiwadsworth.github.io/citrino/api-docs)

### Comunidad

- **Slack**: Únete a nuestro workspace de Slack
- **Discord**: Servidor de la comunidad Citrino
- **LinkedIn**: Síguenos para actualizaciones

## 🗺️ Roadmap Futuro

### Próximos Lanazamientos (Q4 2024)

- [ ] **Mobile App** - Aplicación nativa para iOS y Android
- [ ] **Integración WhatsApp** - Chatbot para WhatsApp Business
- [ ] **Dashboard Analytics** - Métricas avanzadas en tiempo real
- [ ] **Notificaciones Push** - Alertas de nuevas propiedades

### 2025 Roadmap

- [ ] **Migración PostgreSQL** - De JSON a base de datos relacional
- [ ] **ML Avanzado** - Modelos de machine learning predictivos
- [ ] **API GraphQL** - Más eficiente que REST
- [ ] **Multi-zona** - Expansión a otras ciudades bolivianas
- [ ] **Portal de Agentes** - Panel para agentes inmobiliarios

### Mejoras Continuas

- [ ] **Performance Optimization** - Reducción de tiempos de respuesta
- [ ] **UI/UX Enhancements** - Mejora continua de la interfaz
- [ ] **Security Updates** - Mantenimiento de seguridad
- [ ] **Documentation** - Mejora de documentación y tutoriales

## 🏆 Reconocimientos

### Equipo de Desarrollo

- **Desarrollo Principal**: Vincenti Wadsworth
- **Arquitectura de Sistemas**: Equipo técnico Citrino
- **Diseño UI/UX**: Equipo de diseño Citrino
- **Validación de Datos**: Equipo de datos Citrino

### Agradecimientos Especiales

- **Municipalidad de Santa Cruz** - Por los datos de la guía urbana
- **Franz Inmobiliaria** - Por la base de datos de propiedades
- **Comunidad Técnica SCZ** - Por el apoyo y feedback

### Tecnologías de Terceros

- **Bootstrap**: Framework CSS
- **Flask**: Framework web Python
- **Pandas**: Análisis de datos
- **Leaflet**: Mapas interactivos (futuro)

## 📊 Estadísticas del Proyecto

### GitHub Stats
- **⭐ Stars**: [Contribuye con una estrella](https://github.com/vincentiwadsworth/citrino)
- **🍴 Forks**: [Fork para contribuir](https://github.com/vincentiwadsworth/citrino/fork)
- **🐛 Issues**: [Reportar problemas](https://github.com/vincentiwadsworth/citrino/issues)
- **📥 Descargas**: [Código fuente](https://github.com/vincentiwadsworth/citrino/archive/refs/heads/main.zip)

### Impacto
- **🏘️ Propiedades Analizadas**: 76,853 (según `data/base_datos_relevamiento.json`)
- **🏢 Servicios Mapeados**: 4,777 (según `data/guia_urbana_municipal_completa.json`)
- **👥 Equipo Objetivo**: analistas y consultores de Citrino
- **🎯 Aplicación**: soporte interno para recomendaciones a clientes de inversión

---

## 🚀 ¡Comienza a Usar Citrino Hoy!

**URL del Proyecto**: https://github.com/vincentiwadsworth/citrino
**Frontend en Producción**: https://vincentiwadsworth.github.io/citrino/
**Contacto**: soporte@citrino.com

---

**Desarrollado con ❤️ en Santa Cruz de la Sierra, Bolivia**
*Transformando la búsqueda de propiedades con inteligencia artificial y geolocalización precisa*