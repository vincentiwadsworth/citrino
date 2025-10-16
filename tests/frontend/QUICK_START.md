#  Guía Rápida - Citrino Frontend Testing

Inicio rápido para ejecutar tests del frontend de Citrino.

##  Ejecución Inmediata (5 minutos)

### 1. Iniciar Servidor Local
```bash
# En la raíz del proyecto
python -m http.server 8080
```

### 2. Abrir Test Runner
```
http://localhost:8080/tests/frontend/test_runner.html
```

### 3. Ejecutar Todos los Tests
- Click en **"Ejecutar Todos"**
- Espera resultados (~30 segundos)
- Revisa métricas y resultados

##  Tests Específicos

### Citrino Reco Tests
```
http://localhost:8080/tests/frontend/test_reco.html
```
**Qué prueba:**
-  Validación de formularios
-  Generación de recomendaciones
-  Persistencia en localStorage
-  UI/UX responsive

### Citrino Chat Tests
```
http://localhost:8080/tests/frontend/test_chat.html
```
**Qué prueba:**
-  Interface de chat conversacional
-  Mock LLM API responses
-  Manejo de errores y fallbacks
-  Visualización de recomendaciones

### Integration & Quality Tests
```
http://localhost:8080/tests/frontend/test_integration.html
```
**Qué prueba:**
-  Performance (Core Web Vitals)
-  Accesibilidad WCAG AA
-  Cross-browser compatibility
-  Responsive design
-  Security best practices

##  Configuración Rápida

### Mock API (Recomendado para desarrollo)
```javascript
// Activado por defecto en test_runner.html
mockAPI: true
```

### Tests con datos reales
```javascript
// Desactivar mocks para usar API real
document.getElementById('mockAPI').checked = false;
```

### Logging detallado
```javascript
// Activar logs en consola
document.getElementById('verboseLogging').checked = true;
```

##  Métricas Clave

### Buenos Resultados
- **Success Rate**: >95%
- **Performance**: <3s load time
- **Accessibility**: WCAG AA compliance
- **Lighthouse Score**: >85

### Requiere Atención
- **Success Rate**: 80-95%
- **Performance**: 3-5s load time
- **Accessibility**: Algunos checks fallidos
- **Lighthouse Score**: 70-85

### Crítico
- **Success Rate**: <80%
- **Performance**: >5s load time
- **Accessibility**: Múltiples fallos WCAG
- **Lighthouse Score**: <70

##  Atajos de Teclado

### Test Runner Principal
- `Ctrl + Enter`: Ejecutar todos los tests
- `Ctrl + L`: Limpiar resultados
- `Ctrl + E`: Exportar reporte

### Tests Individuales
- `Ctrl + 1`: Tests de formulario (Reco)
- `Ctrl + 2`: Tests de recomendaciones (Reco)
- `Ctrl + 3`: Tests de chat básico
- `Ctrl + 4`: Tests de performance
- `Ctrl + 5`: Tests de accesibilidad

##  Problemas Comunes

### "Tests no cargan"
```bash
# Usar servidor local, NO abrir archivo directamente
python -m http.server 8080
# Luego ir a http://localhost:8080/tests/frontend/
```

### "API timeouts"
```javascript
// Activar mocks para testing sin dependencias
document.getElementById('mockAPI').checked = true;
```

### "Tests lentos"
```javascript
// Reducir timeouts en config.json
"testTimeout": 5000
```

##  Reportes

### Generar Reporte
1. Ejecutar tests
2. Click en **"Exportar Reporte"**
3. Guardar como JSON

### Ver Reporte HTML
El dashboard se actualiza automáticamente con:
-  Métricas de performance
-  Resultados detallados
-  Checks de accesibilidad
-  Compatibilidad cross-browser

##  Integración CI/CD

### GitHub Actions (Ejemplo)
```yaml
name: Frontend Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Start Server
        run: |
          python -m http.server 8080 &
          sleep 5
      - name: Run Tests
        run: |
          # Usar Puppeteer/Playwright para tests headless
          npm run test:frontend:ci
```

##  Referencias Rápidas

### Archivos Clave
- `test_runner.html` - Interface principal
- `test_utils.js` - Framework de testing
- `config.json` - Configuración de tests
- `README.md` - Documentación completa

### Estructura de Tests
```javascript
describe('Suite Name', () => {
  it('should do something', () => {
    testRunner.assert(condition, 'Message');
    testRunner.assertEqual(actual, expected, 'Message');
    testRunner.assertElementExists('#selector');
  });
});
```

##  Ayuda Rápida

### Comandos Útiles
```bash
# Limpiar cache de tests
localStorage.clear();
sessionStorage.clear();

# Resetear resultados
location.reload();

# Debug mode
localStorage.setItem('debug', 'true');
```

### Contacto y Soporte
-  **Docs**: `tests/frontend/README.md`
-  **Issues**: GitHub repository
-  **Chat**: Equipo de desarrollo Citrino

---

**Tiempo estimado de setup**: 5 minutos
**Tiempo estimado de ejecución completa**: 30-60 segundos
**Requerimientos**: Navegador moderno, Python 3.x para servidor local

**Listo para empezar! **