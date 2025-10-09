#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parser de descripciones de propiedades usando sistema híbrido Regex + LLM.

Este módulo extrae datos estructurados de descripciones en texto libre,
usando primero regex para reducir tokens LLM, y solo recurre al modelo
cuando es necesario completar información faltante.
"""

import json
import os
import logging
import time
from typing import Dict, Any, Optional
from pathlib import Path

from llm_integration import LLMIntegration, LLMConfig
from regex_extractor import RegexExtractor

logger = logging.getLogger(__name__)


class DescriptionParser:
    """Parser de descripciones usando sistema híbrido Regex + LLM."""

    def __init__(self, cache_path: Optional[str] = None, use_regex_first: bool = True):
        """
        Inicializa el parser.

        Args:
            cache_path: Ruta al archivo de caché JSON. Si None, usa default.
            use_regex_first: Si debe usar regex antes del LLM (reduce tokens)
        """
        self.llm = LLMIntegration()
        self.regex_extractor = RegexExtractor() if use_regex_first else None
        self.use_regex_first = use_regex_first
        self.cache_path = cache_path or "data/.cache_llm_extractions.json"
        self.cache = self._load_cache()
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "llm_calls": 0,
            "regex_only_success": 0,  # Nuevo: casos donde regex fue suficiente
            "regex_partial_success": 0,  # Nuevo: casos donde regex ayudó parcialmente
            "llm_only": 0,  # Nuevo: casos donde solo usamos LLM
            "errors": 0
        }
        self.fallback_stats = {
            "zai_success": 0,
            "zai_failed": 0,
            "openrouter_used": 0
        }

    def _load_cache(self) -> Dict[str, Any]:
        """Carga el caché desde disco."""
        cache_file = Path(self.cache_path)
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error cargando caché: {e}")
        return {}

    def _save_cache(self):
        """Guarda el caché a disco."""
        try:
            cache_file = Path(self.cache_path)
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Error guardando caché: {e}")

    def _merge_extracted_data(self, regex_data: Dict[str, Any], llm_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combina datos de regex y LLM, dando prioridad a regex.
        
        Args:
            regex_data: Datos extraídos por regex
            llm_data: Datos extraídos por LLM
            
        Returns:
            Datos combinados
        """
        result = {}
        
        # Campos a combinar
        campos = ['precio', 'moneda', 'habitaciones', 'banos', 'superficie',
                  'superficie_terreno', 'superficie_construida', 'zona', 'tipo_propiedad']
        
        for campo in campos:
            # Prioridad a regex si tiene valor
            if regex_data.get(campo):
                result[campo] = regex_data[campo]
            elif llm_data.get(campo):
                result[campo] = llm_data[campo]
            else:
                result[campo] = None
        
        # Combinar características (unir ambas listas)
        result['caracteristicas'] = []
        if regex_data.get('amenities'):
            result['caracteristicas'].extend(regex_data['amenities'])
        if llm_data.get('caracteristicas'):
            result['caracteristicas'].extend(llm_data['caracteristicas'])
        
        # Referencias de ubicación de regex
        if regex_data.get('referencias_ubicacion'):
            result['referencias_ubicacion'] = regex_data['referencias_ubicacion']
        
        return result
    
    def _build_optimized_prompt(self, descripcion: str, titulo: str, regex_data: Dict[str, Any]) -> str:
        """
        Construye un prompt optimizado cuando ya tenemos datos de regex.
        Solo pide al LLM que complete lo que falta, reduciendo tokens.
        
        Args:
            descripcion: Texto de la descripción
            titulo: Título de la propiedad
            regex_data: Datos ya extraídos por regex
            
        Returns:
            Prompt optimizado
        """
        texto_completo = f"{titulo}\n\n{descripcion}".strip()
        
        # Identificar qué encontró regex
        encontrados = []
        faltantes = []
        
        if regex_data.get('precio'):
            encontrados.append(f"precio: {regex_data['precio']} {regex_data.get('moneda', 'USD')}")
        else:
            faltantes.append('precio')
        
        if regex_data.get('habitaciones'):
            encontrados.append(f"habitaciones: {regex_data['habitaciones']}")
        else:
            faltantes.append('habitaciones')
        
        if regex_data.get('banos'):
            encontrados.append(f"baños: {regex_data['banos']}")
        else:
            faltantes.append('baños')
        
        if regex_data.get('superficie'):
            encontrados.append(f"superficie: {regex_data['superficie']} m²")
        else:
            faltantes.append('superficie')
        
        if regex_data.get('zona'):
            encontrados.append(f"zona: {regex_data['zona']}")
        else:
            faltantes.append('zona')
        
        if not regex_data.get('tipo_propiedad'):
            faltantes.append('tipo_propiedad')
        
        # Construir prompt corto
        prompt = f"""Analiza esta descripción de propiedad y completa SOLO los datos faltantes.

TEXTO:
{texto_completo}

DATOS YA EXTRAÍDOS:
{', '.join(encontrados) if encontrados else 'ninguno'}

COMPLETA SOLO ESTOS CAMPOS:
{', '.join(faltantes)}

Responde ÚNICAMENTE con JSON:
{{
"""
        
        # Solo pedir los campos faltantes
        if 'precio' in faltantes:
            prompt += '    "precio": <número o null>,\n    "moneda": "USD" o "Bs" o null,\n'
        if 'habitaciones' in faltantes:
            prompt += '    "habitaciones": <número o null>,\n'
        if 'baños' in faltantes:
            prompt += '    "banos": <número o null>,\n'
        if 'superficie' in faltantes:
            prompt += '    "superficie": <número en m² o null>,\n'
        if 'zona' in faltantes:
            prompt += '    "zona": "<zona de Santa Cruz o null>",\n'
        if 'tipo_propiedad' in faltantes:
            prompt += '    "tipo_propiedad": "casa", "departamento", "terreno", etc o null,\n'
        
        prompt += '    "caracteristicas": [<lista de características adicionales>]\n'
        prompt += '}\n\nJSON:'
        
        return prompt
    
    def _build_extraction_prompt(self, descripcion: str, titulo: str = "") -> str:
        """
        Construye el prompt para extraer datos estructurados.

        Args:
            descripcion: Texto de la descripción
            titulo: Título de la propiedad (opcional)

        Returns:
            Prompt formateado
        """
        texto_completo = f"{titulo}\n\n{descripcion}".strip()
        
        return f"""Analiza esta descripción de propiedad inmobiliaria y extrae datos estructurados.

TEXTO:
{texto_completo}

Responde ÚNICAMENTE con un objeto JSON con esta estructura exacta:
{{
    "precio": <número en USD o null>,
    "moneda": "USD" o "Bs" o null,
    "habitaciones": <número o null>,
    "banos": <número o null>,
    "superficie": <número en m² o null>,
    "superficie_terreno": <número en m² o null>,
    "superficie_construida": <número en m² o null>,
    "zona": "<nombre de zona/barrio de Santa Cruz o null>",
    "tipo_propiedad": "casa", "departamento", "terreno", "local", "oficina" o null,
    "caracteristicas": [<lista de características relevantes>]
}}

REGLAS IMPORTANTES:
1. Precio: Busca valores numéricos con $, USD, Bs, o palabras como "precio", "valor", "costo"
2. Si precio está en Bs (bolivianos), indica moneda: "Bs", si está en USD o $, indica "USD"
3. Habitaciones: busca "dormitorios", "habitaciones", "recámaras", "dorm", "hab"
4. Baños: busca "baños", "baño", "bath"
5. Superficie: busca "m²", "m2", "metros cuadrados", "mt2"
6. Zona: identifica barrios/zonas de Santa Cruz (Equipetrol, Centro, Norte, Sur, Palmar, Urubó, etc)
7. Tipo: identifica si es casa, departamento, terreno, local comercial, oficina, etc
8. Si no encuentras un dato, usa null
9. Responde SOLO el JSON, sin texto adicional

JSON:"""

    def _parse_llm_extraction(self, response_text: str) -> Dict[str, Any]:
        """
        Parsea la respuesta del LLM.

        Args:
            response_text: Texto de respuesta del LLM

        Returns:
            Diccionario con los datos extraídos

        Raises:
            ValueError: Si no se puede parsear el JSON
        """
        try:
            # Limpiar respuesta
            response_text = response_text.strip()
            
            # Remover marcadores de código
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            # Parsear JSON
            data = json.loads(response_text.strip())
            
            # Validar estructura básica
            if not isinstance(data, dict):
                raise ValueError("Respuesta no es un objeto JSON")
            
            # Validar y limpiar rangos
            if data.get('precio'):
                precio = float(data['precio'])
                # Validar rango razonable (10k - 50M USD, o 70k - 350M Bs)
                if data.get('moneda') == 'Bs':
                    if not (70000 <= precio <= 350000000):
                        logger.warning(f"Precio fuera de rango razonable en Bs: {precio}")
                        data['precio'] = None
                else:
                    if not (10000 <= precio <= 50000000):
                        logger.warning(f"Precio fuera de rango razonable en USD: {precio}")
                        data['precio'] = None
            
            if data.get('habitaciones'):
                hab = int(data['habitaciones'])
                if not (1 <= hab <= 20):
                    logger.warning(f"Habitaciones fuera de rango: {hab}")
                    data['habitaciones'] = None
            
            if data.get('banos'):
                banos = int(data['banos'])
                if not (1 <= banos <= 15):
                    logger.warning(f"Baños fuera de rango: {banos}")
                    data['banos'] = None
            
            if data.get('superficie'):
                sup = float(data['superficie'])
                if not (10 <= sup <= 100000):
                    logger.warning(f"Superficie fuera de rango: {sup}")
                    data['superficie'] = None
            
            return data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parseando JSON: {e}")
        except Exception as e:
            raise ValueError(f"Error procesando respuesta: {e}")

    def extract_from_description(
        self, 
        descripcion: str, 
        titulo: str = "",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Extrae datos estructurados de una descripción usando sistema híbrido.
        
        ESTRATEGIA:
        1. Primero intenta con regex (rápido, sin tokens)
        2. Si regex encuentra TODO, retorna sin llamar al LLM
        3. Si regex encuentra ALGO, llama al LLM solo para campos faltantes
        4. Si regex no encuentra NADA, usa LLM completo

        Args:
            descripcion: Texto de la descripción
            titulo: Título de la propiedad (opcional)
            use_cache: Si debe usar caché

        Returns:
            Diccionario con los datos extraídos
        """
        self.stats["total_requests"] += 1
        
        # Crear clave de caché
        cache_key = f"{titulo}|{descripcion[:200]}"
        
        # Verificar caché
        if use_cache and cache_key in self.cache:
            self.stats["cache_hits"] += 1
            logger.debug("Cache hit para descripción")
            return self.cache[cache_key]
        
        # PASO 1: Intentar extracción con regex primero
        regex_data = None
        if self.regex_extractor:
            regex_data = self.regex_extractor.extract_all(descripcion, titulo)
            campos_regex = regex_data.get('_regex_extraction_success', 0)
            logger.info(f"Regex extrajo {campos_regex} campos")
            
            # Si regex extrajo al menos los campos críticos, podemos evitar el LLM
            tiene_precio = regex_data.get('precio') is not None
            tiene_zona = regex_data.get('zona') is not None
            tiene_superficie = regex_data.get('superficie') is not None
            
            # Criterio: si tenemos precio Y (zona O superficie), es suficiente
            if tiene_precio and (tiene_zona or tiene_superficie):
                self.stats["regex_only_success"] += 1
                logger.info("✓ Regex fue suficiente, no se necesita LLM")
                
                # Agregar metadatos
                regex_data["_extraction_method"] = "regex_only"
                regex_data["_llm_provider"] = None
                regex_data["_llm_model"] = None
                regex_data["_fallback_usado"] = False
                
                if use_cache:
                    self.cache[cache_key] = regex_data
                
                return regex_data
        
        # PASO 2: Llamar al LLM (completo o parcial)
        try:
            # Si tenemos datos de regex, construir prompt optimizado
            if regex_data and regex_data.get('_regex_extraction_success', 0) > 0:
                self.stats["regex_partial_success"] += 1
                prompt = self._build_optimized_prompt(descripcion, titulo, regex_data)
                logger.info("Usando prompt optimizado con datos de regex")
            else:
                self.stats["llm_only"] += 1
                prompt = self._build_extraction_prompt(descripcion, titulo)
                logger.info("Usando prompt completo (regex no encontró nada)")
            
            # Llamar al LLM con fallback
            logger.info(f"Llamando LLM para extraer/completar datos...")
            self.stats["llm_calls"] += 1
            
            resultado_llm = self.llm.consultar_con_fallback(prompt, use_fallback=True)
            
            # Actualizar estadísticas de fallback
            provider_usado = resultado_llm["provider_usado"]
            if provider_usado == "zai":
                self.fallback_stats["zai_success"] += 1
            elif provider_usado == "openrouter":
                self.fallback_stats["openrouter_used"] += 1
            
            if resultado_llm["fallback_activado"]:
                logger.info(f">> Fallback activado: {resultado_llm['model_usado']}")
            
            # Parsear respuesta
            llm_data = self._parse_llm_extraction(resultado_llm["respuesta"])
            
            # PASO 3: Combinar datos de regex y LLM (regex tiene prioridad)
            if regex_data:
                final_data = self._merge_extracted_data(regex_data, llm_data)
                extraction_method = "hybrid"
            else:
                final_data = llm_data
                extraction_method = "llm_only"
            
            # Agregar metadatos
            final_data["_extraction_method"] = extraction_method
            final_data["_llm_provider"] = resultado_llm["provider_usado"]
            final_data["_llm_model"] = resultado_llm["model_usado"]
            final_data["_fallback_usado"] = resultado_llm["fallback_activado"]
            
            # Guardar en caché
            if use_cache:
                self.cache[cache_key] = final_data
                # Guardar caché cada 10 extracciones
                if self.stats["llm_calls"] % 10 == 0:
                    self._save_cache()
            
            return final_data
            
        except Exception as e:
            self.stats["errors"] += 1
            self.fallback_stats["zai_failed"] += 1
            logger.error(f"Error extrayendo datos: {e}")
            
            # Si tenemos datos de regex, retornar esos al menos
            if regex_data:
                logger.info("Retornando datos de regex debido a error en LLM")
                regex_data["_extraction_method"] = "regex_fallback"
                regex_data["_llm_provider"] = None
                regex_data["_llm_model"] = None
                regex_data["_fallback_usado"] = False
                return regex_data
            
            return {
                "precio": None,
                "moneda": None,
                "habitaciones": None,
                "banos": None,
                "superficie": None,
                "superficie_terreno": None,
                "superficie_construida": None,
                "zona": None,
                "tipo_propiedad": None,
                "caracteristicas": [],
                "_extraction_method": "error",
                "_llm_provider": None,
                "_llm_model": None,
                "_fallback_usado": False
            }

    def get_stats(self) -> Dict[str, int]:
        """Retorna estadísticas de uso."""
        return self.stats.copy()

    def save_cache(self):
        """Guarda el caché manualmente."""
        self._save_cache()

    def clear_cache(self):
        """Limpia el caché."""
        self.cache = {}
        self._save_cache()
