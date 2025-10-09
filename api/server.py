#!/usr/bin/env python3
"""
API Server para Citrino - Permite consultas desde Cherry Studio
"""

from flask import Flask, request, jsonify
import json
import sys
import os
from flask_cors import CORS

# Agregar los directorios src y scripts al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from recommendation_engine import RecommendationEngine
from recommendation_engine_mejorado import RecommendationEngineMejorado
from property_catalog import SistemaConsultaCitrino

app = Flask(__name__)

# Configuración de CORS para producción
ALLOWED_ORIGINS = [
    'http://localhost:8080',
    'http://127.0.0.1:8080',
    'http://localhost:5500',  # Live Server
    'https://*.github.io',     # GitHub Pages
]

# En producción, añadir origen específico de GitHub Pages
if os.getenv('GITHUB_PAGES_URL'):
    ALLOWED_ORIGINS.append(os.getenv('GITHUB_PAGES_URL'))

CORS(app, resources={r"/api/*": {"origins": "*"}})  # Permitir todos los orígenes para /api/*

# Inicializar sistemas
sistema_consulta = SistemaConsultaCitrino()
motor_recomendacion = RecommendationEngine()
motor_mejorado = RecommendationEngineMejorado()

# Variable global para estado de carga
DATOS_CARGADOS = False

def inicializar_datos():
    """Carga datos una sola vez al iniciar el servidor"""
    global DATOS_CARGADOS
    
    print("=" * 60)
    print("INICIANDO CITRINO API")
    print("=" * 60)
    
    # Intentar cargar base de datos de relevamiento
    try:
        # Usar ruta relativa al directorio del script
        ruta = os.path.join(os.path.dirname(__file__), '..', 'data', 'base_datos_relevamiento.json')
        print(f"Cargando datos desde: {ruta}")
        
        with open(ruta, 'r', encoding='utf-8') as f:
            data = json.load(f)
            propiedades_relevamiento = data.get('propiedades', [])
            print(f"✅ Cargadas {len(propiedades_relevamiento)} propiedades de relevamiento")

            # Cargar en ambos motores
            motor_recomendacion.cargar_propiedades(propiedades_relevamiento)
            motor_mejorado.cargar_propiedades(propiedades_relevamiento)

            # También cargar en el sistema de consulta para compatibilidad
            sistema_consulta.propiedades = propiedades_relevamiento
            sistema_consulta.estadisticas_globales['total_propiedades'] = len(propiedades_relevamiento)
            
            DATOS_CARGADOS = True
            print("=" * 60)
            print("✅ CITRINO API LISTA")
            print("=" * 60)
            return True
            
    except FileNotFoundError as e:
        print(f"❌ Error: No se encontró data/base_datos_relevamiento.json")
        print(f"   Ruta buscada: {e}")
        print("   Ejecute: python scripts/build_relevamiento_dataset.py")
        return False
        
    except Exception as e:
        print(f"❌ Error cargando base de datos de relevamiento: {e}")
        import traceback
        traceback.print_exc()
        return False

# Cargar datos al iniciar (una sola vez)
print("Iniciando carga de datos...")
inicializar_datos()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verifica que el API está funcionando"""
    status = 'ok' if DATOS_CARGADOS else 'degraded'
    total_props = len(sistema_consulta.propiedades) if DATOS_CARGADOS else 0
    
    return jsonify({
        'status': status,
        'message': 'API Citrino funcionando' if DATOS_CARGADOS else 'API activa pero sin datos cargados',
        'total_propiedades': total_props,
        'datos_cargados': DATOS_CARGADOS,
        'version': '1.0.0',
        'endpoints': [
            '/api/health',
            '/api/buscar',
            '/api/recomendar',
            '/api/recomendar-mejorado',
            '/api/estadisticas',
            '/api/zonas',
            '/api/chat/process'
        ]
    })

@app.route('/api/buscar', methods=['POST'])
def buscar_propiedades():
    """Busca propiedades según filtros incluyendo UV/Manzana"""
    try:
        data = request.get_json()

        # Aplicar filtros con soporte UV/Manzana
        filtros = {}

        if 'zona' in data:
            filtros['zona'] = data['zona']

        if 'precio_min' in data and data['precio_min']:
            filtros['precio_min'] = float(data['precio_min'])

        if 'precio_max' in data and data['precio_max']:
            filtros['precio_max'] = float(data['precio_max'])

        if 'tipo_propiedad' in data:
            filtros['tipo_propiedad'] = data['tipo_propiedad']

        # Nuevos filtros UV/Manzana
        if 'unidad_vecinal' in data:
            filtros['unidad_vecinal'] = data['unidad_vecinal']

        if 'manzana' in data:
            filtros['manzana'] = data['manzana']

        # Usar el motor mejorado para búsquedas avanzadas
        resultados = motor_mejorado.buscar_por_filtros(filtros)

        # Limitar resultados
        limite = data.get('limite', 20)
        resultados = resultados[:limite]

        # Formatear resultados para inversores
        propiedades_formateadas = []
        for prop in resultados:
            # Adaptar formato para datos de relevamiento
            caract = prop.get('caracteristicas_principales', {})
            ubicacion = prop.get('ubicacion', {})

            # Para datos de relevamiento, usar campos directos
            if not caract:
                caract = {
                    'precio': prop.get('precio', 0),
                    'superficie_m2': prop.get('superficie', 0),
                    'habitaciones': prop.get('habitaciones', 0),
                    'banos_completos': prop.get('banos', 0)
                }

            if not ubicacion:
                ubicacion = {
                    'zona': prop.get('zona', ''),
                    'direccion': prop.get('direccion', ''),
                    'coordenadas': {
                        'lat': prop.get('latitud'),
                        'lng': prop.get('longitud')
                    } if prop.get('latitud') and prop.get('longitud') else {}
                }

            prop_formateada = {
                'id': prop.get('id', ''),
                'nombre': prop.get('tipo_propiedad', f"Propiedad en {prop.get('zona', 'Zona')}"),
                'precio': caract.get('precio', 0),
                'superficie_m2': caract.get('superficie_m2', 0),
                'habitaciones': caract.get('habitaciones', 0),
                'banos': caract.get('banos_completos', 0),
                'zona': ubicacion.get('zona', ''),
                'direccion': ubicacion.get('direccion', ''),
                'unidad_vecinal': prop.get('unidad_vecinal', ''),
                'manzana': prop.get('manzana', ''),
                'fecha_relevamiento': prop.get('fecha_relevamiento', ''),
                'fuente': prop.get('fuente', ''),
                'descripcion': prop.get('descripcion', '')[:300] + '...' if len(prop.get('descripcion', '')) > 300 else prop.get('descripcion', ''),
                'coordenadas': ubicacion.get('coordenadas', {})
            }
            propiedades_formateadas.append(prop_formateada)

        return jsonify({
            'success': True,
            'total_resultados': len(resultados),
            'propiedades': propiedades_formateadas,
            'fuente_datos': 'relevamiento'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/recomendar', methods=['POST'])
def recomendar_propiedades():
    """Genera recomendaciones basadas en perfil"""
    try:
        data = request.get_json()

        # Formatear perfil para el motor
        perfil = {
            'id': data.get('id', 'perfil_cherry'),
            'presupuesto': {
                'min': data.get('presupuesto_min', 0),
                'max': data.get('presupuesto_max', 1000000)
            },
            'composicion_familiar': {
                'adultos': data.get('adultos', 1),
                'ninos': data.get('ninos', []),
                'adultos_mayores': data.get('adultos_mayores', 0)
            },
            'preferencias': {
                'ubicacion': data.get('zona_preferida', ''),
                'tipo_propiedad': data.get('tipo_propiedad', '')
            },
            'necesidades': data.get('necesidades', [])
        }

        # Generar recomendaciones con motor original (rendimiento optimizado)
        recomendaciones = motor_recomendacion.generar_recomendaciones(
            perfil,
            limite=data.get('limite', 10),
            umbral_minimo=data.get('umbral_minimo', 0.3)
        )

        # Formatear resultados
        resultados_formateados = []
        for rec in recomendaciones:
            prop = rec['propiedad']
            caract = prop.get('caracteristicas_principales', {})
            ubicacion = prop.get('ubicacion', {})

            resultado = {
                'id': prop.get('id', ''),
                'nombre': prop.get('nombre', ''),
                'precio': caract.get('precio', 0),
                'superficie_m2': caract.get('superficie_m2', 0),
                'habitaciones': caract.get('habitaciones', 0),
                'banos': caract.get('banos_completos', 0),
                'zona': ubicacion.get('zona', ''),
                'compatibilidad': round(rec['compatibilidad'] * 100, 1),
                'justificacion': rec.get('justificacion', ''),
                'fuente': prop.get('fuente', '')
            }
            resultados_formateados.append(resultado)

        # Generar briefing personalizado
        briefing = generar_briefing_personalizado(data, resultados_formateados)

        return jsonify({
            'success': True,
            'total_recomendaciones': len(resultados_formateados),
            'recomendaciones': resultados_formateados,
            'briefing_personalizado': briefing
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/estadisticas', methods=['GET'])
def obtener_estadisticas():
    """Obtiene estadísticas generales de propiedades de relevamiento"""
    try:
        propiedades = sistema_consulta.propiedades

        if not propiedades:
            return jsonify({
                'success': True,
                'estadisticas': {
                    'total_propiedades': 0,
                    'mensaje': 'No hay propiedades cargadas'
                }
            })

        # Calcular estadísticas básicas
        precios = []
        superficies = []
        zonas = set()
        tipos = set()

        for prop in propiedades:
            # Extraer precio
            precio = prop.get('precio') or prop.get('caracteristicas_principales', {}).get('precio', 0)
            if precio and precio > 0:
                precios.append(precio)

            # Extraer superficie
            superficie = prop.get('superficie') or prop.get('caracteristicas_principales', {}).get('superficie_m2', 0)
            if superficie and superficie > 0:
                superficies.append(superficie)

            # Extraer zona
            zona = prop.get('zona') or prop.get('ubicacion', {}).get('zona', '')
            if zona:
                zonas.add(zona)

            # Extraer tipo
            tipo = prop.get('tipo_propiedad', '')
            if tipo:
                tipos.add(tipo)

        # Calcular estadísticas
        stats = {
            'total_propiedades': len(propiedades),
            'fuente_datos': 'relevamiento',
            'precio_promedio': sum(precios) / len(precios) if precios else 0,
            'precio_minimo': min(precios) if precios else 0,
            'precio_maximo': max(precios) if precios else 0,
            'superficie_promedio': sum(superficies) / len(superficies) if superficies else 0,
            'total_zonas': len(zonas),
            'total_tipos': len(tipos)
        }

        # Agregar distribución por zonas (top 10)
        distribucion_zonas = {}
        for zona in sorted(zonas)[:10]:
            count = sum(1 for prop in propiedades
                       if (prop.get('zona') or prop.get('ubicacion', {}).get('zona', '')) == zona)
            distribucion_zonas[zona] = count

        stats['distribucion_zonas'] = distribucion_zonas

        # Agregar distribución por precios
        distribucion_precios = {
            '0-50k': 0,
            '50k-100k': 0,
            '100k-150k': 0,
            '150k-200k': 0,
            '200k-300k': 0,
            '300k+': 0
        }

        for precio in precios:
            if precio < 50000:
                distribucion_precios['0-50k'] += 1
            elif precio < 100000:
                distribucion_precios['50k-100k'] += 1
            elif precio < 150000:
                distribucion_precios['100k-150k'] += 1
            elif precio < 200000:
                distribucion_precios['150k-200k'] += 1
            elif precio < 300000:
                distribucion_precios['200k-300k'] += 1
            else:
                distribucion_precios['300k+'] += 1

        stats['distribucion_precios'] = distribucion_precios

        return jsonify({
            'success': True,
            'estadisticas': stats
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/zonas', methods=['GET'])
def obtener_zonas():
    """Obtiene lista de todas las zonas disponibles de relevamiento"""
    try:
        propiedades = sistema_consulta.propiedades

        if not propiedades:
            return jsonify({
                'success': True,
                'zonas': [],
                'mensaje': 'No hay propiedades cargadas'
            })

        # Extraer zonas únicas de las propiedades
        zonas = set()
        for prop in propiedades:
            zona = prop.get('zona') or prop.get('ubicacion', {}).get('zona', '')
            if zona:
                zonas.add(zona)

        return jsonify({
            'success': True,
            'zonas': sorted(zonas),
            'total_zonas': len(zonas)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/recomendar-mejorado', methods=['POST'])
def recomendar_propiedades_mejorado():
    """Genera recomendaciones para inversores con filtros UV/Manzana"""
    try:
        data = request.get_json()

        # Formatear perfil para inversores
        perfil = {
            'id': data.get('id', 'perfil_inversor'),
            'presupuesto': {
                'min': data.get('presupuesto_min', 0),
                'max': data.get('presupuesto_max', 1000000)
            },
            'preferencias': {
                'ubicacion': data.get('zona_preferida', ''),
                'tipo_propiedad': data.get('tipo_propiedad', ''),
                'unidad_vecinal': data.get('unidad_vecinal', ''),
                'manzana': data.get('manzana', ''),
                'disponibilidad_dias': data.get('disponibilidad_dias', 90)
            },
            'necesidades': data.get('necesidades', [])
        }

        # Generar recomendaciones con motor especializado para inversores
        recomendaciones = motor_mejorado.generar_recomendaciones(
            perfil,
            limite=data.get('limite', 5),
            umbral_minimo=data.get('umbral_minimo', 0.3)
        )

        # Formatear resultados para inversores
        resultados_formateados = []
        for rec in recomendaciones:
            prop = rec['propiedad']

            # Adaptar formato para datos de relevamiento
            caract = prop.get('caracteristicas_principales', {})
            if not caract:
                caract = {
                    'precio': prop.get('precio', 0),
                    'superficie_m2': prop.get('superficie', 0),
                    'habitaciones': prop.get('habitaciones', 0),
                    'banos_completos': prop.get('banos', 0)
                }

            ubicacion = prop.get('ubicacion', {})
            if not ubicacion:
                ubicacion = {
                    'zona': prop.get('zona', ''),
                    'direccion': prop.get('direccion', '')
                }

            resultado = {
                'id': prop.get('id', ''),
                'nombre': prop.get('tipo_propiedad', f"Inversión en {prop.get('zona', 'Zona')}"),
                'precio': caract.get('precio', 0),
                'superficie_m2': caract.get('superficie_m2', 0),
                'habitaciones': caract.get('habitaciones', 0),
                'banos': caract.get('banos_completos', 0),
                'zona': ubicacion.get('zona', ''),
                'unidad_vecinal': prop.get('unidad_vecinal', ''),
                'manzana': prop.get('manzana', ''),
                'fecha_relevamiento': prop.get('fecha_relevamiento', ''),
                'compatibilidad': round(rec['compatibilidad'], 1),
                'justificacion': rec.get('justificacion', ''),
                'servicios_cercanos': rec.get('servicios_cercanos', ''),
                'fuente': prop.get('fuente', ''),
                'coordenadas': ubicacion.get('coordenadas', {})
            }
            resultados_formateados.append(resultado)

        return jsonify({
            'success': True,
            'total_recomendaciones': len(resultados_formateados),
            'recomendaciones': resultados_formateados,
            'motor': 'especializado_inversores',
            'fuente_datos': 'relevamiento'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

def generar_briefing_personalizado(datos_prospecto, recomendaciones):
    """Genera un briefing personalizado para compartir con el prospecto"""

    # Formatear información del prospecto
    presupuesto_min = datos_prospecto.get('presupuesto_min', 0)
    presupuesto_max = datos_prospecto.get('presupuesto_max', 0)
    adultos = datos_prospecto.get('adultos', 0)
    ninos = datos_prospecto.get('ninos', [])
    zona_preferida = datos_prospecto.get('zona_preferida', 'No especificada')

    # Crear briefing estructurado
    briefing = f"""ESTIMADO CLIENTE,

Gracias por su interés en nuestras propiedades. Basado en sus necesidades específicas, hemos preparado las siguientes recomendaciones personalizadas:

RESUMEN DE SU BÚSQUEDA:
• Presupuesto: ${presupuesto_min:,} - ${presupuesto_max:,} USD
• Composición: {adultos} adultos" + (f", {len(ninos)} niños" if ninos else "") + "
• Zona de preferencia: {zona_preferida}
• Total de opciones ideales encontradas: {len(recomendaciones)}

RECOMENDACIONES PRINCIPALES:
"""

    # Agregar cada recomendación
    for i, rec in enumerate(recomendaciones, 1):
        briefing += f"""
{i}. {rec['nombre']}
   • Precio: ${rec['precio']:,} USD
   • Ubicación: {rec['zona']}
   • Características: {rec['habitaciones']} habitaciones, {rec['banos']} baños, {rec['superficie_m2']} m²
   • Compatibilidad con sus necesidades: {rec['compatibilidad']}%
   • Justificación: {rec['justificacion']}
"""

    # Agregar información adicional
    briefing += f"""

PRÓXIMOS PASOS:
1. Podemos coordinar visitas a las propiedades de su interés
2. Ofrecemos asesoría legal y financiera completa
3. Contamos con herramientas exclusivas de negociación

CONTACTO:
Para más información o coordinar visitas, por favor contacte a su asesor comercial de Citrino.

---
Este briefing fue generado automáticamente por el sistema inteligente de Citrino
Basado en análisis de 76,853 propiedades en Santa Cruz de la Sierra
"""

    return briefing

@app.route('/api/chat/process', methods=['POST'])
def process_chat_message():
    """Procesa mensaje de chat con z.ai y genera recomendaciones si es posible"""
    try:
        data = request.get_json()
        mensaje = data.get('mensaje', '')

        if not mensaje:
            return jsonify({
                'success': False,
                'error': 'Mensaje vacío'
            }), 400

        # Intentar usar LLM si está configurado
        perfil_extraido = None
        respuesta_llm = None
        recomendaciones = []

        try:
            from llm_integration import LLMIntegration, LLMConfig

            # Inicializar LLM con z.ai
            llm_config = LLMConfig(
                provider=os.getenv('LLM_PROVIDER', 'zai'),
                api_key=os.getenv('ZAI_API_KEY'),
                model=os.getenv('LLM_MODEL', 'glm-4.5-air')
            )

            llm = LLMIntegration(llm_config)

            # Validar configuración
            if llm.validar_configuracion():
                # Parsear perfil desde el mensaje
                perfil_extraido = llm.parsear_perfil_desde_texto(mensaje)

                # Generar recomendaciones si se extrajo un perfil válido
                if perfil_extraido and perfil_extraido.get('presupuesto', {}).get('max'):
                    # Adaptar perfil para el motor de recomendaciones
                    perfil_motor = {
                        'id': 'chat_profile',
                        'presupuesto': perfil_extraido.get('presupuesto', {}),
                        'composicion_familiar': perfil_extraido.get('composicion_familiar', {}),
                        'preferencias': perfil_extraido.get('preferencias', {}),
                        'necesidades': perfil_extraido.get('necesidades', [])
                    }

                    # Generar recomendaciones con motor mejorado
                    resultados = motor_mejorado.generar_recomendaciones(
                        perfil_motor,
                        limite=6,
                        umbral_minimo=0.3
                    )

                    # Formatear recomendaciones
                    for rec in resultados:
                        prop = rec['propiedad']
                        caract = prop.get('caracteristicas_principales', {})
                        if not caract:
                            caract = {
                                'precio': prop.get('precio', 0),
                                'superficie_m2': prop.get('superficie', 0),
                                'habitaciones': prop.get('habitaciones', 0),
                                'banos_completos': prop.get('banos', 0)
                            }

                        ubicacion = prop.get('ubicacion', {})
                        if not ubicacion:
                            ubicacion = {
                                'zona': prop.get('zona', ''),
                                'direccion': prop.get('direccion', '')
                            }

                        recomendaciones.append({
                            'id': prop.get('id', ''),
                            'nombre': prop.get('tipo_propiedad', f"Propiedad en {prop.get('zona', 'Zona')}"),
                            'precio': caract.get('precio', 0),
                            'superficie_m2': caract.get('superficie_m2', 0),
                            'habitaciones': caract.get('habitaciones', 0),
                            'banos': caract.get('banos_completos', 0),
                            'zona': ubicacion.get('zona', ''),
                            'compatibilidad': round(rec['compatibilidad'], 1),
                            'justificacion': rec.get('justificacion', ''),
                            'servicios_cercanos': rec.get('servicios_cercanos', '')
                        })

                    respuesta_llm = f"He analizado tu solicitud y encontré {len(recomendaciones)} propiedades que coinciden con tu perfil."
                else:
                    respuesta_llm = "He entendido tu mensaje. ¿Podrías darme más detalles sobre tu presupuesto y preferencias?"

            else:
                # LLM no configurado, usar análisis básico
                perfil_extraido = extraer_perfil_basico(mensaje)
                respuesta_llm = "Procesé tu mensaje con análisis básico. Para mejores resultados, configura la integración con Z.AI."

        except ImportError:
            # Módulo LLM no disponible
            perfil_extraido = extraer_perfil_basico(mensaje)
            respuesta_llm = "Sistema básico activo. Configura Z.AI para análisis avanzado."

        except Exception as e:
            # Error en procesamiento LLM, usar fallback
            print(f"Error procesando con LLM: {e}")
            perfil_extraido = extraer_perfil_basico(mensaje)
            respuesta_llm = "Hubo un problema con el análisis avanzado. Procesé tu mensaje con el sistema básico."

        return jsonify({
            'success': True,
            'perfil': perfil_extraido,
            'recomendaciones': recomendaciones,
            'respuesta': respuesta_llm,
            'llm_usado': bool(os.getenv('ZAI_API_KEY'))
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

def extraer_perfil_basico(mensaje):
    """Extrae información básica del mensaje usando reglas simples"""
    import re

    mensaje_lower = mensaje.lower()

    # Extraer presupuesto
    presupuesto_min = None
    presupuesto_max = None

    # Buscar números en el mensaje
    numeros = re.findall(r'\b(\d+(?:,\d+)?)\s*(?:k|mil|usd|dolares)?', mensaje_lower)
    if numeros:
        valores = [float(n.replace(',', '')) for n in numeros]
        # Convertir a valores completos si son pequeños
        valores = [v * 1000 if v < 1000 else v for v in valores]

        if len(valores) >= 1:
            presupuesto_min = min(valores) * 0.8
            presupuesto_max = max(valores) * 1.2

    # Extraer zona
    zonas = ['equipetrol', 'santa mónica', 'urbari', 'los olivos', 'zona norte', 'zona sur', 'centro']
    zona_preferida = None
    for zona in zonas:
        if zona in mensaje_lower:
            zona_preferida = zona.title()
            break

    # Extraer tipo de propiedad
    tipo_propiedad = None
    if 'departamento' in mensaje_lower or 'apartamento' in mensaje_lower:
        tipo_propiedad = 'departamento'
    elif 'casa' in mensaje_lower:
        tipo_propiedad = 'casa'
    elif 'penthouse' in mensaje_lower:
        tipo_propiedad = 'penthouse'

    return {
        'composicion_familiar': {
            'adultos': 2,
            'ninos': [],
            'adultos_mayores': 0
        },
        'presupuesto': {
            'min': presupuesto_min,
            'max': presupuesto_max,
            'tipo': 'compra'
        },
        'preferencias': {
            'ubicacion': zona_preferida,
            'tipo_propiedad': tipo_propiedad
        },
        'necesidades': []
    }

if __name__ == '__main__':
    # Configuración para desarrollo vs producción
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    
    print("Iniciando API Citrino...")
    print(f"Endpoint: http://localhost:{port}")
    print(f"Documentación: http://localhost:{port}/api/health")
    print(f"Entorno: {'Producción' if not debug else 'Desarrollo'}")

    app.run(debug=debug, host='0.0.0.0', port=port)