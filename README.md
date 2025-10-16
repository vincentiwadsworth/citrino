#  Citrino - Plataforma de Inteligencia de Inversión Inmobiliaria

> **Herramienta interna de Citrino para análisis inteligente de propiedades de inversión en Santa Cruz de la Sierra, Bolivia**

Citrino es el sistema interno que ayuda al equipo de Citrino a tomar mejores decisiones de inversión para sus clientes mediante análisis automático de propiedades y recomendaciones inteligentes basadas en datos de mercado.

##  ¿Cómo Funciona Citrino?

### 1. **Relevamiento de Datos**
El equipo de Citrino recopila información de propiedades exclusivamente en archivos Excel RAW ubicados en `data/raw/`. Estos archivos son la ÚNICA fuente de datos original del sistema.

### 2. **Validación y Procesamiento**
Los archivos Excel RAW pasan por un proceso de validación estructurado:

- ** Validación Individual**: Cada archivo se procesa individualmente generando archivos intermedios
- **🤖 Revisión Humana**: El equipo Citrino valida manualmente los datos procesados
- ** Control de Calidad**: Generación de reportes de calidad y métricas de validación

### 3. **Migración a PostgreSQL**
Una vez validados, los datos se migran a PostgreSQL con PostGIS:

- **Base de Datos Principal**: PostgreSQL con coordenadas geoespaciales PostGIS
- **Motor de Recomendación**: Consultas optimizadas con índices espaciales
- **API REST**: Datos disponibles para aplicaciones via endpoints

### 4. **Análisis y Recomendaciones**
El sistema proporciona:

- **Búsquedas Geoespaciales**: Consultas por radio y ubicación precisa
- **Recomendaciones Inteligentes**: Evaluación según criterios de inversión
- **Panel de Consulta**: Interface para explorar resultados con filtros avanzados

##  Ventajas para el Equipo Citrino

- ** Decisions Informadas**: Análisis objetivo basado en datos estructurados
- ** Procesamiento Rápido**: Automatización que ahorra horas de trabajo manual
- ** Análisis Geográfico**: Evaluación precisa de ubicaciones y servicios cercanos
- ** Recomendaciones Inteligentes**: Sistema que aprende de los criterios del equipo
- ** Calidad de Datos**: Validación automática y reportes de control

##  Datos del Sistema

### Información Procesada
- **1,578 propiedades** analizadas y estructuradas
- **4,777 servicios urbanos** mapeados en Santa Cruz
- **50+ zonas** con cobertura geográfica detallada
- **5 proveedores** de datos con diferentes estrategias de procesamiento

### Tecnologías Aplicadas
- **Procesamiento**: Python con Pandas para manejo eficiente de datos Excel
- **Inteligencia Artificial**: Modelos de lenguaje para extracción avanzada
- **Análisis Geográfico**: PostgreSQL + PostGIS para consultas geoespaciales optimizadas
- **Interfaz Web**: HTML5 con Bootstrap para acceso multi-dispositivo
- **Base de Datos**: PostgreSQL con PostGIS (base de datos principal)

### Eficiencia del Sistema
- **Procesamiento Excel RAW** directo desde archivos originales
- **Validación estructurada** con archivos intermedios para revisión humana
- **Migración automática** a PostgreSQL con PostGIS
- **Consultas optimizadas** con índices espaciales (milisegundos)

##  Características Principales

### 🤖 Inteligencia Artificial para Inversores
- **Motor de recomendación especializado** en análisis de oportunidades
- **Factores de evaluación** basados en potencial de la zona
- **Análisis de ubicación** mediante coordenadas precisas
- **Filtros por Unidad Vecinal y Manzana** para segmentación detallada

###  Geolocalización para Inversión
- **Fórmula de Haversine** para cálculo de distancias reales
- **Índice espacial** para búsquedas optimizadas por zona
- **Coordenadas exactas** para propiedades de relevamiento
- **Filtros UV/Manzana** para análisis por ubicación precisa
- **Cálculo de proximidad** a servicios que impactan plusvalía

###  Experiencias Asistidas con IA
- **🤖 Chatbot UI Profesional** - Interfaz conversacional con búsqueda natural de propiedades
- **Citrino Reco** centraliza notas de exploración y devuelve recomendaciones al instante
- **Citrino Chat** permite "chatear con la información" sin restricciones temáticas
- **Extracción automática de criterios** desde conversaciones y formularios
- **Arquitectura preparada** con sistema LLM redundante y alta disponibilidad

###  Panel de Inversor
- **Diseño responsive** para visualización de propiedades
- **Bootstrap 5** con componentes funcionales
- **Filtros avanzados** por zona, precio y características
- **Comparativas detalladas** de propiedades seleccionadas

##  Tecnologías y Arquitectura

### Stack Principal

| Capa | Tecnologías | Propósito |
|------|-------------|-----------|
| **Frontend** | HTML5, Bootstrap 5, JavaScript ES6+ | Interfaz responsive y moderna |
| **Backend** | Python 3.8+, Flask 2.3.3 | REST API para análisis |
| **Base de Datos** | PostgreSQL + PostGIS | Almacenamiento geoespacial optimizado |
| **ETL** | Python, Pandas, openpyxl | Procesamiento archivos Excel RAW |
| **IA** | Modelos de lenguaje avanzados | Extracción y análisis inteligente |

### Componentes del Sistema

```
     HTTP/REST     
  Frontend    ←→   API Flask   
  (3 apps)                        (Backend)   
                   
                                         
                               
                                                  
                                
                           Motores           LLM      
                            Reco          Integration 
                                
                                
                          
                           PostgreSQL 
                           + PostGIS  
                          
                                ↑
                        
                         Excel RAW     
                         data/raw/     
                        
```

##  Instalación Rápida (5 minutos)

### Opción 1: Sistema Principal

```bash
# 1. Clonar y entrar
git clone https://github.com/vincentiwadsworth/citrino.git
cd citrino

# 2. Instalar dependencias
pip install -r requirements_api.txt

# 3. Configurar API keys
cp .env.example .env
# Editar .env con tus claves de LLM

# 4. Iniciar backend
python api/server.py  # API en http://localhost:5000

# 5. Iniciar frontend (nueva terminal)
python -m http.server 8080  # UI en http://localhost:8080
```

### Opción 2: Chatbot UI Profesional

```bash
# 1. Clonar y entrar al chatbot
git clone https://github.com/vincentiwadsworth/citrino.git
cd citrino/chatbot

# 2. Setup automático
python setup.py

# 3. Configurar API keys
cp .env.example .env
# Editar .env con tus claves

# 4. Iniciar Chatbot UI + API
docker-compose -f docker-compose.dev.yml up

# 5. Acceder a los servicios
# Chatbot UI: http://localhost:3000
# API Citrino: http://localhost:5001
```

**Producción:** Frontend en [GitHub Pages](https://vincentiwadsworth.github.io/citrino/)

##  Uso del Sistema

### Flujo Principal de Usuario

1. **Inicio** → `index.html`
   - Explora las características del sistema
   - Elige entre "Crear Perfil" o "Asistente Virtual"

2. **Citrino Reco** → `citrino-reco.html`
   - Registra notas de exploración sin exponer datos sensibles
   - Define presupuestos, zonas y contexto de negocio
   - Obtén recomendaciones inline y exporta JSON

3. **Citrino Chat** → `chat.html`
   - Consulta el inventario, la guía urbana y el censo inmobiliario
   - Cruza datasets, genera insights conversacionales
   - Visualiza recomendaciones dentro del chat

###  Ejemplos de Uso

```
• "Propiedades en zonas de alto desarrollo urbano"
• "Inversión entre $150K-$300K con potencial de plusvalía"
• "Terrenos en áreas de expansión"
• "Departamentos cerca de zonas comerciales"
```

## 🤖 Inteligencia Artificial y Análisis

### Sistema de Recomendación Inteligente

Citrino utiliza un **motor de scoring multicritero** que evalúa cada propiedad según:

| Factor | Peso | Qué evalúa |
|--------|------|------------|
|  Ubicación | 35% | Distancia a zonas preferidas, accesos |
|  Precio | 25% | Ajuste al presupuesto del cliente |
|  Servicios | 20% | Proximidad a escuelas, hospitales, comercios |
|  Características | 15% | Habitaciones, baños, amenities |
|  Disponibilidad | 5% | Estado actual en el mercado |

### Integración con Modelos de Lenguaje

**Flujo de Datos ETL**
-  **Excel RAW** como única fuente de datos (data/raw/)
-  **Validación estructurada** con archivos intermedios
-  **Migración automática** a PostgreSQL + PostGIS
-  **Consultas optimizadas** con índices espaciales (milisegundos)

##   Documentación

| Documento | Descripción |
|-----------|-------------|
| [ **PostgreSQL Migration Guide**](README_POSTGRES_MIGRATION.md) | Guía completa para migración a PostgreSQL + PostGIS |
| [ **PostgreSQL Technical Deep Dive**](docs/POSTGRESQL_TECHNICAL_DEEP_DIVE.md) | Arquitectura detallada de implementación PostgreSQL |
| [ **Arquitectura de Datos**](DATA_ARCHITECTURE.md) | Arquitectura actual y plan de migración |
| [ **Reporte Mejoras ETL**](docs/REPORTE_MEJORAS_ETL.md) | Análisis completo y optimización ETL avanzada |
| [ **Sistema Híbrido Extracción**](docs/SISTEMA_HIBRIDO_EXTRACCION.md) | Cómo funciona el sistema Regex + LLM |
| [ **Arquitectura Técnica**](docs/ARQUITECTURA_TECNICA.md) | Diagramas, stack, patrones de diseño |
| [ **Guía de Desarrollo**](docs/GUIA_DESARROLLO.md) | Setup, comandos, testing, deployment |
| [🤖 **CLAUDE.md**](CLAUDE.md) | Guía para trabajar con IA en este proyecto |
| [ **Changelog**](docs/CHANGELOG.md) | Historial completo de cambios y versiones |

##  Licencia y Contacto

- **Licencia**: MIT License
- **Equipo**: Citrino Santa Cruz, Bolivia
- **Soporte**: [GitHub Issues](https://github.com/vincentiwadsworth/citrino/issues)
- **Email**: soporte@citrino.com

##  Roadmap y Próximas Mejoras

Citrino tiene un plan de evolución claro enfocado en:

 **En Progreso - Excel RAW a PostgreSQL** - Migración completa a base de datos relacional
 **Próximos - Validación mejorada** - Sistema automatizado de control de calidad
 **Próximos - Consultas avanzadas** - Análisis geoespacial en tiempo real

**Ver roadmap completo:** [docs/ROADMAP.md](docs/ROADMAP.md)

---

##  Stack Tecnológico

- **Backend:** Python 3.8+, Flask 2.3.3, Pandas, NumPy
- **Frontend:** HTML5, Bootstrap 5, JavaScript ES6+
- **Base de Datos:** PostgreSQL + PostGIS (almacenamiento geoespacial)
- **ETL:** Python, openpyxl (procesamiento archivos Excel RAW)
- **IA:** Modelos de lenguaje avanzados con sistema redundante
- **Algoritmos:** Índices espaciales PostGIS, Weighted Scoring, Regex Patterns

**Ver arquitectura completa:** [docs/ARQUITECTURA_TECNICA.md](docs/ARQUITECTURA_TECNICA.md)

---

##  Contacto y Soporte

**Proyecto interno de Citrino** - Santa Cruz de la Sierra, Bolivia

- **Equipo de Desarrollo**: Vincenti Wadsworth y equipo técnico Citrino
- **Soporte Interno**: Reportar issues en el repositorio
- **Email**: soporte@citrino.com

---

**Herramienta profesional desarrollada para Citrino**