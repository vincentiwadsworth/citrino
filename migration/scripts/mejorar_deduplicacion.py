#!/usr/bin/env python3
"""
Script para mejorar deduplicación de propiedades usando similitud
Detecta duplicados que no tienen la misma URL pero representan la misma propiedad
"""

import os
import pandas as pd
import psycopg2
import psycopg2.extras
import logging
from typing import List, Dict, Tuple
from difflib import SequenceMatcher
import re
from decimal import Decimal

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/deduplicacion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PropertyDeduplicator:
    """Clase para mejorar deduplicación de propiedades"""

    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.conn = None

    def conectar_db(self):
        """Establecer conexión con PostgreSQL"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.conn.autocommit = False
            logger.info("Conexión exitosa a PostgreSQL")
        except Exception as e:
            logger.error(f"Error conectando a PostgreSQL: {e}")
            raise

    def normalizar_texto(self, texto: str) -> str:
        """Normalizar texto para comparación"""
        if not texto:
            return ""

        # Convertir a minúsculas y remover caracteres especiales
        texto = str(texto).lower()
        texto = re.sub(r'[^\w\s]', '', texto)  # Quitar puntuación
        texto = re.sub(r'\s+', ' ', texto)     # Quitar espacios múltiples
        return texto.strip()

    def similitud_texto(self, texto1: str, texto2: str) -> float:
        """Calcular similitud entre dos textos"""
        texto1_norm = self.normalizar_texto(texto1)
        texto2_norm = self.normalizar_texto(texto2)

        if not texto1_norm or not texto2_norm:
            return 0.0

        return SequenceMatcher(None, texto1_norm, texto2_norm).ratio()

    def similitud_precios(self, precio1: Decimal, precio2: Decimal) -> float:
        """Calcular similitud entre precios (diferencia porcentual)"""
        if not precio1 or not precio2:
            return 0.0

        precio1 = float(precio1)
        precio2 = float(precio2)

        if precio1 == 0 or precio2 == 0:
            return 0.0

        diff = abs(precio1 - precio2)
        avg_price = (precio1 + precio2) / 2

        # Retornar 1 - diferencia porcentual
        return max(0, 1 - (diff / avg_price))

    def similitud_coordenadas(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcular similitud entre coordenadas (cercanía en metros)"""
        if not all([lat1, lon1, lat2, lon2]):
            return 0.0

        # Calcular distancia aproximada en metros
        lat_diff = abs(lat1 - lat2) * 111320  # ~111km por grado de latitud
        lon_diff = abs(lon1 - lon2) * 111320 * abs(lat1) / 90  # Ajuste por longitud

        distance = (lat_diff ** 2 + lon_diff ** 2) ** 0.5

        # Similitud alta si están a menos de 100m
        if distance < 100:
            return 1.0
        elif distance < 500:
            return 0.8
        elif distance < 1000:
            return 0.5
        else:
            return 0.0

    def son_duplicados_probables(self, prop1: Dict, prop2: Dict) -> Tuple[bool, float]:
        """
        Determinar si dos propiedades son probablemente duplicadas
        Retorna (es_duplicado, score_similitud)
        """
        similitudes = []

        # 1. Similitud de título (muy importante)
        sim_titulo = self.similitud_texto(prop1['titulo'], prop2['titulo'])
        similitudes.append(('titulo', sim_titulo, 0.7))

        # 2. Similitud de precio
        sim_precio = self.similitud_precios(prop1['precio_usd'], prop2['precio_usd'])
        similitudes.append(('precio', sim_precio, 0.6))

        # 3. Similitud de coordenadas
        sim_coord = self.similitud_coordenadas(
            prop1['latitud'], prop1['longitud'],
            prop2['latitud'], prop2['longitud']
        )
        similitudes.append(('coordenadas', sim_coord, 0.8))

        # 4. Similitud de características principales
        sim_caract = 0.0
        caract_match = 0
        caract_total = 3

        if prop1['habitaciones'] and prop2['habitaciones']:
            if prop1['habitaciones'] == prop2['habitaciones']:
                caract_match += 1

        if prop1['banos'] and prop2['banos']:
            if prop1['banos'] == prop2['banos']:
                caract_match += 1

        if prop1['sup_terreno'] and prop2['sup_terreno']:
            sup_diff = abs(float(prop1['sup_terreno']) - float(prop2['sup_terreno']))
            sup_avg = (float(prop1['sup_terreno']) + float(prop2['sup_terreno'])) / 2
            if sup_diff / sup_avg < 0.1:  # Menos de 10% de diferencia
                caract_match += 1

        sim_caract = caract_match / caract_total
        similitudes.append(('caracteristicas', sim_caract, 0.5))

        # 5. Similitud de zona
        if prop1['zona'] and prop2['zona']:
            sim_zona = 1.0 if prop1['zona'].lower() == prop2['zona'].lower() else 0.0
        else:
            sim_zona = 0.0
        similitudes.append(('zona', sim_zona, 0.4))

        # Calcular score ponderado
        score_total = 0.0
        peso_total = 0.0

        for criterio, similitud, peso in similitudes:
            score_total += similitud * peso
            peso_total += peso

        score_final = score_total / peso_total if peso_total > 0 else 0.0

        # Reglas para determinar duplicados
        duplicado = False

        # Regla estricta: título muy similar + precio similar
        if sim_titulo > 0.8 and sim_precio > 0.9:
            duplicado = True

        # Regla media: título similar + coordenadas muy cercanas
        elif sim_titulo > 0.6 and sim_coord > 0.8:
            duplicado = True

        # Regla general: score ponderado alto
        elif score_final > 0.75:
            duplicado = True

        return duplicado, score_final

    def detectar_duplicados_en_bd(self) -> List[Dict]:
        """Detectar duplicados en la base de datos existente"""
        logger.info("Buscando propiedades en la base de datos...")

        try:
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            # Cargar todas las propiedades
            cursor.execute("""
                SELECT id, url, titulo, precio_usd, latitud, longitud,
                       habitaciones, banos, sup_terreno, zona
                FROM propiedades
                WHERE url IS NOT NULL
                ORDER BY id
            """)

            propiedades = [dict(row) for row in cursor.fetchall()]
            cursor.close()

            logger.info(f"Analizando {len(propiedades)} propiedades para detectar duplicados...")

            duplicados_encontrados = []
            procesados = set()

            for i, prop1 in enumerate(propiedades):
                if prop1['id'] in procesados:
                    continue

                grupo_duplicados = [prop1['id']]

                for j, prop2 in enumerate(propiedades[i+1:], i+1):
                    if prop2['id'] in procesados:
                        continue

                    # Skip si tienen la misma URL (ya deberían estar deduplicadas)
                    if prop1['url'] == prop2['url']:
                        continue

                    es_duplicado, score = self.son_duplicados_probables(prop1, prop2)

                    if es_duplicado:
                        grupo_duplicados.append(prop2['id'])
                        procesados.add(prop2['id'])

                        duplicados_encontrados.append({
                            'propiedad_1_id': prop1['id'],
                            'propiedad_2_id': prop2['id'],
                            'propiedad_1_url': prop1['url'],
                            'propiedad_2_url': prop2['url'],
                            'propiedad_1_titulo': prop1['titulo'],
                            'propiedad_2_titulo': prop2['titulo'],
                            'score_similitud': score,
                            'motivo': self.determinar_motivo_duplicado(prop1, prop2)
                        })

                procesados.add(prop1['id'])

                if len(grupo_duplicados) > 1:
                    logger.info(f"Grupo de duplicados encontrado: {len(grupo_duplicados)} propiedades")

            logger.info(f"Total de duplicados detectados: {len(duplicados_encontrados)}")
            return duplicados_encontrados

        except Exception as e:
            logger.error(f"Error detectando duplicados: {e}")
            raise

    def determinar_motivo_duplicado(self, prop1: Dict, prop2: Dict) -> str:
        """Determinar el motivo principal por el que se consideran duplicados"""
        sim_titulo = self.similitud_texto(prop1['titulo'], prop2['titulo'])
        sim_precio = self.similitud_precios(prop1['precio_usd'], prop2['precio_usd'])
        sim_coord = self.similitud_coordenadas(
            prop1['latitud'], prop1['longitud'],
            prop2['latitud'], prop2['longitud']
        )

        if sim_titulo > 0.8 and sim_precio > 0.9:
            return "Título y precio muy similares"
        elif sim_titulo > 0.6 and sim_coord > 0.8:
            return "Título similar y coordenadas idénticas"
        elif sim_coord > 0.9:
            return "Coordenadas exactamente iguales"
        elif sim_precio > 0.95:
            return "Precio exactamente igual"
        else:
            return "Múltiples características similares"

    def generar_reporte_duplicados(self, duplicados: List[Dict]) -> Dict:
        """Generar reporte de duplicados encontrado"""
        if not duplicados:
            return {'total_duplicados': 0, 'grupos': []}

        # Agrupar por propiedades que se relacionan entre sí
        grupos = {}
        propiedad_grupo = {}

        for dup in duplicados:
            prop1 = dup['propiedad_1_id']
            prop2 = dup['propiedad_2_id']

            # Encontrar grupo existente o crear nuevo
            grupo1 = propiedad_grupo.get(prop1)
            grupo2 = propiedad_grupo.get(prop2)

            if grupo1 and grupo2:
                # Unir grupos si son diferentes
                if grupo1 != grupo2:
                    grupos[grupo1].extend(grupos[grupo2])
                    for p in grupos[grupo2]:
                        propiedad_grupo[p] = grupo1
                    del grupos[grupo2]
            elif grupo1:
                grupos[grupo1].append(prop2)
                propiedad_grupo[prop2] = grupo1
            elif grupo2:
                grupos[grupo2].append(prop1)
                propiedad_grupo[prop1] = grupo2
            else:
                nuevo_grupo = len(grupos)
                grupos[nuevo_grupo] = [prop1, prop2]
                propiedad_grupo[prop1] = nuevo_grupo
                propiedad_grupo[prop2] = nuevo_grupo

        # Preparar reporte
        reporte = {
            'total_duplicados': len(duplicados),
            'total_grupos': len(grupos),
            'grupos': []
        }

        for grupo_id, propiedades_ids in grupos.items():
            if len(propiedades_ids) > 1:
                grupo_info = {
                    'grupo_id': grupo_id,
                    'propiedades_count': len(propiedades_ids),
                    'propiedades_ids': propiedades_ids,
                    ' duplicados_detalle': []
                }

                # Agregar detalles de duplicados para este grupo
                for dup in duplicados:
                    if dup['propiedad_1_id'] in propiedades_ids:
                        grupo_info['duplicados_detalle'].append(dup)

                reporte['grupos'].append(grupo_info)

        return reporte

    def main(self):
        """Función principal"""
        # Conectar a base de datos
        self.conectar_db()

        try:
            # Detectar duplicados
            duplicados = self.detectar_duplicados_en_bd()

            # Generar reporte
            reporte = self.generar_reporte_duplicados(duplicados)

            # Mostrar resultados
            logger.info("=== REPORTE DE DUPLICADOS ===")
            logger.info(f"Total de duplicados detectados: {reporte['total_duplicados']}")
            logger.info(f"Total de grupos de duplicados: {reporte['total_grupos']}")

            if reporte['grupos']:
                logger.info("Grupos encontrados:")
                for grupo in reporte['grupos'][:5]:  # Mostrar primeros 5
                    logger.info(f"  Grupo {grupo['grupo_id']}: {grupo['propiedades_count']} propiedades")

            # Guardar reporte
            import json
            with open('logs/duplicados_report.json', 'w', encoding='utf-8') as f:
                json.dump(reporte, f, indent=2, ensure_ascii=False, default=str)

            logger.info("Reporte guardado en logs/duplicados_report.json")

            return reporte

        finally:
            if self.conn:
                self.conn.close()

if __name__ == "__main__":
    # Configuración de base de datos
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'citrino'),
        'user': os.getenv('DB_USER', 'citrino_app'),
        'password': os.getenv('DB_PASSWORD', 'password'),
        'port': os.getenv('DB_PORT', '5432')
    }

    # Crear directorio de logs
    os.makedirs('logs', exist_ok=True)

    # Ejecutar análisis
    deduplicador = PropertyDeduplicator(db_config)
    reporte = deduplicador.main()