#!/usr/bin/env python3
"""
Script para procesar archivos Excel de propiedades y convertirlos al formato JSON mejorado.
Extrae datos determinantes: superficie, habitaciones, baños, garaje, zonas premium, etc.
"""

import pandas as pd
import json
import os
import re
from typing import List, Dict, Any
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents'))
from unicode_utils import printer

def limpiar_texto(texto):
    """Limpia y normaliza texto."""
    if pd.isna(texto):
        return ""
    texto = str(texto).strip()
    return texto

def extraer_numero(texto):
    """Extrae número de un texto."""
    if pd.isna(texto):
        return None
    texto = str(texto)
    numeros = re.findall(r'(\d+(?:\.\d+)?)', texto)
    if numeros:
        return float(numeros[0])
    return None

def determinar_zona_premium(barrio_o_zona):
    """Determina si es una zona premium basado en el nombre."""
    if pd.isna(barrio_o_zona):
        return "desconocida"

    zona_lower = str(barrio_o_zona).lower()

    zonas_premium = {
        "equipetrol": "Equipetrol",
        "las palmas": "Las Palmas",
        "urubo": "Urubó",
        "norte": "Zona Norte",
        "san isidro": "San Isidro",
        "los lotes": "Los Lotes",
        "el toro": "El Toro"
    }

    for key, value in zonas_premium.items():
        if key in zona_lower:
            return value

    return barrio_o_zona

def extraer_caracteristicas_desde_texto(texto):
    """Extrae características de descripciones textuales."""
    if pd.isna(texto):
        return {}

    texto_lower = str(texto).lower()
    caracteristicas = {}

    # Extraer habitaciones
    if 'habitacion' in texto_lower or 'dormitorio' in texto_lower:
        habitaciones_match = re.search(r'(\d+)\s*(?:habitacion|dormitorio)', texto_lower)
        if habitaciones_match:
            caracteristicas['habitaciones'] = int(habitaciones_match.group(1))

    # Extraer baños
    if 'bano' in texto_lower:
        banos_match = re.search(r'(\d+)\s*bano', texto_lower)
        if banos_match:
            caracteristicas['banos'] = int(banos_match.group(1))

    # Extraer superficie
    if 'm2' in texto_lower or 'metros' in texto_lower:
        superficie_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:m2|metros|m²)', texto_lower)
        if superficie_match:
            caracteristicas['superficie_m2'] = float(superficie_match.group(1))

    # Buscar cochera/garaje
    caracteristicas['tiene_garaje'] = any(word in texto_lower for word in ['garaje', 'cochera', 'estacionamiento'])

    # Buscar amenities
    caracteristicas['piscina'] = 'piscina' in texto_lower
    caracteristicas['gimnasio'] = any(word in texto_lower for word in ['gimnasio', 'gym', 'fitness'])

    return caracteristicas

def procesar_archivo_excel(ruta_archivo, nombre_proyecto):
    """Procesa un archivo Excel y extrae datos de propiedades."""
    try:
        printer.info(f"Procesando archivo: {ruta_archivo}")

        xls = pd.ExcelFile(ruta_archivo)

        propiedades = []

        # Procesar cada hoja
        for sheet_name in xls.sheet_names:
            printer.info(f"  Procesando hoja: {sheet_name}")

            try:
                df = pd.read_excel(ruta_archivo, sheet_name=sheet_name)

                # Buscar columnas relevantes
                precio_col = None
                superficie_col = None
                ubicacion_col = None
                descripcion_col = None

                for col in df.columns:
                    col_lower = str(col).lower()
                    if any(keyword in col_lower for keyword in ['precio', 'valor', 'usd', '$']):
                        precio_col = col
                    elif any(keyword in col_lower for keyword in ['superficie', 'm2', 'metros', 'area']):
                        superficie_col = col
                    elif any(keyword in col_lower for keyword in ['ubicacion', 'zona', 'sector', 'barrio', 'direccion']):
                        ubicacion_col = col
                    elif any(keyword in col_lower for keyword in ['descripcion', 'detalle', 'caracteristica', 'observacion']):
                        descripcion_col = col

                # Extraer datos de cada fila
                for index, row in df.iterrows():
                    # Saltar filas vacías
                    if row.isnull().all():
                        continue

                    propiedad = {
                        "id": f"{nombre_proyecto}_{sheet_name}_{index}",
                        "nombre": f"{nombre_proyecto} - Unidad {index + 1}",
                        "tipo": "Departamento",  # Asumir departamento por defecto
                        "proyecto_origen": nombre_proyecto,
                        "hoja_origen": sheet_name
                    }

                    # Extraer precio
                    precio = None
                    if precio_col and precio_col in row:
                        precio = extraer_numero(row[precio_col])

                    if precio and precio > 1000:  # Precio razonable
                        propiedad["caracteristicas_principales"] = {
                            "precio": int(precio),
                            "superficie_m2": None,
                            "habitaciones": None,
                            "dormitorios": None,
                            "banos_completos": None,
                            "banos_medios": None,
                            "cochera_garaje": False,
                            "numero_espacios_garaje": 0
                        }

                        # Extraer superficie
                        if superficie_col and superficie_col in row:
                            superficie = extraer_numero(row[superficie_col])
                            if superficie:
                                propiedad["caracteristicas_principales"]["superficie_m2"] = int(superficie)

                        # Extraer ubicación
                        if ubicacion_col and ubicacion_col in row:
                            ubicacion = limpiar_texto(row[ubicacion_col])
                            zona = determinar_zona_premium(ubicacion)

                            propiedad["ubicacion"] = {
                                "direccion": ubicacion,
                                "barrio": ubicacion,
                                "zona": zona,
                                "sector": zona,
                                "coordenadas": {"lat": None, "lng": None}
                            }

                            # Valorización por zona
                            if zona in ["Equipetrol", "Las Palmas", "Urubó", "Zona Norte"]:
                                propiedad["valorizacion_sector"] = {
                                    "valor_m2_promedio_zona": 1500 if zona == "Equipetrol" else 1200,
                                    "plusvalia_tendencia": "creciente",
                                    "demanda_sector": "alta",
                                    "seguridad_zona": "alta",
                                    "nivel_socioeconomico": "alto"
                                }

                        # Extraer características de texto descriptivo
                        if descripcion_col and descripcion_col in row:
                            descripcion = limpiar_texto(row[descripcion_col])
                            caracteristicas_texto = extraer_caracteristicas_desde_texto(descripcion)

                            # Actualizar características principales
                            for key, value in caracteristicas_texto.items():
                                if key in propiedad["caracteristicas_principales"]:
                                    propiedad["caracteristicas_principales"][key] = value

                            propiedad["detalles_construccion"] = {
                                "antiguedad_anios": None,
                                "estado_conservacion": "bueno",
                                "balcon": "balcon" in descripcion.lower(),
                                "piscina_privada": caracteristicas_texto.get("piscina", False),
                                "gimnasio": caracteristicas_texto.get("gimnasio", False)
                            }

                        # Añadir detalles básicos de condominio para zonas premium
                        if propiedad.get("ubicacion", {}).get("zona") in ["Equipetrol", "Las Palmas", "Urubó"]:
                            propiedad["condominio"] = {
                                "es_condominio_cerrado": True,
                                "seguridad_24h": True,
                                "amenidades": ["piscina_comunitaria", "seguridad"]
                            }

                        # Calcular precio por m2 si tenemos ambos datos
                        caract = propiedad["caracteristicas_principales"]
                        if caract["precio"] and caract.get("superficie_m2"):
                            precio_m2 = caract["precio"] / caract["superficie_m2"]
                            if not propiedad.get("valorizacion_sector"):
                                propiedad["valorizacion_sector"] = {}
                            propiedad["valorizacion_sector"]["precio_m2_calculado"] = int(precio_m2)

                        propiedades.append(propiedad)

            except Exception as e:
                printer.warning(f"    Error procesando hoja {sheet_name}: {e}")
                continue

        printer.success(f"Extraídas {len(propiedades)} propiedades de {ruta_archivo}")
        return propiedades

    except Exception as e:
        printer.error(f"Error procesando archivo {ruta_archivo}: {e}")
        return []

def main():
    """Función principal."""
    printer.info("Iniciando procesamiento de archivos Excel para extracción de propiedades")
    printer.info("=" * 60)

    # Directorios a procesar
    directorios = [
        "./data/raw/Citrino - Scz/Scz - Bolivia Planillas de Proyectos - Relevamientos de la Oferta/",
        "./data/raw/Citrino - Scz/Brochures proyectos scz/"
    ]

    todas_propiedades = []

    # Procesar archivos Excel
    for directorio in directorios:
        if os.path.exists(directorio):
            printer.info(f"Procesando directorio: {directorio}")

            for archivo in os.listdir(directorio):
                if archivo.endswith('.xlsx'):
                    ruta_completa = os.path.join(directorio, archivo)

                    # Extraer nombre del proyecto del nombre del archivo
                    nombre_proyecto = os.path.splitext(archivo)[0].replace("Planilla ", "").replace("Precios ", "")

                    propiedades = procesar_archivo_excel(ruta_completa, nombre_proyecto)
                    todas_propiedades.extend(propiedades)
        else:
            printer.warning(f"Directorio no encontrado: {directorio}")

    # Eliminar duplicados por ID
    ids_vistos = set()
    propiedades_unicas = []
    for prop in todas_propiedades:
        if prop["id"] not in ids_vistos:
            ids_vistos.add(prop["id"])
            propiedades_unicas.append(prop)

    printer.info(f"Total de propiedades únicas extraídas: {len(propiedades_unicas)}")

    # Guardar en JSON
    if propiedades_unicas:
        ruta_salida = "./data/propiedades_ampliadas.json"
        with open(ruta_salida, 'w', encoding='utf-8') as f:
            json.dump(propiedades_unicas, f, indent=2, ensure_ascii=False)

        printer.success(f"Propiedades guardadas en: {ruta_salida}")

        # Mostrar estadísticas
        printer.info("Estadísticas del dataset:")
        zonas = {}
        total_precio = 0
        propiedades_con_precio = 0

        for prop in propiedades_unicas:
            zona = prop.get("ubicacion", {}).get("zona", "desconocida")
            zonas[zona] = zonas.get(zona, 0) + 1

            precio = prop.get("caracteristicas_principales", {}).get("precio")
            if precio:
                total_precio += precio
                propiedades_con_precio += 1

        for zona, count in zonas.items():
            printer.info(f"  {zona}: {count} propiedades")

        if propiedades_con_precio > 0:
            precio_promedio = total_precio / propiedades_con_precio
            printer.info(f"Precio promedio: ${precio_promedio:,.0f}")
    else:
        printer.error("No se encontraron propiedades para procesar")

if __name__ == "__main__":
    main()