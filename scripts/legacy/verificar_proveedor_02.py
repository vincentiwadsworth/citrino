import json

# Leer datos
with open('data/base_datos_relevamiento.json', encoding='utf-8') as f:
    data = json.load(f)

# Filtrar proveedor 02
props_02 = [p for p in data['propiedades'] if p.get('codigo_proveedor') == '02']

print(f"Total propiedades proveedor 02: {len(props_02)}")
print(f"\nVerificando primeras 5 propiedades:")
for i, prop in enumerate(props_02[:5]):
    desc = prop.get('descripcion', '')
    print(f"\n{i+1}. ID: {prop['id']}")
    print(f"   Tiene descripción: {'SÍ' if desc else 'NO'}")
    if desc:
        print(f"   Primeros 80 chars: {desc[:80]}...")
    print(f"   Código proveedor: {prop.get('codigo_proveedor')}")
