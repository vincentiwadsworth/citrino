#!/usr/bin/env python3
"""
Test simple de API usando Flask y Docker wrapper para PostgreSQL
"""

from flask import Flask, jsonify, request
import sys
import os

# Agregar paths necesarios
sys.path.append('migration/config')
from database_config import create_connection

app = Flask(__name__)

# Variables de entorno para PostgreSQL
os.environ['USE_POSTGRES'] = 'true'

def get_propiedades_from_db(limit=10, zona=None):
    """Obtener propiedades de PostgreSQL usando Docker wrapper"""
    try:
        conn = create_connection()

        with conn.cursor() as cursor:
            if zona:
                cursor.execute("""
                    SELECT titulo, zona, precio_usd, num_dormitorios, num_banos,
                           coordenadas_validas, datos_completos
                    FROM propiedades
                    WHERE LOWER(zona) = LOWER(%s)
                    ORDER BY precio_usd ASC
                    LIMIT %s
                """, [zona, limit])
            else:
                cursor.execute("""
                    SELECT titulo, zona, precio_usd, num_dormitorios, num_banos,
                           coordenadas_validas, datos_completos
                    FROM propiedades
                    ORDER BY precio_usd ASC
                    LIMIT %s
                """, [limit])

            resultados = cursor.fetchall()
            conn.close()

            # Formatear resultados
            propiedades = []
            for row in resultados:
                propiedades.append({
                    'titulo': row[0],
                    'zona': row[1],
                    'precio_usd': float(row[2]) if row[2] else None,
                    'dormitorios': row[3],
                    'banos': row[4],
                    'coordenadas_validas': row[5],
                    'datos_completos': row[6]
                })

            return propiedades

    except Exception as e:
        print(f"Error obteniendo propiedades: {e}")
        return []

def get_stats_from_db():
    """Obtener estadísticas de PostgreSQL"""
    try:
        conn = create_connection()

        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE coordenadas_validas = true) as con_coordenadas,
                    COUNT(*) FILTER (WHERE datos_completos = true) as datos_completos,
                    MIN(precio_usd) as precio_min,
                    MAX(precio_usd) as precio_max,
                    AVG(precio_usd) as precio_avg
                FROM propiedades
            """)

            result = cursor.fetchone()
            conn.close()

            return {
                'total_propiedades': result[0],
                'con_coordenadas': result[1],
                'datos_completos': result[2],
                'precio_minimo': float(result[3]) if result[3] else None,
                'precio_maximo': float(result[4]) if result[4] else None,
                'precio_promedio': float(result[5]) if result[5] else None
            }

    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")
        return {}

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health endpoint"""
    stats = get_stats_from_db()

    if stats.get('total_propiedades', 0) > 0:
        return jsonify({
            'status': 'healthy',
            'datos_cargados': True,
            'total_propiedades': stats.get('total_propiedades', 0),
            'message': 'API funcionando con datos reales de PostgreSQL'
        })
    else:
        return jsonify({
            'status': 'degraded',
            'datos_cargados': False,
            'total_propiedades': 0,
            'message': 'API activa pero sin datos cargados'
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Endpoint de estadísticas"""
    stats = get_stats_from_db()

    if stats:
        return jsonify({
            'status': 'success',
            'data': stats
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'No se pudieron obtener estadísticas'
        }), 500

@app.route('/api/propiedades', methods=['GET'])
def get_propiedades():
    """Endpoint de propiedades"""
    limit = request.args.get('limit', 10, type=int)
    zona = request.args.get('zona', None)

    if limit > 50:
        limit = 50

    propiedades = get_propiedades_from_db(limit=limit, zona=zona)

    return jsonify({
        'status': 'success',
        'count': len(propiedades),
        'data': propiedades
    })

@app.route('/api/zones', methods=['GET'])
def get_zones():
    """Endpoint de zonas disponibles"""
    try:
        conn = create_connection()

        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT zona, COUNT(*) as cantidad
                FROM propiedades
                WHERE zona IS NOT NULL
                GROUP BY zona
                ORDER BY cantidad DESC
            """)

            resultados = cursor.fetchall()
            conn.close()

            zonas = [{'zona': row[0], 'cantidad': row[1]} for row in resultados]

            return jsonify({
                'status': 'success',
                'count': len(zonas),
                'data': zonas
            })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error obteniendo zonas: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("=== INICIANDO API TEST CON DOCKER WRAPPER ===")
    print("Health: http://localhost:5002/api/health")
    print("Stats: http://localhost:5002/api/stats")
    print("Propiedades: http://localhost:5002/api/propiedades")
    print("Zonas: http://localhost:5002/api/zones")

    app.run(host='0.0.0.0', port=5002, debug=False)