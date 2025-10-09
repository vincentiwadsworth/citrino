# Plan: Sistema de Fallback a OpenRouter

## Objetivo
Implementar un sistema de fallback automático que use OpenRouter cuando z.ai no esté disponible (rate limit, downtime, errores 429/500).

## Situación Actual

### ✅ Ya Implementado
- Método `_call_openrouter()` en `llm_integration.py` (línea 187)
- Método `consultar()` con lógica de routing por provider
- Soporte para múltiples providers: zai, openrouter, openai

### ❌ Problema Actual
- Si z.ai falla (429, 500, timeout), el sistema retorna datos vacíos
- No hay retry ni fallback automático
- Solo usa el provider configurado en `.env`

## Diseño Propuesto

### 1. Sistema de Fallback Automático

**Archivo**: `src/llm_integration.py`

#### 1.1 Configuración Multi-Provider en `.env`
```env
# Provider primario
ZAI_API_KEY=your_zai_api_key_here
LLM_PROVIDER=zai
LLM_MODEL=glm-4.6

# Provider de fallback
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_FALLBACK_ENABLED=true

# Configuración
LLM_MAX_TOKENS=8000
LLM_TEMPERATURE=0.1
LLM_RETRY_ATTEMPTS=2
LLM_FALLBACK_ON_RATE_LIMIT=true
```

#### 1.2 Nuevo Método: `consultar_con_fallback()`

```python
def consultar_con_fallback(self, prompt: str, use_fallback: bool = True) -> Dict[str, Any]:
    """
    Realiza consulta LLM con fallback automático.
    
    Returns:
        {
            "respuesta": str,
            "provider_usado": str,  # "zai" o "openrouter"
            "fallback_activado": bool,
            "intentos": int
        }
    """
    providers = self._get_provider_chain()  # ["zai", "openrouter"]
    errores = []
    
    for i, provider in enumerate(providers):
        es_fallback = i > 0
        
        # Si es fallback y está deshabilitado, skip
        if es_fallback and not use_fallback:
            break
            
        try:
            logger.info(f"Intentando con provider: {provider}")
            
            if provider == "zai":
                respuesta = self._call_zai(prompt)
            elif provider == "openrouter":
                respuesta = self._call_openrouter(prompt)
            else:
                continue
            
            return {
                "respuesta": respuesta,
                "provider_usado": provider,
                "fallback_activado": es_fallback,
                "intentos": i + 1
            }
            
        except (ConnectionError, requests.HTTPError) as e:
            error_msg = str(e)
            errores.append(f"{provider}: {error_msg}")
            
            # Detectar rate limit
            if "429" in error_msg or "Too Many Requests" in error_msg:
                logger.warning(f"Rate limit en {provider}, probando fallback...")
                continue
            
            # Detectar server error
            if "500" in error_msg or "502" in error_msg or "503" in error_msg:
                logger.warning(f"Error de servidor en {provider}, probando fallback...")
                continue
            
            # Otros errores
            logger.error(f"Error en {provider}: {e}")
            if not use_fallback:
                raise
    
    # Si todos los providers fallaron
    raise ConnectionError(f"Todos los providers fallaron: {'; '.join(errores)}")
```

#### 1.3 Helper Method: `_get_provider_chain()`

```python
def _get_provider_chain(self) -> List[str]:
    """Retorna lista ordenada de providers a intentar."""
    chain = [self.config.provider]  # Primario primero
    
    # Agregar fallback si está habilitado
    fallback_enabled = os.getenv("OPENROUTER_FALLBACK_ENABLED", "false").lower() == "true"
    
    if fallback_enabled:
        if self.config.provider == "zai" and os.getenv("OPENROUTER_API_KEY"):
            chain.append("openrouter")
        elif self.config.provider == "openrouter" and os.getenv("ZAI_API_KEY"):
            chain.append("zai")
    
    return chain
```

#### 1.4 Actualizar `_call_openrouter()` con Modelo Configurable

```python
def _call_openrouter(self, prompt: str) -> str:
    """Realiza llamada a la API de OpenRouter."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    # Obtener modelo de OpenRouter de env o usar default
    model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY no configurada")
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": self.config.max_tokens,
        "temperature": self.config.temperature
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://citrino.app",  # Opcional
        "X-Title": "Citrino ETL"  # Para tracking en OpenRouter
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
        
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Error de conexión con OpenRouter: {e}")
    except KeyError as e:
        raise ValueError(f"Respuesta inesperada de OpenRouter: {e}")
```

### 2. Actualizar `description_parser.py`

```python
def extract_from_description(
    self, 
    descripcion: str, 
    titulo: str = "",
    use_cache: bool = True,
    use_fallback: bool = True  # Nuevo parámetro
) -> Dict[str, Any]:
    """Extrae datos estructurados de una descripción."""
    self.stats["total_requests"] += 1
    
    # Cache check...
    cache_key = f"{titulo}|{descripcion[:200]}"
    if use_cache and cache_key in self.cache:
        self.stats["cache_hits"] += 1
        return self.cache[cache_key]
    
    try:
        prompt = self._build_extraction_prompt(descripcion, titulo)
        
        logger.info(f"Llamando LLM para extraer datos...")
        self.stats["llm_calls"] += 1
        
        # Usar nuevo método con fallback
        resultado_llm = self.llm.consultar_con_fallback(prompt, use_fallback=use_fallback)
        
        # Parsear respuesta
        extracted_data = self._parse_llm_extraction(resultado_llm["respuesta"])
        
        # Agregar metadatos
        extracted_data["_llm_provider"] = resultado_llm["provider_usado"]
        extracted_data["_fallback_usado"] = resultado_llm["fallback_activado"]
        
        # Logging
        if resultado_llm["fallback_activado"]:
            logger.info(f"✓ Fallback activado: {resultado_llm['provider_usado']}")
        
        # Cache
        if use_cache:
            self.cache[cache_key] = extracted_data
            if self.stats["llm_calls"] % 10 == 0:
                self._save_cache()
        
        return extracted_data
        
    except Exception as e:
        self.stats["errors"] += 1
        logger.error(f"Error extrayendo datos: {e}")
        # Retornar estructura vacía
        return {...}
```

### 3. Modelos Recomendados en OpenRouter

**Para Extracción de Datos (orden de preferencia):**

1. **`anthropic/claude-3.5-sonnet`** (Recomendado)
   - Excelente en seguir instrucciones
   - Output JSON muy preciso
   - $3 / 1M tokens input, $15 / 1M tokens output
   - 200K contexto

2. **`anthropic/claude-3-haiku`** (Económico)
   - Rápido y barato
   - Bueno en tareas estructuradas
   - $0.25 / 1M tokens input, $1.25 / 1M tokens output
   - 200K contexto

3. **`meta-llama/llama-3.1-8b-instruct:free`** (Gratis)
   - Completamente gratuito
   - Calidad decente para extracciones simples
   - Límite de rate más bajo

4. **`google/gemini-pro-1.5`** (Alternativa)
   - $1.25 / 1M tokens input, $5 / 1M tokens output
   - 2M contexto (overkill para esta tarea)

### 4. Actualizar `.env.example`

```env
# ============================================
# PROVEEDOR LLM PRIMARIO
# ============================================

# Z.AI (Primario)
ZAI_API_KEY=your_zai_api_key_here
LLM_PROVIDER=zai
LLM_MODEL=glm-4.6

# ============================================
# FALLBACK LLM (OpenRouter)
# ============================================

# Habilitar fallback automático
OPENROUTER_FALLBACK_ENABLED=true

# OpenRouter API Key
# Obtener en: https://openrouter.ai/keys
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Modelo de fallback
# Opciones:
#   - anthropic/claude-3.5-sonnet (recomendado, $3/$15 por 1M tokens)
#   - anthropic/claude-3-haiku (económico, $0.25/$1.25 por 1M tokens)
#   - meta-llama/llama-3.1-8b-instruct:free (gratis)
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# ============================================
# CONFIGURACIÓN GENERAL LLM
# ============================================

LLM_MAX_TOKENS=8000
LLM_TEMPERATURE=0.1

# Reintentos antes de fallback
LLM_RETRY_ATTEMPTS=2

# Activar fallback en rate limit (429)
LLM_FALLBACK_ON_RATE_LIMIT=true
```

### 5. Tests a Crear

**Archivo**: `tests/test_llm_fallback.py`

```python
import pytest
import os
from unittest.mock import patch, Mock
from src.llm_integration import LLMIntegration

def test_fallback_on_rate_limit():
    """Test que fallback se activa en rate limit 429."""
    with patch.dict(os.environ, {
        "ZAI_API_KEY": "test_key",
        "OPENROUTER_API_KEY": "test_key_or",
        "OPENROUTER_FALLBACK_ENABLED": "true"
    }):
        llm = LLMIntegration()
        
        # Mock z.ai retorna 429
        with patch.object(llm, '_call_zai', side_effect=ConnectionError("429 Too Many Requests")):
            # Mock OpenRouter retorna éxito
            with patch.object(llm, '_call_openrouter', return_value="Test response"):
                resultado = llm.consultar_con_fallback("test prompt")
                
                assert resultado["provider_usado"] == "openrouter"
                assert resultado["fallback_activado"] == True
                assert resultado["respuesta"] == "Test response"

def test_no_fallback_when_disabled():
    """Test que fallback NO se activa si está deshabilitado."""
    with patch.dict(os.environ, {
        "ZAI_API_KEY": "test_key",
        "OPENROUTER_FALLBACK_ENABLED": "false"
    }):
        llm = LLMIntegration()
        
        with patch.object(llm, '_call_zai', side_effect=ConnectionError("429")):
            with pytest.raises(ConnectionError):
                llm.consultar_con_fallback("test prompt", use_fallback=False)

def test_primary_provider_success():
    """Test que usa provider primario cuando funciona."""
    with patch.dict(os.environ, {"ZAI_API_KEY": "test_key"}):
        llm = LLMIntegration()
        
        with patch.object(llm, '_call_zai', return_value="Success from zai"):
            resultado = llm.consultar_con_fallback("test prompt")
            
            assert resultado["provider_usado"] == "zai"
            assert resultado["fallback_activado"] == False
```

### 6. Logging y Monitoreo

**Agregar al final del ETL:**

```python
# En build_relevamiento_dataset.py, al final de main()

print("\n" + "="*80)
print("ESTADÍSTICAS LLM")
print("="*80)
print(f"  Total requests:    {parser.stats['total_requests']}")
print(f"  Cache hits:        {parser.stats['cache_hits']}")
print(f"  LLM calls:         {parser.stats['llm_calls']}")
print(f"  Errors:            {parser.stats['errors']}")

# Nuevas estadísticas de fallback
if hasattr(parser, 'fallback_stats'):
    print(f"\nFALLBACK:")
    print(f"  Z.AI exitosos:      {parser.fallback_stats.get('zai_success', 0)}")
    print(f"  Z.AI fallidos:      {parser.fallback_stats.get('zai_failed', 0)}")
    print(f"  OpenRouter usado:   {parser.fallback_stats.get('openrouter_used', 0)}")
    print(f"  Fallback rate:      {parser.fallback_stats.get('openrouter_used', 0) / max(parser.stats['llm_calls'], 1) * 100:.1f}%")
```

### 7. Costos Estimados

**Escenario: 1,579 propiedades con descripciones**

Asumiendo promedio de 300 tokens por descripción:

| Provider | Modelo | Input | Output | Costo por 1,579 |
|----------|--------|-------|--------|------------------|
| Z.AI | GLM-4.6 | Incluido | Incluido | $0 (plan subscription) |
| OpenRouter | Claude 3.5 Sonnet | $3/1M | $15/1M | ~$0.45 input + ~$0.75 output = **$1.20** |
| OpenRouter | Claude 3 Haiku | $0.25/1M | $1.25/1M | ~$0.04 input + $0.06 output = **$0.10** |
| OpenRouter | Llama 3.1 8B | FREE | FREE | **$0** |

**Recomendación**: Usar Claude 3.5 Sonnet por mejor calidad, o Llama 3.1 si quieres fallback gratuito.

## Orden de Implementación

1. ✅ **Fase 1: Configuración** (15 min)
   - Actualizar `.env.example` con fallback options
   - Documentar en README.md

2. ✅ **Fase 2: Core Fallback** (30 min)
   - Implementar `consultar_con_fallback()` en `llm_integration.py`
   - Implementar `_get_provider_chain()`
   - Actualizar `_call_openrouter()` con modelo configurable

3. ✅ **Fase 3: Integración** (20 min)
   - Actualizar `description_parser.py` para usar nuevo método
   - Agregar tracking de estadísticas de fallback

4. ✅ **Fase 4: Testing** (30 min)
   - Crear `tests/test_llm_fallback.py`
   - Test con rate limit simulado
   - Test con fallback deshabilitado
   - Test con provider primario exitoso

5. ✅ **Fase 5: Monitoreo** (15 min)
   - Agregar logging de fallback stats
   - Actualizar output de ETL con métricas

## Ventajas del Diseño

✅ **Transparente**: Usuario no necesita intervenir
✅ **Configurable**: Puede deshabilitar fallback si quiere
✅ **Robusto**: Maneja rate limits, timeouts, server errors
✅ **Auditable**: Tracking de qué provider se usó
✅ **Flexible**: Fácil agregar más providers (OpenAI, etc.)
✅ **Económico**: Usa fallback solo cuando es necesario

## Testing del Sistema

**Comando para probar fallback manualmente:**

```bash
# 1. Configurar ambos providers
export ZAI_API_KEY=tu_key
export OPENROUTER_API_KEY=tu_key_or
export OPENROUTER_FALLBACK_ENABLED=true
export OPENROUTER_MODEL=anthropic/claude-3-haiku

# 2. Simular que z.ai está down (temporalmente poner API key inválida)
export ZAI_API_KEY=invalid_key_to_test_fallback

# 3. Ejecutar test de 5 muestras
python scripts/test_proveedor02_sample.py

# 4. Verificar que en logs dice "Fallback activado: openrouter"
```

## Resumen

Este plan implementa un sistema robusto de fallback que:
- Detecta automáticamente cuando z.ai falla (429, 500, timeout)
- Cambia a OpenRouter sin intervención manual
- Permite configuración flexible vía variables de entorno
- Mantiene tracking completo de uso de fallback
- Es fácil de probar y mantener

**Tiempo estimado de implementación**: ~2 horas
**Complejidad**: Media
**Beneficio**: Alta disponibilidad del sistema de extracción LLM
