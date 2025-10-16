#!/usr/bin/env python3
"""
Generar archivo SQL para migración de propiedades aprobadas
==========================================================

Este script genera un archivo SQL con todas las propiedades aprobadas
que luego se puede ejecutar directamente en PostgreSQL.

Usage:
    python generate_migration_sql.py
    docker exec -i citrino-postgresql psql -U citrino_app -d citrino < migration_approved.sql
"""

import pandas as pd
from pathlib import Path

def generate_migration_sql():
    """Generate SQL file with approved properties"""

    # Data paths
    project_root = Path(__file__).parent.parent.parent
    intermediate_dir = project_root / "data" / "intermediate"

    # Find intermediate files
    intermediate_files = list(intermediate_dir.glob("*_intermedio.xlsx"))
    print(f"Found {len(intermediate_files)} intermediate files")

    # Generate SQL content
    sql_statements = []
    sql_statements.append("-- Migration of approved properties")
    sql_statements.append("-- Generated at: " + str(pd.Timestamp.now()))
    sql_statements.append("")
    sql_statements.append("BEGIN;")
    sql_statements.append("")

    total_read = 0
    total_approved = 0

    for file_path in intermediate_files:
        print(f"Processing {file_path.name}")

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

            print(f"  Approved: {len(approved_df)}, Rejected: {len(df) - len(approved_df)}")
            total_approved += len(approved_df)

            # Generate INSERT statements
            for _, row in approved_df.iterrows():
                # Clean and escape values
                titulo = str(row.get('TÍTULO', '')).replace("'", "''")
                descripcion = str(row.get('DESCRIPCIÓN', '')).replace("'", "''") if pd.notna(row.get('DESCRIPCIÓN')) else None
                tipo = str(row.get('TIPO_PROPIEDAD', '')).lower()
                zona = str(row.get('ZONA', '')).strip().title()
                precio = float(row.get('PRECIO_USD', 0))
                lat = float(row.get('LATITUD', 0))
                lng = float(row.get('LONGITUD', 0))

                # Optional fields
                direccion = str(row.get('DIRECCIÓN', '')).replace("'", "''") if pd.notna(row.get('DIRECCIÓN')) and str(row.get('DIRECCIÓN', '')).strip() else None
                superficie_total = float(row.get('SUPERFICIE_TOTAL', 0)) if pd.notna(row.get('SUPERFICIE_TOTAL')) and row.get('SUPERFICIE_TOTAL') > 0 else None
                superficie_construida = float(row.get('SUPERFICIE_CONSTRUIDA', 0)) if pd.notna(row.get('SUPERFICIE_CONSTRUIDA')) and row.get('SUPERFICIE_CONSTRUIDA') > 0 else None
                num_dormitorios = int(row.get('NUM_DORMITORIOS', 0)) if pd.notna(row.get('NUM_DORMITORIOS')) and row.get('NUM_DORMITORIOS') > 0 else None
                num_banos = int(row.get('NUM_BAÑOS', 0)) if pd.notna(row.get('NUM_BAÑOS')) and row.get('NUM_BAÑOS') > 0 else None
                num_garajes = int(row.get('NUM_GARAJES', 0)) if pd.notna(row.get('NUM_GARAJES')) and row.get('NUM_GARAJES') > 0 else None
                url_origen = str(row.get('URL_ORIGEN', '')).replace("'", "''") if pd.notna(row.get('URL_ORIGEN')) and str(row.get('URL_ORIGEN', '')).strip() else None

                # Build INSERT SQL
                sql = f"""INSERT INTO propiedades (
    titulo, descripcion, tipo_propiedad, estado_propiedad,
    precio_usd, direccion, zona, superficie_total, superficie_construida,
    num_dormitorios, num_banos, num_garajes, coordenadas, coordenadas_validas,
    datos_completos, proveedor_datos, url_origen, fecha_scraping
) VALUES (
    '{titulo}',
    {f"'{descripcion}'" if descripcion else 'NULL'},
    '{tipo}',
    'disponible',
    {precio},
    {f"'{direccion}'" if direccion else 'NULL'},
    '{zona}',
    {superficie_total if superficie_total else 'NULL'},
    {superficie_construida if superficie_construida else 'NULL'},
    {num_dormitorios if num_dormitorios else 'NULL'},
    {num_banos if num_banos else 'NULL'},
    {num_garajes if num_garajes else 'NULL'},
    ST_SetSRID(ST_MakePoint({lng}, {lat}), 4326)::geography,
    TRUE,
    TRUE,
    'excel_intermedio_approved',
    {f"'{url_origen}'" if url_origen else 'NULL'},
    NOW()
) ON CONFLICT (titulo, zona) DO NOTHING;"""

                sql_statements.append(sql)
                sql_statements.append("")

        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")
            continue

    # Add final statements
    sql_statements.append("COMMIT;")
    sql_statements.append("")
    sql_statements.append("-- Migration summary")
    sql_statements.append(f"-- Total properties read: {total_read}")
    sql_statements.append(f"-- Total properties approved: {total_approved}")
    sql_statements.append(f"-- Approval rate: {total_approved/total_read*100:.1f}%")

    print(f"Total approved properties: {total_approved}")
    print(f"Total properties read: {total_read}")
    print(f"Approval rate: {total_approved/total_read*100:.1f}%")

    # Write SQL file
    sql_file = project_root / "migration_approved.sql"
    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_statements))

    print(f"✅ SQL file generated: {sql_file}")
    print(f"📄 Execute with: docker exec -i citrino-postgresql psql -U citrino_app -d citrino < migration_approved.sql")

if __name__ == "__main__":
    generate_migration_sql()