#!/usr/bin/env python3
"""
Script simple para migrar propiedades aprobadas usando Docker directo
=================================================================

Script simplificado que inserta las propiedades aprobadas directamente
sin dependencias complejas.

Usage:
    python migrate_approved_simple.py
"""

import sys
import os
import pandas as pd
from pathlib import Path
from datetime import datetime
import subprocess
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def execute_sql_via_docker(sql: str, fetch: bool = False) -> list:
    """Execute SQL via Docker and return results if fetch=True"""
    cmd = [
        'docker', 'exec', 'citrino-postgresql',
        'psql', '-U', 'citrino_app', '-d', 'citrino',
        '-t', '-A', '-c', sql
    ]

    try:
        # FIX: Especificar encoding UTF-8 y error handling para Windows
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            encoding='utf-8',          # Forzar UTF-8
            errors='replace'           # Reemplazar caracteres inválidos
        )
        if result.returncode != 0:
            logger.error(f"SQL failed: {result.stderr}")
            raise Exception(f"Docker SQL failed: {result.stderr}")

        if fetch:
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
        return []
    except Exception as e:
        logger.error(f"Error executing SQL: {e}")
        raise

def approve_and_migrate():
    """Approve properties and migrate them to PostgreSQL"""

    # Data paths
    project_root = Path(__file__).parent.parent.parent
    intermediate_dir = project_root / "data" / "intermediate"

    # Find intermediate files
    intermediate_files = list(intermediate_dir.glob("*_intermedio.xlsx"))
    logger.info(f"Found {len(intermediate_files)} intermediate files")

    # Collect approved properties
    all_approved = []
    total_read = 0

    for file_path in intermediate_files:
        logger.info(f"Processing {file_path.name}")

        try:
            df = pd.read_excel(file_path)
            total_read += len(df)

            # Apply approval criteria
            def approve_property(row):
                # Estado debe ser OK o WARNING
                estado = str(row.get('ESTADO', '')).upper()
                if estado not in ['OK', 'WARNING']:
                    return False

                # Título completo
                titulo = str(row.get('TÍTULO', '')).strip()
                if not titulo or titulo.lower() == 'sin título':
                    return False

                # Coordenadas válidas (Santa Cruz bounds)
                try:
                    lat = float(row.get('LATITUD', 0)) if pd.notna(row.get('LATITUD')) else None
                    lng = float(row.get('LONGITUD', 0)) if pd.notna(row.get('LONGITUD')) else None

                    if lat is None or lng is None:
                        return False
                    if not (-18.2 <= lat <= -17.5) or not (-63.5 <= lng <= -63.0):
                        return False
                except (ValueError, TypeError):
                    return False

                # Precio realista
                try:
                    precio = float(row.get('PRECIO_USD', 0)) if pd.notna(row.get('PRECIO_USD')) else None
                    if precio is None or precio <= 0 or precio < 1000 or precio > 5000000:
                        return False
                except (ValueError, TypeError):
                    return False

                # Zona y tipo asignados
                zona = str(row.get('ZONA', '')).strip()
                tipo = str(row.get('TIPO_PROPIEDAD', '')).strip()

                if not zona or zona.lower() in ['nan', 'none', '']:
                    return False
                if not tipo or tipo.lower() in ['nan', 'none', '']:
                    return False

                return True

            approved_mask = df.apply(approve_property, axis=1)
            approved_df = df[approved_mask]

            logger.info(f"  Approved: {len(approved_df)}, Rejected: {len(df) - len(approved_df)}")

            # Convert to SQL insert format
            for _, row in approved_df.iterrows():
                # Build SQL INSERT values
                titulo = str(row.get('TÍTULO', '')).replace("'", "''")
                descripcion = str(row.get('DESCRIPCIÓN', '')).replace("'", "''") if pd.notna(row.get('DESCRIPCIÓN')) else None
                tipo = str(row.get('TIPO_PROPIEDAD', '')).lower()
                zona = str(row.get('ZONA', '')).strip().title()
                precio = float(row.get('PRECIO_USD', 0))
                lat = float(row.get('LATITUD', 0))
                lng = float(row.get('LONGITUD', 0))

                # Generate PostGIS coordinates
                coords_sql = f"ST_SetSRID(ST_MakePoint({lng}, {lat}), 4326)::geography"

                # Build INSERT SQL
                insert_sql = f"""
                INSERT INTO propiedades (
                    titulo, descripcion, tipo_propiedad,
                    precio_usd, zona, coordenadas, coordenadas_validas,
                    datos_completos, proveedor_datos, fecha_scraping
                ) VALUES (
                    '{titulo}',
                    {f"'{descripcion}'" if descripcion else 'NULL'},
                    '{tipo}',
                    {precio},
                    '{zona}',
                    {coords_sql},
                    TRUE,
                    TRUE,
                    'excel_intermedio_approved',
                    NOW()
                );
                """

                all_approved.append(insert_sql)

        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
            continue

    logger.info(f"Total approved properties: {len(all_approved)}")
    logger.info(f"Total properties read: {total_read}")

    if not all_approved:
        logger.warning("No properties to migrate")
        return

    # Execute migration
    logger.info("Starting migration to PostgreSQL...")

    try:
        migrated_count = 0
        for i, insert_sql in enumerate(all_approved):
            try:
                execute_sql_via_docker(insert_sql)
                migrated_count += 1

                if (i + 1) % 10 == 0:
                    logger.info(f"Migrated {i + 1}/{len(all_approved)} properties...")

            except Exception as e:
                logger.warning(f"Failed to migrate property {i+1}: {e}")

        logger.info(f"Migration completed: {migrated_count}/{len(all_approved)} properties migrated")

        # Verify results
        count_result = execute_sql_via_docker("SELECT COUNT(*) FROM propiedades;", fetch=True)
        final_count = int(count_result[0]) if count_result else 0

        logger.info(f"Final database count: {final_count} properties")

        # Show sample
        sample_sql = """
        SELECT titulo, zona, precio_usd, tipo_propiedad
        FROM propiedades
        ORDER BY id
        LIMIT 5;
        """
        sample_result = execute_sql_via_docker(sample_sql, fetch=True)

        logger.info("Sample migrated properties:")
        for row in sample_result:
            logger.info(f"  {row}")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    try:
        approve_and_migrate()
        logger.info("✅ Migration completed successfully!")
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)