# 💰 Citrino - Plataforma de Inteligencia de Inversión Inmobiliaria

**Plataforma interna de Citrino para apoyar a inversores en Santa Cruz de la Sierra, Bolivia** que utiliza análisis de datos, geolocalización precisa y los algoritmos implementados en este repositorio (Haversine, scoring ponderado, caché LRU) para identificar oportunidades con base en la información disponible.

Esta herramienta se emplea exclusivamente por el equipo de Citrino para estudiar el portafolio de propiedades y generar recomendaciones para sus clientes, no es una plataforma de cara al público general.

## 📊 Estado Actual del Proyecto

✅ **PRODUCCIÓN ACTIVA** - Versión 1.1 con integración Z.AI en desarrollo

### 🚀 Componentes Activos

| Componente | Estado | Descripción |
|------------|--------|-------------|
| **Frontend Web** | ✅ **COMPLETO** | Interfaz interna para presentar análisis al equipo de Citrino |
| **API Backend** | ✅ **COMPLETO** | REST API con análisis de inversión |
| **Motor de Recomendación** | ✅ **COMPLETO** | Ponderación multifactor y distancias Haversine implementadas en `src/` |
| **Asistente Virtual** | ✅ **COMPLETO** | Chat para recopilar criterios y consultar resultados desde la API |
| **Datos de Mercado** | ✅ **COMPLETO** | Propiedades de relevamiento y 4,777 servicios urbanos |

### 📈 Métricas del Sistema

- **🏘️ Propiedades**: 1,583 propiedades con coordenadas exactas
- **🏢 Servicios Urbanos**: 4,777 servicios mapeados
- **📍 Cobertura**: Santa Cruz de la Sierra y áreas metropolitanas
- **🤖 LLM Primario**: Z.AI GLM-4.6 para análisis y extracción
- **🔄 LLM Fallback**: OpenRouter con Qwen2.5 72B (gratuito)
- **🎯 Extracción Inteligente**: Procesamiento automático de 1,579 descripciones en texto libre
- **☁️ Deploy**: Backend en Render.com + Frontend en GitHub Pages
- **🛠️ Uso**: Herramienta interna del equipo Citrino

### 🔄 Trabajo en Progreso

**Integración Z.AI en Citrino Reco** - Ver `INTEGRACION_LLM_CAMBIOS_PENDIENTES.md`:
- Enriquecimiento de justificaciones con análisis personalizado
- Generación de briefings ejecutivos con insights de mercado
- Exportación de documentos en markdown

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

## 🤖 Sistema de Recomendaciones con IA

Citrino ofrece dos niveles de análisis según las necesidades del usuario:

### Motor de Recomendación Base (`/api/recomendar-mejorado`)

**Motor matemático determinístico:**
- ✅ Algoritmo de scoring ponderado:
  - Ubicación: 35%
  - Precio: 25%
  - Servicios cercanos: 20%
  - Características: 15%
  - Disponibilidad: 5%
- ✅ Cálculo de distancias con fórmula Haversine
- ✅ Justificaciones generadas con templates predefinidos
- ✅ Funciona sin LLM - lógica 100% determinística
- ✅ Respuesta instantánea

**Ejemplo de justificación (template):**
> "Esta propiedad tiene excelente ubicación en Equipetrol con proximidad a servicios esenciales. Precio competitivo dentro del rango solicitado."

### Motor de Recomendación con Z.AI (`/api/recomendar-mejorado-llm`)

**Motor matemático + Inteligencia Artificial:**
- ✅ **MISMO algoritmo de scoring** que el motor base
- ✅ **SIEMPRE genera briefing ejecutivo** con Z.AI:
  - Análisis del mercado inmobiliario
  - Tendencias de la zona
  - Recomendaciones estratégicas
  - Insights personalizados
- ✅ **Enriquecimiento opcional** de justificaciones:
  - Se activa cuando el usuario provee contexto adicional en `informacion_llm`
  - Análisis personalizado por propiedad con lenguaje natural
  - Considera motivaciones y necesidades específicas del cliente

**Ejemplo de justificación enriquecida (Z.AI):**
> "Considerando tu interés en inversión de mediano plazo, esta propiedad en Equipetrol ofrece alto potencial de plusvalía debido a los desarrollos urbanos planificados en la zona. La proximidad al nuevo centro comercial incrementará su valor estimado en 15-20% en los próximos 3 años."

### Cuándo se Usa Cada Endpoint

| Escenario | Endpoint | Z.AI | Briefing | Enriquecimiento |
|-----------|----------|------|----------|----------------|
| Usuario sin contexto adicional | `/recomendar-mejorado-llm` | ✅ | ✅ Siempre | ❌ Templates |
| Usuario con contexto adicional | `/recomendar-mejorado-llm` | ✅ | ✅ Siempre | ✅ Personalizado |
| Z.AI no disponible (fallback) | `/recomendar-mejorado` | ❌ | ❌ | ❌ Templates |

### Configuración de Z.AI

Para activar el motor con IA, configura la API key en `.env`:

```bash
# Proveedor primario
ZAI_API_KEY=tu_clave_zai_aqui
LLM_PROVIDER=zai
LLM_MODEL=glm-4.6
```

**En producción (Render.com):**
- Configura `ZAI_API_KEY` en las variables de entorno del dashboard
- El briefing ejecutivo se generará automáticamente en cada recomendación
- El enriquecimiento personalizado se activará cuando el usuario provea contexto

### 🔄 Sistema de Fallback Automático (2025)

**Alta disponibilidad con OpenRouter**: El sistema detecta automáticamente cuando Z.AI no está disponible (rate limits 429, errores de servidor 500/502/503) y cambia a OpenRouter con modelos gratuitos de última generación.

**Configuración del Fallback:**

```bash
# Habilitar fallback automático
OPENROUTER_FALLBACK_ENABLED=true
OPENROUTER_API_KEY=tu_clave_openrouter_aqui

# Modelo gratuito recomendado (2025)
OPENROUTER_MODEL=qwen/qwen-2.5-72b-instruct:free
```

**Modelos Gratuitos Disponibles:**

| Modelo | Parámetros | Especialidad | Contexto |
|--------|-----------|--------------|----------|
| **Qwen2.5 72B Instruct** ⭐ | 72B | JSON estructurado | 128K tokens |
| DeepSeek R1 | 671B (37B activos) | Razonamiento complejo | 128K tokens |
| Llama 4 Maverick | 400B (17B activos) | Multimodal | 256K tokens |
| Llama 4 Scout | 109B (17B activos) | Contexto masivo | 512K tokens |

**Ventajas del Sistema de Fallback:**
- ✅ **99%+ disponibilidad** del sistema de extracción LLM
- ✅ **Detección automática** de rate limits y errores
- ✅ **Transparente**: Usuario no necesita intervenir
- ✅ **Sin costo adicional**: Modelos gratuitos de alta calidad
- ✅ **Tracking completo**: Estadísticas de uso por provider

**Casos de Uso:**
- Extracción de datos del Proveedor 02 (1,579 propiedades en texto libre)
- Procesamiento ETL con alto volumen de consultas
- Resiliencia ante limitaciones de API primaria

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

## 🧪 Testing y Calidad de Datos

### Suite de Pruebas Completa

```bash
# Ejecutar todas las pruebas
pytest

# Pruebas específicas
pytest tests/test_api.py -v           # API endpoints
pytest tests/test_api_simple.py -v    # Smoke tests manuales
pytest tests/test_data_validation.py -v   # Validación de datos
pytest tests/test_etl_pipeline.py -v      # Pipeline ETL
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

### Herramientas de Análisis de Calidad

```bash
# Análisis completo de calidad de datos
python scripts/analizar_calidad_datos.py

# Análisis de columnas por proveedor
python scripts/analizar_proveedores.py

# Detección avanzada de duplicados
python scripts/detectar_duplicados.py

# Extracción de características desde descripciones
python scripts/extraer_caracteristicas.py

# Normalización de precios y monedas
python scripts/normalizar_precios.py

# Geocodificación inversa (requiere conexión a internet)
python scripts/geocodificar_coordenadas.py
```

### Estado Actual de Calidad de Datos

**Baseline establecido** (ver `PLAN_PRUEBAS_ETL_RESUMEN.md`):

| Métrica | Estado Actual | Objetivo |
|---------|---------------|----------|
| **Score General** | 14.4% | >40% |
| **Con Zona** | 38.1% | >90% |
| **Con Precio** | 14.4% | >50% |
| **Con Coordenadas** | 96.0% | 96%+ ✅ |
| **Con Características** | ~16% | >60% |

**Mejoras Implementadas:**
- ✅ Sistema de extracción de zonas desde títulos/descripciones (30+ zonas conocidas)
- ✅ Geocodificación inversa desde coordenadas (+420 zonas identificadas)
- ✅ Extracción regex de habitaciones, baños, garajes (+171 propiedades enriquecidas)
- ✅ Detección multi-criterio de duplicados (URL → Coords → Título)
- ✅ Análisis de proveedores y mapeo de esquemas inconsistentes

**Archivos de Soporte:**
- `pytest.ini` - Configuración de pytest con markers personalizados
- `tests/conftest.py` - Fixtures compartidos para testing
- `data/reporte_calidad_datos.json` - Reporte detallado de métricas
- `data/estadisticas_duplicados.json` - Análisis de duplicados
- `data/analisis_proveedores.json` - Mapeo de columnas por proveedor


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

### Commits Prioritarios Planificados

#### 1. Sistema de Gestión de Planillas Excel
**Problema:** Actualmente el personal de Citrino debe cargar/quitar archivos `.xlsx` manualmente en `data/raw/`.

**Solución Propuesta:**
- [ ] Panel web de administración para carga de archivos
- [ ] Validación automática de formato y esquema
- [ ] Versionado y respaldo automático de planillas
- [ ] Vista previa de datos antes de procesar
- [ ] Sistema de permisos por rol (admin/editor/viewer)
- [ ] Historial de cambios con rollback

**Beneficio:** Reducir errores humanos y democratizar acceso a actualización de datos.

#### 2. Corrección de Errores en Archivos Excel
**Problema:** Los archivos `.xlsx` de proveedores contienen errores que corrompen la base de datos:
- Esquemas inconsistentes entre fechas del mismo proveedor
- Campos críticos vacíos o mal formateados (precios, zonas, tipos)
- Duplicados no detectados por falta de identificadores únicos

**Solución Propuesta:**
- [ ] Validador pre-procesamiento con reglas por proveedor
- [ ] Normalización automática de tipos de datos
- [ ] Auto-corrección de formatos de precio/moneda
- [ ] Sugerencias inteligentes para campos vacíos
- [ ] Reportes de calidad por archivo subido
- [ ] Quarantine para archivos con >20% de errores

**Beneficio:** Mejorar score de calidad de 14.4% → >40%.

#### 3. Geocodificación con OpenStreetMap/Google Maps
**Problema:** 61.9% de propiedades sin zona. Geocodificación inversa actual con OSM Nominatim solo identifica 31% de ubicaciones.

**Solución Propuesta:**
- [ ] Integración con Google Maps Geocoding API (mejor para Bolivia)
- [ ] Sistema híbrido: OSM gratuito + Google Maps fallback
- [ ] Cache de resultados de geocodificación
- [ ] Catálogo expandido de 30 → 100+ zonas de Santa Cruz
- [ ] Validación manual asistida para coordenadas ambiguas
- [ ] Enriquecimiento con barrios, UV, manzanas desde coords

**Beneficio:** Reducir propiedades sin zona de 61.9% → <15%.

#### 4. Corrección de Responsividad y UI/UX
**Problema:** Interfaz actual funcional pero mejorable en dispositivos móviles y experiencia de usuario.

**Solución Propuesta:**
- [ ] Rediseño responsive mobile-first
- [ ] Optimización de performance (lazy loading, compresión)
- [ ] Mejora de flujos de navegación
- [ ] Componentes de carga y feedback visual
- [ ] Dark mode
- [ ] Accesibilidad WCAG 2.1 nivel AA
- [ ] PWA con trabajo offline

**Beneficio:** Aumentar adopción y satisfacción del equipo interno.

### Próximos Lanzamientos (Q1 2025)

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