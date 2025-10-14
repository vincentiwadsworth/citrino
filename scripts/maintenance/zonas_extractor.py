#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extractor de zonas geográficas de Santa Cruz de la Sierra desde texto.
"""

import re
from typing import List, Set, Optional, Tuple


class ZonasExtractor:
    """Extrae y valida zonas geográficas de Santa Cruz desde texto."""

    # Catálogo de zonas conocidas de Santa Cruz de la Sierra
    ZONAS_CONOCIDAS = {
        # Zonas premium
        'Equipetrol': ['equipetrol', 'equipe'],
        'Las Palmas': ['las palmas', 'palmas'],
        'Urubó': ['urubo', 'urubó'],
        
        # Zonas norte
        'Zona Norte': ['zona norte', 'norte'],
        'Las Brisas': ['las brisas', 'brisas'],
        'Sirari': ['sirari'],
        
        # Zonas centrales
        'Centro': ['centro', 'centro historico', 'centro histórico'],
        'La Recoleta': ['recoleta', 'la recoleta'],
        'La Salle': ['la salle', 'lasalle'],
        
        # Zonas residenciales
        'Santa Mónica': ['santa monica', 'santa mónica'],
        'Los Olivos': ['los olivos', 'olivos'],
        'Urbari': ['urbari'],
        'Palmar': ['palmar'],
        'Hamacas': ['hamacas'],
        
        # Zonas sur
        'Zona Sur': ['zona sur'],
        
        # Zonas comerciales/industriales
        'Parque Industrial': ['parque industrial'],
        'Km 7': ['km 7', 'kilometro 7'],
        
        # Referencias por plazuelas/lugares conocidos
        'Plazuela Blacutt': ['plazuela blacutt', 'blacutt'],
        'Cristo Redentor': ['cristo redentor'],
        
        # Barrios específicos
        'Barrio La Cuchilla': ['la cuchilla', 'cuchilla'],
        'Barrio Petrolero': ['barrio petrolero', 'petrolero'],
        'Barrio Lindo': ['barrio lindo'],
        'Barrio Plan Tres Mil': ['plan tres mil', 'plan 3000', 'plan 3 mil'],
        'Villa 1ro de Mayo': ['villa 1ro de mayo', 'villa primero de mayo']
    }

    # Patrones para extraer referencias de anillos y radiales
    PATRON_ANILLOS = re.compile(
        r'\b(\d+)(?:do|er|to|mo)?\.?\s*[aA]nillo\b',
        re.IGNORECASE
    )
    
    PATRON_RADIALES = re.compile(
        r'\b[rR]adial\s*(\d+)\b',
        re.IGNORECASE
    )
    
    PATRON_AVENIDAS = re.compile(
        r'\b[aA]v(?:enida)?\.?\s+([\w\s]+?)(?:\s+(?:y|entre|esq|esquina)|\s*$)',
        re.IGNORECASE
    )

    def __init__(self):
        """Inicializa el extractor."""
        # Crear índice invertido para búsqueda rápida
        self.zona_patterns = {}
        for zona_oficial, variantes in self.ZONAS_CONOCIDAS.items():
            for variante in variantes:
                self.zona_patterns[variante.lower()] = zona_oficial

    def extraer_zonas(self, texto: str) -> List[str]:
        """
        Extrae todas las zonas mencionadas en el texto.
        
        Args:
            texto: Texto donde buscar zonas (título, descripción, etc.)
            
        Returns:
            Lista de zonas encontradas (nombres oficiales)
        """
        if not texto:
            return []
        
        texto_lower = texto.lower()
        zonas_encontradas = set()
        
        # Buscar zonas conocidas
        for variante, zona_oficial in self.zona_patterns.items():
            if variante in texto_lower:
                zonas_encontradas.add(zona_oficial)
        
        return sorted(zonas_encontradas)

    def extraer_zona_principal(self, texto: str) -> Optional[str]:
        """
        Extrae la zona principal mencionada en el texto.
        
        Prioriza zonas específicas sobre genéricas y usa la primera mención.
        
        Args:
            texto: Texto donde buscar la zona principal
            
        Returns:
            Zona principal o None si no se encuentra
        """
        zonas = self.extraer_zonas(texto)
        
        if not zonas:
            return None
        
        # Priorizar zonas específicas (no "Zona Norte", "Zona Sur" genéricas)
        zonas_especificas = [z for z in zonas if not z.startswith('Zona ')]
        
        if zonas_especificas:
            return zonas_especificas[0]
        
        return zonas[0]

    def extraer_referencias_ubicacion(self, texto: str) -> dict:
        """
        Extrae todas las referencias de ubicación del texto.
        
        Returns:
            Dict con zonas, anillos, radiales y avenidas encontradas
        """
        if not texto:
            return {
                'zonas': [],
                'anillos': [],
                'radiales': [],
                'avenidas': []
            }
        
        # Extraer zonas
        zonas = self.extraer_zonas(texto)
        
        # Extraer anillos (ej: "3er anillo", "2do anillo")
        anillos = []
        for match in self.PATRON_ANILLOS.finditer(texto):
            numero = match.group(1)
            anillos.append(f"{numero}º Anillo")
        
        # Extraer radiales (ej: "Radial 10", "Radial 27")
        radiales = []
        for match in self.PATRON_RADIALES.finditer(texto):
            numero = match.group(1)
            radiales.append(f"Radial {numero}")
        
        # Extraer avenidas principales
        avenidas = []
        for match in self.PATRON_AVENIDAS.finditer(texto):
            nombre_av = match.group(1).strip()
            # Filtrar nombres muy cortos o genéricos
            if len(nombre_av) > 3 and nombre_av.lower() not in ['los', 'las', 'del', 'de']:
                avenidas.append(nombre_av[:50])  # Limitar longitud
        
        return {
            'zonas': zonas,
            'anillos': list(set(anillos)),
            'radiales': list(set(radiales)),
            'avenidas': avenidas[:3]  # Max 3 avenidas
        }

    def construir_ubicacion_completa(self, referencias: dict) -> str:
        """
        Construye una descripción de ubicación completa desde las referencias.
        
        Args:
            referencias: Dict retornado por extraer_referencias_ubicacion()
            
        Returns:
            String con ubicación completa, ej: "Equipetrol, 3er Anillo"
        """
        partes = []
        
        if referencias['zonas']:
            partes.append(referencias['zonas'][0])
        
        if referencias['anillos']:
            partes.append(referencias['anillos'][0])
        
        if referencias['radiales']:
            partes.append(referencias['radiales'][0])
        
        return ', '.join(partes) if partes else ''

    def validar_zona(self, zona: str) -> bool:
        """
        Valida si una zona está en el catálogo conocido.
        
        Args:
            zona: Nombre de zona a validar
            
        Returns:
            True si la zona es válida
        """
        return zona in self.ZONAS_CONOCIDAS

    def normalizar_zona(self, zona: str) -> Optional[str]:
        """
        Normaliza una zona a su nombre oficial.
        
        Args:
            zona: Zona en cualquier formato
            
        Returns:
            Nombre oficial o None si no se reconoce
        """
        zona_lower = zona.lower().strip()
        return self.zona_patterns.get(zona_lower)

    @classmethod
    def obtener_zonas_validas(cls) -> List[str]:
        """Retorna lista de todas las zonas válidas conocidas."""
        return sorted(cls.ZONAS_CONOCIDAS.keys())


def demo_extractor():
    """Demostración del extractor de zonas."""
    import sys
    import codecs
    
    # Configurar encoding para Windows
    if sys.platform == 'win32':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    
    extractor = ZonasExtractor()
    
    ejemplos = [
        "Casa en venta en Equipetrol cerca del 3er anillo",
        "Departamento Zona Norte, Av Banzer y 7mo anillo",
        "Terreno en Las Palmas con todos los servicios",
        "Oficina en Centro, Plazuela Blacutt",
        "Propiedad en Urubo, sector residencial"
    ]
    
    print("=== DEMO EXTRACTOR DE ZONAS ===\n")
    
    for texto in ejemplos:
        print(f"Texto: {texto}")
        zona_principal = extractor.extraer_zona_principal(texto)
        referencias = extractor.extraer_referencias_ubicacion(texto)
        ubicacion_completa = extractor.construir_ubicacion_completa(referencias)
        
        print(f"  -> Zona principal: {zona_principal}")
        print(f"  -> Referencias: {referencias}")
        print(f"  -> Ubicacion completa: {ubicacion_completa}")
        print()


if __name__ == "__main__":
    demo_extractor()
