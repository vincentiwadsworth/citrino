#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extractor basado en regex para datos estructurados de descripciones del Proveedor 02.
Este módulo reduce significativamente el uso de tokens LLM al extraer información
con patrones regulares antes de recurrir al modelo de lenguaje.
"""

import re
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class RegexExtractor:
    """Extractor de datos usando patrones regex para reducir uso de LLM."""
    
    def __init__(self):
        """Inicializa los patrones regex para extracción de datos."""
        
        # Patrones de precio
        self.precio_patterns = [
            # $us 400.000.- o $us 400,000
            r'(?:precio[:\s]+)?\$\s*us\s*[\s]*([\d,.]+)',
            # $1,757,200 o $1.757.200
            r'(?:precio[:\s]+)?\$\s*([\d,.]+)',
            # Bs. 550.- o 660 Bs o Bs 700
            r'(?:precio[:\s]+)?(?:Bs\.?|bs\.?)\s*([\d,.]+)|(?:precio[:\s]+)?([\d,.]+)\s*(?:Bs\.?|bs\.?)',
        ]
        
        # Patrones de superficie
        self.superficie_patterns = [
            # Superficie: 2.500 m2 o Superficie construida: 12 m
            r'superficie(?:\s+construida)?[:\s]+([\d,.]+)\s*m',
            # 16 m2
            r'(\d+)\s*m[²2]',
            # sup. 3.5x2.5 o sup.(6.50x3.25)
            r'sup\.?\s*[\(]?([\d,.]+)\s*x\s*([\d,.]+)[\)]?',
        ]
        
        # Patrones de habitaciones
        self.habitaciones_patterns = [
            # 4 HABITACIONES EN ALQUILER
            r'(\d+)\s+habitacion(?:es)?',
            # 3 dormitorios
            r'(\d+)\s+dormitorio(?:s)?',
            # 2 hab o 3 dorm
            r'(\d+)\s+(?:hab|dorm)(?:s|\.)?',
        ]
        
        # Patrones de baños
        self.banos_patterns = [
            # baño privado, con Baño, 2 baños
            r'(\d+)?\s*ba[ñn]o(?:s)?(?:\s+privado)?',
            # bño privado (sin la ñ)
            r'(\d+)?\s*b[añn]o(?:s)?',
        ]
        
        # Patrones de zonas conocidas de Santa Cruz
        self.zonas_conocidas = [
            'equipetrol', 'urubó', 'urubo', 'zona norte', 'zona sur', 'zona este', 'zona oeste',
            'villa 1ro de mayo', 'villa primero de mayo', 'plan 3000', 'plan tres mil',
            'el cristo', 'la recoleta', 'av. monseñor rivero', 'av. banzer', 'av. beni',
            'radial 10', 'radial 13', 'radial 17', 'radial 19', 'radial 26', 'radial 27',
            '2do anillo', '3er anillo', '4to anillo', '5to anillo', '6to anillo', 
            '7mo anillo', '8vo anillo', '9no anillo', 'segundo anillo', 'tercer anillo',
            'cuarto anillo', 'quinto anillo', 'sexto anillo', 'séptimo anillo', 
            'octavo anillo', 'noveno anillo', 'las palmas', 'barrio equipetrol',
            'barrio hamacas', 'santos dumont', 'av. cristobal de mendoza',
            'av. busch', 'av. alemana', 'av. roca y coronado', 'av. paraguá',
            'zona central', 'centro', 'casco viejo', 'la ramada', 'mutualista',
            'virgen de luján', 'virgen de lujan', 'el trompillo', 'paraguá',
            'barrio 26 de septiembre', 'cambodromo', 'parque industrial',
            'cataluña', 'vida citadina'
        ]
        
        # Compilar patrones de zona (case insensitive)
        self.zona_pattern = re.compile(
            r'\b(' + '|'.join(re.escape(z) for z in self.zonas_conocidas) + r')\b',
            re.IGNORECASE
        )
        
        # Patrones de anillos y radiales
        self.anillo_pattern = re.compile(
            r'(\d+)(?:do|er|to|mo|vo|no)?\s+anillo',
            re.IGNORECASE
        )
        self.radial_pattern = re.compile(
            r'radial\s+(\d+)',
            re.IGNORECASE
        )
        
        # Patrones de amenities comunes
        self.amenities_keywords = [
            'piscina', 'parque', 'cancha', 'gym', 'gimnasio', 'seguridad', 
            'vigilancia', 'salon de eventos', 'área de juegos', 'jardín',
            'terraza', 'balcón', 'estacionamiento', 'garage', 'garaje',
            'cocina equipada', 'amoblado', 'amueblado', 'aire acondicionado',
            'calefacción', 'calefaccion', 'internet', 'wifi', 'cable'
        ]
    
    def extract_all(self, descripcion: str, titulo: str = "") -> Dict[str, Any]:
        """
        Extrae todos los datos posibles usando regex.
        
        Args:
            descripcion: Texto de la descripción
            titulo: Título de la propiedad (opcional)
            
        Returns:
            Diccionario con los datos extraídos
        """
        texto_completo = f"{titulo} {descripcion}".lower()
        
        resultado = {
            'precio': self.extract_precio(texto_completo),
            'moneda': self.extract_moneda(texto_completo),
            'superficie': self.extract_superficie(texto_completo),
            'habitaciones': self.extract_habitaciones(texto_completo),
            'banos': self.extract_banos(texto_completo),
            'zona': self.extract_zona(texto_completo),
            'amenities': self.extract_amenities(texto_completo),
            'referencias_ubicacion': self.extract_referencias(texto_completo)
        }
        
        # Contar cuántos campos fueron extraídos exitosamente
        campos_extraidos = sum(1 for v in resultado.values() if v)
        resultado['_regex_extraction_success'] = campos_extraidos
        
        return resultado
    
    def extract_precio(self, texto: str) -> Optional[float]:
        """Extrae el precio del texto."""
        for pattern in self.precio_patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                # Obtener el grupo capturado (puede estar en group(1) o group(2))
                precio_str = match.group(1) if match.group(1) else match.group(2) if len(match.groups()) > 1 else None
                if precio_str:
                    # Limpiar y convertir
                    precio_str = precio_str.replace(',', '').replace('.', '')
                    try:
                        return float(precio_str)
                    except ValueError:
                        continue
        return None
    
    def extract_moneda(self, texto: str) -> str:
        """Detecta la moneda usada."""
        if re.search(r'\$\s*us|\$us|usd|dólar|dolar', texto, re.IGNORECASE):
            return 'USD'
        elif re.search(r'bs\.?|boliviano', texto, re.IGNORECASE):
            return 'BOB'
        # Por defecto USD para precios en $
        elif '$' in texto:
            return 'USD'
        return 'USD'  # Default
    
    def extract_superficie(self, texto: str) -> Optional[float]:
        """Extrae la superficie en m²."""
        for pattern in self.superficie_patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    # Formato axb (calcular área)
                    try:
                        a = float(match.group(1).replace(',', '.'))
                        b = float(match.group(2).replace(',', '.'))
                        return round(a * b, 2)
                    except ValueError:
                        continue
                else:
                    # Formato directo
                    try:
                        sup_str = match.group(1).replace(',', '').replace('.', '')
                        return float(sup_str)
                    except ValueError:
                        continue
        return None
    
    def extract_habitaciones(self, texto: str) -> Optional[int]:
        """Extrae el número de habitaciones."""
        for pattern in self.habitaciones_patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match and match.group(1):
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return None
    
    def extract_banos(self, texto: str) -> Optional[int]:
        """Extrae el número de baños."""
        for pattern in self.banos_patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                if match.group(1):
                    try:
                        return int(match.group(1))
                    except ValueError:
                        continue
                else:
                    # Si solo dice "baño privado" sin número, asumir 1
                    return 1
        return None
    
    def extract_zona(self, texto: str) -> Optional[str]:
        """Extrae la zona/barrio de la descripción."""
        match = self.zona_pattern.search(texto)
        if match:
            return match.group(1).title()
        return None
    
    def extract_referencias(self, texto: str) -> Dict[str, List]:
        """Extrae referencias de ubicación (anillos y radiales)."""
        referencias = {
            'anillos': [],
            'radiales': []
        }
        
        # Buscar anillos
        for match in self.anillo_pattern.finditer(texto):
            num = int(match.group(1))
            if 1 <= num <= 12:  # Santa Cruz tiene hasta 12 anillos planificados
                referencias['anillos'].append(f"{num}° Anillo")
        
        # Buscar radiales
        for match in self.radial_pattern.finditer(texto):
            num = int(match.group(1))
            if 1 <= num <= 30:  # Radiales comunes en Santa Cruz
                referencias['radiales'].append(f"Radial {num}")
        
        return referencias if (referencias['anillos'] or referencias['radiales']) else {}
    
    def extract_amenities(self, texto: str) -> List[str]:
        """Extrae lista de amenities mencionados."""
        amenities_encontrados = []
        
        for amenity in self.amenities_keywords:
            if re.search(r'\b' + re.escape(amenity) + r'\b', texto, re.IGNORECASE):
                amenities_encontrados.append(amenity.title())
        
        return amenities_encontrados
    
    def get_extraction_summary(self, resultado: Dict[str, Any]) -> str:
        """Genera un resumen de qué se pudo extraer con regex."""
        campos = []
        if resultado.get('precio'):
            campos.append('precio')
        if resultado.get('superficie'):
            campos.append('superficie')
        if resultado.get('habitaciones'):
            campos.append('habitaciones')
        if resultado.get('banos'):
            campos.append('baños')
        if resultado.get('zona'):
            campos.append('zona')
        if resultado.get('amenities'):
            campos.append(f"{len(resultado['amenities'])} amenities")
        
        if not campos:
            return "No se extrajo nada con regex"
        
        return f"Regex extrajo: {', '.join(campos)}"
