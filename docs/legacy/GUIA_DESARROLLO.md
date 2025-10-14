# 👨‍💻 Guía de Desarrollo para Citrino

## 🚀 Inicio Rápido

### Instalación en 5 Minutos

```bash
# 1. Clonar repositorio
git clone https://github.com/vincentiwadsworth/citrino.git
cd citrino

# 2. Instalar dependencias Python
pip install -r requirements_api.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus API keys

# 4. Iniciar servidor
python api/server.py

# 5. Abrir frontend
python -m http.server 8080
# Navegar a http://localhost:8080
```

## 📁 Estructura del Proyecto

```
citrino/
├── api/                    # Backend REST API
│   └── server.py          # Servidor Flask
├── src/                    # Lógica de negocio
│   ├── recommendation_engine.py
│   ├── recommendation_engine_mejorado.py
│   ├── llm_integration.py
│   ├── description_parser.py
│   └── regex_extractor.py
├── scripts/                # ETL y utilidades
│   ├── build_relevamiento_dataset.py
│   ├── test_regex_vs_llm.py
│   └── analizar_descripciones_p02.py
├── tests/                  # Suite de pruebas
│   ├── test_api.py
│   ├── test_fallback_simple.py
│   └── test_zai_integration.py
├── data/                   # Datos del sistema
│   ├── raw/               # Excel de proveedores
│   └── base_datos_relevamiento.json
├── docs/                   # Documentación técnica
│   ├── SISTEMA_HIBRIDO_EXTRACCION.md
│   ├── ARQUITECTURA_TECNICA.md
│   └── historico/         # Docs archivados
├── assets/                 # Frontend assets
│   ├── css/
│   └── js/
├── index.html             # Landing page
├── citrino-reco.html      # Recomendaciones
├── chat.html              # Asistente virtual
└── README.md              # Este archivo
```

## 🛠️ Comandos de Desarrollo

### Backend

```bash
# Iniciar servidor de desarrollo
python api/server.py

# Ejecutar tests
pytest                              # Todos los tests
pytest tests/test_api.py -v        # Tests de API
pytest -k "llm"                    # Solo tests de LLM

# Regenerar datos
python scripts/build_relevamiento_dataset.py
python scripts/build_urban_services_dataset.py

# Análisis de datos
python scripts/analizar_descripciones_p02.py
python scripts/test_regex_vs_llm.py
```

### Frontend

```bash
# Servidor local simple
python -m http.server 8080

# Con live reload (necesita npm)
npm install -g live-server
live-server --port=8080
```

## 🔧 Configuración de Entorno

### Archivo .env

```bash
# === LLM Configuration ===
# Z.AI (Primary)
ZAI_API_KEY=tu_clave_zai
LLM_PROVIDER=zai
LLM_MODEL=glm-4.6
LLM_MAX_TOKENS=8000
LLM_TEMPERATURE=0.1

# OpenRouter (Fallback)
OPENROUTER_FALLBACK_ENABLED=true
OPENROUTER_API_KEY=tu_clave_openrouter
OPENROUTER_MODEL=qwen/qwen-2.5-72b-instruct:free

# === Flask Configuration ===
FLASK_ENV=development
FLASK_DEBUG=true
FLASK_PORT=5000

# === Data Configuration ===
DATA_PATH=./data
CACHE_ENABLED=true
```

### Obtener API Keys

**Z.AI (Primario):**
1. Regístrate en https://z.ai
2. Ve a Dashboard → API Keys
3. Crea nueva key y copia

**OpenRouter (Fallback - Gratis):**
1. Regístrate en https://openrouter.ai
2. Ve a Keys
3. Crea key (no requiere tarjeta)

## 💻 Desarrollo de Funcionalidades

### Agregar Nuevo Endpoint de API

```python
# api/server.py

@app.route('/api/mi-nuevo-endpoint', methods=['POST'])
def mi_nuevo_endpoint():
    """Descripción del endpoint."""
    try:
        # 1. Validar request
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # 2. Procesar lógica
        resultado = procesar_algo(data)
        
        # 3. Retornar respuesta
        return jsonify({
            'success': True,
            'data': resultado
        }), 200
        
    except Exception as e:
        logger.error(f"Error en endpoint: {e}")
        return jsonify({'error': str(e)}), 500
```

### Agregar Nuevo Patrón Regex

```python
# src/regex_extractor.py

class RegexExtractor:
    def __init__(self):
        # Agregar nuevo patrón
        self.mi_patron = re.compile(
            r'patrón_regex_aquí',
            re.IGNORECASE
        )
    
    def extract_nuevo_campo(self, texto):
        """Extrae nuevo campo del texto."""
        match = self.mi_patron.search(texto)
        if match:
            return match.group(1)
        return None
```

### Modificar Pesos del Motor de Recomendación

```python
# src/recommendation_engine_mejorado.py

# Ajustar pesos según necesidades de negocio
WEIGHTS = {
    'ubicacion': 0.40,      # Aumentar peso de ubicación
    'precio': 0.20,         # Reducir peso de precio
    'servicios': 0.20,      # Mantener
    'caracteristicas': 0.15, # Mantener
    'disponibilidad': 0.05   # Mantener
}
```

## 🧪 Testing

### Escribir Tests

```python
# tests/test_mi_funcionalidad.py

import pytest
from src.mi_modulo import mi_funcion

def test_mi_funcion_caso_basico():
    """Test de caso básico."""
    resultado = mi_funcion("input")
    assert resultado == "output_esperado"

def test_mi_funcion_caso_error():
    """Test de manejo de errores."""
    with pytest.raises(ValueError):
        mi_funcion(None)

@pytest.mark.parametrize("input,expected", [
    ("caso1", "resultado1"),
    ("caso2", "resultado2"),
])
def test_mi_funcion_multiples_casos(input, expected):
    """Test con múltiples casos."""
    assert mi_funcion(input) == expected
```

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Con verbosidad
pytest -v

# Con coverage
pytest --cov=src --cov-report=html

# Solo tests marcados
pytest -m "not slow"
```

## 📊 Debugging

### Logs del Backend

```python
import logging

# Configurar logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Usar en código
logger.debug("Información detallada")
logger.info("Información general")
logger.warning("Advertencia")
logger.error("Error")
```

### Debug en Frontend

```javascript
// Activar modo debug
localStorage.setItem('debug', 'true');

// Ver logs
console.log('Estado:', data);
console.table(propiedades);

// Breakpoints en DevTools
debugger; // Pausa ejecución aquí
```

### Problemas Comunes

**API no responde:**
```bash
# Verificar puerto ocupado
netstat -ano | findstr :5000

# Matar proceso
taskkill /PID <numero> /F
```

**CORS errors:**
```python
# api/server.py
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Solo desarrollo
```

**Import errors:**
```bash
# Verificar PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## 🎨 Convenciones de Código

### Python (PEP 8)

```python
# Nombres de variables: snake_case
mi_variable = 10
nombre_completo = "Juan Pérez"

# Nombres de clases: PascalCase
class MiClase:
    pass

# Constantes: UPPER_CASE
MAX_PROPIEDADES = 1000
API_URL = "https://api.example.com"

# Type hints
def procesar_propiedad(
    titulo: str,
    precio: float,
    zona: Optional[str] = None
) -> Dict[str, Any]:
    """Procesa una propiedad.
    
    Args:
        titulo: Título de la propiedad
        precio: Precio en USD
        zona: Zona opcional
        
    Returns:
        Diccionario con datos procesados
    """
    return {"titulo": titulo, "precio": precio}
```

### JavaScript (ES6+)

```javascript
// Variables: camelCase
const miVariable = 10;
let nombreCompleto = "Juan Pérez";

// Constantes: UPPER_CASE
const MAX_PROPIEDADES = 1000;
const API_URL = "https://api.example.com";

// Funciones: camelCase
function procesarPropiedad(titulo, precio, zona = null) {
    return { titulo, precio, zona };
}

// Arrow functions
const calcularScore = (prop) => prop.precio * 0.8;

// Async/await
async function obtenerPropiedades() {
    try {
        const response = await fetch('/api/search');
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error:', error);
    }
}
```

## 📝 Git Workflow

### Branches

```bash
# Crear feature branch
git checkout -b feature/nombre-feature

# Trabajar en cambios
git add .
git commit -m "feat: agregar nueva funcionalidad"

# Push y crear PR
git push origin feature/nombre-feature
```

### Commits Semánticos

```
feat: nueva funcionalidad
fix: corrección de bug
docs: cambios en documentación
style: formato, espacios (no afecta código)
refactor: refactorización de código
test: agregar o modificar tests
chore: tareas de mantenimiento
```

### Pre-commit Checklist

- [ ] Tests pasan (`pytest`)
- [ ] Código formateado (PEP 8)
- [ ] Documentación actualizada
- [ ] Sin credenciales hardcoded
- [ ] Commit message descriptivo

## 🚢 Deployment

### Deploy a Render.com

```bash
# 1. Conectar repositorio en Render.com
# 2. Configurar variables de entorno
# 3. Deploy automático en push a main
```

### Deploy Frontend a GitHub Pages

```bash
# Ya configurado - auto-deploy en push
git push origin main
# Esperar ~2 minutos
# Ver en: https://vincentiwadsworth.github.io/citrino/
```

## 📚 Recursos

### Documentación Interna
- [Sistema Híbrido Extracción](./SISTEMA_HIBRIDO_EXTRACCION.md)
- [Arquitectura Técnica](./ARQUITECTURA_TECNICA.md)
- [CLAUDE.md](../CLAUDE.md) - Guía para IA

### Referencias Externas
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Bootstrap 5](https://getbootstrap.com/docs/5.3/)
- [Z.AI API](https://z.ai/docs)
- [OpenRouter API](https://openrouter.ai/docs)

## 🤝 Contribuir

### Reportar Bugs

1. Verificar que no existe issue similar
2. Crear issue con template
3. Incluir:
   - Descripción del problema
   - Pasos para reproducir
   - Comportamiento esperado vs actual
   - Screenshots/logs si aplica

### Proponer Funcionalidades

1. Abrir Discussion en GitHub
2. Describir caso de uso
3. Recibir feedback del equipo
4. Si aprobado, crear issue + PR

---

**¿Preguntas? Abre un issue o contacta al equipo de desarrollo**
