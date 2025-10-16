# Cambios Pendientes para Completar Integración LLM en Citrino Reco

##  Completado

1. **Backend (api/server.py)**
   -  Función `generar_briefing_ejecutivo_llm()` agregada
   -  Endpoint `/api/recomendar-mejorado-llm` creado
   -  Enriquecimiento de justificaciones con Z.AI implementado
   -  Health endpoint actualizado con nuevo endpoint

2. **API Client (assets/js/api.js)**
   -  Método `getRecommendationsWithLLM()` agregado

3. **Frontend (citrino-reco.html)**
   -  Funciones `renderBriefing()` y `exportBriefing()` agregadas

##  Cambios Manuales Requeridos en citrino-reco.html

### 1. Añadir Variables Globales (después de línea 824)

```javascript
let latestRecommendations = [];
let currentBriefing = null;  // ← AÑADIR
let currentProfile = null;   // ← AÑADIR
```

### 2. Reemplazar Función `generateRecommendations()` (líneas 1198-1232)

**REEMPLAZAR TODO EL CONTENIDO DE LA FUNCIÓN con:**

```javascript
async function generateRecommendations(profileData) {
    const section = document.getElementById('recoResultsSection');
    const grid = document.getElementById('recommendationsGrid');
    const emptyState = document.getElementById('recommendationsEmpty');
    const briefingSection = document.getElementById('briefingSection');

    currentProfile = profileData;

    section.classList.add('active');
    grid.innerHTML = `
        <div class="col-12">
            <div class="recommendations-empty">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
                <h5 class="mt-3">Analizando oportunidades...</h5>
                <p class="text-muted">Evaluando coincidencias con datos georreferenciados y procesando con Z.AI...</p>
            </div>
        </div>
    `;
    emptyState.classList.add('d-none');
    if (briefingSection) briefingSection.style.display = 'none';

    try {
        // Intentar usar endpoint con LLM si hay información adicional
        const hasLLMInfo = profileData.informacion_llm && profileData.informacion_llm.trim().length > 0;
        
        const result = hasLLMInfo 
            ? await window.citrinoAPI.getRecommendationsWithLLM(profileData, { limite: 6, umbral_minimo: 0.3 })
            : await window.citrinoAPI.getEnhancedRecommendations(profileData, { limite: 6, umbral_minimo: 0.3 });

        if (result.success && result.recommendations.length > 0) {
            renderRecommendations(result.recommendations);
            
            // Mostrar briefing si está disponible
            if (result.briefing) {
                renderBriefing(result.briefing);
                currentBriefing = result.briefing;
            }
            
            const message = result.llmAvailable && hasLLMInfo
                ? 'Recomendaciones enriquecidas con Z.AI generadas exitosamente'
                : 'Recomendaciones generadas con datos en vivo';
            showToast(message, 'success');
        } else {
            renderRecommendations(demoRecommendations);
            showToast('Mostrando recomendaciones de demostración. Conecta la API para resultados reales.', 'warning');
        }
    } catch (error) {
        console.error('Error obteniendo recomendaciones:', error);
        // Fallback: intentar endpoint normal si LLM falla
        try {
            const fallbackResult = await window.citrinoAPI.getEnhancedRecommendations(profileData, { limite: 6, umbral_minimo: 0.3 });
            if (fallbackResult.success && fallbackResult.recommendations.length > 0) {
                renderRecommendations(fallbackResult.recommendations);
                showToast('Recomendaciones generadas (modo básico)', 'success');
                return;
            }
        } catch (fallbackError) {
            console.error('Error en fallback:', fallbackError);
        }
        
        renderRecommendations(demoRecommendations);
        showToast('No pudimos contactar la API. Se muestran datos de demostración.', 'warning');
    }
}
```

### 3. Reemplazar Función `buildRecommendationCard()` (líneas 1249-1288)

**REEMPLAZAR TODO EL CONTENIDO DE LA FUNCIÓN con:**

```javascript
function buildRecommendationCard(property) {
    const compatibilityClass = property.compatibilidad >= 90 ? 'high'
        : property.compatibilidad >= 70 ? 'medium' : 'low';

    const formattedPrice = property.precio ? Utils.formatCurrency(property.precio) : 'Precio reservado';

    // Añadir sección de análisis personalizado si existe
    let llmAnalysis = '';
    if (property.analisis_personalizado) {
        llmAnalysis = `
            <div class="llm-analysis">
                <div class="llm-badge">
                    <i class="bi bi-stars"></i>
                    <span>Análisis con Z.AI</span>
                </div>
                <p>${property.analisis_personalizado}</p>
            </div>
        `;
    }

    return `
        <div class="recommendation-card">
            <div class="recommendation-header d-flex justify-content-between align-items-start">
                <div>
                    <h5 class="mb-1">${property.nombre || 'Propiedad sin título'}</h5>
                    <span class="text-muted"><i class="bi bi-geo-alt me-1"></i>${property.zona || 'Zona no declarada'}</span>
                </div>
                <span class="compatibility-pill ${compatibilityClass}">
                    <i class="bi bi-stars"></i>${Math.round(property.compatibilidad || 0)}%
                </span>
            </div>
            <div class="recommendation-body">
                <div class="h4 fw-bold text-success mb-2">${formattedPrice}</div>
                <div class="recommendation-meta">
                    ${property.habitaciones ? `<span class="meta-chip"><i class="bi bi-door-open"></i>${property.habitaciones} dorm.</span>` : ''}
                    ${property.banos ? `<span class="meta-chip"><i class="bi bi-droplet"></i>${property.banos} baños</span>` : ''}
                    ${property.superficie_m2 ? `<span class="meta-chip"><i class="bi bi-rulers"></i>${property.superficie_m2} m²</span>` : ''}
                </div>
                ${property.caracteristicas?.length ? `
                    <div class="mb-3">
                        ${property.caracteristicas.slice(0, 4).map(feature => `<span class="meta-chip"><i class="bi bi-check-lg"></i>${feature.replace(/_/g, ' ')}</span>`).join('')}
                    </div>
                ` : ''}
                <div class="recommendation-justification">
                    <strong>Motivo</strong>
                    <p class="mb-0 mt-1">${property.justificacion || 'Sin justificación disponible para esta coincidencia.'}</p>
                </div>
                ${llmAnalysis}
            </div>
        </div>
    `;
}
```

### 4. Añadir HTML de Briefing Section (después de línea 748, antes del `</div>` que cierra el container)

```html
            <!-- Briefing Ejecutivo Section -->
            <div id="briefingSection" class="briefing-section" style="display: none;">
                <div class="briefing-header">
                    <h3><i class="bi bi-file-earmark-text"></i> Briefing Ejecutivo</h3>
                    <button class="btn btn-sm btn-outline-primary" onclick="exportBriefing()">
                        <i class="bi bi-download"></i> Exportar
                    </button>
                </div>
                <div id="briefingContent" class="briefing-content markdown-body">
                    <!-- Contenido del briefing en markdown -->
                </div>
            </div>
```

### 5. Añadir CSS para LLM (en el bloque `<style>` después de línea 221)

```css
.llm-analysis {
    background: linear-gradient(135deg, #667eea15, #764ba215);
    border-left: 3px solid #667eea;
    border-radius: 0 10px 10px 0;
    padding: 1rem;
    margin-top: 1rem;
}

.llm-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: #667eea;
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 600;
    margin-bottom: 0.75rem;
}

.llm-analysis p {
    margin: 0;
    font-size: 0.95rem;
    color: #475569;
    line-height: 1.6;
}

.briefing-section {
    margin-top: 2rem;
    padding: 2rem;
    background: white;
    border-radius: 15px;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.briefing-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 2px solid #e9ecef;
    padding-bottom: 1rem;
    margin-bottom: 1.5rem;
}

.briefing-content {
    font-size: 1rem;
    line-height: 1.8;
    color: #334155;
}

.briefing-content h1,
.briefing-content h2,
.briefing-content h3 {
    color: #667eea;
    margin-top: 1.5rem;
    margin-bottom: 0.75rem;
}

.briefing-content ul,
.briefing-content ol {
    margin-left: 1.5rem;
}
```

##  Instrucciones de Implementación

1. Abre `citrino-reco.html` en tu editor
2. Busca línea 824 y añade las dos variables globales
3. Busca la función `generateRecommendations()` (línea ~1198) y reemplázala completamente
4. Busca la función `buildRecommendationCard()` (línea ~1249) y reemplázala completamente
5. Busca dónde termina la sección de recomendaciones (línea ~748) y añade el HTML del briefing
6. En el bloque `<style>` (después de línea 221), añade los estilos CSS para .llm-analysis y .briefing-section
7. Guarda el archivo

##  Testing

Después de hacer estos cambios:

1. **Sin información LLM**: Llenar formulario sin campo "información adicional" → Debe usar endpoint normal
2. **Con información LLM**: Llenar formulario CON campo "información adicional" → Debe usar endpoint LLM y mostrar:
   - Badge "Análisis con Z.AI" en las propiedades
   - Sección de Briefing Ejecutivo debajo de las recomendaciones
   - Botón "Exportar" funcional
3. **Fallback**: Si Z.AI falla, debe caer al endpoint normal automáticamente

##  Deploy

Una vez probado localmente:

```bash
git add .
git commit -m "feat: integrar z.ai en Citrino Reco con enriquecimiento y briefing ejecutivo

- Opción A: Enriquecer justificaciones con análisis personalizado
- Opción C: Generar briefing ejecutivo con análisis de mercado
- Nuevo endpoint /api/recomendar-mejorado-llm
- Campo informacion_llm alimenta prompts de Z.AI
- Exportación de briefing en markdown
- Fallback automático si Z.AI no está disponible

Co-authored-by: factory-droid[bot] <138933559+factory-droid[bot]@users.noreply.github.com>"

git push origin master
```

El despliegue en Render se actualizará automáticamente.
