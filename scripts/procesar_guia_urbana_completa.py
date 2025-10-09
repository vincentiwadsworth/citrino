#!/usr/bin/env python3
"""
Procesamiento e integración de la información completa de la Guía Urbana Municipal
Descubre: 5,261 servicios + 353 proyectos con análisis de mercado + datos temáticos
"""

import json
import pandas as pd
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProcesadorGuiaUrbanaCompleta:
    """Procesador completo de la Guía Urbana Municipal"""

    def __init__(self):
        self.datos_consolidados = []
        self.datos_inteligencia = []
        self.datos_tematicos = {}
        self.ruta_base = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'guia-urbana')

    def procesar_consolidado(self):
        """Procesa el archivo consolidado principal de 5,261 servicios"""
        ruta_consolidado = os.path.join(self.ruta_base, 'Info_Guia Urbana', 'CONSOLIDADO_GUIA_URB.xlsx')

        try:
            logger.info(f"Procesando consolidado: {ruta_consolidado}")
            df = pd.read_excel(ruta_consolidado)

            # Limpieza y estandarización
            df = df.dropna(subset=['Latitud', 'Longitud', 'NOMBRE'])

            # Convertir coordenadas a numérico
            df['Latitud'] = pd.to_numeric(df['Latitud'], errors='coerce')
            df['Longitud'] = pd.to_numeric(df['Longitud'], errors='coerce')

            # Validar coordenadas Santa Cruz
            df = df[df['Latitud'].between(-18, -17)]
            df = df[df['Longitud'].between(-64, -63)]

            # Convertir a formato estandarizado
            servicios = []
            for _, row in df.iterrows():
                servicio = {
                    'id': f"svc_{row.name}",
                    'tipo': row.get('SUB_SISTEM', 'desconocido').lower(),
                    'nombre': row.get('NOMBRE', 'Sin nombre'),
                    'nivel': row.get('NIVEL', 'desconocido'),
                    'distrito': str(row.get('DISTRITO', '')) if pd.notna(row.get('DISTRITO')) else '',
                    'unidad_vecinal': str(row.get('UV', '')) if pd.notna(row.get('UV')) else '',
                    'manzana': str(row.get('MZ', '')) if pd.notna(row.get('MZ')) else '',
                    'barrio': row.get('BARRIO', 'Sin barrio'),
                    'direccion': row.get('DIRECCION', ''),
                    'coordenadas': {
                        'lat': row.get('Latitud'),
                        'lng': row.get('Longitud')
                    },
                    'categoria_principal': self.categorizar_servicio(row.get('SUB_SISTEM', '')),
                    'fuente': 'guia_urbana_consolidada',
                    'fecha_procesamiento': datetime.now().isoformat()
                }
                servicios.append(servicio)

            self.datos_consolidados = servicios
            logger.info(f"Consolidado procesado: {len(servicios)} servicios")

        except Exception as e:
            logger.error(f"Error procesando consolidado: {e}")

    def procesar_inteligencia_inmobiliaria(self):
        """Procesa el archivo de inteligencia inmobiliaria con 353 proyectos"""
        ruta_inteligencia = os.path.join(self.ruta_base, 'Inteligencia_Inmobiliaria', 'SCZ_Inteligencia_Inmobiliaria.xlsx')

        try:
            logger.info(f"Procesando inteligencia inmobiliaria: {ruta_inteligencia}")
            df = pd.read_excel(ruta_inteligencia)

            proyectos = []
            for _, row in df.iterrows():
                # Extraer densidad de servicios por categoría
                servicios_cercanos = {}
                for categoria in ['ABASTECIMIENTO', 'CULTURA', 'DEPORTES', 'EDUCACION', 'SALUD', 'TRANSPORTE']:
                    count = row.get(categoria, 0)
                    if pd.notna(count) and count > 0:
                        servicios_cercanos[categoria.lower()] = int(count)

                proyecto = {
                    'id': f"proj_{row.name}",
                    'nombre_proyecto': row.get('Proyecto', 'Sin nombre'),
                    'zona': row.get('Zona', 'Desconocida'),
                    'tipo': row.get('Tipo', 'Desconocido'),
                    'tipologia': row.get('Tipología', 'Desconocido'),
                    'precio_m2_venta': row.get('$ precio venta actual', 0),
                    'precio_m2_alquiler': row.get('$/m2 Alquiler', 0),
                    'margen_comparativo': row.get('% Margen comparativo', 0),
                    'porcentaje_vendido': row.get('%Vendido', 0),
                    'unidades_disponibles': row.get('UND por vender', 0),
                    'coordenadas': {
                        'lat': row.get('Latitud'),
                        'lng': row.get('Longitud')
                    },
                    'unidad_vecinal': str(row.get('UV', '')) if pd.notna(row.get('UV')) else '',
                    'manzana': str(row.get('MZ', '')) if pd.notna(row.get('MZ')) else '',
                    'servicios_cercanos': servicios_cercanos,
                    'indicadores_mercado': {
                        'ritmo_venta': row.get('Ritmo de venta', 0),
                        'meses_stock': row.get('Meses Stock', 0),
                        'margen_anual': row.get('% Margen anual', 0),
                        'calidad': row.get('Calidad', 'Desconocida')
                    },
                    'fuente': 'inteligencia_inmobiliaria',
                    'fecha_procesamiento': datetime.now().isoformat()
                }
                proyectos.append(proyecto)

            self.datos_inteligencia = proyectos
            logger.info(f"Inteligencia inmobiliaria procesada: {len(proyectos)} proyectos")

        except Exception as e:
            logger.error(f"Error procesando inteligencia inmobiliaria: {e}")

    def procesar_datos_tematicos(self):
        """Procesa archivos temáticos específicos"""
        categorias = {
            'SALUD': 'B_Salud.xlsx',
            'EDUCACION': 'AA_EDUCACION.xlsx',
            'DEPORTE': 'F_Deportes.xlsx',
            'CULTURA': 'E_Cultura_.xlsx'
        }

        for categoria, archivo in categorias.items():
            ruta = os.path.join(self.ruta_base, 'Info_Guia Urbana', categoria, archivo)

            try:
                if os.path.exists(ruta):
                    logger.info(f"Procesando temático {categoria}: {ruta}")
                    df = pd.read_excel(ruta)

                    servicios = []
                    for _, row in df.iterrows():
                        servicio = {
                            'id': f"{categoria.lower()}_{row.name}",
                            'categoria': categoria.lower(),
                            'nombre': row.get('NOMBRE', 'Sin nombre'),
                            'subsistema': row.get('SUB_SISTEM', ''),
                            'nivel': row.get('NIVEL', 'desconocido'),
                            'distrito': str(row.get('DISTRITO', '')) if pd.notna(row.get('DISTRITO')) else '',
                            'unidad_vecinal': str(row.get('UV', '')) if pd.notna(row.get('UV')) else '',
                            'barrio': row.get('BARRIO', 'Sin barrio'),
                            'direccion': row.get('DIRECCION', ''),
                            'coordenadas': {
                                'lat': row.get('Latitud') or row.get('Y'),
                                'lng': row.get('Longitud') or row.get('X')
                            },
                            'fuente': f'guia_urbana_{categoria.lower()}',
                            'fecha_procesamiento': datetime.now().isoformat()
                        }
                        servicios.append(servicio)

                    self.datos_tematicos[categoria.lower()] = servicios
                    logger.info(f"{categoria} procesado: {len(servicios)} servicios")

            except Exception as e:
                logger.warning(f"Error procesando {categoria}: {e}")

    def categorizar_servicio(self, subsistema: str) -> str:
        """Categoriza servicios para mejor organización"""
        subsistema_lower = subsistema.lower()

        categorias = {
            'abastecimiento': ['mercado', 'supermercado', 'abastecimiento'],
            'salud': ['hospital', 'clinica', 'centro', 'salud', 'farmacia'],
            'educacion': ['escuela', 'colegio', 'universidad', 'educacion', 'instituto'],
            'deporte': ['deport', 'gimnasio', 'estadio', 'club'],
            'cultura': ['cultural', 'museo', 'biblioteca', 'teatro'],
            'transporte': ['transporte', 'terminal', 'estacion']
        }

        for categoria, palabras in categorias.items():
            if any(palabra in subsistema_lower for palabra in palabras):
                return categoria

        return 'otros'

    def generar_datos_integrados(self):
        """Genera el archivo final integrado con todos los datos municipales"""
        datos_completos = {
            'metadatos': {
                'fecha_generacion': datetime.now().isoformat(),
                'total_servicios_consolidados': len(self.datos_consolidados),
                'total_proyectos_inteligencia': len(self.datos_inteligencia),
                'total_servicios_tematicos': sum(len(v) for v in self.datos_tematicos.values()),
                'fuentes': ['guia_urbana_consolidada', 'inteligencia_inmobiliaria'] + list(self.datos_tematicos.keys())
            },
            'servicios_consolidados': self.datos_consolidados,
            'proyectos_mercado': self.datos_inteligencia,
            'servicios_tematicos': self.datos_tematicos
        }

        # Guardar archivo completo
        ruta_salida = os.path.join(os.path.dirname(__file__), '..', 'data', 'guia_urbana_municipal_completa.json')
        with open(ruta_salida, 'w', encoding='utf-8') as f:
            json.dump(datos_completos, f, indent=2, ensure_ascii=False)

        logger.info(f"Datos integrados guardados en: {ruta_salida}")
        logger.info(f"Total servicios: {datos_completos['metadatos']['total_servicios_consolidados']}")
        logger.info(f"Total proyectos: {datos_completos['metadatos']['total_proyectos_inteligencia']}")
        logger.info(f"Total servicios temáticos: {datos_completos['metadatos']['total_servicios_tematicos']}")

        return datos_completos

    def procesar_todo(self):
        """Ejecuta todo el procesamiento"""
        logger.info("Iniciando procesamiento completo de Guía Urbana Municipal")

        self.procesar_consolidado()
        self.procesar_inteligencia_inmobiliaria()
        self.procesar_datos_tematicos()

        return self.generar_datos_integrados()

def main():
    """Función principal para probar el procesamiento"""
    print("=== PROCESAMIENTO COMPLETO DE GUÍA URBANA MUNICIPAL ===")

    procesador = ProcesadorGuiaUrbanaCompleta()
    datos_integrados = procesador.procesar_todo()

    print("\n=== RESUMEN DE PROCESAMIENTO ===")
    metadatos = datos_integrados['metadatos']
    print(f"Servicios consolidados: {metadatos['total_servicios_consolidados']:,}")
    print(f"Proyectos con inteligencia: {metadatos['total_proyectos_inteligencia']:,}")
    print(f"Servicios temáticos: {metadatos['total_servicios_tematicos']:,}")
    print(f"Fuentes integradas: {len(metadatos['fuentes'])}")

    # Mostrar algunas estadísticas
    if datos_integrados['servicios_consolidados']:
        tipos_servicio = {}
        for servicio in datos_integrados['servicios_consolidados']:
            tipo = servicio['categoria_principal']
            tipos_servicio[tipo] = tipos_servicio.get(tipo, 0) + 1

        print(f"\nDistribución de servicios:")
        for tipo, count in sorted(tipos_servicio.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {tipo}: {count:,} servicios")

    if datos_integrados['proyectos_mercado']:
        zonas_proyectos = {}
        for proyecto in datos_integrados['proyectos_mercado']:
            zona = proyecto['zona']
            zonas_proyectos[zona] = zonas_proyectos.get(zona, 0) + 1

        print(f"\nProyectos por zona:")
        for zona, count in sorted(zonas_proyectos.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {zona}: {count:,} proyectos")

    print("\n=== PROCESAMIENTO COMPLETADO ===")

if __name__ == "__main__":
    main()