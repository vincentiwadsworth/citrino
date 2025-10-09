# Plan: Integración Z.AI en Citrino Reco

## 📊 Estado Actual del Proyecto

### ✅ Completado en Esta Sesión

1. **Despliegue Online**
   - Backend en Render: https://citrino.onrender.com ✅
   - Frontend en GitHub Pages: https://vincentiwadsworth.github.io/citrino/ (pendiente configurar)
   - Base de datos: 1,583 propiedades cargadas ✅
   - API funcionando correctamente ✅

2. **Integración Z.AI Base**
   - API Key configurada: `34431b5a2e38422baa5551d4d623519f.DEYL3LOWMUFvL0kh`
   - `src/llm_integration.py` con soporte completo para Z.AI (GLM-4.5-Air)
   - Endpoint `/api/chat/process` funcionando
   - **Citrino Chat**: Z.AI completamente integrado ✅
   - **Citrino Reco**: Campo preparado pero NO usa Z.AI aún ❌

3. **Infraestructura**
   - Python 3.11.9 configurado en Render
   - pandas 2.2.3 + numpy 2.2.1 (compatibles)
   - CORS configurado para producción
   - Logs optimizados con banners claros

---

## 🎯 Trabajo Pendiente: Z.AI en Citrino Reco

### Opción A: Enriquecer Justificaciones con Z.AI

**Objetivo**: Usar el campo "Información adicional para z.ai" para generar justificaciones personalizadas y contextualizadas para cada recomendación.

#### Cambios Necesarios

**1. Nuevo endpoint en `api/server.py`**

```python
@app.route('/api/recomendar-mejorado-llm', methods=['POST'])
def recomendar_con_llm():
    """
    Genera recomendaciones y enriquece justificaciones con Z.AI
    """
    try:
        data = request.get_json()
        
        # Generar recomendaciones normales
        perfil = formatear_perfil(data)
        recomendaciones = motor_mejorado.generar_recomendaciones(perfil)
        
        # Si hay información adicional, usar Z.AI para enriquecer
        info_adicional = data.get('informacion_llm', '')
        
        if info_adicional and os.getenv('ZAI_API_KEY'):
            from llm_integration import LLMIntegration, LLMConfig
            
            llm = LLMIntegration(LLMConfig(
                provider='zai',
                api_key=os.getenv('ZAI_API_KEY'),
                model='glm-4.5-air'
            ))
            
            # Enriquecer cada recomendación con análisis LLM
            for rec in recomendaciones:
                prompt = f"""
Contexto de la reunión con el prospecto:
{info_adicional}

Propiedad recomendada:
- Ubicación: {rec['zona']}
- Precio: ${rec['precio']:,} USD
- Características: {rec['habitaciones']} hab, {rec['banos']} baños, {rec['superficie_m2']} m²
- Justificación técnica: {rec['justificacion']}

Genera un análisis personalizado (2-3 oraciones) explicando:
1. Por qué esta propiedad es ideal para este prospecto específico
2. Qué aspectos mencionados en la reunión se alinean con la propiedad
3. Una sugerencia o pregunta para la próxima conversación
"""
                
                try:
                    # Generar análisis enriquecido
                    respuesta_llm = llm._call_zai(prompt)
                    rec['analisis_personalizado'] = respuesta_llm
                    rec['llm_usado'] = True
                except Exception as e:
                    print(f"Error enriqueciendo con LLM: {e}")
                    rec['llm_usado'] = False
        
        return jsonify({
            'success': True,
            'recomendaciones': recomendaciones,
            'llm_disponible': bool(os.getenv('ZAI_API_KEY'))
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
```

**2. Actualizar `assets/js/api.js`**

```javascript
/**
 * Genera recomendaciones enriquecidas con Z.AI
 */
async getRecommendationsWithLLM(profile, options = {}) {
    try {
        const requestData = {
            ...profile,
            limite: options.limite || 5,
            umbral_minimo: options.umbral_minimo || 0.3
        };

        const response = await this.request('/recomendar-mejorado-llm', {
            method: 'POST',
            body: JSON.stringify(requestData)
        });

        return {
            success: true,
            recommendations: response.recomendaciones || [],
            llmAvailable: response.llm_disponible
        };
    } catch (error) {
        return {
            success: false,
            error: error.message
        };
    }
}
```

**3. Actualizar `citrino-reco.html`**

Modificar la función `generateRecommendations()`:

```javascript
async function generateRecommendations(profileData) {
    // ... código existente ...
    
    try {
        // Usar endpoint con LLM si hay información adicional
        const result = await window.citrinoAPI.getRecommendationsWithLLM(
            profileData, 
            { limite: 6, umbral_minimo: 0.3 }
        );

        if (result.success && result.recommendations.length > 0) {
            renderRecommendationsWithLLM(result.recommendations);
            
            if (result.llmAvailable) {
                showToast('Recomendaciones enriquecidas con Z.AI', 'success');
            }
        }
    } catch (error) {
        // Fallback al endpoint normal
        console.warn('LLM endpoint falló, usando endpoint normal');
        // ... código de fallback existente ...
    }
}
```

**4. Nueva función para renderizar recomendaciones con LLM**

```javascript
function buildRecommendationCard(property) {
    // ... código existente ...
    
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
            <!-- ... contenido existente ... -->
            ${llmAnalysis}
        </div>
    `;
}
```

**5. CSS para el análisis LLM**

En `assets/css/custom.css` o `citrino-reco.html`:

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
```

---

### Opción C: Resumen Ejecutivo con LLM

**Objetivo**: Generar un briefing ejecutivo personalizado con análisis de mercado y preguntas sugeridas para la reunión.

#### Cambios Necesarios

**1. Función en `api/server.py`**

```python
def generar_briefing_ejecutivo_llm(recomendaciones, perfil, info_adicional):
    """
    Genera briefing ejecutivo enriquecido con Z.AI
    """
    if not os.getenv('ZAI_API_KEY') or not info_adicional:
        return generar_briefing_personalizado(perfil, recomendaciones)  # Fallback existente
    
    try:
        from llm_integration import LLMIntegration, LLMConfig
        
        llm = LLMIntegration(LLMConfig(
            provider='zai',
            api_key=os.getenv('ZAI_API_KEY'),
            model='glm-4.5-air'
        ))
        
        # Preparar contexto para el LLM
        resumen_recs = "\n".join([
            f"- {rec['nombre']}: ${rec['precio']:,} USD, {rec['zona']}, {rec['compatibilidad']}% match"
            for rec in recomendaciones[:5]
        ])
        
        prompt = f"""
Eres un asesor inmobiliario senior. Genera un briefing ejecutivo profesional.

CONTEXTO DE LA REUNIÓN:
{info_adicional}

PERFIL DEL PROSPECTO:
- Presupuesto: ${perfil['presupuesto']['min']:,} - ${perfil['presupuesto']['max']:,} USD
- Zona preferida: {perfil['preferencias']['ubicacion']}
- Tipo: {perfil['preferencias']['tipo_propiedad']}

RECOMENDACIONES TOP:
{resumen_recs}

Genera un briefing ejecutivo que incluya:

1. RESUMEN EJECUTIVO (2-3 oraciones sobre el perfil del prospecto)

2. ANÁLISIS DE MERCADO (2-3 oraciones sobre las tendencias en su zona de interés)

3. RECOMENDACIONES CLAVE (por qué las propiedades seleccionadas son ideales)

4. PREGUNTAS SUGERIDAS (3-4 preguntas inteligentes para la próxima reunión)

5. PRÓXIMOS PASOS (acciones concretas recomendadas)

Formato: Markdown, profesional, conciso (máximo 400 palabras).
"""
        
        briefing_llm = llm._call_zai(prompt)
        return briefing_llm
        
    except Exception as e:
        print(f"Error generando briefing con LLM: {e}")
        return generar_briefing_personalizado(perfil, recomendaciones)
```

**2. Integrar en endpoint existente**

Modificar `/api/recomendar-mejorado-llm`:

```python
# ... después de generar recomendaciones ...

# Generar briefing ejecutivo con LLM
briefing = generar_briefing_ejecutivo_llm(
    recomendaciones, 
    perfil, 
    data.get('informacion_llm', '')
)

return jsonify({
    'success': True,
    'recomendaciones': recomendaciones,
    'briefing_ejecutivo': briefing,
    'llm_disponible': bool(os.getenv('ZAI_API_KEY'))
})
```

**3. Botón de exportación en `citrino-reco.html`**

```javascript
function exportBriefing(briefing, profileData) {
    const fecha = new Date().toISOString().split('T')[0];
    const nombre = profileData.nombreCliente || 'Prospecto';
    
    const contenido = `
# Briefing Ejecutivo - ${nombre}
**Fecha:** ${fecha}
**Asesor:** Citrino

---

${briefing}

---

*Generado automáticamente por Citrino con análisis de Z.AI GLM-4.5-Air*
*Basado en ${profileData.total_propiedades || 1583} propiedades en Santa Cruz de la Sierra*
    `;
    
    // Descargar como markdown
    const blob = new Blob([contenido], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `briefing_${nombre.replace(/\s+/g, '_')}_${fecha}.md`;
    a.click();
    
    showToast('Briefing exportado correctamente', 'success');
}
```

**4. UI para mostrar el briefing**

```html
<!-- En citrino-reco.html, después de las recomendaciones -->
<div id="briefingSection" class="briefing-section" style="display: none;">
    <div class="briefing-header">
        <h3><i class="bi bi-file-earmark-text"></i> Briefing Ejecutivo</h3>
        <button class="btn btn-sm btn-outline-primary" onclick="exportBriefing(currentBriefing, currentProfile)">
            <i class="bi bi-download"></i> Exportar
        </button>
    </div>
    <div id="briefingContent" class="briefing-content markdown-body">
        <!-- Contenido del briefing en markdown -->
    </div>
</div>
```

**5. CSS para el briefing**

```css
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

---

## 📋 Orden de Implementación Recomendado

### Fase 1: Backend (api/server.py)
1. Crear función `generar_briefing_ejecutivo_llm()`
2. Crear endpoint `/api/recomendar-mejorado-llm`
3. Probar con Postman o curl

### Fase 2: API Client (assets/js/api.js)
1. Añadir método `getRecommendationsWithLLM()`
2. Probar en consola del navegador

### Fase 3: Frontend (citrino-reco.html)
1. Actualizar función `generateRecommendations()`
2. Añadir función `buildRecommendationCard()` con LLM
3. Añadir sección de briefing ejecutivo
4. Implementar función `exportBriefing()`

### Fase 4: Estilos (CSS)
1. Estilos para `.llm-analysis`
2. Estilos para `.briefing-section`

### Fase 5: Testing
1. Probar sin API key (fallback)
2. Probar con API key (enriquecimiento)
3. Verificar exportación de briefing

---

## 🧪 Casos de Prueba

### Test 1: Enriquecimiento Básico
```javascript
// Perfil con información adicional
{
  nombreCliente: "Juan Pérez",
  presupuesto_min: 150000,
  presupuesto_max: 200000,
  zona_preferida: "Equipetrol",
  tipo_propiedad: "departamento",
  informacion_llm: "El prospecto busca para inversión, renta corta plazo, cerca de zona corporativa"
}
```

**Resultado esperado:**
- Recomendaciones con campo `analisis_personalizado`
- Briefing ejecutivo con análisis de mercado
- Badge "Análisis con Z.AI" visible

### Test 2: Fallback sin Z.AI
```javascript
// Sin información adicional o sin API key
{
  nombreCliente: "María González",
  presupuesto_min: 100000,
  presupuesto_max: 150000,
  zona_preferida: "Norte"
}
```

**Resultado esperado:**
- Recomendaciones normales sin LLM
- Briefing estándar (sin Z.AI)
- Sin badge de Z.AI

### Test 3: Error Handling
- Simular timeout de Z.AI
- Verificar que muestra recomendaciones básicas
- Toast indicando fallback

---

## 💰 Consideraciones de Costos Z.AI

### Estimación por Uso

**Opción A (Enriquecer Justificaciones):**
- ~200 tokens por propiedad
- 6 propiedades × 200 tokens = 1,200 tokens/recomendación
- Plan básico $3/mes incluye límite generoso

**Opción C (Briefing Ejecutivo):**
- ~500 tokens por briefing
- 1 briefing por sesión de recomendaciones

**Total estimado:**
- ~1,700 tokens por uso completo de Citrino Reco
- Plan básico cubre ~100-200 usos/mes

### Optimizaciones
1. Cachear briefings por 1 hora (mismo perfil)
2. Limitar enriquecimiento a top 5 propiedades
3. Usar GLM-4.5-Air (más económico que GLM-4.5)

---

## 🚀 Commit Planificado

### Commit Title
```
feat: integrar z.ai en Citrino Reco con enriquecimiento y briefing

- Opción A: Enriquecer justificaciones con análisis personalizado
- Opción C: Generar briefing ejecutivo con análisis de mercado
- Nuevo endpoint /api/recomendar-mejorado-llm
- Campo informacion_llm ahora alimenta prompts de Z.AI
- Exportación de briefing en markdown
- Fallback automático si Z.AI no está disponible
```

### Archivos a Modificar
```
api/server.py (nuevo endpoint + función briefing LLM)
assets/js/api.js (nuevo método getRecommendationsWithLLM)
citrino-reco.html (actualizar renderizado + sección briefing)
assets/css/custom.css (estilos para LLM)
```

### Archivos a Crear
```
NINGUNO (todo se integra en archivos existentes)
```

---

## 📚 Referencias Útiles

### Documentación Z.AI
- API: https://docs.z.ai/api-reference/llm/chat-completion
- Modelos: https://docs.z.ai/guides/llm/glm-4.5
- Pricing: https://z.ai/model-api

### Estado Actual del Código
- `src/llm_integration.py`: Clase `LLMIntegration` lista para usar
- Método `_call_zai()` ya implementado y funcionando
- Variable `ZAI_API_KEY` configurada en Render

### Endpoints Actuales
- `/api/health` - Health check ✅
- `/api/recomendar` - Recomendaciones básicas ✅
- `/api/recomendar-mejorado` - Con georreferenciación ✅
- `/api/chat/process` - Con Z.AI integrado ✅
- `/api/recomendar-mejorado-llm` - **PENDIENTE** ❌

---

## ✅ Checklist de Implementación

### Backend
- [ ] Función `generar_briefing_ejecutivo_llm()` en server.py
- [ ] Endpoint `/api/recomendar-mejorado-llm` en server.py
- [ ] Lógica de enriquecimiento de justificaciones
- [ ] Manejo de errores y fallback

### Frontend
- [ ] Método `getRecommendationsWithLLM()` en api.js
- [ ] Actualizar `generateRecommendations()` en citrino-reco.html
- [ ] Función `buildRecommendationCard()` con soporte LLM
- [ ] Sección de briefing ejecutivo en HTML
- [ ] Función `exportBriefing()` para markdown

### UI/UX
- [ ] Estilos para `.llm-analysis`
- [ ] Estilos para `.briefing-section`
- [ ] Badge "Análisis con Z.AI"
- [ ] Loading states durante llamadas LLM
- [ ] Toast notifications

### Testing
- [ ] Probar con información adicional
- [ ] Probar sin API key (fallback)
- [ ] Verificar exportación de briefing
- [ ] Probar en GitHub Pages
- [ ] Verificar en mobile

---

## 🎯 Resultado Final Esperado

Cuando un usuario use Citrino Reco:

1. **Llena el formulario** con datos del prospecto
2. **Añade contexto** en "Información adicional para z.ai"
3. **Genera recomendaciones**
4. **Ve propiedades** con justificaciones enriquecidas por Z.AI
5. **Lee briefing ejecutivo** con análisis personalizado
6. **Exporta briefing** en markdown para compartir

**Valor añadido:**
- Justificaciones más convincentes y personalizadas
- Análisis de mercado contextualizado
- Preguntas inteligentes para próxima reunión
- Documento profesional para compartir con prospecto

---

## 📞 Contacto y Soporte

**API Key Z.AI:** `34431b5a2e38422baa5551d4d623519f.DEYL3LOWMUFvL0kh`
**Backend URL:** https://citrino.onrender.com
**Frontend URL:** https://vincentiwadsworth.github.io/citrino/

---

**Última actualización:** 2025-10-09
**Estado del sistema:** ✅ Backend Live, Frontend pendiente GitHub Pages
**Próximo paso:** Implementar Opción A + C en Citrino Reco
