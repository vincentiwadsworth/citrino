#!/usr/bin/env python3
"""
DEBUG CRÍTICO DE COORDENADAS
Análisis profundo del problema de parsing de coordenadas en la guía urbana
"""

import pandas as pd
import re
import json

def extraer_muestras_reales():
    """Extrae muestras reales de coordenadas del Excel."""
    print("=== EXTRAYENDO MUESTRAS REALES DE COORDENADAS ===")

    df = pd.read_excel('data/raw/guia/GUIA URBANA.xlsx', header=4)  # Headers detectados en fila 4
    print(f"DataFrame shape: {df.shape}")
    print(f"Columnas: {list(df.columns)[:15]}...")

    coordenadas_muestras = []

    for idx, row in df.iterrows():
        # Buscar coordenadas en cada columna
        for col in df.columns:
            value = str(row[col])
            if re.search(r'-?\d+[.,]\d+[,\s]+-?\d+[.,]\d+', value):
                coordenadas_muestras.append({
                    'fila': idx,
                    'columna': col,
                    'valor_original': value
                })
                if len(coordenadas_muestras) >= 10:
                    break
        if len(coordenadas_muestras) >= 10:
            break

    print(f"\nMuestras de coordenadas encontradas: {len(coordenadas_muestras)}")
    for i, muestra in enumerate(coordenadas_muestras, 1):
        print(f"\nMuestra {i}:")
        print(f"  Fila: {muestra['fila']}, Columna: {muestra['columna']}")
        print(f"  Valor: {muestra['valor_original']}")

    return coordenadas_muestras

def testear_parser_actual(muestras):
    """Testea el parser actual con las muestras reales."""
    print("\n=== TESTEANDO PARSER ACTUAL ===")

    def parsear_coordenadas_actual(coordenadas_str):
        """Parser actual del ETL."""
        if not coordenadas_str or coordenadas_str == 'nan':
            return None

        try:
            coords_clean = coordenadas_str.strip()
            pattern = r'(-1[78]\.[\d,]+),\s*(-6[34]\.[\d,]+)'
            match = re.search(pattern, coords_clean)

            if match:
                lat_str, lng_str = match.groups()
                lat_str = lat_str.replace(',', '.')
                lng_str = lng_str.replace(',', '.')
                lat, lng = float(lat_str), float(lng_str)

                if -18.5 <= lat <= -17.5 and -64.0 <= lng <= -62.5:
                    return {'lat': lat, 'lng': lng}
                else:
                    return None
            else:
                return None
        except Exception as e:
            return None

    print("Test con parser actual:")
    for i, muestra in enumerate(muestras, 1):
        resultado = parsear_coordenadas_actual(muestra['valor_original'])
        print(f"  Muestra {i}: {resultado}")

    return parsear_coordenadas_actual

def testear_variaciones_regex(muestras):
    """Testea diferentes variaciones del regex."""
    print("\n=== TESTEANDO VARIACIONES DE REGEX ===")

    regex_variaciones = [
        # Variación 1: Más flexible con el formato
        r'(-?\d+[.,]\d+)[,\s]+(-?\d+[.,]\d+)',
        # Variación 2: Específico para Santa Cruz pero más flexible
        r'(-1[78][.,]\d+)[,\s]+(-6[34][.,]\d+)',
        # Variación 3: Sin restricciones de formato
        r'(-?\d+[.,]\d+)[,\s]+(-?\d+[.,]\d+)',
        # Variación 4: Captura más amplia
        r'(-?\d+[\d,\.]+)[,\s]+(-?\d+[\d,\.]+)',
    ]

    def parsear_con_regex(coordenadas_str, pattern):
        try:
            coords_clean = coordenadas_str.strip()
            match = re.search(pattern, coords_clean)

            if match:
                lat_str, lng_str = match.groups()
                lat_str = lat_str.replace(',', '.')
                lng_str = lng_str.replace(',', '.')
                lat, lng = float(lat_str), float(lng_str)

                # Validar rangos para Santa Cruz
                if -19.0 <= lat <= -16.0 and -65.0 <= lng <= -62.0:
                    return {'lat': lat, 'lng': lng, 'valido': True}
                else:
                    return {'lat': lat, 'lng': lng, 'valido': False}
            else:
                return None
        except Exception as e:
            return {'error': str(e)}

    for i, pattern in enumerate(regex_variaciones, 1):
        print(f"\nRegex {i}: {pattern}")
        exitos = 0
        for muestra in muestras:
            resultado = parsear_con_regex(muestra['valor_original'], pattern)
            if resultado and resultado.get('valido', False):
                exitos += 1
        print(f"  Éxitos: {exitos}/{len(muestras)}")

def analizar_rangos_validacion(muestras):
    """Analiza los rangos de validación."""
    print("\n=== ANÁLISIS DE RANGOS DE VALIDACIÓN ===")

    # Extraer todas las coordenadas sin filtrar por rangos
    todas_coordenadas = []
    pattern = r'(-?\d+[.,]\d+)[,\s]+(-?\d+[.,]\d+)'

    for muestra in muestras:
        match = re.search(pattern, muestra['valor_original'])
        if match:
            lat_str, lng_str = match.groups()
            lat_str = lat_str.replace(',', '.')
            lng_str = lng_str.replace(',', '.')
            try:
                lat, lng = float(lat_str), float(lng_str)
                todas_coordenadas.append({'lat': lat, 'lng': lng})
            except:
                pass

    print(f"Total coordenadas parseadas: {len(todas_coordenadas)}")

    if todas_coordenadas:
        lats = [c['lat'] for c in todas_coordenadas]
        lngs = [c['lng'] for c in todas_coordenadas]

        print(f"\nRangos encontrados:")
        print(f"  Latitud: {min(lats):.6f} a {max(lats):.6f}")
        print(f"  Longitud: {min(lngs):.6f} a {max(lngs):.6f}")

        print(f"\nCoordenadas individuales:")
        for i, coord in enumerate(todas_coordenadas[:5], 1):
            print(f"  {i}: lat={coord['lat']:.6f}, lng={coord['lng']:.6f}")

        # Probar diferentes rangos de validación
        rangos = [
            (-19.0, -16.0, -65.0, -62.0),  # Actual
            (-18.5, -17.5, -64.0, -62.5),  # Más restrictivo
            (-20.0, -15.0, -66.0, -60.0),  # Más amplio
        ]

        print(f"\nTest de rangos de validación:")
        for lat_min, lat_max, lng_min, lng_max in rangos:
            validas = sum(1 for c in todas_coordenadas
                         if lat_min <= c['lat'] <= lat_max and lng_min <= c['lng'] <= lng_max)
            print(f"  Rango [{lat_min}, {lat_max}] x [{lng_min}, {lng_max}]: {validas}/{len(todas_coordenadas)} válidas")

def main():
    """Función principal de debugging."""
    print("DEBUG CRÍTICO DE COORDENADAS - GUÍA URBANA")
    print("==========================================\n")

    # 1. Extraer muestras reales
    muestras = extraer_muestras_reales()

    if not muestras:
        print("ERROR: No se encontraron coordenadas en el Excel")
        return

    # 2. Testear parser actual
    parser_actual = testear_parser_actual(muestras)

    # 3. Testear variaciones de regex
    testear_variaciones_regex(muestras)

    # 4. Analizar rangos de validación
    analizar_rangos_validacion(muestras)

    print("\n=== ANÁLISIS COMPLETADO ===")
    print("Revisar los resultados para identificar el problema exacto")

if __name__ == "__main__":
    main()