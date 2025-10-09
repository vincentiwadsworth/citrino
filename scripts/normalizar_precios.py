#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Normalizador de precios para extraer y convertir precios faltantes o mal formateados.
"""

import json
import re
import sys
import codecs
from pathlib import Path
from typing import Dict, Optional, Tuple

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')


class NormalizadorPrecios:
    """Normaliza y extrae precios desde diferentes fuentes."""
    
    def __init__(self):
        # Tasas de cambio aproximadas (deberían actualizarse)
        self.tasas_cambio = {
            'usd': 1.0,      # Base
            'bs': 0.145,     # ~6.9 Bs por USD
            'bob': 0.145,    # Boliviano
            '$us': 1.0,
        }
        
        # Patrones para extraer precios
        self.patrones_precio = [
            # $123,456 o $123456 o USD 123456
            r'(?:usd?|us\$|\$)\s*(\d{1,3}(?:[,\.]\d{3})*(?:[,\.]\d{2})?)',
            # Bs 123,456
            r'bs\.?\s*(\d{1,3}(?:[,\.]\d{3})*(?:[,\.]\d{2})?)',
            # 123,456 USD
            r'(\d{1,3}(?:[,\.]\d{3})*(?:[,\.]\d{2})?)\s*(?:usd?|us\$)',
            # Solo números grandes (>= 1000)
            r'\b(\d{1,3}(?:[,\.]\d{3}){1,})\b',
        ]
        
        # Patrones para detectar moneda
        self.patrones_moneda = [
            (r'(?:usd?|us\$|\$)', 'usd'),
            (r'bs\.?|bolivianos?|bob', 'bs'),
        ]
    
    def limpiar_numero(self, texto: str) -> Optional[float]:
        """Convierte texto a número flotante."""
        try:
            # Remover espacios y caracteres no numéricos excepto , y .
            texto = re.sub(r'[^\d,\.]', '', texto)
            
            # Detectar si usa coma como decimal (europeo) o punto (americano)
            if ',' in texto and '.' in texto:
                # Si hay ambos, asumir formato americano: 1,234.56
                texto = texto.replace(',', '')
            elif ',' in texto:
                # Solo comas - puede ser separador de miles o decimal
                partes = texto.split(',')
                if len(partes[-1]) <= 2:  # Última parte corta = decimal
                    texto = texto.replace(',', '.')
                else:  # Separador de miles
                    texto = texto.replace(',', '')
            
            return float(texto)
        except (ValueError, AttributeError):
            return None
    
    def detectar_moneda(self, texto: str) -> str:
        """Detecta la moneda en el texto."""
        if not texto:
            return 'usd'  # Asumir USD por defecto
        
        texto_lower = texto.lower()
        
        for patron, moneda in self.patrones_moneda:
            if re.search(patron, texto_lower):
                return moneda
        
        return 'usd'  # Default
    
    def extraer_precio(self, texto: str) -> Optional[Tuple[float, str]]:
        """
        Extrae precio y moneda desde texto.
        
        Returns:
            (precio, moneda) o None
        """
        if not texto:
            return None
        
        texto_str = str(texto)
        
        # Detectar moneda
        moneda = self.detectar_moneda(texto_str)
        
        # Intentar extraer precio con patrones
        for patron in self.patrones_precio:
            match = re.search(patron, texto_str, re.IGNORECASE)
            if match:
                precio_str = match.group(1)
                precio = self.limpiar_numero(precio_str)
                
                # Validar rango razonable para propiedades
                if precio and 1000 <= precio <= 100000000:
                    return (precio, moneda)
        
        return None
    
    def convertir_a_usd(self, precio: float, moneda: str) -> float:
        """Convierte precio a USD."""
        moneda_lower = moneda.lower()
        tasa = self.tasas_cambio.get(moneda_lower, 1.0)
        return round(precio * tasa, 2)
    
    def normalizar_precio_propiedad(self, propiedad: Dict) -> Optional[Dict]:
        """
        Normaliza el precio de una propiedad.
        
        Returns:
            Dict con precio_usd, precio_original, moneda_original, metodo
        """
        # 1. Revisar si ya tiene precio válido
        precio_actual = propiedad.get('precio')
        moneda_actual = propiedad.get('moneda', 'usd')
        
        if precio_actual and precio_actual > 0:
            precio_usd = self.convertir_a_usd(precio_actual, moneda_actual)
            return {
                'precio_usd': precio_usd,
                'precio_original': precio_actual,
                'moneda_original': moneda_actual,
                'metodo': 'campo_directo'
            }
        
        # 2. Intentar extraer desde título
        titulo = propiedad.get('titulo', '')
        resultado = self.extraer_precio(titulo)
        if resultado:
            precio, moneda = resultado
            precio_usd = self.convertir_a_usd(precio, moneda)
            return {
                'precio_usd': precio_usd,
                'precio_original': precio,
                'moneda_original': moneda,
                'metodo': 'extraido_titulo'
            }
        
        # 3. Intentar extraer desde descripción
        descripcion = propiedad.get('descripcion', '')
        resultado = self.extraer_precio(descripcion)
        if resultado:
            precio, moneda = resultado
            precio_usd = self.convertir_a_usd(precio, moneda)
            return {
                'precio_usd': precio_usd,
                'precio_original': precio,
                'moneda_original': moneda,
                'metodo': 'extraido_descripcion'
            }
        
        # 4. Intentar desde campo "credito" o "crédito $us./mes"
        credito = propiedad.get('credito_mes')
        if credito and credito > 0:
            # Estimar precio total desde cuota mensual (30 años, ~6% interés)
            # Fórmula aproximada: precio ≈ cuota * 166.79
            precio_estimado = credito * 166.79
            return {
                'precio_usd': round(precio_estimado, 2),
                'precio_original': credito,
                'moneda_original': 'usd',
                'metodo': 'estimado_credito_mensual',
                'estimado': True
            }
        
        return None
    
    def procesar_propiedades(self, propiedades: list) -> Dict:
        """Procesa todas las propiedades."""
        print("\n" + "="*80)
        print("  NORMALIZACIÓN DE PRECIOS")
        print("="*80)
        
        stats = {
            'procesadas': 0,
            'con_precio_valido': 0,
            'precios_normalizados': 0,
            'precios_extraidos_titulo': 0,
            'precios_extraidos_descripcion': 0,
            'precios_estimados_credito': 0,
            'sin_precio': 0,
        }
        
        for prop in propiedades:
            stats['procesadas'] += 1
            
            resultado = self.normalizar_precio_propiedad(prop)
            
            if resultado:
                # Actualizar propiedad
                prop['precio_usd'] = resultado['precio_usd']
                prop['precio_original'] = resultado['precio_original']
                prop['moneda_original'] = resultado['moneda_original']
                prop['precio_metodo'] = resultado['metodo']
                
                if resultado.get('estimado'):
                    prop['precio_estimado'] = True
                
                stats['precios_normalizados'] += 1
                
                if resultado['metodo'] == 'campo_directo':
                    stats['con_precio_valido'] += 1
                elif resultado['metodo'] == 'extraido_titulo':
                    stats['precios_extraidos_titulo'] += 1
                elif resultado['metodo'] == 'extraido_descripcion':
                    stats['precios_extraidos_descripcion'] += 1
                elif resultado['metodo'] == 'estimado_credito_mensual':
                    stats['precios_estimados_credito'] += 1
            else:
                stats['sin_precio'] += 1
        
        # Reporte
        print(f"\nPropiedades procesadas: {stats['procesadas']}")
        print(f"\nResultados:")
        print(f"  Con precio válido:          {stats['con_precio_valido']:5d} ({stats['con_precio_valido']/stats['procesadas']*100:5.1f}%)")
        print(f"  Extraídos desde título:     {stats['precios_extraidos_titulo']:5d} ({stats['precios_extraidos_titulo']/stats['procesadas']*100:5.1f}%)")
        print(f"  Extraídos desde descr:      {stats['precios_extraidos_descripcion']:5d} ({stats['precios_extraidos_descripcion']/stats['procesadas']*100:5.1f}%)")
        print(f"  Estimados desde crédito:    {stats['precios_estimados_credito']:5d} ({stats['precios_estimados_credito']/stats['procesadas']*100:5.1f}%)")
        print(f"  Total con precio:           {stats['precios_normalizados']:5d} ({stats['precios_normalizados']/stats['procesadas']*100:5.1f}%)")
        print(f"  Sin precio:                 {stats['sin_precio']:5d} ({stats['sin_precio']/stats['procesadas']*100:5.1f}%)")
        
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
    
    # Estadísticas antes
    sin_precio_antes = sum(1 for p in propiedades if not p.get('precio') or p.get('precio') == 0)
    print(f"Sin precio ANTES: {sin_precio_antes} ({sin_precio_antes/len(propiedades)*100:.1f}%)")
    
    # Procesar
    normalizador = NormalizadorPrecios()
    stats = normalizador.procesar_propiedades(propiedades)
    
    # Guardar resultados
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*80}")
    print(f"Datos actualizados guardados: {data_file}")
    print("="*80)


if __name__ == "__main__":
    main()
