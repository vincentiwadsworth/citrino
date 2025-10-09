"""Property catalog query service for the Citrino platform."""

import json
import pandas as pd
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SistemaConsultaCitrino:
    """Sistema de consulta y análisis para la base de datos de Citrino."""

    def __init__(self):
        self.propiedades = []
        self.indices = {
            'zona': {},
            'precio': {},
            'tipo': {},
            'fuente': {}
        }
        self.estadisticas_globales = {}

    def cargar_base_datos(self, ruta: str = 'data/bd_final/propiedades_limpias.json') -> None:
        """Carga la base de datos integrada."""
        logger.info(f"Cargando base de datos desde {ruta}...")

        with open(ruta, 'r', encoding='utf-8') as f:
            self.propiedades = json.load(f)

        logger.info(f"Cargadas {len(self.propiedades)} propiedades")
        self.crear_indices()
        self.calcular_estadisticas_globales()

    def crear_indices(self) -> None:
        """Crea índices para búsqueda rápida."""
        logger.info("Creando índices de búsqueda...")

        # Reiniciar índices
        self.indices = {
            'zona': {},
            'precio': {},
            'tipo': {},
            'fuente': {}
        }

        for prop in self.propiedades:
            # Índice por zona
            zona = prop.get('ubicacion', {}).get('zona', 'Otra')
            if zona not in self.indices['zona']:
                self.indices['zona'][zona] = []
            self.indices['zona'][zona].append(prop)

            # Índice por precio
            precio = prop.get('caracteristicas_principales', {}).get('precio', 0)
            rango_precio = self.clasificar_rango_precio(precio)
            if rango_precio not in self.indices['precio']:
                self.indices['precio'][rango_precio] = []
            self.indices['precio'][rango_precio].append(prop)

            # Índice por tipo
            nombre = prop.get('nombre', '').lower()
            if 'departamento' in nombre or 'depto' in nombre:
                tipo = 'Departamento'
            elif 'casa' in nombre:
                tipo = 'Casa'
            elif 'townhouse' in nombre:
                tipo = 'Townhouse'
            else:
                tipo = 'Otro'

            if tipo not in self.indices['tipo']:
                self.indices['tipo'][tipo] = []
            self.indices['tipo'][tipo].append(prop)

            # Índice por fuente
            fuente = prop.get('fuente', '')
            if fuente not in self.indices['fuente']:
                self.indices['fuente'][fuente] = []
            self.indices['fuente'][fuente].append(prop)

        logger.info("Índices creados exitosamente")

    def clasificar_rango_precio(self, precio: float) -> str:
        """Clasifica el precio en rangos."""
        if precio < 50000:
            return 'económico'
        elif precio < 100000:
            return 'medio'
        elif precio < 150000:
            return 'alto'
        else:
            return 'premium'

    def calcular_estadisticas_globales(self) -> None:
        """Calcula estadísticas globales de la base de datos."""
        logger.info("Calculando estadísticas globales...")

        precios = [prop.get('caracteristicas_principales', {}).get('precio', 0)
                   for prop in self.propiedades if prop.get('caracteristicas_principales', {}).get('precio', 0) > 0]

        superficies = [prop.get('caracteristicas_principales', {}).get('superficie_m2', 0)
                        for prop in self.propiedades if prop.get('caracteristicas_principales', {}).get('superficie_m2', 0) > 0]

        self.estadisticas_globales = {
            'total_propiedades': len(self.propiedades),
            'precio_promedio': sum(precios) / len(precios) if precios else 0,
            'precio_minimo': min(precios) if precios else 0,
            'precio_maximo': max(precios) if precios else 0,
            'superficie_promedio': sum(superficies) / len(superficies) if superficies else 0,
            'superficie_minima': min(superficies) if superficies else 0,
            'superficie_maxima': max(superficies) if superficies else 0,
            'total_zonas': len(self.indices['zona']),
            'total_tipos': len(self.indices['tipo'])
        }

    def buscar_por_filtros(self, filtros: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Busca propiedades según filtros especificados."""
        resultados = []

        for prop in self.propiedades:
            if self.cumple_filtros(prop, filtros):
                resultados.append(prop)

        return resultados

    def cumple_filtros(self, propiedad: Dict[str, Any], filtros: Dict[str, Any]) -> bool:
        """Verifica si una propiedad cumple con los filtros."""
        try:
            # Filtro por zona
            if 'zona' in filtros:
                zona_prop = propiedad.get('ubicacion', {}).get('zona', '').lower()
                if isinstance(filtros['zona'], str):
                    if filtros['zona'].lower() not in zona_prop:
                        return False
                elif isinstance(filtros['zona'], list):
                    if not any(z.lower() in zona_prop for z in filtros['zona']):
                        return False

            # Filtro por precio
            if 'precio_min' in filtros or 'precio_max' in filtros:
                precio = propiedad.get('caracteristicas_principales', {}).get('precio', 0)

                if 'precio_min' in filtros and precio < filtros['precio_min']:
                    return False

                if 'precio_max' in filtros and precio > filtros['precio_max']:
                    return False

            # Filtro por superficie
            if 'superficie_min' in filtros or 'superficie_max' in filtros:
                superficie = propiedad.get('caracteristicas_principales', {}).get('superficie_m2', 0)

                if 'superficie_min' in filtros and superficie < filtros['superficie_min']:
                    return False

                if 'superficie_max' in filtros and superficie > filtros['superficie_max']:
                    return False

            # Filtro por habitaciones
            if 'habitaciones_min' in filtros:
                habitaciones = propiedad.get('caracteristicas_principales', {}).get('habitaciones', 0)
                if habitaciones < filtros['habitaciones_min']:
                    return False

            # Filtro por baños
            if 'banos_min' in filtros:
                banos = propiedad.get('caracteristicas_principales', {}).get('banos_completos', 0)
                if banos < filtros['banos_min']:
                    return False

            # Filtro por garaje
            if 'tiene_garaje' in filtros:
                tiene_garaje = propiedad.get('caracteristicas_principales', {}).get('cochera_garaje', False)
                if tiene_garaje != filtros['tiene_garaje']:
                    return False

            # Filtro por fuente
            if 'fuente' in filtros:
                fuente_prop = propiedad.get('fuente', '').lower()
                if isinstance(filtros['fuente'], str):
                    if filtros['fuente'].lower() not in fuente_prop:
                        return False

            return True

        except Exception as e:
            logger.error(f"Error verificando filtros: {str(e)}")
            return False

    def buscar_por_zona(self, zona: str) -> List[Dict[str, Any]]:
        """Busca propiedades por zona."""
        resultados = []

        for prop in self.propiedades:
            zona_prop = prop.get('ubicacion', {}).get('zona', '').lower()
            if zona.lower() in zona_prop:
                resultados.append(prop)

        return resultados

    def buscar_por_rango_precio(self, precio_min: float, precio_max: float) -> List[Dict[str, Any]]:
        """Busca propiedades por rango de precio."""
        resultados = []

        for prop in self.propiedades:
            precio = prop.get('caracteristicas_principales', {}).get('precio', 0)
            if precio_min <= precio <= precio_max:
                resultados.append(prop)

        return resultados

    def obtener_top_propiedades(self, n: int = 10, criterio: str = 'precio') -> List[Dict[str, Any]]:
        """Obtiene las top N propiedades según un criterio."""
        if criterio == 'precio':
            return sorted(self.propiedades,
                         key=lambda x: x.get('caracteristicas_principales', {}).get('precio', 0),
                         reverse=True)[:n]
        elif criterio == 'superficie':
            return sorted(self.propiedades,
                         key=lambda x: x.get('caracteristicas_principales', {}).get('superficie_m2', 0),
                         reverse=True)[:n]
        else:
            return []

    def obtener_estadisticas_por_zona(self, zona: str) -> Dict[str, Any]:
        """Obtiene estadísticas específicas por zona."""
        propiedades_zona = self.buscar_por_zona(zona)

        if not propiedades_zona:
            return {}

        precios = [prop.get('caracteristicas_principales', {}).get('precio', 0)
                   for prop in propiedades_zona if prop.get('caracteristicas_principales', {}).get('precio', 0) > 0]

        superficies = [prop.get('caracteristicas_principales', {}).get('superficie_m2', 0)
                       for prop in propiedades_zona if prop.get('caracteristicas_principales', {}).get('superficie_m2', 0) > 0]

        return {
            'zona': zona,
            'total_propiedades': len(propiedades_zona),
            'precio_promedio': sum(precios) / len(precios) if precios else 0,
            'precio_minimo': min(precios) if precios else 0,
            'precio_maximo': max(precios) if precios else 0,
            'superficie_promedio': sum(superficies) / len(superficies) if superficies else 0,
            'precio_m2_promedio': sum(precios) / sum(superficies) if precios and superficies else 0
        }

    def obtener_comparativo_zonas(self, zonas: List[str]) -> Dict[str, Any]:
        """Obtiene un comparativo entre varias zonas."""
        comparativo = {}

        for zona in zonas:
            stats = self.obtener_estadisticas_por_zona(zona)
            if stats:
                comparativo[zona] = stats

        return comparativo

    def exportar_resultados(self, resultados: List[Dict[str, Any]], formato: str = 'json', nombre_archivo: str = None) -> str:
        """Exporta resultados a diferentes formatos."""
        if not nombre_archivo:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"resultados_busqueda_{timestamp}"

        os.makedirs('data/resultados', exist_ok=True)

        if formato == 'json':
            ruta = f"data/resultados/{nombre_archivo}.json"
            with open(ruta, 'w', encoding='utf-8') as f:
                json.dump(resultados, f, indent=2, ensure_ascii=False)

        elif formato == 'csv':
            # Convertir a DataFrame para exportar a CSV
            datos_csv = []
            for prop in resultados:
                datos_csv.append({
                    'id': prop.get('id', ''),
                    'nombre': prop.get('nombre', ''),
                    'precio': prop.get('caracteristicas_principales', {}).get('precio', 0),
                    'superficie_m2': prop.get('caracteristicas_principales', {}).get('superficie_m2', 0),
                    'habitaciones': prop.get('caracteristicas_principales', {}).get('habitaciones', 0),
                    'banos': prop.get('caracteristicas_principales', {}).get('banos_completos', 0),
                    'zona': prop.get('ubicacion', {}).get('zona', ''),
                    'fuente': prop.get('fuente', '')
                })

            df = pd.DataFrame(datos_csv)
            ruta = f"data/resultados/{nombre_archivo}.csv"
            df.to_csv(ruta, index=False, encoding='utf-8')

        elif formato == 'excel':
            # Convertir a DataFrame para exportar a Excel
            datos_excel = []
            for prop in resultados:
                datos_excel.append({
                    'ID': prop.get('id', ''),
                    'Nombre': prop.get('nombre', ''),
                    'Precio': prop.get('caracteristicas_principales', {}).get('precio', 0),
                    'Superficie m²': prop.get('caracteristicas_principales', {}).get('superficie_m2', 0),
                    'Habitaciones': prop.get('caracteristicas_principales', {}).get('habitaciones', 0),
                    'Baños': prop.get('caracteristicas_principales', {}).get('banos_completos', 0),
                    'Zona': prop.get('ubicacion', {}).get('zona', ''),
                    'Fuente': prop.get('fuente', ''),
                    'Descripción': prop.get('descripcion', '')[:200] + '...' if len(prop.get('descripcion', '')) > 200 else prop.get('descripcion', '')
                })

            df = pd.DataFrame(datos_excel)
            ruta = f"data/resultados/{nombre_archivo}.xlsx"
            df.to_excel(ruta, index=False)

        else:
            raise ValueError(f"Formato no soportado: {formato}")

        logger.info(f"Resultados exportados a: {ruta}")
        return ruta

    def mostrar_resumen_estadistico(self) -> None:
        """Muestra un resumen estadístico completo."""
        print("\n" + "="*80)
        print("RESUMEN ESTADÍSTICO - BASE DE DATOS INTEGRADA CITRINO")
        print("="*80)

        print(f"TOTAL DE PROPIEDADES: {self.estadisticas_globales['total_propiedades']:,}")
        print(f"PRECIO PROMEDIO: ${self.estadisticas_globales['precio_promedio']:,.0f}")
        print(f"RANGO DE PRECIOS: ${self.estadisticas_globales['precio_minimo']:,.0f} - ${self.estadisticas_globales['precio_maximo']:,.0f}")
        print(f"SUPERFICIE PROMEDIO: {self.estadisticas_globales['superficie_promedio']:.1f} m²")
        print(f"RANGO DE SUPERFICIES: {self.estadisticas_globales['superficie_minima']:.1f} - {self.estadisticas_globales['superficie_maxima']:.1f} m²")
        print(f"TOTAL DE ZONAS: {self.estadisticas_globales['total_zonas']}")
        print(f"TOTAL DE TIPOS: {self.estadisticas_globales['total_tipos']}")

        print(f"\nDISTRIBUCIÓN POR ZONAS (Top 10):")
        for zona, props in sorted(self.indices['zona'].items(), key=lambda x: len(x[1]), reverse=True)[:10]:
            porcentaje = (len(props) / self.estadisticas_globales['total_propiedades']) * 100
            print(f"   • {zona}: {len(props):,} propiedades ({porcentaje:.1f}%)")

        print(f"\nDISTRIBUCIÓN POR PRECIO:")
        for rango, props in self.indices['precio'].items():
            porcentaje = (len(props) / self.estadisticas_globales['total_propiedades']) * 100
            print(f"   • {rango}: {len(props):,} propiedades ({porcentaje:.1f}%)")

        print(f"\nDISTRIBUCIÓN POR TIPO:")
        for tipo, props in self.indices['tipo'].items():
            porcentaje = (len(props) / self.estadisticas_globales['total_propiedades']) * 100
            print(f"   • {tipo}: {len(props):,} propiedades ({porcentaje:.1f}%)")

        print("="*80)

    def ejecutar_consulta_ejemplo(self) -> None:
        """Ejecuta consultas de ejemplo."""
        print("\n" + "="*80)
        print("EJEMPLOS DE CONSULTA")
        print("="*80)

        # Ejemplo 1: Propiedades en Equipetrol
        print("\n1. Propiedades en Equipetrol:")
        props_equipetrol = self.buscar_por_zona("Equipetrol")
        print(f"   Encontradas: {len(props_equipetrol)} propiedades")

        if props_equipetrol:
            print("   Top 3 propiedades más caras:")
            for i, prop in enumerate(sorted(props_equipetrol, key=lambda x: x.get('caracteristicas_principales', {}).get('precio', 0), reverse=True)[:3], 1):
                precio = prop.get('caracteristicas_principales', {}).get('precio', 0)
                print(f"      {i}. {prop.get('nombre', 'Sin nombre')} - ${precio:,.0f}")

        # Ejemplo 2: Propiedades con 3+ habitaciones y 2+ baños
        print("\n2. Propiedades con 3+ habitaciones y 2+ baños:")
        filtros = {
            'habitaciones_min': 3,
            'banos_min': 2
        }
        props_familiares = self.buscar_por_filtros(filtros)
        print(f"   Encontradas: {len(props_familiares)} propiedades")

        # Ejemplo 3: Comparativo de zonas premium
        print("\n3. Comparativo de zonas premium:")
        zonas_premium = ['Equipetrol', 'Las Palmas', 'Urubó', 'Zona Norte']
        comparativo = self.obtener_comparativo_zonas(zonas_premium)

        for zona, stats in comparativo.items():
            print(f"   {zona}:")
            print(f"      • Propiedades: {stats['total_propiedades']:,}")
            print(f"      • Precio promedio: ${stats['precio_promedio']:,.0f}")
            print(f"      • Precio m² promedio: ${stats['precio_m2_promedio']:,.0f}")

        print("="*80)


def main():
    """Función principal."""
    print("=== SISTEMA DE CONSULTA Y ANÁLISIS CITRINO ===")

    # Crear sistema de consulta
    sistema = SistemaConsultaCitrino()

    # Cargar base de datos
    sistema.cargar_base_datos()

    # Mostrar resumen estadístico
    sistema.mostrar_resumen_estadistico()

    # Ejecutar consultas de ejemplo
    sistema.ejecutar_consulta_ejemplo()

    print("\n=== SISTEMA LISTO PARA CONSULTAS ===")


if __name__ == "__main__":
    main()
