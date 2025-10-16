# Reportes de Testing - Citrino Frontend

Este directorio contiene los reportes generados por la suite de testing del frontend de Citrino.

##  Estructura de Reportes

```
reports/
 html/                   # Reportes HTML visuales
    test-report-2025-10-09-T14-30-00.html
    test-report-2025-10-09-T15-45-12.html
 json/                   # Datos estructurados de tests
    test-results-2025-10-09-T14-30-00.json
    test-results-2025-10-09-T15-45-12.json
 screenshots/            # Capturas de pantalla (automáticas)
    reco-form-validation.png
    chat-interaction.png
    mobile-responsive.png
 README.md               # Este archivo
```

##  Tipos de Reportes

### 1. Reportes HTML
- **Formato**: Visual e interactivo
- **Contenido**: Dashboard completo con métricas, resultados detallados y gráficos
- **Uso**: Presentación a stakeholders, análisis visual rápido
- **Ubicación**: `reports/html/`

### 2. Reportes JSON
- **Formato**: Datos estructurados
- **Contenido**: Resultados crudos, métricas, timestamps, errores
- **Uso**: Integración CI/CD, análisis programático, almacenamiento histórico
- **Ubicación**: `reports/json/`

### 3. Screenshots
- **Formato**: Imágenes PNG
- **Contenido**: Capturas automáticas de estados críticos
- **Uso**: Documentación visual, evidencia de bugs, regresión visual
- **Ubicación**: `reports/screenshots/`

##  Métricas Incluidas

### Performance Metrics
- **First Contentful Paint (FCP)**: Tiempo hasta primer contenido visible
- **Largest Contentful Paint (LCP)**: Tiempo hasta elemento más grande
- **Cumulative Layout Shift (CLS)**: Estabilidad visual
- **First Input Delay (FID)**: Responsividad inicial
- **Page Load Time**: Tiempo total de carga

### Quality Metrics
- **Lighthouse Score**: Puntuación general de calidad (0-100)
- **Accessibility Score**: Cumplimiento WCAG (0-100)
- **Best Practices Score**: Buenas prácticas web (0-100)
- **SEO Score**: Optimización SEO (0-100)

### Test Results
- **Total Tests**: Número total de tests ejecutados
- **Passed Tests**: Tests exitosos
- **Failed Tests**: Tests con errores
- **Coverage**: Porcentaje de funcionalidad cubierta
- **Execution Time**: Tiempo total de ejecución

##  Nomenclatura de Archivos

### Reportes HTML
```
test-report-YYYY-MM-DD-THH-MM-SS.html
```
Ejemplo: `test-report-2025-10-09T14-30-00.html`

### Reportes JSON
```
test-results-YYYY-MM-DD-THH-MM-SS.json
```
Ejemplo: `test-results-2025-10-09T14-30-00.json`

### Screenshots
```
<component>-<action>-<timestamp>.png
```
Ejemplos:
- `reco-form-validation-2025-10-09T14-30-00.png`
- `chat-interaction-2025-10-09T14-30-00.png`
- `mobile-responsive-2025-10-09T14-30-00.png`

##  Contenido de Reportes

### Estructura JSON
```json
{
  "timestamp": "2025-10-09T14:30:00.000Z",
  "summary": {
    "totalTests": 45,
    "passedTests": 43,
    "failedTests": 2,
    "executionTime": 12500,
    "successRate": 95.6
  },
  "suites": [
    {
      "name": "Citrino Reco - Form Validation",
      "total": 15,
      "passed": 15,
      "failed": 0,
      "duration": 3200,
      "tests": [...]
    }
  ],
  "performance": {
    "fcp": 1200,
    "lcp": 2100,
    "cls": 0.05,
    "fid": 45
  },
  "quality": {
    "lighthouse": {
      "performance": 85,
      "accessibility": 95,
      "bestPractices": 90,
      "seo": 92
    }
  },
  "environment": {
    "browser": "Chrome 118.0",
    "userAgent": "...",
    "screenResolution": "1920x1080",
    "viewport": "1200x800"
  }
}
```

### Estructura HTML
El reporte HTML incluye:
- **Dashboard Principal**: Métricas clave y scores
- **Resultados Detallados**: Por suite y test individual
- **Performance Charts**: Gráficos de Core Web Vitals
- **Accessibility Report**: Checks WCAG detallados
- **Browser Compatibility**: Matriz de compatibilidad
- **Timeline**: Ejecución de tests en el tiempo
- **Error Details**: Stack traces y soluciones

##  Generación Automática

### Manual
1. Abrir `test_runner.html`
2. Seleccionar tests deseados
3. Ejecutar tests
4. Click en "Exportar Reporte"
5. Guardar en directorio correspondiente

### Automatizada (Future)
```bash
# Ejecutar todos los tests y generar reporte
npm run test:frontend -- --report

# Solo generar reporte JSON
npm run test:frontend -- --format=json

# Generar reporte con screenshots
npm run test:frontend -- --screenshots
```

### CI/CD Integration
```yaml
# .github/workflows/frontend-tests.yml
- name: Run Frontend Tests
  run: |
    python -m http.server 8080 &
    sleep 5
    python -c "
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
options = Options()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)
driver.get('http://localhost:8080/tests/frontend/test_runner.html')
# Ejecutar tests y exportar resultados
driver.quit()
"
```

##  Historial y Tendencias

### Tracking de Métricas
Los reportes se guardan históricamente para:
- **Trend Analysis**: Evolución de performance y calidad
- **Regression Detection**: Identificar degradaciones
- **Improvement Tracking**: Medir impacto de optimizaciones

### Comparación entre Versiones
```bash
# Comparar reportes entre commits
python scripts/compare_reports.py \
  --before reports/json/test-results-2025-10-08.json \
  --after reports/json/test-results-2025-10-09.json
```

##  Debugging con Reportes

### Análisis de Errores
1. **Identificar Test Fallido**: Revisar reporte HTML
2. **Examinar Detalles**: Stack trace y contexto
3. **Revisar Screenshot**: Visualizar estado cuando ocurrió
4. **Ver Logs**: Consola output y timestamps

### Ejemplo de Debug
```javascript
// Error en test runner
{
  "name": "should validate budget constraints",
  "status": "failed",
  "error": "Expected 100000 < 200000, but got false",
  "duration": 150,
  "timestamp": "2025-10-09T14:30:15.123Z",
  "screenshot": "reports/screenshots/budget-validation-error.png"
}
```

##  Análisis y Reporting

### KPIs Principales
- **Test Success Rate**: % de tests exitosos (meta: >95%)
- **Performance Score**: Promedio Core Web Vitals (meta: >85)
- **Accessibility Score**: Cumplimiento WCAG (meta: >95)
- **Regression Rate**: % de tests que fallan tras cambios (meta: <5%)

### Reportes Personalizados
```javascript
// Generar reporte personalizado
function generateCustomReport(testResults, filters) {
  return {
    period: filters.period,
    kpis: calculateKPIs(testResults, filters),
    trends: analyzeTrends(testResults),
    recommendations: generateRecommendations(testResults)
  };
}
```

##  Mantenimiento

### Limpieza Automática
```bash
# Eliminar reportes antiguos (>30 días)
find reports/ -name "*.html" -mtime +30 -delete
find reports/ -name "*.json" -mtime +30 -delete
find reports/ -name "*.png" -mtime +30 -delete
```

### Compresión de Reportes
```bash
# Comprimir reportes mensuales
tar -czf reports/monthly/2025-10.tar.gz reports/2025-10/
```

##  Soporte

Para problemas con reportes:

1. **Verificar formato**: Asegurar que los archivos sean válidos
2. **Revisar permisos**: Confirmar acceso a directorios
3. **Validar JSON**: Usar validadores online para JSON
4. **Browser Issues**: Probar diferentes navegadores para HTML

### Contacto
- **Issues**: GitHub repository issues
- **Documentation**: Ver `tests/frontend/README.md`
- **Examples**: Revisar reportes de ejemplo en directorio

---

**Última actualización**: 9 de Octubre 2025
**Versión**: 1.0.0
**Citrino Frontend Testing Suite**