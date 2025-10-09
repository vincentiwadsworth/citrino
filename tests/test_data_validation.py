"""
Pruebas de validación de calidad e integridad de datos.
Estas pruebas validan que los datos cargados cumplan con umbrales mínimos de calidad.
"""

import pytest
from collections import defaultdict


class TestCalidadDatos:
    """Suite de pruebas de calidad de datos."""

    def test_archivo_existe(self, base_datos_relevamiento):
        """Verifica que el archivo de datos existe y se puede cargar."""
        assert base_datos_relevamiento is not None
        assert 'propiedades' in base_datos_relevamiento
        assert 'metadata' in base_datos_relevamiento

    def test_cantidad_propiedades(self, propiedades_relevamiento):
        """Verifica que hay propiedades en el dataset."""
        assert len(propiedades_relevamiento) > 0, "El dataset está vacío"
        assert len(propiedades_relevamiento) > 100, "Dataset muy pequeño (< 100 propiedades)"

    def test_estructura_propiedades(self, propiedades_relevamiento):
        """Verifica que las propiedades tienen estructura básica."""
        sample = propiedades_relevamiento[0]
        campos_requeridos = ['id', 'tipo_propiedad']
        
        for campo in campos_requeridos:
            assert campo in sample, f"Campo obligatorio '{campo}' faltante en estructura"

    @pytest.mark.parametrize("campo", [
        'precio', 'zona', 'latitud', 'longitud', 
        'tipo_propiedad', 'habitaciones', 'banos'
    ])
    def test_campos_criticos_no_todos_vacios(self, propiedades_relevamiento, campo):
        """Verifica que los campos críticos no están todos vacíos."""
        con_valor = sum(
            1 for p in propiedades_relevamiento 
            if p.get(campo) is not None and p.get(campo) != ''
        )
        
        porcentaje = (con_valor / len(propiedades_relevamiento)) * 100
        
        # Al menos 5% debe tener el campo (muy bajo, pero establece piso)
        assert con_valor > 0, f"Campo '{campo}' está completamente vacío"
        assert porcentaje >= 5, f"Campo '{campo}' tiene solo {porcentaje:.1f}% de cobertura (< 5%)"


class TestCoordenadasGeograficas:
    """Pruebas de validación de coordenadas geográficas."""

    def test_coordenadas_presentes_umbral(self, propiedades_relevamiento, calidad_umbrales):
        """Verifica que un % mínimo de propiedades tiene coordenadas."""
        con_coords = sum(
            1 for p in propiedades_relevamiento
            if p.get('latitud') and p.get('longitud')
        )
        
        porcentaje = con_coords / len(propiedades_relevamiento)
        umbral = calidad_umbrales['coordenadas_validas_min']
        
        assert porcentaje >= umbral, \
            f"Solo {porcentaje:.1%} propiedades con coordenadas (mínimo: {umbral:.1%})"

    def test_coordenadas_dentro_santa_cruz(self, propiedades_relevamiento, santa_cruz_bounds):
        """Verifica que las coordenadas válidas están dentro de Santa Cruz."""
        fuera_rango = 0
        total_con_coords = 0
        
        for prop in propiedades_relevamiento:
            lat = prop.get('latitud')
            lon = prop.get('longitud')
            
            if lat and lon:
                total_con_coords += 1
                try:
                    lat = float(lat)
                    lon = float(lon)
                    
                    if not (santa_cruz_bounds['lat_min'] <= lat <= santa_cruz_bounds['lat_max']):
                        fuera_rango += 1
                    elif not (santa_cruz_bounds['lon_min'] <= lon <= santa_cruz_bounds['lon_max']):
                        fuera_rango += 1
                except (ValueError, TypeError):
                    fuera_rango += 1
        
        if total_con_coords > 0:
            porcentaje_fuera = fuera_rango / total_con_coords
            assert porcentaje_fuera <= 0.02, \
                f"{porcentaje_fuera:.1%} coordenadas fuera de rango Santa Cruz (máx: 2%)"

    def test_coordenadas_formato_valido(self, propiedades_relevamiento):
        """Verifica que las coordenadas tienen formato numérico válido."""
        coordenadas_invalidas = 0
        
        for prop in propiedades_relevamiento:
            lat = prop.get('latitud')
            lon = prop.get('longitud')
            
            if lat is not None or lon is not None:
                try:
                    if lat is not None:
                        float(lat)
                    if lon is not None:
                        float(lon)
                except (ValueError, TypeError):
                    coordenadas_invalidas += 1
        
        assert coordenadas_invalidas == 0, \
            f"{coordenadas_invalidas} propiedades con coordenadas no numéricas"


class TestZonasYUbicaciones:
    """Pruebas de validación de zonas y ubicaciones."""

    def test_zonas_presentes_minimo(self, propiedades_relevamiento):
        """Verifica que hay múltiples zonas en el dataset."""
        zonas = set()
        
        for prop in propiedades_relevamiento:
            zona = prop.get('zona', '').strip()
            if zona:
                zonas.add(zona)
        
        # Debe haber al menos 5 zonas diferentes
        assert len(zonas) >= 5, \
            f"Solo {len(zonas)} zonas únicas (esperado: ≥5 para diversidad)"

    def test_distribucion_zonas_no_monopolizada(self, propiedades_relevamiento):
        """Verifica que ninguna zona domina completamente el dataset."""
        zonas_count = defaultdict(int)
        total_con_zona = 0
        
        for prop in propiedades_relevamiento:
            zona = prop.get('zona', '').strip()
            if zona:
                zonas_count[zona] += 1
                total_con_zona += 1
        
        if total_con_zona > 0 and zonas_count:
            zona_mas_frecuente = max(zonas_count.values())
            porcentaje_mayor = zona_mas_frecuente / total_con_zona
            
            # Ninguna zona debe tener más del 50% del total
            assert porcentaje_mayor < 0.5, \
                f"Una zona representa {porcentaje_mayor:.1%} del dataset (monopolio de datos)"


class TestPrecios:
    """Pruebas de validación de precios."""

    def test_precios_en_rango_razonable(self, propiedades_relevamiento):
        """Verifica que los precios están en rangos razonables."""
        precios_extremos = []
        
        for prop in propiedades_relevamiento:
            precio = prop.get('precio')
            if precio is not None:
                try:
                    precio = float(precio)
                    # Rango razonable: $10k - $5M USD
                    if precio < 10000 or precio > 5000000:
                        precios_extremos.append(precio)
                except (ValueError, TypeError):
                    pass
        
        total_precios = sum(1 for p in propiedades_relevamiento if p.get('precio'))
        
        if total_precios > 0:
            porcentaje_extremos = len(precios_extremos) / total_precios
            # Máximo 10% de precios extremos
            assert porcentaje_extremos <= 0.10, \
                f"{porcentaje_extremos:.1%} precios fuera de rango razonable ($10k-$5M)"

    def test_precios_no_negativos(self, propiedades_relevamiento):
        """Verifica que no hay precios negativos."""
        precios_negativos = []
        
        for prop in propiedades_relevamiento:
            precio = prop.get('precio')
            if precio is not None:
                try:
                    precio = float(precio)
                    if precio < 0:
                        precios_negativos.append({
                            'id': prop.get('id'),
                            'precio': precio
                        })
                except (ValueError, TypeError):
                    pass
        
        assert len(precios_negativos) == 0, \
            f"{len(precios_negativos)} propiedades con precio negativo"


class TestTiposPropiedades:
    """Pruebas de validación de tipos de propiedades."""

    def test_tipos_estandarizados(self, propiedades_relevamiento):
        """Verifica que los tipos de propiedad están medianamente estandarizados."""
        tipos = defaultdict(int)
        
        for prop in propiedades_relevamiento:
            tipo = prop.get('tipo_propiedad', '').strip()
            if tipo:
                tipos[tipo] += 1
        
        # Debe haber menos de 50 tipos únicos (indica estandarización)
        assert len(tipos) < 50, \
            f"{len(tipos)} tipos únicos (posible falta de estandarización)"

    def test_tipos_inconsistencia_mayusculas(self, propiedades_relevamiento):
        """Detecta inconsistencias por mayúsculas/minúsculas en tipos."""
        tipos_lower = defaultdict(list)
        
        for prop in propiedades_relevamiento:
            tipo = prop.get('tipo_propiedad', '').strip()
            if tipo:
                tipos_lower[tipo.lower()].append(tipo)
        
        # Buscar tipos que son iguales pero con diferente capitalización
        inconsistencias = []
        for tipo_lower, variantes in tipos_lower.items():
            if len(set(variantes)) > 1:
                inconsistencias.append({
                    'tipo_base': tipo_lower,
                    'variantes': list(set(variantes))
                })
        
        # Advertencia si hay más de 5 inconsistencias
        if len(inconsistencias) > 5:
            pytest.warns(
                UserWarning,
                match=f"{len(inconsistencias)} tipos con inconsistencias de capitalización"
            )


class TestDuplicados:
    """Pruebas de detección de duplicados."""

    def test_duplicados_por_coordenadas(self, propiedades_relevamiento):
        """Verifica que no hay muchos duplicados exactos por coordenadas."""
        coordenadas_map = defaultdict(list)
        
        for prop in propiedades_relevamiento:
            lat = prop.get('latitud')
            lon = prop.get('longitud')
            
            if lat and lon:
                try:
                    clave = (round(float(lat), 6), round(float(lon), 6))
                    coordenadas_map[clave].append(prop.get('id'))
                except (ValueError, TypeError):
                    pass
        
        duplicados = {k: v for k, v in coordenadas_map.items() if len(v) > 1}
        total_duplicados = sum(len(v) for v in duplicados.values())
        
        if len(propiedades_relevamiento) > 0:
            porcentaje = total_duplicados / len(propiedades_relevamiento)
            # Máximo 5% de duplicados
            assert porcentaje <= 0.05, \
                f"{porcentaje:.1%} propiedades duplicadas por coordenadas (máx: 5%)"

    def test_ids_unicos(self, propiedades_relevamiento):
        """Verifica que todos los IDs son únicos."""
        ids = [p.get('id') for p in propiedades_relevamiento]
        ids_unicos = set(ids)
        
        assert len(ids) == len(ids_unicos), \
            f"Hay {len(ids) - len(ids_unicos)} IDs duplicados"


class TestIntegridadReferencial:
    """Pruebas de integridad referencial y consistencia."""

    def test_propiedades_con_precio_tienen_tipo(self, propiedades_relevamiento):
        """Propiedades con precio deben tener tipo definido."""
        sin_tipo_con_precio = []
        
        for prop in propiedades_relevamiento:
            if prop.get('precio') and not prop.get('tipo_propiedad'):
                sin_tipo_con_precio.append(prop.get('id'))
        
        total_con_precio = sum(1 for p in propiedades_relevamiento if p.get('precio'))
        
        if total_con_precio > 0:
            porcentaje = len(sin_tipo_con_precio) / total_con_precio
            # Máximo 5% sin tipo pero con precio
            assert porcentaje <= 0.05, \
                f"{porcentaje:.1%} propiedades con precio pero sin tipo"

    def test_metadata_actualizada(self, base_datos_relevamiento):
        """Verifica que los metadatos coinciden con los datos."""
        metadata = base_datos_relevamiento.get('metadata', {})
        propiedades = base_datos_relevamiento.get('propiedades', [])
        
        total_declarado = metadata.get('total_propiedades', 0)
        total_real = len(propiedades)
        
        assert total_declarado == total_real, \
            f"Metadata indica {total_declarado} propiedades pero hay {total_real}"


# Pruebas de regresión para monitorear empeoramiento
class TestRegresionCalidad:
    """Pruebas que monitorean si la calidad empeora."""

    @pytest.mark.regression
    def test_calidad_no_empeora_zona(self, propiedades_relevamiento):
        """La cobertura de zona no debe bajar del baseline actual."""
        con_zona = sum(1 for p in propiedades_relevamiento if p.get('zona', '').strip())
        porcentaje = con_zona / len(propiedades_relevamiento)
        
        # Baseline actual: 6% (muy bajo, pero no debe empeorar)
        assert porcentaje >= 0.05, \
            f"Calidad de zona empeoró: {porcentaje:.1%} (baseline: 6%)"

    @pytest.mark.regression
    def test_calidad_no_empeora_precio(self, propiedades_relevamiento):
        """La cobertura de precio no debe bajar del baseline actual."""
        con_precio = sum(1 for p in propiedades_relevamiento if p.get('precio'))
        porcentaje = con_precio / len(propiedades_relevamiento)
        
        # Baseline actual: 14.4%
        assert porcentaje >= 0.14, \
            f"Calidad de precio empeoró: {porcentaje:.1%} (baseline: 14.4%)"

    @pytest.mark.regression
    def test_calidad_no_empeora_coordenadas(self, propiedades_relevamiento):
        """La cobertura de coordenadas no debe bajar del baseline actual."""
        con_coords = sum(
            1 for p in propiedades_relevamiento
            if p.get('latitud') and p.get('longitud')
        )
        porcentaje = con_coords / len(propiedades_relevamiento)
        
        # Baseline actual: 96%
        assert porcentaje >= 0.95, \
            f"Calidad de coordenadas empeoró: {porcentaje:.1%} (baseline: 96%)"
