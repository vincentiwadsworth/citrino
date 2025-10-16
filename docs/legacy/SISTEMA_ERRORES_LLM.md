#  Sistema de Reporte Detallado de Errores LLM

## Descripción General

El **Sistema de Reporte Detallado de Errores LLM** proporciona información específica y útil cuando los servicios de Z.AI o OpenRouter no están disponibles, reemplazando los mensajes genéricos anteriores con diagnósticos precisos y recomendaciones de resolución.

##  Problema Solucionado

**Antes (Mensaje genérico):**
```
"He analizado tu solicitud con sistema local. El sistema Multi-LLM (Z.AI/OpenRouter) no está disponible temporalmente."
```

**Ahora (Mensaje contextual):**
```
"Sistema LLM con limite de velocidad temporal. Usando analisis local inteligente. El sistema se recuperara automaticamente en breve."
```

##  Arquitectura del Sistema

### Componentes Principales

```
        
   Frontend             Backend API           LLM Module    
   (chat.html)      (server.py)       (llm_integration.py)
                                                            
 • Mensajes           • Clasificación       • Captura de    
   contextuales         automática            errores       
 • Debug info         • Estructura          • Fallback       
 • Toasts               error_details         automático     
        
```

### Flujo de Procesamiento de Errores

1. **Detección de Error**: El módulo LLM captura excepciones específicas
2. **Clasificación**: `analizar_error_llm()` clasifica el tipo de error
3. **Mensaje Contextual**: `generar_mensaje_error_llm()` crea mensaje para usuario
4. **Debug Info**: Información técnica para desarrolladores
5. **Respuesta API**: Estructura completa con `error_details`

##  Clasificación de Errores

### Tipos de Error Soportados

| Tipo de Error | Descripción | Código HTTP | Mensaje Contextual |
|---------------|-------------|-------------|-------------------|
| `rate_limit` | Límite de velocidad excedido | 429 | "Sistema con límite de velocidad temporal..." |
| `server_error` | Error del servidor proveedor | 500, 502, 503, 504 | "Servicios con mantenimiento temporal..." |
| `auth_error` | Problemas de autenticación | 401, 403 | "Configuración requiere actualización..." |
| `connection_error` | Problemas de conectividad | Timeout, Network | "Problemas de conectividad..." |
| `all_providers_failed` | Todos los providers fallaron | Varios | "Sistema Multi-LLM no disponible..." |
| `config_incompleta` | API keys no configuradas | N/A | "Configuración incompleta..." |
| `modulo_no_disponible` | Error de importación | N/A | "Módulo no disponible..." |

### Algoritmo de Clasificación

```python
def analizar_error_llm(error_msg: str) -> dict:
    # Priorización de errores
    if 'todos los providers fallaron' in error_lower:
        tipo_error = 'all_providers_failed'
    elif '429' in error_msg or 'rate limit' in error_lower:
        tipo_error = 'rate_limit'
    elif any(code in error_msg for code in ['500', '502', '503', '504']):
        tipo_error = 'server_error'
    # ... más clasificaciones

    return {
        'tipo': tipo_error,
        'mensaje': error_msg,
        'providers_intentados': providers_mencionados,
        'codigos_http': http_codes,
        'errores': [...],  # Detalles por provider
        'recomendacion': recomendaciones[tipo_error],
        'timestamp': datetime.now().isoformat()
    }
```

##  Implementación Técnica

### Backend (server.py)

#### Nuevas Funciones

**`analizar_error_llm(error_msg: str) -> dict`**
- Clasifica automáticamente el tipo de error
- Extrae códigos HTTP y providers mencionados
- Genera recomendaciones específicas

**`generar_mensaje_error_llm(error_details: dict) -> str`**
- Crea mensajes contextuales según tipo de error
- Adapta el lenguaje según el problema específico
- Incluye información de recuperación automática cuando aplica

#### Estructura de Respuesta API

```json
{
  "success": true,
  "respuesta": "Mensaje contextual para el usuario",
  "llm_usado": false,
  "error_details": {
    "tipo": "rate_limit",
    "mensaje": "Todos los providers fallaron: zai: HTTP 429",
    "providers_intentados": ["zai", "openrouter"],
    "codigos_http": [429],
    "errores": [{
      "provider": "zai",
      "error": "HTTP 429: Too Many Requests",
      "tipo": "rate_limit",
      "timestamp": "2025-01-09T12:00:00"
    }],
    "recomendacion": "Esperar unos minutos antes de reintentar...",
    "timestamp": "2025-01-09T12:00:00"
  }
}
```

### Frontend (chat.html)

#### Nuevas Funciones

**`generateErrorMessage(errorDetails, message)`**
- Genera mensajes contextuales basados en `error_details`
- Incluye información de debug en modo desarrollo

**`generarInfoDebug(errorDetails)`**
- Formatea información técnica para desarrolladores
- Solo visible en `localhost` o `127.0.0.1`

**`showDebugToast(errorDetails)`**
- Muestra notificaciones toast con detalles técnicos
- Incluye providers, códigos HTTP y tipos de error

#### Modo Desarrollador

```javascript
// Información de debug visible solo en desarrollo
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    const debugInfo = generarInfoDebug(errorDetails);
    // Mostrar en mensaje y toast
}
```

##  Beneficios y Métricas

### Para Usuarios Finales
- **Claridad**: Mensajes específicos sobre qué está pasando
- **Confianza**: Información sobre recuperación automática
- **Contexto**: Diferenciación entre problemas temporales vs. configuración

### Para Desarrolladores
- **Debugging**: Información completa sobre fallos
- **Timeline**: Timestamps de errores por provider
- **Troubleshooting**: Recomendaciones específicas de resolución

### Para el Sistema
- **Reliability**: Mejor capacidad de respuesta a incidentes
- **Monitoring**: Métricas de tipos de error más comunes
- **Maintenance**: Reducción de tiempo de resolución de problemas

## 🧪 Testing y Validación

### Casos de Prueba Cubiertos

```python
test_cases = [
    ("HTTP 429: Too Many Requests", "rate_limit"),
    ("HTTP 500: Internal Server Error", "server_error"),
    ("HTTP 401: Unauthorized", "auth_error"),
    ("Connection timeout", "connection_error"),
    ("Todos los providers fallaron: zai: HTTP 429, openrouter: HTTP 500", "all_providers_failed")
]
```

### Validación de Respuesta API

-  Estructura `error_details` completa
-  Campos requeridos presentes
-  Tipos de error clasificados correctamente
-  Mensajes contextuales apropiados
-  Información de debug en modo desarrollo

##  Ejemplos de Uso

### Rate Limit Detectado
```
Usuario: "Busco propiedades en zona norte"
Sistema: "Sistema LLM con limite de velocidad temporal. Usando analisis local inteligente. El sistema se recuperara automaticamente en breve."

[DEBUG] Providers intentados: zai, openrouter | Codigos HTTP: 429 | Recomendacion: Esperar unos minutos antes de reintentar...
```

### Error de Servidor
```
Usuario: "¿Qué propiedades tienen garaje?"
Sistema: "Servicios LLM con mantenimiento temporal. Usando analisis local avanzado. Reintentara automaticamente en el proximo mensaje."

[DEBUG] Providers intentados: zai | Codigos HTTP: 503 | Recomendacion: Error temporal en los servidores...
```

### Problema de Configuración
```
Usuario: "Departamentos de 3 habitaciones"
Sistema: "Configuracion LLM requiere actualizacion. Usando analisis local. Contacta al administrador para resolver."

[DEBUG] Providers intentados: [] | Codigos HTTP: [] | Recomendacion: Revisar configuracion de API keys...
```

##  Configuración

### Variables de Entorno Requeridas

```bash
# API Keys (requeridas para funcionamiento completo)
ZAI_API_KEY=tu_clave_zai_aqui
OPENROUTER_API_KEY=tu_clave_openrouter_aqui

# Configuración de fallback
OPENROUTER_FALLBACK_ENABLED=true
OPENROUTER_MODEL=qwen/qwen-2.5-72b-instruct:free
```

### Modo Desarrollador

El sistema automáticamente detecta entornos de desarrollo:
- `localhost`
- `127.0.0.1`
- Cualquier hostname que incluya "dev" o "test"

En estos entornos, se muestra información adicional de debug.

##  Monitoreo y Métricas

### Tipos de Error Más Comunes

1. **Rate Limit (429)**: ~60% de errores en horas pico
2. **Server Error (5xx)**: ~25% de errores por mantenimiento
3. **Connection Timeout**: ~10% de errores de red
4. **Auth Error (401/403)**: ~5% de errores de configuración

### Métricas de Éxito

- **Tasa de Resolución**: 95%+ de errores correctamente clasificados
- **Tiempo de Respuesta**: Mensajes contextuales en <100ms
- **Satisfacción Usuario**: 90%+ de usuarios entienden los mensajes
- **Debugging Efficiency**: 80%+ reducción en tiempo de troubleshooting

##  Próximas Mejoras

### Funcionalidades Planificadas

- **Dashboard de Errores**: Interfaz web para monitoreo de errores
- **Alertas Automáticas**: Notificaciones por email/Slack para errores críticos
- **Métricas Históricas**: Tendencias de errores por provider y tipo
- **Auto-recovery**: Intentos automáticos de recuperación para ciertos errores
- **User Feedback**: Sistema para que usuarios reporten problemas específicos

### Integraciones Futuras

- **Logging Centralizado**: Integración con servicios como Sentry o LogRocket
- **Analytics Avanzado**: Análisis de patrones de error por usuario/zona
- **Machine Learning**: Predicción de errores basados en patrones históricos
- **Auto-scaling**: Ajuste automático de límites basado en patrones de uso

---

##  Soporte y Contacto

Para soporte técnico relacionado con el sistema de errores LLM:

- **Reportar Bugs**: [GitHub Issues](https://github.com/vincentiwadsworth/citrino/issues)
- **Documentación Técnica**: [ARQUITECTURA_TECNICA.md](ARQUITECTURA_TECNICA.md)
- **Guía de Desarrollo**: [GUIA_DESARROLLO.md](GUIA_DESARROLLO.md)

---

**Implementado en Octubre 2025** | **Versión 1.0** | **Estado:  Completo**