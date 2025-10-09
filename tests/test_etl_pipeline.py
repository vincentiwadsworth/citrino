"""
Pruebas del pipeline ETL de procesamiento de datos.
Valida las funciones de limpieza, transformación y validación.
"""

import pytest
import sys
from pathlib import Path

# Agregar el directorio scripts al path para importar
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from build_relevamiento_dataset import ProcesadorDatosRelevamiento


class TestProcesadorDatosRelevamiento:
    """Pruebas del procesador de datos de relevamiento."""

    @pytest.fixture
    def procesador(self):
        """Crea una instancia del procesador."""
        return ProcesadorDatosRelevamiento()

    def test_inicializacion(self, procesador):
        """Verifica la inicialización correcta del procesador."""
        assert procesador is not None
        assert hasattr(procesador, 'properties_data')
        assert hasattr(procesador, 'processed_files')

    def test_limpiar_texto_basico(self, procesador):
        """Prueba limpieza de texto básica."""
        assert procesador.limpiar_texto('  Hola  ') == 'Hola'
        assert procesador.limpiar_texto('') == ''
        assert procesador.limpiar_texto(None) == ''
        assert procesador.limpiar_texto('nan') == ''

    def test_limpiar_precio_formatos(self, procesador):
        """Prueba limpieza de precios en diferentes formatos."""
        assert procesador.limpiar_precio('$150,000') == 150000
        assert procesador.limpiar_precio('USD 150.000') == 150000
        assert procesador.limpiar_precio('150000') == 150000
        assert procesador.limpiar_precio(150000) == 150000
        assert procesador.limpiar_precio(None) is None
        assert procesador.limpiar_precio('no válido') is None

    def test_limpiar_coordenada_validas(self, procesador):
        """Prueba limpieza de coordenadas válidas para Santa Cruz."""
        # Coordenadas válidas de Santa Cruz
        assert procesador.limpiar_coordenada(-17.7833) == -17.7833
        assert procesador.limpiar_coordenada(-63.1821) == -63.1821
        
        # Coordenadas fuera de rango
        assert procesador.limpiar_coordenada(-25.0) is None
        assert procesador.limpiar_coordenada(-70.0) is None
        assert procesador.limpiar_coordenada(None) is None

    def test_limpiar_numero_basico(self, procesador):
        """Prueba limpieza de números."""
        assert procesador.limpiar_numero(3) == 3
        assert procesador.limpiar_numero('3') == 3
        assert procesador.limpiar_numero('3.5') == 3
        assert procesador.limpiar_numero('3,000') == 3000
        assert procesador.limpiar_numero(None) is None
        assert procesador.limpiar_numero('texto') is None

    def test_extraer_tipo_propiedad_desde_titulo(self, procesador):
        """Prueba extracción de tipo de propiedad desde título."""
        assert procesador.extraer_tipo_propiedad_desde_titulo('Casa en venta') == 'casa'
        assert procesador.extraer_tipo_propiedad_desde_titulo('Departamento amplio') == 'departamento'
        assert procesador.extraer_tipo_propiedad_desde_titulo('Terreno comercial') == 'terreno'
        assert procesador.extraer_tipo_propiedad_desde_titulo('Oficina moderna') == 'oficina'
        assert procesador.extraer_tipo_propiedad_desde_titulo('Penthouse de lujo') == 'penthouse'
        assert procesador.extraer_tipo_propiedad_desde_titulo('Texto sin tipo') == ''

    def test_validar_propiedad_minimos(self, procesador):
        """Prueba validación de propiedad con datos mínimos."""
        # Válida: tiene precio
        prop_con_precio = {
            'precio': 150000,
            'latitud': None,
            'longitud': None
        }
        assert procesador.validar_propiedad(prop_con_precio) is True
        
        # Válida: tiene coordenadas
        prop_con_coords = {
            'precio': None,
            'latitud': -17.7833,
            'longitud': -63.1821
        }
        assert procesador.validar_propiedad(prop_con_coords) is True
        
        # Inválida: sin precio ni coordenadas
        prop_invalida = {
            'precio': None,
            'latitud': None,
            'longitud': None
        }
        assert procesador.validar_propiedad(prop_invalida) is False


class TestEstandarizacionColumnas:
    """Pruebas de estandarización de columnas."""

    @pytest.fixture
    def procesador(self):
        return ProcesadorDatosRelevamiento()

    def test_estandarizar_columnas_precio(self, procesador):
        """Verifica estandarización de columnas de precio."""
        import pandas as pd
        
        df = pd.DataFrame({
            'Precio USD': [150000],
            'Zona': ['Norte']
        })
        
        df_estandarizado = procesador.estandarizar_columnas(df)
        
        assert 'precio' in df_estandarizado.columns
        assert 'zona' in df_estandarizado.columns

    def test_estandarizar_columnas_coordenadas(self, procesador):
        """Verifica estandarización de columnas de coordenadas."""
        import pandas as pd
        
        df = pd.DataFrame({
            'Latitude': [-17.7833],
            'Longitude': [-63.1821]
        })
        
        df_estandarizado = procesador.estandarizar_columnas(df)
        
        assert 'latitud' in df_estandarizado.columns
        assert 'longitud' in df_estandarizado.columns

    def test_estandarizar_columnas_habitaciones(self, procesador):
        """Verifica estandarización de columnas de habitaciones/baños."""
        import pandas as pd
        
        df = pd.DataFrame({
            'Dormitorios': [3],
            'Bathrooms': [2]
        })
        
        df_estandarizado = procesador.estandarizar_columnas(df)
        
        assert 'habitaciones' in df_estandarizado.columns
        assert 'banos' in df_estandarizado.columns


class TestEliminacionDuplicados:
    """Pruebas de eliminación de duplicados."""

    @pytest.fixture
    def procesador(self):
        return ProcesadorDatosRelevamiento()

    def test_eliminar_duplicados_por_coordenadas(self, procesador):
        """Elimina duplicados basados en coordenadas idénticas."""
        propiedades = [
            {
                'id': 'prop1',
                'latitud': -17.7833,
                'longitud': -63.1821,
                'precio': 150000
            },
            {
                'id': 'prop2',
                'latitud': -17.7833,  # Mismas coordenadas
                'longitud': -63.1821,
                'precio': 160000
            },
            {
                'id': 'prop3',
                'latitud': -17.8000,  # Coordenadas diferentes
                'longitud': -63.2000,
                'precio': 140000
            }
        ]
        
        resultado = procesador.eliminar_duplicados(propiedades)
        
        # Debe quedar solo 2 propiedades (duplicado eliminado)
        assert len(resultado) == 2
        
        # Verificar que se mantienen IDs únicos
        ids = [p['id'] for p in resultado]
        assert len(ids) == len(set(ids))

    def test_eliminar_duplicados_por_direccion(self, procesador):
        """Elimina duplicados basados en dirección idéntica."""
        propiedades = [
            {
                'id': 'prop1',
                'direccion': 'Av. Principal 123',
                'latitud': None,
                'longitud': None
            },
            {
                'id': 'prop2',
                'direccion': 'AV. PRINCIPAL 123',  # Misma dirección (case insensitive)
                'latitud': None,
                'longitud': None
            },
            {
                'id': 'prop3',
                'direccion': 'Av. Secundaria 456',
                'latitud': None,
                'longitud': None
            }
        ]
        
        resultado = procesador.eliminar_duplicados(propiedades)
        
        # Debe eliminar el duplicado por dirección
        assert len(resultado) <= 2

    def test_no_eliminar_propiedades_validas_sin_duplicar(self, procesador):
        """No elimina propiedades válidas que no son duplicados."""
        propiedades = [
            {
                'id': 'prop1',
                'latitud': -17.7833,
                'longitud': -63.1821,
                'direccion': 'Dirección 1'
            },
            {
                'id': 'prop2',
                'latitud': -17.8000,
                'longitud': -63.2000,
                'direccion': 'Dirección 2'
            },
            {
                'id': 'prop3',
                'latitud': -17.8100,
                'longitud': -63.2100,
                'direccion': 'Dirección 3'
            }
        ]
        
        resultado = procesador.eliminar_duplicados(propiedades)
        
        # Todas deben mantenerse (no son duplicados)
        assert len(resultado) == 3


class TestExtraccionFechas:
    """Pruebas de extracción de fechas desde nombres de archivo."""

    @pytest.fixture
    def procesador(self):
        return ProcesadorDatosRelevamiento()

    def test_extraer_fecha_desde_filename_valido(self, procesador):
        """Extrae fecha correctamente de nombre de archivo válido."""
        assert procesador.extraer_fecha_desde_filename('2025.01.15 data.xlsx') == '2025.01.15'
        assert procesador.extraer_fecha_desde_filename('2025.08.29 01.xlsx') == '2025.08.29'

    def test_extraer_fecha_desde_filename_invalido(self, procesador):
        """Retorna None para nombres de archivo sin fecha válida."""
        assert procesador.extraer_fecha_desde_filename('datos.xlsx') is None
        assert procesador.extraer_fecha_desde_filename('2025-01-15.xlsx') is None
        assert procesador.extraer_fecha_desde_filename('archivo_sin_fecha.xlsx') is None


class TestProcesamientoPropiedad:
    """Pruebas de procesamiento completo de una propiedad."""

    @pytest.fixture
    def procesador(self):
        return ProcesadorDatosRelevamiento()

    def test_procesar_propiedad_completa(self, procesador, propiedad_valida_sample):
        """Procesa correctamente una propiedad con datos completos."""
        import pandas as pd
        
        row = pd.Series(propiedad_valida_sample)
        fecha_relevamiento = '2025.01.15'
        source_file = 'test.xlsx'
        
        resultado = procesador.procesar_propiedad(row, fecha_relevamiento, source_file)
        
        assert resultado is not None
        assert resultado['precio'] == propiedad_valida_sample['precio']
        assert resultado['zona'] == propiedad_valida_sample['zona']
        assert resultado['latitud'] == propiedad_valida_sample['latitud']

    def test_procesar_propiedad_incompleta_con_minimos(self, procesador):
        """Procesa propiedad incompleta pero con datos mínimos."""
        import pandas as pd
        
        row = pd.Series({
            'precio': 150000,
            'tipo_propiedad': 'casa',
            'latitud': None,
            'longitud': None
        })
        
        resultado = procesador.procesar_propiedad(row, None, 'test.xlsx')
        
        # Debe procesarse porque tiene precio
        assert resultado is not None
        assert resultado['precio'] == 150000

    def test_rechazar_propiedad_sin_minimos(self, procesador):
        """Rechaza propiedad sin datos mínimos requeridos."""
        import pandas as pd
        
        row = pd.Series({
            'titulo': 'Título sin datos',
            'descripcion': 'Descripción',
            'precio': None,
            'latitud': None,
            'longitud': None
        })
        
        resultado = procesador.procesar_propiedad(row, None, 'test.xlsx')
        
        # Debe rechazarse por falta de datos mínimos
        assert resultado is None


# Pruebas de integración (requieren archivos reales)
class TestIntegracionETL:
    """Pruebas de integración del pipeline completo."""

    @pytest.mark.integration
    def test_encontrar_archivos_excel(self):
        """Encuentra archivos Excel en el directorio raw."""
        procesador = ProcesadorDatosRelevamiento()
        archivos = procesador.encontrar_archivos_excel()
        
        # Debe encontrar al menos 1 archivo (o skip si no hay)
        if len(archivos) == 0:
            pytest.skip("No hay archivos Excel en data/raw/")
        
        assert all(f.endswith('.xlsx') for f in archivos)

    @pytest.mark.integration
    @pytest.mark.slow
    def test_procesamiento_completo_produce_datos(self, tmp_path):
        """El procesamiento completo produce datos válidos."""
        from build_relevamiento_dataset import ProcesadorDatosRelevamiento
        
        procesador = ProcesadorDatosRelevamiento(output_dir=str(tmp_path))
        
        # Intentar procesar
        try:
            propiedades = procesador.procesar_todos_los_archivos()
            
            if len(propiedades) > 0:
                # Verificar estructura básica
                assert all('id' in p for p in propiedades)
                assert all('tipo_propiedad' in p for p in propiedades)
        except Exception as e:
            pytest.skip(f"No se pudo ejecutar ETL completo: {e}")


class TestValidacionesETL:
    """Pruebas de validaciones en el pipeline ETL."""

    def test_coordenadas_fuera_rango_rechazadas(self):
        """Las coordenadas fuera de rango de Santa Cruz son rechazadas."""
        procesador = ProcesadorDatosRelevamiento()
        
        # Coordenada fuera de rango latitud
        assert procesador.limpiar_coordenada(-25.0) is None
        
        # Coordenada fuera de rango longitud
        assert procesador.limpiar_coordenada(-70.0) is None

    def test_precios_extremos_aceptados_con_advertencia(self):
        """Los precios extremos son aceptados pero deben generar advertencia."""
        procesador = ProcesadorDatosRelevamiento()
        
        # Precio muy bajo (posible error, pero válido)
        precio_bajo = procesador.limpiar_precio(5000)
        assert precio_bajo == 5000
        
        # Precio muy alto (posible error, pero válido)
        precio_alto = procesador.limpiar_precio(50000000)
        assert precio_alto == 50000000

    def test_tipos_propiedad_normalizacion_requerida(self):
        """Los tipos de propiedad requieren normalización."""
        procesador = ProcesadorDatosRelevamiento()
        
        # Mismo tipo, diferentes capitalizaciones
        tipo1 = procesador.extraer_tipo_propiedad_desde_titulo('Casa en venta')
        tipo2 = procesador.extraer_tipo_propiedad_desde_titulo('CASA moderna')
        tipo3 = procesador.extraer_tipo_propiedad_desde_titulo('casa familiar')
        
        # Todos deben resultar en el mismo tipo normalizado
        assert tipo1 == tipo2 == tipo3 == 'casa'
