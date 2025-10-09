#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parser de descripciones de propiedades usando LLM.

Este módulo extrae datos estructurados de descripciones en texto libre,
especialmente útil para fuentes de datos autogestionadas.
"""

import json
import os
import logging
import time
from typing import Dict, Any, Optional
from pathlib import Path

from llm_integration import LLMIntegration, LLMConfig

logger = logging.getLogger(__name__)


class DescriptionParser:
    """Parser de descripciones usando LLM para extraer datos estructurados."""

    def __init__(self, cache_path: Optional[str] = None):
        """
        Inicializa el parser.

        Args:
            cache_path: Ruta al archivo de caché JSON. Si None, usa default.
        """
        self.llm = LLMIntegration()
        self.cache_path = cache_path or "data/.cache_llm_extractions.json"
        self.cache = self._load_cache()
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "llm_calls": 0,
            "errors": 0
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
        Extrae datos estructurados de una descripción.

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
        
        try:
            # Construir prompt
            prompt = self._build_extraction_prompt(descripcion, titulo)
            
            # Llamar al LLM con fallback
            logger.info(f"Llamando LLM para extraer datos...")
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
            extracted_data = self._parse_llm_extraction(resultado_llm["respuesta"])
            
            # Agregar metadatos
            extracted_data["_llm_provider"] = resultado_llm["provider_usado"]
            extracted_data["_llm_model"] = resultado_llm["model_usado"]
            extracted_data["_fallback_usado"] = resultado_llm["fallback_activado"]
            
            # Guardar en caché
            if use_cache:
                self.cache[cache_key] = extracted_data
                # Guardar caché cada 10 extracciones
                if self.stats["llm_calls"] % 10 == 0:
                    self._save_cache()
            
            return extracted_data
            
        except Exception as e:
            self.stats["errors"] += 1
            self.fallback_stats["zai_failed"] += 1
            logger.error(f"Error extrayendo datos: {e}")
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
