#!/usr/bin/env python3
"""
Simplified deduplication script using Docker connection
"""
import subprocess
import sys
import os

def run_deduplication_via_docker():
    """Run deduplication using Docker psql wrapper"""
    print("=== DEDUPLICATION SYSTEM VIA DOCKER ===")

    try:
        # 1. Check for duplicates by title and zone
        query1 = """
        SELECT titulo, zona, COUNT(*) as duplicate_count,
               STRING_AGG(id::text, ', ' ORDER BY id) as duplicate_ids
        FROM propiedades
        WHERE titulo IS NOT NULL AND zona IS NOT NULL
        GROUP BY titulo, zona
        HAVING COUNT(*) > 1;
        """

        result1 = subprocess.run([
            'docker', 'exec', 'citrino-postgresql', 'psql',
            '-U', 'citrino_app', '-d', 'citrino', '-c', query1
        ], capture_output=True, text=True, encoding='utf-8')

        if result1.returncode == 0:
            print("\n1. DUPLICATE PROPERTIES BY TITLE+ZONE:")
            if result1.stdout.strip():
                lines = result1.stdout.strip().split('\n')
                for line in lines[2:]:  # Skip header lines
                    if line.strip() and not line.startswith('---') and not line.startswith('('):
                        parts = line.split('|')
                        if len(parts) >= 4:
                            titulo = parts[0].strip()
                            zona = parts[1].strip()
                            count = parts[2].strip()
                            ids = parts[3].strip()
                            if count != '1':
                                print(f"   - '{titulo}' in {zona}: {count} duplicates (IDs: {ids})")
            else:
                print("   No duplicates found by title+zone")

        # 2. Check for similar properties (same zone, similar price)
        query2 = """
        SELECT zona,
               ROUND(precio_usd/1000)::text || 'k' as price_range,
               COUNT(*) as similar_count,
               MIN(precio_usd) as min_price,
               MAX(precio_usd) as max_price
        FROM propiedades
        WHERE zona IS NOT NULL AND precio_usd > 0
        GROUP BY zona, ROUND(precio_usd/1000)
        HAVING COUNT(*) > 1
        ORDER BY similar_count DESC;
        """

        result2 = subprocess.run([
            'docker', 'exec', 'citrino-postgresql', 'psql',
            '-U', 'citrino_app', '-d', 'citrino', '-c', query2
        ], capture_output=True, text=True, encoding='utf-8')

        if result2.returncode == 0:
            print("\n2. SIMILAR PROPERTIES BY ZONE+PRICE:")
            if result2.stdout.strip():
                lines = result2.stdout.strip().split('\n')
                for line in lines[2:]:
                    if line.strip() and not line.startswith('---') and not line.startswith('('):
                        parts = line.split('|')
                        if len(parts) >= 4:
                            zona = parts[0].strip()
                            price_range = parts[1].strip()
                            count = parts[2].strip()
                            min_price = parts[3].strip()
                            max_price = parts[4].strip() if len(parts) > 4 else "N/A"
                            if count != '1':
                                print(f"   - {zona}: {count} properties ~{price_range} (range: ${min_price}-${max_price})")
            else:
                print("   No similar properties found")

        # 3. Service deduplication by name and zone
        query3 = """
        SELECT nombre, zona, COUNT(*) as duplicate_count,
               STRING_AGG(id::text, ', ' ORDER BY id) as duplicate_ids
        FROM servicios
        WHERE nombre IS NOT NULL AND zona IS NOT NULL
        GROUP BY nombre, zona
        HAVING COUNT(*) > 1;
        """

        result3 = subprocess.run([
            'docker', 'exec', 'citrino-postgresql', 'psql',
            '-U', 'citrino_app', '-d', 'citrino', '-c', query3
        ], capture_output=True, text=True, encoding='utf-8')

        if result3.returncode == 0:
            print("\n3. DUPLICATE SERVICES BY NAME+ZONE:")
            if result3.stdout.strip():
                lines = result3.stdout.strip().split('\n')
                for line in lines[2:]:
                    if line.strip() and not line.startswith('---') and not line.startswith('('):
                        parts = line.split('|')
                        if len(parts) >= 4:
                            nombre = parts[0].strip()
                            zona = parts[1].strip()
                            count = parts[2].strip()
                            ids = parts[3].strip()
                            if count != '1':
                                print(f"   - '{nombre}' in {zona}: {count} duplicates (IDs: {ids})")
            else:
                print("   No duplicate services found")

        # 4. Overall statistics
        stats_query = """
        SELECT
            'propiedades' as table_name,
            COUNT(*) as total_records,
            COUNT(DISTINCT CONCAT(titulo, '|', zona)) as unique_title_zone,
            COUNT(DISTINCT id) as unique_ids
        FROM propiedades
        UNION ALL
        SELECT
            'servicios' as table_name,
            COUNT(*) as total_records,
            COUNT(DISTINCT CONCAT(nombre, '|', zona)) as unique_name_zone,
            COUNT(DISTINCT id) as unique_ids
        FROM servicios;
        """

        stats_result = subprocess.run([
            'docker', 'exec', 'citrino-postgresql', 'psql',
            '-U', 'citrino_app', '-d', 'citrino', '-c', stats_query
        ], capture_output=True, text=True, encoding='utf-8')

        if stats_result.returncode == 0:
            print("\n4. DEDUPLICATION SUMMARY:")
            if stats_result.stdout.strip():
                lines = stats_result.stdout.strip().split('\n')
                for line in lines[2:]:
                    if line.strip() and not line.startswith('---') and not line.startswith('('):
                        parts = line.split('|')
                        if len(parts) >= 4:
                            table = parts[0].strip()
                            total = parts[1].strip()
                            unique = parts[2].strip()
                            ids = parts[3].strip()
                            duplicate_rate = max(0, int(total) - int(unique))
                            print(f"   - {table}: {total} total, {unique} unique combinations, {duplicate_rate} potential duplicates")

        print("\n=== DEDUPLICATION ANALYSIS COMPLETE ===")
        print("Status: Analysis completed successfully")
        print("Action: Review identified duplicates for manual review")

    except Exception as e:
        print(f"ERROR during deduplication analysis: {e}")
        return False

    return True

if __name__ == "__main__":
    success = run_deduplication_via_docker()
    sys.exit(0 if success else 1)