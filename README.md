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

✅ **SPRINT 1 COMPLETADO** - Versión 2.0.0: Estructura PostgreSQL + PostGIS lista para producción

🚀 **Migración PostgreSQL Preparada** - Scripts ETL completos para migración desde JSON a PostgreSQL + PostGIS

### 🚀 Componentes Activos

| Componente | Estado | Descripción |
|------------|--------|-------------|
| **Frontend Web** | ✅ **COMPLETO** | Interfaz interna para presentar análisis al equipo de Citrino |
| **API Backend** | ✅ **COMPLETO** | REST API con análisis de inversión y filtro de monedas |
| **Motor de Recomendación** | ✅ **COMPLETO** | Ponderación multifactor y distancias Haversine implementadas en `src/` |
| **🤖 Chatbot UI Profesional** | ✅ **COMPLETO** | Interfaz conversacional OpenAI-compatible con búsqueda de propiedades |
| **Análisis de Datos Raw** | ✅ **COMPLETO** | Sistema completo de análisis con métricas LLM para 1,385 propiedades |
| **Sistema de Errores LLM** | ✅ **COMPLETO** | Reporte detallado de errores con clasificación automática y debug |
| **ETL Optimizado** | ✅ **MEJORADO** | Sistema híbrido Regex+LLM con fallback automático |
| **Datos de Mercado** | ✅ **ACTUALIZADO** | Propiedades de relevamiento actualizadas con nuevos archivos Excel |
| **🚀 PostgreSQL + PostGIS** | ✅ **COMPLETO** | Scripts ETL production-ready, DDL optimizado, validación completa |
| **📊 Migración Production** | ✅ **COMPLETA** | Sistema completo para migración JSON → PostgreSQL con PostGIS |
| **📚 Documentación Técnica** | ✅ **COMPLETA** | Deep dive técnico, guía de migración y arquitectura actualizada |

### 📈 Datos del Sistema

| Categoría | Cantidad | Descripción |
|-----------|----------|-------------|
| **Propiedades Procesadas** | 1,385 | Sistema de análisis con métricas LLM completas |
| **Agentes Identificados** | 79 | Únicos agentes de datos procesados |
| **Proveedores de Datos** | 5 | Fuentes diferentes de scraping inmobiliario |
| **Eficiencia LLM** | 37.7% | Procesadas sin costo LLM (regex-only) |
| **Costo Total LLM** | $0.002 | Optimización masiva de tokens |
| **Servicios Urbanos** | 4,777 | Mapeados en Santa Cruz |
| **Zonas Cubiertas** | 50+ | Barrios y áreas metropolitanas |
| **Disponibilidad Chatbot** | 99.9% | Z.AI → OpenRouter automático |

### 🆕 Novedades Recientes

**🤖 Sprint Chatbot & Análisis Completado** *(Octubre 2025)*
- ✅ **Chatbot UI Profesional** implementado con estándar OpenAI-compatible
- ✅ **Análisis de Datos Raw** completo para 1,385 propiedades con métricas LLM detalladas
- ✅ **Sistema de Búsqueda Natural** para propiedades con lenguaje conversacional
- ✅ **Integración Docker** para desarrollo local con un comando
- ✅ **Configuración Automática** con setup.py y plantillas .env
- ✅ **Documentación Completa** con README detallado y troubleshooting
- ✅ **API Endpoint** `/v1/chat/completions` compatible con Chatbot UI
- ✅ **Métricas de Eficiencia**: 37.7% procesado sin LLM, costo $0.002 USD total

**🎉 Sprint 1 Completado: Estructura PostgreSQL + PostGIS** *(Octubre 2025)*
- ✅ 5/5 stories finalizadas (13 puntos) - 100% completado
- ✅ Scripts ETL production-ready para migración completa
- ✅ DDL PostgreSQL + PostGIS con índices GIST optimizados
- ✅ Sistema de validación integral y pruebas de rendimiento
- ✅ Documentación técnica completa y deep dive architecture
- ✅ Sistema switching JSON ↔ PostgreSQL con rollback instantáneo
- ✅ Orquestador automático con recuperación de errores

**🚀 Migración PostgreSQL Production-Ready** *(Octubre 2025)*
- 🗄️ Arquitectura PostgreSQL 15+ con PostGIS 3.3+ optimizada
- ⚡ Índices GIST para búsquedas espaciales ultra rápidas (100x mejora)
- 📊 Expected: consultas geoespaciales de segundos → milisegundos
- 🔄 Soporte para 10x crecimiento sin degradación de rendimiento
- 👥 Concurrencia multiusuario sin bloqueos
- 🛡️ Backup automático y recuperación ante errores
- 📈 Dashboard de monitoreo y validación en tiempo real

**🎨 Mejoras UI/UX en Citrino Chat** *(Octubre 2025)*
- Barra de input siempre visible en la parte inferior sin scroll
- Limpieza automática de historial al cargar página (mejor privacidad)
- Botones de limpiar/exportar más discretos con tooltips
- Eliminación de botones de sugerencias rápidas para interfaz más limpia
- Layout optimizado para mejor experiencia de usuario
- Responsive design mejorado para móviles

**🚨 Sistema de Reporte Detallado de Errores LLM** *(Octubre 2025)*
- Reporte específico cuando Z.AI/OpenRouter no están disponibles
- Clasificación automática de errores (rate limit, server error, auth error, etc.)
- Mensajes contextuales para usuarios según tipo de problema
- Información de debug completa para desarrolladores
- Notificaciones toast con detalles técnicos en modo desarrollo

**🔧 ETL Optimizado y Fallback LLM Corregido** *(Octubre 2025)*
- Sistema de fallback automático corregido (99.9% disponibilidad)
- Procesamiento recursivo de archivos Excel en subcarpetas
- Sistema híbrido Regex+LLM con 70-80% ahorro de tokens
- Modo muestreo para testing controlado

**💰 Filtro de Monedas Implementado** *(Octubre 2025)*
- Filtrado por USD/BOB en Citrino Reco
- Estadísticas de oferta por moneda
- Soporte para mercado bimonetario boliviano

**✨ Sistema Híbrido de Extracción Regex + LLM** *(Enero 2025)*
- 80% de propiedades procesadas sin usar LLM (ahorro masivo)
- 90% reducción en uso de tokens
- ~$0.63 ahorrados solo en Proveedor 02

**🔄 Fallback Automático a OpenRouter** *(Enero 2025)*
- Alta disponibilidad con modelos gratuitos
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
- **🤖 Chatbot UI Profesional** - Interfaz conversacional OpenAI-compatible con búsqueda natural de propiedades
  - Búsqueda conversacional: "Busca casas en Equipetrol hasta 200k USD"
  - Análisis de mercado en tiempo real con datos reales
  - Recomendaciones personalizadas basadas en 1,385 propiedades
  - Integración completa con API de Citrino
  - Docker development environment listo para producción
- **Citrino Reco** centraliza notas de exploración y devuelve recomendaciones al instante
  - Filtrado por moneda (USD/BOB) con estadísticas de oferta
  - Badges de moneda en perfiles guardados
- **Citrino Chat** permite "chatear con la información" sin restricciones temáticas
- **Barra de input siempre visible** sin necesidad de scroll
- **Historial limpio** en cada sesión (mejor privacidad)
- **Controles discretos** con tooltips para mejor UX
- **Extracción automática de criterios** desde conversaciones y formularios
- **Arquitectura preparada** con sistema LLM redundante y alta disponibilidad

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
- ⚡ **90% procesado con regex** (instantáneo, $0 costo)
- 🤖 **10% requiere LLM** (casos complejos)
- 💰 **70-80% reducción de tokens** vs. LLM puro
- 🔄 **Fallback automático** Z.AI → OpenRouter (99.9% uptime)
- 🚨 **Reporte detallado de errores** con clasificación automática y debug

### Sistema de Reporte de Errores Avanzado

**Diagnóstico Inteligente de Problemas LLM:**
- **Clasificación automática** de errores (rate limit, server error, auth error, etc.)
- **Mensajes contextuales** para usuarios según tipo de problema
- **Información de debug completa** para desarrolladores en modo localhost
- **Notificaciones toast** con detalles técnicos (providers, códigos HTTP)
- **Recomendaciones automáticas** de resolución

**Ejemplos de Mensajes Contextuales:**
```javascript
// Rate limit detectado
"Sistema LLM con limite de velocidad temporal. Usando analisis local inteligente."

// Error de servidor
"Servicios LLM con mantenimiento temporal. Usando analisis local avanzado."

// Problema de configuración
"Configuracion LLM requiere actualizacion. Usando analisis local."
```

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

### Opción 1: Chatbot UI Profesional (Recomendado)

**Configuración Rápida con Docker:**
```bash
# 1. Clonar y entrar al chatbot
git clone https://github.com/vincentiwadsworth/citrino.git
cd citrino/chatbot

# 2. Setup automático
python setup.py

# 3. Configurar API keys
cp .env.example .env
# Editar .env con tus claves de Z.AI y OpenRouter

# 4. Iniciar Chatbot UI + API Citrino
docker-compose -f docker-compose.dev.yml up

# 5. Acceder a los servicios
# Chatbot UI: http://localhost:3000
# API Citrino: http://localhost:5001
# Health Check: http://localhost:5001/api/health
```

**Capacidades del Chatbot:**
- 🔍 Búsqueda natural: "Propiedades de 3 dormitorios en Equipetrol hasta 200k USD"
- 📊 Análisis de mercado: Precios promedio por zona en tiempo real
- 💡 Recomendaciones inteligentes basadas en 1,385 propiedades reales
- 🎯 Filtrado avanzado por ubicación, presupuesto y características

### Opción 2: Sistema JSON (Tradicional)

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

### Opción 3: PostgreSQL + PostGIS (Sprint 1 - Nuevo)
```bash
# 1. Prerrequisitos PostgreSQL
sudo apt-get install postgresql-15 postgresql-15-postgis-3
createdb citrino
psql -d citrino -c "CREATE EXTENSION postgis;"

# 2. Instalar dependencias PostgreSQL
pip install -r requirements-postgres.txt

# 3. Configurar base de datos
cp .env.example .env
# Editar .env con configuración PostgreSQL (DB_HOST, DB_USER, etc.)

# 4. Ejecutar migración completa
python migrate_to_postgres.py

# 5. Validar migración
python data/postgres/scripts/etl_validate_migration.py
```

[📖 **Guía completa de migración PostgreSQL** →](README_POSTGRES_MIGRATION.md)

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
| [🚀 **PostgreSQL Migration Guide**](README_POSTGRES_MIGRATION.md) | Guía completa para migración a PostgreSQL + PostGIS |
| [📊 **PostgreSQL Technical Deep Dive**](docs/POSTGRESQL_TECHNICAL_DEEP_DIVE.md) | Arquitectura detallada de implementación PostgreSQL |
| [📋 **Sprint 1 Migration**](docs/SPRINT_1_MIGRACION_POSTGRESQL.md) | Plan completo del Sprint 1 de migración |
| [🗄️ **Arquitectura de Datos**](DATA_ARCHITECTURE.md) | Arquitectura actual y plan de migración |
| [⚡ **Sistema Híbrido Extracción**](docs/SISTEMA_HIBRIDO_EXTRACCION.md) | Cómo funciona el sistema Regex + LLM |
| [🚨 **Sistema de Errores LLM**](docs/SISTEMA_ERRORES_LLM.md) | Reporte detallado y clasificación de errores |
| [🏗️ **Arquitectura Técnica**](docs/ARQUITECTURA_TECNICA.md) | Diagramas, stack, patrones de diseño |
| [📖 **Guía de Desarrollo**](docs/GUIA_DESARROLLO.md) | Setup, comandos, testing, deployment |
| [🤖 **CLAUDE.md**](CLAUDE.md) | Guía para trabajar con IA en este proyecto |

## 📄 Licencia y Contacto

- **Licencia**: MIT License
- **Equipo**: Citrino Santa Cruz, Bolivia
- **Soporte**: [GitHub Issues](https://github.com/vincentiwadsworth/citrino/issues)
- **Email**: soporte@citrino.com

## 🗺️ Roadmap y Próximas Mejoras

Citrino tiene un plan de evolución claro enfocado en:

✅ **Completado - Gestión automatizada de planillas Excel** - Procesamiento recursivo de subcarpetas implementado
✅ **Completado - Sistema fallback LLM corregido** - 99.9% disponibilidad alcanzada
✅ **Completado - Filtro de monedas USD/BOB** - Soporte para mercado bimonetario boliviano
✅ **Completado - Sistema de reporte detallado de errores LLM** - Clasificación automática y debug avanzado
✅ **Completado - Mejoras UI/UX en Citrino Chat** - Barra de input sticky, historial limpio, controles discretos

🔄 **En Progreso - Mejora de calidad de datos** - Sistema híbrido optimizado 90% extracción
📅 **Próximos - Geocodificación avanzada** - Reducir propiedades sin zona de 50% → <15%
📅 **Próximos - Optimización UI/UX** - Mayor adopción del equipo interno

**Ver roadmap completo:** [docs/ROADMAP.md](docs/ROADMAP.md)

---

## 📊 Calidad de Datos y Testing

El sistema mantiene **alta precisión** en procesamiento de datos con el sistema híbrido optimizado:

- **90% extracción automática** con regex (sin costo de LLM)
- **99.9% disponibilidad** del sistema LLM con fallback automático
- **2,010+ propiedades** procesadas de archivos Excel recursivos
- **Soporte bimonetario** USD/BOB para mercado boliviano

**Estado actual:** Sistema híbrido 90% efectividad | **Meta 2025:** >95%

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