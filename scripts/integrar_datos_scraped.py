#!/usr/bin/env python3
"""
Script para integrar datos scrapeados con la base de datos de Franz.
"""

import json
import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Any
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegradorDatosScrapeados:
    """Clase para integrar datos scrapeados con la base de datos de Franz."""

    def __init__(self):
        self.propiedades_franz = []
        self.propiedades_scraped = []
        self.propiedades_integradas = []
        self.estadisticas = {
            'total_franz': 0,
            'total_scraped': 0,
            'total_integradas': 0,
            'duplicados': 0,
            'fuente_scraped': {}
        }

    def cargar_propiedades_franz(self) -> None:
        """Carga las propiedades de Franz desde la base de datos completa."""
        logger.info("Cargando propiedades de Franz...")

        with open('data/bd_franz/propiedades_completas.json', 'r', encoding='utf-8') as f:
            self.propiedades_franz = json.load(f)

        self.estadisticas['total_franz'] = len(self.propiedades_franz)
        logger.info(f"Cargadas {self.estadisticas['total_franz']} propiedades de Franz")

    def procesar_archivo_scraped(self, archivo: str, fuente: str) -> List[Dict[str, Any]]:
        """Procesa un archivo scrapeado y lo convierte al formato estándar."""
        logger.info(f"Procesando archivo: {archivo}")

        try:
            if archivo.endswith('.xlsx'):
                df = pd.read_excel(archivo)
            elif archivo.endswith('.csv'):
                df = pd.read_csv(archivo)
            else:
                logger.warning(f"Formato no soportado: {archivo}")
                return []

            propiedades = []

            for _, row in df.iterrows():
                propiedad = self.convertir_a_formato_estandar(row, fuente)
                if propiedad:
                    propiedades.append(propiedad)

            logger.info(f"Procesadas {len(propiedades)} propiedades de {fuente}")
            return propiedades

        except Exception as e:
            logger.error(f"Error procesando {archivo}: {str(e)}")
            return []

    def convertir_a_formato_estandar(self, row: pd.Series, fuente: str) -> Dict[str, Any]:
        """Convierte una fila scrapeada al formato estándar de Citrino."""

        try:
            # Extraer información básica
            titulo = self.extraer_campo(row, ['Titulo', 'Título', 'titulo', 'T�tulo'], '')
            precio = self.extraer_precio(row)
            ubicacion = self.extraer_ubicacion(row)
            descripcion = self.extraer_campo(row, ['Descripcion', 'Descripción', 'descripcion', 'Descripci�n'], '')

            # Extraer características específicas según la fuente
            caract_principales = self.extraer_caracteristicas_principales(row, fuente)
            detalles_scraping = self.extraer_detalles_scraping(row, fuente)

            # Crear propiedad en formato estándar
            propiedad = {
                'id': f"scraped_{fuente.lower().replace(' ', '_')}_{len(self.propiedades_scraped)}",
                'nombre': titulo,
                'fuente': f"scraping_{fuente}",
                'proyecto_origen': fuente,
                'caracteristicas_principales': caract_principales,
                'ubicacion': ubicacion,
                'descripcion': descripcion,
                'scraping_data': detalles_scraping,
                'fecha_integracion': datetime.now().isoformat()
            }

            return propiedad

        except Exception as e:
            logger.error(f"Error convirtiendo propiedad: {str(e)}")
            return None

    def extraer_campo(self, row: pd.Series, posibles_nombres: List[str], valor_defecto: Any) -> Any:
        """Extrae un campo de una fila buscando en múltiples posibles nombres."""
        for nombre in posibles_nombres:
            if nombre in row and pd.notna(row[nombre]):
                return row[nombre]
        return valor_defecto

    def extraer_precio(self, row: pd.Series) -> float:
        """Extrae el precio de una fila scrapeada."""
        precio_str = self.extraer_campo(row, ['Precio', 'precio'], '0')

        if isinstance(precio_str, str):
            # Limpiar el string de precio
            precio_str = precio_str.replace('$', '').replace(',', '').replace('.', '').strip()
            try:
                return float(precio_str)
            except:
                return 0.0
        elif isinstance(precio_str, (int, float)):
            return float(precio_str)
        else:
            return 0.0

    def extraer_ubicacion(self, row: pd.Series) -> Dict[str, Any]:
        """Extrae la ubicación de una fila scrapeada."""
        ubicacion_str = self.extraer_campo(row, ['Ubicacion', 'Ubicación', 'ubicaci�n'], '')

        # Extraer coordenadas
        latitud = self.extraer_campo(row, ['Latitud', 'latitud'], 0)
        longitud = self.extraer_campo(row, ['Longitud', 'longitud'], 0)

        # Determinar zona basado en la ubicación
        zona = self.determinar_zona(ubicacion_str)

        return {
            'zona': zona,
            'direccion': ubicacion_str,
            'coordenadas': {
                'lat': float(latitud) if latitud else 0,
                'lng': float(longitud) if longitud else 0
            }
        }

    def determinar_zona(self, ubicacion_str: str) -> str:
        """Determina la zona basado en la cadena de ubicación."""
        ubicacion_lower = ubicacion_str.lower()

        zonas_mapping = {
            'equipetrol': ['equipetrol', 'equi'],
            'las palmas': ['las palmas', 'palmas'],
            'urubó': ['urubó', 'urubo', 'urubo'],
            'norte': ['norte', 'zona norte'],
            'sirari': ['sirari'],
            'los cusis': ['los cusis', 'cusis'],
            'centro': ['centro', 'downtown'],
        }

        for zona, keywords in zonas_mapping.items():
            for keyword in keywords:
                if keyword in ubicacion_lower:
                    return zona

        return 'Otra'

    def extraer_caracteristicas_principales(self, row: pd.Series, fuente: str) -> Dict[str, Any]:
        """Extrae características principales según la fuente."""
        caract = {
            'precio': self.extraer_precio(row),
            'superficie_m2': 0,
            'habitaciones': 0,
            'dormitorios': 0,
            'banos_completos': 0,
            'banos_medios': 0,
            'cochera_garaje': False,
            'numero_espacios_garaje': 0
        }

        # Extraer superficie
        superficie = self.extraer_campo(row, ['Sup. Construida', 'Sup. Terreno', 'Superficie'], 0)
        if superficie:
            try:
                caract['superficie_m2'] = float(superficie)
            except:
                pass

        # Extraer habitaciones
        habitaciones = self.extraer_campo(row, ['Habitaciones', 'Dormitorios'], 0)
        if habitaciones:
            try:
                caract['habitaciones'] = int(habitaciones)
                caract['dormitorios'] = int(habitaciones)
            except:
                pass

        # Extraer baños
        banos = self.extraer_campo(row, ['Baños', 'Banos'], 0)
        if banos:
            try:
                caract['banos_completos'] = int(banos)
            except:
                pass

        # Extraer garajes
        garajes = self.extraer_campo(row, ['Garajes', 'Garage'], 0)
        if garajes:
            try:
                caract['numero_espacios_garaje'] = int(garajes)
                caract['cochera_garaje'] = True
            except:
                pass

        return caract

    def extraer_detalles_scraping(self, row: pd.Series, fuente: str) -> Dict[str, Any]:
        """Extrae detalles específicos del scraping."""
        detalles = {
            'fuente_web': fuente,
            'fecha_scraping': self.extraer_campo(row, ['Actualizado', 'Vigencia'], ''),
            'url_original': self.extraer_campo(row, ['URL', 'Link', 'url'], ''),
            'agente': self.extraer_campo(row, ['Agente', 'Agente Nombre'], ''),
            'agencia': self.extraer_campo(row, ['Agencia'], ''),
            'telefono': self.extraer_campo(row, ['Telefono', 'Teléfono', 'teléfono'], ''),
            'descripcion_completa': self.extraer_campo(row, ['Descripcion', 'Descripción', 'descripcion', 'Descripci�n'], ''),
            'detalles_adicionales': {}
        }

        # Extraer campos adicionales según la fuente
        for col in row.index:
            if col not in ['Titulo', 'Título', 'titulo', 'Precio', 'Ubicacion', 'Ubicación',
                          'Descripcion', 'Descripción', 'Latitud', 'Longitud', 'URL', 'Link',
                          'Agente', 'Agente Nombre', 'Agencia', 'Telefono', 'Teléfono']:
                if pd.notna(row[col]):
                    detalles['detalles_adicionales'][col] = str(row[col])

        return detalles

    def cargar_datos_scraped(self) -> None:
        """Carga y procesa todos los archivos scrapeados."""
        logger.info("Cargando datos scrapeados...")

        directorio_scraped = "data/raw/scrapped"
        fuentes = {
            'Bien Inmuebles': ['bieninmuebles_casa_', 'bieninmuebles_departamento_'],
            'C21': ['propiedades_c21_'],
            'Remax': ['propiedades_remax_'],
            'Capital Corp': ['capitalcorp_'],
            'Ultracasas': ['ultracasas_']
        }

        for fuente, prefijos in fuentes.items():
            ruta_fuente = os.path.join(directorio_scraped, fuente)

            if os.path.exists(ruta_fuente):
                archivos = os.listdir(ruta_fuente)

                for archivo in archivos:
                    if any(prefijo in archivo for prefijo in prefijos) and (archivo.endswith('.xlsx') or archivo.endswith('.csv')):
                        ruta_completa = os.path.join(ruta_fuente, archivo)
                        propiedades = self.procesar_archivo_scraped(ruta_completa, fuente)

                        self.propiedades_scraped.extend(propiedades)
                        self.estadisticas['fuente_scraped'][fuente] = len(propiedades)

        self.estadisticas['total_scraped'] = len(self.propiedades_scraped)
        logger.info(f"Cargadas {self.estadisticas['total_scraped']} propiedades scrapeadas")

    def detectar_duplicados(self) -> None:
        """Detecta y elimina propiedades duplicadas."""
        logger.info("Detectando duplicados...")

        # Crear conjunto de IDs existentes
        ids_existentes = {prop['id'] for prop in self.propiedades_franz}
        duplicados = 0

        # Filtrar propiedades scrapeadas no duplicadas
        propiedades_scraped_unicas = []
        for prop_scraped in self.propiedades_scraped:
            # Verificar si es duplicado basado en título y ubicación
            es_duplicado = False
            for prop_franz in self.propiedades_franz:
                if (prop_scraped['nombre'].lower() == prop_franz.get('nombre', '').lower() and
                    prop_scraped['ubicacion']['zona'] == prop_franz.get('ubicacion', {}).get('zona', '')):
                    es_duplicado = True
                    break

            if not es_duplicado:
                propiedades_scraped_unicas.append(prop_scraped)
            else:
                duplicados += 1

        self.propiedades_scraped = propiedades_scraped_unicas
        self.estadisticas['duplicados'] = duplicados
        logger.info(f"Eliminados {duplicados} duplicados")

    def integrar_datos(self) -> None:
        """Integra los datos de Franz con los datos scrapeados."""
        logger.info("Integrando datos...")

        # Combinar propiedades
        self.propiedades_integradas = self.propiedades_franz + self.propiedades_scraped

        self.estadisticas['total_integradas'] = len(self.propiedades_integradas)
        logger.info(f"Integradas {self.estadisticas['total_integradas']} propiedades en total")

    def guardar_base_integrada(self) -> None:
        """Guarda la base de datos integrada."""
        logger.info("Guardando base de datos integrada...")

        # Crear directorio si no existe
        os.makedirs('data/bd_integrada', exist_ok=True)

        # Guardar propiedades integradas
        with open('data/bd_integrada/propiedades_integradas.json', 'w', encoding='utf-8') as f:
            json.dump(self.propiedades_integradas, f, indent=2, ensure_ascii=False)

        # Guardar estadísticas
        with open('data/bd_integrada/estadisticas_integracion.json', 'w', encoding='utf-8') as f:
            json.dump(self.estadisticas, f, indent=2, ensure_ascii=False)

        logger.info("Base de datos integrada guardada exitosamente")

    def mostrar_resumen(self) -> None:
        """Muestra un resumen de la integración."""
        print("\n" + "="*80)
        print("RESUMEN DE INTEGRACIÓN DE DATOS")
        print("="*80)

        print(f"PROPIEDADES DE FRANZ: {self.estadisticas['total_franz']:,}")
        print(f"PROPIEDADES SCRAPEADAS: {self.estadisticas['total_scraped']:,}")
        print(f"DUPLICADOS ELIMINADOS: {self.estadisticas['duplicados']:,}")
        print(f"TOTAL INTEGRADAS: {self.estadisticas['total_integradas']:,}")

        print(f"\nDISTRIBUCIÓN POR FUENTES SCRAPEADAS:")
        for fuente, cantidad in self.estadisticas['fuente_scraped'].items():
            print(f"   • {fuente}: {cantidad:,} propiedades")

        print(f"\nARCHIVOS GENERADOS:")
        print(f"   • data/bd_integrada/propiedades_integradas.json")
        print(f"   • data/bd_integrada/estadisticas_integracion.json")

        print("="*80)

    def ejecutar_integracion_completa(self) -> None:
        """Ejecuta el proceso completo de integración."""
        logger.info("=== INICIANDO INTEGRACIÓN DE DATOS SCRAPEADOS ===")

        # Cargar datos
        self.cargar_propiedades_franz()
        self.cargar_datos_scraped()

        # Procesar datos
        self.detectar_duplicados()
        self.integrar_datos()

        # Guardar resultados
        self.guardar_base_integrada()
        self.mostrar_resumen()

        logger.info("=== INTEGRACIÓN COMPLETADA ===")

def main():
    """Función principal."""
    integrador = IntegradorDatosScrapeados()
    integrador.ejecutar_integracion_completa()

if __name__ == "__main__":
    main()