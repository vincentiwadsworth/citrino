#!/usr/bin/env python3
"""
PostgreSQL Migration Audit Script
=================================

Complete audit system for PostgreSQL + PostGIS migration.
This script performs comprehensive verification without shortcuts
or simplified solutions that could mask underlying issues.

Usage:
    python scripts/audit_postgresql_migration.py [--verbose] [--export-json]

Author: Citrino Engineering Team
Date: 2025-10-16
"""

import subprocess
import json
import time
import sys
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
import pandas as pd

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

class PostgreSQLAuditSystem:
    """Complete audit system for PostgreSQL migration"""

    def __init__(self, verbose: bool = False, export_json: bool = False):
        self.verbose = verbose
        self.export_json = export_json
        self.setup_logging()
        self.start_time = datetime.now()

        # Results storage
        self.audit_results = {
            'timestamp': self.start_time.isoformat(),
            'infrastructure': {},
            'etl_system': {},
            'data_quality': {},
            'api_integration': {},
            'performance': {},
            'summary': {}
        }

        # Docker command base
        self.docker_psql_base = [
            'docker', 'exec', 'citrino-postgresql', 'psql',
            '-U', 'citrino_app', '-d', 'citrino', '-c'
        ]

    def setup_logging(self):
        """Setup comprehensive logging"""
        log_level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/audit.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)

    def run_command(self, command: List[str], description: str) -> Tuple[bool, str, str]:
        """Run command and capture output"""
        self.logger.info(f"Executing: {description}")

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=120
            )

            success = result.returncode == 0
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            if success:
                self.logger.debug(f"OK Success: {description}")
                if self.verbose and stdout:
                    self.logger.debug(f"Output: {stdout[:200]}...")
            else:
                self.logger.error(f"ERROR Failed: {description}")
                self.logger.error(f"Error: {stderr}")

            return success, stdout, stderr

        except subprocess.TimeoutExpired:
            self.logger.error(f"ERROR Timeout: {description}")
            return False, "", "Command timed out after 120 seconds"
        except Exception as e:
            self.logger.error(f"ERROR Exception: {description} - {e}")
            return False, "", str(e)

    def audit_infrastructure(self) -> Dict[str, Any]:
        """Audit PostgreSQL infrastructure"""
        self.logger.info("=" * 60)
        self.logger.info("AUDIT FASE 1: INFRASTRUCTURA POSTGRESQL")
        self.logger.info("=" * 60)

        results = {
            'docker_status': False,
            'postgresql_version': None,
            'postgis_version': None,
            'database_size': None,
            'user_permissions': False,
            'indexes_count': 0,
            'spatial_indexes': 0
        }

        # 1. Docker container status
        success, stdout, _ = self.run_command(
            ['docker', 'ps', '--filter', 'name=citrino-postgresql', '--format', '{{.Status}}'],
            "Check Docker container status"
        )
        results['docker_status'] = success and 'Up' in stdout

        # 2. PostgreSQL version
        success, stdout, _ = self.run_command(
            self.docker_psql_base + ["SELECT version();"],
            "Get PostgreSQL version"
        )
        if success:
            results['postgresql_version'] = stdout

        # 3. PostGIS version
        success, stdout, _ = self.run_command(
            self.docker_psql_base + ["SELECT PostGIS_Version();"],
            "Get PostGIS version"
        )
        if success:
            results['postgis_version'] = stdout

        # 4. Database size
        success, stdout, _ = self.run_command(
            self.docker_psql_base + [
                "SELECT pg_size_pretty(pg_database_size('citrino'));"
            ],
            "Get database size"
        )
        if success:
            results['database_size'] = stdout

        # 5. User permissions test
        success, _, _ = self.run_command(
            self.docker_psql_base + ["SELECT current_user;"],
            "Test user permissions"
        )
        results['user_permissions'] = success

        # 6. Indexes count
        success, stdout, _ = self.run_command(
            self.docker_psql_base + [
                "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';"
            ],
            "Count total indexes"
        )
        if success:
            try:
                # Extract numeric value from PostgreSQL output (skip header)
                lines = stdout.strip().split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('-') and not line.startswith('count'):
                        try:
                            value = int(line.strip())
                            results['indexes_count'] = value
                            break
                        except ValueError:
                            continue
            except Exception:
                results['indexes_count'] = 0

        # 7. Spatial indexes
        success, stdout, _ = self.run_command(
            self.docker_psql_base + [
                "SELECT COUNT(*) FROM pg_indexes WHERE indexdef LIKE '%gist%';"
            ],
            "Count spatial indexes"
        )
        if success:
            try:
                # Extract numeric value from PostgreSQL output (skip header)
                lines = stdout.strip().split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('-') and not line.startswith('count'):
                        try:
                            value = int(line.strip())
                            results['spatial_indexes'] = value
                            break
                        except ValueError:
                            continue
            except Exception:
                results['spatial_indexes'] = 0

        self.audit_results['infrastructure'] = results
        return results

    def audit_etl_system(self) -> Dict[str, Any]:
        """Audit ETL system components"""
        self.logger.info("=" * 60)
        self.logger.info("AUDIT FASE 2: SISTEMA ETL")
        self.logger.info("=" * 60)

        results = {
            'etl_properties_exists': False,
            'etl_properties_dryrun': False,
            'etl_properties_detected': 0,
            'etl_services_exists': False,
            'etl_services_status': False,
            'etl_orchestrator_exists': False,
            'etl_orchestrator_status': False,
            'excel_files_detected': 0,
            'raw_files_processed': 0
        }

        # 1. Check ETL scripts exist
        etl_props_path = Path('migration/scripts/02_etl_propiedades.py')
        etl_svcs_path = Path('migration/scripts/etl_servicios_from_excel.py')
        orchestrator_path = Path('migration/scripts/migration_run_properties.py')

        results['etl_properties_exists'] = etl_props_path.exists()
        results['etl_services_exists'] = etl_svcs_path.exists()
        results['etl_orchestrator_exists'] = orchestrator_path.exists()

        # 2. Test ETL properties dry-run
        if results['etl_properties_exists']:
            success, stdout, _ = self.run_command(
                ['python', 'migration/scripts/02_etl_propiedades.py', '--dry-run'],
                "Test ETL properties dry-run"
            )
            results['etl_properties_dryrun'] = success

            if success:
                # Extract detected properties count
                for line in stdout.split('\n'):
                    if 'Total properties processed' in line:
                        try:
                            count = int(line.split(':')[-1].strip())
                            results['etl_properties_detected'] = count
                        except:
                            pass

        # 3. Test ETL services
        if results['etl_services_exists']:
            success, stdout, _ = self.run_command(
                ['python', 'migration/scripts/etl_servicios_from_excel.py'],
                "Test ETL services"
            )
            results['etl_services_status'] = success

        # 4. Test orchestrator
        if results['etl_orchestrator_exists']:
            success, stdout, _ = self.run_command(
                ['python', 'migration/scripts/migration_run_properties.py', '--dry-run'],
                "Test ETL orchestrator"
            )
            results['etl_orchestrator_status'] = success

        # 5. Count Excel files
        raw_dir = Path('data/raw/relevamiento')
        if raw_dir.exists():
            results['excel_files_detected'] = len(list(raw_dir.glob('*.xlsx')))

        self.audit_results['etl_system'] = results
        return results

    def audit_data_quality(self) -> Dict[str, Any]:
        """Audit data quality in database"""
        self.logger.info("=" * 60)
        self.logger.info("AUDIT FASE 3: CALIDAD DE DATOS")
        self.logger.info("=" * 60)

        results = {
            'properties_count': 0,
            'services_count': 0,
            'valid_coordinates': 0,
            'valid_coordinates_pct': 0,
            'valid_prices': 0,
            'valid_prices_pct': 0,
            'duplicate_properties': 0,
            'coordinate_out_of_range': 0,
            'price_anomalies': 0,
            'zones_count': 0,
            'property_types_count': 0,
            'service_categories_count': 0
        }

        queries = {
            'properties_count': "SELECT COUNT(*) FROM propiedades;",
            'services_count': "SELECT COUNT(*) FROM servicios;",
            'valid_coordinates': """
                SELECT COUNT(*) FROM propiedades
                WHERE coordenadas_validas = true AND coordenadas IS NOT NULL;
            """,
            'valid_prices': """
                SELECT COUNT(*) FROM propiedades
                WHERE precio_usd > 0 AND precio_usd < 10000000;
            """,
            'duplicate_properties': """
                SELECT COUNT(*) - COUNT(DISTINCT CONCAT(titulo, '|', zona))
                FROM propiedades
                WHERE titulo IS NOT NULL AND zona IS NOT NULL;
            """,
            'coordinate_out_of_range': """
                SELECT COUNT(*) FROM propiedades
                WHERE coordenadas_validas = false
                AND latitud IS NOT NULL AND longitud IS NOT NULL;
            """,
            'price_anomalies': """
                SELECT COUNT(*) FROM propiedades
                WHERE precio_usd < 1000 OR precio_usd > 5000000;
            """,
            'zones_count': "SELECT COUNT(DISTINCT zona) FROM propiedades WHERE zona IS NOT NULL;",
            'property_types_count': "SELECT COUNT(DISTINCT tipo_propiedad) FROM propiedades WHERE tipo_propiedad IS NOT NULL;",
            'service_categories_count': "SELECT COUNT(DISTINCT categoria_principal) FROM servicios WHERE categoria_principal IS NOT NULL;"
        }

        for key, query in queries.items():
            success, stdout, _ = self.run_command(
                self.docker_psql_base + [query],
                f"Get data quality metric: {key}"
            )
            if success:
                try:
                    # Extract numeric value from PostgreSQL output (skip header)
                    lines = stdout.strip().split('\n')
                    for line in lines:
                        if line.strip() and not line.startswith('-') and not line.startswith('count') and not line.startswith('Cantidad'):
                            try:
                                value = int(line.strip())
                                results[key] = value
                                break
                            except ValueError:
                                continue
                except Exception:
                    results[key] = 0

        # Calculate percentages
        if results['properties_count'] > 0:
            results['valid_coordinates_pct'] = round(
                (results['valid_coordinates'] / results['properties_count']) * 100, 2
            )
            results['valid_prices_pct'] = round(
                (results['valid_prices'] / results['properties_count']) * 100, 2
            )

        self.audit_results['data_quality'] = results
        return results

    def audit_api_integration(self) -> Dict[str, Any]:
        """Audit API integration with PostgreSQL"""
        self.logger.info("=" * 60)
        self.logger.info("AUDIT FASE 4: INTEGRACIÓN API")
        self.logger.info("=" * 60)

        results = {
            'api_running': False,
            'health_endpoint': False,
            'stats_endpoint': False,
            'recommend_endpoint': False,
            'spatial_query_working': False,
            'database_config': False,
            'postgres_env_var': False
        }

        # 1. Check if API is running
        success, _, _ = self.run_command(
            ['curl', '-s', 'http://localhost:5001/api/health'],
            "Check API running"
        )
        results['api_running'] = success

        if results['api_running']:
            # 2. Test health endpoint
            success, _, _ = self.run_command(
                ['curl', '-s', 'http://localhost:5001/api/health'],
                "Test health endpoint"
            )
            results['health_endpoint'] = success

            # 3. Test stats endpoint
            success, _, _ = self.run_command(
                ['curl', '-s', 'http://localhost:5001/api/stats'],
                "Test stats endpoint"
            )
            results['stats_endpoint'] = success

            # 4. Test recommend endpoint
            test_data = '{"lat": -17.78, "lng": -63.18, "precio_max": 200000}'
            success, _, _ = self.run_command(
                ['curl', '-s', '-X', 'POST', 'http://localhost:5001/api/recommend',
                 '-H', 'Content-Type: application/json',
                 '-d', test_data],
                "Test recommend endpoint"
            )
            results['recommend_endpoint'] = success

        # 5. Test spatial query directly
        success, _, _ = self.run_command(
            self.docker_psql_base + [
                "SELECT COUNT(*) FROM propiedades WHERE ST_DWithin("
                "ST_MakePoint(-63.18, -17.78)::geography, "
                "coordenadas, 1000);"
            ],
            "Test spatial query"
        )
        results['spatial_query_working'] = success

        # 6. Check database configuration
        config_exists = Path('migration/config/database_config.py').exists()
        env_var_set = os.getenv('USE_POSTGRES') == 'true'

        results['database_config'] = config_exists
        results['postgres_env_var'] = env_var_set

        self.audit_results['api_integration'] = results
        return results

    def audit_performance(self) -> Dict[str, Any]:
        """Audit system performance"""
        self.logger.info("=" * 60)
        self.logger.info("AUDIT FASE 5: PERFORMANCE")
        self.logger.info("=" * 60)

        results = {
            'count_query_ms': 0,
            'spatial_query_ms': 0,
            'price_range_query_ms': 0,
            'zone_query_ms': 0,
            'index_usage': 0,
            'database_connections': 0
        }

        # Performance queries
        perf_queries = {
            'count_query_ms': """
                SELECT EXTRACT(EPOCH FROM (now() - (SELECT now()))) * 1000, COUNT(*)
                FROM propiedades;
            """,
            'spatial_query_ms': """
                SELECT EXTRACT(EPOCH FROM (now() - (SELECT now()))) * 1000, COUNT(*)
                FROM propiedades
                WHERE ST_DWithin(
                    ST_MakePoint(-63.18, -17.78)::geography,
                    coordenadas, 1000
                );
            """,
            'price_range_query_ms': """
                SELECT EXTRACT(EPOCH FROM (now() - (SELECT now()))) * 1000, COUNT(*)
                FROM propiedades
                WHERE precio_usd BETWEEN 100000 AND 200000;
            """,
            'zone_query_ms': """
                SELECT EXTRACT(EPOCH FROM (now() - (SELECT now()))) * 1000, COUNT(*)
                FROM propiedades
                WHERE zona = 'Equipetrol';
            """
        }

        for key, query in perf_queries.items():
            start_time = time.time()
            success, stdout, _ = self.run_command(
                self.docker_psql_base + [query],
                f"Performance test: {key}"
            )
            if success:
                results[key] = round((time.time() - start_time) * 1000, 2)
            else:
                results[key] = -1

        # Index usage
        success, stdout, _ = self.run_command(
            self.docker_psql_base + [
                "SELECT SUM(idx_scan) FROM pg_stat_user_indexes WHERE schemaname = 'public';"
            ],
            "Get index usage"
        )
        if success:
            try:
                # Extract numeric value from PostgreSQL output (skip header)
                lines = stdout.strip().split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('-') and not line.startswith('sum'):
                        try:
                            value = int(line.strip())
                            results['index_usage'] = value
                            break
                        except ValueError:
                            continue
            except Exception:
                results['index_usage'] = 0

        # Active connections
        success, stdout, _ = self.run_command(
            self.docker_psql_base + [
                "SELECT COUNT(*) FROM pg_stat_activity WHERE datname = 'citrino';"
            ],
            "Get active connections"
        )
        if success:
            try:
                # Extract numeric value from PostgreSQL output (skip header)
                lines = stdout.strip().split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('-') and not line.startswith('count'):
                        try:
                            value = int(line.strip())
                            results['database_connections'] = value
                            break
                        except ValueError:
                            continue
            except Exception:
                results['database_connections'] = 0

        self.audit_results['performance'] = results
        return results

    def generate_summary(self) -> Dict[str, Any]:
        """Generate audit summary"""
        self.logger.info("=" * 60)
        self.logger.info("AUDIT FASE 6: RESUMEN Y RECOMENDACIONES")
        self.logger.info("=" * 60)

        infra = self.audit_results['infrastructure']
        etl = self.audit_results['etl_system']
        data = self.audit_results['data_quality']
        api = self.audit_results['api_integration']
        perf = self.audit_results['performance']

        # Calculate scores
        infra_score = self._calculate_infrastructure_score(infra)
        etl_score = self._calculate_etl_score(etl)
        data_score = self._calculate_data_score(data)
        api_score = self._calculate_api_score(api)
        perf_score = self._calculate_performance_score(perf)

        overall_score = (infra_score + etl_score + data_score + api_score + perf_score) / 5

        # Determine status
        if overall_score >= 90:
            status = "EXCELLENTE - Listo para producción"
        elif overall_score >= 75:
            status = "BUENO - Ready con mejoras menores"
        elif overall_score >= 50:
            status = "ACEPTABLE - Necesita mejoras significativas"
        else:
            status = "CRÍTICO - No listo para producción"

        summary = {
            'infrastructure_score': infra_score,
            'etl_score': etl_score,
            'data_score': data_score,
            'api_score': api_score,
            'performance_score': perf_score,
            'overall_score': round(overall_score, 2),
            'status': status,
            'critical_issues': self._identify_critical_issues(),
            'recommendations': self._generate_recommendations(),
            'execution_time_ms': round((datetime.now() - self.start_time).total_seconds() * 1000, 2)
        }

        self.audit_results['summary'] = summary
        return summary

    def _calculate_infrastructure_score(self, infra: Dict) -> float:
        """Calculate infrastructure score"""
        score = 0
        if infra.get('docker_status'): score += 20
        if infra.get('postgresql_version'): score += 15
        if infra.get('postgis_version'): score += 15
        if infra.get('user_permissions'): score += 15
        if infra.get('indexes_count', 0) >= 5: score += 15
        if infra.get('spatial_indexes', 0) >= 2: score += 20
        return score

    def _calculate_etl_score(self, etl: Dict) -> float:
        """Calculate ETL score"""
        score = 0
        if etl.get('etl_properties_exists'): score += 15
        if etl.get('etl_properties_dryrun'): score += 20
        if etl.get('etl_properties_detected', 0) >= 1000: score += 20
        if etl.get('etl_services_exists'): score += 15
        if etl.get('etl_services_status'): score += 15
        if etl.get('etl_orchestrator_exists'): score += 15
        return score

    def _calculate_data_score(self, data: Dict) -> float:
        """Calculate data quality score"""
        score = 0
        if data.get('properties_count', 0) >= 1000: score += 25
        if data.get('services_count', 0) >= 50: score += 10
        if data.get('valid_coordinates_pct', 0) >= 90: score += 25
        if data.get('valid_prices_pct', 0) >= 90: score += 20
        if data.get('duplicate_properties', 0) <= 10: score += 10
        if data.get('coordinate_out_of_range', 0) <= 50: score += 10
        return score

    def _calculate_api_score(self, api: Dict) -> float:
        """Calculate API integration score"""
        score = 0
        if api.get('api_running'): score += 20
        if api.get('health_endpoint'): score += 20
        if api.get('stats_endpoint'): score += 20
        if api.get('recommend_endpoint'): score += 20
        if api.get('spatial_query_working'): score += 20
        return score

    def _calculate_performance_score(self, perf: Dict) -> float:
        """Calculate performance score"""
        score = 0
        if 0 < perf.get('count_query_ms', 0) < 100: score += 20
        if 0 < perf.get('spatial_query_ms', 0) < 200: score += 25
        if 0 < perf.get('price_range_query_ms', 0) < 100: score += 20
        if 0 < perf.get('zone_query_ms', 0) < 50: score += 15
        if perf.get('index_usage', 0) > 0: score += 20
        return score

    def _identify_critical_issues(self) -> List[str]:
        """Identify critical issues"""
        issues = []

        if not self.audit_results['infrastructure']['docker_status']:
            issues.append("Docker container not running")

        if not self.audit_results['infrastructure']['postgis_version']:
            issues.append("PostGIS not available")

        if self.audit_results['data_quality']['properties_count'] < 500:
            issues.append("Insufficient property data")

        if self.audit_results['data_quality']['valid_coordinates_pct'] < 80:
            issues.append("Low percentage of valid coordinates")

        if not self.audit_results['api_integration']['api_running']:
            issues.append("API not running")

        if self.audit_results['performance']['spatial_query_ms'] > 500:
            issues.append("Poor spatial query performance")

        return issues

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations"""
        recommendations = []

        if self.audit_results['etl_system']['etl_properties_detected'] < 1500:
            recommendations.append("Run complete ETL migration to load all properties")

        if self.audit_results['data_quality']['duplicate_properties'] > 10:
            recommendations.append("Run deduplication process to clean data")

        if self.audit_results['performance']['spatial_query_ms'] > 200:
            recommendations.append("Optimize spatial indexes for better performance")

        if not self.audit_results['api_integration']['database_config']:
            recommendations.append("Configure database connection for API")

        return recommendations

    def export_results(self):
        """Export audit results to JSON"""
        if self.export_json:
            output_file = f"logs/audit_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.audit_results, f, indent=2, ensure_ascii=False)

            self.logger.info(f"OK Results exported to: {output_file}")

    def run_complete_audit(self) -> Dict[str, Any]:
        """Run complete audit process"""
        self.logger.info("INICIANDO AUDITORIA COMPLETA POSTGRESQL MIGRATION")
        self.logger.info(f"Timestamp: {self.start_time.isoformat()}")

        try:
            # Run all audit phases
            self.audit_infrastructure()
            self.audit_etl_system()
            self.audit_data_quality()
            self.audit_api_integration()
            self.audit_performance()

            # Generate summary
            summary = self.generate_summary()

            # Export results
            self.export_results()

            # Print final results
            self.print_final_results(summary)

            return self.audit_results

        except Exception as e:
            self.logger.error(f"ERROR Audit failed: {e}")
            raise

    def print_final_results(self, summary: Dict[str, Any]):
        """Print final audit results"""
        self.logger.info("=" * 80)
        self.logger.info("RESULTADOS FINALES DE AUDITORIA")
        self.logger.info("=" * 80)

        self.logger.info(f"PUNTAJE GENERAL: {summary['overall_score']}/100")
        self.logger.info(f"ESTADO: {summary['status']}")

        self.logger.info("\nPUNTAJES POR CATEGORIA:")
        self.logger.info(f"  - Infraestructura: {summary['infrastructure_score']}/100")
        self.logger.info(f"  - Sistema ETL: {summary['etl_score']}/100")
        self.logger.info(f"  - Calidad Datos: {summary['data_score']}/100")
        self.logger.info(f"  - Integracion API: {summary['api_score']}/100")
        self.logger.info(f"  - Performance: {summary['performance_score']}/100")

        if summary['critical_issues']:
            self.logger.info("\nISSUES CRITICOS:")
            for issue in summary['critical_issues']:
                self.logger.info(f"  ERROR: {issue}")

        if summary['recommendations']:
            self.logger.info("\nRECOMENDACIONES:")
            for rec in summary['recommendations']:
                self.logger.info(f"  - {rec}")

        self.logger.info(f"\nTiempo ejecucion: {summary['execution_time_ms']}ms")
        self.logger.info("=" * 80)

def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description='Complete PostgreSQL Migration Audit')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--export-json', action='store_true', help='Export results to JSON')

    args = parser.parse_args()

    # Create and run audit system
    audit_system = PostgreSQLAuditSystem(verbose=args.verbose, export_json=args.export_json)

    try:
        results = audit_system.run_complete_audit()

        # Exit with appropriate code
        overall_score = results['summary']['overall_score']
        if overall_score >= 75:
            sys.exit(0)  # Success
        elif overall_score >= 50:
            sys.exit(1)  # Warning
        else:
            sys.exit(2)  # Critical

    except KeyboardInterrupt:
        print("\nWARNING: Audit interrupted by user")
        sys.exit(3)
    except Exception as e:
        print(f"\nERROR: Audit failed: {e}")
        sys.exit(4)

if __name__ == "__main__":
    main()