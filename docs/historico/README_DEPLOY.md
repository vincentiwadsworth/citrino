# Guía de Despliegue - Citrino

Esta guía explica cómo desplegar Citrino en producción utilizando **GitHub Pages** (frontend) y **Render.com** (backend).

## 📋 Requisitos Previos

- Cuenta de GitHub
- Cuenta de Render.com (gratis)
- Cuenta de Z.AI con API Key (para integración LLM)
- Git instalado localmente

## 🏗️ Arquitectura de Despliegue

```
┌─────────────────┐
│  GitHub Pages   │  ← Frontend (HTML, CSS, JS)
│  (Estático)     │     URL: https://[usuario].github.io/citrino-clean/
└────────┬────────┘
         │
         │ API Calls
         ▼
┌─────────────────┐
│   Render.com    │  ← Backend (Flask API)
│  (Python/Flask) │     URL: https://citrino-api.onrender.com/api/
└────────┬────────┘
         │
         │ LLM Requests
         ▼
┌─────────────────┐
│     Z.AI        │  ← Servicio LLM
│  (GLM-4.5-Air)  │     API: https://api.z.ai/
└─────────────────┘
```

## 🚀 PASO 1: Desplegar Backend en Render.com

### 1.1 Crear cuenta en Render

1. Ir a [render.com](https://render.com)
2. Registrarse con GitHub
3. Autorizar acceso a tus repositorios

### 1.2 Conectar repositorio

1. En el Dashboard de Render, click en **"New +"** → **"Web Service"**
2. Conectar tu repositorio `citrino-clean`
3. Configurar el servicio:

   ```
   Name: citrino-api
   Region: Oregon (US West)
   Branch: master
   Runtime: Python 3
   Build Command: pip install -r requirements_api.txt
   Start Command: gunicorn api.server:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
   ```

4. Seleccionar plan **Free**

### 1.3 Configurar Variables de Entorno

En la sección **Environment** del dashboard de Render, añadir:

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `FLASK_ENV` | `production` | Entorno de Flask |
| `PORT` | `(autodetectado)` | Puerto del servidor |
| `ZAI_API_KEY` | `tu_clave_aqui` | API Key de Z.AI (⚠️ marcar como secreta) |
| `LLM_PROVIDER` | `zai` | Proveedor de LLM |
| `LLM_MODEL` | `glm-4.5-air` | Modelo de Z.AI |
| `GITHUB_PAGES_URL` | `https://[tu-usuario].github.io/citrino-clean` | URL del frontend |

### 1.4 Obtener API Key de Z.AI

1. Ir a [z.ai/model-api](https://z.ai/model-api)
2. Crear cuenta o iniciar sesión
3. Navegar a **API Keys** en el dashboard
4. Generar nueva API Key
5. Copiar la clave y añadirla a Render como `ZAI_API_KEY`

⚠️ **IMPORTANTE**: Marcar `ZAI_API_KEY` como **variable secreta** en Render.

### 1.5 Desplegar

1. Click en **"Create Web Service"**
2. Render iniciará el build automáticamente
3. Esperar 3-5 minutos para el primer despliegue
4. Una vez completado, copiar la URL: `https://citrino-api.onrender.com`

### 1.6 Verificar Backend

Abrir en el navegador:
```
https://citrino-api.onrender.com/api/health
```

Deberías ver:
```json
{
  "status": "ok",
  "message": "API Citrino funcionando",
  "total_propiedades": 1583
}
```

## 🌐 PASO 2: Desplegar Frontend en GitHub Pages

### 2.1 Configurar GitHub Pages

1. En tu repositorio de GitHub, ir a **Settings** → **Pages**
2. En **Source**, seleccionar:
   - Branch: `master` (o `main`)
   - Folder: `/ (root)`
3. Click en **Save**
4. GitHub generará tu sitio en: `https://[tu-usuario].github.io/citrino-clean/`

### 2.2 Actualizar URL de API (si es necesario)

Si la URL de Render es diferente a `https://citrino-api.onrender.com`, puedes:

**Opción A**: Configurar globalmente en `index.html` (antes de cargar scripts):
```html
<script>
  window.CITRINO_API_URL = 'https://tu-url-de-render.com/api';
</script>
```

**Opción B**: El código ya detecta automáticamente el entorno y usa la URL por defecto.

### 2.3 Verificar Despliegue

1. Esperar 1-2 minutos para que GitHub Pages procese los archivos
2. Abrir: `https://[tu-usuario].github.io/citrino-clean/`
3. Verificar que:
   - La página carga correctamente
   - Los estilos se aplican
   - La consola del navegador muestra: `[Citrino API] Entorno: Producción`

### 2.4 Probar Integración

1. Ir a **Citrino Reco** desde el menú
2. Llenar el formulario con datos de prueba
3. Click en **"Generar recomendaciones"**
4. Si hay conexión con Render, verás recomendaciones reales
5. Si Render está "durmiendo" (free tier), esperar 30-60 segundos para que despierte

## 🔄 Actualizaciones Automáticas

### Backend (Render)

Render redespliega automáticamente cuando haces `git push` a la rama configurada:

```bash
git add .
git commit -m "feat: actualizar lógica de recomendaciones"
git push origin master
```

Render detectará el cambio y redespliegará en ~2-3 minutos.

### Frontend (GitHub Pages)

GitHub Pages se actualiza automáticamente cuando haces push:

```bash
git add .
git commit -m "docs: actualizar página de inicio"
git push origin master
```

Los cambios aparecerán en 1-2 minutos.

## ⚠️ Limitaciones del Free Tier de Render

1. **Sleep después de 15 minutos de inactividad**
   - Primera petición tarda 30-60 segundos en despertar
   - Peticiones subsiguientes son rápidas

2. **750 horas/mes gratuitas**
   - Suficiente para desarrollo y demos
   - El servicio se apaga cuando no se usa

3. **Builds lentos**
   - Primer despliegue: 3-5 minutos
   - Redespliegues: 2-3 minutos

## 🐛 Solución de Problemas

### Backend no responde

1. **Verificar estado del servicio en Render**
   - Dashboard → citrino-api → Logs
   - Buscar errores en los logs

2. **Error de módulos faltantes**
   ```bash
   # Añadir a requirements_api.txt y push
   nuevo-paquete==version
   ```

3. **CORS bloqueando peticiones**
   - Verificar que `GITHUB_PAGES_URL` esté configurado en Render
   - Revisar logs de CORS en el navegador (F12 → Console)

### Frontend no conecta con Backend

1. **Verificar URL de API en consola**
   ```javascript
   // En la consola del navegador
   console.log(window.citrinoAPI.baseURL)
   ```

2. **Render está "durmiendo"**
   - Esperar 30-60 segundos en la primera carga
   - El spinner de carga debe aparecer

3. **Error de CORS**
   - Abrir DevTools (F12) → Network
   - Buscar requests a `/api/` que fallen
   - Verificar headers CORS en Response

### Z.AI no funciona

1. **Verificar API Key**
   - En Render Dashboard → Environment → `ZAI_API_KEY`
   - Regenerar clave en z.ai si es necesario

2. **Cuota excedida**
   - Revisar uso en dashboard de Z.AI
   - El sistema tiene fallback automático si Z.AI falla

3. **Timeout del LLM**
   - Aumentar timeout en `src/llm_integration.py`
   - Verificar logs en Render

## 📊 Monitoreo

### Logs de Backend (Render)

```bash
# Ver en vivo desde la web
Dashboard → citrino-api → Logs

# O desde CLI (render-cli)
render logs -s citrino-api -f
```

### Logs de Frontend

```javascript
// En la consola del navegador (F12)
// Citrino API logea automáticamente:
// [Citrino API] Entorno: Producción
// [Citrino API] Base URL: https://...
```

### Métricas de Render

Dashboard → citrino-api → Metrics:
- CPU Usage
- Memory Usage
- Request Count
- Response Time

## 🔐 Seguridad

### Variables Secretas

⚠️ **NUNCA** commitear:
- `.env` con valores reales
- `ZAI_API_KEY` en el código
- Credenciales de base de datos

✅ **SIEMPRE**:
- Usar variables de entorno en Render
- Marcar `ZAI_API_KEY` como secreta
- Usar `.env.example` como plantilla

### CORS

El backend está configurado para aceptar requests solo de:
- `localhost` (desarrollo)
- `github.io` (GitHub Pages)
- URL específica en `GITHUB_PAGES_URL`

## 💰 Costos Estimados

| Servicio | Plan | Costo |
|----------|------|-------|
| GitHub Pages | Gratis | $0 |
| Render.com | Free Tier | $0 |
| Z.AI | GLM-4.5-Air | $3/mes (plan básico) |
| **Total** | | **$3/mes** |

## 🚀 Próximos Pasos

1. ✅ Desplegar backend en Render
2. ✅ Desplegar frontend en GitHub Pages
3. ✅ Configurar Z.AI
4. 📧 Compartir URL con el equipo de Citrino
5. 📊 Monitorear uso y métricas
6. 🔄 Iterar basado en feedback

## 🆘 Soporte

Si encuentras problemas:

1. Revisar logs en Render
2. Revisar consola del navegador (F12)
3. Consultar [documentación de Render](https://render.com/docs)
4. Consultar [documentación de Z.AI](https://docs.z.ai)

---

**¡Listo!** Tu sistema Citrino debería estar funcionando online. 🎉

Comparte la URL de GitHub Pages con el equipo de Citrino para mostrar el avance.
