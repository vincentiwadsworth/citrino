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
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from recommendation_engine import RecommendationEngine
from recommendation_engine_mejorado import RecommendationEngineMejorado
from sistema_consulta import SistemaConsultaCitrino

app = Flask(__name__)
CORS(app)  # Permite peticiones desde otros dominios

# Inicializar sistemas
sistema_consulta = SistemaConsultaCitrino()
motor_recomendacion = RecommendationEngine()
motor_mejorado = RecommendationEngineMejorado()

# Cargar base de datos al iniciar
@app.before_request
def cargar_datos():
    if not hasattr(app, 'datos_cargados'):
        print("Cargando base de datos...")
        sistema_consulta.cargar_base_datos("data/bd_final/propiedades_limpias.json")
        motor_recomendacion.cargar_propiedades(sistema_consulta.propiedades)

        # Cargar datos para el motor mejorado
        print("Cargando guía urbana municipal...")
        try:
            motor_mejorado.cargar_propiedades(sistema_consulta.propiedades)
            motor_mejorado.cargar_guias_urbanas("data/guia_urbana_municipal_completa.json")
            print("Guía urbana cargada exitosamente")
        except Exception as e:
            print(f"Advertencia: No se pudo cargar guía urbana: {e}")

        app.datos_cargados = True
        print("Base de datos cargada exitosamente")

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verifica que el API está funcionando"""
    return jsonify({
        'status': 'ok',
        'message': 'API Citrino funcionando',
        'total_propiedades': len(sistema_consulta.propiedades)
    })

@app.route('/api/buscar', methods=['POST'])
def buscar_propiedades():
    """Busca propiedades según filtros"""
    try:
        data = request.get_json()

        # Aplicar filtros
        filtros = {}

        if 'zona' in data:
            filtros['zona'] = data['zona']

        if 'precio_min' in data and data['precio_min']:
            filtros['precio_min'] = float(data['precio_min'])

        if 'precio_max' in data and data['precio_max']:
            filtros['precio_max'] = float(data['precio_max'])

        if 'superficie_min' in data and data['superficie_min']:
            filtros['superficie_min'] = float(data['superficie_min'])

        if 'superficie_max' in data and data['superficie_max']:
            filtros['superficie_max'] = float(data['superficie_max'])

        if 'habitaciones_min' in data and data['habitaciones_min']:
            filtros['habitaciones_min'] = int(data['habitaciones_min'])

        if 'banos_min' in data and data['banos_min']:
            filtros['banos_min'] = int(data['banos_min'])

        if 'tiene_garaje' in data:
            filtros['tiene_garaje'] = bool(data['tiene_garaje'])

        # Realizar búsqueda
        resultados = sistema_consulta.buscar_por_filtros(filtros)

        # Limitar resultados
        limite = data.get('limite', 20)
        resultados = resultados[:limite]

        # Formatear resultados
        propiedades_formateadas = []
        for prop in resultados:
            caract = prop.get('caracteristicas_principales', {})
            ubicacion = prop.get('ubicacion', {})

            prop_formateada = {
                'id': prop.get('id', ''),
                'nombre': prop.get('nombre', ''),
                'precio': caract.get('precio', 0),
                'superficie_m2': caract.get('superficie_m2', 0),
                'habitaciones': caract.get('habitaciones', 0),
                'banos': caract.get('banos_completos', 0),
                'garaje': caract.get('cochera_garaje', False),
                'espacios_garaje': caract.get('numero_espacios_garaje', 0),
                'zona': ubicacion.get('zona', ''),
                'direccion': ubicacion.get('direccion', ''),
                'fuente': prop.get('fuente', ''),
                'descripcion': prop.get('descripcion', '')[:300] + '...' if len(prop.get('descripcion', '')) > 300 else prop.get('descripcion', '')
            }
            propiedades_formateadas.append(prop_formateada)

        return jsonify({
            'success': True,
            'total_resultados': len(resultados),
            'propiedades': propiedades_formateadas
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
    """Obtiene estadísticas generales"""
    try:
        stats = {
            'total_propiedades': sistema_consulta.estadisticas_globales['total_propiedades'],
            'precio_promedio': sistema_consulta.estadisticas_globales['precio_promedio'],
            'precio_minimo': sistema_consulta.estadisticas_globales['precio_minimo'],
            'precio_maximo': sistema_consulta.estadisticas_globales['precio_maximo'],
            'superficie_promedio': sistema_consulta.estadisticas_globales['superficie_promedio'],
            'total_zonas': sistema_consulta.estadisticas_globales['total_zonas'],
            'distribucion_zonas': {},
            'distribucion_precios': {}
        }

        # Agregar distribución por zonas
        for zona, props in list(sistema_consulta.indices['zona'].items())[:10]:
            stats['distribucion_zonas'][zona] = len(props)

        # Agregar distribución por precios
        for rango, props in sistema_consulta.indices['precio'].items():
            stats['distribucion_precios'][rango] = len(props)

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
    """Obtiene lista de todas las zonas disponibles"""
    try:
        zonas = list(sistema_consulta.indices['zona'].keys())
        return jsonify({
            'success': True,
            'zonas': sorted(zonas)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/recomendar-mejorado', methods=['POST'])
def recomendar_propiedades_mejorado():
    """Genera recomendaciones con motor mejorado (georreferenciación real)"""
    try:
        data = request.get_json()

        # Formatear perfil para el motor
        perfil = {
            'id': data.get('id', 'perfil_mejorado'),
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

        # Generar recomendaciones con motor mejorado
        recomendaciones = motor_mejorado.generar_recomendaciones(
            perfil,
            limite=data.get('limite', 5),
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
                'compatibilidad': round(rec['compatibilidad'], 1),
                'justificacion': rec.get('justificacion', ''),
                'fuente': prop.get('fuente', '')
            }
            resultados_formateados.append(resultado)

        return jsonify({
            'success': True,
            'total_recomendaciones': len(resultados_formateados),
            'recomendaciones': resultados_formateados,
            'motor': 'mejorado_con_georreferenciacion'
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

if __name__ == '__main__':
    print("Iniciando API Citrino...")
    print("Endpoint: http://localhost:5000")
    print("Documentación: http://localhost:5000/api/health")

    app.run(debug=True, host='0.0.0.0', port=5000)