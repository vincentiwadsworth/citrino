#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Corrector de Precios con IA

Este módulo detecta y corrige precios inválidos usando información
de descripciones, URLs y otros campos de texto.
"""

import json
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import sys

# Agregar path para importar módulos
sys.path.append(str(Path(__file__).parent))

from llm_integration import LLMIntegration

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PriceCorrector:
    """Detector y corrector de precios inválidos."""

    def __init__(self):
        self.llm_integration = LLMIntegration()

        # Patrones regex para extracción de precios
        self.patrones_precio = [
            # Patrones en USD
            r'\$\s*([\d,\.]+)(?:\s*usd?)?',
            r'([\d,\.]+)\s*usd',
            r'([\d,\.]+)\s*dólares?',
            r'us\s*\$?\s*([\d,\.]+)',

            # Patrones en BOB/Bs
            r'([^\$]\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*bs',
            r'bs\s*([\d,\.]+)',
            r'bolivianos?\s*([\d,\.]+)',
            r'([\d,\.]+)\s*bob',

            # Patrones genéricos (contexto dependiente)
            r'precio[:\s]*\$?\s*([\d,\.]+)',
            r'costo[:\s]*\$?\s*([\d,\.]+)',
            r'valor[:\s]*\$?\s*([\d,\.]+)',
            r'monto[:\s]*\$?\s*([\d,\.]+)',
        ]

        # Palabras clave que indican precio
        self.keywords_precio = [
            'precio', 'costo', 'valor', 'monto', 'alquiler', 'venta',
            'mensual', 'dolares', 'usd', 'bolivianos', 'bs', 'bob'
        ]

        # Cache para optimizar procesamiento
        self.cache_correcciones = {}

    def es_precio_invalido(self, precio: str) -> bool:
        """Determina si un precio es inválido."""
        if not precio or str(precio) == 'nan':
            return True

        precio_str = str(precio).strip()

        # Precios claramente inválidos
        invalidos = [
            '0.00 bob', '0,00 bob', '0 bob', '0.00 usd', '0,00 usd', '0 usd',
            '0', '0.00', '0,00', 'nan', 'null', 'none', '-'
        ]

        if precio_str.lower() in invalidos:
            return True

        # Precios sospechosamente bajos (probablemente errores)
        try:
            # Extraer número del precio
            numero = re.sub(r'[^\d,\.]', '', precio_str)
            if numero:
                # Reemplazar comas por punto y convertir
                numero = numero.replace(',', '')
                valor = float(numero)

                # Menos de 10 es sospechoso
                if valor < 10:
                    return True
        except:
            pass

        return False

    def extraer_precios_con_regex(self, texto: str) -> List[Dict[str, Any]]:
        """Extrae precios de texto usando patrones regex."""
        if not texto or str(texto) == 'nan':
            return []

        texto = str(texto).lower()
        precios_encontrados = []

        for patron in self.patrones_precio:
            matches = re.finditer(patron, texto, re.IGNORECASE)
            for match in matches:
                precio_str = match.group(1)

                try:
                    # Limpiar y convertir el precio
                    precio_str = precio_str.replace(',', '')
                    precio = float(precio_str)

                    # Determinar moneda basada en el contexto
                    moneda = self._determinar_moneda_contexto(match.group(0), texto)

                    # Filtrar precios muy bajos (probablemente errores)
                    if precio >= 10:  # Mínimo 10 unidades
                        precios_encontrados.append({
                            'precio': precio,
                            'moneda': moneda,
                            'texto_original': match.group(0),
                            'posicion': match.start(),
                            'metodo': 'regex'
                        })
                except ValueError:
                    continue

        return precios_encontrados

    def _determinar_moneda_contexto(self, match_text: str, texto_completo: str) -> str:
        """Determina la moneda basada en el contexto."""
        match_text_lower = match_text.lower()
        texto_lower = texto_completo.lower()

        # Indicadores directos de moneda
        if 'usd' in match_text_lower or '$' in match_text:
            return 'USD'
        elif any(ind in match_text_lower for ind in ['bs', 'bob', 'boliviano']):
            return 'BOB'

        # Buscar contexto cercano
        contexto_inicio = max(0, texto_lower.find(match_text_lower) - 50)
        contexto_fin = min(len(texto_lower), texto_lower.find(match_text_lower) + len(match_text_lower) + 50)
        contexto = texto_lower[contexto_inicio:contexto_fin]

        if 'dólar' in contexto or 'dolar' in contexto or 'usd' in contexto or '$' in contexto:
            return 'USD'
        elif any(ind in contexto for ind in ['boliviano', 'bs', 'bob']):
            return 'BOB'

        # Heurística basada en el valor
        try:
            precio_num = float(re.sub(r'[^\d]', '', match_text))
            # En Bolivia, precios altos usualmente son USD
            if precio_num > 10000:
                return 'USD'
            else:
                return 'BOB'
        except:
            return 'BOB'  # Default

    def extraer_precio_con_ia(self, descripcion: str, titulo: str = "", amenities: str = "") -> Optional[Dict[str, Any]]:
        """Usa IA para extraer precios de texto complejo."""
        # Verificar cache primero
        cache_key = f"{descripcion}_{titulo}_{amenities}"
        if cache_key in self.cache_correcciones:
            return self.cache_correcciones[cache_key]

        # Preparar prompt para LLM
        prompt = self._crear_prompt_extraccion_precio(descripcion, titulo, amenities)

        try:
            # Usar LLM para extracción
            resultado = self.llm_integration.extract_structured_data(prompt, descripcion)

            # Procesar resultado
            precio_info = self._procesar_resultado_precio_ia(resultado)

            # Guardar en cache
            if precio_info:
                self.cache_correcciones[cache_key] = precio_info

            return precio_info

        except Exception as e:
            logger.error(f"Error extrayendo precio con IA: {e}")
            return None

    def _crear_prompt_extraccion_precio(self, descripcion: str, titulo: str, amenities: str) -> str:
        """Crea un prompt optimizado para extracción de precios."""
        return f"""
Analiza la siguiente información de una propiedad inmobiliaria y extrae información de precios.

INFORMACIÓN:
- Título: {titulo}
- Descripción: {descripcion}
- Amenities: {amenities}

INSTRUCCIONES:
1. Busca precios de venta o alquiler mencionados en el texto
2. Identifica si es precio total, mensual, o en cuotas
3. Determina la moneda (USD o BOB)
4. Extrae precios tanto explícitos como implícitos
5. Si hay múltiples precios, prioriza el más probable
6. Si no hay precios claros, retorna null

FORMATO DE RESPUESTA (JSON):
{{
    "precio_encontrado": <precio como número o null>,
    "moneda": "USD" o "BOB" o null,
    "tipo_precio": "venta" o "alquiler" o "cuota" o null,
    "contexto": <texto donde se encontró el precio>,
    "confianza": "alta" o "media" o "baja",
    "notas": <comentarios adicionales>
}}

EJEMPLOS:
- "Precio: $us 400.000" → precio: 400000, moneda: USD, tipo: venta
- "Bs. 550 mensuales" → precio: 550, moneda: BOB, tipo: alquiler
- "Alquiler de 400bs" → precio: 400, moneda: BOB, tipo: alquiler

Analiza la información proporcionada y responde únicamente con el JSON estructurado.
"""

    def _procesar_resultado_precio_ia(self, resultado: str) -> Optional[Dict[str, Any]]:
        """Procesa el resultado del LLM para extracción de precios."""
        try:
            if isinstance(resultado, str):
                # Limpiar el resultado
                resultado = resultado.strip()
                if resultado.startswith('```json'):
                    resultado = resultado[7:]
                if resultado.endswith('```'):
                    resultado = resultado[:-3]

                precio_info = json.loads(resultado)

                # Validar estructura básica
                if isinstance(precio_info, dict) and 'precio_encontrado' in precio_info:
                    # Validar que el precio sea un número válido
                    if precio_info['precio_encontrado'] is not None:
                        try:
                            precio_info['precio_encontrado'] = float(precio_info['precio_encontrado'])
                            if precio_info['precio_encontrado'] > 0:
                                precio_info['metodo'] = 'ia'
                                return precio_info
                        except:
                            pass

            return None

        except json.JSONDecodeError as e:
            logger.error(f"Error parseando resultado JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error procesando resultado IA: {e}")
            return None

    def corregir_precio_propiedad(self, propiedad: Dict[str, Any]) -> Dict[str, Any]:
        """Corrige el precio de una propiedad si es inválido."""
        precio_actual = propiedad.get('Precio', '')
        titulo = propiedad.get('titulo', '') or propiedad.get('Título', '')
        descripcion = propiedad.get('descripcion', '') or propiedad.get('Descripción', '')
        amenities = propiedad.get('Amenities', '')

        # Si el precio es válido, no hacer nada
        if not self.es_precio_invalido(precio_actual):
            return propiedad

        logger.info(f"Corrigiendo precio inválido para propiedad {propiedad.get('id', 'unknown')}: {precio_actual}")

        # Paso 1: Extraer precios con regex (rápido)
        texto_completo = f"{titulo} {descripcion} {amenities}"
        precios_regex = self.extraer_precios_con_regex(texto_completo)

        # Paso 2: Si regex encontró precios, usar el mejor
        if precios_regex:
            mejor_precio = self._seleccionar_mejor_precio(precios_regex, descripcion)
            if mejor_precio:
                return self._aplicar_correccion_precio(propiedad, mejor_precio)

        # Paso 3: Usar IA si regex no funcionó
        precio_ia = self.extraer_precio_con_ia(descripcion, titulo, amenities)
        if precio_ia and precio_ia.get('precio_encontrado'):
            precio_ia_structured = {
                'precio': precio_ia['precio_encontrado'],
                'moneda': precio_ia.get('moneda', 'BOB'),
                'texto_original': precio_ia.get('contexto', ''),
                'metodo': 'ia',
                'confianza': precio_ia.get('confianza', 'media'),
                'tipo_precio': precio_ia.get('tipo_precio', 'venta')
            }
            return self._aplicar_correccion_precio(propiedad, precio_ia_structured)

        # Paso 4: No se pudo corregir
        propiedad['precio_corregido'] = None
        propiedad['precio_error'] = 'No se encontró precio válido'
        return propiedad

    def _seleccionar_mejor_precio(self, precios: List[Dict[str, Any]], descripcion: str) -> Optional[Dict[str, Any]]:
        """Selecciona el mejor precio de una lista de candidatos."""
        if not precios:
            return None

        # Ordenar por criterios de calidad
        precios_ordenados = sorted(precios, key=lambda p: (
            # Preferir precios con mayor confianza (palabras clave cercanas)
            self._calcular_confianza_precio(p, descripcion),
            # Preferir precios en USD para inmuebles
            1 if p['moneda'] == 'USD' else 0,
            # Preferir precios más altos (probablemente precios de venta)
            p['precio']
        ), reverse=True)

        return precios_ordenados[0]

    def _calcular_confianza_precio(self, precio_info: Dict[str, Any], descripcion: str) -> int:
        """Calcula un puntaje de confianza para un precio extraído."""
        texto_precio = precio_info['texto_original'].lower()
        descripcion_lower = descripcion.lower()

        confianza = 0

        # Palabras clave de precio cerca
        for keyword in self.keywords_precio:
            if keyword in texto_precio:
                confianza += 2

        # Símbolos de moneda
        if '$' in texto_precio or 'usd' in texto_precio:
            confianza += 1
        elif 'bs' in texto_precio or 'boliviano' in texto_precio:
            confianza += 1

        # Valores realistas
        precio = precio_info['precio']
        if 100 <= precio <= 1000000:  # Rango realista
            confianza += 1

        return confianza

    def _aplicar_correccion_precio(self, propiedad: Dict[str, Any], precio_info: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica la corrección de precio a una propiedad."""
        propiedad['precio_original'] = propiedad.get('Precio', '')
        propiedad['precio_corregido'] = precio_info['precio']
        propiedad['moneda_corregida'] = precio_info['moneda']
        propiedad['precio_metodo'] = precio_info['metodo']
        propiedad['precio_confianza'] = precio_info.get('confianza', 'media')
        propiedad['precio_contexto'] = precio_info.get('texto_original', '')

        # Formatear precio corregido
        precio_formateado = f"{precio_info['precio']:,.2f} {precio_info['moneda']}"
        propiedad['Precio'] = precio_formateado

        # Marcar como corregido
        propiedad['precio_status'] = 'corregido'

        logger.info(f"Precio corregido: {propiedad['precio_original']} → {precio_formateado} ({precio_info['metodo']})")

        return propiedad

    def procesar_lote_propiedades(self, propiedades: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Procesa un lote de propiedades corrigiendo precios inválidos."""
        propiedades_procesadas = []
        stats = {
            'total_propiedades': len(propiedades),
            'precios_invalidos': 0,
            'precios_corregidos': 0,
            'correcciones_regex': 0,
            'correcciones_ia': 0,
            'errores': 0,
            'metodos_usados': {}
        }

        for i, propiedad in enumerate(propiedades):
            try:
                precio = propiedad.get('Precio', '')
                if self.es_precio_invalido(precio):
                    stats['precios_invalidos'] += 1

                    # Corregir precio
                    propiedad_corregida = self.corregir_precio_propiedad(propiedad)

                    # Actualizar estadísticas
                    if propiedad_corregida.get('precio_status') == 'corregido':
                        stats['precios_corregidos'] += 1
                        metodo = propiedad_corregida.get('precio_metodo', 'desconocido')
                        stats['metodos_usados'][metodo] = stats['metodos_usados'].get(metodo, 0) + 1

                        if metodo == 'regex':
                            stats['correcciones_regex'] += 1
                        elif metodo == 'ia':
                            stats['correcciones_ia'] += 1
                else:
                    propiedad['precio_status'] = 'valido'

                propiedades_procesadas.append(propiedad)

                # Progress logging
                if (i + 1) % 100 == 0:
                    logger.info(f"Procesadas {i + 1}/{len(propiedades)} propiedades")

            except Exception as e:
                logger.error(f"Error procesando propiedad {propiedad.get('id', 'unknown')}: {e}")
                stats['errores'] += 1
                propiedades_procesadas.append(propiedad)

        return propiedades_procesadas, stats

    def generar_reporte_correccion(self, stats: Dict[str, Any]) -> str:
        """Genera un reporte del proceso de corrección."""
        total = stats['total_propiedades']
        invalidos = stats['precios_invalidos']
        corregidos = stats['precios_corregidos']

        reporte = f"""
REPORTE DE CORRECCIÓN DE PRECIOS
{'='*50}

Propiedades procesadas: {total}
Precios inválidos detectados: {invalidos} ({(invalidos/total)*100:.1f}%)
Precios corregidos exitosamente: {corregidos} ({(corregidos/invalidos)*100:.1f}% de inválidos)

Métodos de corrección utilizados:
"""
        for metodo, count in stats['metodos_usados'].items():
            reporte += f"  • {metodo}: {count} propiedades\n"

        reporte += f"""
Eficiencia del proceso:
  • Tasa de corrección: {(corregidos/invalidos)*100:.1f}% de precios inválidos
  • Errores: {stats['errores']}
  • Precios sin corregir: {invalidos - corregidos}
"""

        return reporte

def main():
    """Función principal para testing."""
    print("Probando corrector de precios...")

    corrector = PriceCorrector()

    # Caso de prueba
    test_propiedad = {
        'id': 'test_1',
        'Precio': '0.00 BOB',
        'titulo': 'TERRENO EN VENTA EN ZONA NORTE',
        'descripcion': 'TERRENO EN VENTA EN ZONA NORTE\nURBANIZACIÓN CATALUÑA\nIDEAL PARA INVERSIONISTAS\n Superficie: 2.500 m2\nZona Norte entre Beni y Banzer\nPrecio: $us 400.000.-',
        'Amenities': ''
    }

    print(f"Propiedad de prueba:")
    print(f"  Precio original: {test_propiedad['Precio']}")
    print(f"  Descripción: {test_propiedad['descripcion'][:100]}...")

    resultado = corrector.corregir_precio_propiedad(test_propiedad.copy())
    print(f"\nResultado:")
    print(f"  Precio corregido: {resultado.get('precio_corregido', 'No corregido')}")
    print(f"  Método: {resultado.get('precio_metodo', 'N/A')}")
    print(f"  Confianza: {resultado.get('precio_confianza', 'N/A')}")

if __name__ == "__main__":
    main()