#!/usr/bin/env python3
"""
Script para validar el motor de recomendación con la base de datos completa.
"""

import json
import sys
import os
from typing import Dict, List, Any

# Agregar el directorio src al path para importar el motor de recomendación
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from recommendation_engine import RecommendationEngine
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ValidadorMotorRecomendacion:
    """Clase para validar el motor de recomendación con la base de datos completa."""

    def __init__(self):
        self.motor = RecommendationEngine()
        self.propiedades = []
        self.estadisticas_validacion = {
            'total_propiedades': 0,
            'perfiles_prueba': 0,
            'recomendaciones_exitosas': 0,
            'tiempo_promedio_recomendacion': 0,
            'puntuacion_promedio': 0,
            'zona_mas_recomendada': '',
            'precio_promedio_recomendado': 0
        }

    def cargar_base_datos(self) -> None:
        """Carga la base de datos limpia."""
        logger.info("Cargando base de datos limpia...")

        with open('data/bd_final/propiedades_limpias.json', 'r', encoding='utf-8') as f:
            self.propiedades = json.load(f)

        self.estadisticas_validacion['total_propiedades'] = len(self.propiedades)
        logger.info(f"Cargadas {self.estadisticas_validacion['total_propiedades']} propiedades")

        # Cargar propiedades en el motor
        self.motor.cargar_propiedades(self.propiedades)

    def crear_perfiles_prueba(self) -> List[Dict[str, Any]]:
        """Crea perfiles de prueba para validar el motor."""
        return [
            {
                'id': 'perfil_1',
                'nombre': 'Familia joven profesional',
                'presupuesto': {
                    'min': 100000,
                    'max': 250000
                },
                'composicion_familiar': {
                    'adultos': 2,
                    'ninos': [1],
                    'adultos_mayores': 0
                },
                'preferencias': {
                    'ubicacion': 'Equipetrol',
                    'tipo_propiedad': 'departamento'
                },
                'necesidades': ['seguridad', 'estacionamiento', 'gimnasio']
            },
            {
                'id': 'perfil_2',
                'nombre': 'Familia con niños',
                'presupuesto': {
                    'min': 200000,
                    'max': 350000
                },
                'composicion_familiar': {
                    'adultos': 2,
                    'ninos': [1, 2, 3],
                    'adultos_mayores': 0
                },
                'preferencias': {
                    'ubicacion': 'Las Palmas',
                    'tipo_propiedad': 'casa'
                },
                'necesidades': ['seguridad', 'areas_comunes', 'estacionamiento', 'piscina']
            },
            {
                'id': 'perfil_3',
                'nombre': 'Profesional soltero',
                'presupuesto': {
                    'min': 80000,
                    'max': 180000
                },
                'composicion_familiar': {
                    'adultos': 1,
                    'ninos': [],
                    'adultos_mayores': 0
                },
                'preferencias': {
                    'ubicacion': 'Zona Norte',
                    'tipo_propiedad': 'departamento'
                },
                'necesidades': ['seguridad', 'estacionamiento', 'gimnasio']
            },
            {
                'id': 'perfil_4',
                'nombre': 'Pareja joven',
                'presupuesto': {
                    'min': 120000,
                    'max': 200000
                },
                'composicion_familiar': {
                    'adultos': 2,
                    'ninos': [],
                    'adultos_mayores': 0
                },
                'preferencias': {
                    'ubicacion': 'Urubó',
                    'tipo_propiedad': 'departamento'
                },
                'necesidades': ['seguridad', 'areas_comunes', 'estacionamiento']
            },
            {
                'id': 'perfil_5',
                'nombre': 'Familia adinerada',
                'presupuesto': {
                    'min': 300000,
                    'max': 500000
                },
                'composicion_familiar': {
                    'adultos': 2,
                    'ninos': [1, 2],
                    'adultos_mayores': 0
                },
                'preferencias': {
                    'ubicacion': 'Equipetrol',
                    'tipo_propiedad': 'casa'
                },
                'necesidades': ['seguridad', 'areas_comunes', 'estacionamiento', 'piscina', 'gimnasio']
            }
        ]

    def validar_perfil(self, perfil: Dict[str, Any]) -> Dict[str, Any]:
        """Valida un perfil específico."""
        logger.info(f"Validando perfil: {perfil['nombre']}")

        try:
            # Obtener recomendaciones
            recomendaciones = self.motor.generar_recomendaciones(
                perfil, limite=10, umbral_minimo=0.3
            )

            # Calcular estadísticas
            if recomendaciones:
                puntuacion_promedio = sum(rec['compatibilidad'] for rec in recomendaciones) / len(recomendaciones)
                precio_promedio = sum(rec['propiedad'].get('caracteristicas_principales', {}).get('precio', 0) for rec in recomendaciones) / len(recomendaciones)

                # Determinar zona más recomendada
                zonas = {}
                for rec in recomendaciones:
                    zona = rec['propiedad'].get('ubicacion', {}).get('zona', 'Otra')
                    zonas[zona] = zonas.get(zona, 0) + 1

                zona_mas_recomendada = max(zonas, key=zonas.get) if zonas else 'N/A'

                return {
                    'perfil': perfil['nombre'],
                    'recomendaciones_encontradas': len(recomendaciones),
                    'puntuacion_promedio': puntuacion_promedio,
                    'precio_promedio': precio_promedio,
                    'zona_mas_recomendada': zona_mas_recomendada,
                    'exito': len(recomendaciones) > 0
                }
            else:
                return {
                    'perfil': perfil['nombre'],
                    'recomendaciones_encontradas': 0,
                    'puntuacion_promedio': 0,
                    'precio_promedio': 0,
                    'zona_mas_recomendada': 'N/A',
                    'exito': False
                }

        except Exception as e:
            logger.error(f"Error validando perfil {perfil['nombre']}: {str(e)}")
            return {
                'perfil': perfil['nombre'],
                'recomendaciones_encontradas': 0,
                'puntuacion_promedio': 0,
                'precio_promedio': 0,
                'zona_mas_recomendada': 'N/A',
                'exito': False
            }

    def ejecutar_validacion_completa(self) -> None:
        """Ejecuta la validación completa del motor."""
        logger.info("=== INICIANDO VALIDACIÓN DEL MOTOR DE RECOMENDACIÓN ===")

        self.cargar_base_datos()

        # Crear perfiles de prueba
        perfiles = self.crear_perfiles_prueba()
        self.estadisticas_validacion['perfiles_prueba'] = len(perfiles)

        logger.info(f"Validando {len(perfiles)} perfiles de prueba...")

        # Validar cada perfil
        resultados = []
        for perfil in perfiles:
            resultado = self.validar_perfil(perfil)
            resultados.append(resultado)

        # Calcular estadísticas globales
        recomendaciones_exitosas = sum(1 for r in resultados if r['exito'])
        puntuaciones = [r['puntuacion_promedio'] for r in resultados if r['exito']]
        precios = [r['precio_promedio'] for r in resultados if r['exito']]

        self.estadisticas_validacion['recomendaciones_exitosas'] = recomendaciones_exitosas
        self.estadisticas_validacion['puntuacion_promedio'] = sum(puntuaciones) / len(puntuaciones) if puntuaciones else 0
        self.estadisticas_validacion['precio_promedio_recomendado'] = sum(precios) / len(precios) if precios else 0
        self.estadisticas_validacion['tasa_exito'] = (recomendaciones_exitosas / len(perfiles)) * 100

        # Mostrar resultados
        self.mostrar_resultados_validacion(resultados)

        logger.info("=== VALIDACIÓN COMPLETADA ===")

    def mostrar_resultados_validacion(self, resultados: List[Dict[str, Any]]) -> None:
        """Muestra los resultados de la validación."""
        print("\n" + "="*80)
        print("RESULTADOS DE VALIDACIÓN DEL MOTOR DE RECOMENDACIÓN")
        print("="*80)

        print(f"ESTADÍSTICAS GENERALES:")
        print(f"   • Total de propiedades en la base de datos: {self.estadisticas_validacion['total_propiedades']:,}")
        print(f"   • Perfiles de prueba evaluados: {self.estadisticas_validacion['perfiles_prueba']}")
        print(f"   • Tasa de éxito: {self.estadisticas_validacion['tasa_exito']:.1f}%")
        print(f"   • Puntuación promedio de recomendaciones: {self.estadisticas_validacion['puntuacion_promedio']:.3f}")
        print(f"   • Precio promedio de propiedades recomendadas: ${self.estadisticas_validacion['precio_promedio_recomendado']:,.0f}")

        print(f"\nRESULTADOS POR PERFIL:")
        for resultado in resultados:
            estado = "EXITO" if resultado['exito'] else "FALLO"
            print(f"   {estado} - {resultado['perfil']}:")
            print(f"      • Recomendaciones encontradas: {resultado['recomendaciones_encontradas']}")
            print(f"      • Puntuación promedio: {resultado['puntuacion_promedio']:.3f}")
            print(f"      • Precio promedio: ${resultado['precio_promedio']:,.0f}")
            print(f"      • Zona más recomendada: {resultado['zona_mas_recomendada']}")

        print("\n" + "="*80)

        # Mostrar estadísticas del motor
        print(f"ESTADÍSTICAS DEL MOTOR:")
        print(f"   • Cálculos realizizados: {self.motor.stats['calculos_realizados']:,}")
        print(f"   • Cache hits: {self.motor.stats['cache_hits']:,}")
        print(f"   • Tiempo total de procesamiento: {self.motor.stats['tiempo_total']:.3f}s")
        print(f"   • Eficiencia del cache: {(self.motor.stats['cache_hits'] / max(1, self.motor.stats['calculos_realizados']) * 100):.1f}%")

        print("="*80)

def main():
    """Función principal."""
    print("=== VALIDACIÓN DEL MOTOR DE RECOMENDACIÓN ===")

    validador = ValidadorMotorRecomendacion()
    validador.ejecutar_validacion_completa()

    print("\n=== VALIDACIÓN COMPLETADA ===")

if __name__ == "__main__":
    main()