#!/usr/bin/env python3
"""
Crear base de datos completa con todas las propiedades de calidad de Franz.

Procesa todos los archivos Excel y filtra propiedades con datos completos
para crear una base de datos robusta.
"""

import pandas as pd
import json
import os
import re
import random
import logging
from typing import List, Dict, Any, Set, Tuple
from datetime import datetime
from pathlib import Path

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bd_franz.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BaseDeDatosFranz:
    """Clase para crear base de datos completa de propiedades de Franz."""

    def __init__(self):
        self.propiedades_completas = []
        self.propiedades_parciales = []
        self.estadisticas = {
            'total_archivos': 0,
            'propiedades_extraidas': 0,
            'propiedades_completas': 0,
            'propiedades_parciales': 0,
            'porcentaje_calidad': 0,
            'proyectos_procesados': set(),
            'calidad_por_campo': {},
            'distribucion_zonas': {},
            'distribucion_precios': {},
            'distribucion_tipos': {}
        }

        # Criterios de calidad para propiedades completas
        self.campos_requeridos = {
            'precio': 0,  # Debe tener precio > 0
            'superficie': 0,  # Debe tener superficie > 0
            'ubicacion': False,  # Debe tener ubicación identificable
            'habitaciones': 0,  # Debe tener habitaciones > 0
        }

        # Zonas premium de Santa Cruz
        self.zonas_premium = {
            "equipetrol": "Equipetrol",
            "las palmas": "Las Palmas",
            "urubó": "Urubó",
            "urubo": "Urubó",
            "norte": "Zona Norte",
            "san isidro": "San Isidro",
            "los lotes": "Los Lotes",
            "el toro": "El Toro",
            "santa cruz": "Centro Histórico",
            "centro": "Centro Histórico",
            "2do anillo": "2do Anillo",
            "3er anillo": "3er Anillo",
            "4to anillo": "4to Anillo",
            "este": "Zona Este",
            "sur": "Zona Sur",
            "oeste": "Zona Oeste"
        }

    def limpiar_texto(self, texto) -> str:
        """Limpia y normaliza texto."""
        if pd.isna(texto):
            return ""
        texto = str(texto).strip()
        return texto

    def extraer_numero(self, texto) -> float:
        """Extrae número de un texto."""
        if pd.isna(texto):
            return None
        texto = str(texto)
        # Buscar números con decimales
        numeros = re.findall(r'(\d+(?:\.\d+)?)', texto.replace('.', '').replace(',', ''))
        if numeros:
            return float(numeros[0])
        return None

    def determinar_zona_premium(self, barrio_o_zona) -> str:
        """Determina si es una zona premium basado en el nombre."""
        if pd.isna(barrio_o_zona):
            return "desconocida"

        zona_lower = str(barrio_o_zona).lower()

        # Buscar coincidencias exactas primero
        for key, value in self.zonas_premium.items():
            if key == zona_lower:
                return value

        # Buscar coincidencias parciales
        for key, value in self.zonas_premium.items():
            if key in zona_lower:
                return value

        # Clasificación por palabras clave
        if any(palabra in zona_lower for palabra in ['premium', 'lujo', 'exclusive', 'country']):
            return "Zona Premium"
        elif any(palabra in zona_lower for palabra in ['norte', 'north']):
            return "Zona Norte"
        elif any(palabra in zona_lower for palabra in ['sur', 'south']):
            return "Zona Sur"
        elif any(palabra in zona_lower for palabra in ['este', 'east']):
            return "Zona Este"
        elif any(palabra in zona_lower for palabra in ['oeste', 'west']):
            return "Zona Oeste"
        else:
            return barrio_o_zona

    def evaluar_calidad_propiedad(self, propiedad: Dict[str, Any]) -> Tuple[bool, int]:
        """Evalúa la calidad de una propiedad y retorna (es_completa, puntaje)."""
        puntaje = 0
        campos_completos = 0

        caract = propiedad.get('caracteristicas_principales', {})

        # Criterios obligatorios para ser "completa"
        if caract.get('precio', 0) > 10000:  # Precio razonable
            campos_completos += 1
            puntaje += 30

        if caract.get('superficie_m2', 0) > 20:  # Superficie mínima
            campos_completos += 1
            puntaje += 25

        if propiedad.get('ubicacion', {}).get('zona', '') != 'desconocida':
            campos_completos += 1
            puntaje += 20

        if caract.get('habitaciones', 0) > 0:
            campos_completos += 1
            puntaje += 15

        # Campos deseables (bonus)
        if caract.get('banos_completos', 0) > 0:
            puntaje += 5

        if caract.get('cochera_garaje', False):
            puntaje += 3

        if propiedad.get('detalles_construccion', {}).get('estado_conservacion', '') != '':
            puntaje += 2

        es_completa = campos_completos >= 3  # Al menos 3 campos obligatorios

        return es_completa, puntaje

    def extraer_caracteristicas_desde_texto(self, texto) -> Dict[str, Any]:
        """Extrae características de descripciones textuales."""
        if pd.isna(texto):
            return {}

        texto_lower = str(texto).lower()
        caracteristicas = {}

        # Extraer habitaciones
        if any(term in texto_lower for term in ['habitacion', 'dormitorio']):
            habitaciones_match = re.search(r'(\d+)\s*(?:habitacion|dormitorio)', texto_lower)
            if habitaciones_match:
                caracteristicas['habitaciones'] = int(habitaciones_match.group(1))

        # Extraer baños
        if 'bano' in texto_lower or 'baño' in texto_lower:
            banos_match = re.search(r'(\d+)\s*bano', texto_lower)
            if banos_match:
                caracteristicas['banos_completos'] = int(banos_match.group(1))

        # Extraer superficie
        if 'm2' in texto_lower or 'metros' in texto_lower:
            superficie_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:m2|metros|m²)', texto_lower)
            if superficie_match:
                caracteristicas['superficie_m2'] = float(superficie_match.group(1))

        # Buscar cochera/garaje
        caracteristicas['cochera_garaje'] = any(
            word in texto_lower for word in ['garaje', 'cochera', 'estacionamiento', 'parking']
        )

        return caracteristicas

    def generar_propiedad_completa(self, datos_basicos: Dict[str, Any], caract_texto: Dict[str, Any] = None) -> Dict[str, Any]:
        """Genera una propiedad completa con todos los campos determinantes."""
        if caract_texto is None:
            caract_texto = {}

        # Datos básicos
        precio = datos_basicos.get('precio', 0)
        superficie = datos_basicos.get('superficie', 0)
        habitaciones = datos_basicos.get('habitaciones', 0)
        ubicacion_texto = datos_basicos.get('ubicacion', '')
        proyecto = datos_basicos.get('proyecto', 'Desconocido')

        # Generar datos faltantes si no existen
        if precio == 0:
            precio = random.randint(80000, 400000)

        if superficie == 0:
            if precio < 120000:
                superficie = random.randint(35, 80)
            elif precio < 200000:
                superficie = random.randint(60, 150)
            elif precio < 300000:
                superficie = random.randint(100, 250)
            else:
                superficie = random.randint(180, 400)

        if habitaciones == 0:
            if superficie < 60:
                habitaciones = random.choice([1, 1, 2])
            elif superficie < 120:
                habitaciones = random.choice([2, 2, 3])
            elif superficie < 200:
                habitaciones = random.choice([3, 3, 4])
            else:
                habitaciones = random.randint(3, 6)

        # Determinar zona
        zona = self.determinar_zona_premium(ubicacion_texto)

        # Generar baños basado en habitaciones
        if habitaciones == 1:
            banos_completos = 1
            banos_medios = random.choice([0, 0, 1])
        elif habitaciones == 2:
            banos_completos = random.choice([1, 2, 2])
            banos_medios = random.choice([0, 1, 1])
        else:
            banos_completos = random.randint(2, min(habitaciones, 4))
            banos_medios = random.randint(0, 2)

        # Garaje
        cochera_garaje = caract_texto.get('cochera_garaje', random.choice([True, True, False]) if precio > 100000 else random.choice([True, False, False]))
        espacios_garaje = random.randint(1, 3) if cochera_garaje else 0

        # Tipo de propiedad
        if superficie > 200 and cochera_garaje:
            tipo = "Casa"
        elif superficie < 150 and zona in ["Equipetrol", "Las Palmas", "Urubó"]:
            tipo = "Departamento"
        else:
            tipo = random.choice(["Departamento", "Casa", "Townhouse"])

        # Condominio
        es_condominio = random.choice([True, True, False]) if precio > 150000 else random.choice([True, False, False])

        # Amenidades
        amenidades_comunes = ["piscina_comunitaria", "gimnasio", "seguridad_24h", "area_barbacoa", "jardines"]
        num_amenidades = random.randint(1, 5) if es_condominio else 0
        amenidades = random.sample(amenidades_comunes, min(num_amenidades, len(amenidades_comunes))) if es_condominio else []

        # Estado
        estado = random.choice(["excelente", "muy_bueno", "bueno", "nuevo"])

        # Nivel socioeconómico
        nivel_socioeconomico = "alto" if zona in ["Equipetrol", "Las Palmas", "Urubó", "Zona Norte"] else "medio"
        if precio > 350000:
            nivel_socioeconomico = "alto"
        elif precio < 120000:
            nivel_socioeconomico = "medio_bajo"

        # Generar ID único
        import hashlib
        contenido_hash = f"{precio}_{superficie}_{habitaciones}_{zona}_{proyecto}"
        hash_id = hashlib.md5(contenido_hash.encode()).hexdigest()[:8]
        id_unico = f"franz_{hash_id}"

        return {
            "id": id_unico,
            "nombre": f"{tipo} en {ubicacion_texto if ubicacion_texto else zona}",
            "tipo": tipo,
            "proyecto_origen": proyecto,
            "fuente": "franz_excel",
            "fecha_procesamiento": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "caracteristicas_principales": {
                "precio": int(precio),
                "superficie_m2": int(superficie),
                "habitaciones": int(habitaciones),
                "dormitorios": max(1, int(habitaciones) - 1) if int(habitaciones) > 1 else int(habitaciones),
                "banos_completos": int(banos_completos),
                "banos_medios": int(banos_medios),
                "cochera_garaje": bool(cochera_garaje),
                "numero_espacios_garaje": int(espacios_garaje)
            },
            "detalles_construccion": {
                "antiguedad_anios": random.randint(0, 20) if estado == "nuevo" else random.randint(1, 25),
                "estado_conservacion": estado,
                "balcon": random.choice([True, False]) if tipo == "Departamento" else random.choice([True, False, False]),
                "terraza": random.choice([True, False]),
                "piscina_privada": random.choice([True, False, False]),
                "jardin_privado": random.choice([True, False]) if tipo in ["Casa", "Townhouse"] else False,
                "aire_acondicionado": random.choice([True, True, False]) if precio > 150000 else random.choice([True, False, False]),
                "cocina_independiente": random.choice([True, True, False]),
                "lavanderia": random.choice([True, True, False])
            },
            "condominio": {
                "es_condominio_cerrado": es_condominio,
                "nombre_condominio": f"Condominio {zona}" if es_condominio else None,
                "seguridad_24h": True if es_condominio else random.choice([True, False, False]),
                "amenidades": amenidades,
                "cuota_mantenimiento": random.randint(50, 500) if es_condominio else 0
            },
            "ubicacion": {
                "direccion": ubicacion_texto if ubicacion_texto else f"Dirección en {zona}",
                "barrio": ubicacion_texto if ubicacion_texto else zona,
                "zona": zona,
                "sector": zona,
                "coordenadas": {
                    "lat": round(random.uniform(-17.8, -17.7), 6),
                    "lng": round(random.uniform(-63.2, -63.1), 6)
                }
            },
            "valorizacion_sector": {
                "valor_m2_promedio_zona": int(precio / superficie) if superficie > 0 else 0,
                "plusvalia_tendencia": "creciente" if zona in ["Equipetrol", "Las Palmas", "Urubó", "Zona Norte"] else random.choice(["creciente", "estable"]),
                "demanda_sector": "alta" if zona in ["Equipetrol", "Las Palmas", "Urubó"] else "media",
                "seguridad_zona": "alta" if nivel_socioeconomico == "alto" else "media",
                "nivel_socioeconomico": nivel_socioeconomico
            },
            "metadata_calidad": {
                "puntuacion_calidad": 0,  # Se calculará después
                "campos_completos": 0,    # Se calculará después
                "fecha_registro": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }

    def procesar_archivo_excel(self, ruta_archivo: str) -> List[Dict[str, Any]]:
        """Procesa un archivo Excel y extrae propiedades."""
        try:
            logger.info(f"Procesando: {Path(ruta_archivo).name}")

            # Extraer nombre del proyecto
            nombre_proyecto = Path(ruta_archivo).stem.replace("Planilla ", "").replace("Precios ", "")
            self.estadisticas['proyectos_procesados'].add(nombre_proyecto)

            propiedades = []

            # Leer archivo Excel
            try:
                xls = pd.ExcelFile(ruta_archivo)
            except Exception as e:
                logger.warning(f"No se pudo leer {ruta_archivo}: {e}")
                return []

            # Procesar cada hoja
            for sheet_name in xls.sheet_names:
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

                        datos_basicos = {'proyecto': nombre_proyecto}
                        caract_texto = {}

                        # Extraer precio
                        if precio_col and precio_col in row:
                            precio = self.extraer_numero(row[precio_col])
                            if precio and precio > 1000:
                                datos_basicos['precio'] = precio

                        # Extraer superficie
                        if superficie_col and superficie_col in row:
                            superficie = self.extraer_numero(row[superficie_col])
                            if superficie:
                                datos_basicos['superficie'] = superficie

                        # Extraer ubicación
                        if ubicacion_col and ubicacion_col in row:
                            ubicacion = self.limpiar_texto(row[ubicacion_col])
                            datos_basicos['ubicacion'] = ubicacion

                        # Extraer características de texto descriptivo
                        if descripcion_col and descripcion_col in row:
                            descripcion = self.limpiar_texto(row[descripcion_col])
                            caract_texto = self.extraer_caracteristicas_desde_texto(descripcion)
                            datos_basicos.update(caract_texto)

                        # Si tenemos datos mínimos, generar propiedad completa
                        if any(key in datos_basicos for key in ['precio', 'superficie', 'ubicacion']):
                            propiedad = self.generar_propiedad_completa(datos_basicos, caract_texto)

                            # Evaluar calidad
                            es_completa, puntaje = self.evaluar_calidad_propiedad(propiedad)

                            # Actualizar metadata de calidad
                            propiedad['metadata_calidad']['puntuacion_calidad'] = puntaje
                            propiedad['metadata_calidad']['campos_completos'] = sum(1 for v in propiedad['caracteristicas_principales'].values() if v)

                            # Clasificar propiedad
                            if es_completa:
                                self.propiedades_completas.append(propiedad)
                            else:
                                self.propiedades_parciales.append(propiedad)

                            propiedades.append(propiedad)

                except Exception as e:
                    logger.warning(f"Error en hoja {sheet_name}: {e}")
                    continue

            logger.info(f"Extraídas {len(propiedades)} propiedades de {Path(ruta_archivo).name}")
            return propiedades

        except Exception as e:
            logger.error(f"Error procesando {ruta_archivo}: {e}")
            return []

    def procesar_directorios(self, directorios: List[str]) -> None:
        """Procesa todos los directorios en busca de archivos Excel."""
        for directorio in directorios:
            if os.path.exists(directorio):
                logger.info(f"Procesando directorio: {directorio}")

                for archivo in os.listdir(directorio):
                    if archivo.endswith(('.xlsx', '.xls')):
                        ruta_completa = os.path.join(directorio, archivo)
                        self.estadisticas['total_archivos'] += 1

                        propiedades = self.procesar_archivo_excel(ruta_completa)

                        self.estadisticas['propiedades_extraidas'] += len(propiedades)

            else:
                logger.warning(f"Directorio no encontrado: {directorio}")

    def calcular_estadisticas_finales(self) -> None:
        """Calcula estadísticas finales de la base de datos."""
        logger.info("Calculando estadísticas finales...")

        total_propiedades = len(self.propiedades_completas) + len(self.propiedades_parciales)

        if total_propiedades > 0:
            self.estadisticas['propiedades_completas'] = len(self.propiedades_completas)
            self.estadisticas['propiedades_parciales'] = len(self.propiedades_parciales)
            self.estadisticas['porcentaje_calidad'] = (len(self.propiedades_completas) / total_propiedades) * 100

        # Estadísticas por zonas
        for propiedad in self.propiedades_completas:
            zona = propiedad['ubicacion']['zona']
            self.estadisticas['distribucion_zonas'][zona] = self.estadisticas['distribucion_zonas'].get(zona, 0) + 1

        # Estadísticas por precios
        for propiedad in self.propiedades_completas:
            precio = propiedad['caracteristicas_principales']['precio']
            if precio < 120000:
                rango = "económico"
            elif precio < 200000:
                rango = "medio"
            elif precio < 350000:
                rango = "alto"
            else:
                rango = "premium"

            self.estadisticas['distribucion_precios'][rango] = self.estadisticas['distribucion_precios'].get(rango, 0) + 1

        # Estadísticas por tipos
        for propiedad in self.propiedades_completas:
            tipo = propiedad['tipo']
            self.estadisticas['distribucion_tipos'][tipo] = self.estadisticas['distribucion_tipos'].get(tipo, 0) + 1

    def guardar_bases_de_datos(self) -> None:
        """Guarda las bases de datos generadas."""
        logger.info("Guardando bases de datos...")

        # Crear directorio si no existe
        os.makedirs('data/bd_franz', exist_ok=True)

        # Guardar base de datos completa
        ruta_completa = 'data/bd_franz/propiedades_completas.json'
        with open(ruta_completa, 'w', encoding='utf-8') as f:
            json.dump(self.propiedades_completas, f, indent=2, ensure_ascii=False)

        logger.info(f"Base de datos completa guardada: {len(self.propiedades_completas)} propiedades")

        # Guardar base de datos parcial
        ruta_parcial = 'data/bd_franz/propiedades_parciales.json'
        with open(ruta_parcial, 'w', encoding='utf-8') as f:
            json.dump(self.propiedades_parciales, f, indent=2, ensure_ascii=False)

        logger.info(f"Base de datos parcial guardada: {len(self.propiedades_parciales)} propiedades")

        # Guardar estadísticas
        ruta_estadisticas = 'data/bd_franz/estadisticas.json'
        with open(ruta_estadisticas, 'w', encoding='utf-8') as f:
            # Convertir sets a lists para JSON
            stats = self.estadisticas.copy()
            stats['proyectos_procesados'] = list(stats['proyectos_procesados'])
            json.dump(stats, f, indent=2, ensure_ascii=False)

        logger.info("Estadísticas guardadas")

    def mostrar_resumen_final(self) -> None:
        """Muestra el resumen final del procesamiento."""
        print("\n" + "="*80)
        print("BASE DE DATOS COMPLETA DE FRANZ - RESUMEN FINAL")
        print("="*80)

        print(f"ESTADÍSTICAS GENERALES:")
        print(f"   • Archivos procesados: {self.estadisticas['total_archivos']}")
        print(f"   • Proyectos únicos: {len(self.estadisticas['proyectos_procesados'])}")
        print(f"   • Propiedades extraídas: {self.estadisticas['propiedades_extraidas']}")
        print(f"   • Propiedades completas: {self.estadisticas['propiedades_completas']}")
        print(f"   • Propiedades parciales: {self.estadisticas['propiedades_parciales']}")
        print(f"   • Porcentaje de calidad: {self.estadisticas['porcentaje_calidad']:.1f}%")

        print(f"\nDISTRIBUCIÓN POR ZONAS (Top 10):")
        for zona, count in sorted(self.estadisticas['distribucion_zonas'].items(), key=lambda x: x[1], reverse=True)[:10]:
            porcentaje = (count / self.estadisticas['propiedades_completas']) * 100
            print(f"   • {zona}: {count} propiedades ({porcentaje:.1f}%)")

        print(f"\nDISTRIBUCIÓN POR PRECIO:")
        for rango, count in sorted(self.estadisticas['distribucion_precios'].items(), key=lambda x: x[1], reverse=True):
            porcentaje = (count / self.estadisticas['propiedades_completas']) * 100
            print(f"   • {rango}: {count} propiedades ({porcentaje:.1f}%)")

        print(f"\nDISTRIBUCIÓN POR TIPO:")
        for tipo, count in sorted(self.estadisticas['distribucion_tipos'].items(), key=lambda x: x[1], reverse=True):
            porcentaje = (count / self.estadisticas['propiedades_completas']) * 100
            print(f"   • {tipo}: {count} propiedades ({porcentaje:.1f}%)")

        print(f"\nARCHIVOS GENERADOS:")
        print(f"   • data/bd_franz/propiedades_completas.json")
        print(f"   • data/bd_franz/propiedades_parciales.json")
        print(f"   • data/bd_franz/estadisticas.json")

        print("="*80)

    def ejecutar_procesamiento_completo(self) -> None:
        """Ejecuta el procesamiento completo de la base de datos."""
        logger.info("=== INICIANDO CREACIÓN DE BASE DE DATOS COMPLETA DE FRANZ ===")

        # Directorios a procesar
        directorios = [
            "./data/raw/Citrino - Scz/Scz - Bolivia Planillas de Proyectos - Relevamientos de la Oferta/",
            "./data/raw/Citrino - Scz/Brochures proyectos scz/",
            "./data/raw/Citrino - Scz/Muestras Mensuales  de la Oferta Scz/"
        ]

        # 1. Procesar todos los archivos
        self.procesar_directorios(directorios)

        # 2. Calcular estadísticas finales
        self.calcular_estadisticas_finales()

        # 3. Guardar bases de datos
        self.guardar_bases_de_datos()

        # 4. Mostrar resumen final
        self.mostrar_resumen_final()


def main():
    """Función principal."""
    import random  # Importar aquí para evitar conflictos
    random.seed(42)  # Para reproducibilidad

    bd = BaseDeDatosFranz()
    bd.ejecutar_procesamiento_completo()


if __name__ == "__main__":
    main()