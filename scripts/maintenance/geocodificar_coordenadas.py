#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Geocodificación inversa para extraer zonas desde coordenadas.
Usa API de OpenStreetMap Nominatim (gratuita, rate-limited).
"""

import json
import time
import sys
import codecs
from pathlib import Path
from typing import Optional, Dict
import urllib.request
import urllib.parse

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# Importar extractor de zonas
import sys
sys.path.append(str(Path(__file__).parent))
from zonas_extractor import ZonasExtractor


class GeocodificadorInverso:
    """Geocodificación inversa usando OpenStreetMap Nominatim."""
    
    def __init__(self, rate_limit_seconds: float = 1.0):
        """
        Args:
            rate_limit_seconds: Segundos entre requests (Nominatim requiere >= 1 segundo)
        """
        self.rate_limit = rate_limit_seconds
        self.last_request_time = 0
        self.cache = {}
        self.extractor_zonas = ZonasExtractor()
        
        # Headers requeridos por Nominatim
        self.headers = {
            'User-Agent': 'Citrino/1.0 (Real Estate Investment Platform; Bolivia)'
        }
    
    def _respetar_rate_limit(self):
        """Espera el tiempo necesario para respetar rate limit."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()
    
    def geocodificar_inverso(self, latitud: float, longitud: float) -> Optional[Dict]:
        """
        Obtiene información de ubicación desde coordenadas.
        
        Returns:
            Dict con información de ubicación o None si falla
        """
        # Revisar cache
        cache_key = f"{round(latitud, 6)}_{round(longitud, 6)}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Respetar rate limit
        self._respetar_rate_limit()
        
        # Construir URL
        base_url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            'format': 'json',
            'lat': str(latitud),
            'lon': str(longitud),
            'zoom': 16,  # Nivel de detalle de barrio
            'addressdetails': 1
        }
        
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        
        try:
            request = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                # Guardar en cache
                self.cache[cache_key] = data
                return data
                
        except Exception as e:
            print(f"  ⚠ Error geocodificando ({latitud}, {longitud}): {str(e)[:100]}")
            return None
    
    def extraer_zona_de_respuesta(self, geo_data: Dict) -> Optional[str]:
        """
        Extrae la zona desde la respuesta de geocodificación.
        
        Prioriza:
        1. neighbourhood (barrio)
        2. suburb (zona suburbana)
        3. quarter (distrito)
        4. display_name completo
        """
        if not geo_data:
            return None
        
        address = geo_data.get('address', {})
        
        # Intentar diferentes niveles de ubicación
        candidatos = [
            address.get('neighbourhood'),
            address.get('suburb'),
            address.get('quarter'),
            address.get('residential'),
            geo_data.get('display_name')
        ]
        
        for candidato in candidatos:
            if candidato:
                # Usar el extractor de zonas para normalizar
                zonas = self.extractor_zonas.extraer_zonas(candidato)
                if zonas:
                    # Tomar la primera zona encontrada
                    return zonas[0]
        
        return None
    
    def procesar_propiedades(self, propiedades: list) -> Dict:
        """
        Procesa todas las propiedades sin zona pero con coordenadas.
        
        Returns:
            Estadísticas del procesamiento
        """
        print("\n" + "="*80)
        print("  GEOCODIFICACIÓN INVERSA - EXTRACCIÓN DE ZONAS")
        print("="*80)
        
        sin_zona = [p for p in propiedades if not p.get('zona') and p.get('latitud') and p.get('longitud')]
        
        print(f"\nPropiedades sin zona: {len(sin_zona)}")
        print(f"Propiedades a procesar: {len(sin_zona)}")
        print(f"\nRate limit: {self.rate_limit}s entre requests")
        print(f"Tiempo estimado: {len(sin_zona) * self.rate_limit / 60:.1f} minutos")
        
        stats = {
            'procesadas': 0,
            'zonas_encontradas': 0,
            'zonas_fallidas': 0,
            'errores_api': 0
        }
        
        print("\nProcesando...")
        
        for i, prop in enumerate(sin_zona, 1):
            lat = prop['latitud']
            lon = prop['longitud']
            
            if i % 50 == 0 or i == len(sin_zona):
                print(f"  Progreso: {i}/{len(sin_zona)} ({i/len(sin_zona)*100:.1f}%) - Zonas: {stats['zonas_encontradas']}")
            
            # Geocodificar
            geo_data = self.geocodificar_inverso(lat, lon)
            stats['procesadas'] += 1
            
            if not geo_data:
                stats['errores_api'] += 1
                continue
            
            # Extraer zona
            zona = self.extraer_zona_de_respuesta(geo_data)
            
            if zona:
                prop['zona'] = zona
                prop['zona_metodo'] = 'geocodificacion_inversa'
                prop['zona_confianza'] = 'media'
                stats['zonas_encontradas'] += 1
            else:
                stats['zonas_fallidas'] += 1
        
        # Reporte final
        print(f"\n{'='*80}")
        print("  RESULTADOS")
        print("="*80)
        print(f"Propiedades procesadas:     {stats['procesadas']}")
        print(f"Zonas encontradas:          {stats['zonas_encontradas']} ({stats['zonas_encontradas']/stats['procesadas']*100:.1f}%)")
        print(f"Zonas fallidas:             {stats['zonas_fallidas']} ({stats['zonas_fallidas']/stats['procesadas']*100:.1f}%)")
        print(f"Errores API:                {stats['errores_api']}")
        
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
    
    print(f"\nPropiedades cargadas: {len(propiedades)}")
    
    # Contar situación actual
    sin_zona = sum(1 for p in propiedades if not p.get('zona'))
    con_coords = sum(1 for p in propiedades if p.get('latitud') and p.get('longitud'))
    sin_zona_con_coords = sum(1 for p in propiedades if not p.get('zona') and p.get('latitud') and p.get('longitud'))
    
    print(f"Sin zona: {sin_zona} ({sin_zona/len(propiedades)*100:.1f}%)")
    print(f"Con coordenadas: {con_coords} ({con_coords/len(propiedades)*100:.1f}%)")
    print(f"Sin zona pero con coords: {sin_zona_con_coords} ({sin_zona_con_coords/len(propiedades)*100:.1f}%)")
    
    # Procesar
    geocodificador = GeocodificadorInverso(rate_limit_seconds=1.0)
    stats = geocodificador.procesar_propiedades(propiedades)
    
    # Guardar resultados
    backup_file = Path("data/base_datos_relevamiento_backup.json")
    if not backup_file.exists():
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\nBackup guardado: {backup_file}")
    
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\nDatos actualizados guardados: {data_file}")
    
    # Estadísticas finales
    sin_zona_final = sum(1 for p in propiedades if not p.get('zona'))
    print(f"\nSin zona ANTES: {sin_zona} ({sin_zona/len(propiedades)*100:.1f}%)")
    print(f"Sin zona DESPUÉS: {sin_zona_final} ({sin_zona_final/len(propiedades)*100:.1f}%)")
    print(f"Mejora: {sin_zona - sin_zona_final} propiedades ({(sin_zona - sin_zona_final)/len(propiedades)*100:.1f}%)")


if __name__ == "__main__":
    main()
