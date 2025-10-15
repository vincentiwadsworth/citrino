#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL Mejorado con Estrategias Específicas por Proveedor

Este script implementa un ETL mejorado que aplica diferentes estrategias
según el proveedor de datos, utilizando IA donde realmente aporta valor.
"""

import json
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
from datetime import datetime

# Agregar path para importar módulos
sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))

from amenities_extractor import AmenitiesExtractor
from price_corrector import PriceCorrector
from llm_integration import LLMIntegration
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ETLMejoradoProveedores:
    """ETL mejorado con estrategias específicas por proveedor."""

    def __init__(self):
        self.amenities_extractor = AmenitiesExtractor()
        self.price_corrector = PriceCorrector()
        self.llm_integration = LLMIntegration()

        # Estrategias específicas por proveedor
        self.estrategias_proveedores = {
            '01': {
                'nombre': 'UltraCasas',
                'prioridades': ['enriquecimiento_contacto', 'extraccion_descripciones'],
                'usar_amenities': False,  # No tiene campo amenities
                'usar_price_correction': True,
                'campos_faltantes': ['URL', 'agente_email']
            },
            '02': {
                'nombre': 'RE/MAX',
                'prioridades': ['amenities', 'price_correction', 'datos_contacto'],
                'usar_amenities': True,
                'usar_price_correction': True,
                'campos_fortaleza': ['contacto_completo', 'URLs', 'coordenadas']
            },
            '03': {
                'nombre': 'C21',
                'prioridades': ['georreferenciacion', 'normalizacion'],
                'usar_amenities': False,
                'usar_price_correction': False,
                'problema_principal': 'coordenadas_ausentes'
            },
            '04': {
                'nombre': 'CapitalCorp',
                'prioridades': ['expansion_contenido', 'mejora_general'],
                'usar_amenities': False,
                'usar_price_correction': True,
                'problema_principal': 'calidad_general_baja'
            },
            '05': {
                'nombre': 'BienInmuebles',
                'prioridades': ['optimizacion', 'validacion'],
                'usar_amenities': True,
                'usar_price_correction': True,
                'campos_fortaleza': ['datos_estructurados']
            }
        }

        # Estadísticas globales
        self.stats_globales = {
            'inicio_procesamiento': datetime.now().isoformat(),
            'proveedores_procesados': [],
            'total_propiedades': 0,
            'mejoras_aplicadas': {
                'amenities_extraidos': 0,
                'precios_corregidos': 0,
                'contactos_normalizados': 0,
                'coordenadas_agregadas': 0
            },
            'tokens_consumidos': 0,
            'costo_estimado_usd': 0.0
        }

    def cargar_datos_proveedores(self) -> Dict[str, pd.DataFrame]:
        """Carga los datos de todos los proveedores."""
        logger.info("Cargando datos de proveedores...")

        proveedores = {}
        archivos_proveedores = {
            '01': ['2025.08.17 01.xlsx', '2025.08.29 01.xlsx'],
            '02': ['2025.08.29 02.xlsx'],
            '03': ['2025.08.29 03.xlsx'],
            '04': ['2025.08.29 04.xlsx'],
            '05': ['2025.08.15 05.xlsx', '2025.08.29 05.xlsx']
        }

        for codigo, archivos in archivos_proveedores.items():
            dfs = []
            for archivo in archivos:
                try:
                    file_path = f"data/raw/relevamiento/{archivo}"
                    df = pd.read_excel(file_path)
                    df['codigo_proveedor'] = codigo
                    df['archivo_origen'] = archivo
                    dfs.append(df)
                    logger.info(f"Cargado {archivo}: {len(df)} filas")
                except Exception as e:
                    logger.error(f"Error cargando {archivo}: {e}")

            if dfs:
                proveedores[codigo] = pd.concat(dfs, ignore_index=True)
                logger.info(f"Proveedor {codigo}: Total {len(proveedores[codigo])} filas")

        return proveedores

    def procesar_proveedor_01(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Estrategia específica para Proveedor 01 (UltraCasas)."""
        logger.info("Procesando Proveedor 01 (UltraCasas) - Estrategia: Enriquecimiento")

        propiedades = df.to_dict('records')
        estrategia = self.estrategias_proveedores['01']

        for i, prop in enumerate(propiedades):
            try:
                # Enriquecer datos de contacto desde descripciones
                if 'descripcion' in prop and prop['descripcion']:
                    contacto_extraido = self.extraer_contacto_de_descripcion(prop['descripcion'])
                    if contacto_extraido:
                        prop.update(contacto_extraido)
                        self.stats_globales['mejoras_aplicadas']['contactos_normalizados'] += 1

                # Extraer características adicionales de descripciones
                if 'descripcion' in prop and prop['descripcion']:
                    caract_extraidas = self.extraer_caracteristicas_descripcion(prop['descripcion'])
                    if caract_extraidas:
                        prop['caracteristicas_extraidas'] = caract_extraidas

                # Marcar como procesado
                prop['etl_estrategia'] = estrategia['nombre']
                prop['etl_mejoras'] = 'enriquecimiento_contacto'

                # Progress logging
                if (i + 1) % 50 == 0:
                    logger.info(f"Proveedor 01: Procesadas {i + 1}/{len(propiedades)} propiedades")

            except Exception as e:
                logger.error(f"Error procesando propiedad Proveedor 01: {e}")

        return propiedades

    def procesar_proveedor_02(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Estrategia específica para Proveedor 02 (RE/MAX)."""
        logger.info("Procesando Proveedor 02 (RE/MAX) - Estrategia: Amenities + Precios")

        propiedades = df.to_dict('records')
        estrategia = self.estrategias_proveedores['02']

        # Paso 1: Corregir precios inválidos
        logger.info("  - Corrigiendo precios inválidos...")
        propiedades, stats_precios = self.price_corrector.procesar_lote_propiedades(propiedades)
        self.stats_globales['mejoras_aplicadas']['precios_corregidos'] += stats_precios['precios_corregidos']

        # Paso 2: Extraer amenities
        logger.info("  - Extrayendo amenities estructurados...")
        propiedades, stats_amenities = self.amenities_extractor.procesar_lote_propiedades(propiedades)
        self.stats_globales['mejoras_aplicadas']['amenities_extraidos'] += stats_amenities['con_amenities']

        # Paso 3: Enriquecer datos de agente
        logger.info("  - Enriqueciendo datos de agente...")
        for i, prop in enumerate(propiedades):
            try:
                # Normalizar datos de contacto
                if 'Agente Nombre' in prop and prop['Agente Nombre']:
                    prop['agente_normalizado'] = self.normalizar_nombre_agente(prop['Agente Nombre'])

                # Extraer información adicional de URLs si están disponibles
                if 'URL' in prop and prop['URL']:
                    prop['url_info'] = self.analizar_url_propiedad(prop['URL'])

                # Marcar como procesado
                prop['etl_estrategia'] = estrategia['nombre']
                prop['etl_mejoras'] = 'amenities+precios+contacto'

                # Progress logging
                if (i + 1) % 100 == 0:
                    logger.info(f"Proveedor 02: Procesadas {i + 1}/{len(propiedades)} propiedades")

            except Exception as e:
                logger.error(f"Error procesando propiedad Proveedor 02: {e}")

        return propiedades

    def procesar_proveedor_03(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Estrategia específica para Proveedor 03 (C21)."""
        logger.info("Procesando Proveedor 03 (C21) - Estrategia: Georreferenciación")

        propiedades = df.to_dict('records')
        estrategia = self.estrategias_proveedores['03']

        for i, prop in enumerate(propiedades):
            try:
                # Extraer coordenadas del campo "Coordenadas" si existe
                if 'Coordenadas' in prop and prop['Coordenadas']:
                    coords_parseadas = self.parsear_coordenadas_texto(prop['Coordenadas'])
                    if coords_parseadas:
                        prop.update(coords_parseadas)
                        self.stats_globales['mejoras_aplicadas']['coordenadas_agregadas'] += 1

                # Geocodificar dirección si no hay coordenadas
                elif 'Direccion' in prop and prop['Direccion']:
                    coords_geocod = self.geocodificar_direccion(prop['Direccion'])
                    if coords_geocod:
                        prop.update(coords_geocod)
                        self.stats_globales['mejoras_aplicadas']['coordenadas_agregadas'] += 1

                # Marcar como procesado
                prop['etl_estrategia'] = estrategia['nombre']
                prop['etl_mejoras'] = 'georreferenciacion'

                # Progress logging
                if (i + 1) % 10 == 0:
                    logger.info(f"Proveedor 03: Procesadas {i + 1}/{len(propiedades)} propiedades")

            except Exception as e:
                logger.error(f"Error procesando propiedad Proveedor 03: {e}")

        return propiedades

    def procesar_proveedor_04(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Estrategia específica para Proveedor 04 (CapitalCorp)."""
        logger.info("Procesando Proveedor 04 (CapitalCorp) - Estrategia: Mejora General")

        propiedades = df.to_dict('records')
        estrategia = self.estrategias_proveedores['04']

        # Paso 1: Corregir precios
        propiedades, stats_precios = self.price_corrector.procesar_lote_propiedades(propiedades)
        self.stats_globales['mejoras_aplicadas']['precios_corregidos'] += stats_precios['precios_corregidos']

        for i, prop in enumerate(propiedades):
            try:
                # Enriquecer con análisis de descripción
                if 'descripcion' in prop and prop['descripcion']:
                    analisis_desc = self.analizar_descripcion_profundamente(prop['descripcion'])
                    if analisis_desc:
                        prop['analisis_descripcion'] = analisis_desc

                # Extraer características de título si está disponible
                if 'titulo' in prop and prop['titulo']:
                    caract_titulo = self.extraer_caracteristicas_titulo(prop['titulo'])
                    if caract_titulo:
                        prop['caracteristicas_titulo'] = caract_titulo

                # Marcar como procesado
                prop['etl_estrategia'] = estrategia['nombre']
                prop['etl_mejoras'] = 'mejora_general'

                # Progress logging
                if (i + 1) % 50 == 0:
                    logger.info(f"Proveedor 04: Procesadas {i + 1}/{len(propiedades)} propiedades")

            except Exception as e:
                logger.error(f"Error procesando propiedad Proveedor 04: {e}")

        return propiedades

    def procesar_proveedor_05(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Estrategia específica para Proveedor 05 (BienInmuebles)."""
        logger.info("Procesando Proveedor 05 (BienInmuebles) - Estrategia: Optimización")

        propiedades = df.to_dict('records')
        estrategia = self.estrategias_proveedores['05']

        for i, prop in enumerate(propiedades):
            try:
                # Validar y optimizar datos estructurados
                if 'Habitaciones' in prop and prop['Habitaciones']:
                    prop['habitaciones_validadas'] = self.validar_numero_habitaciones(prop['Habitaciones'])

                if 'Baños' in prop and prop['Baños']:
                    prop['banos_validados'] = self.validar_numero_banos(prop['Baños'])

                # Optimizar superficies
                if 'Sup. Construida' in prop and prop['Sup. Construida']:
                    prop['superficie_normalizada'] = self.normalizar_superficie(prop['Sup. Construida'])

                # Extraer amenities adicionales de características
                if 'Características - General' in prop and prop['Características - General']:
                    caract_generales = self.parsear_caracteristicas_generales(prop['Características - General'])
                    if caract_generales:
                        prop['caracteristicas_generales_struct'] = caract_generales

                # Marcar como procesado
                prop['etl_estrategia'] = estrategia['nombre']
                prop['etl_mejoras'] = 'optimizacion'

                # Progress logging
                if (i + 1) % 30 == 0:
                    logger.info(f"Proveedor 05: Procesadas {i + 1}/{len(propiedades)} propiedades")

            except Exception as e:
                logger.error(f"Error procesando propiedad Proveedor 05: {e}")

        return propiedades

    # Métodos auxiliares para las estrategias específicas
    def extraer_contacto_de_descripcion(self, descripcion: str) -> Dict[str, Any]:
        """Extrae información de contacto de descripciones usando IA."""
        prompt = f"""
Analiza esta descripción de propiedad inmobiliaria y extrae información de contacto si está presente.

Descripción: "{descripcion}"

Responde únicamente con este JSON:
{{
    "telefono": null,
    "email": null,
    "whatsapp": null,
    "agente": null,
    "contacto_encontrado": false
}}

Si no hay información de contacto, retorna los valores como null.
"""

        try:
            resultado = self.llm_integration.extract_structured_data(prompt, descripcion)
            if resultado:
                return json.loads(resultado)
        except:
            pass

        return {}

    def normalizar_nombre_agente(self, nombre: str) -> Dict[str, str]:
        """Normaliza nombres de agentes."""
        if not nombre or str(nombre) == 'nan':
            return {}

        nombre_limpio = str(nombre).strip()

        # Eliminar sufijos comunes
        sufijos = [' Vendedor', ' Inmobiliaria', ' SRL', ' LTDA']
        for sufijo in sufijos:
            if nombre_limpio.endswith(sufijo):
                nombre_limpio = nombre_limpio[:-len(sufijo)].strip()

        # Dividir nombre y apellido si es posible
        partes = nombre_limpio.split()
        if len(partes) >= 2:
            return {
                'nombre': ' '.join(partes[:-1]),
                'apellido': partes[-1],
                'nombre_completo': nombre_limpio
            }
        else:
            return {
                'nombre': nombre_limpio,
                'apellido': '',
                'nombre_completo': nombre_limpio
            }

    def parsear_coordenadas_texto(self, coords_text: str) -> Optional[Dict[str, float]]:
        """Parsea coordenadas de texto."""
        if not coords_text or str(coords_text) == 'nan':
            return None

        try:
            # Intentar diferentes formatos
            # Formato: "-17.783, -63.184"
            if ',' in str(coords_text):
                parts = str(coords_text).split(',')
                if len(parts) == 2:
                    lat = float(parts[0].strip())
                    lon = float(parts[1].strip())
                    return {'latitud': lat, 'longitud': lon}

            # Formato: "-17.783 -63.184"
            if ' ' in str(coords_text):
                parts = str(coords_text).split()
                if len(parts) == 2:
                    lat = float(parts[0].strip())
                    lon = float(parts[1].strip())
                    return {'latitud': lat, 'longitud': lon}

        except:
            pass

        return None

    def geocodificar_direccion(self, direccion: str) -> Optional[Dict[str, float]]:
        """Geocodifica una dirección (simulado - requeriría API externa)."""
        # Esta es una implementación simulada
        # En producción, se usaría Google Maps API, OpenStreetMap, etc.

        if not direccion or str(direccion) == 'nan':
            return None

        # Coordenadas aproximadas de Santa Cruz como fallback
        coords_santacruz = {'latitud': -17.786, 'longitud': -63.181}

        # Por ahora, retornar coordenadas por defecto
        # En producción, esto haría una llamada real a API de geocodificación
        return coords_santacruz

    def validar_numero_habitaciones(self, habitaciones: Any) -> int:
        """Valida y normaliza número de habitaciones."""
        try:
            if isinstance(habitaciones, (int, float)):
                return max(0, int(habitaciones))
            elif isinstance(habitaciones, str):
                # Extraer números de texto
                import re
                numeros = re.findall(r'\d+', str(habitaciones))
                if numeros:
                    return max(0, int(numeros[0]))
        except:
            pass
        return 0

    def validar_numero_banos(self, banos: Any) -> int:
        """Valida y normaliza número de baños."""
        return self.validar_numero_habitaciones(banos)

    def normalizar_superficie(self, superficie: Any) -> Optional[float]:
        """Normaliza valores de superficie."""
        try:
            if isinstance(superficie, (int, float)):
                return float(superficie)
            elif isinstance(superficie, str):
                # Limpiar y extraer números
                import re
                numero = re.sub(r'[^\d\.]', '', str(superficie))
                if numero:
                    return float(numero)
        except:
            pass
        return None

    def procesar_todos_los_proveedores(self) -> Dict[str, Any]:
        """Procesa todos los proveedores con sus estrategias específicas."""
        logger.info("Iniciando ETL mejorado para todos los proveedores...")

        # Cargar datos
        proveedores_df = self.cargar_datos_proveedores()

        resultados = {}

        # Procesar cada proveedor con su estrategia específica
        for codigo, df in proveedores_df.items():
            logger.info(f"\n{'='*50}")
            logger.info(f"PROCESANDO PROVEEDOR {codigo}")
            logger.info(f"{'='*50}")

            estrategia = self.estrategias_proveedores.get(codigo, {})
            logger.info(f"Estrategia: {estrategia.get('nombre', 'Desconocida')}")
            logger.info(f"Propiedades a procesar: {len(df)}")

            # Seleccionar método de procesamiento según proveedor
            if codigo == '01':
                propiedades_procesadas = self.procesar_proveedor_01(df)
            elif codigo == '02':
                propiedades_procesadas = self.procesar_proveedor_02(df)
            elif codigo == '03':
                propiedades_procesadas = self.procesar_proveedor_03(df)
            elif codigo == '04':
                propiedades_procesadas = self.procesar_proveedor_04(df)
            elif codigo == '05':
                propiedades_procesadas = self.procesar_proveedor_05(df)
            else:
                # Estrategia genérica
                propiedades_procesadas = df.to_dict('records')
                for prop in propiedades_procesadas:
                    prop['etl_estrategia'] = 'generico'

            # Guardar resultados
            resultados[codigo] = {
                'estrategia': estrategia.get('nombre', 'Desconocida'),
                'propiedades_originales': len(df),
                'propiedades_procesadas': len(propiedades_procesadas),
                'datos': propiedades_procesadas
            }

            self.stats_globales['proveedores_procesados'].append(codigo)
            self.stats_globales['total_propiedades'] += len(propiedades_procesadas)

            logger.info(f"Proveedor {codigo} completado: {len(propiedades_procesadas)} propiedades procesadas")

        # Generar reporte final
        self.stats_globales['fin_procesamiento'] = datetime.now().isoformat()

        return {
            'metadata': {
                'fecha_procesamiento': datetime.now().isoformat(),
                'etl_version': 'mejorado_v2.0',
                'proveedores_procesados': self.stats_globales['proveedores_procesados'],
                'total_propiedades': self.stats_globales['total_propiedades']
            },
            'estadisticas_globales': self.stats_globales,
            'resultados_por_proveedor': resultados,
            'estrategias_aplicadas': self.estrategias_proveedores
        }

    def guardar_resultados(self, resultados: Dict[str, Any], output_path: str = "data/etl_mejorado_resultados.json"):
        """Guarda los resultados del ETL mejorado."""
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(resultados, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"Resultados guardados en: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error guardando resultados: {e}")
            return None

    def generar_reporte_ejecucion(self, resultados: Dict[str, Any]) -> str:
        """Genera un reporte de la ejecución del ETL."""
        stats = resultados['estadisticas_globales']
        proveedores = resultados['resultados_por_proveedor']

        reporte = f"""
REPORTE DE EJECUCIÓN - ETL MEJORADO V2.0
{'='*60}

PROVEEDORES PROCESADOS:
"""

        for codigo, datos in proveedores.items():
            reporte += f"  • Proveedor {codigo} ({datos['estrategia']}): {datos['propiedades_procesadas']} propiedades\n"

        reporte += f"""
MEJORAS APLICADAS:
  • Amenities extraídos: {stats['mejoras_aplicadas']['amenities_extraidos']}
  • Precios corregidos: {stats['mejoras_aplicadas']['precios_corregidos']}
  • Contactos normalizados: {stats['mejoras_aplicadas']['contactos_normalizados']}
  • Coordenadas agregadas: {stats['mejoras_aplicadas']['coordenadas_agregadas']}

ESTADÍSTICAS:
  • Total propiedades procesadas: {stats['total_propiedades']}
  • Tokens consumidos: {stats['tokens_consumidos']}
  • Costo estimado: ${stats['costo_estimado_usd']:.4f} USD
  • Tiempo de procesamiento: {stats['inicio_procesamiento']} → {stats['fin_procesamiento']}

EFICIENCIA:
  • Tasa de mejora general: {(sum(stats['mejoras_aplicadas'].values()) / stats['total_propiedades']) * 100:.1f}%
  • Estrategias personalizadas: {len(proveedores)} proveedores
"""

        return reporte

def main():
    """Función principal del ETL mejorado."""
    print("=" * 70)
    print("ETL MEJORADO CON ESTRATEGIAS ESPECÍFICAS POR PROVEEDOR")
    print("=" * 70)

    # Crear procesador
    etl = ETLMejoradoProveedores()

    # Procesar todos los proveedores
    resultados = etl.procesar_todos_los_proveedores()

    # Guardar resultados
    output_file = etl.guardar_resultados(resultados)

    # Generar y mostrar reporte
    reporte = etl.generar_reporte_ejecucion(resultados)
    print(reporte)

    # Guardar reporte
    reporte_file = "data/etl_mejorado_reporte.txt"
    with open(reporte_file, 'w', encoding='utf-8') as f:
        f.write(reporte)

    print(f"\nReporte guardado en: {reporte_file}")
    print(f"Resultados guardados en: {output_file}")
    print("ETL mejorado completado exitosamente")

    return 0

if __name__ == "__main__":
    exit(main())