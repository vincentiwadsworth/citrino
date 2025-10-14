#!/usr/bin/env python3
"""
ETL Script 03: Urban Services Migration
========================================

Migra datos de servicios urbanos desde JSON a PostgreSQL con coordenadas PostGIS.
Este script procesa la guía urbana municipal y la migra a la tabla servicios
con soporte geoespacial completo para puntos de interés.

Usage:
    python 03_etl_servicios.py [--dry-run] [--verbose] [--batch-size N]

Dependencies:
    - psycopg2-binary
    - python-dotenv
"""

import json
import sys
import os
import time
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import psycopg2
    from psycopg2 import sql, extras
    from psycopg2.extras import execute_values
except ImportError:
    print("ERROR: psycopg2-binary not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("WARNING: python-dotenv not installed. Using environment variables directly.")
    load_dotenv = lambda: None

# Load environment variables
load_dotenv()

# =====================================================
# Configuration and Setup
# =====================================================

@dataclass
class Service:
    """Data class for urban service information"""
    nombre: str
    tipo_servicio: Optional[str] = None
    subtipo_servicio: Optional[str] = None
    direccion: Optional[str] = None
    zona: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    coordenadas_postgis: Optional[str] = None
    telefono: Optional[str] = None
    horario: Optional[str] = None
    fuente_datos: Optional[str] = None
    fecha_registro: Optional[datetime] = None

    def __post_init__(self):
        # Normalize string fields
        if self.nombre:
            self.nombre = self.nombre.strip()
        if self.tipo_servicio:
            self.tipo_servicio = self.tipo_servicio.strip().lower()
        if self.subtipo_servicio:
            self.subtipo_servicio = self.subtipo_servicio.strip().lower()
        if self.direccion:
            self.direccion = self.direccion.strip()
        if self.zona:
            self.zona = self.zona.strip().title()
        if self.telefono:
            self.telefono = self.telefono.strip()
        if self.horario:
            self.horario = self.horario.strip()

        # Generate PostGIS coordinates if lat/lon available
        if self.latitud is not None and self.longitud is not None:
            self.coordenadas_postgis = f"ST_SetSRID(ST_MakePoint({self.longitud}, {self.latitud}), 4326)::geography"

    def is_valid_coordinates(self) -> bool:
        """Check if coordinates are valid for Santa Cruz de la Sierra area"""
        if self.latitud is None or self.longitud is None:
            return False
        # Santa Cruz de la Sierra approximate bounds
        return (-18.5 <= self.latitud <= -17.5) and (-63.5 <= self.longitud <= -63.0)

class ServiceETL:
    """ETL class for urban services migration"""

    def __init__(self, dry_run: bool = False, verbose: bool = False, batch_size: int = 1000):
        self.dry_run = dry_run
        self.verbose = verbose
        self.batch_size = batch_size
        self.setup_logging()
        self.db_connection = None

        # Data paths
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data"
        self.json_file = self.data_dir / "guia_urbana_municipal_completa.json"

        # Service type mappings for standardization
        self.service_type_mapping = {
            'educación': 'educacion',
            'educacion': 'educacion',
            'escuela': 'educacion',
            'colegio': 'colegio',
            'universidad': 'universidad',
            'academia': 'academia',

            'salud': 'salud',
            'hospital': 'hospital',
            'clínica': 'clinica',
            'clinica': 'clinica',
            'farmacia': 'farmacia',
            'centro de salud': 'centro_de_salud',

            'comercio': 'comercio',
            'supermercado': 'supermercado',
            'tienda': 'tienda',
            'centro comercial': 'centro_comercial',
            'mercado': 'mercado',

            'servicios': 'servicios',
            'banco': 'banco',
            'cajero automático': 'cajero_automatico',
            'oficina': 'oficina',
            'gobierno': 'gobierno',

            'transporte': 'transporte',
            'parada de bus': 'parada_bus',
            'terminal': 'terminal',

            'recreación': 'recreacion',
            'recreacion': 'recreacion',
            'parque': 'parque',
            'plaza': 'plaza',
            'deporte': 'deporte'
        }

        # Statistics
        self.stats = {
            'total_services_processed': 0,
            'valid_coordinates_count': 0,
            'invalid_coordinates_count': 0,
            'services_inserted': 0,
            'services_updated': 0,
            'errors': 0,
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
            connection_params = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': os.getenv('DB_PORT', '5432'),
                'database': os.getenv('DB_NAME', 'citrino'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', 'password')
            }

            if self.dry_run:
                self.logger.info("DRY RUN: Would connect to database with params:")
                self.logger.info(f"  Host: {connection_params['host']}")
                self.logger.info(f"  Database: {connection_params['database']}")
                return True

            self.db_connection = psycopg2.connect(**connection_params)
            self.db_connection.autocommit = False
            self.logger.info("Successfully connected to PostgreSQL database")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            return False

    def extract_services_from_json(self) -> List[Service]:
        """Extract services from JSON file"""
        self.logger.info(f"Processing JSON file: {self.json_file}")

        if not self.json_file.exists():
            raise FileNotFoundError(f"JSON file not found: {self.json_file}")

        with open(self.json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        services = []

        # Handle different JSON structures
        if isinstance(data, list):
            services_data = data
        elif isinstance(data, dict):
            # Try common keys for service lists
            services_data = data.get('servicios', data.get('services', data.get('data', [])))
        else:
            raise ValueError(f"Unexpected JSON structure in {self.json_file}")

        for service_data in services_data:
            try:
                service_obj = self.parse_service_data(service_data)
                if service_obj:
                    services.append(service_obj)
            except Exception as e:
                self.logger.warning(f"Failed to parse service: {e}")
                self.stats['errors'] += 1

        self.stats['total_services_processed'] = len(services)
        self.logger.info(f"Processed {len(services)} services from JSON")

        return services

    def parse_service_data(self, service_data: Dict[str, Any]) -> Optional[Service]:
        """Parse individual service data from JSON"""
        # Extract coordinates
        latitud = None
        longitud = None

        # Try different coordinate field names
        lat_fields = ['latitud', 'lat', 'latitude', 'y']
        lon_fields = ['longitud', 'lon', 'lng', 'longitude', 'x']

        for field in lat_fields:
            if field in service_data and service_data[field] is not None:
                try:
                    latitud = float(service_data[field])
                    break
                except (ValueError, TypeError):
                    continue

        for field in lon_fields:
            if field in service_data and service_data[field] is not None:
                try:
                    longitud = float(service_data[field])
                    break
                except (ValueError, TypeError):
                    continue

        # Extract and standardize service type
        tipo_servicio = None
        subtipo_servicio = None

        # Try different service type fields
        type_fields = ['tipo', 'categoria', 'category', 'tipo_servicio', 'tipo_servicio']
        for field in type_fields:
            if field in service_data and service_data[field]:
                tipo_servicio = self.standardize_service_type(service_data[field])
                break

        # Try subtype fields
        subtype_fields = ['subtipo', 'subcategoria', 'subcategory', 'subtipo_servicio']
        for field in subtype_fields:
            if field in service_data and service_data[field]:
                subtipo_servicio = service_data[field].strip().lower()
                break

        # Parse phone number
        telefono = self.parse_phone_number(service_data.get('telefono'))

        # Parse registration date
        fecha_registro = self.parse_date(service_data.get('fecha_registro'))

        service_obj = Service(
            nombre=service_data.get('nombre', service_data.get('name', 'Servicio sin nombre')),
            tipo_servicio=tipo_servicio,
            subtipo_servicio=subtipo_servicio,
            direccion=service_data.get('direccion', service_data.get('address')),
            zona=service_data.get('zona', service_data.get('zone')),
            latitud=latitud,
            longitud=longitud,
            telefono=telefono,
            horario=service_data.get('horario', service_data.get('schedule')),
            fuente_datos=service_data.get('fuente', service_data.get('source', 'Municipalidad')),
            fecha_registro=fecha_registro or datetime.now()
        )

        # Check coordinate validity
        if service_obj.is_valid_coordinates():
            self.stats['valid_coordinates_count'] += 1
        else:
            self.stats['invalid_coordinates_count'] += 1

        return service_obj

    def standardize_service_type(self, service_type: str) -> str:
        """Standardize service type names"""
        if not service_type:
            return None

        type_normalized = service_type.strip().lower()

        # Remove common prefixes/suffixes and normalize
        type_normalized = re.sub(r['^(el|la|los|las)\s+', '', type_normalized)
        type_normalized = re.sub(r['s$'], '', type_normalized)

        # Apply mapping
        return self.service_type_mapping.get(type_normalized, type_normalized)

    def parse_phone_number(self, phone_value: Any) -> Optional[str]:
        """Parse and normalize phone number"""
        if not phone_value:
            return None

        if isinstance(phone_value, str):
            # Remove common phone formatting
            phone_clean = re.sub(r'[^\d+]', '', phone_value)

            # Validate length for Bolivia phone numbers
            if len(phone_clean) >= 7:
                return phone_clean

        return None

    def parse_date(self, date_value: Any) -> Optional[datetime]:
        """Parse date from various formats"""
        if date_value is None:
            return None

        if isinstance(date_value, datetime):
            return date_value

        if isinstance(date_value, str):
            # Try common date formats
            date_formats = [
                '%Y-%m-%d',
                '%Y-%m-%d %H:%M:%S',
                '%d/%m/%Y',
                '%d/%m/%Y %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%SZ'
            ]

            for fmt in date_formats:
                try:
                    return datetime.strptime(date_value, fmt)
                except ValueError:
                    continue

        return None

    def migrate_services(self, services: List[Service]) -> bool:
        """Migrate services to PostgreSQL in batches"""
        self.logger.info(f"Starting migration of {len(services)} services to PostgreSQL")

        if self.dry_run:
            self.logger.info(f"DRY RUN: Would migrate {len(services)} services")
            # Show sample of first few services
            for i, service in enumerate(services[:3]):
                self.logger.info(f"  {i+1}. {service.nombre} | {service.tipo_servicio} | {service.zona} | Coords: {service.latitud}, {service.longitud}")
            if len(services) > 3:
                self.logger.info(f"  ... and {len(services) - 3} more")
            return True

        try:
            total_inserted = 0
            total_updated = 0

            # Process in batches
            for i in range(0, len(services), self.batch_size):
                batch = services[i:i + self.batch_size]
                batch_inserted, batch_updated = self.migrate_batch(batch)
                total_inserted += batch_inserted
                total_updated += batch_updated

                self.logger.info(f"Processed batch {i//self.batch_size + 1}: {batch_inserted} inserted, {batch_updated} updated")

            self.stats['services_inserted'] = total_inserted
            self.stats['services_updated'] = total_updated

            self.logger.info(f"Migration completed: {total_inserted} inserted, {total_updated} updated")
            return True

        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
            self.stats['errors'] += 1
            return False

    def migrate_batch(self, services: List[Service]) -> Tuple[int, int]:
        """Migrate a batch of services"""
        services_data = []

        for service in services:
            services_data.append((
                service.nombre,
                service.tipo_servicio,
                service.subtipo_servicio,
                service.direccion,
                service.zona,
                service.coordenadas_postgis,
                service.telefono,
                service.horario,
                service.fuente_datos,
                service.fecha_registro,
                service.is_valid_coordinates()
            ))

        with self.db_connection.cursor() as cursor:
            # Use UPSERT based on name and zone (assuming they identify unique services)
            insert_query = """
            INSERT INTO servicios (
                nombre, tipo_servicio, subtipo_servicio, direccion, zona,
                coordenadas, telefono, horario, fuente_datos, fecha_registro, coordenadas_validas
            ) VALUES %s
            ON CONFLICT (nombre, zona) DO UPDATE SET
                tipo_servicio = EXCLUDED.tipo_servicio,
                subtipo_servicio = EXCLUDED.subtipo_servicio,
                direccion = EXCLUDED.direccion,
                coordenadas = EXCLUDED.coordenadas,
                telefono = EXCLUDED.telefono,
                horario = EXCLUDED.horario,
                fuente_datos = EXCLUDED.fuente_datos,
                fecha_registro = EXCLUDED.fecha_registro,
                coordenadas_validas = EXCLUDED.coordenadas_validas
            RETURNING id, CASE WHEN xmin::text::int = 1 THEN 'inserted' ELSE 'updated' END as action
            """

            results = execute_values(cursor, insert_query, services_data, fetch=True)
            self.db_connection.commit()

            # Count inserts vs updates
            inserted = sum(1 for record in results if record[1] == 'inserted')
            updated = sum(1 for record in results if record[1] == 'updated')

            return inserted, updated

    def create_service_type_summary(self):
        """Create a summary of service types in the database"""
        if self.dry_run:
            self.logger.info("DRY RUN: Would create service type summary")
            return

        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        tipo_servicio,
                        COUNT(*) as count,
                        COUNT(CASE WHEN coordenadas_validas = true THEN 1 END) as valid_coords
                    FROM servicios
                    WHERE tipo_servicio IS NOT NULL
                    GROUP BY tipo_servicio
                    ORDER BY count DESC
                """)

                results = cursor.fetchall()
                self.logger.info("=== Service Type Summary ===")
                for tipo_servicio, count, valid_coords in results:
                    percentage = (valid_coords / count * 100) if count > 0 else 0
                    self.logger.info(f"  {tipo_servicio}: {count} services ({percentage:.1f}% with valid coordinates)")

        except Exception as e:
            self.logger.warning(f"Failed to create service type summary: {e}")

    def log_migration_results(self):
        """Log migration results to migration_log table"""
        log_query = """
        INSERT INTO migration_log (
            tabla_migrada, registros_procesados, registros_exitosos,
            registros_errores, execution_time_ms
        ) VALUES (%s, %s, %s, %s, %s)
        """

        if self.dry_run:
            self.logger.info("DRY RUN: Would log migration results")
            return

        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(log_query, (
                    'servicios',
                    self.stats['total_services_processed'],
                    self.stats['services_inserted'] + self.stats['services_updated'],
                    self.stats['errors'],
                    self.stats['execution_time_ms']
                ))
                self.db_connection.commit()
        except Exception as e:
            self.logger.warning(f"Failed to log migration results: {e}")

    def run(self) -> bool:
        """Execute the complete ETL process"""
        start_time = time.time()
        self.logger.info("Starting Urban Services ETL migration")

        try:
            # Connect to database
            if not self.connect_database():
                return False

            # Extract services from JSON
            services = self.extract_services_from_json()

            # Migrate services
            success = self.migrate_services(services)

            if success:
                # Create service type summary
                self.create_service_type_summary()

            # Calculate execution time
            self.stats['execution_time_ms'] = int((time.time() - start_time) * 1000)

            # Log results
            self.log_migration_results()

            # Print summary
            self.logger.info("=== Migration Summary ===")
            self.logger.info(f"Total services processed: {self.stats['total_services_processed']}")
            self.logger.info(f"Valid coordinates: {self.stats['valid_coordinates_count']}")
            self.logger.info(f"Invalid coordinates: {self.stats['invalid_coordinates_count']}")
            self.logger.info(f"Services inserted: {self.stats['services_inserted']}")
            self.logger.info(f"Services updated: {self.stats['services_updated']}")
            self.logger.info(f"Errors: {self.stats['errors']}")
            self.logger.info(f"Execution time: {self.stats['execution_time_ms']}ms")

            return success

        except Exception as e:
            self.logger.error(f"ETL process failed: {e}")
            self.stats['errors'] += 1
            return False

        finally:
            if self.db_connection:
                self.db_connection.close()
                self.logger.info("Database connection closed")

# =====================================================
# Main execution
# =====================================================

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='ETL script for urban services migration')
    parser.add_argument('--dry-run', action='store_true', help='Simulate migration without database changes')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for database operations')

    args = parser.parse_args()

    # Check environment variables for dry run
    if os.getenv('DRY_RUN', 'false').lower() == 'true':
        args.dry_run = True

    etl = ServiceETL(dry_run=args.dry_run, verbose=args.verbose, batch_size=args.batch_size)
    success = etl.run()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()