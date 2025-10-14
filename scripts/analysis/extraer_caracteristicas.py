#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extractor de características (habitaciones, baños, superficie, garajes)
desde descripciones y campos de texto.
"""

import json
import re
import sys
import codecs
from pathlib import Path
from typing import Dict, Optional, List

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')


class ExtractorCaracteristicas:
    """Extrae características estructuradas desde texto libre."""
    
    def __init__(self):
        # Patrones regex para diferentes formatos
        self.patrones = {
            'habitaciones': [
                r'(\d+)\s*(?:dormitorios?|habitaciones?|dorms?|habs?|recámaras?)',
                r'(?:dormitorios?|habitaciones?|dorms?|habs?)[:.\s]*(\d+)',
                r'(\d+)\s*(?:bed|bedroom|br)',
            ],
            'banos': [
                r'(\d+(?:\.\d+)?)\s*(?:baños?|baths?)',
                r'(?:baños?|baths?)[:.\s]*(\d+(?:\.\d+)?)',
            ],
            'garajes': [
                r'(\d+)\s*(?:garajes?|estacionamientos?|parkings?|cocheras?)',
                r'(?:garajes?|estacionamientos?|parkings?)[:.\s]*(\d+)',
            ],
            'superficie_terreno': [
                r'(\d+(?:[,\.]\d+)?)\s*(?:m2|m²|mts2|metros?\s*cuadrados?)\s*(?:de\s*)?(?:terreno|lote)',
                r'(?:terreno|lote)[:.\s]*(\d+(?:[,\.]\d+)?)\s*(?:m2|m²|mts2)',
                r'm²\s*terreno[:.\s]*(\d+(?:[,\.]\d+)?)',
            ],
            'superficie_construida': [
                r'(\d+(?:[,\.]\d+)?)\s*(?:m2|m²|mts2|metros?\s*cuadrados?)\s*(?:de\s*)?(?:construcción|construida|const)',
                r'(?:construcción|construida|const)[:.\s]*(\d+(?:[,\.]\d+)?)\s*(?:m2|m²|mts2)',
                r'm²\s*construcción[:.\s]*(\d+(?:[,\.]\d+)?)',
            ],
            'superficie_general': [
                r'(\d+(?:[,\.]\d+)?)\s*(?:m2|m²|mts2|metros?\s*cuadrados?)',
            ]
        }
    
    def limpiar_numero(self, texto: str) -> Optional[float]:
        """Convierte texto a número."""
        try:
            # Remover separadores de miles y convertir coma decimal a punto
            texto = texto.replace(',', '.')
            # Si hay múltiples puntos, asumir que el último es decimal
            if texto.count('.') > 1:
                partes = texto.split('.')
                texto = ''.join(partes[:-1]) + '.' + partes[-1]
            return float(texto)
        except (ValueError, AttributeError):
            return None
    
    def extraer_con_patrones(self, texto: str, patrones: List[str]) -> Optional[float]:
        """Intenta extraer un número usando una lista de patrones."""
        if not texto:
            return None
        
        texto_lower = texto.lower()
        
        for patron in patrones:
            match = re.search(patron, texto_lower, re.IGNORECASE)
            if match:
                numero_str = match.group(1)
                numero = self.limpiar_numero(numero_str)
                if numero and numero > 0:
                    return numero
        
        return None
    
    def extraer_caracteristicas(self, propiedad: Dict) -> Dict:
        """
        Extrae características de una propiedad.
        
        Campos fuente (prioridad):
        1. Campos estructurados (Habitaciones, Baños, etc.)
        2. Detalles / Características
        3. Descripción
        4. Título
        """
        resultados = {}
        
        # Construir texto combinado para búsqueda
        textos_busqueda = []
        
        # Campos directos (máxima prioridad)
        if propiedad.get('habitaciones'):
            try:
                resultados['habitaciones'] = int(float(propiedad['habitaciones']))
            except (ValueError, TypeError):
                pass
        
        if propiedad.get('banos'):
            try:
                resultados['banos'] = float(propiedad['banos'])
            except (ValueError, TypeError):
                pass
        
        if propiedad.get('garajes'):
            try:
                resultados['garajes'] = int(float(propiedad['garajes']))
            except (ValueError, TypeError):
                pass
        
        # Superficie terreno
        for campo in ['superficie_terreno', 'sup_terreno']:
            if propiedad.get(campo):
                try:
                    resultados['superficie_terreno'] = float(str(propiedad[campo]).replace(',', ''))
                    break
                except (ValueError, TypeError):
                    pass
        
        # Superficie construida
        for campo in ['superficie_construida', 'sup_construida']:
            if propiedad.get(campo):
                try:
                    resultados['superficie_construida'] = float(str(propiedad[campo]).replace(',', ''))
                    break
                except (ValueError, TypeError):
                    pass
        
        # Construir texto de búsqueda para campos faltantes
        for campo in ['detalles', 'caracteristicas', 'descripcion', 'titulo']:
            valor = propiedad.get(campo)
            if valor:
                textos_busqueda.append(str(valor))
        
        texto_completo = ' '.join(textos_busqueda)
        
        # Extraer campos faltantes
        if 'habitaciones' not in resultados:
            hab = self.extraer_con_patrones(texto_completo, self.patrones['habitaciones'])
            if hab:
                resultados['habitaciones'] = int(hab)
        
        if 'banos' not in resultados:
            banos = self.extraer_con_patrones(texto_completo, self.patrones['banos'])
            if banos:
                resultados['banos'] = banos
        
        if 'garajes' not in resultados:
            garajes = self.extraer_con_patrones(texto_completo, self.patrones['garajes'])
            if garajes:
                resultados['garajes'] = int(garajes)
        
        if 'superficie_terreno' not in resultados:
            sup_t = self.extraer_con_patrones(texto_completo, self.patrones['superficie_terreno'])
            if sup_t:
                resultados['superficie_terreno'] = sup_t
        
        if 'superficie_construida' not in resultados:
            sup_c = self.extraer_con_patrones(texto_completo, self.patrones['superficie_construida'])
            if sup_c:
                resultados['superficie_construida'] = sup_c
        
        # Si no hay terreno ni construida, buscar superficie general
        if 'superficie_terreno' not in resultados and 'superficie_construida' not in resultados:
            sup_gen = self.extraer_con_patrones(texto_completo, self.patrones['superficie_general'])
            if sup_gen:
                # Asumir que es superficie total (puede ser terreno o construida)
                resultados['superficie_total'] = sup_gen
        
        return resultados
    
    def procesar_propiedades(self, propiedades: List[Dict]) -> Dict:
        """Procesa todas las propiedades."""
        print("\n" + "="*80)
        print("  EXTRACCIÓN DE CARACTERÍSTICAS")
        print("="*80)
        
        stats = {
            'procesadas': 0,
            'habitaciones_extraidas': 0,
            'banos_extraidos': 0,
            'garajes_extraidos': 0,
            'superficie_terreno_extraida': 0,
            'superficie_construida_extraida': 0,
            'superficie_total_extraida': 0,
        }
        
        # Mapeo de campos a stats
        campo_to_stat = {
            'habitaciones': 'habitaciones_extraidas',
            'banos': 'banos_extraidos',
            'garajes': 'garajes_extraidos',
            'superficie_terreno': 'superficie_terreno_extraida',
            'superficie_construida': 'superficie_construida_extraida',
            'superficie_total': 'superficie_total_extraida',
        }
        
        for prop in propiedades:
            caracteristicas = self.extraer_caracteristicas(prop)
            stats['procesadas'] += 1
            
            # Actualizar propiedad
            for campo, valor in caracteristicas.items():
                if not prop.get(campo):  # Solo actualizar si no existe
                    prop[campo] = valor
                    prop[f'{campo}_extraido'] = True
                    stat_key = campo_to_stat.get(campo)
                    if stat_key:
                        stats[stat_key] += 1
        
        # Reporte
        print(f"\nPropiedades procesadas: {stats['procesadas']}")
        print(f"\nCaracterísticas extraídas:")
        print(f"  Habitaciones:           {stats['habitaciones_extraidas']:5d} ({stats['habitaciones_extraidas']/stats['procesadas']*100:5.1f}%)")
        print(f"  Baños:                  {stats['banos_extraidos']:5d} ({stats['banos_extraidos']/stats['procesadas']*100:5.1f}%)")
        print(f"  Garajes:                {stats['garajes_extraidos']:5d} ({stats['garajes_extraidos']/stats['procesadas']*100:5.1f}%)")
        print(f"  Superficie terreno:     {stats['superficie_terreno_extraida']:5d} ({stats['superficie_terreno_extraida']/stats['procesadas']*100:5.1f}%)")
        print(f"  Superficie construida:  {stats['superficie_construida_extraida']:5d} ({stats['superficie_construida_extraida']/stats['procesadas']*100:5.1f}%)")
        print(f"  Superficie total:       {stats['superficie_total_extraida']:5d} ({stats['superficie_total_extraida']/stats['procesadas']*100:5.1f}%)")
        
        return stats


def main():
    # Cargar datos
    data_file = Path("data/base_datos_relevamiento.json")
    
    if not data_file.exists():
        print(f"Error: No se encontró {data_file}")
        return
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    propiedades = data.get('propiedades', [])
    print(f"Propiedades cargadas: {len(propiedades)}")
    
    # Procesar
    extractor = ExtractorCaracteristicas()
    stats = extractor.procesar_propiedades(propiedades)
    
    # Guardar resultados
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*80}")
    print(f"Datos actualizados guardados: {data_file}")
    print("="*80)


if __name__ == "__main__":
    main()
