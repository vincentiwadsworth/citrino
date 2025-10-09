/**
 * Citrino Frontend - JavaScript Principal
 * Funcionalidades globales compartidas entre todas las páginas
 */

// Configuración global
const CitrinoConfig = {
    apiURL: 'http://localhost:5000/api',
    appVersion: '1.0.0',
    appName: 'Citrino - Sistema de Recomendación Inmobiliaria',
    maxRetries: 3,
    timeoutDuration: 30000
};

// Estado global de la aplicación
const AppState = {
    currentUser: null,
    currentProfile: null,
    isOnline: navigator.onLine,
    theme: 'light',
    language: 'es'
};

// Utilidades
const Utils = {
    /**
     * Formatea números como moneda
     */
    formatCurrency: (amount, currency = 'USD') => {
        return new Intl.NumberFormat('es-BO', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 0
        }).format(amount);
    },

    /**
     * Formatea fechas
     */
    formatDate: (date, options = {}) => {
        const defaultOptions = {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        };
        return new Intl.DateTimeFormat('es-BO', { ...defaultOptions, ...options }).format(new Date(date));
    },

    /**
     * Sanitiza HTML para prevenir XSS
     */
    escapeHtml: (text) => {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * Genera un ID único
     */
    generateId: () => {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    },

    /**
     * Verifica si un objeto está vacío
     */
    isEmpty: (obj) => {
        return Object.keys(obj).length === 0;
    },

    /**
     * Debounce function para optimizar eventos
     */
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Throttle function para limitar ejecución
     */
    throttle: (func, limit) => {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};

// Sistema de notificaciones
const NotificationSystem = {
    /**
     * Muestra una notificación toast
     */
    showToast: (message, type = 'info', duration = 3000, position = 'top-end') => {
        const alertClass = type === 'success' ? 'alert-success' :
                         type === 'error' ? 'alert-danger' :
                         type === 'warning' ? 'alert-warning' : 'alert-info';
        const icon = type === 'success' ? 'bi-check-circle-fill' :
                    type === 'error' ? 'bi-exclamation-triangle-fill' :
                    type === 'warning' ? 'bi-exclamation-circle-fill' : 'bi-info-circle-fill';

        const toastId = 'toast_' + Utils.generateId();
        const positionClass = position === 'top-end' ? 'top-0 end-0' :
                             position === 'top-start' ? 'top-0 start-0' :
                             position === 'bottom-end' ? 'bottom-0 end-0' :
                             position === 'bottom-start' ? 'bottom-0 start-0' :
                             'top-0 end-0';

        const toastHTML = `
            <div id="${toastId}" class="alert ${alertClass} alert-dismissible fade show position-fixed ${positionClass} m-3" style="z-index: 1060;" role="alert">
                <div class="d-flex align-items-center">
                    <i class="bi ${icon} me-2 flex-shrink-0"></i>
                    <div class="flex-grow-1">${message}</div>
                    <button type="button" class="btn-close ms-2" data-bs-dismiss="alert"></button>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', toastHTML);

        // Auto remover después de duration
        setTimeout(() => {
            const toastElement = document.getElementById(toastId);
            if (toastElement) {
                const bsAlert = new bootstrap.Alert(toastElement);
                bsAlert.close();
            }
        }, duration);
    },

    /**
     * Muestra un diálogo de confirmación
     */
    showConfirm: async (title, message, confirmText = 'Confirmar', cancelText = 'Cancelar') => {
        return new Promise((resolve) => {
            const modalId = 'confirm_' + Utils.generateId();

            const modalHTML = `
                <div class="modal fade" id="${modalId}" tabindex="-1">
                    <div class="modal-dialog modal-dialog-centered">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">${title}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                ${message}
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">${cancelText}</button>
                                <button type="button" class="btn btn-primary" id="${modalId}_confirm">${confirmText}</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            document.body.insertAdjacentHTML('beforeend', modalHTML);

            const modal = new bootstrap.Modal(document.getElementById(modalId));
            modal.show();

            // Event listeners
            document.getElementById(`${modalId}_confirm`).addEventListener('click', () => {
                modal.hide();
                document.getElementById(modalId).remove();
                resolve(true);
            });

            document.getElementById(modalId).addEventListener('hidden.bs.modal', () => {
                document.getElementById(modalId).remove();
                resolve(false);
            });
        });
    },

    /**
     * Muestra un diálogo de alerta
     */
    showAlert: (title, message, type = 'info') => {
        return new Promise((resolve) => {
            const modalId = 'alert_' + Utils.generateId();
            const iconClass = type === 'success' ? 'text-success' :
                            type === 'error' ? 'text-danger' :
                            type === 'warning' ? 'text-warning' : 'text-info';
            const icon = type === 'success' ? 'bi-check-circle' :
                        type === 'error' ? 'bi-exclamation-triangle' :
                        type === 'warning' ? 'bi-exclamation-circle' : 'bi-info-circle';

            const modalHTML = `
                <div class="modal fade" id="${modalId}" tabindex="-1">
                    <div class="modal-dialog modal-dialog-centered">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">
                                    <i class="bi ${icon} ${iconClass} me-2"></i>${title}
                                </h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                ${message}
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Entendido</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            document.body.insertAdjacentHTML('beforeend', modalHTML);

            const modal = new bootstrap.Modal(document.getElementById(modalId));
            modal.show();

            document.getElementById(modalId).addEventListener('hidden.bs.modal', () => {
                document.getElementById(modalId).remove();
                resolve();
            });
        });
    }
};

// Gestor de estado de conexión
const ConnectionManager = {
    /**
     * Verifica el estado de conexión
     */
    checkConnection: async () => {
        try {
            const response = await fetch(`${CitrinoConfig.apiURL}/health`, {
                method: 'GET',
                timeout: 5000
            });

            AppState.isOnline = response.ok;
            return AppState.isOnline;
        } catch (error) {
            AppState.isOnline = false;
            return false;
        }
    },

    /**
     * Inicia monitoreo de conexión
     */
    startMonitoring: () => {
        // Event listeners del navegador
        window.addEventListener('online', () => {
            AppState.isOnline = true;
            NotificationSystem.showToast('Conexión restaurada', 'success');
        });

        window.addEventListener('offline', () => {
            AppState.isOnline = false;
            NotificationSystem.showToast('Sin conexión a internet', 'warning', 5000);
        });

        // Verificación periódica
        setInterval(ConnectionManager.checkConnection, 30000); // Cada 30 segundos
    }
};

// Gestor de almacenamiento local
const StorageManager = {
    /**
     * Guarda datos en localStorage
     */
    save: (key, data) => {
        try {
            localStorage.setItem(key, JSON.stringify(data));
            return true;
        } catch (error) {
            console.error('Error saving to localStorage:', error);
            return false;
        }
    },

    /**
     * Carga datos desde localStorage
     */
    load: (key, defaultValue = null) => {
        try {
            const data = localStorage.getItem(key);
            return data ? JSON.parse(data) : defaultValue;
        } catch (error) {
            console.error('Error loading from localStorage:', error);
            return defaultValue;
        }
    },

    /**
     * Elimina datos de localStorage
     */
    remove: (key) => {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Error removing from localStorage:', error);
            return false;
        }
    },

    /**
     * Limpia todo el localStorage
     */
    clear: () => {
        try {
            localStorage.clear();
            return true;
        } catch (error) {
            console.error('Error clearing localStorage:', error);
            return false;
        }
    }
};

// Gestor de análisis y métricas
const AnalyticsManager = {
    /**
     * Registra un evento
     */
    trackEvent: (eventName, properties = {}) => {
        const event = {
            name: eventName,
            properties: {
                ...properties,
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent,
                url: window.location.href
            }
        };

        // Guardar en localStorage para análisis offline
        const events = StorageManager.load('analytics_events', []);
        events.push(event);

        // Mantener solo los últimos 100 eventos
        if (events.length > 100) {
            events.splice(0, events.length - 100);
        }

        StorageManager.save('analytics_events', events);

        // Enviar a servidor si está online
        if (AppState.isOnline) {
            AnalyticsManager.sendEvents();
        }
    },

    /**
     * Envía eventos al servidor
     */
    sendEvents: async () => {
        const events = StorageManager.load('analytics_events', []);
        if (events.length === 0) return;

        try {
            // Aquí iría la lógica para enviar eventos al servidor
            // Por ahora, solo limpiamos el localStorage
            StorageManager.save('analytics_events', []);
        } catch (error) {
            console.error('Error sending analytics events:', error);
        }
    },

    /**
     * Registra página vista
     */
    trackPageView: (pageName = null) => {
        const page = pageName || window.location.pathname;
        AnalyticsManager.trackEvent('page_view', { page });
    }
};

// Gestor de tema
const ThemeManager = {
    /**
     * Cambia el tema
     */
    setTheme: (theme) => {
        if (theme === 'dark') {
            document.body.classList.add('dark-theme');
        } else {
            document.body.classList.remove('dark-theme');
        }

        AppState.theme = theme;
        StorageManager.save('theme', theme);
    },

    /**
     * Inicializa el tema
     */
    init: () => {
        const savedTheme = StorageManager.load('theme', 'light');
        ThemeManager.setTheme(savedTheme);

        // Detectar preferencia del sistema
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            if (!StorageManager.load('theme')) {
                ThemeManager.setTheme('dark');
            }
        }

        // Listener para cambios en preferencia del sistema
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!StorageManager.load('theme')) {
                ThemeManager.setTheme(e.matches ? 'dark' : 'light');
            }
        });
    }
};

// Gestor de accesibilidad
const AccessibilityManager = {
    /**
     * Inicializa características de accesibilidad
     */
    init: () => {
        // Skip links para navegación por teclado
        const skipLinksHTML = `
            <a href="#main-content" class="skip-link">Saltar al contenido principal</a>
            <a href="#navigation" class="skip-link">Saltar a navegación</a>
        `;
        document.body.insertAdjacentHTML('afterbegin', skipLinksHTML);

        // Focus management
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                document.body.classList.add('keyboard-navigation');
            }
        });

        document.addEventListener('mousedown', () => {
            document.body.classList.remove('keyboard-navigation');
        });

        // ARIA labels dinámicos
        AccessibilityManager.setupARIALiveRegions();
    },

    /**
     * Configura regiones ARIA live
     */
    setupARIALiveRegions: () => {
        const liveRegion = document.createElement('div');
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        liveRegion.setAttribute('class', 'sr-only');
        liveRegion.id = 'aria-live-region';
        document.body.appendChild(liveRegion);

        const assertiveRegion = document.createElement('div');
        assertiveRegion.setAttribute('aria-live', 'assertive');
        assertiveRegion.setAttribute('aria-atomic', 'true');
        assertiveRegion.setAttribute('class', 'sr-only');
        assertiveRegion.id = 'aria-assertive-region';
        document.body.appendChild(assertiveRegion);
    },

    /**
     * Anuncia cambios a lectores de pantalla
     */
    announce: (message, priority = 'polite') => {
        const regionId = priority === 'assertive' ? 'aria-assertive-region' : 'aria-live-region';
        const region = document.getElementById(regionId);
        if (region) {
            region.textContent = message;
            setTimeout(() => {
                region.textContent = '';
            }, 1000);
        }
    }
};

// Gestor de rendimiento
const PerformanceManager = {
    /**
     * Mide el tiempo de carga
     */
    measurePageLoad: () => {
        window.addEventListener('load', () => {
            const perfData = window.performance.timing;
            const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;

            AnalyticsManager.trackEvent('page_load_time', {
                load_time: pageLoadTime,
                url: window.location.href
            });

            console.log(`Page load time: ${pageLoadTime}ms`);
        });
    },

    /**
     * Lazy loading para imágenes
     */
    setupLazyLoading: () => {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                });
            });

            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        }
    }
};

// Gestor de errores global
const ErrorManager = {
    /**
     * Maneja errores globales
     */
    setup: () => {
        window.addEventListener('error', (event) => {
            ErrorManager.handleError(event.error, event.filename, event.lineno);
        });

        window.addEventListener('unhandledrejection', (event) => {
            ErrorManager.handleError(event.reason, 'Promise', 0);
        });
    },

    /**
     * Procesa un error
     */
    handleError: (error, filename = '', lineno = 0) => {
        console.error('Global error:', error);

        AnalyticsManager.trackEvent('error', {
            message: error.message || error,
            filename: filename,
            line: lineno,
            stack: error.stack,
            url: window.location.href,
            timestamp: new Date().toISOString()
        });

        // Mostrar mensaje amigable al usuario
        if (AppState.isOnline) {
            NotificationSystem.showToast(
                'Ha ocurrido un error. Estamos trabajando para solucionarlo.',
                'error',
                5000
            );
        }
    }
};

// Inicialización de la aplicación
const App = {
    /**
     * Inicializa la aplicación
     */
    init: async () => {
        try {
            console.log(`🏠 ${CitrinoConfig.appName} v${CitrinoConfig.appVersion}`);
            console.log('Initializing application...');

            // Inicializar gestores en orden
            PerformanceManager.measurePageLoad();
            ThemeManager.init();
            AccessibilityManager.init();
            ConnectionManager.startMonitoring();
            ErrorManager.setup();

            // Verificar conexión inicial
            await ConnectionManager.checkConnection();

            // Trackear página vista
            AnalyticsManager.trackPageView();

            // Setup lazy loading
            PerformanceManager.setupLazyLoading();

            // Aplicar configuraciones guardadas
            App.applySavedSettings();

            // Inicializar componentes específicos de la página
            App.initializePageComponents();

            console.log('✅ Application initialized successfully');

            // Event listener para beforeunload
            window.addEventListener('beforeunload', App.cleanup);

        } catch (error) {
            console.error('❌ Error initializing application:', error);
            NotificationSystem.showToast(
                'Error al inicializar la aplicación. Por favor, recarga la página.',
                'error',
                5000
            );
        }
    },

    /**
     * Aplica configuraciones guardadas
     */
    applySavedSettings: () => {
        // Restaurar tema
        const savedTheme = StorageManager.load('theme', 'light');
        ThemeManager.setTheme(savedTheme);

        // Restaurar otras configuraciones
        const savedSettings = StorageManager.load('user_settings', {});
        Object.assign(AppState, savedSettings);
    },

    /**
     * Inicializa componentes específicos de la página
     */
    initializePageComponents: () => {
        const currentPath = window.location.pathname;

        // Inicializar componentes según la página
        if (currentPath.includes('index.html') || currentPath === '/') {
            // Componentes de página principal
            App.initializeHomePage();
        } else if (currentPath.includes('citrino-reco.html')) {
            // Componentes de Citrino Reco
            App.initializeRecoPage();
        } else if (currentPath.includes('chat.html')) {
            // Componentes de página de chat
            App.initializeChatPage();
        }

        // Inicializar tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });

        // Inicializar popovers
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    },

    /**
     * Inicializa componentes de página principal
     */
    initializeHomePage: () => {
        // Animaciones al hacer scroll
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in-up');
                }
            });
        }, observerOptions);

        document.querySelectorAll('.feature-card, .action-card, .step-card').forEach(el => {
            observer.observe(el);
        });
    },

    /**
     * Inicializa componentes de Citrino Reco
     */
    initializeRecoPage: () => {
        // Auto-save del formulario
        const formInputs = document.querySelectorAll('#profileForm input, #profileForm select, #profileForm textarea');
        formInputs.forEach(input => {
            input.addEventListener('input', Utils.debounce(() => {
                const formData = new FormData(document.getElementById('profileForm'));
                const formDataObj = Object.fromEntries(formData);
                StorageManager.save('profile_draft', formDataObj);
            }, 1000));
        });
    },

    /**
     * Inicializa componentes de página de chat
     */
    initializeChatPage: () => {
        // Manejar resize del chat input
        const chatInput = document.getElementById('chatInput');
        if (chatInput) {
            chatInput.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 120) + 'px';
            });
        }
    },
    /**
     * Limpieza antes de salir de la página
     */
    cleanup: () => {
        // Enviar eventos de analytics pendientes
        AnalyticsManager.sendEvents();

        // Guardar estado actual
        StorageManager.save('app_state', AppState);

        console.log('🧹 Application cleanup completed');
    },

    /**
     * Recarga la aplicación
     */
    reload: () => {
        window.location.reload();
    }
};

// Funciones globales para fácil acceso
window.showToast = NotificationSystem.showToast;
window.showConfirm = NotificationSystem.showConfirm;
window.showAlert = NotificationSystem.showAlert;
window.Utils = Utils;
window.App = App;

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', App.init);
} else {
    App.init();
}

// Exportar para módulos si está disponible
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        CitrinoConfig,
        AppState,
        Utils,
        NotificationSystem,
        ConnectionManager,
        StorageManager,
        AnalyticsManager,
        ThemeManager,
        AccessibilityManager,
        PerformanceManager,
        ErrorManager,
        App
    };
}