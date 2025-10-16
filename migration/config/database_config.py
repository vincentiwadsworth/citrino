#!/usr/bin/env python3
"""
Database Configuration for PostgreSQL Migration
===============================================

Centralized configuration management for PostgreSQL connection and migration settings.
This module handles environment variables, connection pooling, and provides a unified
interface for all migration scripts.

Usage:
    from database_config import get_database_config, create_connection, test_connection
"""

import os
import logging
import subprocess
import tempfile
import csv
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

try:
    import psycopg2
    from psycopg2 import pool
    from psycopg2.extras import execute_values
except ImportError:
    print("ERROR: psycopg2-binary not installed. Run: pip install psycopg2-binary")
    raise

try:
    from dotenv import load_dotenv
except ImportError:
    print("WARNING: python-dotenv not installed. Using environment variables directly.")
    load_dotenv = lambda: None

# Load environment variables
load_dotenv()

# =====================================================
# Configuration Data Classes
# =====================================================

@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    host: str
    port: int
    database: str
    user: str
    password: str
    sslmode: str = 'prefer'
    connect_timeout: int = 30
    application_name: str = 'citrino_migration'

    def get_connection_string(self) -> str:
        """Generate PostgreSQL connection string"""
        return (
            f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
            f"?sslmode={self.sslmode}&connect_timeout={self.connect_timeout}"
            f"&application_name={self.application_name}"
        )

    def get_connection_params(self) -> Dict[str, Any]:
        """Get connection parameters for psycopg2.connect()"""
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.user,
            'password': self.password,
            'sslmode': self.sslmode,
            'connect_timeout': self.connect_timeout,
            'application_name': self.application_name
        }

@dataclass
class MigrationConfig:
    """Migration process configuration"""
    batch_size: int = 1000
    max_retries: int = 3
    retry_delay: float = 1.0
    dry_run: bool = False
    verbose: bool = False
    enable_performance_test: bool = False
    backup_before_migration: bool = True

# =====================================================
# Configuration Loading Functions
# =====================================================

def load_database_config() -> DatabaseConfig:
    """Load database configuration from environment variables"""

    # Required configuration
    required_vars = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'citrino'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '')
    }

    # Check for required password
    if not required_vars['password']:
        raise ValueError("DB_PASSWORD environment variable is required")

    # Optional configuration
    optional_vars = {
        'sslmode': os.getenv('DB_SSLMODE', 'prefer'),
        'connect_timeout': int(os.getenv('DB_CONNECT_TIMEOUT', '30')),
        'application_name': os.getenv('DB_APPLICATION_NAME', 'citrino_migration')
    }

    return DatabaseConfig(**required_vars, **optional_vars)

def load_migration_config() -> MigrationConfig:
    """Load migration configuration from environment variables"""

    return MigrationConfig(
        batch_size=int(os.getenv('MIGRATION_BATCH_SIZE', '1000')),
        max_retries=int(os.getenv('MIGRATION_MAX_RETRIES', '3')),
        retry_delay=float(os.getenv('MIGRATION_RETRY_DELAY', '1.0')),
        dry_run=os.getenv('DRY_RUN', 'false').lower() == 'true',
        verbose=os.getenv('VERBOSE', 'false').lower() == 'true',
        enable_performance_test=os.getenv('ENABLE_PERFORMANCE_TEST', 'false').lower() == 'true',
        backup_before_migration=os.getenv('BACKUP_BEFORE_MIGRATION', 'true').lower() == 'true'
    )

# =====================================================
# Docker-based PostgreSQL Connection
# =====================================================

class DockerPostgresConnection:
    """
    PostgreSQL connection wrapper using Docker psql
    Maintains compatibility with psycopg2 interface
    """

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.container_name = 'citrino-postgres-new'
        self._committed = False
        self._closed = False

    def cursor(self):
        """Return a cursor-like object"""
        return DockerPostgresCursor(self, self.config)

    def commit(self):
        """Commit transaction (no-op for Docker wrapper)"""
        self._committed = True
        logging.debug("Transaction committed (Docker wrapper)")

    def rollback(self):
        """Rollback transaction (no-op for Docker wrapper)"""
        logging.debug("Transaction rolled back (Docker wrapper)")

    def close(self):
        """Close connection (no-op for Docker wrapper)"""
        self._closed = True
        logging.debug("Connection closed (Docker wrapper)")

    def autocommit(self, value: bool):
        """Set autocommit mode (no-op for Docker wrapper)"""
        logging.debug(f"Autocommit set to {value} (Docker wrapper)")

class DockerPostgresCursor:
    """
    PostgreSQL cursor wrapper using Docker psql
    Maintains compatibility with psycopg2 cursor interface
    """

    def __init__(self, connection: DockerPostgresConnection, config: DatabaseConfig):
        self.connection = connection
        self.config = config
        self._last_result = None

    def execute(self, query: str, params: Optional[Tuple] = None):
        """Execute SQL query using Docker psql"""
        try:
            # Replace %s parameters with actual values for Docker psql
            if params:
                # Simple parameter substitution - WARNING: only for trusted queries
                formatted_query = query % tuple(f"'{str(p)}'" for p in params)
            else:
                formatted_query = query

            # Build psql command
            cmd = [
                'docker', 'exec', '-i', self.connection.container_name,
                'psql', '-U', self.config.user, '-d', self.config.database,
                '-t', '-A', '-F,', '-c', formatted_query
            ]

            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip()
                logging.error(f"Query failed: {error_msg}")
                raise Exception(f"Docker psql query failed: {error_msg}")

            # Parse result
            self._last_result = self._parse_result(result.stdout.strip())

        except subprocess.TimeoutExpired:
            raise Exception("Query timeout (60s)")
        except Exception as e:
            logging.error(f"Error executing query: {e}")
            raise

    def fetchone(self) -> Optional[Tuple]:
        """Fetch one row from last result"""
        if self._last_result and len(self._last_result) > 0:
            return self._last_result.pop(0)
        return None

    def fetchall(self) -> List[Tuple]:
        """Fetch all rows from last result"""
        if self._last_result:
            result = self._last_result
            self._last_result = []
            return result
        return []

    def fetchmany(self, size: int) -> List[Tuple]:
        """Fetch many rows from last result"""
        if self._last_result:
            result = self._last_result[:size]
            self._last_result = self._last_result[size:]
            return result
        return []

    def rowcount(self) -> int:
        """Return number of rows affected"""
        if self._last_result:
            return len(self._last_result)
        return 0

    def _parse_result(self, output: str) -> List[Tuple]:
        """Parse CSV-like output from psql"""
        if not output.strip():
            return []

        # Split by lines and parse CSV
        lines = output.strip().split('\n')
        result = []

        for line in lines:
            if line.strip():
                # Handle CSV parsing for complex values
                try:
                    reader = csv.reader([line])
                    row = next(reader)
                    result.append(tuple(row))
                except:
                    # Fallback for simple cases
                    row = [col.strip() for col in line.split(',')]
                    result.append(tuple(row))

        return result

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

def docker_connection(config: Optional[DatabaseConfig] = None):
    """Factory function for Docker PostgreSQL connection"""
    if config is None:
        config = load_database_config()

    return DockerPostgresConnection(config)

# =====================================================
# Database Connection Functions
# =====================================================

def create_connection(config: Optional[DatabaseConfig] = None) -> DockerPostgresConnection:
    """Create a single database connection using Docker"""

    if config is None:
        config = load_database_config()

    try:
        # Test Docker container is running
        container_name = 'citrino-postgres-new'
        test_cmd = ['docker', 'exec', container_name, 'pg_isready']
        result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            raise Exception(f"Docker container {container_name} is not ready")

        connection = DockerPostgresConnection(config)
        logging.info(f"Successfully connected to PostgreSQL via Docker: {config.database}")
        return connection
    except Exception as e:
        logging.error(f"Failed to connect to database via Docker: {e}")
        raise

def create_connection_pool(
    config: Optional[DatabaseConfig] = None,
    min_connections: int = 1,
    max_connections: int = 5
) -> psycopg2.pool.ThreadedConnectionPool:
    """Create a connection pool for concurrent operations"""

    if config is None:
        config = load_database_config()

    try:
        pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=min_connections,
            maxconn=max_connections,
            **config.get_connection_params()
        )
        logging.info(f"Created connection pool: {min_connections}-{max_connections} connections")
        return pool
    except Exception as e:
        logging.error(f"Failed to create connection pool: {e}")
        raise

def test_connection(config: Optional[DatabaseConfig] = None) -> bool:
    """Test database connection and basic functionality"""

    if config is None:
        config = load_database_config()

    try:
        conn = create_connection(config)

        with conn.cursor() as cursor:
            # Test basic query
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            logging.info(f"PostgreSQL version: {version}")

            # Test PostGIS extension
            cursor.execute("SELECT PostGIS_Version()")
            postgis_version = cursor.fetchone()[0]
            logging.info(f"PostGIS version: {postgis_version}")

            # Test basic spatial function
            cursor.execute("SELECT ST_Distance(ST_MakePoint(-63.18, -17.78)::geography, ST_MakePoint(-63.19, -17.79)::geography)")
            distance_result = cursor.fetchone()
            if distance_result:
                distance = float(distance_result[0])
                logging.info(f"Test spatial query result: {distance:.2f} meters")
            else:
                logging.warning("No spatial query result")

            conn.close()
            return True

    except Exception as e:
        logging.error(f"Connection test failed: {e}")
        return False

# =====================================================
# Database Setup and Validation Functions
# =====================================================

def validate_database_setup(config: Optional[DatabaseConfig] = None) -> Dict[str, Any]:
    """Validate database setup and return status information"""

    if config is None:
        config = load_database_config()

    validation_results = {
        'connection': False,
        'postgis_enabled': False,
        'required_tables': {},
        'indexes': {},
        'estimated_sizes': {}
    }

    try:
        conn = create_connection(config)

        with conn.cursor() as cursor:
                # Test connection
                cursor.execute("SELECT 1")
                validation_results['connection'] = True

                # Check PostGIS extension
                cursor.execute("""
                    SELECT 1 FROM pg_extension WHERE extname = 'postgis'
                """)
                validation_results['postgis_enabled'] = cursor.fetchone() is not None

                # Check required tables
                required_tables = ['agentes', 'propiedades', 'servicios', 'migration_log']
                for table in required_tables:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_schema = 'public' AND table_name = %s
                        )
                    """, (table,))
                    validation_results['required_tables'][table] = cursor.fetchone()[0]

                # Check indexes (if tables exist)
                if validation_results['required_tables'].get('propiedades'):
                    cursor.execute("""
                        SELECT indexname FROM pg_indexes
                        WHERE tablename = 'propiedades' AND indexname LIKE '%coordenadas%'
                    """)
                    validation_results['indexes']['propiedades_spatial'] = len(cursor.fetchall()) > 0

                if validation_results['required_tables'].get('servicios'):
                    cursor.execute("""
                        SELECT indexname FROM pg_indexes
                        WHERE tablename = 'servicios' AND indexname LIKE '%coordenadas%'
                    """)
                    validation_results['indexes']['servicios_spatial'] = len(cursor.fetchall()) > 0

                # Get estimated table sizes
                for table in required_tables:
                    if validation_results['required_tables'].get(table):
                        try:
                            cursor.execute(f"""
                                SELECT pg_size_pretty(pg_total_relation_size('{table}')) as size
                            """)
                            size = cursor.fetchone()[0]
                            validation_results['estimated_sizes'][table] = size
                        except Exception:
                            validation_results['estimated_sizes'][table] = 'Unknown'

        conn.close()

    except Exception as e:
        logging.error(f"Database validation failed: {e}")
        validation_results['error'] = str(e)

    return validation_results

def setup_database_logging(config: Optional[DatabaseConfig] = None) -> bool:
    """Configure database logging for migration monitoring"""

    if config is None:
        config = load_database_config()

    try:
        with create_connection(config) as conn:
            with conn.cursor() as cursor:
                # Enable statement logging (optional, for debugging)
                cursor.execute("SET log_statement = 'mod'")  # Log modification statements
                cursor.execute("SET log_min_duration_statement = '1000'")  # Log queries > 1s
                conn.commit()
                return True

    except Exception as e:
        logging.warning(f"Failed to setup database logging: {e}")
        return False

# =====================================================
# Migration Utility Functions
# =====================================================

def create_migration_backup(config: Optional[DatabaseConfig] = None) -> bool:
    """Create a backup of existing data before migration (if tables exist)"""

    if config is None:
        config = load_database_config()

    try:
        with create_connection(config) as conn:
            with conn.cursor() as cursor:
                # Check if tables already exist
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name IN ('agentes', 'propiedades', 'servicios')
                """)
                existing_tables = [row[0] for row in cursor.fetchall()]

                if not existing_tables:
                    logging.info("No existing tables found - no backup needed")
                    return True

                # Create backup tables with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_suffix = f"_backup_{timestamp}"

                for table in existing_tables:
                    backup_table = table + backup_suffix
                    cursor.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM {table}")
                    logging.info(f"Created backup table: {backup_table}")

                conn.commit()
                logging.info(f"Backup completed for tables: {', '.join(existing_tables)}")
                return True

    except Exception as e:
        logging.error(f"Failed to create backup: {e}")
        return False

def get_migration_status(config: Optional[DatabaseConfig] = None) -> Dict[str, Any]:
    """Get current migration status from migration_log"""

    if config is None:
        config = load_database_config()

    status = {
        'migrations_completed': [],
        'total_records_migrated': 0,
        'last_migration_time': None,
        'errors_count': 0
    }

    try:
        with create_connection(config) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT tabla_migrada, fecha_ejecucion, registros_procesados,
                           registros_exitosos, registros_errores, execution_time_ms
                    FROM migration_log
                    ORDER BY fecha_ejecucion DESC
                """)
                records = cursor.fetchall()

                for record in records:
                    table, fecha, procesados, exitosos, errores, tiempo = record
                    status['migrations_completed'].append({
                        'table': table,
                        'timestamp': fecha,
                        'processed': procesados,
                        'successful': exitosos,
                        'errors': errores,
                        'execution_time_ms': tiempo
                    })
                    status['total_records_migrated'] += exitosos
                    status['errors_count'] += errores

                if status['migrations_completed']:
                    status['last_migration_time'] = status['migrations_completed'][0]['timestamp']

    except Exception as e:
        logging.warning(f"Failed to get migration status: {e}")

    return status

# =====================================================
# Environment Setup and Validation
# =====================================================

def validate_environment() -> bool:
    """Validate that all required environment variables are set"""

    required_vars = [
        'DB_HOST',
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD'
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("ERROR: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease set these variables in your .env file or environment.")
        return False

    return True

def print_configuration_info(config: Optional[DatabaseConfig] = None):
    """Print current configuration information (without sensitive data)"""

    if config is None:
        config = load_database_config()

    print("=== Database Configuration ===")
    print(f"Host: {config.host}")
    print(f"Port: {config.port}")
    print(f"Database: {config.database}")
    print(f"User: {config.user}")
    print(f"SSL Mode: {config.sslmode}")
    print(f"Application Name: {config.application_name}")
    print("=" * 30)

def setup_logging(verbose: bool = False):
    """Setup logging configuration"""

    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

# =====================================================
# Main Execution for Testing
# =====================================================

def main():
    """Main function for testing database configuration"""
    import argparse

    parser = argparse.ArgumentParser(description='Test database configuration')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--test-connection', action='store_true', help='Test database connection')
    parser.add_argument('--validate-setup', action='store_true', help='Validate database setup')
    parser.add_argument('--migration-status', action='store_true', help='Show migration status')

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Validate environment
    if not validate_environment():
        return 1

    try:
        # Load configuration
        db_config = load_database_config()
        migration_config = load_migration_config()

        print_configuration_info(db_config)

        if args.test_connection:
            print("\nTesting connection...")
            success = test_connection(db_config)
            print(f"Connection test: {'PASSED' if success else 'FAILED'}")

        if args.validate_setup:
            print("\nValidating database setup...")
            validation = validate_database_setup(db_config)
            print("Validation Results:")
            for key, value in validation.items():
                print(f"  {key}: {value}")

        if args.migration_status:
            print("\nMigration status:")
            status = get_migration_status(db_config)
            print(f"  Tables migrated: {len(status['migrations_completed'])}")
            print(f"  Total records: {status['total_records_migrated']}")
            print(f"  Errors: {status['errors_count']}")
            if status['last_migration_time']:
                print(f"  Last migration: {status['last_migration_time']}")

        return 0

    except Exception as e:
        logging.error(f"Configuration test failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())