#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor Unificado Citrino v2.3.0
Chatbot como reemplazo principal de Reco
API completa con motor de recomendación y análisis
"""

import os
import sys
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import logging

# Agregar paths del proyecto
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar componentes
try:
    from recommendation_engine_mejorado import RecommendationEngineMejorado
    from chatbot_completions import CitrinoChatbotAPI, create_chatbot_routes
    from prompts.system_prompt_chat import CITRINO_CHAT_SYSTEM_PROMPT, CITRINO_CHAT_CONFIG
    COMPONENTS_AVAILABLE = True
    logger.info("Todos los componentes importados exitosamente")
except ImportError as e:
    logger.error(f"Error importando componentes: {e}")
    COMPONENTS_AVAILABLE = False

class CitrinoUnifiedServer:
    """Servidor unificado para Citrino con chatbot como principal"""

    def __init__(self):
        self.app = Flask(__name__, static_folder='.', static_url_path='')
        CORS(self.app)

        # Inicializar componentes
        self.recommendation_engine = None
        self.chatbot_api = None
        self.propiedades = []
        self.stats = {
            'inicio_servidor': datetime.now().isoformat(),
            'consultas_chatbot': 0,
            'recomendaciones_generadas': 0,
            'servicios_cargados': 0
        }

        # Configurar rutas
        self._setup_routes()

        # Inicializar motores
        self._initialize_engines()

    def _initialize_engines(self):
        """Inicializa los motores de recomendación y chatbot"""
        if not COMPONENTS_AVAILABLE:
            logger.warning("Componentos no disponibles, funcionando en modo limitado")
            return

        try:
            # Inicializar motor de recomendación
            self.recommendation_engine = RecommendationEngineMejorado()
            self._load_properties()
            self.recommendation_engine.cargar_guias_urbanas()

            # Inicializar chatbot
            self.chatbot_api = CitrinoChatbotAPI()

            # Actualizar estadísticas
            self.stats['servicios_cargados'] = len(self.recommendation_engine.guias_urbanas)

            logger.info("Motores inicializados exitosamente")
            logger.info(f"Propiedades cargadas: {len(self.propiedades)}")
            logger.info(f"Servicios urbanos: {self.stats['servicios_cargados']}")

        except Exception as e:
            logger.error(f"Error inicializando motores: {e}")

    def _load_properties(self):
        """Carga las propiedades desde archivos JSON"""
        try:
            rutas_posibles = [
                'data/base_datos_relevamiento.json',
                'data/base_datos_citrino_limpios.json'
            ]

            for ruta in rutas_posibles:
                if os.path.exists(ruta):
                    with open(ruta, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.propiedades = data.get('propiedades', [])
                        break

            if self.recommendation_engine and self.propiedades:
                self.recommendation_engine.cargar_propiedades(self.propiedades)

            logger.info(f"Cargadas {len(self.propiedades)} propiedades")

        except Exception as e:
            logger.error(f"Error cargando propiedades: {e}")
            self.propiedades = []

    def _setup_routes(self):
        """Configura todas las rutas del servidor"""

        # Rutas estáticas (servir archivos HTML, CSS, JS)
        @self.app.route('/')
        def index():
            return send_from_directory('.', 'index.html')

        @self.app.route('/chat.html')
        def chat_page():
            return send_from_directory('.', 'chat.html')

        @self.app.route('/citrino-reco.html')
        def reco_page():
            return send_from_directory('.', 'citrino-reco.html')

        @self.app.route('/assets/<path:filename>')
        def assets(filename):
            return send_from_directory('assets', filename)

        # API endpoints
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Endpoint de salud del sistema"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '2.3.0',
                'components': {
                    'recommendation_engine': self.recommendation_engine is not None,
                    'chatbot_api': self.chatbot_api is not None,
                    'properties_loaded': len(self.propiedades)
                },
                'stats': self.stats
            })

        @self.app.route('/api/recommend', methods=['POST'])
        def recommend_properties():
            """Endpoint de recomendación (compatibilidad con Reco)"""
            if not self.recommendation_engine:
                return jsonify({'error': 'Motor de recomendación no disponible'}), 503

            try:
                data = request.get_json()
                perfil = data.get('perfil', {})
                limite = data.get('limite', 5)

                recomendaciones = self.recommendation_engine.generar_recomendaciones(perfil, limite)
                self.stats['recomendaciones_generadas'] += 1

                return jsonify({
                    'recomendaciones': recomendaciones,
                    'total': len(recomendaciones),
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"Error en recomendación: {e}")
                return jsonify({'error': 'Error generando recomendaciones'}), 500

        @self.app.route('/api/search', methods=['POST'])
        def search_properties():
            """Endpoint de búsqueda de propiedades"""
            if not self.recommendation_engine:
                return jsonify({'error': 'Motor de búsqueda no disponible'}), 503

            try:
                data = request.get_json()
                filtros = data.get('filtros', {})

                resultados = self.recommendation_engine.buscar_por_filtros(filtros)

                return jsonify({
                    'resultados': resultados,
                    'total': len(resultados),
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"Error en búsqueda: {e}")
                return jsonify({'error': 'Error en búsqueda'}), 500

        @self.app.route('/api/stats', methods=['GET'])
        def get_stats():
            """Endpoint de estadísticas del sistema"""
            if not self.recommendation_engine:
                return jsonify({'error': 'Estadísticas no disponibles'}), 503

            try:
                stats_engine = self.recommendation_engine.obtener_estadisticas_rendimiento()

                return jsonify({
                    'sistema': self.stats,
                    'motor_recomendacion': stats_engine,
                    'propiedades': len(self.propiedades),
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"Error obteniendo estadísticas: {e}")
                return jsonify({'error': 'Error obteniendo estadísticas'}), 500

        # Rutas del chatbot (compatibilidad OpenAI)
        if COMPONENTS_AVAILABLE:
            create_chatbot_routes(self.app)

        # Endpoint adicional para el chatbot (no OpenAI-compatible)
        @self.app.route('/api/chat/simple', methods=['POST'])
        def simple_chat():
            """Endpoint simple para chatbot sin compatibilidad OpenAI"""
            if not self.chatbot_api:
                return jsonify({'error': 'Chatbot no disponible'}), 503

            try:
                data = request.get_json()
                message = data.get('message', '')

                # Simular messages para el chatbot
                messages = [{"role": "user", "content": message}]
                chat_data = {"messages": messages}

                response = self.chatbot_api.process_chat_completion(chat_data)
                content = response.get("choices", [{}])[0].get("message", {}).get("content", "")

                self.stats['consultas_chatbot'] += 1

                return jsonify({
                    'response': content,
                    'timestamp': datetime.now().isoformat(),
                    'query': message
                })

            except Exception as e:
                logger.error(f"Error en chat simple: {e}")
                return jsonify({'error': 'Error procesando consulta'}), 500

        @self.app.route('/api/zones', methods=['GET'])
        def get_zones():
            """Endpoint para obtener zonas disponibles"""
            try:
                if not self.propiedades:
                    return jsonify({'zones': []})

                zonas = set()
                for prop in self.propiedades[:500]:  # Muestra para rendimiento
                    zona = prop.get('zona') or prop.get('ubicacion', {}).get('zona')
                    if zona:
                        zonas.add(zona)

                return jsonify({
                    'zones': sorted(list(zonas)),
                    'total': len(zonas),
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"Error obteniendo zonas: {e}")
                return jsonify({'error': 'Error obteniendo zonas'}), 500

        # Manejo de errores
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({'error': 'Recurso no encontrado'}), 404

        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({'error': 'Error interno del servidor'}), 500

        logger.info("Rutas configuradas exitosamente")

    def run(self, host='0.0.0.0', port=8080, debug=False):
        """Inicia el servidor unificado"""
        logger.info(f"Iniciando servidor Citrino v2.3.0 en http://{host}:{port}")
        logger.info(f"Modo debug: {debug}")

        self.app.run(host=host, port=port, debug=debug)

def main():
    """Función principal"""
    print("=" * 60)
    print("CITRINO SERVIDOR UNIFICADO v2.3.0")
    print("Chatbot como reemplazo principal de Reco")
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Crear servidor
    server = CitrinoUnifiedServer()

    # Iniciar servidor
    server.run(
        host='127.0.0.1',
        port=5000,
        debug=False
    )

if __name__ == '__main__':
    main()