# 🤖 Citrino Chatbot UI

Interfaz conversacional profesional para el sistema inmobiliario Citrino, basada en Chatbot UI con integración OpenAI-compatible.

##  Overview

Citrino Chatbot UI proporciona una experiencia de chat conversacional moderna para interactuar con el sistema de análisis de propiedades de Santa Cruz de la Sierra. La interfaz es compatible con la API estándar de OpenAI y permite:

- **Búsqueda natural de propiedades**
- **Análisis de mercado en tiempo real**
- **Recomendaciones personalizadas**
- **Integración con LLM (Z.AI + OpenRouter)**
- **Historial de conversaciones**
- **Exportación de resultados**

##  Quick Start

### Prerrequisitos

- Docker y Docker Compose instalados
- API keys de Z.AI (opcional pero recomendado)
- Archivos de datos procesados del Commit 1

### Instalación

1. **Clonar y navegar al directorio del chatbot:**
```bash
cd chatbot
```

2. **Ejecutar el script de setup:**
```bash
python setup.py
```

3. **Configurar variables de entorno:**
```bash
# Copiar template
cp .env.example .env

# Editar .env con tus API keys
nano .env
```

4. **Iniciar los servicios:**
```bash
docker-compose -f docker-compose.dev.yml up
```

5. **Acceder al chatbot:**
- **Chatbot UI**: http://localhost:3000
- **API Citrino**: http://localhost:5001
- **Health Check**: http://localhost:5001/api/health

##  Configuración

### Variables de Entorno

Configura estas variables en el archivo `.env`:

```bash
# Z.AI (proveedor primario)
ZAI_API_KEY=tu_clave_zai_aqui
LLM_PROVIDER=zai
LLM_MODEL=glm-4.6

# OpenRouter (fallback)
OPENROUTER_API_KEY=tu_clave_openrouter_aqui
OPENROUTER_MODEL=qwen/qwen-2.5-72b-instruct:free

# Chatbot UI
OPENAI_API_BASE_URL=http://localhost:5001/v1
DEFAULT_MODEL=citrino-v1
```

### Personalización

El comportamiento del chatbot se configura en `config/chatbot-ui.json`:

- **System Prompt**: Personaliza el comportamiento del asistente
- **Welcome Message**: Mensaje de bienvenida para usuarios
- **Examples**: Ejemplos de consultas predefinidas
- **Branding**: Colores y apariencia personalizada

##  Capacidades

### Búsqueda de Propiedades

El chatbot puede entender consultas naturales como:

```
"Busca casas de 3 dormitorios en Equipetrol hasta 200.000 USD"
"Muestrame departamentos con potencial de renta en zona norte"
"Propiedades cerca de colegios y hospitales en Santa Mónica"
```

### Análisis de Mercado

```
"¿Cuál es el precio promedio por metro cuadrado en Urbari?"
"¿Cuáles son las zonas con más propiedades disponibles?"
"Tendencias del mercado inmobiliario en Santa Cruz"
```

### Recomendaciones Inteligentes

El sistema utiliza el motor de recomendaciones de Citrino para:

- **Análisis de compatibilidad** basado en perfil del usuario
- **Cálculo de distancias** a servicios importantes
- **Evaluación de potencial de plusvalía**
- **Justificación personalizada** de cada recomendación

##  Arquitectura

```

   Chatbot UI       
   (Frontend)      
  Port: 3000       
  
                    
                    
        
      Citrino        
      API            
      (Backend)       
      Port: 5001     
        
                    
                    
        
      Data           
      Processing    
      Layer          
        
```

### Componentes Principales

- **Chatbot UI**: Interfaz frontend basada en Chatbot UI
- **API Server**: Servidor Flask con endpoints OpenAI-compatible
- **LLM Integration**: Sistema híbrido Z.AI + OpenRouter
- **Recommendation Engine**: Motor de recomendaciones geoespaciales
- **Data Layer**: Acceso a 1,385 propiedades procesadas

##  API Endpoints

### Endpoints OpenAI-Compatible

- `POST /v1/chat/completions` - Chat completions
- `GET /v1/models` - Listar modelos disponibles
- `GET /v1/models/{model}` - Información de modelo específico

### Endpoints Citrino

- `GET /api/health` - Health check de la API
- `POST /api/recomendar-mejorado` - Recomendaciones avanzadas
- `GET /api/estadisticas` - Estadísticas del sistema
- `GET /api/zonas` - Lista de zonas disponibles

##  Datos Procesados (Commit 1)

### Estadísticas de Extracción

- **Total propiedades procesadas**: 1,385
- **Proveedores**: 5 diferentes fuentes de datos
- **Agentes únicos**: 79 identificados
- **Uso de LLM**: 1,593 propiedades evaluadas

### Eficiencia del Sistema Híbrido

- **Regex-only**: 601 propiedades (37.7%) - Sin costo LLM
- **Regex+LLM**: 992 propiedades (62.3%) - Con optimización
- **LLM-only**: 0 propiedades - Sistema eficiente
- **Costo total**: $0.002 USD (muy optimizado)

### Distribución por Proveedor

| Proveedor | Propiedades | Características |
|-----------|-------------|-----------------|
| 02 | 968 | Datos en texto libre, requiere LLM |
| 01 | 181 | Agentes identificados, datos estructurados |
| 04 | 119 | Calidad variable |
| 05 | 98 | Datos estructurados |
| 03 | 19 | Volumen bajo |

##  Casos de Uso

### Para Inversores

1. **Búsqueda de oportunidades**: "Buscar propiedades con alto potencial de plusvalía"
2. **Análisis de zonas**: "Comparar rentabilidad entre Equipetrol y Urbari"
3. **Evaluación de riesgos**: "¿Qué factores considerar para inversión inmobiliar?"

### Para Agentes

1. **Atención a clientes**: "Propiedades para familias con 2 hijos en zona norte"
2. **Presentaciones**: "Preparar portafolio para reunión con prospecto"
3. **Seguimiento**: "Generar briefing de visita para 3 propiedades seleccionadas"

### Para Analistas

1. **Estudios de mercado**: "Tendencias de precios por zona en los últimos 6 meses"
2. **Cobertura de servicios**: "Análisis de disponibilidad de colegios y hospitales"
3. **Proyecciones**: "Modelar crecimiento de valores por zona"

##  Integración de Datos

El chatbot tiene acceso a:

- **Base de datos principal**: 1,385 propiedades actualizadas
- **Sistema de recomendaciones**: Motor con algoritmos de matching
- **Análisis geoespacial**: Cálculo de distancias y cobertura
- **Inteligencia artificial**: Sistema híbrido Regex + LLM

### Fuentes de Datos

1. **Scraping Citrino**: 7 archivos Excel con relevamiento
2. **Agentes identificados**: 79 profesionales activos
3. **Servicios urbanos**: 4,777 servicios municipales (integración futura)
4. **Datos georreferenciados**: Coordenadas y análisis espacial

##  Solución de Problemas

### Problemas Comunes

**Docker no se inicia:**
```bash
# Verificar instalación
docker --version
docker-compose --version

# Reinstalar si es necesario
# Seguir documentación oficial de Docker
```

**Error 404 en API:**
```bash
# Verificar que el API esté corriendo
curl http://localhost:5001/api/health

# Revisar logs del contenedor
docker-compose logs citrino-api
```

**No se conecta a LLM:**
```bash
# Verificar configuración en .env
cat .env | grep -E "(ZAI_API_KEY|OPENROUTER_API_KEY)"

# Test de conexión directa
python -c "
import sys
sys.path.append('..')
from src.llm_integration import LLMIntegration, LLMConfig
llm = LLMIntegration(LLMConfig(
    provider='zai',
    api_key='tu_key_aqui',
    model='glm-4.6'
))
print(llm.consultar('Test de conexión'))
"
```

**Chatbot UI no carga:**
```bash
# Limpiar caché de Docker
docker-compose down
docker system prune -f
docker-compose -f docker-compose.dev.yml up --build
```

### Debug Mode

Para habilitar logging detallado:

```bash
# Agregar a docker-compose.dev.yml
environment:
  - FLASK_ENV=development
  - LOG_LEVEL=DEBUG
```

##  Monitoreo

### Logs del Sistema

- **API Server**: `docker-compose logs citrino-api`
- **Chatbot UI**: `docker-compose logs chatbot-ui`
- **Base de datos**: Logs integrados en la API

### Métricas Disponibles

- **Uso de LLM**: Tokens consumidos por proveedor
- **Cache hits**: Eficiencia del sistema de caché
- **Queries procesadas**: Número de consultas exitosas
- **Tiempo de respuesta**: Latencia promedio por endpoint

##  Actualizaciones

### Para actualizar el sistema:

1. **Actualizar código fuente:**
```bash
# Desde directorio raíz
git pull origin main
```

2. **Actualizar imágenes Docker:**
```bash
# Desde directorio chatbot
docker-compose down
docker-compose pull
docker-compose up --build
```

3. **Reprocesar datos:**
```bash
# Desde directorio raíz
python scripts/analysis/procesar_y_analizar_raw.py
```

## 🤝 Contribución

### Flujo de Desarrollo

1. **Crear feature branch**: `git checkout -b feature/nueva-funcionalidad`
2. **Desarcar cambios**: Realizar commits descriptivos
3. **Testing**: Probar con datos de muestra
4. **Pull Request**: Abrir PR para revisión

### Estándares de Código

- **Python**: PEP 8, type hints obligatorios
- **JavaScript**: ES6+, módulos con import/export
- **Docker**: Multi-stage builds optimizados
- **Documentación**: Markdown con ejemplos claros

##  Soporte

### Para ayuda técnica:

1. **Revisar logs** del sistema
2. **Consultar documentación** en `docs/`
3. **Verificar issues** conocidos en GitHub
4. **Contactar al equipo** de desarrollo

### Comandos Útiles

```bash
# Verificar estado de todos los servicios
docker-compose ps

# Reiniciar servicios específicos
docker-compose restart citrino-api

# Verificar recursos utilizados
docker stats

# Acceder a logs en tiempo real
docker-compose logs -f citrino-api
```

##  Documentación Adicional

- **API Reference**: Documentación completa de endpoints
- **Architecture Guide**: Detalles técnicos del sistema
- **Migration Guide**: Guía para PostgreSQL + PostGIS
- **Data Analysis**: Scripts para análisis de datos

##  Licencia

Este proyecto está licenciado bajo los términos de la Licencia MIT. Ver archivo `LICENSE` para más detalles.

---

**Citrino Chatbot UI** - Transformando la búsqueda inmobiliar con inteligencia conversacional.