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
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import glob

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# psycopg2 eliminated - using native Docker implementation

# Import database configuration for Docker wrapper
try:
    from database_config import create_connection, load_database_config
except ImportError:
    print("WARNING: database_config not available, using direct connection")
    create_connection = None
    load_database_config = None

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
        self.raw_dir = self.data_dir / "raw" / "relevamiento"
        self.intermediate_dir = self.data_dir / "intermediate"

        # Find all raw Excel files
        self.excel_files = list(self.raw_dir.glob("*.xlsx"))
        if not self.excel_files:
            self.logger.warning(f"No raw Excel files found in {self.raw_dir}")
        else:
            self.logger.info(f"Found {len(self.excel_files)} raw Excel files")

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
            if self.dry_run:
                self.logger.info("DRY RUN: Would connect to database with params:")
                self.logger.info(f"  Host: localhost")
                self.logger.info(f"  Database: citrino")
                return True

            # Import here to avoid module loading issues
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
            try:
                from database_config import DockerPostgresConnection, DatabaseConfig
                # Create connection with hardcoded parameters that work
                config = DatabaseConfig(
                    host='localhost',
                    port=5432,
                    database='citrino',
                    user='citrino_app',
                    password='citrino_password'
                )
                self.db_connection = DockerPostgresConnection(config)
                self.logger.info("Successfully connected to PostgreSQL via hardcoded Docker wrapper")
            except Exception as config_error:
                self.logger.error(f"Failed to load Docker config: {config_error}")
                # Last resort - use subprocess directly
                raise Exception("All connection methods failed")

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

    def extract_properties_from_excel(self) -> List[Property]:
        """Extract properties from all intermediate Excel files"""
        self.logger.info(f"Processing {len(self.excel_files)} Excel files")

        properties = []

        for excel_file in self.excel_files:
            self.logger.info(f"Processing Excel file: {excel_file.name}")

            try:
                # Read Excel file
                df = pd.read_excel(excel_file)
                self.logger.info(f"Read {len(df)} rows from {excel_file.name}")

                # Map expected columns to standard names (based on real Excel structure)
                column_mapping = {
                    'Título': 'titulo',
                    'Titulo': 'titulo',
                    'título': 'titulo',
                    'titulo': 'titulo',
                    'Precio': 'precio_usd',
                    'precio': 'precio_usd',
                    'Descripción': 'descripcion',
                    'Descripcion': 'descripcion',
                    'descripción': 'descripcion',
                    'descripcion': 'descripcion',
                    'Agente': 'agente',
                    'agente': 'agente',
                    'URL': 'url',
                    'url': 'url',
                    'Latitud': 'latitud',
                    'latitud': 'latitud',
                    'Longitud': 'longitud',
                    'longitud': 'longitud',
                    'Habitaciones': 'num_dormitorios',
                    'habitaciones': 'num_dormitorios',
                    'Baños': 'num_banos',
                    'Banos': 'num_banos',
                    'baños': 'num_banos',
                    'Garajes': 'num_garajes',
                    'garajes': 'num_garajes',
                    'Sup. Terreno': 'superficie_total',
                    'Sup. Construida': 'superficie_construida',
                    'Teléfono': 'telefono',
                    'Telefono': 'telefono',
                    'teléfono': 'telefono',
                    'Correo': 'email',
                    'correo': 'email'
                }

                # Rename columns based on mapping
                df = df.rename(columns=column_mapping)

                # Process each row as a property
                file_properties = []
                for _, row in df.iterrows():
                    try:
                        property_data = row.to_dict()
                        property_obj = self.parse_property_data(property_data)
                        if property_obj:
                            file_properties.append(property_obj)
                            properties.append(property_obj)
                    except Exception as e:
                        self.logger.warning(f"Failed to parse property from {excel_file.name}: {e}")
                        self.stats['errors'] += 1

                self.logger.info(f"Processed {len(file_properties)} properties from {excel_file.name}")

                # Save to intermediate file for manual review
                self.save_to_intermediate_file(file_properties, excel_file.name)

            except Exception as e:
                self.logger.error(f"Error processing Excel file {excel_file.name}: {e}")
                self.stats['errors'] += 1
                continue

        self.stats['total_properties_processed'] = len(properties)
        self.logger.info(f"Total properties processed from all Excel files: {len(properties)}")

        return properties

    def extract_zona_from_text(self, text: str) -> Optional[str]:
        """Extract zone information from title or description"""
        if not text or not isinstance(text, str):
            return None

        text_lower = text.lower()

        # Zone patterns for Santa Cruz
        zone_patterns = [
            (r'equipetrol', 'Equipetrol'),
            (r'centro|centro histórico|plaza 24 de septiembre|plaza principal', 'Centro'),
            (r'primer anillo|1er anillo', '1er Anillo'),
            (r'segundo anillo|2do anillo', '2do Anillo'),
            (r'tercer anillo|3er anillo', '3er Anillo'),
            (r'cuarto anillo|4to anillo', '4to Anillo'),
            (r'quinto anillo|5to anillo', '5to Anillo'),
            (r'zona sur|sur', 'Zona Sur'),
            (r'zona norte|norte', 'Zona Norte'),
            (r'zona este|este', 'Zona Este'),
            (r'zona oeste|oeste', 'Zona Oeste'),
            (r'san martin|av\. san martín', 'Av. San Martín'),
            (r'melchor pinto|av\. melchor pinto', 'Av. Melchor Pinto'),
            (r'viedma|av\. viedma', 'Av. Viedma'),
            (r'radial', 'Radial'),
            (r'villa 1ro de mayo|primero de mayo', 'Villa 1ro de Mayo'),
            (r'barrio', 'Barrios'),
            (r'urb\.|urbanización', 'Urbanizaciones'),
            (r'country|condominio', 'Condominios'),
            (r'santa cruz de la sierra|santa cruz', 'Santa Cruz'),
            (r'plaza', 'Plaza'),
            (r'campero', 'Campero'),
            (r'el palmar', 'El Palmar'),
            (r'los lotes', 'Los Lotes'),
            (r'pampa de la isla', 'Pampa de la Isla'),
            (r'equipetrol sur', 'Equipetrol Sur'),
            (r'plan 3000', 'Plan 3000')
        ]

        for pattern, zone in zone_patterns:
            if re.search(pattern, text_lower):
                return zone

        return None

    def extract_tipo_propiedad_from_text(self, text: str) -> Optional[str]:
        """Extract property type from title or description"""
        if not text or not isinstance(text, str):
            return None

        text_lower = text.lower()

        # Property type patterns
        if re.search(r'departamento|depto|apartamento|apto', text_lower):
            return 'Departamento'
        elif re.search(r'casa|chalet|bungalow', text_lower):
            return 'Casa'
        elif re.search(r'terreno|lote|solar', text_lower):
            return 'Terreno'
        elif re.search(r'oficina|local comercial|local|negocio', text_lower):
            return 'Oficina/Local'
        elif re.search(r'galpón|depósito|almacén|bodega', text_lower):
            return 'Galpón/Depósito'
        elif re.search(r'finca|quinta|hacienda|campestre', text_lower):
            return 'Finca/Campestre'
        elif re.search(r'duplex|townhouse', text_lower):
            return 'Duplex/Townhouse'
        elif re.search(r'penthouse|ático', text_lower):
            return 'Penthouse'
        elif re.search(r'edificio|torre', text_lower):
            return 'Edificio/Torre'
        elif re.search(r'casa comercial', text_lower):
            return 'Casa Comercial'

        return None

    def parse_property_data(self, property_data: Dict[str, Any]) -> Optional[Property]:
        """Parse individual property data from Excel/JSON"""
        # Extract agent information (handle Excel vs JSON)
        agent_info = property_data.get('agente')
        agente_id = None

        # For Excel files, agent info might be in different fields or missing
        if agent_info:
            if isinstance(agent_info, str):
                agent_name = agent_info.strip().title()
                agente_id = self.agent_name_to_id.get(agent_name)
            elif isinstance(agent_info, dict):
                agent_name = agent_info.get('nombre', '').strip().title()
                agente_id = self.agent_name_to_id.get(agent_name)
        else:
            # Excel files might not have agent info - assign default or None
            agente_id = None

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
                    # Handle Excel NaN values
                    val = property_data[field]
                    if pd.isna(val) or val == '' or str(val).lower() in ['nan', 'none', 'null']:
                        continue
                    latitud = float(val)
                    break
                except (ValueError, TypeError):
                    continue

        for field in lon_fields:
            if field in property_data and property_data[field] is not None:
                try:
                    # Handle Excel NaN values
                    val = property_data[field]
                    if pd.isna(val) or val == '' or str(val).lower() in ['nan', 'none', 'null']:
                        continue
                    longitud = float(val)
                    break
                except (ValueError, TypeError):
                    continue

        # Extract and parse price
        precio_usd = None
        precio_fields = ['precio', 'precio_usd', 'price', 'precio_usd']

        for field in precio_fields:
            if field in property_data and property_data[field] is not None:
                val = property_data[field]
                # Handle Excel NaN values
                if pd.isna(val) or val == '' or str(val).lower() in ['nan', 'none', 'null']:
                    continue
                precio_usd = self.parse_price(val)
                if precio_usd is not None:
                    break

        # Parse numeric fields with Excel NaN handling
        superficie_total = self.parse_numeric_field(property_data.get('superficie_total'))
        superficie_construida = self.parse_numeric_field(property_data.get('superficie_construida'))
        num_dormitorios = self.parse_numeric_field(property_data.get('num_dormitorios'), integer=True)
        num_banos = self.parse_numeric_field(property_data.get('num_banos'), integer=True)
        num_garajes = self.parse_numeric_field(property_data.get('num_garajes'), integer=True)

        # Parse dates
        fecha_publicacion = self.parse_date(property_data.get('fecha_publicacion'))
        fecha_scraping = self.parse_date(property_data.get('fecha_scraping'))

        # Helper function to clean string values from Excel
        def clean_excel_value(val):
            if val is None:
                return None
            if hasattr(val, '__module__') and 'pandas' in str(type(val)):
                if pd.isna(val):
                    return None
            if isinstance(val, str):
                val = str(val).strip()
                if val.lower() in ['nan', 'none', 'null', '']:
                    return None
                return val
            return val

        # Extract title and description for intelligent parsing
        titulo = clean_excel_value(property_data.get('titulo')) or 'Sin título'
        descripcion = clean_excel_value(property_data.get('descripcion'))

        # Extract zone and type using intelligent parsing if not already present
        zona = clean_excel_value(property_data.get('zona'))
        if not zona:
            zona = self.extract_zona_from_text(titulo)
            if not zona:
                zona = self.extract_zona_from_text(descripcion)

        tipo_propiedad = clean_excel_value(property_data.get('tipo_propiedad'))
        if not tipo_propiedad:
            tipo_propiedad = self.extract_tipo_propiedad_from_text(titulo)
            if not tipo_propiedad:
                tipo_propiedad = self.extract_tipo_propiedad_from_text(descripcion)

        property_obj = Property(
            titulo=titulo,
            agente_id=agente_id,
            descripcion=descripcion,
            tipo_propiedad=tipo_propiedad,
            estado_propiedad=clean_excel_value(property_data.get('estado_propiedad')),
            precio_usd=precio_usd,
            direccion=clean_excel_value(property_data.get('direccion')),
            zona=zona,
            uv=clean_excel_value(property_data.get('uv')),
            manzana=clean_excel_value(property_data.get('manzana')),
            lote=clean_excel_value(property_data.get('lote')),
            superficie_total=superficie_total,
            superficie_construida=superficie_construida,
            num_dormitorios=num_dormitorios,
            num_banos=num_banos,
            num_garajes=num_garajes,
            latitud=latitud,
            longitud=longitud,
            fecha_publicacion=fecha_publicacion,
            fecha_scraping=fecha_scraping,
            proveedor_datos=clean_excel_value(property_data.get('proveedor_datos')) or 'excel_intermedio',
            codigo_proveedor=clean_excel_value(property_data.get('codigo_proveedor')),
            url_origen=clean_excel_value(property_data.get('url_origen'))
        )

        # Check coordinate validity
        if property_obj.is_valid_coordinates():
            self.stats['valid_coordinates_count'] += 1
        else:
            self.stats['invalid_coordinates_count'] += 1

        return property_obj

    def parse_price(self, price_value: Any) -> Optional[float]:
        """Parse price from various formats including '200,000 Usd'"""
        if price_value is None:
            return None

        # Handle Excel NaN
        if hasattr(price_value, '__module__') and 'pandas' in str(type(price_value)):
            if pd.isna(price_value):
                return None

        if isinstance(price_value, (int, float)):
            if pd.isna(price_value):
                return None
            return float(price_value)

        if isinstance(price_value, str):
            if price_value.strip() == '' or price_value.lower() in ['nan', 'none', 'null']:
                return None

            # Remove common price formatting but keep digits and commas/periods
            price_str = re.sub(r'[^\d.,]', '', price_value)

            # Handle Bolivian format: 200.000,00 or 200,000 USD
            if ',' in price_str and '.' in price_str:
                # If both exist, assume last is decimal separator
                if price_str.rfind(',') > price_str.rfind('.'):
                    price_str = price_str.replace('.', '').replace(',', '.')
                else:
                    price_str = price_str.replace(',', '')
            elif ',' in price_str:
                # Could be decimal separator or thousands
                if price_str.count(',') == 1 and len(price_str.split(',')[1]) <= 2:
                    price_str = price_str.replace(',', '.')
                else:
                    price_str = price_str.replace(',', '')

            try:
                return float(price_str)
            except ValueError:
                return None

        return None

    def parse_numeric_field(self, value: Any, integer: bool = False) -> Optional[float]:
        """Parse numeric field from various formats including Excel NaN"""
        if value is None:
            return None

        # Handle Excel NaN values
        if hasattr(value, '__module__') and 'pandas' in str(type(value)):
            if pd.isna(value):
                return None

        if isinstance(value, (int, float)):
            if pd.isna(value):
                return None
            return int(value) if integer else float(value)

        if isinstance(value, str):
            # Remove formatting characters
            if value.strip() == '' or value.lower() in ['nan', 'none', 'null']:
                return None
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
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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

            # Simple batch insertion using cursor.execute for each record
            inserted = 0
            updated = 0

            for prop_data in properties_data:
                try:
                    cursor.execute(insert_query, prop_data)
                    result = cursor.fetchone()
                    if result and result[1] == 'inserted':
                        inserted += 1
                    elif result and result[1] == 'updated':
                        updated += 1
                except Exception as e:
                    self.logger.warning(f"Failed to insert property: {e}")

            self.db_connection.commit()
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

            # Extract properties from Excel files
            properties = self.extract_properties_from_excel()

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

    def save_to_intermediate_file(self, properties: List[Property], original_filename: str):
        """Save processed properties to intermediate Excel file for manual review"""
        self.logger.info(f"Saving intermediate file for {original_filename}")

        # Create intermediate directory if it doesn't exist
        self.intermediate_dir.mkdir(exist_ok=True)

        # Generate intermediate filename
        intermediate_filename = original_filename.replace('.xlsx', '_intermedio.xlsx')
        intermediate_path = self.intermediate_dir / intermediate_filename

        # Prepare data for DataFrame
        intermediate_data = []
        for prop in properties:
            row = {
                'TÍTULO': prop.titulo,
                'DESCRIPCIÓN': prop.descripcion,
                'TIPO_PROPIEDAD': prop.tipo_propiedad,
                'ESTADO_PROPIEDAD': prop.estado_propiedad,
                'PRECIO_USD': prop.precio_usd,
                'PRECIO_USD_M2': prop.precio_usd_m2,
                'DIRECCIÓN': prop.direccion,
                'ZONA': prop.zona,
                'UV': prop.uv,
                'MANZANA': prop.manzana,
                'LOTE': prop.lote,
                'SUPERFICIE_TOTAL': prop.superficie_total,
                'SUPERFICIE_CONSTRUIDA': prop.superficie_construida,
                'NUM_DORMITORIOS': prop.num_dormitorios,
                'NUM_BAÑOS': prop.num_banos,
                'NUM_GARAJES': prop.num_garajes,
                'LATITUD': prop.latitud,
                'LONGITUD': prop.longitud,
                'COORDENADAS_POSTGIS': prop.coordenadas_postgis,
                'FECHA_PUBLICACIÓN': prop.fecha_publicacion,
                'FECHA_SCRAPING': prop.fecha_scraping,
                'PROVEEDOR_DATOS': prop.proveedor_datos,
                'CÓDIGO_PROVEEDOR': prop.codigo_proveedor,
                'URL_ORIGEN': prop.url_origen,
                'COORDENADAS_VÁLIDAS': prop.is_valid_coordinates(),
                'DATOS_COMPLETOS': bool(prop.precio_usd and prop.zona and prop.tipo_propiedad)
            }
            intermediate_data.append(row)

        # Create DataFrame
        df_intermediate = pd.DataFrame(intermediate_data)

        # Add validation columns
        df_intermediate['ESTADO'] = df_intermediate.apply(self._determine_property_status, axis=1)
        df_intermediate['OBSERVACIONES'] = df_intermediate.apply(self._generate_property_observations, axis=1)

        # Reorder columns to put validation first
        validation_cols = ['ESTADO', 'OBSERVACIONES']
        data_cols = [col for col in df_intermediate.columns if col not in validation_cols]
        df_intermediate = df_intermediate[validation_cols + data_cols]

        # Save to Excel
        try:
            df_intermediate.to_excel(intermediate_path, index=False, engine='openpyxl')
            self.logger.info(f"Saved intermediate file: {intermediate_path}")
            self.logger.info(f"Total properties in intermediate file: {len(df_intermediate)}")
            self.logger.info(f"Properties by status: {df_intermediate['ESTADO'].value_counts().to_dict()}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save intermediate file: {e}")
            return False

    def _determine_property_status(self, row) -> str:
        """Determine validation status for a property"""
        issues = []

        # Check title
        if not row['TÍTULO'] or pd.isna(row['TÍTULO']) or str(row['TÍTULO']).strip() == '':
            issues.append('Sin título')

        # Check coordinates
        if not row['LATITUD'] or not row['LONGITUD'] or pd.isna(row['LATITUD']) or pd.isna(row['LONGITUD']):
            issues.append('Sin coordenadas')
        elif not row['COORDENADAS_VÁLIDAS']:
            issues.append('Coordenadas fuera de rango')

        # Check price
        if not row['PRECIO_USD'] or pd.isna(row['PRECIO_USD']) or row['PRECIO_USD'] <= 0:
            issues.append('Sin precio o precio inválido')
        elif row['PRECIO_USD'] < 1000 or row['PRECIO_USD'] > 5000000:
            issues.append('Precio sospechoso')

        # Check zone
        if not row['ZONA'] or pd.isna(row['ZONA']) or str(row['ZONA']).strip() == '':
            issues.append('Sin zona')

        # Check property type
        if not row['TIPO_PROPIEDAD'] or pd.isna(row['TIPO_PROPIEDAD']) or str(row['TIPO_PROPIEDAD']).strip() == '':
            issues.append('Sin tipo de propiedad')

        if not issues:
            return 'OK'
        elif len(issues) <= 2:
            return 'WARNING'
        else:
            return 'ERROR'

    def _generate_property_observations(self, row) -> str:
        """Generate observations for property validation"""
        observations = []

        if not row['TÍTULO'] or pd.isna(row['TÍTULO']) or str(row['TÍTULO']).strip() == '':
            observations.append('Falta título')

        if not row['LATITUD'] or not row['LONGITUD'] or pd.isna(row['LATITUD']) or pd.isna(row['LONGITUD']):
            observations.append('Sin coordenadas')
        elif not row['COORDENADAS_VÁLIDAS']:
            observations.append('Coordenadas fuera de Santa Cruz')

        if not row['PRECIO_USD'] or pd.isna(row['PRECIO_USD']) or row['PRECIO_USD'] <= 0:
            observations.append('Precio inválido o faltante')
        elif row['PRECIO_USD'] < 1000:
            observations.append('Precio muy bajo (<$1,000)')
        elif row['PRECIO_USD'] > 5000000:
            observations.append('Precio muy alto (>$5M)')

        if not row['ZONA'] or pd.isna(row['ZONA']) or str(row['ZONA']).strip() == '':
            observations.append('Falta zona')

        if not row['TIPO_PROPIEDAD'] or pd.isna(row['TIPO_PROPIEDAD']) or str(row['TIPO_PROPIEDAD']).strip() == '':
            observations.append('Falta tipo de propiedad')

        if not row['DIRECCIÓN'] or pd.isna(row['DIRECCIÓN']) or str(row['DIRECCIÓN']).strip() == '':
            observations.append('Falta dirección')

        return '; '.join(observations) if observations else 'Sin observaciones'

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