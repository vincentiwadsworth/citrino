# Sistema de Prompts y Restricciones LLM - Citrino

Documentación completa del sistema de prompts, restricciones y configuraciones para controlar el comportamiento de los modelos de lenguaje en Citrino.

##  Overview

El sistema de prompts de Citrino está diseñado para:

- **Reducir alucinaciones** mediante restricciones estrictas
- **Limitar respuestas** a datos existentes en la base de datos
- **Controlar temperatura** para mantener consistencia
- **Validar información** en tiempo real
- **Prevenir especulaciones** y promesas irreales

##  Estructura de Archivos

```
src/prompts/
 system_prompt_chat.py        # System prompts para Citrino Chat
 system_prompt_reco.py        # System prompts para Citrino Reco
 llm_config.py               # Configuración centralizada de LLM
 data_restrictions.py        # Restricciones de datos y fuentes
 README.md                   # Esta documentación
```

##  Configuración de Temperatura

### Temperatura Ultra-Baja: 0.05 - 0.1
- **Chat**: 0.05 (máxima consistencia)
- **Reco**: 0.1 (consistencia con cálculos)
- **Propósito**: Respuestas predecibles y basadas en datos

### Límites de Tokens
- **Chat**: 250 tokens máximo (respuestas breves)
- **Reco**: 400 tokens máximo (recomendaciones detalladas)
- **General**: 300 tokens máximo

##  Restricciones Principales

### 1. Fuentes de Datos Permitidas
```python
ALLOWED_DATA_SOURCES = {
    "primary_database": "base_datos_relevamiento.json",
    "urban_guide": "guia_urbana_municipal_completa.json"
}
```

### 2. Zonas Autorizadas
- **Equipetrol**: $200k - $800k
- **Urbari**: $350k - $1.5M
- **Santa Mónica**: $80k - $400k
- **Las Palmas**: $150k - $600k
- **Santiago**: $100k - $500k
- **Sacta**: $70k - $300k
- **Pampa de la Isla**: $60k - $250k

### 3. Tipos de Propiedad Permitidos
- **Casa**: 60-1000m², 1-6 habitaciones, $50k-$2M
- **Departamento**: 30-300m², 1-4 habitaciones, $50k-$1M
- **Terreno**: 100-5000m², $30k-$2M
- **Duplex**: 80-400m², 2-5 habitaciones, $100k-$1.5M
- **Loft**: 40-200m², 1-2 habitaciones, $80k-$600k

### 4. Palabras Prohibidas
- **Garantías**: "garantizado", "seguro", "100%"
- **Especulación**: "plusvalía garantida", "rentabilidad segura"
- **Subjetividad**: "perfecto", "excelente", "mejor"
- **Presión**: "urgente", "oportunidad única", "no te lo pierdas"

##  System Prompts

### Citrino Chat - Principios Clave

1. **Solo Datos Existentes**: Responder únicamente con información de la BD
2. **Verificación Obligatoria**: Validar cada dato mencionado
3. **Transparencia**: Admitir limitaciones de información
4. **Sin Promesas**: Evitar garantías o predicciones futuras

#### Ejemplo de Prompt:
```python
"Eres un asistente de inversión inmobiliaria especializado para Citrino Bolivia.
Tu función es proporcionar información ÚNICAMENTE basada en los datos existentes
en nuestra base de datos. Si no tienes información, di claramente
'No tengo datos sobre esa consulta'."
```

### Citrino Reco - Principios Clave

1. **Propiedades Reales**: Solo recomendar propiedades existentes
2. **Compatibilidad Calculada**: Fórmula matemática estricta
3. **Justificaciones Basadas en Datos**: Solo características verificables
4. **Límites Estrictos**: Máximo 5 recomendaciones, 60-95% compatibilidad

#### Ejemplo de Prompt:
```python
"Eres el motor de recomendaciones de Citrino Bolivia.
Tu función es generar recomendaciones ÚNICAMENTE basadas en propiedades
existententes en nuestra base de datos. Cada recomendación debe corresponder
a una propiedad real con ID."
```

##  Validación de Datos

### Validación en Tiempo Real
```python
class DataValidator:
    @staticmethod
    def validate_zone(zone_name: str) -> bool
    @staticmethod
    def validate_price(price: float, prop_type: str, zone: str) -> bool
    @staticmethod
    def validate_property_data(property_data: dict) -> dict
```

### Reglas de Validación
- **Campos Requeridos**: id, precio, zona, tipo
- **Rangos Numéricos**: Verificar límites de precios y características
- **Existencia en BD**: Confirmar que los datos existen
- **Consistencia**: Validar relaciones entre datos

##  Configuración LLM

### Parámetros por Componente

#### Chat Configuration
```python
CITRINO_CHAT_LLM_CONFIG = {
    "temperature": 0.05,        # Ultra-baja
    "max_tokens": 250,          # Respuestas breves
    "validate_facts": True,     # Validación activa
    "check_hallucinations": True
}
```

#### Reco Configuration
```python
CITRINO_RECO_LLM_CONFIG = {
    "temperature": 0.1,         # Baja
    "max_tokens": 400,          # Recomendaciones detalladas
    "validate_budget": True,     # Validar presupuesto
    "validate_compatibility": True
}
```

### Seguridad y Control
- **Safe Mode**: Activado por defecto
- **Content Filter**: Filtrado de contenido inapropiado
- **Rate Limiting**: 60 solicitudes por minuto
- **Timeout**: 30 segundos por solicitud

##  Métricas y Monitoreo

### Métricas Clave
- **Response Time**: Tiempo de respuesta (objetivo: <5s)
- **Success Rate**: Tasa de éxito (objetivo: >95%)
- **Hallucination Rate**: Tasa de alucinaciones (objetivo: <5%)
- **Data Accuracy Rate**: Precisión de datos (objetivo: >80%)

### Alertas Automáticas
- **Response Time > 5s**: Alerta de rendimiento
- **Error Rate > 10%**: Alerta de calidad
- **Hallucination Rate > 5%**: Alerta crítica
- **Data Accuracy < 80%**: Alerta de validación

##  Implementación

### Integración con LLM
```python
from src.prompts.llm_config import get_llm_config
from src.prompts.data_restrictions import DataValidator

# Obtener configuración
chat_config = get_llm_config('chat')

# Validar datos
validator = DataValidator()
validation = validator.validate_property_data(property_data)

# Usar solo si la validación es exitosa
if validation['valid']:
    # Procesar con LLM
    pass
```

### Uso en Código
```python
# Para Chat
from src.prompts.system_prompt_chat import CITRINO_CHAT_SYSTEM_PROMPT

# Para Reco
from src.prompts.system_prompt_reco import CITRINO_RECO_SYSTEM_PROMPT

# Para Configuración
from src.prompts.llm_config import get_llm_config
```

##  Guía de Uso Rápido

### 1. Configurar Ambiente
```bash
# Verificar archivos de prompts
ls src/prompts/

# Probar configuración
python src/prompts/llm_config.py
```

### 2. Implementar en LLM
```python
# Importar configuración
from src.prompts.llm_config import get_llm_config

# Obtener config para componente
config = get_llm_config('chat')

# Aplicar a llamada LLM
response = llm_client.chat.completions.create(
    model="glm-4.6",
    messages=[{"role": "system", "content": config["system_prompt"]}],
    temperature=config["temperature"],
    max_tokens=config["max_tokens"]
)
```

### 3. Validar Respuestas
```python
from src.prompts.data_restrictions import DataValidator

validator = DataValidator()
forbidden_words = validator.check_forbidden_words(response.text)
if forbidden_words:
    # Manejar palabras prohibidas
    pass
```

##  Mejoras Futuras

### Planeado
- [ ] Integración con más modelos LLM
- [ ] Sistema de aprendizaje automático para detección de alucinaciones
- [ ] Métricas avanzadas de calidad
- [ ] Sistema de feedback continuo

### Consideraciones
- **Scalability**: Sistema diseñado para escalar horizontalmente
- **Maintainability**: Configuración centralizada y modular
- **Security**: Validación y filtros en múltiples capas
- **Performance**: Optimización para respuestas rápidas

##  Troubleshooting

### Problemas Comunes

#### 1. Alucinaciones Detectadas
**Síntoma**: El sistema detecta datos inventados
**Solución**:
- Reducir temperatura a 0.0
- Reforzar prompts de validación
- Revisar base de datos

#### 2. Respuestas Vacías
**Síntoma**: El LLM no genera respuestas
**Solución**:
- Aumentar max_tokens
- Verificar que la consulta tenga datos en BD
- Revisar prompts demasiado restrictivos

#### 3. Tiempos de Respuesta Lentos
**Síntoma**: Las respuestas tardan más de 5 segundos
**Solución**:
- Reducir max_tokens
- Optimizar validación de datos
- Considerar cache de respuestas

### Debug Mode
```python
# Activar logging detallado
import logging
logging.basicConfig(level=logging.DEBUG)

# Ver configuración
from src.prompts.llm_config import print_config_summary
print_config_summary('chat')
```

##  Soporte

Para problemas con el sistema de prompts:

1. **Revisar logs**: Buscar errores en `logs/llm_errors.log`
2. **Validar configuración**: Usar `python src/prompts/llm_config.py`
3. **Test de validación**: Probar con `python src/prompts/data_restrictions.py`
4. **Documentation**: Revisar esta documentación y comentarios en código

---

**Última actualización**: 9 de Octubre 2025
**Versión**: 1.0.0
**Citrino LLM Prompt System**