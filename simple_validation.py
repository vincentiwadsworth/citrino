#!/usr/bin/env python3
"""
Simple migration validation
"""
import sys
import os
import time
sys.path.append('migration/config')

from database_config import create_connection

def validate_migration():
    """Simple validation of PostgreSQL + PostGIS migration"""
    print("=== SIMPLE POSTGRESQL MIGRATION VALIDATION ===")

    conn = create_connection()
    cursor = conn.cursor()

    try:
        # 1. Basic Data Counts
        print("\n1. DATA INVENTORY:")

        cursor.execute("SELECT COUNT(*) FROM propiedades")
        properties = int(cursor.fetchone()[0])

        cursor.execute("SELECT COUNT(*) FROM servicios")
        services = int(cursor.fetchone()[0])

        print(f"   - Properties: {properties}")
        print(f"   - Services: {services}")
        print(f"   - Total Records: {properties + services}")

        # 2. Performance Test
        print("\n2. PERFORMANCE TEST:")

        start = time.time()
        cursor.execute("SELECT COUNT(*) FROM propiedades WHERE zona = 'Equipetrol'")
        count = cursor.fetchone()[0]
        query_time = time.time() - start

        print(f"   - Zone query time: {query_time:.3f}s")
        print(f"   - Properties in Equipetrol: {count}")
        print(f"   - Performance: {'EXCELLENT' if query_time < 0.05 else 'GOOD' if query_time < 0.1 else 'NEEDS OPTIMIZATION'}")

        # 3. Data Quality
        print("\n3. DATA QUALITY:")

        cursor.execute("SELECT COUNT(*) FROM propiedades WHERE precio_usd > 0")
        valid_prices = int(cursor.fetchone()[0])

        cursor.execute("SELECT COUNT(DISTINCT zona) FROM propiedades WHERE zona IS NOT NULL")
        zones = int(cursor.fetchone()[0])

        print(f"   - Valid prices: {valid_prices}/{properties} ({round(valid_prices/properties*100,1)}%)")
        print(f"   - Unique zones: {zones}")

        # 4. PostGIS Functions
        print("\n4. POSTGIS VERIFICATION:")

        try:
            start = time.time()
            cursor.execute("SELECT ST_Distance(ST_MakePoint(-63.18, -17.78)::geography, ST_MakePoint(-63.19, -17.79)::geography)")
            distance = cursor.fetchone()[0]
            spatial_time = time.time() - start

            print(f"   - ST_Distance function: {float(distance):.2f}m in {spatial_time:.3f}s")
            print(f"   - PostGIS Status: WORKING")
        except Exception as e:
            print(f"   - PostGIS Status: ERROR - {e}")

        # 5. Index Verification
        print("\n5. INDEX VERIFICATION:")

        cursor.execute("SELECT COUNT(*) FROM pg_indexes WHERE tablename IN ('propiedades', 'servicios')")
        indexes = int(cursor.fetchone()[0])

        print(f"   - Total indexes: {indexes}")
        print(f"   - Index Status: {'OK' if indexes >= 4 else 'NEEDS MORE INDEXES'}")

        # Summary
        print("\n6. SUMMARY:")
        overall_score = 100
        if query_time > 0.1: overall_score -= 20
        if valid_prices/properties < 0.8: overall_score -= 20
        if indexes < 4: overall_score -= 20

        status = "SUCCESS" if overall_score >= 80 else "NEEDS IMPROVEMENT"

        print(f"   - Overall Score: {overall_score}/100")
        print(f"   - Migration Status: {status}")
        print(f"   - PostgreSQL + PostGIS: {'OPERATIONAL' if overall_score >= 80 else 'NEEDS WORK'}")

    except Exception as e:
        print(f"   ERROR: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    validate_migration()