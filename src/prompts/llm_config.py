"""
Configuración centralizada de parámetros LLM para Citrino
Control estricto para evitar alucinaciones y limitar a datos existentes
"""

# Configuración general de LLM para Citrino
LLM_GENERAL_CONFIG = {
    # Parámetros de control de temperatura y creatividad
    "temperature": 0.1,           # Muy baja - respuestas consistentes y predecibles
    "top_p": 0.9,                 # Control de diversidad - bajo para mantener consistencia
    "top_k": 20,                  # Limitar opciones consideradas
    "repetition_penalty": 1.1,     # Penalización leve para evitar repeticiones

    # Límites de tokens
    "max_tokens": 300,             # Máximo 300 tokens por respuesta
    "min_tokens": 10,              # Mínimo para respuestas muy cortas
    "presence_penalty": 0.0,       # Sin penalización por nuevos temas
    "frequency_penalty": 0.1,      # Penalización leve por repetición de palabras

    # Parámetros de seguridad
    "safe_mode": True,             # Modo seguro activado
    "filter_content": True,        # Filtrar contenido inapropiado
    "validate_facts": True,        # Validación de hechos activada

    # Control de salida
    "stop_sequences": [
        "¿Necesitas algo más?",
        "¿Te gustaría ver más opciones?",
        "¿Hay algo más en lo que pueda ayudarte?",
        "No dudes en consultarme si tienes más preguntas."
    ],

    # Timeouts y retries
    "timeout": 30,                 # 30 segundos timeout
    "max_retries": 2,              # Máximo 2 reintentos
    "retry_delay": 1,              # 1 segundo entre reintentos

    # Logging y monitoreo
    "log_requests": True,           # Log todas las solicitudes
    "track_usage": True,           # Monitorear uso de tokens
    "measure_latency": True,       # Medir latencia de respuestas
}

# Configuración específica para Citrino Chat
CITRINO_CHAT_LLM_CONFIG = {
    **LLM_GENERAL_CONFIG,

    # Parámetros específicos para chat
    "temperature": 0.05,           # Ultra-baja para máxima consistencia
    "max_tokens": 250,             # Respuestas más cortas en chat
    "top_p": 0.85,                # Control más estricto

    # Sistema de prompts
    "system_prompt_path": "src/prompts/system_prompt_chat.py",
    "fallback_prompt": "Eres un asistente de inversión inmobiliaria. Responde únicamente con datos existentes.",

    # Validaciones específicas de chat
    "validate_zones": True,        # Validar zonas mencionadas
    "validate_prices": True,       # Validar rangos de precios
    "validate_properties": True,   # Validar propiedades mencionadas
    "check_hallucinations": True,  # Detección activa de alucinaciones

    # Límites de contenido
    "max_properties_mentioned": 3, # Máximo 3 propiedades por respuesta
    "max_price_mentioned": 5000000, # Máximo precio permitido mencionar
    "allowed_zones": [             # Zonas permitidas explícitamente
        "Equipetrol", "Urbari", "Santa Mónica", "Las Palmas",
        "Santiago", "Sacta", "Pampa de la Isla", "Urbari"
    ],

    # Restricciones de lenguaje
    "forbidden_words": [           # Palabras prohibidas
        "garantizado", "seguro", "100%", "perfecto", "excelente",
        "increíble", "mejor", "único", "oportunidad única"
    ],
    "required_words": [],          # Palabras requeridas

    # Formato de respuesta
    "response_format": "structured", # Respuestas estructuradas
    "include_metadata": True,       # Incluir metadatos de validación
    "mark_uncertain": True,         # Marcar información incierta
}

# Configuración específica para Citrino Reco
CITRINO_RECO_LLM_CONFIG = {
    **LLM_GENERAL_CONFIG,

    # Parámetros específicos para recomendaciones
    "temperature": 0.1,            # Baja para consistencia en cálculos
    "max_tokens": 400,             # Más tokens para recomendaciones detalladas
    "top_p": 0.9,                 # Control estándar

    # Sistema de prompts
    "system_prompt_path": "src/prompts/system_prompt_reco.py",
    "fallback_prompt": "Genera recomendaciones basadas únicamente en propiedades existentes.",

    # Validaciones específicas de recomendaciones
    "validate_budget": True,        # Validar rangos de presupuesto
    "validate_compatibility": True, # Validar cálculos de compatibilidad
    "check_property_existence": True, # Verificar existencia de propiedades
    "validate_scores": True,        # Validar puntuaciones de compatibilidad

    # Límites de recomendaciones
    "max_recommendations": 5,       # Máximo 5 recomendaciones
    "min_compatibility": 60,        # Compatibilidad mínima 60%
    "max_compatibility": 95,        # Compatibilidad máxima 95%
    "compatibility_steps": 5,       # Incrementos de 5% en compatibilidad

    # Filtros obligatorios
    "require_price_filter": True,   # Filtro de precio obligatorio
    "require_location_filter": True, # Filtro de ubicación obligatorio
    "require_type_filter": True,     # Filtro de tipo obligatorio
    "require_availability_filter": True, # Filtro de disponibilidad obligatorio

    # Cálculo de compatibilidad
    "compatibility_weights": {
        "presupuesto": 0.4,          # 40% peso presupuesto
        "ubicacion": 0.25,           # 25% peso ubicación
        "caracteristicas": 0.2,      # 20% peso características
        "disponibilidad": 0.15       # 15% peso disponibilidad
    },

    # Formato de salida
    "output_format": "json",         # Salida JSON estructurada
    "include_scores": True,          # Incluir puntuaciones detalladas
    "include_justifications": True,  # Incluir justificaciones
    "include_metadata": True,        # Incluir metadatos de validación
}

# Configuración para fallback y errores
FALLBACK_CONFIG = {
    # Configuración de fallback
    "use_fallback": True,            # Usar sistema de fallback
    "fallback_temperature": 0.0,     # Temperatura cero para fallback
    "fallback_max_tokens": 100,      # Respuestas muy cortas en fallback

    # Mensajes de fallback
    "fallback_messages": {
        "no_data": "No tengo información específica sobre esa consulta en mi base de datos.",
        "error": "Experimentando dificultades técnicas. Por favor, intenta nuevamente.",
        "rate_limit": "Sistema temporalmente ocupado. Intenta en unos momentos.",
        "invalid_query": "No puedo procesar esa consulta específica con los datos disponibles."
    },

    # Tiempos de espera
    "fallback_timeout": 5,          # 5 segundos para fallback
    "max_fallback_attempts": 3,     # Máximo 3 intentos de fallback
}

# Configuración de logging y monitoreo
MONITORING_CONFIG = {
    # Niveles de logging
    "log_level": "INFO",             # INFO, DEBUG, WARNING, ERROR
    "log_requests": True,            # Log todas las solicitudes
    "log_responses": True,           # Log todas las respuestas
    "log_errors": True,              # Log todos los errores

    # Métricas a monitorear
    "track_metrics": [
        "response_time",             # Tiempo de respuesta
        "token_usage",               # Uso de tokens
        "success_rate",              # Tasa de éxito
        "error_rate",                # Tasa de errores
        "hallucination_rate",        # Tasa de alucinaciones detectadas
        "data_accuracy_rate"         # Tasa de precisión de datos
    ],

    # Alertas
    "alert_thresholds": {
        "response_time": 5000,        # 5 segundos alerta
        "error_rate": 0.1,           # 10% tasa de error alerta
        "hallucination_rate": 0.05,   # 5% tasa de alucinación alerta
        "data_accuracy_rate": 0.8     # 80% precisión mínima
    },

    # Exportación de métricas
    "export_metrics": True,          # Exportar métricas
    "metrics_format": "json",         # Formato de exportación
    "metrics_retention_days": 30,    # Retención de métricas
}

# Configuración de seguridad y validación
SECURITY_CONFIG = {
    # Validación de entrada
    "sanitize_input": True,          # Sanitizar entrada
    "validate_input": True,          # Validar formato de entrada
    "max_input_length": 500,         # Longitud máxima de entrada

    # Validación de salida
    "validate_output": True,         # Validar formato de salida
    "sanitize_output": True,         # Sanitizar salida
    "check_forbidden_content": True, # Verificar contenido prohibido

    # Control de acceso
    "rate_limiting": True,           # Limitar tasa de solicitudes
    "max_requests_per_minute": 60,   # Máximo 60 solicitudes por minuto
    "user_authentication": False,     # Autenticación de usuario (deshabilitada)

    # Validación de datos
    "validate_property_data": True,  # Validar datos de propiedades
    "validate_location_data": True,   # Validar datos de ubicación
    "validate_price_data": True,      # Validar datos de precios
    "cross_reference_data": True,     # Referencia cruzada de datos
}

# Función para obtener configuración por componente
def get_llm_config(component: str) -> dict:
    """
    Obtener configuración LLM para un componente específico.

    Args:
        component: 'chat', 'reco', o 'general'

    Returns:
        dict: Configuración para el componente solicitado
    """
    configs = {
        'chat': CITRINO_CHAT_LLM_CONFIG,
        'reco': CITRINO_RECO_LLM_CONFIG,
        'general': LLM_GENERAL_CONFIG
    }

    config = configs.get(component, LLM_GENERAL_CONFIG)
    return config.copy()

# Función para validar configuración
def validate_config(config: dict) -> bool:
    """
    Validar que la configuración cumpla con los requisitos mínimos.

    Args:
        config: Configuración a validar

    Returns:
        bool: True si la configuración es válida
    """
    required_fields = ['temperature', 'max_tokens', 'system_prompt_path']

    for field in required_fields:
        if field not in config:
            print(f"ERROR: Campo requerido faltante: {field}")
            return False

    # Validar rangos de valores
    if not (0 <= config['temperature'] <= 1):
        print("ERROR: Temperature debe estar entre 0 y 1")
        return False

    if not (10 <= config['max_tokens'] <= 1000):
        print("ERROR: Max tokens debe estar entre 10 y 1000")
        return False

    return True

# Función para imprimir configuración
def print_config_summary(component: str = 'general'):
    """
    Imprimir resumen de configuración para un componente.

    Args:
        component: Componente a mostrar
    """
    config = get_llm_config(component)

    print(f"\n=== CONFIGURACIÓN LLM - {component.upper()} ===")
    print(f"Temperature: {config['temperature']}")
    print(f"Max Tokens: {config['max_tokens']}")
    print(f"Top P: {config['top_p']}")
    print(f"Validation: {config.get('validate_facts', False)}")
    print(f"Safe Mode: {config.get('safe_mode', False)}")
    print(f"Timeout: {config.get('timeout', 30)}s")
    print("=" * 40)

if __name__ == "__main__":
    # Mostrar resúmenes de configuración
    print_config_summary('general')
    print_config_summary('chat')
    print_config_summary('reco')

    # Validar configuraciones
    print("\n=== VALIDACIÓN DE CONFIGURACIONES ===")
    for component in ['chat', 'reco', 'general']:
        config = get_llm_config(component)
        is_valid = validate_config(config)
        print(f"{component}: {'✅ VÁLIDA' if is_valid else '❌ INVÁLIDA'}")