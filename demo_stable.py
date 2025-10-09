#!/usr/bin/env python3
"""
Versión simplificada y estable de Citrino Demo
Diseñada para máxima estabilidad y rendimiento
"""

import streamlit as st
import requests
import json
from datetime import datetime

# Configuración
API_URL = "http://localhost:5000"

st.set_page_config(
    page_title="Citrino - Sistema de Recomendación Inmobiliaria",
    page_icon="🏠",
    layout="centered"
)

# CSS minimal para evitar conflictos
st.markdown("""
<style>
    .welcome-card {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-box {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem;
    }
    .profile-box {
        background: #e8f4f8;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #bee5eb;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Estado simple
if 'show_welcome' not in st.session_state:
    st.session_state.show_welcome = True

# Pantalla de bienvenida simplificada
if st.session_state.show_welcome:
    st.markdown("""
    <div class="welcome-card">
        <h1>🏠 Bienvenido a Citrino</h1>
        <h3>Sistema de Recomendación Inmobiliaria</h3>
        <p>Geolocalización inteligente para Santa Cruz de la Sierra</p>
        <br>
        <div style="display: flex; justify-content: center; gap: 1rem;">
            <div class="metric-box">
                <h4>🗺️ 76,853</h4>
                <p>Propiedades</p>
            </div>
            <div class="metric-box">
                <h4>🏛️ 4,777</h4>
                <p>Servicios Urbanos</p>
            </div>
            <div class="metric-box">
                <h4>🎯 Precisión</h4>
                <p>Distancias Reales</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    ### 🚀 ¿Qué hace a Citrino diferente?

    Nuestro sistema utiliza **geolocalización real** y la **fórmula de Haversine**
    para calcular distancias exactas entre propiedades y servicios urbanos.

    #### 🎯 Beneficios Clave:
    - **Recomendaciones precisas** basadas en distancia real a servicios
    - **Análisis de necesidades** (educación, salud, transporte, etc.)
    - **Optimización inteligente** para resultados en tiempo real
    - **Transparencia total** en el proceso de recomendación
    """)

    if st.button("🚀 Comenzar a Explorar", use_container_width=True):
        st.session_state.show_welcome = False
        st.rerun()

else:
    # Header principal
    st.markdown("""
    <div class="welcome-card">
        <h1>🏠 Citrino - Sistema de Recomendación Inmobiliaria</h1>
        <p>Inteligencia de mercado con geolocalización precisa</p>
    </div>
    """, unsafe_allow_html=True)

    # Botón para volver
    if st.button("🏠 Volver a Bienvenida", use_container_width=True):
        st.session_state.show_welcome = True
        st.rerun()

    # Estado del sistema
    st.subheader("📊 Estado del Sistema")
    try:
        health_response = requests.get(f"{API_URL}/api/health", timeout=3)
        if health_response.status_code == 200:
            health_data = health_response.json()
            st.success("✅ API Activa")
            st.write(f"Propiedades disponibles: {health_data.get('total_propiedades', 0):,}")
        else:
            st.error("❌ API No Responde")
    except:
        st.error("❌ Error de Conexión con API")

    # Perfiles simplificados
    st.subheader("👥 Perfiles de Prospectos")

    perfiles = {
        "familia_joven": {
            "nombre": "Familia Joven Profesional",
            "presupuesto_min": 120000,
            "presupuesto_max": 200000,
            "adultos": 2,
            "ninos": [1],
            "zona_preferida": "Equipetrol",
            "tipo_propiedad": "departamento",
            "necesidades": ["seguridad", "estacionamiento", "gimnasio"]
        },
        "inversor": {
            "nombre": "Inversor Inmobiliario",
            "presupuesto_min": 200000,
            "presupuesto_max": 400000,
            "adultos": 1,
            "ninos": [],
            "zona_preferida": "Equipetrol",
            "tipo_propiedad": "departamento",
            "necesidades": ["plusvalia", "rentabilidad", "seguridad"]
        },
        "joven_emprendedor": {
            "nombre": "Joven Emprendedor (Herencia)",
            "presupuesto_min": 300000,
            "presupuesto_max": 600000,
            "adultos": 1,
            "ninos": [],
            "zona_preferida": "Equipetrol",
            "tipo_propiedad": "departamento",
            "necesidades": ["seguridad", "inversion_segura", "plusvalia", "prestigio"]
        },
        "profesional_joven": {
            "nombre": "Profesional Joven",
            "presupuesto_min": 80000,
            "presupuesto_max": 150000,
            "adultos": 1,
            "ninos": [],
            "zona_preferida": "Zona Norte",
            "tipo_propiedad": "departamento",
            "necesidades": ["seguridad", "estacionamiento", "ubicacion_centrada"]
        }
    }

    # Selección de perfil
    perfil_seleccionado = st.selectbox(
        "Seleccionar Perfil:",
        list(perfiles.keys()),
        format_func=lambda x: perfiles[x]["nombre"]
    )

    if perfil_seleccionado:
        perfil = perfiles[perfil_seleccionado]
        st.markdown(f"""
        <div class="profile-box">
            <h4>{perfil['nombre']}</h4>
            <p><strong>Presupuesto:</strong> ${perfil['presupuesto_min']:,} - ${perfil['presupuesto_max']:,} USD</p>
            <p><strong>Zona:</strong> {perfil['zona_preferida']} | <strong>Tipo:</strong> {perfil['tipo_propiedad']}</p>
            <p><strong>Necesidades:</strong> {', '.join(perfil['necesidades'])}</p>
        </div>
        """, unsafe_allow_html=True)

    # Botón de recomendación simplificado
    if st.button("🎯 Generar Recomendaciones", type="primary", use_container_width=True):
        if perfil_seleccionado:
            with st.spinner("Generando recomendaciones..."):
                try:
                    api_perfil = {
                        "id": f"demo_{perfil_seleccionado}",
                        "presupuesto_min": perfil["presupuesto_min"],
                        "presupuesto_max": perfil["presupuesto_max"],
                        "adultos": perfil["adultos"],
                        "ninos": perfil["ninos"],
                        "adultos_mayores": 0,
                        "zona_preferida": perfil["zona_preferida"],
                        "tipo_propiedad": perfil["tipo_propiedad"],
                        "necesidades": perfil["necesidades"],
                        "limite": 3,
                        "umbral_minimo": 0.5
                    }

                    response = requests.post(f"{API_URL}/api/recomendar-mejorado", json=api_perfil, timeout=30)

                    if response.status_code == 200:
                        resultado = response.json()

                        if resultado.get('success'):
                            recomendaciones = resultado.get('recomendaciones', [])

                            if recomendaciones:
                                st.success(f"🎯 Se encontraron {len(recomendaciones)} recomendaciones")

                                for i, rec in enumerate(recomendaciones, 1):
                                    with st.expander(f"🏠 Opción {i}: {rec['nombre']} - ${rec['precio']:,} USD"):
                                        col1, col2 = st.columns(2)

                                        with col1:
                                            st.write(f"**Zona:** {rec['zona']}")
                                            st.write(f"**Superficie:** {rec['superficie_m2']} m²")
                                            st.write(f"**Habitaciones:** {rec['habitaciones']}")
                                            st.write(f"**Baños:** {rec['banos']}")

                                        with col2:
                                            st.write(f"**Compatibilidad:** {rec.get('compatibilidad', 0)}%")
                                            st.write(f"**Precio/m²:** ${rec['precio']/rec['superficie_m2']:,.0f}")

                                        st.write("**Justificación:**")
                                        st.write(rec['justificacion'])
                            else:
                                st.warning("⚠️ No se encontraron propiedades para este perfil")
                        else:
                            st.error(f"❌ Error: {resultado.get('error', 'Error desconocido')}")
                    else:
                        st.error(f"❌ Error HTTP: {response.status_code}")

                except requests.exceptions.ConnectionError:
                    st.error("❌ No se puede conectar al servidor API")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    # Información técnica simplificada
    with st.expander("🔬 Tecnología Utilizada"):
        st.markdown("""
        ### Algoritmo de Haversine

        Calcula distancias reales entre propiedades y servicios usando coordenadas geográficas.

        **Fórmula:** `a = sin²(Δφ/2) + cos(φ₁) × cos(φ₂) × sin²(Δλ/2)`

        ### Optimización por Zonas

        Pre-filtrado de propiedades por zona preferida para reducir tiempo de procesamiento.
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 8px;">
    <h3>🏠 Sistema de Recomendación Inmobiliaria Citrino</h3>
    <p>76,853 propiedades | 4,777 servicios urbanos | 323 proyectos de inteligencia</p>
</div>
""", unsafe_allow_html=True)