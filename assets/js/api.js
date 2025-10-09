/**
 * Módulo de API para Citrino
 * Maneja la comunicación con el backend Flask
 */

class CitrinoAPI {
    constructor() {
        // Detectar entorno automáticamente
        const isDev = window.location.hostname === 'localhost' || 
                      window.location.hostname === '127.0.0.1' ||
                      window.location.hostname === '';
        
        // Configuración base de la API según entorno
        this.baseURL = isDev 
            ? 'http://localhost:5001/api'
            : (window.CITRINO_API_URL || 'https://citrino-api.onrender.com/api');
        
        this.timeout = 30000; // 30 segundos
        this.isDevelopment = isDev;

        // Configuración de headers por defecto
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };

        // Estado de la conexión
        this.isOnline = navigator.onLine;
        this.connectionRetryCount = 0;
        this.maxRetries = 3;
        
        // Log del entorno
        console.log(`[Citrino API] Entorno: ${isDev ? 'Desarrollo' : 'Producción'}`);
        console.log(`[Citrino API] Base URL: ${this.baseURL}`);

        // Event listeners para conexión
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.connectionRetryCount = 0;
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
        });
    }

    /**
     * Realiza una petición HTTP con manejo de errores y reintentos
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: { ...this.defaultHeaders, ...options.headers },
            timeout: this.timeout,
            ...options
        };

        try {
            if (!this.isOnline) {
                throw new Error('Sin conexión a internet');
            }

            // Mostrar loading si se proporciona un callback
            if (config.onLoadingStart) {
                config.onLoadingStart();
            }

            const response = await fetch(url, config);

            // Resetear contador de reintentos si la petición es exitosa
            this.connectionRetryCount = 0;

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            // Ocultar loading si se proporciona un callback
            if (config.onLoadingEnd) {
                config.onLoadingEnd();
            }

            return data;

        } catch (error) {
            // Ocultar loading si se proporciona un callback
            if (config.onLoadingEnd) {
                config.onLoadingEnd();
            }

            // Reintentar automáticamente si es un error de conexión
            if (this.shouldRetry(error) && this.connectionRetryCount < this.maxRetries) {
                this.connectionRetryCount++;
                console.log(`Reintentando petición (${this.connectionRetryCount}/${this.maxRetries})...`);
                await this.delay(1000 * this.connectionRetryCount);
                return this.request(endpoint, options);
            }

            throw error;
        }
    }

    /**
     * Determina si se debe reintentar una petición
     */
    shouldRetry(error) {
        return (
            error.message.includes('fetch') ||
            error.message.includes('network') ||
            error.message.includes('timeout') ||
            error.message.includes('connection')
        );
    }

    /**
     * Función de delay para reintentos
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Verifica el estado de salud de la API
     */
    async healthCheck() {
        try {
            const response = await this.request('/health');
            return {
                success: true,
                data: response,
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            return {
                success: false,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * Busca propiedades con filtros
     */
    async searchProperties(filters = {}) {
        try {
            const response = await this.request('/buscar', {
                method: 'POST',
                body: JSON.stringify(filters)
            });

            return {
                success: true,
                data: response,
                count: response.total_resultados || 0
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Genera recomendaciones basadas en perfil
     */
    async getRecommendations(profile, options = {}) {
        try {
            const requestData = {
                ...profile,
                limite: options.limite || 10,
                umbral_minimo: options.umbral_minimo || 0.3
            };

            const response = await this.request('/recomendar', {
                method: 'POST',
                body: JSON.stringify(requestData)
            });

            return {
                success: true,
                data: response,
                recommendations: response.recomendaciones || [],
                briefing: response.briefing_personalizado
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Genera recomendaciones mejoradas con georreferenciación
     */
    async getEnhancedRecommendations(profile, options = {}) {
        try {
            const requestData = {
                ...profile,
                limite: options.limite || 5,
                umbral_minimo: options.umbral_minimo || 0.3
            };

            const response = await this.request('/recomendar-mejorado', {
                method: 'POST',
                body: JSON.stringify(requestData)
            });

            return {
                success: true,
                data: response,
                recommendations: response.recomendaciones || [],
                engine: 'mejorado_con_georreferenciacion'
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Obtiene estadísticas generales del sistema
     */
    async getStatistics() {
        try {
            const response = await this.request('/estadisticas');
            return {
                success: true,
                data: response.estadisticas
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Obtiene la lista de zonas disponibles
     */
    async getZones() {
        try {
            const response = await this.request('/zonas');
            return {
                success: true,
                data: response.zonas || []
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Obtiene detalles de una propiedad específica
     */
    async getPropertyDetails(propertyId) {
        try {
            const response = await this.request(`/property/${propertyId}`);
            return {
                success: true,
                data: response
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Procesa lenguaje natural con LLM
     */
    async processNaturalLanguage(text) {
        try {
            const response = await this.request('/natural-language', {
                method: 'POST',
                body: JSON.stringify({ text })
            });

            return {
                success: true,
                data: response
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Procesa mensaje de chat con z.ai y genera recomendaciones
     */
    async processChatWithLLM(message) {
        try {
            const response = await this.request('/chat/process', {
                method: 'POST',
                body: JSON.stringify({ mensaje: message })
            });

            return {
                success: true,
                profile: response.perfil,
                recommendations: response.recomendaciones || [],
                response: response.respuesta,
                llmUsed: response.llm_usado
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Guarda un perfil de cliente
     */
    async saveProfile(profile) {
        try {
            // En una implementación real, esto llamaría a un endpoint del backend
            // Por ahora, guardamos en localStorage
            const profiles = this.getStoredProfiles();
            const profileWithId = {
                ...profile,
                id: this.generateId(),
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString()
            };

            profiles.push(profileWithId);
            localStorage.setItem('citrino_profiles', JSON.stringify(profiles));

            return {
                success: true,
                data: profileWithId
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Obtiene perfiles guardados
     */
    getStoredProfiles() {
        try {
            const profiles = localStorage.getItem('citrino_profiles');
            return profiles ? JSON.parse(profiles) : [];
        } catch (error) {
            console.error('Error al cargar perfiles guardados:', error);
            return [];
        }
    }

    /**
     * Elimina un perfil guardado
     */
    deleteProfile(profileId) {
        try {
            const profiles = this.getStoredProfiles();
            const filteredProfiles = profiles.filter(p => p.id !== profileId);
            localStorage.setItem('citrino_profiles', JSON.stringify(filteredProfiles));

            return {
                success: true
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Genera un ID único
     */
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    /**
     * Formatea un perfil para la API
     */
    formatProfileForAPI(formData) {
        return {
            id: formData.id || 'perfil_web',
            presupuesto_min: parseFloat(formData.presupuesto_min) || 0,
            presupuesto_max: parseFloat(formData.presupuesto_max) || 1000000,
            adultos: parseInt(formData.adultos) || 1,
            ninos: formData.ninos ? formData.ninos.split(',').map(age => parseInt(age.trim())).filter(age => !isNaN(age)) : [],
            adultos_mayores: parseInt(formData.adultos_mayores) || 0,
            zona_preferida: formData.zona_preferida || '',
            tipo_propiedad: formData.tipo_propiedad || '',
            necesidades: Array.isArray(formData.necesidades) ? formData.necesidades : (formData.necesidades ? formData.necesidades.split(',') : []),
            caracteristicas_deseadas: formData.caracteristicas_deseadas ? formData.caracteristicas_deseadas.split(',') : [],
            seguridad: formData.seguridad || null,
            estilo_vida: formData.estilo_vida || ''
        };
    }

    /**
     * Valida un perfil antes de enviarlo
     */
    validateProfile(profile) {
        const errors = [];

        // Validación de presupuesto
        if (!profile.presupuesto_min || !profile.presupuesto_max) {
            errors.push('Debe especificar un presupuesto mínimo y máximo');
        } else if (profile.presupuesto_min >= profile.presupuesto_max) {
            errors.push('El presupuesto mínimo debe ser menor al máximo');
        }

        // Validación de composición familiar
        if (!profile.adultos || profile.adultos < 1) {
            errors.push('Debe especificar al menos un adulto');
        }

        // Validación de zona
        if (!profile.zona_preferida) {
            errors.push('Debe especificar una zona de preferencia');
        }

        return {
            isValid: errors.length === 0,
            errors
        };
    }

    /**
     * Obtiene el estado de conexión
     */
    getConnectionStatus() {
        return {
            isOnline: this.isOnline,
            retryCount: this.connectionRetryCount,
            maxRetries: this.maxRetries
        };
    }

    /**
     * Limpia el caché local
     */
    clearCache() {
        try {
            localStorage.removeItem('citrino_profiles');
            localStorage.removeItem('citrino_search_history');
            return {
                success: true
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Exporta datos de usuario
     */
    exportUserData() {
        try {
            const userData = {
                profiles: this.getStoredProfiles(),
                searchHistory: this.getSearchHistory(),
                exportDate: new Date().toISOString(),
                version: '1.0'
            };

            const dataStr = JSON.stringify(userData, null, 2);
            const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);

            const exportFileDefaultName = `citrino_data_${new Date().toISOString().split('T')[0]}.json`;

            const linkElement = document.createElement('a');
            linkElement.setAttribute('href', dataUri);
            linkElement.setAttribute('download', exportFileDefaultName);
            linkElement.click();

            return {
                success: true
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Obtiene historial de búsquedas
     */
    getSearchHistory() {
        try {
            const history = localStorage.getItem('citrino_search_history');
            return history ? JSON.parse(history) : [];
        } catch (error) {
            console.error('Error al cargar historial de búsquedas:', error);
            return [];
        }
    }

    /**
     * Guarda una búsqueda en el historial
     */
    saveSearch(searchData) {
        try {
            const history = this.getSearchHistory();
            const searchWithTimestamp = {
                ...searchData,
                timestamp: new Date().toISOString()
            };

            // Mantener solo las últimas 50 búsquedas
            history.unshift(searchWithTimestamp);
            if (history.length > 50) {
                history.splice(50);
            }

            localStorage.setItem('citrino_search_history', JSON.stringify(history));
            return {
                success: true
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }
}

// Crear instancia global de la API
window.citrinoAPI = new CitrinoAPI();

// Exportar para módulos si está disponible
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CitrinoAPI;
}