#!/usr/bin/env python3
"""
Demo mejorada de Citrino con UX profesional
Incluye explicaciones, perfiles diversos y corrección de problemas
"""

import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime

# Configuración
API_URL = "http://localhost:5000"

st.set_page_config(
    page_title="Citrino - Sistema de Recomendación Inmobiliaria",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para mejor diseño
st.markdown("""
<style>
    .welcome-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 3rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .main-header {
        background: linear-gradient(135deg, #2c5f7a 0%, #1e3c72 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .feature-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #2a5298;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .compatibility-high {
        color: #28a745;
        font-weight: bold;
    }
    .compatibility-medium {
        color: #ffc107;
        font-weight: bold;
    }
    .compatibility-low {
        color: #dc3545;
        font-weight: bold;
    }
    .profile-card {
        background: #e8f4f8;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #bee5eb;
        margin-bottom: 0.5rem;
    }
    .profile-card.selected {
        background: #d1ecf1;
        border-color: #2a5298;
    }
    .cta-button {
        background: linear-gradient(45deg, #28a745, #20c997);
        color: white;
        padding: 1rem 2rem;
        border-radius: 8px;
        text-decoration: none;
        font-weight: bold;
        display: inline-block;
        margin: 1rem;
        transition: transform 0.2s;
    }
    .cta-button:hover {
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# Estado de la sesión
if 'show_welcome' not in st.session_state:
    st.session_state.show_welcome = True

# Pantalla de bienvenida
if st.session_state.show_welcome:
    st.markdown("""
    <div class="welcome-header">
        <h1>🏠 Bienvenido a Citrino</h1>
        <h3>Sistema de Recomendación Inmobiliaria con Geolocalización Inteligente</h3>
        <p>Transformando la búsqueda de propiedades en Santa Cruz de la Sierra con tecnología de precisión</p>
        <br>
        <div style="display: flex; justify-content: center; gap: 1rem;">
            <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; margin: 0.5rem;">
                <h4>🗺️ 76,853 Propiedades</h4>
                <p>Con coordenadas exactas</p>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; margin: 0.5rem;">
                <h4>🏛️ 4,777 Servicios</h4>
                <p>Guía urbana municipal</p>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; margin: 0.5rem;">
                <h4>🎯 Precisión Real</h4>
                <p>Distancias Haversine</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])

    with col1:
        st.write("")

    with col2:
        st.markdown("""
        <div class="feature-card">
            <h4>🚀 ¿Qué hace a Citrino diferente?</h4>
            <p>Nuestro sistema utiliza <strong>geolocalización real</strong> y la <strong>fórmula de Haversine</strong>
            para calcular distancias exactas entre propiedades y servicios urbanos, reemplazando las aproximaciones
            tradicionales por zona.</p>

            <h5>🎯 Beneficios Clave:</h5>
            <ul>
                <li><strong>Recomendaciones precisas</strong> basadas en distancia real a servicios</li>
                <li><strong>Análisis de necesidades</strong> (educación, salud, transporte, etc.)</li>
                <li><strong>Optimización inteligente</strong> para resultados en tiempo real</li>
                <li><strong>Transparencia total</strong> en el proceso de recomendación</li>
            </ul>

            <p style="text-align: center; margin-top: 2rem;">
                <em>Descubre cómo la tecnología está transformando el mercado inmobiliario en Santa Cruz de la Sierra</em>
            </p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚀 Comenzar a Explorar", type="primary", use_container_width=True):
            st.session_state.show_welcome = False
            st.rerun()

    with col3:
        st.write("")

else:
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>🏠 Citrino - Sistema de Recomendación Inmobiliaria</h1>
        <h3>Inteligencia de Mercado con Geolocalización Precisa para Santa Cruz de la Sierra</h3>
        <p>Analizando 76,853 propiedades con tecnología de distancia Haversine y guía urbana municipal</p>
        <p style="font-size: 0.9em; opacity: 0.8;">
            <a href="#" onclick="alert('Función no implementada en demo')">← Volver a la bienvenida</a>
        </p>
    </div>
    """, unsafe_allow_html=True)

# Contenido principal (solo se muestra después de la bienvenida)
if not st.session_state.show_welcome:
    # Sidebar con información y controles
    st.sidebar.title("🎯 Panel de Control")

  # Estado del sistema
    st.sidebar.subheader("📊 Estado del Sistema")
    try:
        health_response = requests.get(f"{API_URL}/api/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            st.sidebar.success(f"✅ API Activa")
            st.sidebar.metric("Propiedades", f"{health_data.get('total_propiedades', 0):,}")
        else:
            st.sidebar.error("❌ API No Responde")
    except:
        st.sidebar.error("❌ Error de Conexión")

    # Botón para volver a bienvenida
    if st.sidebar.button("🏠 Volver a Bienvenida"):
        st.session_state.show_welcome = True
        st.rerun()

    st.sidebar.markdown("---")

    # Sección 1: Valor de Citrino
    st.header("💎 El Valor de Citrino")

# Sección Técnica: Algoritmo de Georreferenciación
with st.expander("🔬 Tecnología: Algoritmo de Cercanía con Haversine", expanded=False):
    st.markdown("""
    <div class="feature-card">
        <h4>🧮 Fórmula de Haversine para Cálculo de Distancias Reales</h4>
        <p><strong>Problema:</strong> Calcular distancias exactas entre propiedades y servicios en Santa Cruz de la Sierra.</p>

        <p><strong>Solución:</strong> Implementamos la fórmula de Haversine que calcula la distancia entre dos puntos
        en una esfera (la Tierra) usando sus coordenadas de latitud y longitud.</p>

        <p><strong>Fórmula:</strong></p>
        <code>
        a = sin²(Δφ/2) + cos(φ₁) × cos(φ₂) × sin²(Δλ/2)<br>
        c = 2 × atan2(√a, √(1−a))<br>
        d = R × c<br>
        (donde R = 6,371 km, radio de la Tierra)
        </code>

        <h4>⚡ Optimización por Pre-filtrado de Zonas</h4>
        <p><strong>Problema:</strong> Procesar 76,853 propiedades con 4,777 servicios es computacionalmente costoso.</p>

        <p><strong>Solución:</strong> Antes de calcular distancias, el sistema:</p>
        <ol>
            <li><strong>Pre-filtra por zona preferida:</strong> Si el usuario especifica "Equipetrol",
                solo evalúa propiedades en esa zona (reduciendo ~76k a ~2k propiedades)</li>
            <li><strong>Búsqueda flexible:</strong> Busca coincidencias parciales (ej: "Equipetrol" en "Equipetrol Norte")</li>
            <li><strong>Fallback inteligente:</strong> Si no hay propiedades en la zona, evalúa todas las propiedades</li>
        </ol>

        <p><strong>Resultado:</strong> Reducción de tiempo de procesamiento de ~2 minutos a ~0.8 segundos</p>

        <h4>🎯 Mapeo de Necesidades a Servicios</h4>
        <p>El sistema convierte necesidades genéricas de usuarios en categorías específicas de servicios:</p>
        <ul>
            <li><strong>"seguridad"</strong> → busca servicios cercanos de <em>salud</em> y <em>transporte</em></li>
            <li><strong>"educación"</strong> → busca <em>centros educativos</em> en radio de 1km</li>
            <li><strong>"compras"</strong> → busca <em>abastecimiento</em> (supermercados, comercios)</li>
            <li><strong>"deporte"</strong> → busca <em>instalaciones deportivas</em> y áreas verdes</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="metric-card">
        <h4>🏠 Propiedades</h4>
        <h2>76,853</h2>
        <p>Registros validados</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-card">
        <h4>📊 Inteligencia</h4>
        <h2>323</h2>
        <p>Proyectos con análisis</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-card">
        <h4>🏙️ Datos Urbanos</h4>
        <h2>8,623</h2>
        <p>Puntos georreferenciados</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="metric-card">
        <h4>⚡ Rendimiento</h4>
        <h2><2s</h2>
        <p>Tiempo de respuesta</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Características principales
st.subheader("🚀 Características Principales")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("""
    <div class="feature-card">
        <h4>🎯 Sistema de Recomendación Avanzado</h4>
        <p>Algoritmo multi-factor que evalúa:
        • Compatibilidad presupuestaria (30%)
        • Composición familiar (25%)
        • Servicios cercanos (20%)
        • Análisis demográfico (15%)
        • Preferencias personales (10%)</p>
    </div>
    """, unsafe_allow_html=True)

with col_b:
    st.markdown("""
    <div class="feature-card">
        <h4>📊 Inteligencia de Mercado Exclusiva</h4>
        <p>Análisis detallado de:
        • Tendencias de precios por zona
        • Demanda y oferta en tiempo real
        • Proyectos de desarrollo inmobiliario
        • Valorización sectorial</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Sección 2: Perfiles de Prospectos
st.header("👥 Perfiles de Prospectos")

st.markdown("""
Seleccione un perfil de prospecto para ver recomendaciones personalizadas.
Cada perfil tiene diferentes necesidades, presupuestos y preferencias.
""")

# Definición de perfiles diversos
perfiles = {
    "familia_joven": {
        "nombre": "Familia Joven Profesional",
        "descripcion": "Pareja joven con 1 hijo, buscando seguridad y espacio para crecer",
        "presupuesto_min": 120000,
        "presupuesto_max": 200000,
        "adultos": 2,
        "ninos": [1],
        "adultos_mayores": 0,
        "zona_preferida": "Equipetrol",
        "tipo_propiedad": "departamento",
        "necesidades": ["seguridad", "estacionamiento", "areas_comunes", "gimnasio"],
        "icono": "👨‍👩‍👧"
    },
    "inversor": {
        "nombre": "Inversor Inmobiliario",
        "descripcion": "Buscando propiedades con alto potencial de plusvalía y rentabilidad",
        "presupuesto_min": 200000,
        "presupuesto_max": 400000,
        "adultos": 1,
        "ninos": [],
        "adultos_mayores": 0,
        "zona_preferida": "Equipetrol",
        "tipo_propiedad": "departamento",
        "necesidades": ["plusvalia", "rentabilidad", "ubicacion_estrategica", "seguridad"],
        "icono": "💼"
    },
    "joven_emprendedor": {
        "nombre": "Joven Emprendedor (Herencia)",
        "descripcion": "Joven que recibió herencia sustancial, busca proteger poder adquisitivo y seguridad",
        "presupuesto_min": 300000,
        "presupuesto_max": 600000,
        "adultos": 1,
        "ninos": [],
        "adultos_mayores": 0,
        "zona_preferida": "Equipetrol",
        "tipo_propiedad": "departamento",
        "necesidades": ["seguridad", "inversion_segura", "plusvalia", "prestigio", "calidad_construccion"],
        "icono": "🎯"
    },
    "profesional_joven": {
        "nombre": "Profesional Joven",
        "descripcion": "Individuo independiente, buscando primera inversión o propiedad para vivir",
        "presupuesto_min": 80000,
        "presupuesto_max": 150000,
        "adultos": 1,
        "ninos": [],
        "adultos_mayores": 0,
        "zona_preferida": "Zona Norte",
        "tipo_propiedad": "departamento",
        "necesidades": ["seguridad", "estacionamiento", "gimnasio", "ubicacion_centrada"],
        "icono": "👔"
    },
    "familia_grande": {
        "nombre": "Familia Grande",
        "descripcion": "Familia con 3 hijos, necesita espacio amplio y zonas seguras",
        "presupuesto_min": 250000,
        "presupuesto_max": 400000,
        "adultos": 2,
        "ninos": [1, 2, 3],
        "adultos_mayores": 0,
        "zona_preferida": "Las Palmas",
        "tipo_propiedad": "casa",
        "necesidades": ["espacio", "seguridad", "areas_verdes", "colegios_cercanos"],
        "icono": "👨‍👩‍👧‍👦"
    },
    "adultos_mayores": {
        "nombre": "Adultos Mayores",
        "descripcion": "Pareja de adultos mayores, buscando tranquilidad y accesibilidad",
        "presupuesto_min": 100000,
        "presupuesto_max": 180000,
        "adultos": 2,
        "ninos": [],
        "adultos_mayores": 2,
        "zona_preferida": "Centro",
        "tipo_propiedad": "departamento",
        "necesidades": ["tranquilidad", "accesibilidad", "servicios_medicos", "seguridad"],
        "icono": "👴👵"
    }
}

# Selección de perfil
st.subheader("👥 Perfiles de Prospectos")
perfil_seleccionado = st.selectbox(
    "Seleccionar Perfil de Prospecto:",
    list(perfiles.keys()),
    format_func=lambda x: f"{perfiles[x]['icono']} {perfiles[x]['nombre']}"
)

# Mostrar detalles del perfil seleccionado
if perfil_seleccionado:
    perfil = perfiles[perfil_seleccionado]
    st.markdown(f"""
    <div class="profile-card selected">
        <h4>{perfil['icono']} {perfil['nombre']}</h4>
        <p><strong>Descripción:</strong> {perfil['descripcion']}</p>
        <p><strong>Presupuesto:</strong> ${perfil['presupuesto_min']:,} - ${perfil['presupuesto_max']:,} USD</p>
        <p><strong>Zona preferida:</strong> {perfil['zona_preferida']}</p>
        <p><strong>Tipo:</strong> {perfil['tipo_propiedad']}</p>
        <p><strong>Necesidades:</strong> {', '.join(perfil['necesidades'])}</p>
    </div>
    """, unsafe_allow_html=True)

# Botón para generar recomendaciones
if st.button("🎯 Generar Recomendaciones", type="primary", use_container_width=True):
    if perfil_seleccionado:
        with st.spinner("Generando recomendaciones personalizadas..."):
            try:
                # Preparar perfil para la API
                api_perfil = {
                    "id": f"demo_{perfil_seleccionado}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "presupuesto_min": perfil["presupuesto_min"],
                    "presupuesto_max": perfil["presupuesto_max"],
                    "adultos": perfil["adultos"],
                    "ninos": perfil["ninos"],
                    "adultos_mayores": perfil["adultos_mayores"],
                    "zona_preferida": perfil["zona_preferida"],
                    "tipo_propiedad": perfil["tipo_propiedad"],
                    "necesidades": perfil["necesidades"],
                    "limite": 5,  # Reducido para mejor rendimiento del motor mejorado
                    "umbral_minimo": 0.5  # Aumentado para recomendaciones más relevantes
                }

                # Hacer petición a la API
                response = requests.post(f"{API_URL}/api/recomendar-mejorado", json=api_perfil, timeout=60)

                if response.status_code == 200:
                    resultado = response.json()

                    if resultado.get('success'):
                        recomendaciones = resultado.get('recomendaciones', [])

                        if recomendaciones:
                            st.success(f"🎯 Se encontraron {len(recomendaciones)} recomendaciones con geolocalización real")
                            st.info("ℹ️ Usando motor mejorado con distancias Haversine y guía urbana municipal")

                            # Mostrar recomendaciones en un formato mejorado
                            for i, rec in enumerate(recomendaciones, 1):
                                # Determinar clase de compatibilidad
                                compatibilidad = rec.get('compatibilidad', 0)
                                if compatibilidad >= 80:
                                    compat_class = "compatibility-high"
                                elif compatibilidad >= 60:
                                    compat_class = "compatibility-medium"
                                else:
                                    compat_class = "compatibility-low"

                                with st.expander(f"🏠 Opción {i}: {rec['nombre']} - ${rec['precio']:,} USD"):
                                    col1, col2 = st.columns([2, 1])

                                    with col1:
                                        st.markdown(f"""
                                        <div class="feature-card">
                                            <h4>📍 Ubicación y Características</h4>
                                            <p><strong>Zona:</strong> {rec['zona']}</p>
                                            <p><strong>Superficie:</strong> {rec['superficie_m2']} m²</p>
                                            <p><strong>Habitaciones:</strong> {rec['habitaciones']}</p>
                                            <p><strong>Baños:</strong> {rec['banos']}</p>
                                            <p><strong>Fuente:</strong> {rec['fuente']}</p>
                                        </div>
                                        """, unsafe_allow_html=True)

                                    with col2:
                                        st.markdown(f"""
                                        <div class="feature-card">
                                            <h4>📊 Análisis</h4>
                                            <p class="{compat_class}">Compatibilidad: {compatibility}%</p>
                                            <p><strong>Precio/m²:</strong> ${rec['precio']/rec['superficie_m2']:,.0f}</p>
                                        </div>
                                        """, unsafe_allow_html=True)

                                    st.markdown(f"""
                                    <div class="feature-card">
                                        <h4>💡 Justificación de Recomendación</h4>
                                        <p>{rec['justificacion']}</p>
                                    </div>
                                    """, unsafe_allow_html=True)

                                st.markdown("---")

                            # Mostrar briefing personalizado
                            if 'briefing_personalizado' in resultado:
                                st.subheader("📋 Briefing Personalizado")
                                st.markdown(f"""
                                <div class="feature-card">
                                    <pre>{resultado['briefing_personalizado']}</pre>
                                </div>
                                """, unsafe_allow_html=True)

                        else:
                            st.warning("⚠️ No se encontraron propiedades que coincidan con este perfil. Intente con otro perfil o ajuste los criterios.")

                    else:
                        st.error(f"❌ Error en la respuesta: {resultado.get('error', 'Error desconocido')}")

                else:
                    st.error(f"❌ Error HTTP: {response.status_code}")

            except requests.exceptions.ConnectionError:
                st.error("❌ No se puede conectar al servidor API. Asegúrese de que el servidor esté corriendo en http://localhost:5000")
            except Exception as e:
                st.error(f"❌ Error inesperado: {str(e)}")

# Sección 3: Limitaciones y Próximos Pasos
st.header("📈 Limitaciones y Roadmap")

col_l1, col_l2 = st.columns(2)

with col_l1:
    st.markdown("""
    <div class="feature-card">
        <h4>⚠️ Limitaciones Actuales</h4>
        <ul>
            <li><strong>Cobertura Geográfica:</strong> Enfocada en zonas principales de Santa Cruz</li>
            <li><strong>Actualización de Datos:</strong> Periodicidad semanal (no tiempo real)</li>
            <li><strong>Análisis de Riesgo:</strong> Limitado a factores básicos de mercado</li>
            <li><strong>Integración Externa:</strong> Sin conexión a servicios financieros aún</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col_l2:
    st.markdown("""
    <div class="feature-card">
        <h4>🚀 Próximos Mejoras</h4>
        <ul>
            <li><strong>Chat Natural:</strong> Interfaz conversacional con LLM</li>
            <li><strong>Análisis Predictivo:</strong> Modelos de valorización futura</li>
            <li><strong>Integración Financiera:</strong> Conexión con bancos y entidades</li>
            <li><strong>Mobile App:</strong> Versión móvil para agentes de campo</li>
            <li><strong>Dashboard Avanzado:</strong> Métricas de mercado en tiempo real</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem; background: #f8f9fa; border-radius: 8px;">
    <h3>🏢 Citrino Platform</h3>
    <p>Transformando la experiencia inmobiliaria en Santa Cruz de la Sierra con tecnología e inteligencia de mercado.</p>
    <p><strong>Base de Datos:</strong> 76,853 propiedades | <strong>Proyectos:</strong> 323 con inteligencia | <strong>Cobertura:</strong> 8,623 puntos urbanos</p>
</div>
""", unsafe_allow_html=True)

# Sidebar con información adicional
st.sidebar.markdown("---")
st.sidebar.subheader("ℹ️ Información")
st.sidebar.markdown("""
**Versión:** Demo v2.0
**Fecha:** {}
**Estado:** Funcional

**Requerimientos:**
- Servidor API corriendo
- Python 3.8+
- Streamlit 1.40+
""".format(datetime.now().strftime("%Y-%m-%d")))

st.sidebar.markdown("---")
st.sidebar.subheader("🔧 Configuración API")
st.sidebar.code("""
URL: http://localhost:5000
Endpoints:
- GET /api/health
- POST /api/buscar
- POST /api/recomendar
- GET /api/estadisticas
""")