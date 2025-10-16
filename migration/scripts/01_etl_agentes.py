#!/usr/bin/env python3
"""
ETL Script 01: Agentes Migration
================================

Migra datos de agentes desde archivos JSON a PostgreSQL con deduplicación.
Este script procesa los datos de agentes del JSON principal y los normaliza
en la tabla agentes de PostgreSQL.

Usage:
    python 01_etl_agentes.py [--dry-run] [--verbose]

Dependencies:
    - psycopg2-binary
    - python-dotenv
"""

import json
import sys
import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    sys.path.append(str(Path(__file__).parent.parent / 'config'))
    from database_config import create_connection
    # Use custom execute_values function for Docker compatibility
    def execute_values(cursor, query, data, fetch=False):
        """Custom execute_values function for Docker wrapper"""
        if not data:
            return []

        # Split query to get the base INSERT part
        base_query = query.split('VALUES')[0] + 'VALUES '

        # Execute individual INSERT statements (slower but compatible)
        results = []
        for row in data:
            # Escape single quotes in data
            escaped_row = []
            for item in row:
                if item is None:
                    escaped_row.append('NULL')
                elif isinstance(item, str):
                    escaped_row.append("'" + item.replace("'", "''") + "'")
                else:
                    escaped_row.append(str(item))

            single_query = base_query + '(' + ', '.join(escaped_row) + ')'
            single_query += '''
                ON CONFLICT (nombre)
                DO UPDATE SET
                    telefono = EXCLUDED.telefono,
                    email = EXCLUDED.email,
                    empresa = EXCLUDED.empresa
                RETURNING id, CASE WHEN xmin::text::int = 1 THEN 'inserted' ELSE 'updated' END as action
            '''

            cursor.execute(single_query)
            if fetch:
                result = cursor.fetchone()
                if result:
                    results.append(result)

        return results

except ImportError:
    print("ERROR: database_config module not found")
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
class Agent:
    """Data class for agent information"""
    nombre: str
    telefono: Optional[str] = None
    email: Optional[str] = None
    empresa: Optional[str] = None

    def __post_init__(self):
        # Normalize name for consistency
        self.nombre = self.nombre.strip().title()
        if self.telefono:
            self.telefono = self.telefono.strip()
        if self.email:
            self.email = self.email.strip().lower()
        if self.empresa:
            self.empresa = self.empresa.strip().title()

class AgentETL:
    """ETL class for agent migration"""

    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.setup_logging()
        self.db_connection = None

        # Data paths
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data"
        self.json_file = self.data_dir / "base_datos_relevamiento.json"

        # Statistics
        self.stats = {
            'total_properties_processed': 0,
            'unique_agents_found': 0,
            'agents_inserted': 0,
            'agents_updated': 0,
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
        """Establish connection to PostgreSQL database using Docker"""
        try:
            if self.dry_run:
                self.logger.info("DRY RUN: Would connect to database via Docker")
                self.logger.info(f"  Database: {os.getenv('DB_NAME', 'citrino')}")
                return True

            self.db_connection = create_connection()
            self.logger.info("Successfully connected to PostgreSQL database via Docker")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to database via Docker: {e}")
            return False

    def extract_agents_from_json(self) -> Dict[str, Agent]:
        """Extract unique agents from JSON file"""
        self.logger.info(f"Processing JSON file: {self.json_file}")

        if not self.json_file.exists():
            raise FileNotFoundError(f"JSON file not found: {self.json_file}")

        with open(self.json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        agents_dict = {}

        for property_data in data.get('propiedades', []):
            self.stats['total_properties_processed'] += 1

            # Extract agent information if available
            agent_info = property_data.get('agente')
            if not agent_info:
                continue

            # Handle different agent data formats
            if isinstance(agent_info, str):
                agent = Agent(nombre=agent_info)
            elif isinstance(agent_info, dict):
                agent = Agent(
                    nombre=agent_info.get('nombre', 'Desconocido'),
                    telefono=agent_info.get('telefono'),
                    email=agent_info.get('email'),
                    empresa=agent_info.get('empresa')
                )
            else:
                continue

            # Use normalized name as key for deduplication
            key = agent.nombre
            if key not in agents_dict:
                agents_dict[key] = agent
            else:
                # Merge information if we have more complete data
                existing = agents_dict[key]
                if not existing.telefono and agent.telefono:
                    existing.telefono = agent.telefono
                if not existing.email and agent.email:
                    existing.email = agent.email
                if not existing.empresa and agent.empresa:
                    existing.empresa = agent.empresa

        self.stats['unique_agents_found'] = len(agents_dict)
        self.logger.info(f"Found {len(agents_dict)} unique agents from {self.stats['total_properties_processed']} properties")

        return agents_dict

    def create_agents_table(self):
        """Create agents table if it doesn't exist"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS agentes (
            id BIGSERIAL PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            telefono VARCHAR(50),
            email VARCHAR(255) UNIQUE,
            empresa VARCHAR(100),
            fecha_registro TIMESTAMPTZ DEFAULT now(),
            CONSTRAINT uq_agente_nombre UNIQUE (nombre)
        );
        """

        if self.dry_run:
            self.logger.info("DRY RUN: Would create agents table")
            return

        with self.db_connection.cursor() as cursor:
            cursor.execute(create_table_sql)
            self.db_connection.commit()
            self.logger.info("Agents table verified/created")

    def migrate_agents(self, agents_dict: Dict[str, Agent]) -> bool:
        """Migrate agents to PostgreSQL with deduplication"""
        self.logger.info("Starting agent migration to PostgreSQL")

        if self.dry_run:
            self.logger.info(f"DRY RUN: Would migrate {len(agents_dict)} agents:")
            for agent in list(agents_dict.values())[:5]:  # Show first 5
                self.logger.info(f"  - {agent.nombre} | {agent.telefono} | {agent.email}")
            if len(agents_dict) > 5:
                self.logger.info(f"  ... and {len(agents_dict) - 5} more")
            return True

        try:
            with self.db_connection.cursor() as cursor:
                # Prepare data for insertion
                agents_data = []
                for agent in agents_dict.values():
                    agents_data.append((
                        agent.nombre,
                        agent.telefono,
                        agent.email,
                        agent.empresa
                    ))

                # Use INSERT ... ON CONFLICT for upsert behavior
                insert_query = """
                INSERT INTO agentes (nombre, telefono, email, empresa)
                VALUES %s
                ON CONFLICT (nombre)
                DO UPDATE SET
                    telefono = EXCLUDED.telefono,
                    email = EXCLUDED.email,
                    empresa = EXCLUDED.empresa
                RETURNING id, CASE WHEN xmin::text::int = 1 THEN 'inserted' ELSE 'updated' END as action
                """

                results = execute_values(
                    cursor,
                    insert_query,
                    agents_data,
                    fetch=True
                )

                # Count inserts vs updates
                for record in results:
                    if record[1] == 'inserted':
                        self.stats['agents_inserted'] += 1
                    else:
                        self.stats['agents_updated'] += 1

                self.db_connection.commit()
                self.logger.info(f"Migration completed: {self.stats['agents_inserted']} inserted, {self.stats['agents_updated']} updated")

                return True

        except Exception as e:
            self.db_connection.rollback()
            self.logger.error(f"Migration failed: {e}")
            self.stats['errors'] += 1
            return False

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
                    'agentes',
                    self.stats['unique_agents_found'],
                    self.stats['agents_inserted'] + self.stats['agents_updated'],
                    self.stats['errors'],
                    self.stats['execution_time_ms']
                ))
                self.db_connection.commit()
        except Exception as e:
            self.logger.warning(f"Failed to log migration results: {e}")

    def run(self) -> bool:
        """Execute the complete ETL process"""
        start_time = time.time()
        self.logger.info("Starting Agent ETL migration")

        try:
            # Connect to database
            if not self.connect_database():
                return False

            # Extract agents from JSON
            agents_dict = self.extract_agents_from_json()

            # Create table if needed
            self.create_agents_table()

            # Migrate agents
            success = self.migrate_agents(agents_dict)

            # Calculate execution time
            self.stats['execution_time_ms'] = int((time.time() - start_time) * 1000)

            # Log results
            self.log_migration_results()

            # Print summary
            self.logger.info("=== Migration Summary ===")
            self.logger.info(f"Properties processed: {self.stats['total_properties_processed']}")
            self.logger.info(f"Unique agents found: {self.stats['unique_agents_found']}")
            self.logger.info(f"Agents inserted: {self.stats['agents_inserted']}")
            self.logger.info(f"Agents updated: {self.stats['agents_updated']}")
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

    parser = argparse.ArgumentParser(description='ETL script for agent migration')
    parser.add_argument('--dry-run', action='store_true', help='Simulate migration without database changes')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    # Check environment variables for dry run
    if os.getenv('DRY_RUN', 'false').lower() == 'true':
        args.dry_run = True

    etl = AgentETL(dry_run=args.dry_run, verbose=args.verbose)
    success = etl.run()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()