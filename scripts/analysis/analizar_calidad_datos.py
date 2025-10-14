#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analizar la calidad e integridad de los datos de Citrino.
Genera un reporte completo de problemas y estadísticas.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
import logging
import sys

# Configurar encoding para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AnalizadorCalidadDatos:
    """Analiza la calidad e integridad de los datos del proyecto."""

    def __init__(self, ruta_datos: str = "data/base_datos_relevamiento.json"):
        self.ruta_datos = Path(ruta_datos)
        self.propiedades = []
        self.problemas = defaultdict(list)
        self.estadisticas = {}

    def cargar_datos(self):
        """Carga los datos desde el archivo JSON."""
        logger.info(f"Cargando datos desde {self.ruta_datos}...")
        
        with open(self.ruta_datos, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.propiedades = data.get('propiedades', [])
        logger.info(f"Cargadas {len(self.propiedades)} propiedades")

    def analizar_campos_vacios(self):
        """Analiza campos vacíos o nulos en las propiedades."""
        logger.info("\n=== ANALIZANDO CAMPOS VACÍOS ===")
        
        campos_criticos = [
            'precio', 'zona', 'latitud', 'longitud', 'tipo_propiedad',
            'habitaciones', 'banos', 'superficie', 'titulo'
        ]
        
        conteo_vacios = {campo: 0 for campo in campos_criticos}
        
        for prop in self.propiedades:
            for campo in campos_criticos:
                valor = prop.get(campo)
                if valor is None or valor == '' or (isinstance(valor, str) and valor.strip() == ''):
                    conteo_vacios[campo] += 1
                    if len(self.problemas[f'campo_vacio_{campo}']) < 5:  # Guardar solo 5 ejemplos
                        self.problemas[f'campo_vacio_{campo}'].append({
                            'id': prop.get('id'),
                            'titulo': prop.get('titulo', 'Sin título')[:50]
                        })
        
        total = len(self.propiedades)
        print("\n📊 CAMPOS VACÍOS O NULOS:")
        for campo, cantidad in sorted(conteo_vacios.items(), key=lambda x: x[1], reverse=True):
            porcentaje = (cantidad / total) * 100
            estado = "🔴" if porcentaje > 20 else "🟡" if porcentaje > 5 else "🟢"
            print(f"{estado} {campo:20s}: {cantidad:6d} ({porcentaje:5.1f}%)")
        
        self.estadisticas['campos_vacios'] = conteo_vacios

    def analizar_coordenadas(self):
        """Analiza la validez de las coordenadas geográficas."""
        logger.info("\n=== ANALIZANDO COORDENADAS ===")
        
        sin_coordenadas = 0
        coordenadas_invalidas = 0
        fuera_de_rango = 0
        
        # Rangos válidos para Santa Cruz, Bolivia
        LAT_MIN, LAT_MAX = -18.5, -17.0
        LON_MIN, LON_MAX = -64.0, -62.5
        
        for prop in self.propiedades:
            lat = prop.get('latitud')
            lon = prop.get('longitud')
            
            if lat is None or lon is None:
                sin_coordenadas += 1
                continue
            
            try:
                lat = float(lat)
                lon = float(lon)
                
                # Validar rangos para Santa Cruz
                if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
                    fuera_de_rango += 1
                    if len(self.problemas['coordenadas_fuera_rango']) < 5:
                        self.problemas['coordenadas_fuera_rango'].append({
                            'id': prop.get('id'),
                            'titulo': prop.get('titulo', 'Sin título')[:50],
                            'lat': lat,
                            'lon': lon
                        })
            except (ValueError, TypeError):
                coordenadas_invalidas += 1
        
        total = len(self.propiedades)
        print("\n🗺️ ANÁLISIS DE COORDENADAS:")
        print(f"🔴 Sin coordenadas:        {sin_coordenadas:6d} ({sin_coordenadas/total*100:5.1f}%)")
        print(f"🔴 Coordenadas inválidas:  {coordenadas_invalidas:6d} ({coordenadas_invalidas/total*100:5.1f}%)")
        print(f"🟡 Fuera de rango SC:      {fuera_de_rango:6d} ({fuera_de_rango/total*100:5.1f}%)")
        print(f"🟢 Coordenadas válidas:    {total - sin_coordenadas - coordenadas_invalidas - fuera_de_rango:6d} ({(total - sin_coordenadas - coordenadas_invalidas - fuera_de_rango)/total*100:5.1f}%)")
        
        self.estadisticas['coordenadas'] = {
            'sin_coordenadas': sin_coordenadas,
            'invalidas': coordenadas_invalidas,
            'fuera_rango': fuera_de_rango,
            'validas': total - sin_coordenadas - coordenadas_invalidas - fuera_de_rango
        }

    def analizar_zonas(self):
        """Analiza la distribución y calidad de las zonas."""
        logger.info("\n=== ANALIZANDO ZONAS ===")
        
        zonas_distribucion = defaultdict(int)
        sin_zona = 0
        
        for prop in self.propiedades:
            zona = prop.get('zona', '').strip()
            if not zona:
                sin_zona += 1
            else:
                zonas_distribucion[zona] += 1
        
        total = len(self.propiedades)
        print(f"\n🏘️ ANÁLISIS DE ZONAS:")
        print(f"Total de zonas únicas:     {len(zonas_distribucion)}")
        print(f"🔴 Propiedades sin zona:   {sin_zona:6d} ({sin_zona/total*100:5.1f}%)")
        print(f"\n📍 Top 15 zonas más frecuentes:")
        
        for i, (zona, cantidad) in enumerate(sorted(zonas_distribucion.items(), key=lambda x: x[1], reverse=True)[:15], 1):
            print(f"{i:2d}. {zona:30s}: {cantidad:5d} ({cantidad/total*100:5.1f}%)")
        
        self.estadisticas['zonas'] = {
            'total_zonas': len(zonas_distribucion),
            'sin_zona': sin_zona,
            'distribucion': dict(sorted(zonas_distribucion.items(), key=lambda x: x[1], reverse=True)[:20])
        }

    def analizar_precios(self):
        """Analiza la distribución y anomalías en precios."""
        logger.info("\n=== ANALIZANDO PRECIOS ===")
        
        precios_validos = []
        sin_precio = 0
        precios_extremos = []
        
        for prop in self.propiedades:
            precio = prop.get('precio')
            if precio is None:
                sin_precio += 1
            else:
                try:
                    precio = float(precio)
                    precios_validos.append(precio)
                    
                    # Detectar precios extremos (< $10k o > $1M)
                    if precio < 10000 or precio > 1000000:
                        if len(precios_extremos) < 10:
                            precios_extremos.append({
                                'id': prop.get('id'),
                                'titulo': prop.get('titulo', 'Sin título')[:40],
                                'precio': precio,
                                'zona': prop.get('zona', 'Sin zona')
                            })
                except (ValueError, TypeError):
                    sin_precio += 1
        
        if precios_validos:
            df_precios = pd.Series(precios_validos)
            print(f"\n💰 ANÁLISIS DE PRECIOS:")
            print(f"🔴 Sin precio:             {sin_precio:6d} ({sin_precio/len(self.propiedades)*100:5.1f}%)")
            print(f"🟢 Con precio válido:      {len(precios_validos):6d} ({len(precios_validos)/len(self.propiedades)*100:5.1f}%)")
            print(f"\n📊 Estadísticas de Precios (USD):")
            print(f"Mínimo:                    ${df_precios.min():>12,.0f}")
            print(f"Máximo:                    ${df_precios.max():>12,.0f}")
            print(f"Media:                     ${df_precios.mean():>12,.0f}")
            print(f"Mediana:                   ${df_precios.median():>12,.0f}")
            print(f"Percentil 25:              ${df_precios.quantile(0.25):>12,.0f}")
            print(f"Percentil 75:              ${df_precios.quantile(0.75):>12,.0f}")
            
            if precios_extremos:
                print(f"\n🟡 Precios extremos detectados ({len(precios_extremos)} ejemplos):")
                for pe in precios_extremos[:5]:
                    print(f"   ${pe['precio']:>10,.0f} - {pe['titulo'][:40]} ({pe['zona']})")
        
        self.estadisticas['precios'] = {
            'sin_precio': sin_precio,
            'con_precio': len(precios_validos),
            'min': float(df_precios.min()) if precios_validos else 0,
            'max': float(df_precios.max()) if precios_validos else 0,
            'media': float(df_precios.mean()) if precios_validos else 0,
            'mediana': float(df_precios.median()) if precios_validos else 0
        }

    def analizar_duplicados(self):
        """Detecta posibles duplicados por coordenadas o dirección."""
        logger.info("\n=== ANALIZANDO DUPLICADOS ===")
        
        # Agrupar por coordenadas exactas
        coordenadas_grupos = defaultdict(list)
        for prop in self.propiedades:
            lat = prop.get('latitud')
            lon = prop.get('longitud')
            if lat and lon:
                clave = (round(float(lat), 6), round(float(lon), 6))
                coordenadas_grupos[clave].append(prop)
        
        duplicados_coords = {k: v for k, v in coordenadas_grupos.items() if len(v) > 1}
        
        print(f"\n🔄 ANÁLISIS DE DUPLICADOS:")
        print(f"Grupos de coordenadas idénticas:    {len(duplicados_coords)}")
        print(f"Total propiedades en duplicados:    {sum(len(v) for v in duplicados_coords.values())}")
        
        if duplicados_coords:
            print(f"\n📍 Ejemplos de duplicados (primeros 5 grupos):")
            for i, (coords, props) in enumerate(list(duplicados_coords.items())[:5], 1):
                print(f"\n{i}. Coordenadas {coords} ({len(props)} propiedades):")
                for prop in props[:3]:
                    print(f"   - {prop.get('titulo', 'Sin título')[:50]}")
        
        self.estadisticas['duplicados'] = {
            'grupos_coordenadas': len(duplicados_coords),
            'total_propiedades_duplicadas': sum(len(v) for v in duplicados_coords.values())
        }

    def analizar_tipos_propiedad(self):
        """Analiza la distribución de tipos de propiedad."""
        logger.info("\n=== ANALIZANDO TIPOS DE PROPIEDAD ===")
        
        tipos_distribucion = defaultdict(int)
        sin_tipo = 0
        
        for prop in self.propiedades:
            tipo = prop.get('tipo_propiedad', '').strip()
            if not tipo:
                sin_tipo += 1
            else:
                tipos_distribucion[tipo] += 1
        
        total = len(self.propiedades)
        print(f"\n🏠 ANÁLISIS DE TIPOS DE PROPIEDAD:")
        print(f"Tipos únicos encontrados:  {len(tipos_distribucion)}")
        print(f"🔴 Sin tipo:               {sin_tipo:6d} ({sin_tipo/total*100:5.1f}%)")
        print(f"\n📋 Distribución de tipos:")
        
        for tipo, cantidad in sorted(tipos_distribucion.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {tipo:30s}: {cantidad:5d} ({cantidad/total*100:5.1f}%)")
        
        self.estadisticas['tipos_propiedad'] = {
            'total_tipos': len(tipos_distribucion),
            'sin_tipo': sin_tipo,
            'distribucion': dict(sorted(tipos_distribucion.items(), key=lambda x: x[1], reverse=True)[:15])
        }

    def generar_reporte_completo(self):
        """Genera un reporte completo de calidad de datos."""
        print("\n" + "="*80)
        print("  📊 REPORTE DE CALIDAD E INTEGRIDAD DE DATOS - CITRINO")
        print("="*80)
        print(f"Total de propiedades analizadas: {len(self.propiedades):,}")
        print("="*80)
        
        self.analizar_campos_vacios()
        self.analizar_coordenadas()
        self.analizar_zonas()
        self.analizar_precios()
        self.analizar_tipos_propiedad()
        self.analizar_duplicados()
        
        print("\n" + "="*80)
        print("  🎯 RESUMEN Y RECOMENDACIONES")
        print("="*80)
        
        # Calcular score de calidad general
        total = len(self.propiedades)
        campos_criticos_completos = total - max([
            self.estadisticas['campos_vacios'].get('precio', 0),
            self.estadisticas['campos_vacios'].get('zona', 0),
            self.estadisticas['coordenadas']['sin_coordenadas']
        ])
        
        score_calidad = (campos_criticos_completos / total) * 100
        
        print(f"\n📈 Score de Calidad General: {score_calidad:.1f}%")
        
        if score_calidad < 70:
            print("🔴 CRÍTICO - Calidad de datos deficiente")
        elif score_calidad < 85:
            print("🟡 ADVERTENCIA - Calidad de datos mejorable")
        else:
            print("🟢 BUENO - Calidad de datos aceptable")
        
        print("\n🔧 PRIORIDADES DE MEJORA:")
        
        prioridades = []
        
        # Evaluar problemas críticos
        if self.estadisticas['coordenadas']['sin_coordenadas'] > total * 0.1:
            prioridades.append(f"1️⃣ ALTO - Completar coordenadas faltantes ({self.estadisticas['coordenadas']['sin_coordenadas']} propiedades)")
        
        if self.estadisticas['campos_vacios'].get('zona', 0) > total * 0.1:
            prioridades.append(f"2️⃣ ALTO - Completar zonas faltantes ({self.estadisticas['campos_vacios'].get('zona', 0)} propiedades)")
        
        if self.estadisticas['campos_vacios'].get('precio', 0) > total * 0.15:
            prioridades.append(f"3️⃣ ALTO - Completar precios faltantes ({self.estadisticas['campos_vacios'].get('precio', 0)} propiedades)")
        
        if self.estadisticas['duplicados']['grupos_coordenadas'] > 0:
            prioridades.append(f"4️⃣ MEDIO - Revisar y resolver duplicados ({self.estadisticas['duplicados']['grupos_coordenadas']} grupos)")
        
        if self.estadisticas['coordenadas']['fuera_rango'] > 0:
            prioridades.append(f"5️⃣ MEDIO - Validar coordenadas fuera de rango ({self.estadisticas['coordenadas']['fuera_rango']} propiedades)")
        
        for prioridad in prioridades:
            print(f"   {prioridad}")
        
        if not prioridades:
            print("   ✅ No se detectaron problemas críticos")
        
        # Guardar estadísticas en JSON
        output_file = Path("data/reporte_calidad_datos.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.estadisticas, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Reporte detallado guardado en: {output_file}")
        print("="*80)

    def ejecutar_analisis(self):
        """Ejecuta el análisis completo."""
        try:
            self.cargar_datos()
            self.generar_reporte_completo()
        except Exception as e:
            logger.error(f"Error durante el análisis: {e}")
            raise


def main():
    """Función principal."""
    analizador = AnalizadorCalidadDatos()
    analizador.ejecutar_analisis()


if __name__ == "__main__":
    main()
