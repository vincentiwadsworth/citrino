#!/usr/bin/env python3
"""
Migrate to PostgreSQL - Sprint 1 Migration Script
==================================================

Script principal para ejecutar la migración completa de Citrino
desde archivos Excel hacia PostgreSQL + PostGIS.

Author: Claude Code for Citrino
Date: October 2025
"""

import os
import sys
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PostgresMigration:
    """Orquestador principal de la migración a PostgreSQL."""

    def __init__(self, skip_steps: Optional[List[str]] = None):
        """
        Inicializar migración.

        Args:
            skip_steps: Lista de pasos a omitir
        """
        self.skip_steps = skip_steps or []
        self.start_time = datetime.now()
        self.migration_steps = [
            {
                'name': 'create_schema',
                'description': 'Crear esquema PostgreSQL + PostGIS',
                'script': 'data/postgres/scripts/01_create_schema.sql',
                'type': 'sql',
                'required': True
            },
            {
                'name': 'excel_to_intermediate',
                'description': 'Procesar archivos Excel de propiedades',
                'script': 'data/postgres/scripts/etl_excel_to_intermediate.py',
                'type': 'python',
                'required': True
            },
            {
                'name': 'guia_to_intermediate',
                'description': 'Procesar guía urbana municipal',
                'script': 'data/postgres/scripts/etl_guia_to_intermediate.py',
                'type': 'python',
                'required': True
            },
            {
                'name': 'consolidar_agentes',
                'description': 'Consolidar y deduplicar agentes',
                'script': 'data/postgres/scripts/etl_consolidar_agentes.py',
                'type': 'python',
                'required': True
            },
            {
                'name': 'intermediate_to_postgres',
                'description': 'Cargar datos a PostgreSQL',
                'script': 'data/postgres/scripts/etl_intermediate_to_postgres.py',
                'type': 'python',
                'required': True
            },
            {
                'name': 'validate_migration',
                'description': 'Validar migración completa',
                'script': 'data/postgres/scripts/etl_validate_migration.py',
                'type': 'python',
                'required': False
            }
        ]

        self.results = {
            'successful_steps': [],
            'failed_steps': [],
            'skipped_steps': [],
            'start_time': self.start_time,
            'end_time': None,
            'total_duration': None
        }

    def check_prerequisites(self) -> bool:
        """
        Verificar prerrequisitos para la migración.

        Returns:
            True si todos los prerrequisitos están cumplidos
        """
        logger.info("Verificando prerrequisitos...")

        # 1. Verificar variables de entorno
        required_env_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]

        if missing_vars:
            logger.error(f"Faltan variables de entorno requeridas: {missing_vars}")
            logger.error("Por favor configure las variables de entorno en .env")
            return False

        # 2. Verificar directorios necesarios
        required_dirs = [
            'data/raw/relevamiento',
            'data/raw/guia',
            'data/intermedio/procesados',
            'data/intermedio/errores',
            'data/postgres/logs',
            'data/postgres/backups'
        ]

        missing_dirs = []
        for dir_path in required_dirs:
            if not Path(dir_path).exists():
                missing_dirs.append(dir_path)

        if missing_dirs:
            logger.error(f"No existen directorios requeridos: {missing_dirs}")
            logger.info("Ejecutiendo: mkdir -p " + " ".join(missing_dirs))
            try:
                for dir_path in missing_dirs:
                    Path(dir_path).mkdir(parents=True, exist_ok=True)
                logger.info("Directorios creados exitosamente")
            except Exception as e:
                logger.error(f"No se pudieron crear directorios: {e}")
                return False

        # 3. Verificar archivos de scripts
        missing_scripts = []
        for step in self.migration_steps:
            script_path = Path(step['script'])
            if not script_path.exists():
                missing_scripts.append(str(script_path))

        if missing_scripts:
            logger.error(f"No existen scripts requeridos: {missing_scripts}")
            return False

        # 4. Verificar conexión a PostgreSQL (para pasos que lo requieren)
        try:
            import psycopg2
            from dotenv import load_dotenv
            load_dotenv()

            conn = psycopg2.connect(
                host=os.getenv('DB_HOST'),
                port=os.getenv('DB_PORT', '5432'),
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD')
            )
            conn.close()
            logger.info("✓ Conexión a PostgreSQL exitosa")
        except Exception as e:
            logger.error(f"No se puede conectar a PostgreSQL: {e}")
            logger.error("Verifique que PostgreSQL esté corriendo y la configuración sea correcta")
            return False

        logger.info("✓ Todos los prerrequisitos cumplidos")
        return True

    def execute_sql_script(self, script_path: str) -> bool:
        """
        Ejecutar script SQL usando psql.

        Args:
            script_path: Ruta al script SQL

        Returns:
            True si la ejecución fue exitosa
        """
        try:
            from dotenv import load_dotenv
            load_dotenv()

            # Construir comando psql
            cmd = [
                'psql',
                '-h', os.getenv('DB_HOST', 'localhost'),
                '-p', os.getenv('DB_PORT', '5432'),
                '-U', os.getenv('DB_USER'),
                '-d', os.getenv('DB_NAME'),
                '-f', script_path
            ]

            # Establecer variable de entorno de password
            env = os.environ.copy()
            env['PGPASSWORD'] = os.getenv('DB_PASSWORD')

            logger.info(f"Ejecutando: {' '.join(cmd)}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"✓ Script SQL ejecutado exitosamente: {script_path}")
                return True
            else:
                logger.error(f"Error ejecutando script SQL: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error ejecutando script SQL {script_path}: {e}")
            return False

    def execute_python_script(self, script_path: str) -> bool:
        """
        Ejecutar script Python.

        Args:
            script_path: Ruta al script Python

        Returns:
            True si la ejecución fue exitosa
        """
        try:
            logger.info(f"Ejecutando script Python: {script_path}")

            # Usar subprocess para mejor control de errores
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )

            if result.returncode == 0:
                logger.info(f"✓ Script Python ejecutado exitosamente: {script_path}")
                if result.stdout:
                    logger.info(f"Output: {result.stdout[-500:]}")  # Últimos 500 caracteres
                return True
            else:
                logger.error(f"Error ejecutando script Python: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error ejecutando script Python {script_path}: {e}")
            return False

    def execute_step(self, step: Dict) -> bool:
        """
        Ejecutar un paso específico de la migración.

        Args:
            step: Configuración del paso a ejecutar

        Returns:
            True si el paso fue exitoso
        """
        step_name = step['name']
        description = step['description']

        if step_name in self.skip_steps:
            logger.info(f"⏭️  OMITIENDO: {description}")
            self.results['skipped_steps'].append(step)
            return True

        logger.info(f"🔄 EJECUTANDO: {description}")

        start_time = time.time()

        try:
            if step['type'] == 'sql':
                success = self.execute_sql_script(step['script'])
            elif step['type'] == 'python':
                success = self.execute_python_script(step['script'])
            else:
                logger.error(f"Tipo de paso no soportado: {step['type']}")
                success = False

            duration = time.time() - start_time

            if success:
                logger.info(f"✓ COMPLETADO: {description} ({duration:.2f}s)")
                self.results['successful_steps'].append({
                    **step,
                    'duration': duration
                })
                return True
            else:
                logger.error(f"✗ FALLÓ: {description}")
                self.results['failed_steps'].append({
                    **step,
                    'duration': duration
                })

                if step.get('required', True):
                    logger.error("Paso requerido falló. Deteniendo migración.")
                    return False
                else:
                    logger.warning("Paso opcional falló. Continuando migración.")
                    return True

        except Exception as e:
            logger.error(f"Excepción en paso {step_name}: {e}")
            self.results['failed_steps'].append({
                **step,
                'error': str(e)
            })

            if step.get('required', True):
                return False
            else:
                return True

    def run_migration(self) -> bool:
        """
        Ejecutar la migración completa.

        Returns:
            True si la migración fue exitosa
        """
        logger.info("🚀 Iniciando migración a PostgreSQL + PostGIS")
        logger.info(f"Fecha: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)

        # Verificar prerrequisitos
        if not self.check_prerequisites():
            logger.error("❌ Prerrequisitos no cumplidos. Abortando migración.")
            return False

        # Ejecutar cada paso
        for step in self.migration_steps:
            if not self.execute_step(step):
                logger.error("❌ Migración falló")
                return False

        # Finalizar migración
        self.results['end_time'] = datetime.now()
        self.results['total_duration'] = (self.results['end_time'] - self.results['start_time']).total_seconds()

        logger.info("=" * 80)
        logger.info("🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE")
        logger.info("=" * 80)
        self.print_summary()

        return True

    def print_summary(self):
        """Imprimir resumen de la migración."""
        duration = self.results['total_duration']
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)

        logger.info(f"Duración total: {hours:02d}:{minutes:02d}:{seconds:02d}")
        logger.info(f"Pasos exitosos: {len(self.results['successful_steps'])}")
        logger.info(f"Pasos fallidos: {len(self.results['failed_steps'])}")
        logger.info(f"Pasos omitidos: {len(self.results['skipped_steps'])}")

        if self.results['successful_steps']:
            logger.info("")
            logger.info("Pasos ejecutados exitosamente:")
            for step in self.results['successful_steps']:
                logger.info(f"  ✓ {step['description']} ({step.get('duration', 0):.2f}s)")

        if self.results['failed_steps']:
            logger.info("")
            logger.warning("Pasos que fallaron:")
            for step in self.results['failed_steps']:
                logger.warning(f"  ✗ {step['description']} ({step.get('duration', 0):.2f}s)")

        if self.results['skipped_steps']:
            logger.info("")
            logger.info("Pasos omitidos:")
            for step in self.results['skipped_steps']:
                logger.info(f"  ⏭️  {step['description']}")

        # Próximos pasos
        logger.info("")
        logger.info("📋 Próximos pasos recomendados:")
        logger.info("  1. Revisar logs en data/postgres/logs/")
        logger.info("  2. Verificar reportes de validación")
        logger.info("  3. Probar consultas espaciales en PostgreSQL")
        logger.info("  4. Configurar aplicación para usar PostgreSQL")

    def save_results(self):
        """Guardar resultados de la migración en archivo JSON."""
        import json

        results_path = Path("data/postgres/logs")
        results_path.mkdir(parents=True, exist_ok=True)

        timestamp = self.start_time.strftime('%Y%m%d_%H%M%S')
        filename = f"migration_results_{timestamp}.json"
        filepath = results_path / filename

        # Convertir objetos datetime a string
        results_serializable = {
            **self.results,
            'start_time': self.results['start_time'].isoformat(),
            'end_time': self.results['end_time'].isoformat() if self.results['end_time'] else None
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results_serializable, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Resultados guardados en: {filepath}")


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description='Migración Citrino a PostgreSQL + PostGIS')
    parser.add_argument(
        '--skip',
        nargs='+',
        choices=['create_schema', 'excel_to_intermediate', 'guia_to_intermediate',
                'consolidar_agentes', 'intermediate_to_postgres', 'validate_migration'],
        help='Pasos a omitir en la migración'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Solo verificar prerrequisitos sin ejecutar migración'
    )

    args = parser.parse_args()

    # Crear instancia de migración
    migration = PostgresMigration(skip_steps=args.skip)

    if args.dry_run:
        logger.info("🔍 Modo dry-run: solo verificando prerrequisitos")
        success = migration.check_prerequisites()
        if success:
            logger.info("✅ Prerrequisitos cumplidos. Listo para migración.")
        else:
            logger.error("❌ Prerrequisitos no cumplidos. Corrija los problemas antes de ejecutar la migración.")
        return

    # Ejecutar migración
    try:
        success = migration.run_migration()
        if success:
            migration.save_results()
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n⏹️  Migración interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error inesperado en migración: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()