#!/usr/bin/env python3
"""
Verifica el dataset ampliado con campos determinantes.
"""

import json

def main():
    print("=== Verificación del Dataset Ampliado ===")

    # Cargar dataset
    with open('data/propiedades_mejorado.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Total de propiedades: {len(data)}")
    print()

    # Verificar campos determinantes
    print("=== Campos determinantes presentes ===")
    campos_determinantes = [
        'caracteristicas_principales.precio',
        'caracteristicas_principales.superficie_m2',
        'caracteristicas_principales.habitaciones',
        'caracteristicas_principales.dormitorios',
        'caracteristicas_principales.banos_completos',
        'caracteristicas_principales.banos_medios',
        'caracteristicas_principales.cochera_garaje',
        'caracteristicas_principales.numero_espacios_garaje',
        'detalles_construccion.estado_conservacion',
        'detalles_construccion.antiguedad_anios',
        'condominio.es_condominio_cerrado',
        'condominio.seguridad_24h',
        'condominio.amenidades',
        'ubicacion.zona',
        'ubicacion.barrio',
        'valorizacion_sector.nivel_socioeconomico',
        'valorizacion_sector.seguridad_zona',
        'valorizacion_sector.plusvalia_tendencia'
    ]

    # Contar propiedades que tienen cada campo
    for campo in campos_determinantes:
        partes = campo.split('.')
        count = 0
        for prop in data:
            valor = prop
            try:
                for parte in partes:
                    valor = valor.get(parte, {})
                if valor is not None and valor != {}:
                    count += 1
            except:
                pass
        print(f"{campo}: {count}/{len(data)} propiedades ({count/len(data)*100:.1f}%)")

    print()
    print("=== Ejemplos de propiedades con campos determinantes ===")

    for i, prop in enumerate(data[:3], 1):
        caract = prop.get('caracteristicas_principales', {})
        detalles = prop.get('detalles_construccion', {})
        condominio = prop.get('condominio', {})
        ubicacion = prop.get('ubicacion', {})

        print(f"{i}. {prop['nombre']}")
        print(f"   Precio: ${caract.get('precio', 0):,.0f}")
        print(f"   Superficie: {caract.get('superficie_m2', 0)}m²")
        print(f"   Habitaciones: {caract.get('habitaciones', 0)}")
        print(f"   Baños completos: {caract.get('banos_completos', 0)}")
        print(f"   Baños medios: {caract.get('banos_medios', 0)}")
        print(f"   Garaje: {'Sí' if caract.get('cochera_garaje') else 'No'}")
        print(f"   Espacios garaje: {caract.get('numero_espacios_garaje', 0)}")
        print(f"   Zona: {ubicacion.get('zona', 'N/A')}")
        print(f"   Condominio cerrado: {'Sí' if condominio.get('es_condominio_cerrado') else 'No'}")
        if condominio.get('amenidades'):
            print(f"   Amenidades: {', '.join(condominio['amenidades'])}")
        print(f"   Estado: {detalles.get('estado_conservacion', 'N/A')}")
        print()

if __name__ == "__main__":
    main()