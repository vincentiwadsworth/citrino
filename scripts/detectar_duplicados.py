#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detector avanzado de duplicados con múltiples criterios y estadísticas.
"""

import json
import sys
import codecs
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple, Set

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')


class DetectorDuplicados:
    """Detecta duplicados usando múltiples criterios."""
    
    def __init__(self):
        self.duplicados_por_criterio = defaultdict(list)
        self.propiedades_unicas = []
        self.estadisticas = defaultdict(int)
        
    def normalizar_url(self, url: str) -> str:
        """Normaliza una URL para comparación."""
        if not url:
            return ""
        url = url.lower().strip()
        # Remover http/https y trailing slashes
        url = url.replace('https://', '').replace('http://', '')
        url = url.rstrip('/')
        return url
    
    def normalizar_titulo(self, titulo: str) -> str:
        """Normaliza un título para comparación."""
        if not titulo:
            return ""
        # Minúsculas, sin espacios múltiples
        titulo = titulo.lower().strip()
        titulo = ' '.join(titulo.split())
        # Remover caracteres especiales comunes
        for char in ['$', ',', '.', '!', '?', ':']:
            titulo = titulo.replace(char, '')
        return titulo
    
    def generar_clave_coords(self, lat, lon, precision=5) -> str:
        """Genera clave de coordenadas con precisión ajustable."""
        if not lat or not lon:
            return ""
        try:
            # Redondear a N decimales (5 = ~1.1m precisión)
            lat_round = round(float(lat), precision)
            lon_round = round(float(lon), precision)
            return f"{lat_round}_{lon_round}"
        except (ValueError, TypeError):
            return ""
    
    def identificar_criterio_identificacion(self, prop: dict) -> Tuple[str, str]:
        """
        Identifica el mejor criterio para identificar esta propiedad.
        
        Returns:
            (criterio, valor_clave) donde criterio es 'url', 'coords', 'titulo_zona', etc.
        """
        proveedor = prop.get('codigo_proveedor', 'unknown')
        
        # Prioridad 1: URL (más confiable)
        url = self.normalizar_url(prop.get('url', ''))
        if url:
            return 'url', f"{proveedor}_{url}"
        
        # Prioridad 2: Coordenadas (muy confiable para ubicación exacta)
        clave_coords = self.generar_clave_coords(
            prop.get('latitud'),
            prop.get('longitud')
        )
        if clave_coords:
            # Incluir proveedor para evitar que diferentes fuentes de la misma ubicación se consideren duplicadas
            return 'coords', f"{proveedor}_{clave_coords}"
        
        # Prioridad 3: Título normalizado + zona (menos confiable)
        titulo = self.normalizar_titulo(prop.get('titulo', ''))
        zona = prop.get('zona', '').strip().lower()
        if titulo:
            clave = f"{proveedor}_{titulo}"
            if zona:
                clave += f"_{zona}"
            return 'titulo_zona', clave
        
        # Sin criterio confiable - usar ID único
        return 'id', prop.get('id', 'unknown')
    
    def analizar_duplicados(self, propiedades: List[dict]) -> Dict:
        """
        Analiza duplicados en el conjunto de propiedades.
        
        Returns:
            Diccionario con estadísticas detalladas
        """
        print("\n" + "="*80)
        print("  ANÁLISIS DE DUPLICADOS MULTI-CRITERIO")
        print("="*80)
        
        # Agrupar por criterio de identificación
        grupos = defaultdict(list)
        criterios_usados = defaultdict(int)
        
        for prop in propiedades:
            criterio, clave = self.identificar_criterio_identificacion(prop)
            grupos[clave].append(prop)
            criterios_usados[criterio] += 1
        
        # Estadísticas generales
        print(f"\nTotal propiedades analizadas: {len(propiedades)}")
        print(f"\nCriterios de identificación utilizados:")
        for criterio, cantidad in sorted(criterios_usados.items(), key=lambda x: x[1], reverse=True):
            print(f"  {criterio:20s}: {cantidad:5d} ({cantidad/len(propiedades)*100:5.1f}%)")
        
        # Identificar grupos duplicados
        grupos_duplicados = {k: v for k, v in grupos.items() if len(v) > 1}
        total_duplicados = sum(len(v) for v in grupos_duplicados.values())
        
        print(f"\nGrupos con duplicados: {len(grupos_duplicados)}")
        print(f"Total propiedades duplicadas: {total_duplicados} ({total_duplicados/len(propiedades)*100:.1f}%)")
        print(f"Propiedades únicas: {len(grupos)} ({len(grupos)/len(propiedades)*100:.1f}%)")
        
        # Análisis por proveedor y fecha
        print(f"\n{'='*80}")
        print("  ANÁLISIS DE NUEVAS VS ACTUALIZADAS POR PROVEEDOR")
        print("="*80)
        
        por_proveedor = defaultdict(lambda: defaultdict(list))
        
        for clave, props in grupos.items():
            if len(props) > 1:
                # Hay duplicados - ordenar por fecha
                props_ordenadas = sorted(
                    props,
                    key=lambda p: (p.get('fecha_scraping', ''), p.get('archivo_origen', '')),
                    reverse=False  # Más antigua primero
                )
                
                for i, prop in enumerate(props_ordenadas):
                    prov = prop.get('codigo_proveedor', 'unknown')
                    fecha = prop.get('fecha_scraping', 'unknown')
                    
                    if i == 0:
                        # Primera aparición = nueva
                        por_proveedor[prov]['nuevas'].append((fecha, prop))
                    else:
                        # Apariciones posteriores = actualizaciones
                        por_proveedor[prov]['actualizadas'].append((fecha, prop))
            else:
                # No hay duplicados - es nueva
                prop = props[0]
                prov = prop.get('codigo_proveedor', 'unknown')
                fecha = prop.get('fecha_scraping', 'unknown')
                por_proveedor[prov]['nuevas'].append((fecha, prop))
        
        # Reportar por proveedor
        for prov in sorted(por_proveedor.keys()):
            datos = por_proveedor[prov]
            nuevas = datos.get('nuevas', [])
            actualizadas = datos.get('actualizadas', [])
            
            print(f"\nPROVEEDOR {prov}:")
            print(f"  Propiedades nuevas:       {len(nuevas):5d}")
            print(f"  Propiedades actualizadas: {len(actualizadas):5d}")
            
            # Agrupar por fecha
            nuevas_por_fecha = defaultdict(int)
            actualizadas_por_fecha = defaultdict(int)
            
            for fecha, prop in nuevas:
                nuevas_por_fecha[fecha] += 1
            for fecha, prop in actualizadas:
                actualizadas_por_fecha[fecha] += 1
            
            if len(nuevas_por_fecha) > 1:
                print(f"  Desglose nuevas por fecha:")
                for fecha in sorted(nuevas_por_fecha.keys()):
                    print(f"    {fecha}: {nuevas_por_fecha[fecha]:5d}")
            
            if actualizadas_por_fecha:
                print(f"  Desglose actualizadas por fecha:")
                for fecha in sorted(actualizadas_por_fecha.keys()):
                    print(f"    {fecha}: {actualizadas_por_fecha[fecha]:5d}")
        
        # Ejemplos de duplicados detectados
        print(f"\n{'='*80}")
        print("  EJEMPLOS DE DUPLICADOS DETECTADOS (Primeros 10)")
        print("="*80)
        
        for i, (clave, props) in enumerate(list(grupos_duplicados.items())[:10], 1):
            print(f"\n{i}. Grupo de {len(props)} propiedades duplicadas:")
            
            for j, prop in enumerate(props, 1):
                titulo = prop.get('titulo', 'Sin título')[:50]
                fecha = prop.get('fecha_scraping', 'unknown')
                prov = prop.get('codigo_proveedor', 'unknown')
                archivo = prop.get('archivo_origen', 'unknown')
                
                print(f"   {j}) [{prov}] {fecha} - {titulo}")
                print(f"      Archivo: {archivo}")
        
        return {
            'total_propiedades': len(propiedades),
            'propiedades_unicas': len(grupos),
            'grupos_duplicados': len(grupos_duplicados),
            'total_duplicados': total_duplicados,
            'porcentaje_duplicados': total_duplicados / len(propiedades) * 100 if propiedades else 0,
            'criterios_usados': dict(criterios_usados),
            'por_proveedor': {
                prov: {
                    'nuevas': len(datos.get('nuevas', [])),
                    'actualizadas': len(datos.get('actualizadas', []))
                }
                for prov, datos in por_proveedor.items()
            }
        }
    
    def seleccionar_version_mas_reciente(self, propiedades: List[dict]) -> List[dict]:
        """
        De todas las propiedades, mantiene solo la versión más reciente de cada una.
        
        Returns:
            Lista de propiedades únicas con versiones más recientes
        """
        grupos = defaultdict(list)
        
        for prop in propiedades:
            criterio, clave = self.identificar_criterio_identificacion(prop)
            grupos[clave].append(prop)
        
        propiedades_finales = []
        
        for clave, props in grupos.items():
            if len(props) == 1:
                propiedades_finales.append(props[0])
            else:
                # Seleccionar la más reciente
                mas_reciente = max(
                    props,
                    key=lambda p: (
                        p.get('fecha_scraping', ''),
                        p.get('archivo_origen', '')
                    )
                )
                
                # Agregar metadato de versiones
                mas_reciente['versiones_previas'] = len(props) - 1
                mas_reciente['ultima_actualizacion'] = mas_reciente.get('fecha_scraping')
                
                propiedades_finales.append(mas_reciente)
        
        return propiedades_finales


def main():
    # Cargar datos
    data_file = Path("data/base_datos_relevamiento.json")
    
    if not data_file.exists():
        print(f"Error: No se encontró {data_file}")
        return
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    propiedades = data.get('propiedades', [])
    
    # Analizar duplicados
    detector = DetectorDuplicados()
    estadisticas = detector.analizar_duplicados(propiedades)
    
    # Generar versión deduplicada
    print(f"\n{'='*80}")
    print("  GENERANDO VERSIÓN DEDUPLICADA")
    print("="*80)
    
    propiedades_unicas = detector.seleccionar_version_mas_reciente(propiedades)
    
    print(f"\nPropiedades originales: {len(propiedades)}")
    print(f"Propiedades únicas:     {len(propiedades_unicas)}")
    print(f"Duplicados eliminados:  {len(propiedades) - len(propiedades_unicas)}")
    print(f"Reducción:              {(len(propiedades) - len(propiedades_unicas))/len(propiedades)*100:.1f}%")
    
    # Guardar resultados
    output_stats = Path("data/estadisticas_duplicados.json")
    with open(output_stats, 'w', encoding='utf-8') as f:
        json.dump(estadisticas, f, ensure_ascii=False, indent=2)
    
    print(f"\nEstadísticas guardadas en: {output_stats}")
    print("="*80)


if __name__ == "__main__":
    main()
