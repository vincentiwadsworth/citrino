# 🗺️ Roadmap de Citrino

## Prioridades 2025

### 1. Sistema de Gestión de Planillas Excel
**Problema:** El personal debe cargar/quitar archivos `.xlsx` manualmente en `data/raw/`.

**Solución:**
- [ ] Panel web de administración para carga de archivos
- [ ] Validación automática de formato y esquema
- [ ] Versionado y respaldo automático
- [ ] Vista previa de datos antes de procesar
- [ ] Sistema de permisos por rol (admin/editor/viewer)
- [ ] Historial de cambios con rollback

**Beneficio:** Reducir errores humanos y democratizar acceso a actualización de datos.

---

### 2. Corrección de Errores en Archivos Excel
**Problema:** Los archivos `.xlsx` contienen:
- Esquemas inconsistentes entre fechas del mismo proveedor
- Campos críticos vacíos o mal formateados
- Duplicados no detectados

**Solución:**
- [ ] Validador pre-procesamiento con reglas por proveedor
- [ ] Normalización automática de tipos de datos
- [ ] Auto-corrección de formatos de precio/moneda
- [ ] Sugerencias inteligentes para campos vacíos
- [ ] Reportes de calidad por archivo
- [ ] Quarantine para archivos con >20% errores

**Beneficio:** Mejorar score de calidad de 14.4% → >40%.

---

### 3. Geocodificación con OpenStreetMap/Google Maps
**Problema:** 61.9% de propiedades sin zona.

**Solución:**
- [ ] Integración con Google Maps Geocoding API
- [ ] Sistema híbrido: OSM gratuito + Google fallback
- [ ] Cache de resultados de geocodificación
- [ ] Catálogo expandido 30 → 100+ zonas
- [ ] Validación manual asistida para coordenadas ambiguas
- [ ] Enriquecimiento con barrios, UV, manzanas

**Beneficio:** Reducir propiedades sin zona de 61.9% → <15%.

---

### 4. Mejoras de UI/UX y Responsividad
**Problema:** Interfaz funcional pero mejorable en móviles.

**Solución:**
- [ ] Rediseño responsive mobile-first
- [ ] Optimización de performance (lazy loading)
- [ ] Mejora de flujos de navegación
- [ ] Componentes de carga y feedback visual
- [ ] Dark mode
- [ ] Accesibilidad WCAG 2.1 nivel AA
- [ ] PWA con trabajo offline

**Beneficio:** Aumentar adopción del equipo interno.

---

## Q1 2025

- [ ] **Mobile App** - iOS y Android nativo
- [ ] **Integración WhatsApp** - Chatbot Business
- [ ] **Dashboard Analytics** - Métricas en tiempo real
- [ ] **Notificaciones Push** - Alertas de nuevas propiedades

## Mediano Plazo

- [ ] **Migración PostgreSQL** - De JSON a relacional
- [ ] **ML Avanzado** - Modelos predictivos
- [ ] **API GraphQL** - Más eficiente que REST
- [ ] **Multi-zona** - Expansión a otras ciudades bolivianas
- [ ] **Portal de Agentes** - Panel para agentes inmobiliarios

## Mejoras Continuas

- [ ] **Performance Optimization** - Reducción de latencia
- [ ] **Security Updates** - Mantenimiento continuo
- [ ] **Documentation** - Tutoriales y ejemplos

---

---

**Documento interno de Citrino - Última actualización:** Enero 2025
