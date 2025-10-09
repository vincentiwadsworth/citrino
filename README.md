# 💰 Citrino - Plataforma de Inteligencia de Inversión Inmobiliaria

> **Herramienta interna de Citrino para análisis inteligente de propiedades de inversión en Santa Cruz de la Sierra, Bolivia**

Citrino combina **análisis de datos**, **inteligencia artificial** y **geolocalización precisa** para ayudar al equipo de Citrino a identificar las mejores oportunidades de inversión para sus clientes. No es una plataforma pública, sino una herramienta profesional de trabajo interno.

## 🌟 ¿Qué hace especial a Citrino?

- **🤖 Inteligencia Artificial**: Extracción y análisis automático de propiedades usando modelos de lenguaje avanzados
- **🗺️ Geolocalización Precisa**: Cálculo de distancias reales con algoritmo Haversine y análisis de servicios cercanos
- **⚡ Sistema Híbrido Optimizado**: 80% de extracción sin costo usando regex, LLM solo cuando es necesario
- **💰 Análisis de Inversión**: Motor de recomendación especializado con scoring multicritero
- **🔄 Alta Disponibilidad**: Sistema de fallback automático entre proveedores LLM (99%+ uptime)

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

### 📈 Datos del Sistema

| Categoría | Cantidad | Descripción |
|-----------|----------|-------------|
| **Propiedades** | 1,583 | Con coordenadas GPS precisas |
| **Servicios Urbanos** | 4,777 | Mapeados en Santa Cruz |
| **Zonas Cubiertas** | 50+ | Barrios y áreas metropolitanas |
| **Tasa de Extracción** | 80% | Procesadas solo con regex (sin LLM) |
| **Ahorro de Tokens** | 631,600 | En procesamiento del Proveedor 02 |

### 🆕 Novedades Recientes

**✨ Sistema Híbrido de Extracción Regex + LLM** *(Enero 2025)*
- 80% de propiedades procesadas sin usar LLM (ahorro masivo)
- 90% reducción en uso de tokens
- ~$0.63 ahorrados solo en Proveedor 02

**🔄 Fallback Automático a OpenRouter** *(Enero 2025)*
- Alta disponibilidad (99%+) con modelos gratuitos
- Detecta errores y rate limits automáticamente
- Sin intervención manual necesaria

[Ver detalles técnicos →](docs/SISTEMA_HIBRIDO_EXTRACCION.md)

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

## 🤖 Inteligencia Artificial y Análisis

### Sistema de Recomendación Inteligente

Citrino utiliza un **motor de scoring multicritero** que evalúa cada propiedad según:

| Factor | Peso | Qué evalúa |
|--------|------|------------|
| 📍 Ubicación | 35% | Distancia a zonas preferidas, accesos |
| 💵 Precio | 25% | Ajuste al presupuesto del cliente |
| 🏢 Servicios | 20% | Proximidad a escuelas, hospitales, comercios |
| 🏠 Características | 15% | Habitaciones, baños, amenities |
| ✅ Disponibilidad | 5% | Estado actual en el mercado |

### Integración con Modelos de Lenguaje

**Proveedor Primario: Z.AI GLM-4.6**
- Extracción automática de datos desde descripciones
- Generación de análisis personalizados
- Briefings ejecutivos con insights de mercado

**Fallback Automático: OpenRouter (Modelos Gratuitos 2025)**
- Qwen2.5 72B, DeepSeek R1, Llama 4 Scout
- **99%+ disponibilidad** sin interrupciones
- Cambio automático ante rate limits o errores

**Sistema Híbrido de Extracción (Optimización 2025)**
- ⚡ **80% procesado con regex** (instantáneo, $0 costo)
- 🤖 **20% requiere LLM** (casos complejos)
- 💰 **90% reducción de tokens** vs. LLM puro

[📖 Ver arquitectura técnica completa →](docs/ARQUITECTURA_TECNICA.md)

## 🏗️ Tecnologías y Arquitectura

### Stack Principal

| Capa | Tecnologías | Propósito |
|------|-------------|-----------|
| **Frontend** | HTML5, Bootstrap 5, JavaScript ES6+ | Interfaz responsive y moderna |
| **Backend** | Python 3.8+, Flask 2.3.3 | REST API para análisis |
| **Datos** | Pandas, NumPy, JSON | Procesamiento y almacenamiento |
| **IA** | Z.AI GLM-4.6, OpenRouter | Extracción y análisis inteligente |
| **Geoespacial** | Haversine, Índices espaciales | Cálculos de distancia precisos |

### Componentes del Sistema

```
┌─────────────┐     HTTP/REST     ┌──────────────┐
│  Frontend   │ ←───────────────→ │  API Flask   │
│  (3 apps)   │                   │  (Backend)   │
└─────────────┘                   └──────┬───────┘
                                         │
                               ┌─────────┴─────────┐
                               │                   │
                          ┌────▼────┐      ┌──────▼──────┐
                          │ Motores │      │    LLM      │
                          │  Reco   │      │ Integration │
                          └─────────┘      └─────────────┘
                                │
                          ┌─────▼──────┐
                          │   Datos    │
                          │  (1.5GB)   │
                          └────────────┘
```

[📖 Ver arquitectura detallada →](docs/ARQUITECTURA_TECNICA.md)

## 🚀 Instalación Rápida (5 minutos)

```bash
# 1. Clonar y entrar
git clone https://github.com/vincentiwadsworth/citrino.git
cd citrino

# 2. Instalar dependencias
pip install -r requirements_api.txt

# 3. Configurar API keys
cp .env.example .env
# Editar .env con tus claves de Z.AI y OpenRouter

# 4. Iniciar backend
python api/server.py  # API en http://localhost:5000

# 5. Iniciar frontend (nueva terminal)
python -m http.server 8080  # UI en http://localhost:8080
```

**Producción:** Frontend en [GitHub Pages](https://vincentiwadsworth.github.io/citrino/) | Backend en Render.com

[📖 Guía completa de instalación y desarrollo →](docs/GUIA_DESARROLLO.md)

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

### 💡 Ejemplos de Uso

```
• "Propiedades en zonas de alto desarrollo urbano"
• "Inversión entre $150K-$300K con potencial de plusvalía"
• "Terrenos en áreas de expansión"
• "Departamentos cerca de zonas comerciales"
```

[📖 Ver guía completa de uso →](docs/GUIA_DESARROLLO.md)

##  📚 Documentación

| Documento | Descripción |
|-----------|-------------|
| [**Sistema Híbrido Extracción**](docs/SISTEMA_HIBRIDO_EXTRACCION.md) | Cómo funciona el sistema Regex + LLM |
| [**Arquitectura Técnica**](docs/ARQUITECTURA_TECNICA.md) | Diagramas, stack, patrones de diseño |
| [**Guía de Desarrollo**](docs/GUIA_DESARROLLO.md) | Setup, comandos, testing, deployment |
| [**CLAUDE.md**](CLAUDE.md) | Guía para trabajar con IA en este proyecto |

## 📄 Licencia y Contacto

- **Licencia**: MIT License
- **Equipo**: Citrino Santa Cruz, Bolivia
- **Soporte**: [GitHub Issues](https://github.com/vincentiwadsworth/citrino/issues)
- **Email**: soporte@citrino.com

## 🗺️ Roadmap y Próximas Mejoras

Citrino tiene un plan de evolución claro enfocado en:

1. **Gestión automatizada de planillas Excel** - Reducir errores manuales
2. **Mejora de calidad de datos** - Score 14.4% → >40%
3. **Geocodificación avanzada** - Reducir propiedades sin zona de 61.9% → <15%
4. **Optimización UI/UX** - Mayor adopción del equipo interno

**Ver roadmap completo:** [docs/ROADMAP.md](docs/ROADMAP.md)

---

## 📊 Calidad de Datos y Testing

El sistema mantiene **96% de propiedades con coordenadas GPS** precisas y mejora continuamente la extracción de zonas, precios y características usando el sistema híbrido Regex+LLM.

**Estado actual:** Score 14.4% | **Meta 2025:** >40%

**Ver análisis completo:** [docs/CALIDAD_DATOS.md](docs/CALIDAD_DATOS.md)

---

## 🛠️ Stack Tecnológico

- **Backend:** Python 3.8+, Flask 2.3.3, Pandas, NumPy
- **Frontend:** HTML5, Bootstrap 5, JavaScript ES6+
- **IA:** Z.AI GLM-4.6, OpenRouter (Qwen2.5 72B fallback)
- **Algoritmos:** Haversine, Weighted Scoring, LRU Cache, Regex Patterns

**Ver arquitectura completa:** [docs/ARQUITECTURA_TECNICA.md](docs/ARQUITECTURA_TECNICA.md)

---

## 📞 Contacto y Soporte

**Proyecto interno de Citrino** - Santa Cruz de la Sierra, Bolivia

- **Equipo de Desarrollo**: Vincenti Wadsworth y equipo técnico Citrino
- **Soporte Interno**: Reportar issues en el repositorio
- **Email**: soporte@citrino.com

---

**Herramienta profesional desarrollada para Citrino**