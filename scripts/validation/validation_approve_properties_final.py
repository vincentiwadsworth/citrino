#!/usr/bin/env python3
"""
Script para aprobar datos intermedios y migrarlos a PostgreSQL
==============================================================

Este script lee los archivos intermedios generados por el ETL,
filtra las propiedades que cumplen con los criterios de calidad,
y las migra a la base de datos PostgreSQL.

Criterios de aprobación:
- ESTADO debe ser 'OK' o 'WARNING'
- Coordenadas válidas (Santa Cruz bounds)
- Precio realista (> $1,000 y <$5M)
- Título, zona y tipo de propiedad completos

Usage:
    python approve_intermediate_data.py [--dry-run] [--verbose]
"""

import sys
import os
import time
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import database configuration
sys.path.append(str(Path(__file__).parent.parent / "migration" / "config"))
try:
    from database_config import DatabaseConfig, DockerPostgresConnection
    load_database_config = lambda: DatabaseConfig(
        host='localhost', port=5433, database='citrino',
        user='citrino_app', password='citrino123'
    )
    create_connection = lambda config: DockerPostgresConnection(config)
except ImportError:
    print("WARNING: database_config not available, using dry-run mode")
    def create_connection(config): return None
    def load_database_config(): return None

# Configuration
SANTA_CRUZ_BOUNDS = {
    'lat_min': -18.2, 'lat_max': -17.5,
    'lng_min': -63.5, 'lng_max': -63.0
}

class DataApprover:
    """Approves intermediate data and migrates to PostgreSQL"""

    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.setup_logging()
        self.db_connection = None

        # Data paths
        self.project_root = Path(__file__).parent.parent.parent
        self.intermediate_dir = self.project_root / "data" / "intermediate"

        # Statistics
        self.stats = {
            'total_files_processed': 0,
            'total_properties_read': 0,
            'properties_approved': 0,
            'properties_rejected': 0,
            'properties_migrated': 0,
            'migration_errors': 0,
            'execution_time_ms': 0
        }

    def setup_logging(self):
        """Configure logging based on verbosity"""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)

    def connect_database(self) -> bool:
        """Establish connection to PostgreSQL database"""
        try:
            if self.dry_run:
                self.logger.info("DRY RUN: Would connect to PostgreSQL database")
                return True

            db_config = load_database_config()
            self.db_connection = create_connection(db_config)
            self.logger.info("Connected to PostgreSQL database")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            return False

    def load_intermediate_files(self) -> List[Path]:
        """Load all intermediate Excel files"""
        if not self.intermediate_dir.exists():
            self.logger.error(f"Intermediate directory not found: {self.intermediate_dir}")
            return []

        files = list(self.intermediate_dir.glob("*_intermedio.xlsx"))
        if not files:
            self.logger.warning(f"No intermediate files found in {self.intermediate_dir}")
        else:
            self.logger.info(f"Found {len(files)} intermediate files")

        return files

    def approve_property(self, row: pd.Series) -> bool:
        """Determine if a property meets approval criteria"""

        # CRITERIO 1: Estado de validación
        estado = str(row.get('ESTADO', '')).upper()
        if estado not in ['OK', 'WARNING']:
            return False

        # CRITERIO 2: Título completo
        titulo = str(row.get('TÍTULO', '')).strip()
        if not titulo or titulo.lower() == 'sin título':
            return False

        # CRITERIO 3: Coordenadas válidas
        try:
            lat = float(row.get('LATITUD', 0)) if pd.notna(row.get('LATITUD')) else None
            lng = float(row.get('LONGITUD', 0)) if pd.notna(row.get('LONGITUD')) else None

            if lat is None or lng is None:
                return False

            # Validar bounds de Santa Cruz
            if not (SANTA_CRUZ_BOUNDS['lat_min'] <= lat <= SANTA_CRUZ_BOUNDS['lat_max']):
                return False
            if not (SANTA_CRUZ_BOUNDS['lng_min'] <= lng <= SANTA_CRUZ_BOUNDS['lng_max']):
                return False

        except (ValueError, TypeError):
            return False

        # CRITERIO 4: Precio realista
        try:
            precio = float(row.get('PRECIO_USD', 0)) if pd.notna(row.get('PRECIO_USD')) else None
            if precio is None or precio <= 0:
                return False
            if precio < 1000 or precio > 5000000:  # $1k - $5M rango realista
                return False
        except (ValueError, TypeError):
            return False

        # CRITERIO 5: Zona asignada
        zona = str(row.get('ZONA', '')).strip()
        if not zona or zona.lower() in ['nan', 'none', '']:
            return False

        # CRITERIO 6: Tipo de propiedad asignado
        tipo = str(row.get('TIPO_PROPIEDAD', '')).strip()
        if not tipo or tipo.lower() in ['nan', 'none', '']:
            return False

        return True

    def process_intermediate_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Process a single intermediate file and return approved properties"""
        self.logger.info(f"Processing intermediate file: {file_path.name}")

        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            self.logger.info(f"Read {len(df)} properties from {file_path.name}")

            # Apply approval criteria
            approved_mask = df.apply(self.approve_property, axis=1)
            approved_df = df[approved_mask]
            rejected_df = df[~approved_mask]

            self.logger.info(f"Approved: {len(approved_df)}, Rejected: {len(rejected_df)}")

            # Log rejection reasons
            if self.verbose and len(rejected_df) > 0:
                self.logger.debug("Rejection reasons:")
                for idx, row in rejected_df.head(5).iterrows():
                    estado = str(row.get('ESTADO', 'UNKNOWN'))
                    titulo = str(row.get('TÍTULO', 'No title'))[:50]
                    self.logger.debug(f"  Rejected: {estado} | {titulo}...")

            # Update statistics
            self.stats['total_properties_read'] += len(df)
            self.stats['properties_approved'] += len(approved_df)
            self.stats['properties_rejected'] += len(rejected_df)

            # Convert to list of dictionaries for migration
            approved_properties = []
            for _, row in approved_df.iterrows():
                prop_data = {
                    'titulo': str(row.get('TÍTULO', '')),
                    'descripcion': str(row.get('DESCRIPCIÓN', '')) if pd.notna(row.get('DESCRIPCIÓN')) else None,
                    'tipo_propiedad': str(row.get('TIPO_PROPIEDAD', '')).lower(),
                    'estado_propiedad': 'disponible',  # Default value
                    'precio_usd': float(row.get('PRECIO_USD', 0)) if pd.notna(row.get('PRECIO_USD')) else None,
                    'direccion': str(row.get('DIRECCIÓN', '')) if pd.notna(row.get('DIRECCIÓN')) and str(row.get('DIRECCIÓN', '')).strip() else None,
                    'zona': str(row.get('ZONA', '')).strip().title(),
                    'uv': str(row.get('UV', '')).strip().upper() if pd.notna(row.get('UV')) and str(row.get('UV', '')).strip() else None,
                    'manzana': str(row.get('MANZANA', '')).strip().upper() if pd.notna(row.get('MANZANA')) and str(row.get('MANZANA', '')).strip() else None,
                    'lote': str(row.get('LOTE', '')).strip().upper() if pd.notna(row.get('LOTE')) and str(row.get('LOTE', '')).strip() else None,
                    'superficie_total': float(row.get('SUPERFICIE_TOTAL', 0)) if pd.notna(row.get('SUPERFICIE_TOTAL')) and row.get('SUPERFICIE_TOTAL') > 0 else None,
                    'superficie_construida': float(row.get('SUPERFICIE_CONSTRUIDA', 0)) if pd.notna(row.get('SUPERFICIE_CONSTRUIDA')) and row.get('SUPERFICIE_CONSTRUIDA') > 0 else None,
                    'num_dormitorios': int(row.get('NUM_DORMITORIOS', 0)) if pd.notna(row.get('NUM_DORMITORIOS')) and row.get('NUM_DORMITORIOS') > 0 else None,
                    'num_banos': int(row.get('NUM_BAÑOS', 0)) if pd.notna(row.get('NUM_BAÑOS')) and row.get('NUM_BAÑOS') > 0 else None,
                    'num_garajes': int(row.get('NUM_GARAJES', 0)) if pd.notna(row.get('NUM_GARAJES')) and row.get('NUM_GARAJES') > 0 else None,
                    'latitud': float(row.get('LATITUD', 0)) if pd.notna(row.get('LATITUD')) else None,
                    'longitud': float(row.get('LONGITUD', 0)) if pd.notna(row.get('LONGITUD')) else None,
                    'proveedor_datos': 'excel_intermedio_approved',
                    'url_origen': str(row.get('URL_ORIGEN', '')) if pd.notna(row.get('URL_ORIGEN')) and str(row.get('URL_ORIGEN', '')).strip() else None
                }
                approved_properties.append(prop_data)

            return approved_properties

        except Exception as e:
            self.logger.error(f"Error processing file {file_path.name}: {e}")
            self.stats['migration_errors'] += 1
            return []

    def migrate_approved_properties(self, all_approved_properties: List[Dict[str, Any]]) -> bool:
        """Migrate all approved properties to PostgreSQL"""
        self.logger.info(f"Starting migration of {len(all_approved_properties)} approved properties")

        if self.dry_run:
            self.logger.info(f"DRY RUN: Would migrate {len(all_approved_properties)} properties")
            # Show sample
            for i, prop in enumerate(all_approved_properties[:5]):
                self.logger.info(f"  {i+1}. {prop['titulo'][:50]}... | {prop['zona']} | ${prop['precio_usd']} | {prop['tipo_propiedad']}")
            if len(all_approved_properties) > 5:
                self.logger.info(f"  ... and {len(all_approved_properties) - 5} more")
            return True

        try:
            cursor = self.db_connection.cursor()

            # Prepare batch insert
            batch_size = 500
            total_migrated = 0

            for i in range(0, len(all_approved_properties), batch_size):
                batch = all_approved_properties[i:i + batch_size]

                for prop in batch:
                    try:
                        # Generate PostGIS coordinates
                        if prop['latitud'] and prop['longitud']:
                            coords_postgis = f"ST_SetSRID(ST_MakePoint({prop['longitud']}, {prop['latitud']}), 4326)::geography"
                            coords_validas = True
                        else:
                            coords_postgis = None
                            coords_validas = False

                        # Insert query with ON CONFLICT handling
                        insert_query = """
                        INSERT INTO propiedades (
                            titulo, descripcion, tipo_propiedad, estado_propiedad,
                            precio_usd, direccion, zona, uv, manzana, lote,
                            superficie_total, superficie_construida,
                            num_dormitorios, num_banos, num_garajes,
                            coordenadas, coordenadas_validas, datos_completos,
                            proveedor_datos, url_origen, fecha_scraping
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (titulo, zona) DO UPDATE SET
                            descripcion = EXCLUDED.descripcion,
                            estado_propiedad = EXCLUDED.estado_propiedad,
                            precio_usd = EXCLUDED.precio_usd,
                            direccion = EXCLUDED.direccion,
                            uv = EXCLUDED.uv,
                            manzana = EXCLUDED.manzana,
                            lote = EXCLUDED.lote,
                            superficie_total = EXCLUDED.superficie_total,
                            superficie_construida = EXCLUDED.superficie_construida,
                            num_dormitorios = EXCLUDED.num_dormitorios,
                            num_banos = EXCLUDED.num_banos,
                            num_garajes = EXCLUDED.num_garajes,
                            coordenadas = EXCLUDED.coordenadas,
                            coordenadas_validas = EXCLUDED.coordenadas_validas,
                            datos_completos = EXCLUDED.datos_completos,
                            proveedor_datos = EXCLUDED.proveedor_datos,
                            url_origen = EXCLUDED.url_origen,
                            ultima_actualizacion = NOW()
                        """

                        cursor.execute(insert_query, (
                            prop['titulo'], prop['descripcion'], prop['tipo_propiedad'], prop['estado_propiedad'],
                            prop['precio_usd'], prop['direccion'], prop['zona'], prop['uv'], prop['manzana'], prop['lote'],
                            prop['superficie_total'], prop['superficie_construida'],
                            prop['num_dormitorios'], prop['num_banos'], prop['num_garajes'],
                            coords_postgis, coords_validas, True,  # datos_completos = True (approved)
                            prop['proveedor_datos'], prop['url_origen'], datetime.now()
                        ))

                        total_migrated += 1

                    except Exception as e:
                        self.logger.warning(f"Failed to migrate property: {prop['titulo'][:50]}... - {e}")
                        self.stats['migration_errors'] += 1

                # Commit batch
                self.db_connection.commit()
                self.logger.info(f"Migrated batch {i//batch_size + 1}: {min(batch_size, len(batch))} properties")

            self.stats['properties_migrated'] = total_migrated
            self.logger.info(f"Migration completed: {total_migrated} properties migrated successfully")
            return True

        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
            if self.db_connection:
                self.db_connection.rollback()
            return False

    def run(self) -> bool:
        """Execute the complete approval and migration process"""
        start_time = time.time()
        self.logger.info("Starting data approval and migration process")

        try:
            # Connect to database
            if not self.connect_database():
                return False

            # Load intermediate files
            intermediate_files = self.load_intermediate_files()
            if not intermediate_files:
                self.logger.error("No intermediate files to process")
                return False

            # Process all files and collect approved properties
            all_approved_properties = []
            for file_path in intermediate_files:
                self.stats['total_files_processed'] += 1
                approved_properties = self.process_intermediate_file(file_path)
                all_approved_properties.extend(approved_properties)

            self.logger.info(f"Total approved properties across all files: {len(all_approved_properties)}")

            # Migrate approved properties
            success = self.migrate_approved_properties(all_approved_properties)

            # Calculate execution time
            self.stats['execution_time_ms'] = int((time.time() - start_time) * 1000)

            # Print summary
            self.logger.info("=== Approval and Migration Summary ===")
            self.logger.info(f"Files processed: {self.stats['total_files_processed']}")
            self.logger.info(f"Total properties read: {self.stats['total_properties_read']}")
            self.logger.info(f"Properties approved: {self.stats['properties_approved']}")
            self.logger.info(f"Properties rejected: {self.stats['properties_rejected']}")
            self.logger.info(f"Properties migrated: {self.stats['properties_migrated']}")
            self.logger.info(f"Migration errors: {self.stats['migration_errors']}")
            self.logger.info(f"Approval rate: {self.stats['properties_approved']}/{self.stats['total_properties_read']} ({self.stats['properties_approved']/self.stats['total_properties_read']*100:.1f}%)")
            self.logger.info(f"Execution time: {self.stats['execution_time_ms']}ms")

            return success

        except Exception as e:
            self.logger.error(f"Approval process failed: {e}")
            return False

        finally:
            if self.db_connection:
                self.db_connection.close()
                self.logger.info("Database connection closed")

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Approve intermediate data and migrate to PostgreSQL')
    parser.add_argument('--dry-run', action='store_true', help='Simulate process without database changes')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    approver = DataApprover(dry_run=args.dry_run, verbose=args.verbose)
    success = approver.run()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()