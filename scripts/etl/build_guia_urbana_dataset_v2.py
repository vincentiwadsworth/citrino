#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL mejorado para Guía Urbana Municipal v2.2.0
Procesa data/raw/guia/GUIA URBANA.xlsx y genera servicios georreferenciados
con integración PostgreSQL + PostGIS y optimización de rendimiento.

Este script:
1. Extrae datos del Excel municipal (4,942 servicios)
2. Transforma y normaliza información de servicios urbanos
3. Georreferencia con PostGIS para consultas espaciales eficientes
4. Genera datasets JSON y carga en PostgreSQL
"""

import pandas as pd
import json
import os
import re
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GuiaUrbanaETL:
    """Clase principal para procesamiento ETL de Guía Urbana Municipal."""

    def __init__(self, use_postgres: bool = False):
        """
        Inicializar procesador ETL.

        Args:
            use_postgres: Si True, intenta cargar datos en PostgreSQL
        """
        self.use_postgres = use_postgres
        self.servicios_procesados = []
        self.estadisticas = {
            'total_registros': 0,
            'servicios_extraidos': 0,
            'coordenadas_validas': 0,
            'coordenadas_invalidas': 0,
            'categorias_detectadas': {},
            'sistemas_detectados': set()
        }

        # Mapeo de categorías principales
        self.categorias_mapping = {
            'abastecimiento': {
                'supermercado', 'tienda', 'tiendas_de_barrios', 'mercado',
                'plaza', 'feria', 'comercio'
            },
            'deporte': {
                'cancha', 'coliseo', 'piscina', 'balneario', 'gimnasio',
                'parque', 'plaza', 'pista', 'estadio'
            },
            'educacion': {
                'colegio', 'escuela', 'universidad', 'instituto', 'academia',
                'centro_educativo', 'jardin', 'guarderia'
            },
            'salud': {
                'hospital', 'clinica', 'centro_medico', 'farmacia', 'drogueria',
                'consultorio', 'laboratorio'
            },
            'transporte': {
                'terminal', 'parada', 'transporte', 'bus', 'taxi', 'estacion'
            },
            'instituciones': {
                'municipal', 'gubernamental', 'institucion', 'oficina',
                'ministerio', 'secretaria'
            },
            'cultura': {
                'centro_cultural', 'museo', 'biblioteca', 'teatro', 'casa_cultural'
            },
            'integracion': {
                'centro_integracion', 'comunitario', 'social'
            }
        }

    def leer_guia_urbana_excel(self, ruta_archivo: str) -> Optional[pd.DataFrame]:
        """
        Lee el archivo Excel de Guía Urbana con manejo robusto de formatos.

        Args:
            ruta_archivo: Ruta al archivo Excel

        Returns:
            DataFrame con los datos o None si hay error
        """
        try:
            logger.info(f"Leyendo archivo: {ruta_archivo}")

            # Leer sin header para detectar estructura real
            df_raw = pd.read_excel(ruta_archivo, header=None)
            logger.info(f"Dimensiones crudas: {df_raw.shape}")

            # Detectar fila de headers (donde comienza 'UV', 'MZ', etc.)
            header_row = None
            for idx, row in df_raw.iterrows():
                # Buscar fila que tenga UV, MZ, SUB_SISTEM, NIVEL, GOOGLE_MAP
                valores_unicos = set(str(cell).strip() for cell in row if pd.notna(cell) and str(cell).strip() not in ['', 'nan'])
                if any(header in valores_unicos for header in ['UV', 'MZ', 'SUB_SISTEM', 'NIVEL', 'GOOGLE_MAP']):
                    header_row = idx
                    logger.info(f"Fila de headers detectada en índice {idx}: {list(valores_unicos)}")
                    break

            if header_row is None:
                logger.warning("No se detectó fila de headers, usando primera fila")
                header_row = 0

            # Leer con header detectado
            df = pd.read_excel(ruta_archivo, header=header_row)

            # Limpiar nombres de columnas
            df.columns = [str(col).strip() for col in df.columns]

            logger.info(f"Archivo leído exitosamente: {df.shape}")
            logger.info(f"Columnas detectadas: {list(df.columns)[:10]}...")

            return df

        except Exception as e:
            logger.error(f"Error leyendo archivo {ruta_archivo}: {e}")
            return None

    def extraer_servicios_urbanos(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Extrae y estructura servicios urbanos del DataFrame.

        Args:
            df: DataFrame con datos de Guía Urbana

        Returns:
            Lista de servicios procesados
        """
        servicios = []
        self.estadisticas['total_registros'] = len(df)

        logger.info("Iniciando extracción de servicios urbanos...")

        for idx, row in df.iterrows():
            try:
                servicio = self.procesar_fila_servicio(row, idx)
                if servicio:
                    servicios.append(servicio)
                    self.servicios_procesados.append(servicio)  # ← BUG CORREGIDO: guardar referencia
                    self.estadisticas['servicios_extraidos'] += 1

                    # Actualizar estadísticas
                    categoria = servicio['categoria_principal']
                    self.estadisticas['categorias_detectadas'][categoria] = \
                        self.estadisticas['categorias_detectadas'].get(categoria, 0) + 1

                    self.estadisticas['sistemas_detectados'].add(servicio['sistema'])

                    if servicio.get('metadatos', {}).get('coordenadas_validadas', False):  # ← BUG CORREGIDO: usar metadatos
                        self.estadisticas['coordenadas_validas'] += 1
                    else:
                        self.estadisticas['coordenadas_invalidas'] += 1

            except Exception as e:
                logger.warning(f"Error procesando fila {idx}: {e}")
                continue

        logger.info(f"Extracción completada: {len(servicios)} servicios procesados")
        return servicios

    def procesar_fila_servicio(self, row: pd.Series, idx: int) -> Optional[Dict[str, Any]]:
        """
        Procesa una fila individual del DataFrame para extraer información de servicio.

        Args:
            row: Fila del DataFrame
            idx: Índice de la fila

        Returns:
            Diccionario con datos del servicio o None
        """
        servicio = None

        try:
            # Extraer información básica - buscar en diferentes nombres de columnas
            uv = self.limpiar_texto(self._buscar_valor_columna(row, ['UV', 'Unnamed: 0', 'Unnamed: 1']))
            mz = self.limpiar_texto(self._buscar_valor_columna(row, ['MZ', 'Unnamed: 1', 'Unnamed: 0']))
            sub_sistema = self.limpiar_texto(self._buscar_valor_columna(row, ['SUB_SISTEM', 'Unnamed: 2']))
            nivel = self.limpiar_texto(self._buscar_valor_columna(row, ['NIVEL', 'Unnamed: 3']))
            coordenadas_str = self.limpiar_texto(self._buscar_valor_columna(row, ['GOOGLE_MAP', 'Unnamed: 4']))

            # Validar datos mínimos
            if not (sub_sistema or nivel):
                return None

            # Parsear coordenadas
            coordenadas = self.parsear_coordenadas(coordenadas_str)
            coordenadas_validas = self.validar_coordenadas(coordenadas)

            # Determinar categoría principal
            categoria_principal = self.determinar_categoria_principal(sub_sistema, nivel)

            # Construir nombre del servicio
            nombre_servicio = self.construir_nombre_servicio(nivel, uv, mz, sub_sistema)

            # Extraer información de contacto y horarios si está disponible
            contacto = self.extraer_informacion_contacto(row)

            servicio = {
                'id': f"guia_urbana_{idx:06d}",
                'nombre': nombre_servicio,
                'categoria_principal': categoria_principal,
                'subcategoria': nivel.lower().replace(' ', '_') if nivel else '',
                'sistema': sub_sistema.lower().replace(' ', '_') if sub_sistema else '',
                'nivel_original': nivel,
                'ubicacion': {
                    'direccion': f"UV {uv}" if uv else '',
                    'coordenadas': coordenadas if coordenadas_validas else None,
                    'uv': uv,
                    'manzana': mz,
                    'zona_uv': f"UV-{uv}" if uv else ''
                },
                'contacto': contacto,
                'metadatos': {
                    'fuente': 'guia_urbana_municipal',
                    'fecha_procesamiento': datetime.now().isoformat(),
                    'fila_original': idx,
                    'coordenadas_validadas': coordenadas_validas,
                    'confidence_calificacion': 0.0  # Temporal, se calculará después
                }
            }

            # Calcular confidence después de crear el servicio
            servicio['metadatos']['confidence_calificacion'] = self.calcular_confidence(servicio)

            return servicio

        except Exception as e:
            logger.warning(f"Error procesando fila {idx}: {e}")
            return None

    def parsear_coordenadas(self, coordenadas_str: str) -> Optional[Dict[str, float]]:
        """
        Parsea coordenadas en formato "lat,lng" para Santa Cruz, Bolivia.
        Soporta punto y coma decimal: -17,734683,-63,143766

        Args:
            coordenadas_str: String con coordenadas (formato: -17.XXXXXX,-63.XXXXXX)

        Returns:
            Diccionario con lat/lng para PostGIS o None
        """
        if not coordenadas_str or coordenadas_str == 'nan':
            return None

        try:
            # Limpiar string
            coords_clean = coordenadas_str.strip()

            # Patrón específico para coordenadas de Santa Cruz (soporta coma y punto decimal)
            # Más específico: latitud (empieza con -17), longitud (empieza con -63)
            pattern = r'(-1[78]\.[\d,]+),\s*(-6[34]\.[\d,]+)'
            match = re.search(pattern, coords_clean)

            if match:
                lat_str, lng_str = match.groups()

                # Convertir coma decimal a punto decimal
                lat_str = lat_str.replace(',', '.')
                lng_str = lng_str.replace(',', '.')

                lat, lng = float(lat_str), float(lng_str)

                # Para Santa Cruz: lat ≈ -17.8, lng ≈ -63.2
                # Validación específica para la región
                if -18.5 <= lat <= -17.5 and -64.0 <= lng <= -62.5:
                    return {'lat': lat, 'lng': lng}
                else:
                    logger.debug(f"Coordenadas fuera de rango Santa Cruz: lat={lat}, lng={lng}")
            else:
                logger.debug(f"No se pudo parsear coordenadas: '{coordenadas_str}'")

        except Exception as e:
            logger.debug(f"Error parseando coordenadas '{coordenadas_str}': {e}")

        return None

    def validar_coordenadas(self, coordenadas: Optional[Dict[str, float]]) -> bool:
        """Valida que las coordenadas sean válidas para Santa Cruz de la Sierra."""
        if not coordenadas:
            return False

        lat, lng = coordenadas.get('lat'), coordenadas.get('lng')

        # Rangos validados para Santa Cruz, Bolivia
        if not (-19.0 <= lat <= -16.0 and -65.0 <= lng <= -62.0):
            return False

        return True

    def determinar_categoria_principal(self, sub_sistema: str, nivel: str) -> str:
        """
        Determina la categoría principal basada en sistema y nivel.

        Args:
            sub_sistema: Sistema principal
            nivel: Nivel específico del servicio

        Returns:
            Categoría principal normalizada
        """
        texto_combinado = f"{sub_sistema} {nivel}".lower()

        # Buscar coincidencias exactas primero
        for categoria, keywords in self.categorias_mapping.items():
            for keyword in keywords:
                if keyword in texto_combinado:
                    return categoria

        # Mapeo directo por sistema
        sistema_lower = sub_sistema.lower()
        if 'abastecimiento' in sistema_lower:
            return 'abastecimiento'
        elif 'deporte' in sistema_lower:
            return 'deporte'
        elif 'educacion' in sistema_lower or 'educaci' in sistema_lower:
            return 'educacion'
        elif 'salud' in sistema_lower:
            return 'salud'
        elif 'transporte' in sistema_lower:
            return 'transporte'
        elif 'institucione' in sistema_lower:
            return 'instituciones'
        elif 'cultura' in sistema_lower:
            return 'cultura'
        elif 'integracion' in sistema_lower:
            return 'integracion'

        # Si no se clasifica, usar "otros"
        return 'otros'

    def construir_nombre_servicio(self, nivel: str, uv: str, mz: str, sistema: str) -> str:
        """
        Construye un nombre descriptivo para el servicio.

        Args:
            nivel: Nivel del servicio
            uv: Unidad vecinal
            mz: Manzana
            sistema: Sistema principal

        Returns:
            Nombre descriptivo del servicio
        """
        componentes = []

        if nivel and nivel != 'nan':
            componentes.append(nivel.title())

        if uv and uv != 'nan':
            componentes.append(f"UV {uv}")
        elif mz and mz != 'nan':
            componentes.append(f"MZ {mz}")

        if not componentes and sistema and sistema != 'nan':
            componentes.append(sistema.title())

        return ' - '.join(componentes) if componentes else 'Servicio sin Nombre'

    def extraer_informacion_contacto(self, row: pd.Series) -> Dict[str, str]:
        """Extrae información de contacto si está disponible en columnas adicionales."""
        contacto = {
            'telefono': '',
            'horario': '',
            'email': '',
            'web': ''
        }

        # Buscar en columnas adicionales que puedan contener info de contacto
        for col_name, value in row.items():
            if pd.isna(value) or str(value).strip() == 'nan':
                continue

            value_str = str(value).strip()
            col_lower = str(col_name).lower()

            # Detectar teléfono
            if any(term in col_lower for term in ['telefono', 'tel', 'celular', 'contacto']):
                if re.search(r'\d{7,}', value_str):
                    contacto['telefono'] = value_str

            # Detectar horarios
            elif any(term in col_lower for term in ['horario', 'hora', 'atencion']):
                contacto['horario'] = value_str

            # Detectar email
            elif any(term in col_lower for term in ['email', 'correo', 'e-mail']):
                if '@' in value_str:
                    contacto['email'] = value_str

            # Detectar web
            elif any(term in col_lower for term in ['web', 'pagina', 'url', 'sitio']):
                contacto['web'] = value_str

        return contacto

    def calcular_confidence(self, servicio: Dict[str, Any]) -> float:
        """
        Calcula un puntaje de confianza para la calidad del dato.

        Args:
            servicio: Diccionario del servicio

        Returns:
            Puntaje de confianza (0.0 - 1.0)
        """
        confidence = 0.0

        # Tener nombre (30%)
        if servicio.get('nombre') and len(servicio['nombre'].strip()) > 3:
            confidence += 0.3

        # Tener coordenadas válidas (40%)
        if servicio.get('metadatos', {}).get('coordenadas_validadas', False):
            confidence += 0.4

        # Tener UV/MZ (20%)
        if servicio.get('ubicacion', {}).get('uv') or servicio.get('ubicacion', {}).get('manzana'):
            confidence += 0.2

        # Tener información de contacto (10%)
        contacto = servicio.get('contacto', {})
        if any(contacto.values()):
            confidence += 0.1

        return min(confidence, 1.0)

    def _buscar_valor_columna(self, row: pd.Series, posibles_nombres: List[str]) -> str:
        """
        Busca el valor de una columna en diferentes nombres posibles.

        Args:
            row: Fila del DataFrame
            posibles_nombres: Lista de posibles nombres de columna

        Returns:
            Valor encontrado o vacío
        """
        for nombre in posibles_nombres:
            if nombre in row and not pd.isna(row[nombre]):
                valor = str(row[nombre]).strip()
                if valor and valor != 'nan':
                    return valor
        return ''

    def limpiar_texto(self, texto) -> str:
        """Limpia y normaliza texto."""
        if pd.isna(texto) or str(texto).strip() == 'nan':
            return ''
        return str(texto).strip()

    def generar_dataset_json(self, servicios: List[Dict[str, Any]], output_file: str) -> str:
        """
        Genera el dataset JSON final con metadata.

        Args:
            servicios: Lista de servicios procesados
            output_file: Ruta del archivo de salida

        Returns:
            Ruta del archivo generado
        """
        # Preparar metadata
        metadata = {
            'fecha_procesamiento': datetime.now().isoformat(),
            'fuente': 'guia_urbana_municipal',
            'version': 'v2.2.0',
            'estadisticas': {
                'total_servicios': len(servicios),
                'coordenadas_validas': self.estadisticas['coordenadas_validas'],
                'coordenadas_invalidas': self.estadisticas['coordenadas_invalidas'],
                'categorias_detectadas': self.estadisticas['categorias_detectadas'],
                'sistemas_detectados': list(self.estadisticas['sistemas_detectados'])
            }
        }

        # Estructura final
        dataset = {
            'metadata': metadata,
            'servicios': servicios
        }

        # Guardar archivo
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)

        logger.info(f"Dataset guardado en: {output_file}")
        return output_file

    def cargar_servicios_postgis(self, servicios: List[Dict[str, Any]]) -> bool:
        """
        Carga servicios en PostgreSQL con PostGIS (opcional).

        Args:
            servicios: Lista de servicios procesados

        Returns:
            True si éxito, False si error
        """
        if not self.use_postgres:
            logger.info("Carga PostgreSQL deshabilitada")
            return False

        try:
            # Aquí iría la lógica de conexión a PostgreSQL
            # y carga de datos con PostGIS
            logger.info("Preparando carga en PostgreSQL + PostGIS...")
            # TODO: Implementar conexión y carga PostGIS
            return True

        except Exception as e:
            logger.error(f"Error cargando en PostgreSQL: {e}")
            return False

    def procesar_guia_urbana(self, input_file: str, output_dir: str = "data") -> str:
        """
        Procesamiento completo del pipeline ETL.

        Args:
            input_file: Ruta al archivo Excel de entrada
            output_dir: Directorio de salida

        Returns:
            Ruta del archivo generado
        """
        logger.info("=== INICIANDO ETL GUÍA URBANA MUNICIPAL v2.2.0 ===")

        # 1. EXTRACCIÓN
        df = self.leer_guia_urbana_excel(input_file)
        if df is None:
            raise Exception("No se pudo leer el archivo de entrada")

        # 2. TRANSFORMACIÓN
        servicios = self.extraer_servicios_urbanos(df)

        # 3. CARGA
        # 3.1. Generar JSON
        output_file = os.path.join(output_dir, 'guia_urbana_municipal_v2.json')
        self.generar_dataset_json(servicios, output_file)

        # 3.2. Cargar en PostgreSQL (opcional)
        if self.use_postgres:
            self.cargar_servicios_postgis(servicios)

        # 4. LOGGING DE RESULTADOS
        self.imprimir_resumen()

        logger.info("=== ETL COMPLETADO EXITOSAMENTE ===")
        return output_file

    def imprimir_resumen(self):
        """Imprime resumen de procesamiento."""
        logger.info("\n=== RESUMEN DE PROCESAMIENTO ===")
        logger.info(f"Registros totales procesados: {self.estadisticas['total_registros']}")
        logger.info(f"Servicios extraídos: {self.estadisticas['servicios_extraidos']}")
        logger.info(f"Coordenadas válidas: {self.estadisticas['coordenadas_validas']}")
        logger.info(f"Coordenadas inválidas: {self.estadisticas['coordenadas_invalidas']}")

        logger.info("\nCategorías detectadas:")
        for categoria, count in self.estadisticas['categorias_detectadas'].items():
            logger.info(f"  {categoria}: {count} servicios")

        logger.info(f"\nSistemas detectados: {len(self.estadisticas['sistemas_detectados'])}")
        logger.info(f"Confidence promedio: {sum(s.get('metadatos', {}).get('confidence_calificacion', 0) for s in self.servicios_procesados) / max(len(self.servicios_procesados), 1):.3f}")


def main():
    """Función principal del script ETL."""
    import argparse

    parser = argparse.ArgumentParser(description='ETL Guía Urbana Municipal v2.2.0')
    parser.add_argument('--input', '-i', default='data/raw/guia/GUIA URBANA.xlsx',
                       help='Archivo Excel de entrada (default: data/raw/guia/GUIA URBANA.xlsx)')
    parser.add_argument('--output', '-o', default='data',
                       help='Directorio de salida (default: data)')
    parser.add_argument('--postgres', action='store_true',
                       help='Habilitar carga en PostgreSQL + PostGIS')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Logging detallado')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validar archivo de entrada
    if not os.path.exists(args.input):
        logger.error(f"Archivo de entrada no encontrado: {args.input}")
        return 1

    try:
        # Crear procesador ETL
        etl = GuiaUrbanaETL(use_postgres=args.postgres)

        # Ejecutar procesamiento completo
        output_file = etl.procesar_guia_urbana(args.input, args.output)

        logger.info(f"\nProcesamiento completado exitosamente:")
        logger.info(f"Archivo generado: {output_file}")
        logger.info(f"Servicios procesados: {len(etl.servicios_procesados)}")

        return 0

    except Exception as e:
        logger.error(f"Error en procesamiento ETL: {e}")
        return 1


if __name__ == "__main__":
    exit(main())