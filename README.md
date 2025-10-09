# Citrino Frontend

Interfaz web profesional para el sistema de recomendación inmobiliaria Citrino.

## 🏠 Descripción

Este frontend proporciona una interfaz moderna y accesible para que el personal de Citrino pueda:

- **Crear perfiles de clientes** con formulario detallado
- **Chatear con asistente IA** para consultas en lenguaje natural
- **Ver resultados personalizados** con filtros avanzados
- **Exportar recomendaciones** en múltiples formatos

## ✨ Características

### 🎨 Diseño y UX
- **Responsive Design**: Funciona perfectamente en móviles, tablets y desktop
- **Bootstrap 5**: Framework CSS moderno y accesible
- **Animaciones suaves**: Experiencia de usuario fluida
- **Accesibilidad**: WCAG 2.1 AA compliant

### 🔧 Funcionalidades
- **Formulario de Perfil**: Validación en tiempo real, auto-guardado
- **Chat con IA**: Reconocimiento de voz, procesamiento natural
- **Sistema de Resultados**: Filtros, ordenamiento, paginación
- **Gestión de Datos**: localStorage, exportación, favoritos

### 🚀 Performance
- **Carga Rápida**: Sitio estático optimizado
- **Lazy Loading**: Imágenes y componentes bajo demanda
- **Caching**: Estrategias inteligentes de caché
- **SEO Optimizado**: Meta tags, structured data

## 📁 Estructura de Archivos

```
frontend/
├── index.html              # Página principal
├── perfil.html             # Formulario de perfil
├── chat.html               # Asistente virtual
├── resultados.html         # Visualización de resultados
├── README.md               # Documentación
├── assets/
│   ├── css/
│   │   └── custom.css      # Estilos personalizados
│   ├── js/
│   │   ├── main.js         # Lógica principal
│   │   └── api.js          # Conexión al backend
│   └── img/                # Imágenes y recursos
└── .github/
    └── workflows/
        └── deploy.yml       # GitHub Actions
```

## 🛠️ Tecnologías

- **HTML5**: Semántico y accesible
- **CSS3**: Flexbox, Grid, Animaciones
- **JavaScript ES6+**: Módulos, async/await
- **Bootstrap 5**: Framework CSS
- **Bootstrap Icons**: Iconos vectoriales
- **Web APIs**: Speech Recognition, LocalStorage, Geolocation

## 🚀 Despliegue

### GitHub Pages (Recomendado)

1. **Hacer fork** del repositorio
2. **Activar GitHub Pages**:
   - Settings → Pages
   - Source: Deploy from a branch
   - Branch: gh-pages
3. **Automático**: Cada push se despliega automáticamente

### Manual

1. **Clonar repositorio**:
```bash
git clone https://github.com/tu-usuario/citrino-frontend.git
cd citrino-frontend
```

2. **Iniciar servidor local**:
```bash
# Python 3
python -m http.server 8000

# Node.js (con live-server)
npx live-server

# PHP
php -S localhost:8000
```

3. **Acceder**: `http://localhost:8000`

## ⚙️ Configuración

### Backend API

Edita `assets/js/api.js` para configurar la URL del backend:

```javascript
const baseURL = 'https://tu-backend.com/api'; // Tu API backend
```

### Opciones Avanzadas

En `assets/js/main.js`:

```javascript
const CitrinoConfig = {
    apiURL: 'http://localhost:5000/api',  // URL del backend
    appVersion: '1.0.0',                   // Versión de la app
    maxRetries: 3,                         // Reintentos de conexión
    timeoutDuration: 30000                 // Timeout (ms)
};
```

## 🌐 URLs y Rutas

- **Inicio**: `/` → `index.html`
- **Perfil**: `/perfil.html`
- **Chat**: `/chat.html`
- **Resultados**: `/resultados.html`

Las URLs limpias están configuradas para GitHub Pages.

## 📱 Compatibilidad

### Navegadores Soportados
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

### Dispositivos
- ✅ iOS 14+
- ✅ Android 8+
- ✅ Desktop (Windows, macOS, Linux)

## 🔒 Seguridad

- **XSS Protection**: Sanitización de HTML
- **HTTPS Only**: Solo se despliega con HTTPS
- **CSP Ready**: Headers de seguridad configurados
- **No Cookies**: Sin almacenamiento de datos sensibles

## 📊 Analytics y Monitoreo

- **Event Tracking**: Interacciones del usuario
- **Performance Metrics**: Tiempos de carga
- **Error Tracking**: Reporte automático de errores
- **Offline Support**: Funcionalidad básica sin conexión

## 🔧 Desarrollo

### Instalación Local

1. **Clonar el repositorio**:
```bash
git clone https://github.com/tu-usuario/citrino-frontend.git
cd citrino-frontend
```

2. **Instalar dependencias** (si usas npm para herramientas):
```bash
npm install
```

3. **Iniciar desarrollo**:
```bash
# Servidor simple
python -m http.server 8000

# O con herramientas de desarrollo
npm run dev
```

### Estructura de Componentes

#### Página Principal (`index.html`)
- Hero section con animaciones
- Tarjetas de características
- Llamadas a la acción
- Estadísticas del sistema

#### Formulario de Perfil (`perfil.html`)
- Validación en tiempo real
- Secciones organizadas
- Auto-guardado local
- Perfiles guardados

#### Chat Virtual (`chat.html`)
- Interface tipo WhatsApp
- Reconocimiento de voz
- Historial de conversación
- Procesamiento LLM

#### Resultados (`resultados.html`)
- Grid/List/Map views
- Filtros avanzados
- Paginación
- Exportación de datos

## 🎨 Personalización

### Colores y Branding

Edita `assets/css/custom.css`:

```css
:root {
    --citrino-primary: #0d6efd;      /* Color principal */
    --citrino-secondary: #6c757d;    /* Color secundario */
    --citrino-success: #198754;      /* Color éxito */
    --citrino-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
```

### Textos y Contenido

Los textos están en español y pueden modificarse directamente en los archivos HTML o mediante JavaScript para internacionalización.

## 🚀 CI/CD

### GitHub Actions

El flujo de despliegue automático:

1. **Push** a rama `main`
2. **Build** y **test** automáticos
3. **Deploy** a GitHub Pages
4. **Notificación** de despliegue exitoso

### Verificación de Despliegue

```bash
# Verificar estatus
curl -I https://tu-usuario.github.io/citrino-frontend/

# Test de API health
curl https://tu-backend.com/api/health
```

## 🐛 Troubleshooting

### Problemas Comunes

#### API No Responde
- Verificar URL en `assets/js/api.js`
- Revisar CORS en el backend
- Comprobar conexión a internet

#### Errores de Carga
- Limpiar localStorage
- Verificar consola del navegador
- Revisar network tab

#### Problemas con GitHub Pages
- Verificar nombre del repositorio
- Confirmar rama `gh-pages`
- Revisar settings de Pages

### Debug Mode

Activa debug en consola:

```javascript
localStorage.setItem('debug', 'true');
```

## 📄 Licencia

MIT License - ver archivo LICENSE para detalles.

## 🤝 Contribuciones

1. **Fork** el proyecto
2. **Crear branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit** cambios (`git commit -m 'Add some AmazingFeature'`)
4. **Push** a la rama (`git push origin feature/AmazingFeature`)
5. **Abrir Pull Request**

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/tu-usuario/citrino-frontend/issues)
- **Discussions**: [GitHub Discussions](https://github.com/tu-usuario/citrino-frontend/discussions)
- **Email**: soporte@citrino.com

---

**Desarrollado con ❤️ para Citrino Sistema de Recomendación Inmobiliaria**