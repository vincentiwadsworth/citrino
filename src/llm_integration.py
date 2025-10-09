"""
Integración con LLM para procesamiento de lenguaje natural.

Este módulo proporciona la funcionalidad para convertir descripciones
en lenguaje natural a perfiles estructurados del sistema de recomendación.
"""

import os
import json
import requests
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """Configuración para el servicio LLM."""
    provider: str = "zai"  # zai, openrouter, openai
    api_key: Optional[str] = None
    model: str = "glm-4.5-air"
    base_url: Optional[str] = None
    max_tokens: int = 2000
    temperature: float = 0.1


class LLMIntegration:
    """Clase principal para integración con LLM."""

    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Inicializa la integración LLM.

        Args:
            config: Configuración del LLM. Si es None, usa variables de entorno.
        """
        self.config = config or self._config_from_env()
        self.session = requests.Session()

        # Configurar headers por defecto
        if self.config.provider == "openrouter":
            self.session.headers.update({
                "Authorization": f"Bearer {self.config.api_key}",
                "HTTP-Referer": "https://github.com/vincentiwadsworth/citrino-poc",
                "X-Title": "Citrino PoC - Sistema de Recomendación"
            })
        elif self.config.provider == "openai":
            self.session.headers.update({
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            })

    def _config_from_env(self) -> LLMConfig:
        """Crea configuración desde variables de entorno."""
        provider = os.getenv("LLM_PROVIDER", "zai")
        api_key = os.getenv("ZAI_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        model = os.getenv("LLM_MODEL", "glm-4.5-air")

        return LLMConfig(
            provider=provider,
            api_key=api_key,
            model=model
        )

    def _build_prompt(self, texto: str) -> str:
        """
        Construye el prompt para el LLM.

        Args:
            texto: Descripción en lenguaje natural del prospecto

        Returns:
            Prompt formateado para el LLM
        """
        return f"""
Eres un asistente especializado en bienes raíces. Tu tarea es analizar la descripción
de un prospecto y convertirla a un perfil estructurado en formato JSON.

Analiza el siguiente texto y extrae la información relevante:

"{texto}"

Responde ÚNICAMENTE con un objeto JSON que tenga esta estructura exacta:
{{
    "composicion_familiar": {{
        "adultos": <número>,
        "ninos": [<edades si aplica>],
        "adultos_mayores": <número>
    }},
    "presupuesto": {{
        "min": <número o null>,
        "max": <número o null>,
        "tipo": "compra" o "alquiler"
    }},
    "necesidades": [<lista de servicios necesarios>],
    "preferencias": {{
        "ubicacion": <ubicación deseada o null>,
        "seguridad": "alta", "media" o null,
        "estilo_propiedad": <tipo de propiedad o null>,
        "caracteristicas_deseadas": [<lista de características>]
    }}
}}

Reglas:
1. Si no se menciona algo, usa null o lista vacía según corresponda
2. Para presupuesto, interpreta frases como "alrededor de X" como min y max similares
3. Las necesidades pueden incluir: escuela_primaria, secundaria, universidad,
   supermercado, hospital, clinica, farmacia, transporte, gym, etc.
4. Las características deseadas pueden incluir: amoblado, espacioso, planta_baja,
   ascensor, estacionamiento, etc.
5. Responde solo con el JSON, sin texto adicional

JSON:"""

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parsea la respuesta del LLM a un diccionario.

        Args:
            response_text: Respuesta cruda del LLM

        Returns:
            Diccionario estructurado con el perfil
        """
        try:
            # Limpiar la respuesta y extraer JSON
            response_text = response_text.strip()

            # Eliminar marcadores de código si existen
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            # Parsear JSON
            perfil = json.loads(response_text.strip())

            # Validar estructura básica
            if not isinstance(perfil, dict):
                raise ValueError("La respuesta no es un objeto JSON válido")

            # Asegurar campos obligatorios
            campos_obligatorios = ["composicion_familiar", "presupuesto", "necesidades", "preferencias"]
            for campo in campos_obligatorios:
                if campo not in perfil:
                    perfil[campo] = {} if campo in ["composicion_familiar", "presupuesto", "preferencias"] else []

            return perfil

        except json.JSONDecodeError as e:
            raise ValueError(f"Error al parsear JSON: {e}")
        except Exception as e:
            raise ValueError(f"Error procesando respuesta: {e}")

    def _call_zai(self, prompt: str) -> str:
        """Realiza llamada a la API de Z.AI."""
        url = "https://api.z.ai/api/paas/v4/chat/completions"

        payload = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        }

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()

            data = response.json()
            return data["choices"][0]["message"]["content"]

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error de conexión con Z.AI: {e}")
        except KeyError as e:
            raise ValueError(f"Respuesta inesperada de Z.AI: {e}")

    def _call_openrouter(self, prompt: str) -> str:
        """Realiza llamada a la API de OpenRouter."""
        url = "https://openrouter.ai/api/v1/chat/completions"

        payload = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        }

        try:
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()
            return data["choices"][0]["message"]["content"]

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error de conexión con OpenRouter: {e}")
        except KeyError as e:
            raise ValueError(f"Respuesta inesperada de OpenRouter: {e}")

    def _call_openai(self, prompt: str) -> str:
        """Realiza llamada a la API de OpenAI."""
        url = "https://api.openai.com/v1/chat/completions"

        payload = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        }

        try:
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()
            return data["choices"][0]["message"]["content"]

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error de conexión con OpenAI: {e}")
        except KeyError as e:
            raise ValueError(f"Respuesta inesperada de OpenAI: {e}")

    def parsear_perfil_desde_texto(self, texto: str) -> Dict[str, Any]:
        """
        Convierte una descripción en lenguaje natural a un perfil estructurado.

        Args:
            texto: Descripción del prospecto en lenguaje natural

        Returns:
            Diccionario con el perfil estructurado

        Raises:
            ValueError: Si el texto no puede ser parseado
            ConnectionError: Si hay problemas de conexión con el LLM
        """
        if not texto or not texto.strip():
            raise ValueError("El texto de entrada no puede estar vacío")

        # Construir prompt
        prompt = self._build_prompt(texto)

        try:
            # Llamar al LLM según el proveedor
            if self.config.provider == "zai":
                response_text = self._call_zai(prompt)
            elif self.config.provider == "openrouter":
                response_text = self._call_openrouter(prompt)
            elif self.config.provider == "openai":
                response_text = self._call_openai(prompt)
            else:
                raise ValueError(f"Proveedor no soportado: {self.config.provider}")

            # Parsear respuesta
            perfil = self._parse_llm_response(response_text)

            return perfil

        except (ConnectionError, ValueError) as e:
            # En caso de error, retornar un perfil básico con logging
            print(f"Advertencia: Error procesando con LLM ({e}). Usando perfil básico.")
            return self._perfil_basico_desde_texto(texto)

    def _perfil_basico_desde_texto(self, texto: str) -> Dict[str, Any]:
        """
        Genera un perfil básico usando reglas simples cuando el LLM falla.

        Args:
            texto: Descripción del prospecto

        Returns:
            Perfil básico estructurado
        """
        texto_lower = texto.lower()

        # Análisis simple de composición familiar
        adultos = 2  # valor por defecto
        ninos = []
        adultos_mayores = 0

        if "solo" in texto_lower or "individual" in texto_lower:
            adultos = 1
        elif "pareja" in texto_lower or "matrimonio" in texto_lower:
            adultos = 2
        elif "familia" in texto_lower:
            adultos = 2
            if "hijo" in texto_lower or "niño" in texto_lower:
                ninos = [{"edad": 8}]  # edad estimada

        # Análisis simple de presupuesto
        presupuesto_min = None
        presupuesto_max = None

        # Buscar números en el texto
        import re
        numeros = re.findall(r'\b(\d+(?:\.\d+)?)\s*[kK]?\b', texto)
        if numeros:
            # Convertir a números y asumir que son miles si tienen 'k' o son < 1000
            valores = []
            for num in numeros:
                valor = float(num)
                if valor < 1000:
                    valor *= 1000  # asumir miles
                valores.append(valor)

            if valores:
                presupuesto_min = min(valores) * 0.8  # 20% menos como mínimo
                presupuesto_max = max(valores) * 1.2  # 20% más como máximo

        # Necesidades básicas según palabras clave
        necesidades = []
        if "escuela" in texto_lower or "colegio" in texto_lower:
            necesidades.append("escuela_primaria")
        if "universidad" in texto_lower:
            necesidades.append("universidad")
        if "supermercado" in texto_lower or "mercado" in texto_lower:
            necesidades.append("supermercado")
        if "hospital" in texto_lower or "clinica" in texto_lower:
            necesidades.append("hospital")

        # Preferencias de ubicación
        ubicacion = None
        if "norte" in texto_lower:
            ubicacion = "norte"
        elif "sur" in texto_lower:
            ubicacion = "sur"
        elif "centro" in texto_lower:
            ubicacion = "centro"

        return {
            "composicion_familiar": {
                "adultos": adultos,
                "ninos": ninos,
                "adultos_mayores": adultos_mayores
            },
            "presupuesto": {
                "min": presupuesto_min,
                "max": presupuesto_max,
                "tipo": "compra"
            },
            "necesidades": necesidades,
            "preferencias": {
                "ubicacion": ubicacion,
                "seguridad": "alta",
                "caracteristicas_deseadas": []
            }
        }

    def validar_configuracion(self) -> bool:
        """
        Valida que la configuración del LLM sea correcta.

        Returns:
            True si la configuración es válida, False en caso contrario
        """
        if not self.config.api_key:
            print("Error: No se encontró API key para el LLM")
            return False

        if self.config.provider not in ["zai", "openrouter", "openai"]:
            print(f"Error: Proveedor no soportado: {self.config.provider}")
            return False

        return True

    def obtener_info_configuracion(self) -> Dict[str, Any]:
        """
        Retorna información sobre la configuración actual.

        Returns:
            Diccionario con información de configuración
        """
        return {
            "provider": self.config.provider,
            "model": self.config.model,
            "api_key_configurada": bool(self.config.api_key),
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        }