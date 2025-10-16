#!/usr/bin/env python3
"""
Complete migration validation suite
"""
import sys
import os
import time
sys.path.append('migration/config')

from database_config import create_connection
import json
from datetime import datetime

def validate_migration_complete():
    """Complete validation of the PostgreSQL + PostGIS migration"""
    print("=== POSTGRESQL MIGRATION VALIDATION SUITE ===")
    print(f"Timestamp: {datetime.now().isoformat()}")

    conn = create_connection()
    cursor = conn.cursor()

    validation_results = {
        'timestamp': datetime.now().isoformat(),
        'validations': {},
        'performance_tests': {},
        'spatial_queries': {},
        'data_quality': {},
        'summary': {}
    }

    try:
        # 1. Basic Structure Validation
        print("\n1. VALIDATING DATABASE STRUCTURE...")

        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
        total_tables = cursor.fetchone()[0]

        required_tables = ['propiedades', 'servicios']
        existing_tables = []
        for table in required_tables:
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = %s)", (table,))
            exists = cursor.fetchone()[0]
            if exists:
                existing_tables.append(table)

        validation_results['validations']['structure'] = {
            'total_tables': total_tables,
            'required_tables': required_tables,
            'existing_tables': existing_tables,
            'structure_valid': len(existing_tables) == len(required_tables)
        }

        print(f"   - Total tables: {total_tables}")
        print(f"   - Required tables found: {len(existing_tables)}/{len(required_tables)}")

        # 2. Data Volume Validation
        print("\n2. VALIDATING DATA VOLUME...")

        cursor.execute("SELECT COUNT(*) FROM propiedades")
        properties_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM servicios")
        services_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM propiedades WHERE coordenadas IS NOT NULL")
        properties_with_coords = int(cursor.fetchone()[0])

        cursor.execute("SELECT COUNT(*) FROM servicios WHERE coordenadas IS NOT NULL")
        services_with_coords = int(cursor.fetchone()[0])

        validation_results['validations']['data_volume'] = {
            'properties_total': properties_count,
            'properties_with_coordinates': properties_with_coords,
            'services_total': services_count,
            'services_with_coordinates': services_with_coords,
            'properties_coord_coverage': round(properties_with_coords / properties_count * 100, 1) if properties_count > 0 else 0,
            'services_coord_coverage': round(services_with_coords / services_count * 100, 1) if services_count > 0 else 0
        }

        print(f"   - Properties: {properties_count} total, {properties_with_coords} with coordinates ({validation_results['validations']['data_volume']['properties_coord_coverage']}%)")
        print(f"   - Services: {services_count} total, {services_with_coords} with coordinates ({validation_results['validations']['data_volume']['services_coord_coverage']}%)")

        # 3. Performance Tests
        print("\n3. PERFORMANCE BENCHMARKS...")

        # Test 1: Simple count
        start_time = time.time()
        cursor.execute("SELECT COUNT(*) FROM propiedades")
        cursor.fetchone()
        count_time = time.time() - start_time

        # Test 2: Zone query
        start_time = time.time()
        cursor.execute("SELECT COUNT(*) FROM propiedades WHERE zona = 'Equipetrol'")
        cursor.fetchone()
        zone_time = time.time() - start_time

        # Test 3: Price range query
        start_time = time.time()
        cursor.execute("SELECT COUNT(*) FROM propiedades WHERE precio_usd BETWEEN 100000 AND 200000")
        cursor.fetchone()
        price_time = time.time() - start_time

        validation_results['performance_tests'] = {
            'count_query': round(count_time * 1000, 2),
            'zone_query': round(zone_time * 1000, 2),
            'price_query': round(price_time * 1000, 2)
        }

        print(f"   - Count query: {count_time:.3f}s")
        print(f"   - Zone query: {zone_time:.3f}s")
        print(f"   - Price range query: {price_time:.3f}s")

        # 4. Spatial Function Tests (if coordinates available)
        if services_with_coords > 0 and properties_with_coords > 0:
            print("\n4. SPATIAL FUNCTION TESTS...")

            # Test basic spatial functions
            start_time = time.time()
            cursor.execute("SELECT ST_Distance(ST_MakePoint(-63.18, -17.78)::geography, ST_MakePoint(-63.19, -17.79)::geography)")
            distance_test = cursor.fetchone()[0]
            distance_time = time.time() - start_time

            validation_results['spatial_queries']['distance_test'] = {
                'result': float(distance_test),
                'execution_time_ms': round(distance_time * 1000, 2)
            }

            print(f"   - ST_Distance test: {distance_test:.2f}m in {distance_time:.3f}s")

        # 5. Data Quality Analysis
        print("\n5. DATA QUALITY ANALYSIS...")

        cursor.execute("SELECT COUNT(*) FROM propiedades WHERE precio_usd > 0 AND precio_usd < 1000000")
        valid_prices = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT zona) FROM propiedades WHERE zona IS NOT NULL")
        unique_zones = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT tipo) FROM servicios WHERE tipo IS NOT NULL")
        unique_service_types = cursor.fetchone()[0]

        validation_results['data_quality'] = {
            'valid_price_range': valid_prices,
            'price_quality_percentage': round(valid_prices / properties_count * 100, 1) if properties_count > 0 else 0,
            'unique_zones': unique_zones,
            'unique_service_types': unique_service_types
        }

        print(f"   - Valid price range: {valid_prices}/{properties_count} ({validation_results['data_quality']['price_quality_percentage']}%)")
        print(f"   - Unique zones: {unique_zones}")
        print(f"   - Unique service types: {unique_service_types}")

        # 6. Final Summary
        print("\n6. VALIDATION SUMMARY...")

        structure_score = 100 if validation_results['validations']['structure']['structure_valid'] else 0
        data_score = min(100, (properties_count + services_count) / 10)  # Basic data presence
        performance_score = 100 if all(t < 0.1 for t in [count_time, zone_time, price_time]) else 75
        spatial_score = 100 if validation_results.get('spatial_queries') else 50

        overall_score = (structure_score + data_score + performance_score + spatial_score) / 4

        validation_results['summary'] = {
            'structure_score': structure_score,
            'data_score': data_score,
            'performance_score': performance_score,
            'spatial_score': spatial_score,
            'overall_score': round(overall_score, 1),
            'migration_status': 'SUCCESS' if overall_score >= 75 else 'NEEDS_IMPROVEMENT'
        }

        print(f"   - Structure Score: {structure_score}/100")
        print(f"   - Data Score: {data_score}/100")
        print(f"   - Performance Score: {performance_score}/100")
        print(f"   - Spatial Score: {spatial_score}/100")
        print(f"   - OVERALL SCORE: {overall_score:.1f}/100")
        print(f"   - STATUS: {validation_results['summary']['migration_status']}")

        # Save results
        with open('migration/validation_results.json', 'w') as f:
            json.dump(validation_results, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Detailed results saved to: migration/validation_results.json")

        return validation_results

    except Exception as e:
        print(f"ERROR: VALIDATION FAILED: {e}")
        validation_results['summary']['migration_status'] = 'ERROR'
        validation_results['summary']['error'] = str(e)
        return validation_results

    finally:
        conn.close()

if __name__ == "__main__":
    results = validate_migration_complete()
    print(f"\n{'='*60}")
    print(f"MIGRATION VALIDATION COMPLETE")
    print(f"Status: {results['summary']['migration_status']}")
    print(f"Score: {results['summary']['overall_score']}/100")
    print(f"{'='*60}")