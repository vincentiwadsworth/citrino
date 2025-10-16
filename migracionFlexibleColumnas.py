#!/usr/bin/env python3
"""
MIGRACIÓN FLEXIBLE DE EXCEL RAW → POSTGRESQL
Procesa TODOS los archivos con mapeo inteligente de columnas
"""

import os
import pandas as pd
import psycopg2
from pathlib import Path
import re
import json
from collections import defaultdict

def detectar_columna(df, posibles_nombres):
    """Detecta automáticamente qué columna usar basado en nombres posibles"""
    for posible in posibles_nombres:
        for col in df.columns:
            if str(col).strip().lower() == posible.lower():
                return col
    return None

def procesar_archivo_excel_flexible(archivo, cursor, urls_procesadas):
    """Procesa un archivo Excel con mapeo flexible de columnas"""
    print(f"\n=== PROCESANDO: {archivo.name} ===")

    try:
        df = pd.read_excel(str(archivo))
        print(f"Filas leídas: {len(df)}")
        print(f"Columnas encontradas: {list(df.columns)}")

        # Mapeo flexible de columnas
        mapping_columnas = {}

        # Detectar URL
        posibles_urls = ['url', 'URL', 'Link', 'link', 'link de la publicación', 'enlace']
        mapping_columnas['url'] = detectar_columna(df, posibles_urls)

        # Detectar Título
        posibles_titulos = ['título', 'titulo', 'Título', 'Titulo', 'title', 'property']
        mapping_columnas['titulo'] = detectar_columna(df, posibles_titulos)

        # Detectar Precio
        posibles_precios = ['precio', 'Precio', 'price', 'usd', '$']
        mapping_columnas['precio'] = detectar_columna(df, posibles_precios)

        # Detectar Descripción
        posibles_descripciones = ['descripción', 'descripcion', 'Descripción', 'Descripcion',
                                'details', 'detalle', 'información', 'informacion']
        mapping_columnas['descripcion'] = detectar_columna(df, posibles_descripciones)

        # Detectar Coordenadas
        posibles_lat = ['latitud', 'lat', 'latitude', 'Latitud', 'Lat']
        posibles_lon = ['longitud', 'lon', 'longitude', 'Longitud', 'Lng']
        mapping_columnas['latitud'] = detectar_columna(df, posibles_lat)
        mapping_columnas['longitud'] = detectar_columna(df, posibles_lon)

        # Detectar Zona
        posibles_zonas = ['zona', 'Zona', 'sector', 'Sector', 'barrio', 'Barrio']
        mapping_columnas['zona'] = detectar_columna(df, posibles_zonas)

        # Detectar Tipo de propiedad
        posibles_tipos = ['tipo', 'Tipo', 'categoría', 'categoria', 'property type']
        mapping_columnas['tipo'] = detectar_columna(df, posibles_tipos)

        # Detectar Superficie
        posibles_superficies = ['superficie', 'Superficie', 'área', 'area', 'm2', 'metros']
        mapping_columnas['superficie'] = detectar_columna(df, posibles_superficies)

        # Detectar Habitaciones
        posibles_habitaciones = ['habitaciones', 'Habitaciones', 'dormitorios', 'Dormitorios',
                               'rooms', 'bedrooms']
        mapping_columnas['habitaciones'] = detectar_columna(df, posibles_habitaciones)

        # Detectar Baños
        posibles_banios = ['baños', 'Baños', 'banos', 'Banos', 'bathrooms', 'baño']
        mapping_columnas['banios'] = detectar_columna(df, posibles_banios)

        # Mostrar mapeo detectado
        print("Mapeo de columnas detectado:")
        for key, col in mapping_columnas.items():
            print(f"  {key}: {col}")

        # Estadísticas
        total_filas = len(df)
        procesadas = 0
        con_coordenadas = 0
        duplicadas = 0

        for idx, row in df.iterrows():
            try:
                # Extraer datos usando mapeo flexible
                url = str(row.get(mapping_columnas['url'], '')).strip() if mapping_columnas['url'] else ''
                titulo = str(row.get(mapping_columnas['titulo'], '')).strip() if mapping_columnas['titulo'] else ''
                precio = str(row.get(mapping_columnas['precio'], '')).strip() if mapping_columnas['precio'] else ''

                # Validaciones básicas
                if not titulo or not precio or not url:
                    continue

                # Evitar duplicados
                if url in urls_procesadas:
                    duplicadas += 1
                    continue
                urls_procesadas.add(url)

                # Extraer precio numérico
                numeros = re.findall(r'[0-9,]+', precio)
                if numeros:
                    precio_num = float(numeros[0].replace(',', ''))
                else:
                    continue

                # Coordenadas con validación
                lat_raw = row.get(mapping_columnas['latitud']) if mapping_columnas['latitud'] else None
                lon_raw = row.get(mapping_columnas['longitud']) if mapping_columnas['longitud'] else None

                lat_num, lon_num = None, None
                if lat_raw is not None and lon_raw is not None and not pd.isna(lat_raw) and not pd.isna(lon_raw):
                    try:
                        lat_num = float(lat_raw)
                        lon_num = float(lon_raw)

                        # Normalizar coordenadas absurdamente grandes
                        if abs(lat_num) > 1000:
                            lat_num = lat_num / 10000000000000
                        if abs(lon_num) > 1000:
                            lon_num = lon_num / 10000000000000

                        # Validar rango Santa Cruz
                        if not (-18.5 <= lat_num <= -17.0 and -64.0 <= lon_num <= -63.0):
                            lat_num, lon_num = None, None
                        else:
                            con_coordenadas += 1

                    except:
                        lat_num, lon_num = None, None

                # Extraer otros datos
                descripcion = str(row.get(mapping_columnas['descripcion'], '')).strip() if mapping_columnas['descripcion'] else ''
                zona = str(row.get(mapping_columnas['zona'], '')).strip() if mapping_columnas['zona'] else ''
                tipo_propiedad = str(row.get(mapping_columnas['tipo'], '')).strip() if mapping_columnas['tipo'] else ''
                superficie = str(row.get(mapping_columnas['superficie'], '')).strip() if mapping_columnas['superficie'] else ''
                habitaciones = str(row.get(mapping_columnas['habitaciones'], '')).strip() if mapping_columnas['habitaciones'] else ''
                banios = str(row.get(mapping_columnas['banios'], '')).strip() if mapping_columnas['banios'] else ''

                # Limitar descripción
                if len(descripcion) > 500:
                    descripcion = descripcion[:500] + "..."

                # Insertar propiedad
                cursor.execute('''
                    INSERT INTO propiedades
                    (titulo, descripcion, precio_usd, url, latitud, longitud,
                     zona, tipo_propiedad, superficie, habitaciones, banios,
                     proveedor_datos, codigo_proveedor, coordenadas_validas)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO NOTHING
                ''', (
                    titulo,
                    descripcion,
                    precio_num,
                    url,
                    lat_num,
                    lon_num,
                    zona,
                    tipo_propiedad,
                    superficie,
                    habitaciones,
                    banios,
                    'excel_raw_flexible',
                    archivo.name,
                    lat_num is not None and lon_num is not None
                ))

                procesadas += 1

            except Exception as e:
                print(f"    Error fila {idx}: {e}")
                continue

        print(f"Propiedades procesadas: {procesadas}")
        print(f"Con coordenadas válidas: {con_coordenadas}")
        print(f"Duplicadas evitadas: {duplicadas}")

        return {
            'archivo': archivo.name,
            'total_filas': total_filas,
            'procesadas': procesadas,
            'con_coordenadas': con_coordenadas,
            'duplicadas': duplicadas
        }

    except Exception as e:
        print(f"Error procesando {archivo}: {e}")
        return {
            'archivo': archivo.name,
            'error': str(e),
            'procesadas': 0,
            'con_coordenadas': 0
        }

def procesar_guia_urbana(cursor):
    """Procesa la guía urbana con mapeo flexible"""
    print(f"\n=== PROCESANDO GUÍA URBANA ===")
    archivo_guia = '/tmp/data/raw/guia/GUIA URBANA.xlsx'

    if not os.path.exists(archivo_guia):
        # Buscar en ubicaciones alternativas
        ubicaciones_alternativas = [
            'data/raw/guia/GUIA URBANA.xlsx',
            'data/raw/guia_urbana.xlsx',
            '/tmp/data/raw/guia/GUIA URBANA.xlsx'
        ]

        for ubicacion in ubicaciones_alternativas:
            if os.path.exists(ubicacion):
                archivo_guia = ubicacion
                break
        else:
            print("ERROR: No se encontró GUIA URBANA.xlsx")
            return {'servicios': 0, 'con_coordenadas': 0}

    print(f"Procesando: {Path(archivo_guia).name}")

    try:
        df_guia = pd.read_excel(archivo_guia)
        print(f"Filas leídas: {len(df_guia)}")
        print(f"Columnas encontradas: {list(df_guia.columns)}")

        # Mapeo flexible para servicios
        mapping_servicios = {}

        posibles_nombres = ['nombre', 'Nombre', 'name', 'establecimiento']
        mapping_servicios['nombre'] = detectar_columna(df_guia, posibles_nombres)

        posibles_tipos = ['tipo', 'Tipo', 'categoría', 'categoria', 'category']
        mapping_servicios['tipo'] = detectar_columna(df_guia, posibles_tipos)

        posibles_subtipos = ['subtipo', 'Subtipo', 'subcategory', 'subcategoría']
        mapping_servicios['subtipo'] = detectar_columna(df_guia, posibles_subtipos)

        posibles_direcciones = ['dirección', 'direccion', 'Dirección', 'Direccion', 'address']
        mapping_servicios['direccion'] = detectar_columna(df_guia, posibles_direcciones)

        posibles_zonas = ['zona', 'Zona', 'sector', 'Sector']
        mapping_servicios['zona'] = detectar_columna(df_guia, posibles_zonas)

        posibles_lat = ['latitud', 'lat', 'latitude']
        mapping_servicios['latitud'] = detectar_columna(df_guia, posibles_lat)

        posibles_lon = ['longitud', 'lon', 'longitude', 'lng']
        mapping_servicios['longitud'] = detectar_columna(df_guia, posibles_lon)

        print("Mapeo de servicios detectado:")
        for key, col in mapping_servicios.items():
            print(f"  {key}: {col}")

        total_servicios = 0
        con_coordenadas = 0

        for idx, row in df_guia.iterrows():
            try:
                nombre = str(row.get(mapping_servicios['nombre'], '')).strip() if mapping_servicios['nombre'] else ''
                if not nombre:
                    continue

                # Extraer datos de servicio
                tipo_servicio = str(row.get(mapping_servicios['tipo'], '')).strip() if mapping_servicios['tipo'] else ''
                subtipo_servicio = str(row.get(mapping_servicios['subtipo'], '')).strip() if mapping_servicios['subtipo'] else ''
                direccion = str(row.get(mapping_servicios['direccion'], '')).strip() if mapping_servicios['direccion'] else ''
                zona = str(row.get(mapping_servicios['zona'], '')).strip() if mapping_servicios['zona'] else ''

                # Coordenadas
                lat_raw = row.get(mapping_servicios['latitud']) if mapping_servicios['latitud'] else None
                lon_raw = row.get(mapping_servicios['longitud']) if mapping_servicios['longitud'] else None

                if lat_raw is not None and lon_raw is not None and not pd.isna(lat_raw) and not pd.isna(lon_raw):
                    try:
                        lat_num = float(lat_raw)
                        lon_num = float(lon_raw)

                        # Validar rango Santa Cruz
                        if (-18.5 <= lat_num <= -17.0 and -64.0 <= lon_num <= -63.0):
                            # Insertar servicio con coordenadas PostGIS
                            cursor.execute('''
                                INSERT INTO servicios
                                (nombre, tipo_servicio, subtipo_servicio, direccion, zona,
                                 coordenadas, fuente_datos, coordenadas_validas)
                                VALUES (%s, %s, %s, %s, %s,
                                        ST_GeographyFromText('SRID=4326;POINT(' || %s || ' ' || %s || ')'),
                                        %s, %s)
                                ON CONFLICT (nombre, direccion) DO NOTHING
                            ''', (
                                nombre,
                                tipo_servicio,
                                subtipo_servicio,
                                direccion,
                                zona,
                                lon_num,  # PostgreSQL usa (longitud, latitud)
                                lat_num,
                                'excel_raw_guia_urbana',
                                True
                            ))

                            total_servicios += 1
                            con_coordenadas += 1

                    except Exception as e:
                        print(f"    Error coordenadas servicio {idx}: {e}")
                        continue

            except Exception as e:
                print(f"Error fila servicio {idx}: {e}")
                continue

        print(f"Servicios procesados: {total_servicios}")
        print(f"Con coordenadas válidas: {con_coordenadas}")

        return {
            'servicios': total_servicios,
            'con_coordenadas': con_coordenadas
        }

    except Exception as e:
        print(f"Error procesando guía urbana: {e}")
        return {'servicios': 0, 'con_coordenadas': 0}

def main():
    """Función principal de migración flexible"""
    # Configuración PostgreSQL
    db_config = {
        'host': 'localhost',
        'database': 'citrino',
        'user': 'citrino_app',
        'password': 'citrino123',
        'port': '5432',
        'client_encoding': 'utf8'
    }

    print("=" * 80)
    print("MIGRACION FLEXIBLE EXCEL RAW -> POSTGRESQL")
    print("Mapeo inteligente de columnas")
    print("=" * 80)

    # Conectar a PostgreSQL
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        print("Conexión PostgreSQL establecida")
    except Exception as e:
        print(f"Error conectando a PostgreSQL: {e}")
        return 1

    # Procesar archivos de relevamiento
    urls_procesadas = set()
    resultados_relevamiento = []

    # Buscar archivos en múltiples ubicaciones
    ubicaciones_relevamiento = [
        '/tmp/data/raw/relevamiento',
        'data/raw/relevamiento',
        'data/raw'
    ]

    archivos_relevamiento = []
    for ubicacion in ubicaciones_relevamiento:
        if os.path.exists(ubicacion):
            archivos_encontrados = list(Path(ubicacion).glob('*.xlsx'))
            if archivos_encontrados:
                archivos_relevamiento = archivos_encontrados
                print(f"Usando ubicación: {ubicacion}")
                break

    if not archivos_relevamiento:
        print("ERROR: No se encontraron archivos Excel de relevamiento")
        cursor.close()
        conn.close()
        return 1

    print(f"\nEncontrados {len(archivos_relevamiento)} archivos de relevamiento:")
    for archivo in archivos_relevamiento:
        print(f"  - {archivo.name}")

    total_propiedades = 0
    total_con_coordenadas = 0

    for archivo in archivos_relevamiento:
        resultado = procesar_archivo_excel_flexible(archivo, cursor, urls_procesadas)
        resultados_relevamiento.append(resultado)

        if 'error' not in resultado:
            total_propiedades += resultado['procesadas']
            total_con_coordenadas += resultado['con_coordenadas']

    # Procesar guía urbana
    resultado_guia = procesar_guia_urbana(cursor)
    total_servicios = resultado_guia['servicios']
    total_servicios_con_coordenadas = resultado_guia['con_coordenadas']

    # Commit de transacciones
    conn.commit()

    # Actualizar coordenadas PostGIS para propiedades
    print("\nActualizando coordenadas PostGIS para propiedades...")
    cursor.execute('''
        UPDATE propiedades
        SET coordenadas = ST_GeographyFromText('SRID=4326;POINT(' || longitud || ' ' || latitud || ')')
        WHERE latitud IS NOT NULL AND longitud IS NOT NULL AND coordenadas IS NULL
    ''')

    # Estadísticas finales
    cursor.execute("SELECT COUNT(*) FROM propiedades")
    total_propiedades_db = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM propiedades WHERE coordenadas IS NOT NULL")
    propiedades_con_coordenadas = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM servicios")
    total_servicios_db = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM servicios WHERE coordenadas IS NOT NULL")
    servicios_con_coordenadas = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    # Reporte final
    print("\n" + "=" * 80)
    print("MIGRACION FLEXIBLE COMPLETADA")
    print("=" * 80)
    print(f"PROPIEDADES TOTALES EN BD: {total_propiedades_db}")
    print(f"Propiedades con coordenadas: {propiedades_con_coordenadas} ({propiedades_con_coordenadas/total_propiedades_db*100:.1f}%)")
    print(f"SERVICIOS TOTALES EN BD: {total_servicios_db}")
    print(f"Servicios con coordenadas: {servicios_con_coordenadas} ({servicios_con_coordenadas/total_servicios_db*100:.1f}%)")
    print(f"REGISTROS TOTALES: {total_propiedades_db + total_servicios_db}")

    print("\n=== DETALLE POR ARCHIVO ===")
    for resultado in resultados_relevamiento:
        if 'error' in resultado:
            print(f"ERROR {resultado['archivo']}: {resultado['error']}")
        else:
            print(f"{resultado['archivo']}: {resultado['procesadas']} procesadas, {resultado['con_coordenadas']} con coordenadas")

    print("=" * 80)

    # Guardar reporte
    reporte = {
        'fecha': pd.Timestamp.now().isoformat(),
        'propiedades': {
            'total_db': total_propiedades_db,
            'con_coordenadas': propiedades_con_coordenadas,
            'procesadas_en_sesion': total_propiedades
        },
        'servicios': {
            'total_db': total_servicios_db,
            'con_coordenadas': servicios_con_coordenadas,
            'procesados_en_sesion': total_servicios
        },
        'archivos_procesados': resultados_relevamiento
    }

    with open('migration_report.json', 'w', encoding='utf-8') as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)

    print(f"Reporte guardado en: migration_report.json")

    return 0

if __name__ == '__main__':
    exit(main())