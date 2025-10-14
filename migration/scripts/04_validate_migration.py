#!/usr/bin/env python3
"""
Migration Validation Script
===========================

Validates the complete migration from JSON to PostgreSQL + PostGIS.
This script performs comprehensive checks to ensure data integrity,
coordinate validity, and performance improvements.

Usage:
    python 04_validate_migration.py [--verbose] [--performance-test]

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
from typing import Dict, List, Tuple, Optional
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
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

class MigrationValidator:
    """Comprehensive migration validation tool"""

    def __init__(self, verbose: bool = False, performance_test: bool = False):
        self.verbose = verbose
        self.performance_test = performance_test
        self.setup_logging()
        self.db_connection = None

        # Data paths
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data"
        self.properties_json = self.data_dir / "base_datos_relevamiento.json"
        self.services_json = self.data_dir / "guia_urbana_municipal_completa.json"

        # Validation results
        self.validation_results = {
            'data_integrity': {},
            'coordinate_validation': {},
            'performance_metrics': {},
            'relationship_validation': {},
            'errors': []
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

            self.db_connection = psycopg2.connect(**connection_params)
            self.logger.info("Successfully connected to PostgreSQL database")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            return False

    def load_json_data(self) -> Dict[str, any]:
        """Load original JSON data for comparison"""
        self.logger.info("Loading original JSON data")

        data = {}

        try:
            # Load properties
            if self.properties_json.exists():
                with open(self.properties_json, 'r', encoding='utf-8') as f:
                    data['properties'] = json.load(f)
                self.logger.info(f"Loaded {len(data['properties'])} properties from JSON")
            else:
                self.logger.warning(f"Properties JSON file not found: {self.properties_json}")

            # Load services
            if self.services_json.exists():
                with open(self.services_json, 'r', encoding='utf-8') as f:
                    services_data = json.load(f)
                # Handle different JSON structures
                if isinstance(services_data, list):
                    data['services'] = services_data
                elif isinstance(services_data, dict):
                    data['services'] = services_data.get('servicios', services_data.get('services', []))
                else:
                    data['services'] = []

                self.logger.info(f"Loaded {len(data['services'])} services from JSON")
            else:
                self.logger.warning(f"Services JSON file not found: {self.services_json}")

            return data

        except Exception as e:
            self.logger.error(f"Failed to load JSON data: {e}")
            return {}

    def validate_data_integrity(self, json_data: Dict[str, any]) -> bool:
        """Validate data integrity between JSON and PostgreSQL"""
        self.logger.info("=== Validating Data Integrity ===")

        success = True

        try:
            with self.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:

                # Validate properties count
                if 'properties' in json_data:
                    json_properties_count = len(json_data['properties'])
                    cursor.execute("SELECT COUNT(*) as count FROM propiedades")
                    pg_properties_count = cursor.fetchone()['count']

                    self.validation_results['data_integrity']['properties'] = {
                        'json_count': json_properties_count,
                        'postgresql_count': pg_properties_count,
                        'match': json_properties_count == pg_properties_count
                    }

                    if json_properties_count != pg_properties_count:
                        self.logger.error(f"Properties count mismatch: JSON={json_properties_count}, PG={pg_properties_count}")
                        success = False
                    else:
                        self.logger.info(f"Properties count validated: {json_properties_count}")

                # Validate services count
                if 'services' in json_data:
                    json_services_count = len(json_data['services'])
                    cursor.execute("SELECT COUNT(*) as count FROM servicios")
                    pg_services_count = cursor.fetchone()['count']

                    self.validation_results['data_integrity']['services'] = {
                        'json_count': json_services_count,
                        'postgresql_count': pg_services_count,
                        'match': json_services_count == pg_services_count
                    }

                    if json_services_count != pg_services_count:
                        self.logger.error(f"Services count mismatch: JSON={json_services_count}, PG={pg_services_count}")
                        success = False
                    else:
                        self.logger.info(f"Services count validated: {json_services_count}")

                # Validate agents count
                cursor.execute("SELECT COUNT(*) as count FROM agentes")
                pg_agents_count = cursor.fetchone()['count']
                self.validation_results['data_integrity']['agents'] = {
                    'postgresql_count': pg_agents_count
                }
                self.logger.info(f"Agents count: {pg_agents_count}")

                # Check for duplicate properties
                cursor.execute("""
                    SELECT titulo, zona, COUNT(*) as count
                    FROM propiedades
                    GROUP BY titulo, zona
                    HAVING COUNT(*) > 1
                """)
                duplicates = cursor.fetchall()
                self.validation_results['data_integrity']['property_duplicates'] = len(duplicates)

                if duplicates:
                    self.logger.warning(f"Found {len(duplicates)} duplicate property combinations")
                    for dup in duplicates[:5]:  # Show first 5
                        self.logger.warning(f"  Duplicate: {dup['titulo']} in {dup['zona']} ({dup['count']} times)")

                # Check for duplicate services
                cursor.execute("""
                    SELECT nombre, zona, COUNT(*) as count
                    FROM servicios
                    GROUP BY nombre, zona
                    HAVING COUNT(*) > 1
                """)
                service_duplicates = cursor.fetchall()
                self.validation_results['data_integrity']['service_duplicates'] = len(service_duplicates)

                if service_duplicates:
                    self.logger.warning(f"Found {len(service_duplicates)} duplicate service combinations")

                return success

        except Exception as e:
            self.logger.error(f"Data integrity validation failed: {e}")
            return False

    def validate_coordinates(self) -> bool:
        """Validate coordinate data and spatial integrity"""
        self.logger.info("=== Validating Coordinate Data ===")

        success = True

        try:
            with self.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:

                # Properties coordinate validation
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_properties,
                        COUNT(CASE WHEN coordenadas_validas = true THEN 1 END) as valid_coords,
                        COUNT(CASE WHEN coordenadas IS NULL THEN 1 END) as null_coords,
                        COUNT(CASE WHEN NOT ST_IsValid(coordenadas::geometry) THEN 1 END) as invalid_geom
                    FROM propiedades
                """)
                prop_coords = cursor.fetchone()

                self.validation_results['coordinate_validation']['properties'] = dict(prop_coords)
                valid_coord_percentage = (prop_coords['valid_coords'] / prop_coords['total_properties'] * 100) if prop_coords['total_properties'] > 0 else 0

                self.logger.info(f"Properties: {prop_coords['total_properties']} total, {prop_coords['valid_coords']} valid coordinates ({valid_coord_percentage:.1f}%)")

                if prop_coords['invalid_geom'] > 0:
                    self.logger.error(f"Found {prop_coords['invalid_geom']} properties with invalid geometry")
                    success = False

                # Services coordinate validation
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_services,
                        COUNT(CASE WHEN coordenadas_validas = true THEN 1 END) as valid_coords,
                        COUNT(CASE WHEN coordenadas IS NULL THEN 1 END) as null_coords,
                        COUNT(CASE WHEN NOT ST_IsValid(coordenadas::geometry) THEN 1 END) as invalid_geom
                    FROM servicios
                """)
                serv_coords = cursor.fetchone()

                self.validation_results['coordinate_validation']['services'] = dict(serv_coords)
                serv_valid_percentage = (serv_coords['valid_coords'] / serv_coords['total_services'] * 100) if serv_coords['total_services'] > 0 else 0

                self.logger.info(f"Services: {serv_coords['total_services']} total, {serv_coords['valid_coords']} valid coordinates ({serv_valid_percentage:.1f}%)")

                if serv_coords['invalid_geom'] > 0:
                    self.logger.error(f"Found {serv_coords['invalid_geom']} services with invalid geometry")
                    success = False

                # Test spatial functions
                cursor.execute("""
                    SELECT COUNT(*) as properties_in_equipetrol
                    FROM propiedades
                    WHERE zona = 'Equipetrol' AND coordenadas_validas = true
                """)
                equipetrol_props = cursor.fetchone()['properties_in_equipetrol']
                self.logger.info(f"Properties in Equipetrol with valid coordinates: {equipetrol_props}")

                # Test distance calculation
                cursor.execute("""
                    SELECT COUNT(*) as near_hospitals
                    FROM propiedades p
                    JOIN servicios s ON s.tipo_servicio = 'hospital' AND s.coordenadas_validas = true
                    WHERE p.coordenadas_validas = true
                      AND ST_DWithin(p.coordenadas, s.coordenadas, 2000)  -- 2km
                """)
                near_hospitals = cursor.fetchone()['near_hospitals']
                self.logger.info(f"Properties within 2km of hospitals: {near_hospitals}")

                return success

        except Exception as e:
            self.logger.error(f"Coordinate validation failed: {e}")
            return False

    def validate_relationships(self) -> bool:
        """Validate foreign key relationships and data consistency"""
        self.logger.info("=== Validating Data Relationships ===")

        success = True

        try:
            with self.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:

                # Check properties with valid agent references
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_properties,
                        COUNT(CASE WHEN agente_id IS NOT NULL THEN 1 END) as with_agent,
                        COUNT(CASE WHEN agente_id IS NULL THEN 1 END) as without_agent
                    FROM propiedades
                """)
                agent_refs = cursor.fetchone()

                self.validation_results['relationship_validation']['property_agents'] = dict(agent_refs)
                self.logger.info(f"Properties with agents: {agent_refs['with_agent']}, without agents: {agent_refs['without_agent']}")

                # Check for orphaned properties (agents that don't exist)
                cursor.execute("""
                    SELECT COUNT(*) as orphaned_properties
                    FROM propiedades p
                    LEFT JOIN agentes a ON p.agente_id = a.id
                    WHERE p.agente_id IS NOT NULL AND a.id IS NULL
                """)
                orphaned = cursor.fetchone()['orphaned_properties']

                if orphaned > 0:
                    self.logger.error(f"Found {orphaned} properties with non-existent agent references")
                    success = False
                else:
                    self.logger.info("All property agent references are valid")

                # Validate data provider consistency
                cursor.execute("""
                    SELECT proveedor_datos, COUNT(*) as count
                    FROM propiedades
                    WHERE proveedor_datos IS NOT NULL
                    GROUP BY proveedor_datos
                    ORDER BY count DESC
                """)
                providers = cursor.fetchall()
                self.validation_results['relationship_validation']['data_providers'] = providers

                self.logger.info("Data providers:")
                for provider in providers:
                    self.logger.info(f"  {provider['proveedor_datos']}: {provider['count']} properties")

                return success

        except Exception as e:
            self.logger.error(f"Relationship validation failed: {e}")
            return False

    def run_performance_tests(self) -> bool:
        """Run performance tests to validate migration improvements"""
        if not self.performance_test:
            return True

        self.logger.info("=== Running Performance Tests ===")

        success = True

        try:
            with self.db_connection.cursor() as cursor:

                # Test 1: Count all properties
                start_time = time.time()
                cursor.execute("SELECT COUNT(*) FROM propiedades")
                count_result = cursor.fetchone()[0]
                count_time = (time.time() - start_time) * 1000

                self.validation_results['performance_metrics']['count_properties_ms'] = count_time
                self.logger.info(f"Property count query: {count_time:.2f}ms")

                # Test 2: Spatial query - properties near hospitals
                start_time = time.time()
                cursor.execute("""
                    SELECT COUNT(*) FROM propiedades p
                    JOIN servicios s ON s.tipo_servicio = 'hospital'
                    WHERE ST_DWithin(p.coordenadas, s.coordenadas, 2000)
                """)
                spatial_result = cursor.fetchone()[0]
                spatial_time = (time.time() - start_time) * 1000

                self.validation_results['performance_metrics']['spatial_query_ms'] = spatial_time
                self.logger.info(f"Spatial query (near hospitals): {spatial_time:.2f}ms")

                # Test 3: Complex query with filters and spatial condition
                start_time = time.time()
                cursor.execute("""
                    SELECT COUNT(*) FROM propiedades p
                    WHERE p.zona = 'Equipetrol'
                      AND p.precio_usd BETWEEN 100000 AND 300000
                      AND p.tipo_propiedad = 'departamento'
                      AND EXISTS (
                          SELECT 1 FROM servicios s
                          WHERE s.tipo_servicio = 'colegio'
                            AND ST_DWithin(p.coordenadas, s.coordenadas, 1500)
                      )
                """)
                complex_result = cursor.fetchone()[0]
                complex_time = (time.time() - start_time) * 1000

                self.validation_results['performance_metrics']['complex_query_ms'] = complex_time
                self.logger.info(f"Complex query (Equipetrol + price + type + school): {complex_time:.2f}ms")

                # Test 4: Index usage check
                cursor.execute("""
                    SELECT
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan,
                        idx_tup_read
                    FROM pg_stat_user_indexes
                    WHERE tablename IN ('propiedades', 'servicios', 'agentes')
                    ORDER BY idx_scan DESC
                    LIMIT 10
                """)
                index_usage = cursor.fetchall()

                self.logger.info("Top 10 most used indexes:")
                for idx in index_usage:
                    self.logger.info(f"  {idx[2]} on {idx[1]}: {idx[3]} scans")

                # Performance benchmarks
                if spatial_time > 1000:  # > 1 second
                    self.logger.warning(f"Spatial query is slow: {spatial_time:.2f}ms (>1000ms threshold)")
                    success = False
                else:
                    self.logger.info("Spatial query performance is acceptable")

                if complex_time > 2000:  # > 2 seconds
                    self.logger.warning(f"Complex query is slow: {complex_time:.2f}ms (>2000ms threshold)")
                    success = False
                else:
                    self.logger.info("Complex query performance is acceptable")

                return success

        except Exception as e:
            self.logger.error(f"Performance tests failed: {e}")
            return False

    def check_migration_logs(self) -> bool:
        """Check migration logs for errors"""
        self.logger.info("=== Checking Migration Logs ===")

        try:
            with self.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:

                cursor.execute("""
                    SELECT tabla_migrada, fecha_ejecucion, registros_procesados,
                           registros_exitosos, registros_errores, execution_time_ms
                    FROM migration_log
                    ORDER BY fecha_ejecucion DESC
                """)
                logs = cursor.fetchall()

                if not logs:
                    self.logger.warning("No migration logs found")
                    return True

                total_errors = 0
                self.logger.info("Migration log summary:")

                for log in logs:
                    error_rate = (log['registros_errores'] / log['registros_procesados'] * 100) if log['registros_procesados'] > 0 else 0
                    self.logger.info(f"  {log['tabla_migrada']}: {log['registros_procesados']} processed, "
                                   f"{log['registros_exitosos']} successful, {log['registros_errores']} errors "
                                   f"({error_rate:.1f}% error rate)")
                    total_errors += log['registros_errores']

                if total_errors > 0:
                    self.logger.warning(f"Total migration errors: {total_errors}")
                    return False
                else:
                    self.logger.info("No migration errors detected")
                    return True

        except Exception as e:
            self.logger.error(f"Failed to check migration logs: {e}")
            return False

    def generate_validation_report(self) -> str:
        """Generate comprehensive validation report"""
        report = []
        report.append("=" * 60)
        report.append("CITRINO MIGRATION VALIDATION REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)

        # Data Integrity Section
        report.append("\n📊 DATA INTEGRITY")
        report.append("-" * 30)
        if 'properties' in self.validation_results['data_integrity']:
            props = self.validation_results['data_integrity']['properties']
            status = "✅ PASS" if props['match'] else "❌ FAIL"
            report.append(f"Properties Count: JSON={props['json_count']}, PostgreSQL={props['postgresql_count']} {status}")

        if 'services' in self.validation_results['data_integrity']:
            servs = self.validation_results['data_integrity']['services']
            status = "✅ PASS" if servs['match'] else "❌ FAIL"
            report.append(f"Services Count: JSON={servs['json_count']}, PostgreSQL={servs['postgresql_count']} {status}")

        if 'property_duplicates' in self.validation_results['data_integrity']:
            dup_count = self.validation_results['data_integrity']['property_duplicates']
            status = "✅ PASS" if dup_count == 0 else "⚠️ WARNING"
            report.append(f"Property Duplicates: {dup_count} {status}")

        # Coordinate Validation Section
        report.append("\n🗺️ COORDINATE VALIDATION")
        report.append("-" * 30)
        if 'properties' in self.validation_results['coordinate_validation']:
            props = self.validation_results['coordinate_validation']['properties']
            valid_pct = (props['valid_coords'] / props['total_properties'] * 100) if props['total_properties'] > 0 else 0
            report.append(f"Properties: {props['valid_coords']}/{props['total_properties']} valid coordinates ({valid_pct:.1f}%)")

        if 'services' in self.validation_results['coordinate_validation']:
            servs = self.validation_results['coordinate_validation']['services']
            valid_pct = (servs['valid_coords'] / servs['total_services'] * 100) if servs['total_services'] > 0 else 0
            report.append(f"Services: {servs['valid_coords']}/{servs['total_services']} valid coordinates ({valid_pct:.1f}%)")

        # Performance Metrics Section
        if self.validation_results['performance_metrics']:
            report.append("\n⚡ PERFORMANCE METRICS")
            report.append("-" * 30)
            metrics = self.validation_results['performance_metrics']
            if 'count_properties_ms' in metrics:
                report.append(f"Property Count Query: {metrics['count_properties_ms']:.2f}ms")
            if 'spatial_query_ms' in metrics:
                report.append(f"Spatial Query (Near Hospitals): {metrics['spatial_query_ms']:.2f}ms")
            if 'complex_query_ms' in metrics:
                report.append(f"Complex Query: {metrics['complex_query_ms']:.2f}ms")

        # Overall Assessment
        report.append("\n🎯 OVERALL ASSESSMENT")
        report.append("-" * 30)

        errors = len(self.validation_results['errors'])
        if errors == 0:
            report.append("✅ MIGRATION VALIDATION: PASSED")
            report.append("All checks completed successfully. Migration is ready for production.")
        else:
            report.append(f"❌ MIGRATION VALIDATION: FAILED")
            report.append(f"Found {errors} critical issues that must be resolved.")
            report.append("Issues:")
            for error in self.validation_results['errors']:
                report.append(f"  - {error}")

        report.append("\n" + "=" * 60)

        return "\n".join(report)

    def run(self) -> bool:
        """Execute complete validation suite"""
        self.logger.info("Starting migration validation")

        try:
            # Connect to database
            if not self.connect_database():
                return False

            # Load original JSON data
            json_data = self.load_json_data()

            # Run validation checks
            success = True

            success &= self.validate_data_integrity(json_data)
            success &= self.validate_coordinates()
            success &= self.validate_relationships()
            success &= self.check_migration_logs()

            if self.performance_test:
                success &= self.run_performance_tests()

            # Generate and display report
            report = self.generate_validation_report()
            print(report)

            # Save report to file
            report_file = self.project_root / f"migration_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            self.logger.info(f"Validation report saved to: {report_file}")

            return success

        except Exception as e:
            self.logger.error(f"Validation process failed: {e}")
            self.validation_results['errors'].append(f"Validation process failed: {e}")
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

    parser = argparse.ArgumentParser(description='Migration validation script')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--performance-test', action='store_true', help='Run performance tests')

    args = parser.parse_args()

    validator = MigrationValidator(verbose=args.verbose, performance_test=args.performance_test)
    success = validator.run()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()