#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análisis de calidad de datos del Proveedor 02.

Este script analiza la calidad de los datos del Proveedor 02 para identificar:
- Porcentaje de campos vacíos
- Campos que pueden ser extraídos de descripciones
- Estadísticas de calidad por campo
- Potencial de mejora con LLM
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnalizadorCalidadProveedor02:
    """Analiza la calidad de datos del Proveedor 02."""

    def __init__(self, dataset_path: str = "data/base_datos_relevamiento.json"):
        """
        Inicializa el analizador.

        Args:
            dataset_path: Ruta al dataset de relevamiento
        """
        self.dataset_path = Path(dataset_path)
        self.propiedades_proveedor02 = []
        self.total_propiedades = 0
        self.propiedades_con_descripcion = 0

    def cargar_datos(self):
        """Carga y filtra propiedades del Proveedor 02."""
        try:
            with open(self.dataset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            all_propiedades = data.get('propiedades', [])
            self.total_propiedades = len(all_propiedades)

            # Filtrar solo propiedades del Proveedor 02
            self.propiedades_proveedor02 = [
                prop for prop in all_propiedades
                if prop.get('codigo_proveedor') == '02'
            ]

            logger.info(f"Total propiedades en dataset: {self.total_propiedades}")
            logger.info(f"Propiedades del Proveedor 02: {len(self.propiedades_proveedor02)}")
            logger.info(f"Porcentaje del Proveedor 02: {len(self.propiedades_proveedor02) / self.total_propiedades * 100:.1f}%")

            # Contar propiedades con descripción
            self.propiedades_con_descripcion = len([
                prop for prop in self.propiedades_proveedor02
                if prop.get('descripcion') and prop.get('descripcion').strip()
            ])

            logger.info(f"Propiedades con descripción: {self.propiedades_con_descripcion}")
            logger.info(f"Porcentaje con descripción: {self.propiedades_con_descripcion / len(self.propiedades_proveedor02) * 100:.1f}%")

        except Exception as e:
            logger.error(f"Error cargando datos: {e}")
            raise

    def analizar_calidad_campos(self) -> Dict[str, Any]:
        """Analiza la calidad de los campos clave."""
        campos_clave = [
            'precio', 'zona', 'superficie', 'habitaciones', 'banos',
            'tipo_propiedad', 'direccion', 'latitud', 'longitud'
        ]

        analisis = {}

        for campo in campos_clave:
            total = len(self.propiedades_proveedor02)
            con_dato = sum(1 for prop in self.propiedades_proveedor02
                          if self._tiene_dato_valido(prop, campo))

            porcentaje = (con_dato / total * 100) if total > 0 else 0

            analisis[campo] = {
                'total': total,
                'con_dato': con_dato,
                'sin_dato': total - con_dato,
                'porcentaje_completitud': porcentaje,
                'severidad': self._clasificar_severidad(porcentaje)
            }

        return analisis

    def _tiene_dato_valido(self, propiedad: Dict[str, Any], campo: str) -> bool:
        """Verifica si una propiedad tiene un dato válido en el campo especificado."""
        valor = propiedad.get(campo)

        if valor is None or valor == '':
            return False

        # Para números, verificar que no sea NaN
        if campo in ['precio', 'superficie', 'habitaciones', 'banos']:
            try:
                if pd.isna(valor):
                    return False
                if float(valor) == 0:
                    return False
            except (ValueError, TypeError):
                return False

        # Para texto, verificar que no sea vacío después de limpiar
        if isinstance(valor, str):
            return valor.strip() != ''

        return True

    def _clasificar_severidad(self, porcentaje: float) -> str:
        """Clasifica la severidad del problema de calidad."""
        if porcentaje >= 80:
            return 'bajo'
        elif porcentaje >= 60:
            return 'medio'
        elif porcentaje >= 40:
            return 'alto'
        else:
            return 'crítico'

    def analizar_potencial_mejora_llm(self) -> Dict[str, Any]:
        """Analiza el potencial de mejora usando LLM en descripciones."""
        potencial = {
            'total_propiedades': len(self.propiedades_proveedor02),
            'con_descripcion': self.propiedades_con_descripcion,
            'sin_descripcion': len(self.propiedades_proveedor02) - self.propiedades_con_descripcion,
            'campos_mejorables': {}
        }

        # Campos que podrían ser extraídos de descripciones
        campos_extraibles = ['precio', 'zona', 'superficie', 'habitaciones', 'banos', 'tipo_propiedad']

        for campo in campos_extraibles:
            # Contar propiedades que no tienen el campo PERO tienen descripción
            sin_campo_con_desc = sum(1 for prop in self.propiedades_proveedor02
                                    if not self._tiene_dato_valido(prop, campo)
                                    and prop.get('descripcion') and prop.get('descripcion').strip())

            potencial['campos_mejorables'][campo] = {
                'propiedades_mejorables': sin_campo_con_desc,
                'porcentaje_mejorable': (sin_campo_con_desc / len(self.propiedades_proveedor02) * 100) if self.propiedades_proveedor02 else 0,
                'potencial_alto': sin_campo_con_desc > 50,  # Más de 50 propiedades mejorables
                'impacto_estimado': self._estimar_impacto(campo, sin_campo_con_desc)
            }

        return potencial

    def _estimar_impacto(self, campo: str, cantidad: int) -> str:
        """Estima el impacto de mejorar un campo."""
        if cantidad < 20:
            return 'bajo'
        elif cantidad < 50:
            return 'medio'
        elif cantidad < 100:
            return 'alto'
        else:
            return 'muy alto'

    def analizar_ejemplos_problematicos(self, limite: int = 5) -> Dict[str, List[Dict]]:
        """Analiza ejemplos específicos de propiedades con problemas."""
        ejemplos = {
            'sin_datos_clave': [],
            'solo_descripcion': [],
            'datos_parciales': []
        }

        for prop in self.propiedades_proveedor02[:limite * 3]:  # Tomar muestra más grande
            problemas = []

            # Verificar campos críticos
            if not self._tiene_dato_valido(prop, 'precio'):
                problemas.append('precio')
            if not self._tiene_dato_valido(prop, 'zona'):
                problemas.append('zona')
            if not self._tiene_dato_valido(prop, 'tipo_propiedad'):
                problemas.append('tipo')

            # Clasificar tipo de problema
            tiene_descripcion = prop.get('descripcion') and prop.get('descripcion').strip()

            if len(problemas) >= 3 and tiene_descripcion:
                ejemplos['sin_datos_clave'].append({
                    'id': prop['id'],
                    'titulo': prop.get('titulo', ''),
                    'problemas': problemas,
                    'descripcion_preview': prop.get('descripcion', '')[:200] + '...' if len(prop.get('descripcion', '')) > 200 else prop.get('descripcion', '')
                })
            elif len(problemas) >= 2 and tiene_descripcion:
                ejemplos['datos_parciales'].append({
                    'id': prop['id'],
                    'titulo': prop.get('titulo', ''),
                    'problemas': problemas,
                    'descripcion_preview': prop.get('descripcion', '')[:200] + '...' if len(prop.get('descripcion', '')) > 200 else prop.get('descripcion', '')
                })
            elif tiene_descripcion and not any(self._tiene_dato_valido(prop, campo) for campo in ['precio', 'zona', 'superficie']):
                ejemplos['solo_descripcion'].append({
                    'id': prop['id'],
                    'titulo': prop.get('titulo', ''),
                    'descripcion_preview': prop.get('descripcion', '')[:200] + '...' if len(prop.get('descripcion', '')) > 200 else prop.get('descripcion', '')
                })

            # Limitar ejemplos
            for categoria in ejemplos:
                if len(ejemplos[categoria]) >= limite:
                    break

        return ejemplos

    def generar_reporte(self) -> Dict[str, Any]:
        """Genera un reporte completo de calidad de datos."""
        logger.info("Generando reporte de calidad de datos...")

        calidad_campos = self.analizar_calidad_campos()
        potencial_llm = self.analizar_potencial_mejora_llm()
        ejemplos = self.analizar_ejemplos_problematicos()

        # Calcular métricas generales
        campos_criticos_vacios = sum(1 for campo, analisis in calidad_campos.items()
                                   if analisis['porcentaje_completitud'] < 50)

        reporte = {
            'resumen_ejecutivo': {
                'total_propiedades': len(self.propiedades_proveedor02),
                'con_descripcion': self.propiedades_con_descripcion,
                'campos_criticos_con_problemas': campos_criticos_vacios,
                'prioridad_mejora': 'alta' if campos_criticos_vacios >= 3 else 'media',
                'potencial_llm': 'muy alto' if self.propiedades_con_descripcion > len(self.propiedades_proveedor02) * 0.8 else 'alto'
            },
            'calidad_por_campo': calidad_campos,
            'potencial_mejora_llm': potencial_llm,
            'ejemplos_problematicos': ejemplos,
            'recomendaciones': self._generar_recomendaciones(calidad_campos, potencial_llm)
        }

        return reporte

    def _generar_recomendaciones(self, calidad: Dict[str, Any], potencial: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones basadas en el análisis."""
        recomendaciones = []

        # Analizar peores campos
        campos_peores = sorted(calidad.items(), key=lambda x: x[1]['porcentaje_completitud'])[:3]

        if campos_peores[0][1]['porcentaje_completitud'] < 30:
            recomendaciones.append(f"Prioridad CRÍTICA: Mejorar {campos_peores[0][0]} (solo {campos_peores[0][1]['porcentaje_completitud']:.1f}% completitud)")

        # Recomendaciones basadas en potencial LLM
        for campo, info in potencial['campos_mejorables'].items():
            if info['propiedades_mejorables'] > 50:
                recomendaciones.append(f"ALTO IMPACTO: {campo} tiene potencial de mejorar {info['propiedades_mejorables']} propiedades via LLM")

        # Recomendación general
        if potencial['con_descripcion'] > 100:
            recomendaciones.append("Implementar sistema híbrido Regex + LLM para extracción masiva de datos")

        return recomendaciones

    def guardar_reporte(self, reporte: Dict[str, Any], output_path: str = "docs/reporte_calidad_proveedor02.json"):
        """Guarda el reporte en formato JSON."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(reporte, f, ensure_ascii=False, indent=2)

        logger.info(f"Reporte guardado en: {output_file}")

    def imprimir_resumen(self, reporte: Dict[str, Any]):
        """Imprime un resumen del reporte en consola."""
        print("\n" + "="*80)
        print("REPORTE DE CALIDAD DE DATOS - PROVEEDOR 02")
        print("="*80)

        # Resumen ejecutivo
        resumen = reporte['resumen_ejecutivo']
        print(f"\n[RESUMEN EJECUTIVO]:")
        print(f"• Total propiedades: {resumen['total_propiedades']}")
        print(f"• Con descripcion: {resumen['con_descripcion']} ({resumen['con_descripcion']/resumen['total_propiedades']*100:.1f}%)")
        print(f"• Campos criticos con problemas: {resumen['campos_criticos_con_problemas']}")
        print(f"• Prioridad de mejora: {resumen['prioridad_mejora'].upper()}")
        print(f"• Potencial LLM: {resumen['potencial_llm'].upper()}")

        # Calidad por campo
        print(f"\n[CALIDAD POR CAMPO]:")
        for campo, analisis in reporte['calidad_por_campo'].items():
            severidad_simbolo = {'bajo': '[OK]', 'medio': '[!]', 'alto': '[X]', 'crítico': '[!!]'}[analisis['severidad']]
            print(f"• {campo}: {analisis['porcentaje_completitud']:.1f}% completitud {severidad_simbolo}")

        # Potencial de mejora
        print(f"\n[POTENCIAL DE MEJORA CON LLM]:")
        for campo, info in reporte['potencial_mejora_llm']['campos_mejorables'].items():
            if info['propiedades_mejorables'] > 0:
                print(f"• {campo}: {info['propiedades_mejorables']} propiedades mejorables ({info['porcentaje_mejorable']:.1f}%)")

        # Recomendaciones
        if reporte['recomendaciones']:
            print(f"\n[RECOMENDACIONES]:")
            for i, rec in enumerate(reporte['recomendaciones'], 1):
                print(f"{i}. {rec}")

        print("\n" + "="*80)

def main():
    """Función principal."""
    analizador = AnalizadorCalidadProveedor02()

    try:
        # Cargar datos
        analizador.cargar_datos()

        # Generar reporte
        reporte = analizador.generar_reporte()

        # Imprimir resumen
        analizador.imprimir_resumen(reporte)

        # Guardar reporte completo
        analizador.guardar_reporte(reporte)

        print(f"\n[OK] Analisis completado exitosamente")
        print(f"[ARCHIVO] Reporte completo guardado en: docs/reporte_calidad_proveedor02.json")

    except Exception as e:
        logger.error(f"Error en el análisis: {e}")
        print(f"\n[ERROR] {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())