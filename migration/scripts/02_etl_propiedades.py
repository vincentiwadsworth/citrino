#!/usr/bin/env python3
"""
ETL Script 02: Properties Migration
====================================

Migra datos de propiedades desde JSON a PostgreSQL con coordenadas PostGIS.
Este script procesa las propiedades del JSON principal y las migra a la tabla
propiedades con soporte geoespacial completo.

Usage:
    python 02_etl_propiedades.py [--dry-run] [--verbose] [--batch-size N]

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
class Property:
    """Data class for property information"""
    titulo: str
    agente_id: Optional[int]
    descripcion: Optional[str] = None
    tipo_propiedad: Optional[str] = None
    estado_propiedad: Optional[str] = None
    precio_usd: Optional[float] = None
    precio_usd_m2: Optional[float] = None
    direccion: Optional[str] = None
    zona: Optional[str] = None
    uv: Optional[str] = None
    manzana: Optional[str] = None
    lote: Optional[str] = None
    superficie_total: Optional[float] = None
    superficie_construida: Optional[float] = None
    num_dormitorios: Optional[int] = None
    num_banos: Optional[int] = None
    num_garajes: Optional[int] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    coordenadas_postgis: Optional[str] = None
    fecha_publicacion: Optional[datetime] = None
    fecha_scraping: Optional[datetime] = None
    proveedor_datos: Optional[str] = None
    codigo_proveedor: Optional[str] = None
    url_origen: Optional[str] = None

    def __post_init__(self):
        # Normalize string fields
        if self.titulo:
            self.titulo = self.titulo.strip()
        if self.descripcion:
            self.descripcion = self.descripcion.strip()
        if self.tipo_propiedad:
            self.tipo_propiedad = self.tipo_propiedad.strip().lower()
        if self.estado_propiedad:
            self.estado_propiedad = self.estado_propiedad.strip().lower()
        if self.direccion:
            self.direccion = self.direccion.strip()
        if self.zona:
            self.zona = self.zona.strip().title()
        if self.uv:
            self.uv = self.uv.strip().upper()
        if self.manzana:
            self.manzana = self.manzana.strip().upper()
        if self.lote:
            self.lote = self.lote.strip().upper()

        # Generate PostGIS coordinates if lat/lon available
        if self.latitud is not None and self.longitud is not None:
            self.coordenadas_postgis = f"ST_SetSRID(ST_MakePoint({self.longitud}, {self.latitud}), 4326)::geography"

    def is_valid_coordinates(self) -> bool:
        """Check if coordinates are valid for Santa Cruz de la Sierra area"""
        if self.latitud is None or self.longitud is None:
            return False
        # Santa Cruz de la Sierra approximate bounds
        return (-18.5 <= self.latitud <= -17.5) and (-63.5 <= self.longitud <= -63.0)

class PropertyETL:
    """ETL class for property migration"""

    def __init__(self, dry_run: bool = False, verbose: bool = False, batch_size: int = 1000):
        self.dry_run = dry_run
        self.verbose = verbose
        self.batch_size = batch_size
        self.setup_logging()
        self.db_connection = None

        # Data paths
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data"
        self.json_file = self.data_dir / "base_datos_relevamiento.json"

        # Agent name to ID mapping (cached)
        self.agent_name_to_id = {}

        # Statistics
        self.stats = {
            'total_properties_processed': 0,
            'valid_coordinates_count': 0,
            'properties_inserted': 0,
            'properties_updated': 0,
            'invalid_coordinates_count': 0,
            'missing_agents_count': 0,
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

    def load_agent_mapping(self):
        """Load agent name to ID mapping from database"""
        self.logger.info("Loading agent mapping from database")

        if self.dry_run:
            self.logger.info("DRY RUN: Would load agent mapping")
            return

        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute("SELECT id, nombre FROM agentes")
                for agent_id, agent_name in cursor.fetchall():
                    # Normalize for consistent matching
                    normalized_name = agent_name.strip().title()
                    self.agent_name_to_id[normalized_name] = agent_id

                self.logger.info(f"Loaded {len(self.agent_name_to_id)} agents from database")

        except Exception as e:
            self.logger.error(f"Failed to load agent mapping: {e}")

    def extract_properties_from_json(self) -> List[Property]:
        """Extract properties from JSON file"""
        self.logger.info(f"Processing JSON file: {self.json_file}")

        if not self.json_file.exists():
            raise FileNotFoundError(f"JSON file not found: {self.json_file}")

        with open(self.json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        properties = []

        for property_data in data:
            try:
                property_obj = self.parse_property_data(property_data)
                if property_obj:
                    properties.append(property_obj)
            except Exception as e:
                self.logger.warning(f"Failed to parse property: {e}")
                self.stats['errors'] += 1

        self.stats['total_properties_processed'] = len(properties)
        self.logger.info(f"Processed {len(properties)} properties from JSON")

        return properties

    def parse_property_data(self, property_data: Dict[str, Any]) -> Optional[Property]:
        """Parse individual property data from JSON"""
        # Extract agent information
        agent_info = property_data.get('agente')
        agente_id = None

        if agent_info:
            if isinstance(agent_info, str):
                agent_name = agent_info.strip().title()
                agente_id = self.agent_name_to_id.get(agent_name)
            elif isinstance(agent_info, dict):
                agent_name = agent_info.get('nombre', '').strip().title()
                agente_id = self.agent_name_to_id.get(agent_name)

        if not agente_id and agent_info:
            self.stats['missing_agents_count'] += 1

        # Extract coordinates
        latitud = None
        longitud = None

        # Try different coordinate field names
        lat_fields = ['latitud', 'lat', 'latitude']
        lon_fields = ['longitud', 'lon', 'lng', 'longitude']

        for field in lat_fields:
            if field in property_data and property_data[field] is not None:
                try:
                    latitud = float(property_data[field])
                    break
                except (ValueError, TypeError):
                    continue

        for field in lon_fields:
            if field in property_data and property_data[field] is not None:
                try:
                    longitud = float(property_data[field])
                    break
                except (ValueError, TypeError):
                    continue

        # Extract and parse price
        precio_usd = None
        precio_fields = ['precio', 'precio_usd', 'price', 'precio_usd']

        for field in precio_fields:
            if field in property_data and property_data[field] is not None:
                precio_usd = self.parse_price(property_data[field])
                if precio_usd is not None:
                    break

        # Parse numeric fields
        superficie_total = self.parse_numeric_field(property_data.get('superficie_total'))
        superficie_construida = self.parse_numeric_field(property_data.get('superficie_construida'))
        num_dormitorios = self.parse_numeric_field(property_data.get('num_dormitorios'), integer=True)
        num_banos = self.parse_numeric_field(property_data.get('num_banos'), integer=True)
        num_garajes = self.parse_numeric_field(property_data.get('num_garajes'), integer=True)

        # Parse dates
        fecha_publicacion = self.parse_date(property_data.get('fecha_publicacion'))
        fecha_scraping = self.parse_date(property_data.get('fecha_scraping'))

        property_obj = Property(
            titulo=property_data.get('titulo', 'Sin título'),
            agente_id=agente_id,
            descripcion=property_data.get('descripcion'),
            tipo_propiedad=property_data.get('tipo_propiedad'),
            estado_propiedad=property_data.get('estado_propiedad'),
            precio_usd=precio_usd,
            direccion=property_data.get('direccion'),
            zona=property_data.get('zona'),
            uv=property_data.get('uv'),
            manzana=property_data.get('manzana'),
            lote=property_data.get('lote'),
            superficie_total=superficie_total,
            superficie_construida=superficie_construida,
            num_dormitorios=num_dormitorios,
            num_banos=num_banos,
            num_garajes=num_garajes,
            latitud=latitud,
            longitud=longitud,
            fecha_publicacion=fecha_publicacion,
            fecha_scraping=fecha_scraping,
            proveedor_datos=property_data.get('proveedor_datos'),
            codigo_proveedor=property_data.get('codigo_proveedor'),
            url_origen=property_data.get('url_origen')
        )

        # Check coordinate validity
        if property_obj.is_valid_coordinates():
            self.stats['valid_coordinates_count'] += 1
        else:
            self.stats['invalid_coordinates_count'] += 1

        return property_obj

    def parse_price(self, price_value: Any) -> Optional[float]:
        """Parse price from various formats"""
        if price_value is None:
            return None

        if isinstance(price_value, (int, float)):
            return float(price_value)

        if isinstance(price_value, str):
            # Remove common price formatting
            price_str = re.sub(r'[^\d.,]', '', price_value)
            price_str = price_str.replace(',', '.')

            try:
                return float(price_str)
            except ValueError:
                return None

        return None

    def parse_numeric_field(self, value: Any, integer: bool = False) -> Optional[float]:
        """Parse numeric field from various formats"""
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return int(value) if integer else float(value)

        if isinstance(value, str):
            # Remove formatting characters
            num_str = re.sub(r'[^\d.,-]', '', value)
            num_str = num_str.replace(',', '.')

            try:
                num_val = float(num_str)
                return int(num_val) if integer else num_val
            except ValueError:
                return None

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

    def migrate_properties(self, properties: List[Property]) -> bool:
        """Migrate properties to PostgreSQL in batches"""
        self.logger.info(f"Starting migration of {len(properties)} properties to PostgreSQL")

        if self.dry_run:
            self.logger.info(f"DRY RUN: Would migrate {len(properties)} properties")
            # Show sample of first few properties
            for i, prop in enumerate(properties[:3]):
                self.logger.info(f"  {i+1}. {prop.titulo} | {prop.zona} | ${prop.precio_usd} | Coords: {prop.latitud}, {prop.longitud}")
            if len(properties) > 3:
                self.logger.info(f"  ... and {len(properties) - 3} more")
            return True

        try:
            total_inserted = 0
            total_updated = 0

            # Process in batches
            for i in range(0, len(properties), self.batch_size):
                batch = properties[i:i + self.batch_size]
                batch_inserted, batch_updated = self.migrate_batch(batch)
                total_inserted += batch_inserted
                total_updated += batch_updated

                self.logger.info(f"Processed batch {i//self.batch_size + 1}: {batch_inserted} inserted, {batch_updated} updated")

            self.stats['properties_inserted'] = total_inserted
            self.stats['properties_updated'] = total_updated

            self.logger.info(f"Migration completed: {total_inserted} inserted, {total_updated} updated")
            return True

        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
            self.stats['errors'] += 1
            return False

    def migrate_batch(self, properties: List[Property]) -> Tuple[int, int]:
        """Migrate a batch of properties"""
        properties_data = []

        for prop in properties:
            properties_data.append((
                prop.agente_id,
                prop.titulo,
                prop.descripcion,
                prop.tipo_propiedad,
                prop.estado_propiedad,
                prop.precio_usd,
                prop.precio_usd_m2,
                prop.direccion,
                prop.zona,
                prop.uv,
                prop.manzana,
                prop.lote,
                prop.superficie_total,
                prop.superficie_construida,
                prop.num_dormitorios,
                prop.num_banos,
                prop.num_garajes,
                prop.coordenadas_postgis,
                prop.fecha_publicacion,
                prop.fecha_scraping,
                prop.proveedor_datos,
                prop.codigo_proveedor,
                prop.url_origen,
                prop.is_valid_coordinates(),
                bool(prop.precio_usd and prop.zona and prop.tipo_propiedad)
            ))

        with self.db_connection.cursor() as cursor:
            # Use UPSERT based on title and zone (assuming they identify unique properties)
            insert_query = """
            INSERT INTO propiedades (
                agente_id, titulo, descripcion, tipo_propiedad, estado_propiedad,
                precio_usd, precio_usd_m2, direccion, zona, uv, manzana, lote,
                superficie_total, superficie_construida, num_dormitorios, num_banos,
                num_garajes, coordenadas, fecha_publicacion, fecha_scraping,
                proveedor_datos, codigo_proveedor, url_origen, coordenadas_validas, datos_completos
            ) VALUES %s
            ON CONFLICT (titulo, zona) DO UPDATE SET
                agente_id = EXCLUDED.agente_id,
                descripcion = EXCLUDED.descripcion,
                estado_propiedad = EXCLUDED.estado_propiedad,
                precio_usd = EXCLUDED.precio_usd,
                precio_usd_m2 = EXCLUDED.precio_usd_m2,
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
                fecha_publicacion = EXCLUDED.fecha_publicacion,
                fecha_scraping = EXCLUDED.fecha_scraping,
                proveedor_datos = EXCLUDED.proveedor_datos,
                codigo_proveedor = EXCLUDED.codigo_proveedor,
                url_origen = EXCLUDED.url_origen,
                coordenadas_validas = EXCLUDED.coordenadas_validas,
                datos_completos = EXCLUDED.datos_completos,
                ultima_actualizacion = now()
            RETURNING id, CASE WHEN xmin::text::int = 1 THEN 'inserted' ELSE 'updated' END as action
            """

            results = execute_values(cursor, insert_query, properties_data, fetch=True)
            self.db_connection.commit()

            # Count inserts vs updates
            inserted = sum(1 for record in results if record[1] == 'inserted')
            updated = sum(1 for record in results if record[1] == 'updated')

            return inserted, updated

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
                    'propiedades',
                    self.stats['total_properties_processed'],
                    self.stats['properties_inserted'] + self.stats['properties_updated'],
                    self.stats['errors'],
                    self.stats['execution_time_ms']
                ))
                self.db_connection.commit()
        except Exception as e:
            self.logger.warning(f"Failed to log migration results: {e}")

    def run(self) -> bool:
        """Execute the complete ETL process"""
        start_time = time.time()
        self.logger.info("Starting Property ETL migration")

        try:
            # Connect to database
            if not self.connect_database():
                return False

            # Load agent mapping
            self.load_agent_mapping()

            # Extract properties from JSON
            properties = self.extract_properties_from_json()

            # Migrate properties
            success = self.migrate_properties(properties)

            # Calculate execution time
            self.stats['execution_time_ms'] = int((time.time() - start_time) * 1000)

            # Log results
            self.log_migration_results()

            # Print summary
            self.logger.info("=== Migration Summary ===")
            self.logger.info(f"Total properties processed: {self.stats['total_properties_processed']}")
            self.logger.info(f"Valid coordinates: {self.stats['valid_coordinates_count']}")
            self.logger.info(f"Invalid coordinates: {self.stats['invalid_coordinates_count']}")
            self.logger.info(f"Properties inserted: {self.stats['properties_inserted']}")
            self.logger.info(f"Properties updated: {self.stats['properties_updated']}")
            self.logger.info(f"Missing agents: {self.stats['missing_agents_count']}")
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

    parser = argparse.ArgumentParser(description='ETL script for property migration')
    parser.add_argument('--dry-run', action='store_true', help='Simulate migration without database changes')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for database operations')

    args = parser.parse_args()

    # Check environment variables for dry run
    if os.getenv('DRY_RUN', 'false').lower() == 'true':
        args.dry_run = True

    etl = PropertyETL(dry_run=args.dry_run, verbose=args.verbose, batch_size=args.batch_size)
    success = etl.run()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()