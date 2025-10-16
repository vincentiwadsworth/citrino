#!/usr/bin/env python3
"""
ETL de prueba usando Docker wrapper en lugar de psycopg2 directo
Para migrar datos del archivo procesado a PostgreSQL
"""

import os
import sys
import pandas as pd
import subprocess
from datetime import datetime
import json

class ETLDockerWrapper:
    """ETL que usa Docker wrapper para evitar problemas de psycopg2"""

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

    def insertar_agente(self, nombre, telefono='', email='', empresa=''):
        """Insertar agente con deduplicación"""
        sql = """
        SELECT id FROM agentes
        WHERE LOWER(nombre) = LOWER(%s)
        AND COALESCE(telefono, '') = COALESCE(%s, '')
        LIMIT 1
        """

        result = self.ejecutar_sql(sql, [nombre, telefono])
        if result and result.strip():
            return int(result.strip())

        # Insertar nuevo agente
        sql = """
        INSERT INTO agentes (nombre, telefono, email, empresa)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """

        result = self.ejecutar_sql(sql, [nombre, telefono, email, empresa])
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

    def procesar_archivo_intermedio(self, archivo_path):
        """Procesar archivo intermedio y migrar a PostgreSQL"""
        print(f"Procesando archivo: {archivo_path}")

        try:
            # Leer Excel intermedio
            df = pd.read_excel(archivo_path)
            print(f"Leídas {len(df)} filas del archivo intermedio")

            # Filtrar solo filas con ESTADO = OK
            df_ok = df[df['ESTADO'] == 'OK'].copy()
            print(f"Filas con ESTADO OK: {len(df_ok)}")

            if len(df_ok) == 0:
                print("No hay filas válidas para procesar")
                return

            # Procesar cada propiedad
            insertadas = 0
            for idx, row in df_ok.iterrows():
                # Procesar agente
                agente_id = None
                if pd.notna(row.get('Agente')):
                    agente_id = self.insertar_agente(
                        nombre=str(row.get('Agente', '')),
                        telefono=str(row.get('Teléfono', '')),
                        email=str(row.get('Correo', ''))
                    )

                # Preparar datos de propiedad
                propiedad = {
                    'agente_id': agente_id,
                    'titulo': str(row.get('Título', '')),
                    'descripcion': str(row.get('Descripción', '')),
                    'precio_usd': row.get('Precio_Normalizado') if pd.notna(row.get('Precio_Normalizado')) else None,
                    'habitaciones': int(row.get('Habitaciones')) if pd.notna(row.get('Habitaciones')) and row.get('Habitaciones') > 0 else None,
                    'banos': int(row.get('Baños')) if pd.notna(row.get('Baños')) and row.get('Baños') > 0 else None,
                    'garajes': int(row.get('Garajes')) if pd.notna(row.get('Garajes')) and row.get('Garajes') > 0 else None,
                    'sup_terreno': row.get('Sup. Terreno') if pd.notna(row.get('Sup. Terreno')) else None,
                    'sup_construida': row.get('Sup. Construida') if pd.notna(row.get('Sup. Construida')) else None,
                    'direccion': None,  # No hay en datos
                    'zona': row.get('Zona_Extraida'),
                    'fuente_origen': row.get('fuente_archivo'),
                    'url': str(row.get('URL', '')),
                    'coordenadas_validas': row.get('coordenadas_validadas', False),
                    'datos_completos': row.get('datos_completos', False)
                }

                # Insertar propiedad
                if self.insertar_propiedad(propiedad):
                    insertadas += 1
                    if insertadas % 10 == 0:
                        print(f"Insertadas: {insertadas} propiedades")

            print(f"Total propiedades insertadas: {insertadas}")

            # Verificar resultado
            count_result = self.ejecutar_sql("SELECT COUNT(*) FROM propiedades")
            if count_result:
                total_propiedades = int(count_result)
                print(f"Total propiedades en BD: {total_propiedades}")

            return insertadas

        except Exception as e:
            print(f"Error procesando archivo: {e}")
            return 0

def main():
    """Función principal"""
    etl = ETLDockerWrapper()

    # Procesar archivo intermedio
    archivo_intermedio = 'data/processed/2025.08.15 05_intermedio.xlsx'

    if os.path.exists(archivo_intermedio):
        print("=== ETL CON DOCKER WRAPPER ===")
        resultado = etl.procesar_archivo_intermedio(archivo_intermedio)

        if resultado > 0:
            print(f"ETL completado exitosamente: {resultado} propiedades migradas")
        else:
            print("ETL falló o no migró datos")
    else:
        print(f"Archivo no encontrado: {archivo_intermedio}")

if __name__ == "__main__":
    main()