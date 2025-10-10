"""
Restricciones de datos y fuentes permitidas para Citrino
Control estricto para evitar uso de información no autorizada
"""

# Fuentes de datos permitidas y autorizadas
ALLOWED_DATA_SOURCES = {
    # Base de datos primaria (solo lectura)
    "primary_database": {
        "name": "base_datos_citrino_limpios.json",
        "path": "data/base_datos_relevamiento.json",
        "type": "json",
        "access": "readonly",
        "last_updated": "2025-10-09",
        "record_count": 1588,
        "validation_required": True
    },

    # Guía urbana municipal (solo lectura)
    "urban_guide": {
        "name": "guia_urbana_municipal_completa.json",
        "path": "data/guia_urbana_municipal_completa.json",
        "type": "json",
        "access": "readonly",
        "last_updated": "2025-10-09",
        "record_count": 4777,
        "validation_required": True
    }
}

# Datos estrictamente prohibidos
PROHIBITED_DATA = [
    # Información financiera personal
    "datos_bancarios_clientes",
    "informacion_crediticia",
    "historial_financiero",
    "datos_sensibles_clientes",

    # Información no verificada
    "rumores_mercado",
    "especulaciones_precios",
    "tendencias_no_confirmadas",
    "opiniones_sin_fuentes",

    # Proyecciones futuras
    "proyecciones_plusvalia",
    "predicciones_mercado",
    "estimaciones_futuras",
    "garantias_rentabilidad",

    # Datos de terceros no autorizados
    "informacion_competencia",
    "datos_proveedores_externos",
    "listados_otros_portales",
    "api_externas_no_autorizadas"
]

# Restricciones de zonas permitidas
ALLOWED_ZONES = {
    # Zonas principales con datos verificados
    "equipetrol": {
        "name": "Equipetrol",
        "status": "active",
        "price_range": {"min": 200000, "max": 800000},
        "property_types": ["departamento", "casa", "duplex"],
        "data_quality": "high",
        "last_updated": "2025-10-09"
    },

    "urbari": {
        "name": "Urbari",
        "status": "active",
        "price_range": {"min": 350000, "max": 1500000},
        "property_types": ["casa", "departamento", "terreno"],
        "data_quality": "high",
        "last_updated": "2025-10-09"
    },

    "santa_monica": {
        "name": "Santa Mónica",
        "status": "active",
        "price_range": {"min": 80000, "max": 400000},
        "property_types": ["terreno", "casa", "departamento"],
        "data_quality": "medium",
        "last_updated": "2025-10-09"
    },

    "las_palmas": {
        "name": "Las Palmas",
        "status": "active",
        "price_range": {"min": 150000, "max": 600000},
        "property_types": ["casa", "departamento"],
        "data_quality": "medium",
        "last_updated": "2025-10-09"
    },

    "santiago": {
        "name": "Santiago",
        "status": "active",
        "price_range": {"min": 100000, "max": 500000},
        "property_types": ["casa", "terreno", "departamento"],
        "data_quality": "medium",
        "last_updated": "2025-10-09"
    },

    "sacta": {
        "name": "Sacta",
        "status": "active",
        "price_range": {"min": 70000, "max": 300000},
        "property_types": ["terreno", "casa"],
        "data_quality": "low",
        "last_updated": "2025-10-09"
    },

    "pampa_de_la_isla": {
        "name": "Pampa de la Isla",
        "status": "active",
        "price_range": {"min": 60000, "max": 250000},
        "property_types": ["terreno", "casa"],
        "data_quality": "low",
        "last_updated": "2025-10-09"
    }
}

# Restricciones de tipos de propiedad
ALLOWED_PROPERTY_TYPES = {
    "casa": {
        "name": "Casa",
        "min_rooms": 1,
        "max_rooms": 6,
        "min_surface": 60,
        "max_surface": 1000,
        "price_range": {"min": 50000, "max": 2000000}
    },

    "departamento": {
        "name": "Departamento",
        "min_rooms": 1,
        "max_rooms": 4,
        "min_surface": 30,
        "max_surface": 300,
        "price_range": {"min": 50000, "max": 1000000}
    },

    "terreno": {
        "name": "Terreno",
        "min_rooms": 0,
        "max_rooms": 0,
        "min_surface": 100,
        "max_surface": 5000,
        "price_range": {"min": 30000, "max": 2000000}
    },

    "duplex": {
        "name": "Duplex",
        "min_rooms": 2,
        "max_rooms": 5,
        "min_surface": 80,
        "max_surface": 400,
        "price_range": {"min": 100000, "max": 1500000}
    },

    "loft": {
        "name": "Loft",
        "min_rooms": 1,
        "max_rooms": 2,
        "min_surface": 40,
        "max_surface": 200,
        "price_range": {"min": 80000, "max": 600000}
    }
}

# Restricciones de rangos de precios
PRICE_RESTRICTIONS = {
    "global": {
        "min_price": 50000,           # Precio mínimo global
        "max_price": 5000000,         # Precio máximo global
        "currency": "USD",            # Moneda permitida
        "inflation_adjustment": False # Sin ajuste por inflación
    },

    "by_property_type": {
        "casa": {"min": 50000, "max": 2000000},
        "departamento": {"min": 50000, "max": 1000000},
        "terreno": {"min": 30000, "max": 2000000},
        "duplex": {"min": 100000, "max": 1500000},
        "loft": {"min": 80000, "max": 600000}
    },

    "by_zone": {
        "equipetrol": {"min": 200000, "max": 800000},
        "urbari": {"min": 350000, "max": 1500000},
        "santa_monica": {"min": 80000, "max": 400000},
        "las_palmas": {"min": 150000, "max": 600000},
        "santiago": {"min": 100000, "max": 500000},
        "sacta": {"min": 70000, "max": 300000},
        "pampa_de_la_isla": {"min": 60000, "max": 250000}
    }
}

# Restricciones de características
CHARACTERISTIC_RESTRICTIONS = {
    "habitaciones": {
        "min": 0,
        "max": 6,
        "valid_values": [0, 1, 2, 3, 4, 5, 6]
    },

    "banos": {
        "min": 0,
        "max": 6,
        "valid_values": [0, 1, 2, 3, 4, 5, 6]
    },

    "superficie": {
        "min": 30,       # m² mínimo
        "max": 5000,     # m² máximo
        "unit": "m²"
    },

    "garajes": {
        "min": 0,
        "max": 4,
        "valid_values": [0, 1, 2, 3, 4]
    },

    "antiguedad": {
        "min": 0,        # años
        "max": 50,       # años máximo
        "unit": "años"
    }
}

# Palabras y frases prohibidas
FORBIDDEN_WORDS = {
    # Garantías y promesas
    "garantizado": ["garantizado", "garantía", "asegurado"],
    "seguro": ["seguro", "seguridad", "certeza"],
    "perfecto": ["perfecto", "perfectamente", "ideal"],
    "mejor": ["mejor", "el mejor", "la mejor"],

    # Especulaciones
    "plusvalia": ["plusvalía garantida", "rentabilidad segura", "inversión segura"],
    "futuro": ["futuro", "próximo", "vendrá"],
    "tendencia": ["tendencia alcista", "mercado en alza", "subirá de valor"],

    # Opiniones subjetivas
    "excelente": ["excelente", "excepcional", "extraordinario"],
    "increible": ["increíble", "asombroso", "maravilloso"],
    "unico": ["único", "exclusivo", "inigualable"],

    # Palabras de alta presión
    "urgente": ["urgente", "inmediato", "ahora"],
    "oportunidad": ["oportunidad única", "no te lo pierdas", "última chance"]
}

# Frases obligatorias (cuando aplica)
REQUIRED_PHRASES = {
    "no_data": [
        "No tengo información específica sobre esa consulta",
        "No dispongo de datos para esa solicitud",
        "La información que tengo es limitada para esa consulta"
    ],

    "data_source": [
        "Según nuestros datos",
        "En nuestra base de datos",
        "Basado en la información disponible"
    ],

    "uncertainty": [
        "Según los datos disponibles",
        "Con la información que tengo",
        "Basado en los registros existentes"
    ]
}

# Validación de datos en tiempo real
DATA_VALIDATION_RULES = {
    # Validación de propiedades
    "property_validation": {
        "required_fields": ["id", "precio", "zona", "tipo"],
        "field_types": {
            "id": "string",
            "precio": "number",
            "zona": "string",
            "tipo": "string",
            "habitaciones": "number",
            "superficie": "number"
        },
        "validation_functions": [
            "validate_price_range",
            "validate_zone_exists",
            "validate_property_type",
            "validate_characteristics"
        ]
    },

    # Validación de ubicaciones
    "location_validation": {
        "required_fields": ["zona", "latitud", "longitud"],
        "coordinate_ranges": {
            "latitud": {"min": -18.0, "max": -17.0},
            "longitud": {"min": -64.0, "max": -62.0}
        },
        "validation_functions": [
            "validate_coordinates",
            "validate_zone_in_boundaries",
            "validate_location_data"
        ]
    },

    # Validación de servicios
    "services_validation": {
        "required_fields": ["nombre", "categoria", "coordenadas"],
        "allowed_categories": [
            "educacion", "salud", "transporte", "abastecimiento",
            "deporte", "seguridad", "comercio", "otros"
        ],
        "validation_functions": [
            "validate_service_category",
            "validate_service_location",
            "validate_service_name"
        ]
    }
}

# Funciones de validación
class DataValidator:
    """Clase para validar datos según restricciones"""

    @staticmethod
    def validate_zone(zone_name: str) -> bool:
        """Valida que una zona exista en las zonas permitidas"""
        zone_key = zone_name.lower().replace(" ", "_")
        return zone_key in ALLOWED_ZONES

    @staticmethod
    def validate_property_type(prop_type: str) -> bool:
        """Valida que un tipo de propiedad exista"""
        type_key = prop_type.lower()
        return type_key in ALLOWED_PROPERTY_TYPES

    @staticmethod
    def validate_price(price: float, prop_type: str = None, zone: str = None) -> bool:
        """Valida que un precio esté en rangos permitidos"""
        global_min = PRICE_RESTRICTIONS["global"]["min_price"]
        global_max = PRICE_RESTRICTIONS["global"]["max_price"]

        if price < global_min or price > global_max:
            return False

        if prop_type and prop_type.lower() in PRICE_RESTRICTIONS["by_property_type"]:
            type_range = PRICE_RESTRICTIONS["by_property_type"][prop_type.lower()]
            if price < type_range["min"] or price > type_range["max"]:
                return False

        if zone and zone.lower() in PRICE_RESTRICTIONS["by_zone"]:
            zone_range = PRICE_RESTRICTIONS["by_zone"][zone.lower()]
            if price < zone_range["min"] or price > zone_range["max"]:
                return False

        return True

    @staticmethod
    def validate_characteristics(habitaciones: int, banos: int, superficie: float) -> bool:
        """Valida características de la propiedad"""
        char_restrictions = CHARACTERISTIC_RESTRICTIONS

        if not (char_restrictions["habitaciones"]["min"] <= habitaciones <= char_restrictions["habitaciones"]["max"]):
            return False

        if not (char_restrictions["banos"]["min"] <= banos <= char_restrictions["banos"]["max"]):
            return False

        if not (char_restrictions["superficie"]["min"] <= superficie <= char_restrictions["superficie"]["max"]):
            return False

        return True

    @staticmethod
    def check_forbidden_words(text: str) -> list:
        """Verifica si hay palabras prohibidas en el texto"""
        text_lower = text.lower()
        found_words = []

        for category, words in FORBIDDEN_WORDS.items():
            for word in words:
                if word in text_lower:
                    found_words.append({
                        "category": category,
                        "word": word,
                        "position": text_lower.find(word)
                    })

        return found_words

    @staticmethod
    def validate_property_data(property_data: dict) -> dict:
        """Valida datos completos de una propiedad"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        # Validar campos requeridos
        required_fields = DATA_VALIDATION_RULES["property_validation"]["required_fields"]
        for field in required_fields:
            if field not in property_data:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Campo requerido faltante: {field}")

        # Validar zona
        if "zona" in property_data:
            if not DataValidator.validate_zone(property_data["zona"]):
                validation_result["valid"] = False
                validation_result["errors"].append(f"Zona no permitida: {property_data['zona']}")

        # Validar tipo
        if "tipo" in property_data:
            if not DataValidator.validate_property_type(property_data["tipo"]):
                validation_result["valid"] = False
                validation_result["errors"].append(f"Tipo de propiedad no permitido: {property_data['tipo']}")

        # Validar precio
        if "precio" in property_data:
            zone = property_data.get("zona")
            prop_type = property_data.get("tipo")
            if not DataValidator.validate_price(property_data["precio"], prop_type, zone):
                validation_result["valid"] = False
                validation_result["errors"].append(f"Precio fuera de rango permitido: ${property_data['precio']}")

        return validation_result

# Funciones de utilidad
def get_allowed_zones() -> dict:
    """Retorna lista de zonas permitidas con sus características"""
    return ALLOWED_ZONES.copy()

def get_allowed_property_types() -> dict:
    """Retorna lista de tipos de propiedad permitidos"""
    return ALLOWED_PROPERTY_TYPES.copy()

def get_price_range(property_type: str = None, zone: str = None) -> dict:
    """Retorna rango de precios permitido"""
    if property_type and property_type.lower() in PRICE_RESTRICTIONS["by_property_type"]:
        return PRICE_RESTRICTIONS["by_property_type"][property_type.lower()]
    elif zone and zone.lower() in PRICE_RESTRICTIONS["by_zone"]:
        return PRICE_RESTRICTIONS["by_zone"][zone.lower()]
    else:
        return PRICE_RESTRICTIONS["global"]

def is_data_source_allowed(source: str) -> bool:
    """Verifica si una fuente de datos está permitida"""
    return source in ALLOWED_DATA_SOURCES

if __name__ == "__main__":
    # Mostrar resumen de restricciones
    print("=== RESTRICCIONES DE DATOS CITRINO ===")
    print(f"Fuentes permitidas: {len(ALLOWED_DATA_SOURCES)}")
    print(f"Zonas permitidas: {len(ALLOWED_ZONES)}")
    print(f"Tipos de propiedad: {len(ALLOWED_PROPERTY_TYPES)}")
    print(f"Categorías prohibidas: {len(FORBIDDEN_WORDS)}")
    print(f"Precio global: ${PRICE_RESTRICTIONS['global']['min_price']:,} - ${PRICE_RESTRICTIONS['global']['max_price']:,}")
    print("=" * 50)

    # Ejemplo de validación
    validator = DataValidator()
    test_property = {
        "id": "test_123",
        "precio": 280000,
        "zona": "Equipetrol",
        "tipo": "departamento",
        "habitaciones": 3,
        "superficie": 135
    }

    validation = validator.validate_property_data(test_property)
    print(f"\nValidación de propiedad de prueba: {'✅ VÁLIDA' if validation['valid'] else '❌ INVÁLIDA'}")
    if validation["errors"]:
        print("Errores:", validation["errors"])
    if validation["warnings"]:
        print("Advertencias:", validation["warnings"])