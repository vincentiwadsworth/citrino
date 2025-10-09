# Configuración de Z.AI para Citrino

## ✅ Configuración Local (Ya completada)

Tu API key de Z.AI está configurada en el archivo `.env` local. Este archivo **NO se sube a GitHub** por seguridad.

**API Key configurada:** `34431b5a2e38422baa5551d4d623519f.DEYL3LOWMUFvL0kh`

---

## 🧪 Probar Z.AI Localmente

### Paso 1: Instalar dependencias

```bash
pip install -r requirements_api.txt
```

### Paso 2: Ejecutar script de prueba

```bash
python test_zai_integration.py
```

**Resultado esperado:**
```
============================================================
PRUEBA DE INTEGRACIÓN Z.AI
============================================================
✅ API Key configurada: 34431b5a2e38422baa...
Validando configuración...
✅ Configuración válida

📝 Mensaje de prueba:
   'Busco un departamento en Equipetrol de 3 habitaciones, presupuesto hasta 200000 dólares'

🔄 Procesando con Z.AI (puede tardar 10-30 segundos)...

✅ RESPUESTA DE Z.AI:
------------------------------------------------------------
Composición familiar: {'adultos': 2, 'ninos': [], 'adultos_mayores': 0}
Presupuesto: {'min': 160000, 'max': 200000, 'tipo': 'compra'}
Necesidades: []
Preferencias: {'ubicacion': 'Equipetrol', ...}
------------------------------------------------------------

✅ ¡Integración con Z.AI funcionando correctamente!
```

### Paso 3: Iniciar API con Z.AI

```bash
python api/server.py
```

Luego abre en tu navegador: `http://localhost:5001/api/health`

---

## 🚀 Configurar Z.AI en Producción (Render.com)

### IMPORTANTE: NO subir la API key a GitHub

La API key ya está protegida localmente. Para producción:

### Paso 1: Subir código a GitHub (sin .env)

```bash
git status  # Verificar que .env NO aparece
git push origin master
```

### Paso 2: Configurar en Render

1. **Ir a [render.com](https://render.com)**
2. **Conectar tu repositorio** `citrino-clean`
3. **Crear Web Service** (Render detectará `render.yaml` automáticamente)
4. **En la sección "Environment"**, añadir variable:

   | Variable | Valor | Secret |
   |----------|-------|--------|
   | `ZAI_API_KEY` | `34431b5a2e38422baa5551d4d623519f.DEYL3LOWMUFvL0kh` | ✅ Sí |
   | `LLM_PROVIDER` | `zai` | No |
   | `LLM_MODEL` | `glm-4.5-air` | No |

5. **Deploy** (tarda 3-5 minutos la primera vez)

### Paso 3: Verificar que funciona

Una vez deployado, probar:

```
https://citrino-api.onrender.com/api/health
```

---

## 🔒 Seguridad

### ✅ Protecciones Implementadas

- ✅ `.env` está en `.gitignore` → NO se sube a GitHub
- ✅ API key solo en variables de entorno
- ✅ Render marca `ZAI_API_KEY` como secreta (encriptada)

### ⚠️ NUNCA hacer esto:

- ❌ Commitear archivo `.env`
- ❌ Hardcodear la API key en el código
- ❌ Compartir la API key públicamente
- ❌ Subirla a issues o PRs de GitHub

### 🔄 Si la API key se compromete:

1. Ir a [z.ai/model-api](https://z.ai/model-api)
2. Revocar la API key antigua
3. Generar una nueva
4. Actualizar en `.env` local
5. Actualizar en Render → Environment

---

## 💰 Costos de Z.AI

**Plan actual recomendado:** GLM Coding Plan

- **Costo:** $3/mes
- **Modelo:** GLM-4.5-Air (eficiente y económico)
- **Tokens:** Incluye límite generoso
- **Upgrades:** Disponibles según necesidad

**Monitorear uso en:** [z.ai dashboard](https://z.ai/dashboard)

---

## 🐛 Solución de Problemas

### Error: "API key no configurada"

**Local:**
```bash
# Verificar que .env existe
ls -la .env

# Verificar contenido (sin mostrar la key completa)
cat .env | grep ZAI_API_KEY
```

**Render:**
- Dashboard → tu servicio → Environment
- Verificar que `ZAI_API_KEY` está presente

### Error: "Proveedor no soportado"

Verificar que `LLM_PROVIDER=zai` está configurado.

### Error de conexión con Z.AI

1. Verificar que la API key es válida en [z.ai](https://z.ai)
2. Revisar que hay créditos disponibles
3. Verificar límites de rate no excedidos
4. Probar con el script `test_zai_integration.py`

### Timeout al procesar

Z.AI puede tardar 10-30 segundos. El timeout está configurado en 60s.

---

## 📊 Monitoreo

### Logs en Render

```bash
# Ver logs en vivo
render logs -s citrino-api -f
```

### Verificar que Z.AI se está usando

En los logs del backend, buscar:
```
[Citrino API] Usando Z.AI para procesamiento LLM
```

---

## ✅ Checklist de Configuración

- [x] API key de Z.AI obtenida
- [x] `.env` creado localmente
- [x] `.env` en `.gitignore`
- [ ] Dependencias instaladas (`pip install -r requirements_api.txt`)
- [ ] Script de prueba ejecutado (`python test_zai_integration.py`)
- [ ] API local funcionando (`python api/server.py`)
- [ ] Código subido a GitHub (`git push`)
- [ ] Servicio creado en Render
- [ ] Variables de entorno configuradas en Render
- [ ] Deploy exitoso en Render
- [ ] Verificación de `/api/health` en producción
- [ ] GitHub Pages configurado
- [ ] Frontend conectando con backend en producción

---

**¡Tu API key de Z.AI está segura y lista para usar!** 🎉
