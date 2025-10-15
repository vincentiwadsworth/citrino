#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Endpoint compatible con OpenAI Chat Completions para Chatbot UI

Este módulo implementa la API compatible con OpenAI que permite
integrar Chatbot UI directamente con el sistema Citrino.
"""

import json
import sys
import os
from datetime import datetime
from flask import Flask, request, jsonify
from typing import Dict, List, Any, Optional
import logging

# Agregar paths del proyecto
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from llm_integration import LLMIntegration, LLMConfig
    from description_parser import DescriptionParser
    from recommendation_engine_mejorado import RecommendationEngineMejorado
    LLM_AVAILABLE = True
except ImportError as e:
    logging.warning(f"LLM modules not available: {e}")
    LLM_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CitrinoChatbotAPI:
    """
    API compatible con OpenAI Chat Completions para Chatbot UI
    """

    def __init__(self):
        """Inicializa la API del chatbot."""
        self.llm = None
        self.description_parser = None
        self.recommendation_engine = None
        self.propiedades = []

        # Inicializar componentes LLM si están disponibles
        if LLM_AVAILABLE:
            self._initialize_llm_components()

        # Cargar propiedades
        self._load_properties()

        logger.info("Citrino Chatbot API inicializada")

    def _initialize_llm_components(self):
        """Inicializa componentes LLM si están configurados."""
        try:
            # Inicializar LLM Integration
            if os.getenv('ZAI_API_KEY'):
                self.llm = LLMIntegration(LLMConfig(
                    provider=os.getenv('LLM_PROVIDER', 'zai'),
                    api_key=os.getenv('ZAI_API_KEY'),
                    model=os.getenv('LLM_MODEL', 'glm-4.6')
                ))
                logger.info("LLM Integration inicializada")

            # Inicializar Description Parser
            self.description_parser = DescriptionParser()
            logger.info("Description Parser inicializado")

            # Inicializar motor de recomendaciones
            self.recommendation_engine = RecommendationEngineMejorado()
            self.recommendation_engine.cargar_propiedades(self.propiedades)
            logger.info("Recommendation Engine inicializado")

        except Exception as e:
            logger.error(f"Error inicializando componentes LLM: {e}")

    def _load_properties(self):
        """Carga las propiedades desde el archivo JSON."""
        try:
            # Intentar cargar desde diferentes rutas posibles
            rutas_posibles = [
                os.path.join(os.path.dirname(__file__), '..', 'data', 'base_datos_relevamiento.json'),
                os.path.join(os.path.dirname(__file__), '..', 'data', 'metrics', 'analisis_data_raw_20251015_112747_readable.json'),
            ]

            for ruta in rutas_posibles:
                if os.path.exists(ruta):
                    with open(ruta, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if 'propiedades' in data:
                            self.propiedades = data['propiedades']
                            break

            # Si el motor de recomendaciones está inicializado, cargar propiedades
            if self.recommendation_engine and self.propiedades:
                self.recommendation_engine.cargar_propiedades(self.propiedades)

            logger.info(f"Cargadas {len(self.propiedades)} propiedades")

        except Exception as e:
            logger.error(f"Error cargando propiedades: {e}")
            self.propiedades = []

    def format_openai_response(self, content: str, model: str = "citrino-v1") -> Dict[str, Any]:
        """
        Formatea la respuesta al estilo OpenAI Chat Completions.

        Args:
            content: Contenido del mensaje
            model: Nombre del modelo

        Returns:
            Dict compatible con OpenAI API
        """
        return {
            "id": f"chatcmpl-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }

    def analyze_message_intent(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Analiza el intent del mensaje del usuario.

        Args:
            messages: Lista de mensajes de la conversación

        Returns:
            Dict con análisis del intent
        """
        if not messages:
            return {"intent": "unknown", "entities": {}}

        # Obtener el último mensaje del usuario
        user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        if not user_message:
            return {"intent": "unknown", "entities": {}}

        # Análisis básico de intent
        user_lower = user_message.lower()

        # Detectar tipo de consulta
        intent = "general"
        entities = {}

        # Búsqueda de propiedades
        if any(keyword in user_lower for keyword in ["buscar", "busco", "necesito", "quiero", "buscar", "muestrame"]):
            intent = "property_search"

            # Extraer entidades
            if "casa" in user_lower:
                entities["property_type"] = "casa"
            elif "departamento" in user_lower or "apartamento" in user_lower:
                entities["property_type"] = "departamento"

            # Extraer presupuesto
            import re
            precios = re.findall(r'(\$?\d+(?:,\d+)*)\s*(?:usd|dólares|bolivianos|bs)?', user_lower)
            if precios:
                entities["budget"] = precios[0]

            # Extraer zona
            zonas = ["equipetrol", "santa mónica", "urbari", "los olivos", "zona norte", "zona sur", "centro"]
            for zona in zonas:
                if zona in user_lower:
                    entities["zone"] = zona
                    break

        # Análisis de mercado
        elif any(keyword in user_lower for keyword in ["precio", "promedio", "mercado", "análisis", "tendencia"]):
            intent = "market_analysis"

        # Información general
        elif any(keyword in user_lower for keyword in ["información", "saber", "conocer", "explicar"]):
            intent = "general_info"

        return {"intent": intent, "entities": entities, "message": user_message}

    def generate_property_search_response(self, entities: Dict[str, Any]) -> str:
        """
        Genera respuesta para búsqueda de propiedades.

        Args:
            entities: Entidades extraídas del mensaje

        Returns:
            Respuesta generada
        """
        try:
            # Construir filtros para búsqueda
            filtros = {}

            if entities.get("property_type"):
                filtros["tipo_propiedad"] = entities["property_type"]

            if entities.get("zone"):
                filtros["zona"] = entities["zone"].title()

            if entities.get("budget"):
                # Extraer valor numérico del presupuesto
                import re
                budget_str = entities["budget"]
                budget_num = re.sub(r'[^\d]', '', budget_str)
                try:
                    budget = float(budget_num)
                    filtros["precio_max"] = budget
                except:
                    pass

            # Buscar propiedades usando el motor de recomendaciones
            if self.recommendation_engine:
                perfil = {
                    "id": "chatbot_search",
                    "presupuesto": {
                        "min": 0,
                        "max": filtros.get("precio_max", 1000000)
                    },
                    "preferencias": {
                        "ubicacion": filtros.get("zona", ""),
                        "tipo_propiedad": filtros.get("tipo_propiedad", "")
                    },
                    "necesidades": []
                }

                recomendaciones = self.recommendation_engine.generar_recomendaciones(
                    perfil,
                    limite=5,
                    umbral_minimo=0.01  # Bajo umbral para mostrar resultados
                )

                if recomendaciones:
                    response = f"Encontré {len(recomendaciones)} propiedades que coinciden con tu búsqueda:\n\n"

                    for i, rec in enumerate(recomendaciones[:3], 1):
                        prop = rec["propiedad"]

                        response += f"**{i}. {prop.get('tipo_propiedad', 'Propiedad').title()} en {prop.get('zona', 'Zona')}**\n"

                        if prop.get('precio'):
                            response += f"Precio: ${prop.get('precio', 0):,.0f} USD\n"

                        if prop.get('habitaciones'):
                            response += f"Habitaciones: {prop.get('habitaciones')}\n"

                        if prop.get('superficie'):
                            response += f"Superficie: {prop.get('superficie')} m²\n"

                        response += f"Justificación: {rec.get('justificacion', 'Buena opción')}\n\n"

                    response += "¿Te gustaría más detalles sobre alguna de estas propiedades?"
                    return response
                else:
                    return "No encontré propiedades que coincidan exactamente con tus criterios. ¿Podrías ajustar algún parámetro de búsqueda?"
            else:
                return "El motor de búsqueda no está disponible en este momento. Por favor, intenta más tarde."

        except Exception as e:
            logger.error(f"Error en búsqueda de propiedades: {e}")
            return "Tuve un problema al buscar propiedades. Por favor, intenta con diferentes criterios."

    def generate_market_analysis_response(self, entities: Dict[str, Any]) -> str:
        """
        Genera respuesta para análisis de mercado.

        Args:
            entities: Entidades extraídas

        Returns:
            Respuesta generada
        """
        try:
            zone = entities.get("zone", "Santa Cruz")

            # Análisis básico con las propiedades cargadas
            if self.propiedades:
                propiedades_zona = [p for p in self.propiedades
                                  if zone.lower() in p.get('zona', '').lower()]

                if propiedades_zona:
                    precios = [p.get('precio') for p in propiedades_zona if p.get('precio')]

                    if precios:
                        promedio = sum(precios) / len(precios)
                        minimo = min(precios)
                        maximo = max(precios)

                        response = f"**Análisis de mercado para {zone.title()}**\n\n"
                        response += f"Propiedades disponibles: {len(propiedades_zona)}\n"
                        response += f"Precio promedio: ${promedio:,.0f} USD\n"
                        response += f"Rango de precios: ${minimo:,.0f} - ${maximo:,.0f} USD\n\n"

                        # Tipos de propiedad
                        tipos = {}
                        for prop in propiedades_zona:
                            tipo = prop.get('tipo_propiedad', 'Otro')
                            tipos[tipo] = tipos.get(tipo, 0) + 1

                        if tipos:
                            response += "**Distribución por tipo:**\n"
                            for tipo, count in sorted(tipos.items(), key=lambda x: x[1], reverse=True):
                                response += f"- {tipo.title()}: {count} propiedades\n"

                        response += f"\n¿Te gustaría ver propiedades específicas en {zone.title()}?"
                        return response
                    else:
                        return f"No hay información de precios disponible para {zone.title()}."
                else:
                    return f"No encontré propiedades registradas en {zone.title()}."
            else:
                return "No hay datos de mercado disponibles en este momento."

        except Exception as e:
            logger.error(f"Error en análisis de mercado: {e}")
            return "Tuve un problema al analizar el mercado. Por favor, intenta más tarde."

    def generate_general_info_response(self, message: str) -> str:
        """
        Genera respuesta para información general.

        Args:
            message: Mensaje del usuario

        Returns:
            Respuesta generada
        """
        try:
            # Usar LLM si está disponible
            if self.llm:
                prompt = f"""Eres el asistente inmobiliario de Citrino. Responde a esta consulta de manera profesional y útil:

Consulta: {message}

Contexto: Tienes acceso a 1,385 propiedades en Santa Cruz de la Sierra, Bolivia.
Las zonas principales incluyen Equipetrol, Santa Mónica, Urbari, Los Olivos, etc.

Responde de manera concisa pero informativa, enfocándote en información práctica para decisiones inmobiliarias."""

                resultado = self.llm.consultar_con_fallback(prompt, use_fallback=True)
                return resultado.get("respuesta", "No pude procesar tu consulta en este momento.")
            else:
                # Respuesta fallback sin LLM
                return """Soy el asistente inmobiliario de Citrino. Puedo ayudarte con:

🏠 **Búsqueda de propiedades**: Dime qué buscas (zona, presupuesto, características)

📊 **Análisis de mercado**: Precios promedio, tendencias por zona

🏘️ **Información de zonas**: Características de los barrios de Santa Cruz

💰 **Asesoría de inversión**: Oportunidades y potencial de plusvalía

¿Qué te gustaría consultar hoy?"""

        except Exception as e:
            logger.error(f"Error generando respuesta general: {e}")
            return "Tuve un problema al procesar tu consulta. Por favor, intenta nuevamente."

    def process_chat_completion(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa una solicitud de chat completion.

        Args:
            data: Datos de la solicitud OpenAI-compatible

        Returns:
            Respuesta OpenAI-compatible
        """
        try:
            messages = data.get("messages", [])
            model = data.get("model", "citrino-v1")

            # Analizar intent del mensaje
            analysis = self.analyze_message_intent(messages)

            # Generar respuesta según el intent
            if analysis["intent"] == "property_search":
                content = self.generate_property_search_response(analysis["entities"])
            elif analysis["intent"] == "market_analysis":
                content = self.generate_market_analysis_response(analysis["entities"])
            else:
                content = self.generate_general_info_response(analysis.get("message", ""))

            # Formatear respuesta OpenAI-compatible
            return self.format_openai_response(content, model)

        except Exception as e:
            logger.error(f"Error procesando chat completion: {e}")

            # Respuesta de error
            error_content = "Lo siento, tuve un problema procesando tu solicitud. Por favor, intenta nuevamente."
            return self.format_openai_response(error_content, model)

# Instancia global del chatbot
chatbot_api = CitrinoChatbotAPI()

def create_chatbot_routes(app: Flask):
    """
    Crea las rutas para la API del chatbot.

    Args:
        app: Aplicación Flask
    """

    @app.route('/v1/chat/completions', methods=['POST'])
    def chat_completions():
        """
        Endpoint compatible con OpenAI Chat Completions.
        """
        try:
            data = request.get_json()

            if not data:
                return jsonify({
                    "error": {
                        "message": "No se proporcionaron datos",
                        "type": "invalid_request_error"
                    }
                }), 400

            # Procesar la solicitud
            response = chatbot_api.process_chat_completion(data)

            return jsonify(response)

        except Exception as e:
            logger.error(f"Error en chat completions: {e}")
            return jsonify({
                "error": {
                    "message": "Error interno del servidor",
                    "type": "server_error"
                }
            }), 500

    @app.route('/v1/models', methods=['GET'])
    def list_models():
        """
        Endpoint para listar modelos disponibles.
        """
        return jsonify({
            "object": "list",
            "data": [
                {
                    "id": "citrino-v1",
                    "object": "model",
                    "created": int(datetime.now().timestamp()),
                    "owned_by": "citrino"
                }
            ]
        })

    @app.route('/v1/models/<model_id>', methods=['GET'])
    def get_model(model_id: str):
        """
        Endpoint para obtener información de un modelo.
        """
        if model_id == "citrino-v1":
            return jsonify({
                "id": "citrino-v1",
                "object": "model",
                "created": int(datetime.now().timestamp()),
                "owned_by": "citrino"
            })
        else:
            return jsonify({
                "error": {
                    "message": f"Modelo '{model_id}' no encontrado",
                    "type": "invalid_request_error"
                }
            }), 404

if __name__ == "__main__":
    # Para pruebas manuales
    app = Flask(__name__)
    create_chatbot_routes(app)
    app.run(debug=True, host='0.0.0.0', port=5001)