# Citrino Frontend Test Suite

Suite de testing automatizado para las interfaces HTML del sistema Citrino.

## 📋 Tabla de Contenidos

- [Overview](#overview)
- [Estructura](#estructura)
- [Setup](#setup)
- [Ejecución](#ejecución)
- [Suites de Tests](#suites-de-tests)
- [Mock Data](#mock-data)
- [Reportes](#reportes)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

Esta suite de tests está diseñada para validar la funcionalidad, usabilidad y performance de las interfaces HTML del sistema Citrino:

- **Citrino Reco**: Formulario de perfiles y sistema de recomendaciones
- **Citrino Chat**: Interface conversacional con LLM
- **Integración**: Cross-browser testing, accesibilidad y performance

## 📁 Estructura

```
tests/frontend/
├── test_runner.html          # Interfaz principal para ejecutar tests
├── test_utils.js            # Utilidades y framework de testing
├── config.json              # Configuración de tests
├── README.md                # Este archivo
├── test_reco.html           # Tests específicos para Citrino Reco
├── test_chat.html           # Tests específicos para Citrino Chat
├── test_integration.html    # Tests de integración
└── reports/                 # Directorio para reportes generados
    ├── screenshots/
    ├── json/
    └── html/
```

## 🚀 Setup

### Prerrequisitos

- Navegador moderno (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)
- Servidor local para los archivos HTML (ver sección Ejecución)

### Instalación

1. Clonar el repositorio (si no lo tienes):
   ```bash
   git clone https://github.com/vincentiwadsworth/citrino.git
   cd citrino
   ```

2. Asegurarse que los archivos HTML estén disponibles:
   - `index.html`
   - `citrino-reco.html`
   - `chat.html`
   - `assets/js/api.js`
   - `assets/js/main.js`

3. Iniciar un servidor local:
   ```bash
   # Opción 1: Python
   python -m http.server 8080

   # Opción 2: Node.js (si tienes live-server)
   npx live-server --port=8080

   # Opción 3: PHP
   php -S localhost:8080
   ```

## 🏃‍♂️ Ejecución

### Método 1: Interface Web

1. Navegar a `http://localhost:8080/tests/frontend/test_runner.html`
2. Seleccionar las suites de tests deseadas
3. Hacer clic en "Ejecutar Seleccionados"
4. Revisar resultados en tiempo real

### Método 2: Automatizado

```javascript
// Para ejecutar todos los tests programáticamente
await runAllTests();

// Para ejecutar suites específicas
await runSelectedTests(['reco', 'chat']);
```

### Atajos de Teclado

- `Ctrl/Cmd + Enter`: Ejecutar todos los tests
- `Ctrl/Cmd + L`: Limpiar resultados
- `Ctrl/Cmd + E`: Exportar resultados

## 🧩 Suites de Tests

### 1. Utils Tests
Valida las utilidades base del framework de testing.

```javascript
describe('Utils Tests', () => {
    it('should create TestUtils instance', () => {
        // Test de inicialización
    });

    it('should perform basic assertions', () => {
        // Test de assertions
    });
});
```

### 2. Citrino Reco Tests
Tests para el formulario de perfiles y sistema de recomendaciones.

- **Validación de formulario**: Campos requeridos, presupuesto, zonas
- **Persistencia**: localStorage de perfiles
- **API Integration**: Mock de endpoints
- **UI/UX**: Responsive design, animaciones
- **Casos límite**: Datos inválidos, caracteres especiales

### 3. Citrino Chat Tests
Tests para la interface conversacional.

- **Interface**: Input sticky, scroll automático
- **Chat LLM**: Simulación de respuestas, manejo de errores
- **Visualización**: Renderizado de recomendaciones
- **Controles**: Botones exportar/limpiar
- **Mobile UX**: Responsive, touch interactions

### 4. Integration Tests
Tests de integración y calidad.

- **Cross-browser**: Chrome, Firefox, Safari compatibility
- **Performance**: Tiempos de carga, Core Web Vitals
- **Accesibilidad**: WCAG AA compliance
- **Errores**: Manejo de desconexión, fallbacks
- **Flujo completo**: Reco → Chat → Exportar

## 🎭 Mock Data

Los tests utilizan datos mock para simular respuestas de API y datos de prueba:

### API Mock
```javascript
// Mock de respuesta de API
mockAPI('/api/health', {
    status: 'ok',
    properties_count: 1583
});
```

### Perfiles Mock
```javascript
// Perfil de prueba
{
    nombreCliente: "Test User",
    presupuesto_min: 100000,
    presupuesto_max: 300000,
    zona_preferida: "Equipetrol",
    tipo_propiedad: "departamento"
}
```

## 📊 Reportes

### Formatos Disponibles

1. **HTML Report**: Reporte visual con estadísticas y detalles
2. **JSON Export**: Datos estructurados para análisis
3. **Console Logs**: Salida en tiempo real durante ejecución

### Métricas Incluidas

- **Coverage**: Número de tests ejecutados vs. planeados
- **Performance**: Tiempos de ejecución y carga
- **Browser Info**: Navegador, versión, capabilities
- **Accessibility**: Cumplimiento WCAG
- **Error Details**: Stack traces y mensajes de error

### Exportación

Los reportes se pueden exportar haciendo clic en "Exportar Reporte" o programáticamente:

```javascript
const results = testRunner.exportResults();
```

## 🔧 Configuración

La configuración se encuentra en `config.json`:

```json
{
  "suites": {
    "reco": {
      "enabled": true,
      "timeout": 15000,
      "mockAPI": true
    }
  },
  "performance": {
    "budgets": {
      "scriptSize": 250000,
      "cssSize": 50000
    }
  },
  "accessibility": {
    "wcagLevel": "AA"
  }
}
```

## 🐛 Troubleshooting

### Problemas Comunes

#### 1. Tests no cargan
**Síntoma**: La página queda en blanco o muestra errores
**Causa**: Archivos no encontrados, problema CORS
**Solución**:
```bash
# Asegurarse de usar un servidor HTTP local
python -m http.server 8080
# No abrir el archivo directamente (file://)
```

#### 2. Tests fallan consistentemente
**Síntoma**: Los mismos tests siempre fallan
**Causa**: Cambios en el DOM o API no actualizados
**Solución**:
- Revisar selectores CSS en los tests
- Actualizar datos mock
- Verificar cambios en la estructura HTML

#### 3. Performance muy lenta
**Síntoma**: Tests tardan mucho en ejecutarse
**Causa**: Demora en load de páginas o timeouts
**Solución**:
- Ajustar timeouts en `config.json`
- Optimizar waits y sleeps
- Revisar mock responses

#### 4. Tests de accesibilidad fallan
**Síntoma**: Errores de WCAG o contrastes
**Causa**: Problemas reales de accesibilidad
**Solución**:
- Usar herramientas axe DevTools
- Corregir problemas identificados
- Actualizar thresholds si aplica

### Debug Mode

Para habilitar debug mode:

```javascript
// En test_runner.html
testRunner.verbose = true;

// O en consola
localStorage.setItem('debug', 'true');
```

### Logs Detallados

Para ver logs detallados durante ejecución:

```javascript
// Habilitar console logging
testRunner.enableConsoleLogging = true;
```

## 📝 Desarrollo de Nuevos Tests

### Añadir Nueva Suite

1. Crear archivo `test_mi_suite.html`
2. Implementar tests usando el framework:

```javascript
describe('Mi Suite', () => {
    it('should do something', async () => {
        // Preparación
        await testRunner.click('#mi-boton');

        // Assertions
        testRunner.assertElementExists('#resultado');
        testRunner.assertEqual(
            document.querySelector('#resultado').textContent,
            'Expected result'
        );
    });
});
```

3. Agregar configuración en `config.json`
4. Incluir en `test_runner.html`

### Best Practices

1. **Selectores**: Usar IDs o clases específicas, no selectores frágiles
2. **Waits**: Usar `waitForElement` para contenido dinámico
3. **Cleanup**: Limpiar estado entre tests
4. **Assertions**: Ser específicos en mensajes de error
5. **Timeouts**: Configurar timeouts apropiados

## 🚀 Roadmap

### v1.1 (Planeado)
- [ ] Visual regression testing
- [ ] CI/CD integration
- [ ] Cross-device testing
- [ ] Network throttling simulation

### v1.2 (Planeado)
- [ ] E2E testing con Cypress
- [ ] Component testing aislado
- [ ] Performance profiling
- [ ] Accessibility auditing avanzado

## 📚 Documentación Adicional

### Guías Rápidas
- **[QUICK_START.md](QUICK_START.md)** - Guía de inicio en 5 minutos
- **[Reports Guide](reports/README.md)** - Documentación de reportes y métricas

### Archivos de Referencia
- **[test_utils.js](test_utils.js)** - API del framework de testing
- **[config.json](config.json)** - Configuración completa de tests
- **[test_runner.html](test_runner.html)** - Interface principal de testing

## 📄 Licencia

Esta suite de tests sigue la misma licencia MIT que el proyecto Citrino principal.

## 📞 Soporte

Para preguntas o problemas:

1. **Revisar QUICK_START.md** para solución rápida
2. Revisar este README principal
3. Buscar issues similares en el repositorio
4. Crear nuevo issue con:
   - Navegador y versión
   - Pasos para reproducir
   - Screenshots si aplica
   - Consola errors
   - URL del test específico

### 🆘 Comandos de Debug Rápido
```javascript
// En consola del navegador
localStorage.clear();           // Limpiar cache
location.reload();              // Recargar página
localStorage.setItem('debug', 'true'); // Activar debug mode
```

---

**Desarrollado para Citrino - Sistema de Recomendación Inmobiliaria**
**Versión 1.0.0** | **Actualizado: 9 de Octubre 2025**