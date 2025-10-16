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
        
        # Patrones de precio (mejorados para Proveedor 02)
        self.precio_patterns = [
            # $us 400.000.- o $us 400,000 (formato boliviano común)
            r'(?:precio[:\s]+)?\$\s*us\s*[\s]*([\d,.]+)',
            # $1,757,200 o $1.757.200 (formato estándar)
            r'(?:precio[:\s]+)?\$\s*([\d,.]+)',
            # Bs. 550.- o 660 Bs o Bs 700 (moneda boliviana)
            r'(?:precio[:\s]+)?(?:Bs\.?|bs\.?)\s*([\d,.]+)|(?:precio[:\s]+)?([\d,.]+)\s*(?:Bs\.?|bs\.?)',
            # us$ 450000 o us$ 450.000 (formato variante)
            r'(?:precio[:\s]+)?us\$\s*([\d,.]+)',
            # 450.000us o 450,000 us (sin espacio)
            r'([\d,.]+)\s*us',
            # 500000 bs o 500.000bs (formato compacto)
            r'([\d,.]+)\s*(?:bs|bolivianos?)',
            # venta en 350000 (implícito que es precio)
            r'(?:venta\s+en|precio[:\s]*|valor[:\s]*|costo[:\s]*)\s*([\d,.]+)',
        ]
        
        # Patrones de superficie (mejorados para Proveedor 02)
        self.superficie_patterns = [
            # Superficie: 2.500 m2 o Superficie construida: 12 m
            r'superficie(?:\s+construida)?[:\s]+([\d,.]+)\s*m',
            # 16 m2 o 16 m²
            r'(\d+(?:[,.]\d+)?)\s*m[²2]',
            # sup. 3.5x2.5 o sup.(6.50x3.25)
            r'sup\.?\s*[\(]?([\d,.]+)\s*x\s*([\d,.]+)[\)]?',
            # 250 mt2 o 250 m2 (formato compacto)
            r'(\d+(?:[,.]\d+)?)\s*(?:mt2|m2|m²)',
            # terreno de 200m2 o lote 300m2
            r'(?:terreno|lote)\s+(?:de\s+)?(\d+(?:[,.]\d+)?)\s*m[²2]?',
            # area construida 120m2
            r'(?:area|área)\s+(?:construida\s+)?(\d+(?:[,.]\d+)?)\s*m[²2]?',
        ]
        
        # Patrones de habitaciones (mejorados para Proveedor 02)
        self.habitaciones_patterns = [
            # 4 HABITACIONES EN ALQUILER
            r'(\d+)\s+habitacion(?:es)?',
            # 3 dormitorios
            r'(\d+)\s+dormitorio(?:s)?',
            # 2 hab o 3 dorm
            r'(\d+)\s+(?:hab|dorm)(?:s|\.)?',
            # con 3 habitaciones o cuenta con 2 dormitorios
            r'(?:con|cuenta\s+con)\s+(\d+)\s+(?:habitaciones?|dormitorios?)',
            # departamento de 2 ambientes (ambientes ≈ habitaciones)
            r'(\d+)\s+ambientes?',
            # 3 dorms o 4 habs (abreviaturas comunes)
            r'(\d+)\s+(?:dorms|habs)',
            # ideal para 1 persona (inferir 1 habitación)
            r'(?:ideal|perfecto)\s+para\s+(\d+)\s+persona',
        ]
        
        # Patrones de baños (mejorados para Proveedor 02)
        self.banos_patterns = [
            # 2 baños o 3 baño (con número)
            r'(\d+)\s+ba[ñn]o(?:s)?',
            # baño privado o con baño (sin número, asumir 1)
            r'(?:con\s+)?ba[ñn]o\s+(?:privado|social|completo)',
            # baño completo o baño social
            r'ba[ñn]o\s+(?:completo|social)',
            # 1 baño o 2.5 baños (medio baño)
            r'(\d+(?:\.5)?)\s*ba[ñn]o(?:s)?',
            # bño o bños (sin la ñ, común en descripciones)
            r'(\d*)\s*b[añn]o(?:s)?',
            # con baño y shower
            r'(?:con\s+)?ba[ñn]o\s+y\s+shower',
            # servicio sanitario
            r'(?:con\s+)?(?:servicio\s+)?sanitario',
        ]
        
        # Patrones de zonas conocidas de Santa Cruz (expandido para Proveedor 02)
        self.zonas_conocidas = [
            # Zonas principales y exclusivas
            'equipetrol', 'urubó', 'urubo', 'zona norte', 'zona sur', 'zona este', 'zona oeste',
            'santa mónica', 'santa monica', 'los olivos', 'urbari', 'pampa de la isla',
            'el valle', 'las brisas', 'el palmar', 'el mirador', 'santo domingo',
            'guapay', 'sarah', 'abapo', 'bienestar', 'los lotes', 'el pedregal',

            # Zonas tradicionales
            'villa 1ro de mayo', 'villa primero de mayo', 'plan 3000', 'plan tres mil',
            'el cristo', 'la recoleta', 'av. monseñor rivero', 'av. banzer', 'av. beni',
            'zona central', 'centro', 'casco viejo', 'la ramada', 'mutualista',
            'virgen de luján', 'virgen de lujan', 'el trompillo', 'paraguá',

            # Avenidas principales (como referencia de zona)
            'av. cristobal de mendoza', 'av. busch', 'av. alemana', 'av. roca y coronado',
            'av. paraguá', 'av. santiesteban', 'av. 6 de agosto', 'av. cañoto',

            # Anillos y radiales
            'radial 10', 'radial 13', 'radial 17', 'radial 19', 'radial 26', 'radial 27',
            '2do anillo', '3er anillo', '4to anillo', '5to anillo', '6to anillo',
            '7mo anillo', '8vo anillo', '9no anillo', 'segundo anillo', 'tercer anillo',
            'cuarto anillo', 'quinto anillo', 'sexto anillo', 'séptimo anillo',
            'octavo anillo', 'noveno anillo',

            # Barrios residenciales
            'las palmas', 'barrio equipetrol', 'barrio hamacas', 'santos dumont',
            'barrio 26 de septiembre', 'cambodromo', 'parque industrial',
            'cataluña', 'vida citadina', 'barrio los pinos', 'barrio jardín',
            'barrio sucre', 'barrio libertad', 'barrio san pedro',

            # Nuevos desarrollos
            'norte villa', 'norte villa country club', 'san marcos', 'country club',
            'club de golf', 'golf & country club', 'campestre', 'el toro'
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

        # Patrones de estado operativo (nuevos)
        self.estado_patterns = [
            # Patrones de venta
            r'en\s+venta',
            r'venta(?:\s+directa)?',
            r'se\s+vende',
            r'por\s+venta',
            r'oportunidad\s+de\s+venta',

            # Patrones de alquiler
            r'en\s+alquiler',
            r'en\s+arriendo',
            r'para\s+alquilar',
            r'para\s+arrendar',
            r'alquiler',
            r'arriendo',

            # Patrones de anticrético
            r'en\s+anticr[ée]tico',
            r'anticr[ée]tico',
            r'para\s+anticr[ée]tico',

            # Patrones de pre-venta
            r'pre[-\s]?venta',
            r'en\s+pre[-\s]?venta',
            r'preventa(?:\s+inmediata)?',
            r'proyecto\s+de\s+preventa',

            # Patrones generales
            r'operaci[óo]n\s+inmobiliaria',
            r'transferencia\s+inmobiliaria'
        ]

        # Patrones de agente inmobiliario (nuevos)
        self.agente_patterns = [
            # Patrones explícitos
            r'agente:\s*([^\n,]+)',
            r'asesor:\s*([^\n,]+)',
            r'contacto:\s*([^\n,]+)',
            r'vendedor:\s*([^\n,]+)',
            r'broker:\s*([^\n,]+)',
            r'inmobiliaria:\s*([^\n,]+)',

            # Patrones de teléfonos
            r'tel[ée]fono:\s*([^\n,]+)',
            r'tel\s*[:\-]?\s*([^\n,]+)',
            r'celular:\s*([^\n,]+)',
            r'whatsapp:\s*([^\n,]+)',
            r'wp\s*[:\-]?\s*([^\n,]+)',

            # Patrones de email
            r'email:\s*([^\n,]+)',
            r'e-mail:\s*([^\n,]+)',
            r'correo:\s*([^\n,]+)',

            # Patrones de nombres de inmobiliarias conocidas en Santa Cruz
            r'(citi\s*inmuebles|citinmuebles)',
            r'(urbana\s*propiedades|propiedades\s*urbanas)',
            r'(inmobiliaria\s+[^,\n]+)',
            r'(grupo\s+[^,\n]+\s*inmobiliario)',

            # Patrones de contacto genérico
            r'contactar\s+a\s+([^\n,]+)',
            r'comunicarse\s+con\s+([^\n,]+)',
            r'informes\s+con\s+([^\n,]+)'
        ]

        # Patrones de garajes/estacionamiento (mejorados)
        self.garaje_patterns = [
            # Patrones con número
            r'(\d+)\s+garages?',
            r'(\d+)\s+estacionamientos?',
            r'(\d+)\s+plazas?\s+de\s+estacionamiento',
            r'(\d+)\s+parqueos?',
            r'(\d+)\s+places?\s+de\s+parking',

            # Patrones sin número (asumir 1)
            r'con\s+garage',
            r'con\s+garaje',
            r'con\s+estacionamiento',
            r'con\s+parqueo',
            r'cuenta\s+con\s+garage',
            r'posee\s+estacionamiento',

            # Patrones de cubiertos/descubiertos
            r'(\d+)\s+garages?\s+cubiertos?',
            r'(\d+)\s+estacionamientos?\s+cubiertos?',
            r'(\d+)\s+parqueos?\s+cubiertos?'
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
            'garajes': self.extract_garajes(texto_completo),
            'zona': self.extract_zona(texto_completo),
            'amenities': self.extract_amenities(texto_completo),
            'referencias_ubicacion': self.extract_referencias(texto_completo),
            'estado_operativo': self.extract_estado_operativo(texto_completo),
            'agente': self.extract_agente(texto_completo),
            'contacto_agente': self.extract_contacto_agente(texto_completo)
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
                # Obtener el grupo capturado (manejar diferentes números de grupos)
                groups = match.groups()
                if groups:
                    # Buscar el primer grupo no nulo
                    precio_str = None
                    for group in groups:
                        if group is not None:
                            precio_str = group
                            break

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
                groups = match.groups()
                if len(groups) == 2 and groups[0] is not None and groups[1] is not None:
                    # Formato axb (calcular área)
                    try:
                        a = float(groups[0].replace(',', '.'))
                        b = float(groups[1].replace(',', '.'))
                        return round(a * b, 2)
                    except (ValueError, AttributeError):
                        continue
                elif groups and groups[0] is not None:
                    # Formato directo
                    try:
                        sup_str = groups[0].replace(',', '').replace('.', '')
                        return float(sup_str)
                    except (ValueError, AttributeError):
                        continue
        return None
    
    def extract_habitaciones(self, texto: str) -> Optional[int]:
        """Extrae el número de habitaciones."""
        for pattern in self.habitaciones_patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                groups = match.groups()
                if groups and groups[0] is not None:
                    try:
                        return int(groups[0])
                    except (ValueError, AttributeError):
                        continue
        return None

    def extract_banos(self, texto: str) -> Optional[float]:
        """Extrae el número de baños (permite medio baño: 1.5)."""
        for pattern in self.banos_patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                groups = match.groups()
                if groups and groups[0] is not None:
                    try:
                        # Permite valores como 1.5 (medio baño)
                        return float(groups[0])
                    except (ValueError, AttributeError):
                        continue
                else:
                    # Si solo dice "baño privado" sin número, asumir 1
                    return 1.0
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

    def extract_garajes(self, texto: str) -> Optional[int]:
        """Extrae el número de garajes/estacionamientos."""
        for pattern in self.garaje_patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                groups = match.groups()
                if groups and groups[0] is not None:
                    try:
                        return int(groups[0])
                    except (ValueError, AttributeError):
                        continue
                else:
                    # Si solo dice "con garage" sin número, asumir 1
                    return 1
        return None

    def extract_estado_operativo(self, texto: str) -> Optional[str]:
        """Extrae el estado operativo (venta, alquiler, etc.)."""
        texto_original = texto  # Mantener original para retornar el valor encontrado

        # Prioridad: pre-venta > venta > alquiler > anticrético
        if re.search(r'pre[-\s]?venta|en\s+pre[-\s]?venta', texto, re.IGNORECASE):
            return "pre-venta"
        elif re.search(r'en\s+venta|venta|se\s+vende|por\s+venta', texto, re.IGNORECASE):
            return "venta"
        elif re.search(r'en\s+alquiler|alquiler|arriendo|para\s+alquilar', texto, re.IGNORECASE):
            return "alquiler"
        elif re.search(r'en\s+anticr[ée]tico|anticr[ée]tico', texto, re.IGNORECASE):
            return "anticrético"

        return None

    def extract_agente(self, texto: str) -> Optional[str]:
        """Extrae el nombre del agente o inmobiliaria."""
        for pattern in self.agente_patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                groups = match.groups()
                if groups and groups[0] is not None:
                    agente = groups[0].strip()
                    # Limpiar y capitalizar
                    if len(agente) > 2:  # Evitar resultados muy cortos
                        return agente.title()
        return None

    def extract_contacto_agente(self, texto: str) -> Optional[str]:
        """Extrae información de contacto (teléfono, email)."""
        # Patrones de teléfono (formatos bolivianos)
        telefono_patterns = [
            r'\b(\d{4}\s*[-\s]\s*\d{4})\b',  # 7777-7777
            r'\b(\d{3}\s*[-\s]\s*\d{7})\b',  # 777-7777777
            r'\b(\d{8})\b',                   # 77777777
            r'\b(\d{7})\b',                   # 7777777
            r'\b(\+\s*591\s*\d{8})\b',        # +591 77777777
            r'\b(591\s*\d{8})\b',             # 591 77777777
        ]

        # Extraer teléfono
        for pattern in telefono_patterns:
            match = re.search(pattern, texto)
            if match:
                telefono = match.group(1).strip()
                return telefono

        # Patrones de email
        email_patterns = [
            r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
        ]

        for pattern in email_patterns:
            match = re.search(pattern, texto)
            if match:
                email = match.group(0).strip().lower()
                return email

        # Patrones de WhatsApp
        whatsapp_patterns = [
            r'whatsapp[:\s]*([^\n,]+)',
            r'wp[:\s]*([^\n,]+)',
        ]

        for pattern in whatsapp_patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                whatsapp = match.group(1).strip()
                return f"WhatsApp: {whatsapp}"

        return None
    
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
