/**
 * Cliente de Chatbot Citrino v2.3.0 - Optimizado para GitHub Pages
 * Funciona con o sin servidor backend
 */

class CitrinoChatbotClient {
    constructor() {
        this.apiBase = this.detectAPIBase();
        this.fallbackMode = false;
        this.sessionId = this.generateSessionId();
        this.conversationHistory = [];
    }

    detectAPIBase() {
        // Detectar si estamos en GitHub Pages o localmente
        if (window.location.hostname === 'vincentiwadsworth.github.io') {
            // GitHub Pages - usar API pública o demo
            return 'https://api.citrino.bo'; // API pública futura
        } else if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            // Desarrollo local
            return 'http://127.0.0.1:5000';
        } else {
            // Otro dominio - intentar detectar API
            return `${window.location.protocol}//${window.location.hostname}:5000`;
        }
    }

    generateSessionId() {
        return 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    async sendMessage(message, conversationHistory = []) {
        this.conversationHistory = conversationHistory;

        try {
            // Intentar usar API real primero
            const response = await this.callRealAPI(message);
            if (response.success) {
                return response;
            }
        } catch (error) {
            console.warn('API no disponible, usando modo demo:', error);
        }

        // Fallback a modo demo con datos predefinidos
        return this.generateDemoResponse(message);
    }

    async callRealAPI(message) {
        const payload = {
            message: message,
            session_id: this.sessionId,
            conversation_history: this.conversationHistory,
            timestamp: new Date().toISOString()
        };

        const response = await fetch(`${this.apiBase}/api/chat/simple`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Citrino-Client': 'web-chatbot-v2.3.0'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        return {
            success: true,
            data: data,
            llmUsed: true,
            source: 'api'
        };
    }

    generateDemoResponse(message) {
        const lowerMessage = message.toLowerCase();

        // Análisis del mensaje para generar respuesta contextual
        let response = '';
        let recommendations = [];
        let profile = null;

        // Extraer información del perfil
        profile = this.extractProfileFromMessage(message);

        // Generar respuesta según el tipo de consulta
        if (lowerMessage.includes('departamento') && lowerMessage.includes('equipetrol')) {
            response = 'He encontrado excelentes opciones de departamentos en Equipetrol. Esta zona es una de las más exclusivas de Santa Cruz con alta demanda de alquiler y plusvalía constante. Los departamentos en Equipetrol se caracterizan por su seguridad, accesos comerciales y excelente infraestructura.\n\n¿En qué rango de precios te interesa?';
            recommendations = this.getDemoProperties('departamento', 'Equipetrol');

        } else if (lowerMessage.includes('casa') && (lowerMessage.includes('los olivos') || lowerMessage.includes('santa mónica'))) {
            const zona = lowerMessage.includes('los olivos') ? 'Los Olivos' : 'Santa Mónica';
            response = `Las casas en ${zona} son ideales para familias que buscan tranquilidad y servicios completos. ${zona} ofrece excelentes colegios, parques y una creciente infraestructura comercial.\n\nLas propiedades en esta zona tienen buen potencial de plusvalía a mediano plazo debido al desarrollo continuo de la zona.`;
            recommendations = this.getDemoProperties('casa', zona);

        } else if (lowerMessage.includes('inversión') || lowerMessage.includes('renta') || lowerMessage.includes('plusvalía')) {
            response = 'Para inversión en Santa Cruz, te recomiendo enfocarte en zonas con alta demanda y potencial de desarrollo como Equipetrol, Urbari o áreas cercanas a nuevos proyectos comerciales.\n\nFactores clave para inversión:\n• Proximidad a centros educativos y comerciales\n• Accesibilidad y vías principales\n• Zonas con desarrollo urbano planificado\n• Demanda histórica de alquiler\n\n¿Cuál es tu rango de presupuesto para la inversión?';

        } else if (lowerMessage.includes('precio') || lowerMessage.includes('cuánto') || lowerMessage.includes('costo')) {
            response = 'Los precios en Santa Cruz varían significativamente según la zona:\n\n**Zonas Premium:**\n• Equipetrol: $150,000 - $400,000+ (departamentos)\n• Santa Mónica: $120,000 - $350,000 (casas)\n• Urbari: $100,000 - $300,000 (mixto)\n\n**Zonas Económicas:**\n• Zonas periféricas: $50,000 - $150,000\n• Áreas en desarrollo: $70,000 - $200,000\n\n¿Qué zona te interesa más y cuál es tu presupuesto?';

        } else if (lowerMessage.includes('familia') || lowerMessage.includes('niños') || lowerMessage.includes('hijos')) {
            response = 'Para familias recomiendo zonas con buenos colegios, seguridad y áreas verdes:\n\n**Mejores Opciones para Familias:**\n• Santa Mónica: Excelentes colegios, parques, ambiente familiar\n• Los Olivos: Tranquilidad, espacios verdes, buena plusvalía\n• Equipetrol: Seguridad, servicios premium, accesos rápidos\n\nConsidera también la proximidad a centros educativos de calidad y servicios médicos. ¿Cuántos hijos tienes y qué edad tienen?';

        } else {
            // Respuesta genérica
            response = 'Entiendo tu interés en el mercado inmobiliario de Santa Cruz. Para darte las mejores recomendaciones, necesito saber más detalles:\n\n• ¿Tu presupuesto aproximado?\n• ¿Buscas para vivir o invertir?\n• ¿Qué tipo de propiedad prefieres (casa, departamento, etc.)?\n• ¿Alguna zona en particular?\n• ¿Servicios importantes para ti (colegios, hospitales, etc.)?\n\nCon esta información podré darte recomendaciones más precisas.';
        }

        // Si se extrajo perfil, agregar recomendaciones
        if (profile) {
            recommendations = this.getDemoProperties(
                profile.tipo_propiedad || 'departamento',
                profile.zona_preferida || null
            );
        }

        return {
            success: true,
            data: {
                response: response,
                profile: profile,
                recommendations: recommendations,
                llmUsed: false,
                source: 'demo',
                session_id: this.sessionId
            }
        };
    }

    extractProfileFromMessage(message) {
        const lowerMessage = message.toLowerCase();

        let profile = {
            presupuesto_min: null,
            presupuesto_max: null,
            zona_preferida: null,
            tipo_propiedad: null,
            necesidades: []
        };

        // Extraer presupuesto
        const presupuestoMatch = message.match(/\$(\d+(?:,\d+)*)/g);
        if (presupuestoMatch) {
            const amounts = presupuestoMatch.map(p => parseInt(p.replace('$', '').replace(',', '')));
            profile.presupuesto_min = Math.min(...amounts) * 0.8;
            profile.presupuesto_max = Math.max(...amounts) * 1.2;
        }

        // Extraer zona
        const zonas = ['equipetrol', 'santa mónica', 'urbari', 'los olivos', 'zona norte', 'zona sur', 'centro'];
        for (const zona of zonas) {
            if (lowerMessage.includes(zona)) {
                profile.zona_preferida = zona.charAt(0).toUpperCase() + zona.slice(1);
                break;
            }
        }

        // Extraer tipo de propiedad
        if (lowerMessage.includes('departamento') || lowerMessage.includes('apartamento')) {
            profile.tipo_propiedad = 'departamento';
        } else if (lowerMessage.includes('casa')) {
            profile.tipo_propiedad = 'casa';
        } else if (lowerMessage.includes('penthouse')) {
            profile.tipo_propiedad = 'penthouse';
        } else if (lowerMessage.includes('terreno')) {
            profile.tipo_propiedad = 'terreno';
        }

        // Extraer necesidades
        if (lowerMessage.includes('colegio') || lowerMessage.includes('escuela')) {
            profile.necesidades.push('educacion');
        }
        if (lowerMessage.includes('hospital') || lowerMessage.includes('clinica')) {
            profile.necesidades.push('salud');
        }
        if (lowerMessage.includes('seguridad')) {
            profile.necesidades.push('seguridad');
        }
        if (lowerMessage.includes('parque') || lowerMessage.includes('jardín')) {
            profile.necesidades('areas_verdes');
        }

        // Verificar si se extrajo información suficiente
        const hasInfo = profile.presupuesto_max || profile.zona_preferida || profile.tipo_propiedad || profile.necesidades.length > 0;
        return hasInfo ? profile : null;
    }

    getDemoProperties(tipo, zona) {
        const demoProperties = [
            {
                id: 'demo_1',
                nombre: tipo === 'departamento' ? 'Departamento Premium en Equipetrol' : 'Casa Familiar en Santa Mónica',
                tipo: tipo,
                zona: zona || 'Equipetrol',
                precio: tipo === 'departamento' ? 220000 : 280000,
                habitaciones: 3,
                banos: 2,
                superficie_m2: tipo === 'departamento' ? 120 : 180,
                compatibilidad: 92,
                justificacion: 'Ubicación privilegiada con excelente acceso a servicios comerciales y educativos. Alto potencial de plusvalía y demanda constante de alquiler.',
                caracteristicas: ['garaje', 'seguridad_24h', 'piscina', 'gimnasio']
            },
            {
                id: 'demo_2',
                nombre: tipo === 'departamento' ? 'Departamento Moderno en Urbarí' : 'Casa Residencial en Los Olivos',
                tipo: tipo,
                zona: zona || 'Urbari',
                precio: tipo === 'departamento' ? 180000 : 240000,
                habitaciones: 2,
                banos: 2,
                superficie_m2: tipo === 'departamento' ? 95 : 150,
                compatibilidad: 87,
                justificacion: 'Zona en desarrollo con excelente potencial de crecimiento. Buena relación precio/valor y creciente infraestructura de servicios.',
                caracteristicas: ['cocina_integrada', 'balcon', 'estacionamiento']
            },
            {
                id: 'demo_3',
                nombre: tipo === 'departamento' ? 'Studio en Centro' : 'Casa con Jardín en Zona Norte',
                tipo: tipo,
                zona: zona || 'Centro',
                precio: tipo === 'departamento' ? 95000 : 320000,
                habitaciones: tipo === 'departamento' ? 1 : 4,
                banos: 1,
                superficie_m2: tipo === 'departamento' ? 45 : 220,
                compatibilidad: 78,
                justificacion: 'Excelente opción para inversión inicial o residencia. Buena ubicación con acceso a todos los servicios principales de la ciudad.',
                caracteristicas: ['amoblado', 'acceso_rapido', 'terraza']
            }
        ];

        // Filtrar por tipo y zona si se especificaron
        return demoProperties.filter(prop => {
            const tipoMatch = !tipo || prop.tipo === tipo;
            const zonaMatch = !zona || prop.zona.toLowerCase().includes(zona.toLowerCase());
            return tipoMatch && zonaMatch;
        });
    }

    async getHealthCheck() {
        try {
            const response = await fetch(`${this.apiBase}/api/health`);
            if (response.ok) {
                const data = await response.json();
                return {
                    success: true,
                    data: data,
                    source: 'api'
                };
            }
        } catch (error) {
            // Retornar estado demo
            return {
                success: true,
                data: {
                    status: 'demo',
                    timestamp: new Date().toISOString(),
                    version: '2.3.0-demo',
                    components: {
                        chatbot_api: true,
                        properties_loaded: 1578,
                        recommendation_engine: true
                    },
                    stats: {
                        consultas_chatbot: 0,
                        servicios_cargados: 4938
                    }
                },
                source: 'demo'
            };
        }
    }

    async getRecommendations(profile) {
        try {
            const response = await fetch(`${this.apiBase}/api/recommend`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Citrino-Client': 'web-chatbot-v2.3.0'
                },
                body: JSON.stringify({
                    perfil: profile,
                    limite: 5
                })
            });

            if (response.ok) {
                const data = await response.json();
                return {
                    success: true,
                    recommendations: data.recomendaciones || [],
                    source: 'api'
                };
            }
        } catch (error) {
            console.warn('API no disponible, usando recomendaciones demo:', error);
        }

        // Fallback a demo
        return {
            success: true,
            recommendations: this.getDemoProperties(
                profile.tipo_propiedad || 'departamento',
                profile.zona_preferida
            ),
            source: 'demo'
        };
    }
}

// Exportar para uso global
window.CitrinoChatbot = CitrinoChatbotClient;

// Inicializar automáticamente si estamos en la página de chat
if (document.getElementById('chatMessages')) {
    window.citrinoChatbot = new CitrinoChatbotClient();

    // Reemplazar la función de envío del chat
    const originalSendMessage = window.sendMessage;
    window.sendMessage = async function(message) {
        try {
            // Obtener historial actual
            const messages = document.querySelectorAll('.message');
            const history = Array.from(messages).map(msg => {
                const content = msg.querySelector('.message-bubble')?.textContent || '';
                const type = msg.classList.contains('user') ? 'user' : 'assistant';
                return { role: type, content: content };
            });

            // Usar el cliente del chatbot
            const result = await window.citrinoChatbot.sendMessage(message, history);

            if (result.success) {
                // Simular la respuesta del asistente
                const assistantMessage = {
                    type: 'assistant',
                    content: result.data.response,
                    timestamp: new Date().toISOString(),
                    profile: result.data.profile,
                    showRecommendationButton: result.data.recommendations?.length > 0 && !result.data.llmUsed
                };

                // Usar la función existente para agregar el mensaje
                if (typeof addMessage === 'function') {
                    addMessage(assistantMessage);

                    // Mostrar recomendaciones si hay
                    if (result.data.recommendations?.length > 0) {
                        chatRecommendations = result.data.recommendations;
                        setTimeout(() => {
                            addRecommendationsMessage(chatRecommendations, !result.data.llmUsed);
                        }, 500);
                    }
                }

                return result;
            }
        } catch (error) {
            console.error('Error sending message:', error);

            // Fallback a comportamiento original
            if (typeof originalSendMessage === 'function') {
                return originalSendMessage(message);
            }
        }
    };
}