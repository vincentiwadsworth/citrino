#!/usr/bin/env python3
"""
ETL simple que procesa archivos Excel RAW directamente usando Docker wrapper
Sin dependencia de psycopg2, evitando problemas de encoding
"""

import os
import pandas as pd
import subprocess
from datetime import datetime
import re

class SimpleETL:
    """ETL simple usando Docker wrapper"""

    def __init__(self):
        self.container_name = 'citrino-postgres-new'
        self.db_user = 'citrino_app'
        self.db_name = 'citrino'

    def ejecutar_sql(self, sql, params=None):
        """Ejecutar SQL usando Docker psql"""
        try:
            if params:
                # Reemplazar %s con valores escapados
                param_list = []
                for p in params:
                    if p is None:
                        param_list.append('NULL')
                    else:
                        escaped = str(p).replace("'", "''")
                        param_list.append(f"'{escaped}'")
                formatted_sql = sql % tuple(param_list)
            else:
                formatted_sql = sql

            cmd = [
                'docker', 'exec', '-i', self.container_name,
                'psql', '-U', self.db_user, '-d', self.db_name,
                '-t', '-A', '-c', formatted_sql
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                print(f"Error SQL: {result.stderr}")
                return None

            return result.stdout.strip()

        except Exception as e:
            print(f"Error ejecutando SQL: {e}")
            return None

    def limpiar_precio(self, precio):
        """Limpiar precio y convertir a float"""
        if pd.isna(precio) or not precio:
            return None

        precio_str = str(precio).strip()
        numeros = re.findall(r'[0-9,]+', precio_str)
        if not numeros:
            return None

        precio_limpio = numeros[0].replace(',', '')
        try:
            return float(precio_limpio)
        except ValueError:
            return None

    def validar_coordenadas(self, lat, lon):
        """Validar coordenadas Santa Cruz"""
        if pd.isna(lat) or pd.isna(lon):
            return False, None, None

        try:
            lat_float = float(lat)
            lon_float = float(lon)

            # Validar rango Santa Cruz
            if -18.2 <= lat_float <= -17.5 and -63.5 <= lon_float <= -63.0:
                return True, lat_float, lon_float
            else:
                return False, None, None
        except (ValueError, TypeError):
            return False, None, None

    def extraer_zona(self, titulo, descripcion):
        """Extraer zona desde título/descripción"""
        texto_completo = f"{titulo} {descripcion}".lower()

        zonas_conocidas = [
            'equipetrol', 'santos', 'urbari', 'la paz', 'san pedro', 'las brisas',
            'lazareto', 'pampa', 'sauces', 'el porvenir', 'villarroel',
            '1er anillo', '2do anillo', '3er anillo', '4to anillo',
            'norte', 'sur', 'este', 'oeste', 'centro'
        ]

        for zona in zonas_conocidas:
            if zona in texto_completo:
                return zona.title()

        return None

    def insertar_agente(self, nombre, telefono='', email=''):
        """Insertar agente con deduplicación"""
        if not nombre or pd.isna(nombre):
            return None

        # Buscar existente
        sql = "SELECT id FROM agentes WHERE LOWER(nombre) = LOWER(%s) LIMIT 1"
        result = self.ejecutar_sql(sql, [nombre])
        if result and result.strip():
            return int(result.strip())

        # Insertar nuevo
        sql = """
        INSERT INTO agentes (nombre, telefono, email)
        VALUES (%s, %s, %s)
        RETURNING id
        """
        result = self.ejecutar_sql(sql, [nombre, telefono, email])
        if result:
            return int(result.strip())

        return None

    def insertar_propiedad(self, propiedad_data):
        """Insertar una propiedad"""
        sql = """
        INSERT INTO propiedades (
            agente_id, titulo, descripcion, precio_usd,
            num_dormitorios, num_banos, num_garajes,
            superficie_total, superficie_construida,
            direccion, zona,
            proveedor_datos, url_origen,
            coordenadas_validas, datos_completos
        ) VALUES (
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s,
            %s, %s,
            %s, %s,
            %s, %s
        )
        """

        params = [
            propiedad_data.get('agente_id'),
            propiedad_data.get('titulo'),
            propiedad_data.get('descripcion'),
            propiedad_data.get('precio_usd'),
            propiedad_data.get('habitaciones'),
            propiedad_data.get('banos'),
            propiedad_data.get('garajes'),
            propiedad_data.get('sup_terreno'),
            propiedad_data.get('sup_construida'),
            propiedad_data.get('direccion'),
            propiedad_data.get('zona'),
            propiedad_data.get('fuente_origen'),
            propiedad_data.get('url'),
            propiedad_data.get('coordenadas_validas', False),
            propiedad_data.get('datos_completos', False)
        ]

        result = self.ejecutar_sql(sql, params)
        return result is not None

    def procesar_archivo_raw(self, archivo_path):
        """Procesar archivo Excel RAW directamente"""
        print(f"Procesando archivo RAW: {archivo_path}")

        try:
            # Leer Excel RAW
            df = pd.read_excel(archivo_path)
            print(f"Leídas {len(df)} filas del archivo RAW")
            print(f"Columnas: {list(df.columns)}")

            insertadas = 0
            for idx, row in df.iterrows():
                # Procesar precio
                precio = self.limpiar_precio(row.get('Precio'))
                if not precio:
                    continue  # Saltar propiedades sin precio

                # Validar coordenadas
                coords_ok, lat, lon = self.validar_coordenadas(
                    row.get('Latitud'), row.get('Longitud')
                )

                # Extraer zona
                titulo = str(row.get('Título', ''))
                descripcion = str(row.get('Descripción', ''))
                zona = self.extraer_zona(titulo, descripcion)

                # Procesar agente
                agente_id = None
                agente_nombre = row.get('Agente')
                if pd.notna(agente_nombre) and agente_nombre:
                    agente_id = self.insertar_agente(
                        nombre=str(agente_nombre),
                        telefono=str(row.get('Teléfono', '')),
                        email=str(row.get('Correo', ''))
                    )

                # Preparar datos de propiedad
                propiedad = {
                    'agente_id': agente_id,
                    'titulo': titulo,
                    'descripcion': descripcion,
                    'precio_usd': precio,
                    'habitaciones': int(row.get('Habitaciones')) if pd.notna(row.get('Habitaciones')) and row.get('Habitaciones') > 0 else None,
                    'banos': int(row.get('Baños')) if pd.notna(row.get('Baños')) and row.get('Baños') > 0 else None,
                    'garajes': int(row.get('Garajes')) if pd.notna(row.get('Garajes')) and row.get('Garajes') > 0 else None,
                    'sup_terreno': self.limpiar_precio(row.get('Sup. Terreno')),
                    'sup_construida': self.limpiar_precio(row.get('Sup. Construida')),
                    'direccion': None,
                    'zona': zona,
                    'fuente_origen': os.path.basename(archivo_path),
                    'url': str(row.get('URL', '')),
                    'coordenadas_validas': coords_ok,
                    'datos_completos': bool(precio and coords_ok)
                }

                # Insertar propiedad
                if self.insertar_propiedad(propiedad):
                    insertadas += 1
                    if insertadas % 10 == 0:
                        print(f"Insertadas: {insertadas} propiedades")

            print(f"Total propiedades insertadas: {insertadas}")
            return insertadas

        except Exception as e:
            print(f"Error procesando archivo: {e}")
            import traceback
            traceback.print_exc()
            return 0

def main():
    """Función principal"""
    etl = SimpleETL()

    # Procesar archivo RAW más pequeño
    archivo_raw = 'data/raw/relevamiento/2025.08.15 05.xlsx'

    if os.path.exists(archivo_raw):
        print("=== ETL SIMPLE CON DOCKER WRAPPER ===")
        resultado = etl.procesar_archivo_raw(archivo_raw)

        # Verificar resultado
        count_result = etl.ejecutar_sql("SELECT COUNT(*) FROM propiedades")
        if count_result:
            total_propiedades = int(count_result)
            print(f"Total propiedades en BD: {total_propiedades}")

        count_agentes = etl.ejecutar_sql("SELECT COUNT(*) FROM agentes")
        if count_agentes:
            total_agentes = int(count_agentes)
            print(f"Total agentes en BD: {total_agentes}")

        if resultado > 0:
            print(f"ETL completado exitosamente: {resultado} propiedades migradas")
        else:
            print("ETL falló o no migró datos")
    else:
        print(f"Archivo no encontrado: {archivo_raw}")

if __name__ == "__main__":
    main()