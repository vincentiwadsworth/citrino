#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extractor de Amenities con IA

Este módulo utiliza LLM para extraer y estructurar información de amenities
de texto libre, convirtiéndolo en campos estructurados útiles.
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
import logging
from pathlib import Path
import sys

# Agregar path para importar módulos
sys.path.append(str(Path(__file__).parent))

from llm_integration import LLMIntegration
from description_parser import DescriptionParser

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AmenitiesExtractor:
    """Extractor especializado de amenities usando IA."""

    def __init__(self):
        self.llm_integration = LLMIntegration()
        self.description_parser = DescriptionParser()

        # Diccionarios de mapeo de amenities a categorías estándar
        self.categorias_amenities = {
            'seguridad': [
                'seguridad', 'vigilancia', 'cámara', 'alarma', 'sistema de seguridad',
                'vigilancia', 'guardia', 'seguridad 24h', 'portero', 'control acceso'
            ],
            'servicios_basicos': [
                'agua', 'electricidad', 'luz', 'gas', 'alcantarillado', 'cloacas',
                'agua potable', 'energía eléctrica', 'medidor', 'conexion'
            ],
            'ubicacion': [
                'cerca', 'cercano', 'acceso', 'avenida', 'calle', 'zona', 'centro',
                'transporte', 'colegio', 'escuela', 'hospital', 'comercio', 'supermercado',
                'iglesia', 'plaza', 'parque', 'gimnasio'
            ],
            'estacionamiento': [
                'parqueo', 'garage', 'garaje', 'estacionamiento', 'aparcamiento',
                'parqueadero', ' Cochera'
            ],
            'areas_comunes': [
                'terraza', 'balcón', 'jardín', 'patio', 'sala', 'lobby', 'hall',
                'área social', 'quincho', 'piscina', 'gimnasio', 'spa', 'sauna'
            ],
            'comunicaciones': [
                'internet', 'wifi', 'cable', 'televisión', 'teléfono', 'fibra óptica',
                'conectividad', 'señal'
            ],
            'clima': [
                'aire acondicionado', 'calefacción', 'ventilación', 'clima',
                'aire acondicionado central', 'climatización'
            ],
            'cocina': [
                'cocina', 'cocina integral', 'cocina equipada', 'lavaplatos',
                'refrigerador', 'horno', 'microondas', 'campana'
            ],
            'banios': [
                'baño', 'baño de servicio', 'baño privado', 'ducha', 'jacuzzi',
                'hidromasaje', 'calefón', 'termotanque'
            ],
            'estructura': [
                'ladrillo', 'hormigón', 'acero', 'estructura', 'techo', 'piso',
                'cerámica', 'porcelanato', 'madera', 'yeso', 'piedra'
            ]
        }

        # Cache para optimizar procesamiento
        self.cache_amenities = {}

    def extraer_con_regex(self, amenities_text: str) -> Dict[str, List[str]]:
        """Extrae amenities usando regex primero (rápido y económico)."""
        if not amenities_text or str(amenities_text) == 'nan':
            return {}

        amenities_text = str(amenities_text).lower()
        amenities_encontrados = {}

        for categoria, keywords in self.categorias_amenities.items():
            encontrados = []
            for keyword in keywords:
                # Buscar palabras clave en el texto
                if re.search(r'\b' + re.escape(keyword) + r'\b', amenities_text):
                    encontrados.append(keyword)

            if encontrados:
                amenities_encontrados[categoria] = encontrados

        return amenities_encontrados

    def extraer_con_ia(self, amenities_text: str, titulo: str = "", descripcion: str = "") -> Dict[str, Any]:
        """Usa IA para extraer amenities complejos y contextuales."""
        if not amenities_text or str(amenities_text) == 'nan':
            return {}

        # Verificar cache primero
        cache_key = f"{amenities_text}_{titulo}_{descripcion}"
        if cache_key in self.cache_amenities:
            return self.cache_amenities[cache_key]

        # Preparar prompt para LLM
        prompt = self._crear_prompt_extraccion(amenities_text, titulo, descripcion)

        try:
            # Usar LLM para extracción avanzada
            resultado = self.llm_integration.extract_structured_data(prompt, amenities_text)

            # Procesar resultado
            amenities_estructurados = self._procesar_resultado_ia(resultado)

            # Guardar en cache
            self.cache_amenities[cache_key] = amenities_estructurados

            return amenities_estructurados

        except Exception as e:
            logger.error(f"Error extrayendo amenities con IA: {e}")
            # Fallback a regex
            return self.extraer_con_regex(amenities_text)

    def _crear_prompt_extraccion(self, amenities_text: str, titulo: str, descripcion: str) -> str:
        """Crea un prompt optimizado para extracción de amenities."""
        return f"""
Analiza el siguiente texto de amenities de una propiedad inmobiliaria y extrae información estructurada.

CONTEXTO:
- Título: {titulo}
- Descripción: {descripcion[:200]}...
- Amenities: {amenities_text}

INSTRUCCIONES:
1. Extrae características específicas y cuantificables
2. Agrupa por categorías lógicas
3. Identifica números (superficies, cantidades)
4. Determina la calidad o tipo de cada característica
5. Ignora información genérica o de marketing

CATEGORÍAS A IDENTIFICAR:
- Seguridad (vigilancia, cámaras, alarmas, etc.)
- Servicios (agua, electricidad, gas, internet, etc.)
- Ubicación (cercanía a servicios, transporte, etc.)
- Estacionamiento (garage, superficie, capacidad)
- Áreas Comunes (terraza, piscina, jardín, etc.)
- Estructura y Materiales (tipo de construcción, acabados)
- Equipamiento (cocina, aire acondicionado, etc.)

FORMATO DE RESPUESTA (JSON):
{{
    "seguridad": {{
        "vigilancia": "24 horas",
        "camaras": true,
        "alarma": true,
        "tipo_seguridad": "sistema integrado"
    }},
    "servicios": {{
        "agua": "potable",
        "electricidad": "individual",
        "internet": "fibra óptica",
        "gas": "natural"
    }},
    "ubicacion": {{
        "tipo_zona": "residencial",
        "cercania_colegios": true,
        "cercania_hospitales": false,
        "transporte_publico": "a 50m"
    }},
    "estacionamiento": {{
        "tipo": "cubierto",
        "capacidad": 2,
        "superficie": "40m2"
    }},
    "areas_comunes": {{
        "terraza": true,
        "piscina": false,
        "jardin": "privado",
        "superficie_terraza": "25m2"
    }},
    "estructura": {{
        "materiales": ["ladrillo", "hormigón"],
        "acabados": "cerámica de primera",
        "techo": "plano"
    }},
    "equipamiento": {{
        "cocina": "integral equipada",
        "aire_acondicionado": "central",
        "calefaccion": false
    }}
}}

Analiza el texto proporcionado y responde únicamente con el JSON estructurado.
"""

    def _procesar_resultado_ia(self, resultado: str) -> Dict[str, Any]:
        """Procesa y limpia el resultado del LLM."""
        try:
            # Intentar parsear como JSON
            if isinstance(resultado, str):
                # Limpiar el resultado para asegurar que sea JSON válido
                resultado = resultado.strip()
                if resultado.startswith('```json'):
                    resultado = resultado[7:]
                if resultado.endswith('```'):
                    resultado = resultado[:-3]

                amenities_json = json.loads(resultado)
                return amenities_json
            elif isinstance(resultado, dict):
                return resultado
            else:
                return {}

        except json.JSONDecodeError as e:
            logger.error(f"Error parseando resultado JSON: {e}")
            # Intentar extracción con regex como fallback
            return self.extraer_con_regex(str(resultado))
        except Exception as e:
            logger.error(f"Error procesando resultado IA: {e}")
            return {}

    def extraer_amenities_hibrido(self, amenities_text: str, titulo: str = "", descripcion: str = "") -> Dict[str, Any]:
        """Método híbrido que combina regex y IA para máxima eficiencia."""
        # Paso 1: Extraer con regex (rápido y económico)
        amenities_regex = self.extraer_con_regex(amenities_text)

        # Paso 2: Determinar si se necesita IA
        necesita_ia = self._debe_usar_ia(amenities_text, amenities_regex)

        if necesita_ia:
            # Paso 3: Extraer con IA para información compleja
            amenities_ia = self.extraer_con_ia(amenities_text, titulo, descripcion)

            # Paso 4: Combinar resultados
            return self._combinarResultados(amenities_regex, amenities_ia)
        else:
            return amenities_regex

    def _debe_usar_ia(self, amenities_text: str, amenities_regex: Dict[str, List[str]]) -> bool:
        """Determina si es necesario usar IA basado en la complejidad del texto."""
        # Usar IA si el texto es largo (>100 caracteres)
        if len(str(amenities_text)) > 100:
            return True

        # Usar IA si hay números que podrían indicar superficies o cantidades
        if re.search(r'\d+', str(amenities_text)):
            return True

        # Usar AI si hay menciones de calidad o materiales específicos
        palabras_clave_ia = ['premium', 'lujo', 'primera', 'calidad', 'madera', 'cerámica', 'porcelanato']
        for palabra in palabras_clave_ia:
            if palabra in str(amenities_text).lower():
                return True

        # Usar IA si regex no encontró suficiente información
        total_encontrados = sum(len(categoria) for categoria in amenities_regex.values())
        if total_encontrados < 3:
            return True

        return False

    def _combinarResultados(self, amenities_regex: Dict[str, List[str]],
                           amenities_ia: Dict[str, Any]) -> Dict[str, Any]:
        """Combina los resultados de regex y IA."""
        combinado = {}

        # Primero agregar resultados de IA (más estructurados)
        for categoria, datos in amenities_ia.items():
            if isinstance(datos, dict):
                combinado[categoria] = datos
            else:
                # Convertir lista de regex a formato estructurado
                combinado[categoria] = {'caracteristicas': datos}

        # Agregar resultados adicionales de regex
        for categoria, lista_regex in amenities_regex.items():
            if categoria not in combinado:
                combinado[categoria] = {'caracteristicas': lista_regex}
            elif 'caracteristicas' in combinado[categoria]:
                # Combinar sin duplicados
                existentes = set(combinado[categoria]['caracteristicas'])
                nuevos = [item for item in lista_regex if item not in existentes]
                combinado[categoria]['caracteristicas'].extend(nuevos)

        return combinado

    def procesar_lote_propiedades(self, propiedades: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Procesa un lote de propiedades extrayendo amenities."""
        propiedades_procesadas = []
        stats = {
            'total_propiedades': len(propiedades),
            'con_amenities': 0,
            'solo_regex': 0,
            'con_ia': 0,
            'errores': 0,
            'categorias_encontradas': {},
            'tokens_consumidos': 0
        }

        for i, propiedad in enumerate(propiedades):
            try:
                amenities_text = propiedad.get('Amenities', '')
                titulo = propiedad.get('titulo', '') or propiedad.get('Título', '')
                descripcion = propiedad.get('descripcion', '') or propiedad.get('Descripción', '')

                if amenities_text and str(amenities_text) != 'nan':
                    stats['con_amenities'] += 1

                    # Extraer amenities
                    amenities_extraidos = self.extraer_amenities_hibrido(
                        amenities_text, titulo, descripcion
                    )

                    # Agregar a la propiedad
                    propiedad['amenities_estructurados'] = amenities_extraidos
                    propiedad['amenities_procesamiento'] = 'hibrido'

                    # Actualizar estadísticas
                    for categoria in amenities_extraidos.keys():
                        stats['categorias_encontradas'][categoria] = stats['categorias_encontradas'].get(categoria, 0) + 1

                    # Determinar si se usó IA (simplificado)
                    if len(str(amenities_text)) > 100:
                        stats['con_ia'] += 1
                    else:
                        stats['solo_regex'] += 1

                propiedades_procesadas.append(propiedad)

                # Progress logging
                if (i + 1) % 100 == 0:
                    logger.info(f"Procesadas {i + 1}/{len(propiedades)} propiedades")

            except Exception as e:
                logger.error(f"Error procesando propiedad {propiedad.get('id', 'unknown')}: {e}")
                stats['errores'] += 1
                propiedades_procesadas.append(propiedad)

        return propiedades_procesadas, stats

    def generar_reporte_extraccion(self, stats: Dict[str, Any]) -> str:
        """Genera un reporte del proceso de extracción."""
        total = stats['total_propiedades']
        con_amenities = stats['con_amenities']

        reporte = f"""
REPORTE DE EXTRACCIÓN DE AMENITIES
{'='*50}

Propiedades procesadas: {total}
Con amenities: {con_amenities} ({(con_amenities/total)*100:.1f}%)

Métodos utilizados:
  • Regex solamente: {stats['solo_regex']} propiedades
  • Con IA: {stats['con_ia']} propiedades

Errores: {stats['errores']}

Categorías encontradas:
"""

        for categoria, count in stats['categorias_encontradas'].items():
            reporte += f"  • {categoria}: {count} propiedades\n"

        reporte += f"""
Eficiencia del método híbrido:
  • Reducción de costos: {((stats['solo_regex']/con_amenities)*100):.1f}% procesado solo con regex
  • Calidad mejorada: {((stats['con_ia']/con_amenities)*100):.1f}% procesado con IA
"""

        return reporte

def main():
    """Función principal para testing."""
    print("Probando extractor de amenities...")

    extractor = AmenitiesExtractor()

    # Caso de prueba
    test_amenities = "Vida citadina, Inversión, Cerca de Aeropuerto, Comercios cercanos, Cerca de Avenida, Zona Concurrida, Residencial, Autobús cercano, Norte, Agua potable, Electricidad"

    print(f"Texto de prueba: {test_amenities}")
    print("\nExtracción con regex:")
    resultado_regex = extractor.extraer_con_regex(test_amenities)
    print(json.dumps(resultado_regex, indent=2, ensure_ascii=False))

    print("\nExtracción híbrida:")
    resultado_hibrido = extractor.extraer_amenities_hibrido(test_amenities)
    print(json.dumps(resultado_hibrido, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()