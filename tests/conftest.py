"""
Configuración compartida de pytest y fixtures para pruebas.
"""

import pytest
import json
from pathlib import Path


@pytest.fixture(scope="session")
def project_root():
    """Retorna la ruta raíz del proyecto."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def data_dir(project_root):
    """Retorna el directorio de datos."""
    return project_root / "data"


@pytest.fixture(scope="session")
def test_data_dir():
    """Retorna el directorio de datos de prueba."""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def base_datos_relevamiento(data_dir):
    """Carga la base de datos de relevamiento completa."""
    file_path = data_dir / "base_datos_relevamiento.json"
    if not file_path.exists():
        pytest.skip(f"Archivo no encontrado: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture(scope="session")
def propiedades_relevamiento(base_datos_relevamiento):
    """Retorna solo la lista de propiedades del relevamiento."""
    return base_datos_relevamiento.get('propiedades', [])


@pytest.fixture
def propiedad_valida_sample():
    """Retorna una propiedad de muestra con todos los campos válidos."""
    return {
        'id': 'test_001',
        'titulo': 'Casa en venta zona norte',
        'tipo_propiedad': 'casa',
        'precio': 150000,
        'zona': 'Zona Norte',
        'direccion': 'Av. Principal 123',
        'latitud': -17.7833,
        'longitud': -63.1821,
        'superficie': 200,
        'superficie_terreno': 250,
        'superficie_construida': 200,
        'habitaciones': 3,
        'banos': 2,
        'garajes': 2,
        'descripcion': 'Hermosa casa en zona privilegiada',
        'fecha_relevamiento': '2025.01.15',
        'fuente': 'test_source.xlsx',
        'url': 'http://example.com/prop/001'
    }


@pytest.fixture
def propiedad_incompleta_sample():
    """Retorna una propiedad de muestra con campos faltantes."""
    return {
        'id': 'test_002',
        'titulo': '',  # Vacío
        'tipo_propiedad': 'departamento',
        'precio': None,  # Faltante
        'zona': '',  # Vacío
        'latitud': -17.7833,
        'longitud': -63.1821,
        'superficie': None,
        'habitaciones': None,
        'banos': None
    }


@pytest.fixture
def propiedad_coordenadas_invalidas_sample():
    """Retorna una propiedad con coordenadas fuera de rango."""
    return {
        'id': 'test_003',
        'tipo_propiedad': 'casa',
        'latitud': -25.0,  # Fuera de rango Santa Cruz
        'longitud': -70.0,  # Fuera de rango Santa Cruz
        'precio': 100000
    }


@pytest.fixture
def calidad_umbrales():
    """Define los umbrales mínimos de calidad de datos."""
    return {
        'coordenadas_validas_min': 0.85,  # 85% mínimo
        'con_zona_min': 0.70,  # 70% mínimo
        'con_precio_min': 0.80,  # 80% mínimo
        'con_tipo_propiedad_min': 0.90,  # 90% mínimo
        'duplicados_max': 0.05,  # 5% máximo
        'coordenadas_fuera_rango_max': 0.02  # 2% máximo
    }


@pytest.fixture
def santa_cruz_bounds():
    """Define los límites geográficos de Santa Cruz de la Sierra."""
    return {
        'lat_min': -18.5,
        'lat_max': -17.0,
        'lon_min': -64.0,
        'lon_max': -62.5
    }
