#!/usr/bin/env python3
"""
PROCESAR TODO EXCEL RAW → CSV LOCAL
Genera archivos CSV listos para importar a PostgreSQL
"""

import os
import pandas as pd
from pathlib import Path
import re
import json
import sys

def extraer_precio_numerico(precio_str):
    """Extrae valor numérico de precio"""
    if pd.isna(precio_str) or precio_str == '':
        return None

    precio_str = str(precio_str)
    # Buscar números en el texto
    numeros = re.findall(r'[0-9,]+', precio_str)
    if numeros:
        try:
            # Limpiar y convertir
            precio_limpio = numeros[0].replace(',', '')
            return float(precio_limpio)
        except:
            return None
    return None

def limpiar_texto(texto):
    """Limpia texto para CSV"""
    if pd.isna(texto) or texto == '':
        return ''
    texto = str(texto)
    # Limitar longitud
    if len(texto) > 500:
        texto = texto[:500] + "..."
    # Reemplazar saltos de línea
    texto = texto.replace('\n', ' ').replace('\r', ' ')
    return texto.strip()

def procesar_archivo_completo(archivo):
    """Procesa archivo completo con detección automática de columnas"""
    print(f"\n=== PROCESANDO: {archivo.name} ===")

    try:
        df = pd.read_excel(str(archivo))
        print(f"Filas leídas: {len(df)}")
        print(f"Columnas: {list(df.columns)}")

        # Detectar columnas automáticamente
        columnas = df.columns.tolist()

        # Mapeo flexible
        url_col = None
        titulo_col = None
        precio_col = None
        descripcion_col = None
        lat_col = None
        lon_col = None
        zona_col = None
        tipo_col = None

        for col in columnas:
            col_lower = str(col).lower()

            # URL
            if url_col is None and any(keyword in col_lower for keyword in ['url', 'link', 'enlace']):
                url_col = col

            # Título
            elif titulo_col is None and any(keyword in col_lower for keyword in ['título', 'titulo', 'title']):
                titulo_col = col

            # Precio
            elif precio_col is None and any(keyword in col_lower for keyword in ['precio', 'price', '$']):
                precio_col = col

            # Descripción
            elif descripcion_col is None and any(keyword in col_lower for keyword in ['descripción', 'descripcion', 'details']):
                descripcion_col = col

            # Latitud
            elif lat_col is None and any(keyword in col_lower for keyword in ['latitud', 'lat']):
                lat_col = col

            # Longitud
            elif lon_col is None and any(keyword in col_lower for keyword in ['longitud', 'lon', 'lng']):
                lon_col = col

            # Zona
            elif zona_col is None and any(keyword in col_lower for keyword in ['zona', 'sector', 'ubicaci', 'direccion']):
                zona_col = col

            # Tipo
            elif tipo_col is None and any(keyword in col_lower for keyword in ['tipo', 'categoria', 'operaci']):
                tipo_col = col

        print(f"Columnas detectadas:")
        print(f"  URL: {url_col}")
        print(f"  Título: {titulo_col}")
        print(f"  Precio: {precio_col}")
        print(f"  Descripción: {descripcion_col}")
        print(f"  Latitud: {lat_col}")
        print(f"  Longitud: {lon_col}")
        print(f"  Zona: {zona_col}")
        print(f"  Tipo: {tipo_col}")

        # Procesar datos
        datos_procesados = []
        procesadas = 0
        con_coordenadas = 0
        sin_url = 0
        sin_precio = 0

        for idx, row in df.iterrows():
            try:
                # Extraer datos
                url = str(row.get(url_col, '')).strip() if url_col else ''
                titulo = limpiar_texto(row.get(titulo_col, '')) if titulo_col else ''
                precio = str(row.get(precio_col, '')).strip() if precio_col else ''
                descripcion = limpiar_texto(row.get(descripcion_col, '')) if descripcion_col else ''
                zona = limpiar_texto(row.get(zona_col, '')) if zona_col else ''
                tipo = limpiar_texto(row.get(tipo_col, '')) if tipo_col else ''

                # Validaciones básicas
                if not titulo:
                    # Generar título automático
                    if zona:
                        titulo = f"Propiedad en {zona}"
                    elif tipo:
                        titulo = f"{tipo}"
                    else:
                        titulo = f"Propiedad {idx+1}"

                if not precio:
                    sin_precio += 1
                    continue

                # Extraer precio numérico
                precio_num = extraer_precio_numerico(precio)
                if precio_num is None:
                    sin_precio += 1
                    continue

                # Coordenadas
                lat_num, lon_num = None, None
                tiene_coordenadas = False

                # Caso especial: coordenadas combinadas
                if 'Coordenadas' in df.columns and pd.notna(row.get('Coordenadas')):
                    coord_str = str(row.get('Coordenadas', ''))
                    if ',' in coord_str:
                        try:
                            parts = coord_str.split(',')
                            lat_num = float(parts[0])
                            lon_num = float(parts[1])

                            # Validar rango Santa Cruz
                            if (-18.5 <= lat_num <= -17.0 and -64.0 <= lon_num <= -63.0):
                                tiene_coordenadas = True
                                con_coordenadas += 1
                            else:
                                lat_num, lon_num = None, None
                        except:
                            lat_num, lon_num = None, None
                else:
                    # Coordenadas separadas
                    lat_raw = row.get(lat_col) if lat_col else None
                    lon_raw = row.get(lon_col) if lon_col else None

                    if lat_raw is not None and lon_raw is not None and not pd.isna(lat_raw) and not pd.isna(lon_raw):
                        try:
                            lat_num = float(lat_raw)
                            lon_num = float(lon_raw)

                            # Validar rango Santa Cruz
                            if not (-18.5 <= lat_num <= -17.0 and -64.0 <= lon_num <= -63.0):
                                lat_num, lon_num = None, None
                            else:
                                tiene_coordenadas = True
                                con_coordenadas += 1

                        except:
                            lat_num, lon_num = None, None

                # Generar URL si no existe
                if not url:
                    sin_url += 1
                    url = f"sin_url_{archivo.name}_{idx+1}"

                # Agregar a datos procesados
                datos_procesados.append({
                    'titulo': titulo,
                    'descripcion': descripcion,
                    'precio_usd': precio_num,
                    'url': url,
                    'latitud': lat_num,
                    'longitud': lon_num,
                    'zona': zona,
                    'tipo_propiedad': tipo,
                    'proveedor_datos': 'excel_raw_local',
                    'codigo_proveedor': archivo.name,
                    'coordenadas_validas': tiene_coordenadas
                })

                procesadas += 1

            except Exception as e:
                print(f"    Error fila {idx}: {e}")
                continue

        print(f"Propiedades procesadas: {procesadas}")
        print(f"Con coordenadas válidas: {con_coordenadas}")
        print(f"Sin URL: {sin_url}")
        print(f"Sin precio válido: {sin_precio}")

        return {
            'archivo': archivo.name,
            'datos': datos_procesados,
            'procesadas': procesadas,
            'con_coordenadas': con_coordenadas
        }

    except Exception as e:
        print(f"Error procesando {archivo}: {e}")
        return {
            'archivo': archivo.name,
            'error': str(e),
            'datos': [],
            'procesadas': 0,
            'con_coordenadas': 0
        }

def procesar_guia_urbana():
    """Procesa guía urbana"""
    print(f"\n=== PROCESANDO GUÍA URBANA ===")

    ubicaciones = [
        'data/raw/guia/GUIA URBANA.xlsx',
        'data/raw/guia_urbana.xlsx'
    ]

    archivo_guia = None
    for ubicacion in ubicaciones:
        if os.path.exists(ubicacion):
            archivo_guia = ubicacion
            break

    if not archivo_guia:
        print("ERROR: No se encontró GUIA URBANA.xlsx")
        return {'datos': [], 'procesados': 0}

    print(f"Procesando: {Path(archivo_guia).name}")

    try:
        df = pd.read_excel(archivo_guia)
        print(f"Filas leídas: {len(df)}")

        datos_servicios = []
        procesados = 0
        con_coordenadas = 0

        for idx, row in df.iterrows():
            try:
                nombre = limpiar_texto(row.get('nombre', ''))
                if not nombre:
                    continue

                # Extraer datos
                tipo_servicio = limpiar_texto(row.get('tipo', ''))
                subtipo_servicio = limpiar_texto(row.get('subtipo', ''))
                direccion = limpiar_texto(row.get('direccion', ''))
                zona = limpiar_texto(row.get('zona', ''))

                # Coordenadas
                lat_raw = row.get('latitud')
                lon_raw = row.get('longitud')

                lat_num, lon_num = None, None
                tiene_coordenadas = False

                if lat_raw is not None and lon_raw is not None and not pd.isna(lat_raw) and not pd.isna(lon_raw):
                    try:
                        lat_num = float(lat_raw)
                        lon_num = float(lon_raw)

                        # Validar rango Santa Cruz
                        if (-18.5 <= lat_num <= -17.0 and -64.0 <= lon_num <= -63.0):
                            tiene_coordenadas = True
                            con_coordenadas += 1
                        else:
                            lat_num, lon_num = None, None

                    except:
                        lat_num, lon_num = None, None

                datos_servicios.append({
                    'nombre': nombre,
                    'tipo_servicio': tipo_servicio,
                    'subtipo_servicio': subtipo_servicio,
                    'direccion': direccion,
                    'zona': zona,
                    'latitud': lat_num,
                    'longitud': lon_num,
                    'fuente_datos': 'excel_raw_guia_local',
                    'coordenadas_validas': tiene_coordenadas
                })

                procesados += 1

            except Exception as e:
                print(f"Error fila servicio {idx}: {e}")
                continue

        print(f"Servicios procesados: {procesados}")
        print(f"Con coordenadas válidas: {con_coordenadas}")

        return {
            'datos': datos_servicios,
            'procesados': procesados,
            'con_coordenadas': con_coordenadas
        }

    except Exception as e:
        print(f"Error procesando guía urbana: {e}")
        return {'datos': [], 'procesados': 0, 'error': str(e)}

def main():
    """Función principal"""
    print("=" * 80)
    print("PROCESAMIENTO COMPLETO EXCEL RAW -> CSV LOCAL")
    print("Genera archivos CSV listos para importar")
    print("=" * 80)

    # Procesar archivos de relevamiento
    directorio = Path('data/raw/relevamiento')
    archivos_excel = list(directorio.glob('*.xlsx'))

    print(f"Encontrados {len(archivos_excel)} archivos Excel de relevamiento")

    todos_los_datos = []
    resultados_relevamiento = []
    total_propiedades = 0
    total_con_coordenadas = 0

    for archivo in archivos_excel:
        resultado = procesar_archivo_completo(archivo)
        resultados_relevamiento.append(resultado)

        if 'error' not in resultado:
            todos_los_datos.extend(resultado['datos'])
            total_propiedades += resultado['procesadas']
            total_con_coordenadas += resultado['con_coordenadas']

    # Procesar guía urbana
    resultado_guia = procesar_guia_urbana()
    datos_servicios = resultado_guia.get('datos', [])
    total_servicios = resultado_guia.get('procesados', 0)
    total_servicios_con_coordenadas = resultado_guia.get('con_coordenadas', 0)

    # Crear DataFrames
    if todos_los_datos:
        df_propiedades = pd.DataFrame(todos_los_datos)
        archivo_propiedades = 'propiedades_procesadas.csv'
        df_propiedades.to_csv(archivo_propiedades, index=False, encoding='utf-8')
        print(f"\nPropiedades guardadas en: {archivo_propiedades}")
        print(f"Total propiedades: {len(df_propiedades)}")
        print(f"Con coordenadas: {df_propiedades['coordenadas_validas'].sum()}")

    if datos_servicios:
        df_servicios = pd.DataFrame(datos_servicios)
        archivo_servicios = 'servicios_procesados.csv'
        df_servicios.to_csv(archivo_servicios, index=False, encoding='utf-8')
        print(f"\nServicios guardados en: {archivo_servicios}")
        print(f"Total servicios: {len(df_servicios)}")
        print(f"Con coordenadas: {df_servicios['coordenadas_validas'].sum()}")

    # Reporte final
    print("\n" + "=" * 80)
    print("PROCESAMIENTO COMPLETO FINALIZADO")
    print("=" * 80)
    print(f"PROPIEDADES PROCESADAS: {total_propiedades}")
    print(f"Propiedades con coordenadas: {total_con_coordenadas}")
    print(f"SERVICIOS PROCESADOS: {total_servicios}")
    print(f"Servicios con coordenadas: {total_servicios_con_coordenadas}")
    print(f"REGISTROS TOTALES: {total_propiedades + total_servicios}")

    print("\n=== DETALLE POR ARCHIVO ===")
    for resultado in resultados_relevamiento:
        if 'error' in resultado:
            print(f"ERROR {resultado['archivo']}: {resultado['error']}")
        else:
            print(f"{resultado['archivo']}: {resultado['procesadas']} procesadas, {resultado['con_coordenadas']} con coordenadas")

    print("\n=== ARCHIVOS GENERADOS ===")
    if todos_los_datos:
        print(f"- propiedades_procesadas.csv ({len(df_propiedades)} registros)")
    if datos_servicios:
        print(f"- servicios_procesados.csv ({len(df_servicios)} registros)")

    # Generar SQL de importación
    if todos_los_datos:
        sql_file = 'importar_propiedades.sql'
        with open(sql_file, 'w', encoding='utf-8') as f:
            f.write("-- Importar propiedades desde CSV\n")
            f.write(f"COPY propiedades (titulo, descripcion, precio_usd, url, latitud, longitud, zona, tipo_propiedad, proveedor_datos, codigo_proveedor, coordenadas_validas)\n")
            f.write(f"FROM '{os.path.abspath('propiedades_procesadas.csv')}'\n")
            f.write(f"DELIMITER ','\n")
            f.write(f"CSV HEADER;\n\n")
            f.write("-- Actualizar coordenadas PostGIS\n")
            f.write("UPDATE propiedades\n")
            f.write("SET coordenadas = ST_GeographyFromText('SRID=4326;POINT(' || longitud || ' ' || latitud || ')')\n")
            f.write("WHERE latitud IS NOT NULL AND longitud IS NOT NULL AND coordenadas IS NULL;\n")
        print(f"- {sql_file} (script de importación PostgreSQL)")

    print("=" * 80)

    # Guardar reporte
    reporte = {
        'fecha': pd.Timestamp.now().isoformat(),
        'metodo': 'csv_local',
        'propiedades': {
            'procesadas': total_propiedades,
            'con_coordenadas': total_con_coordenadas
        },
        'servicios': {
            'procesados': total_servicios,
            'con_coordenadas': total_servicios_con_coordenadas
        },
        'archivos_generados': [
            'propiedades_procesadas.csv' if todos_los_datos else None,
            'servicios_procesados.csv' if datos_servicios else None,
            'importar_propiedades.sql' if todos_los_datos else None
        ],
        'archivos_procesados': resultados_relevamiento
    }

    with open('procesamiento_local_report.json', 'w', encoding='utf-8') as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)

    print(f"Reporte guardado en: procesamiento_local_report.json")

    return 0

if __name__ == '__main__':
    sys.exit(main())