"""
Test de validación para submódulos en CompositeModule.
Verifica que se pueden crear jerarquías anidadas de módulos.
"""

import sys
from pathlib import Path
import json

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from iac_patterns.factory import NullResourceFactory
from iac_patterns.composite import CompositeModule

def test_basic_submodule():
    """Valida agregación básica de submódulos"""

    print("=== Test 1: Agregación básica de submódulos ===\n")

    # Crear módulo raíz
    root = CompositeModule(name="infrastructure")

    # Crear submódulo de red
    network_module = CompositeModule(name="network")
    network_module.add(NullResourceFactory.create("vpc"))
    network_module.add(NullResourceFactory.create("subnet"))

    # Crear submódulo de aplicación
    app_module = CompositeModule(name="application")
    app_module.add(NullResourceFactory.create("web_server"))
    app_module.add(NullResourceFactory.create("api_server"))

    # Agregar submódulos al raíz
    root.add_submodule(network_module)
    root.add_submodule(app_module)

    print(f"✓ Módulo raíz: {root}")
    print(f"✓ Submódulo network: {network_module}")
    print(f"✓ Submódulo application: {app_module}")

    # Exportar y validar
    exported = root.export()
    print(f"\n✓ Recursos totales exportados: {len(exported['resource'])}")

    assert len(exported["resource"]) == 4, f"❌ Esperaba 4 recursos, obtuvo {len(exported['resource'])}"
    assert root.count_resources() == 4, f"❌ count_resources() incorrecto: {root.count_resources()}"

    print("✅ Validación exitosa: submódulos básicos funcionan")

def test_nested_hierarchy():
    """Valida jerarquías multinivel"""

    print("\n=== Test 2: Jerarquías multinivel ===\n")

    # Nivel 1: Root
    root = CompositeModule(name="cloud_infrastructure")

    # Nivel 2: Regiones
    us_east = CompositeModule(name="us-east-1")
    us_west = CompositeModule(name="us-west-2")

    # Nivel 3: Servicios en us-east-1
    us_east_compute = CompositeModule(name="compute")
    us_east_compute.add(NullResourceFactory.create("ec2_1"))
    us_east_compute.add(NullResourceFactory.create("ec2_2"))

    us_east_storage = CompositeModule(name="storage")
    us_east_storage.add(NullResourceFactory.create("s3_bucket"))

    # Nivel 3: Servicios en us-west-2
    us_west_compute = CompositeModule(name="compute")
    us_west_compute.add(NullResourceFactory.create("ec2_3"))

    # Construir jerarquía
    us_east.add_submodule(us_east_compute)
    us_east.add_submodule(us_east_storage)
    us_west.add_submodule(us_west_compute)

    root.add_submodule(us_east)
    root.add_submodule(us_west)

    print(f"✓ Estructura creada:")
    print(f"  └─ {root}")
    print(f"     ├─ {us_east}")
    print(f"     │  ├─ {us_east_compute}")
    print(f"     │  └─ {us_east_storage}")
    print(f"     └─ {us_west}")
    print(f"        └─ {us_west_compute}")

    # Validar conteo recursivo
    assert root.count_resources() == 4, f"❌ Total de recursos incorrecto: {root.count_resources()}"
    assert us_east.count_resources() == 3, f"❌ us-east recursos incorrectos: {us_east.count_resources()}"
    assert us_west.count_resources() == 1, f"❌ us-west recursos incorrectos: {us_west.count_resources()}"

    print(f"\n✓ Total de recursos: {root.count_resources()}")
    print("✅ Validación exitosa: jerarquías multinivel funcionan")

def test_mixed_content():
    """Valida mezcla de recursos y submódulos"""

    print("\n=== Test 3: Recursos y submódulos mezclados ===\n")

    # Módulo que contiene tanto recursos directos como submódulos
    mixed = CompositeModule(name="mixed_module")

    # Agregar recurso directo
    mixed.add(NullResourceFactory.create("direct_resource"))

    # Agregar submódulo
    sub = CompositeModule(name="submodule")
    sub.add(NullResourceFactory.create("sub_resource_1"))
    sub.add(NullResourceFactory.create("sub_resource_2"))
    mixed.add_submodule(sub)

    # Agregar otro recurso directo
    mixed.add(NullResourceFactory.create("another_direct"))

    print(f"✓ Módulo mixto: {mixed}")
    print(f"  - Recursos directos: 2")
    print(f"  - Submódulos: 1 (con 2 recursos)")

    assert mixed.count_resources() == 4, f"❌ Conteo incorrecto: {mixed.count_resources()}"

    exported = mixed.export()
    assert len(exported["resource"]) == 4, f"❌ Exportación incorrecta"

    print("✅ Validación exitosa: contenido mixto funciona")

def test_export_structure():
    """Valida que la estructura exportada es válida para Terraform"""

    print("\n=== Test 4: Estructura exportada válida ===\n")

    root = CompositeModule(name="test")

    sub1 = CompositeModule(name="sub1")
    sub1.add(NullResourceFactory.create("res1"))
    sub1.add(NullResourceFactory.create("res2"))

    sub2 = CompositeModule(name="sub2")
    sub2.add(NullResourceFactory.create("res3"))

    root.add_submodule(sub1)
    root.add_submodule(sub2)

    exported = root.export()

    print("✓ Estructura exportada:")
    print(json.dumps(exported, indent=2)[:500] + "...")

    # Validar estructura
    assert "resource" in exported, "❌ Falta clave 'resource'"
    assert isinstance(exported["resource"], list), "❌ 'resource' no es lista"
    assert len(exported["resource"]) == 3, "❌ Cantidad de recursos incorrecta"

    # Validar que cada recurso tiene la estructura correcta
    for resource in exported["resource"]:
        assert "null_resource" in resource, "❌ Falta 'null_resource' en recurso"

    print("\n✅ Validación exitosa: estructura Terraform válida")

def test_empty_submodules():
    """Valida manejo de submódulos vacíos"""

    print("\n=== Test 5: Submódulos vacíos ===\n")

    root = CompositeModule(name="root")

    empty1 = CompositeModule(name="empty1")
    empty2 = CompositeModule(name="empty2")

    root.add_submodule(empty1)
    root.add_submodule(empty2)
    root.add(NullResourceFactory.create("solo_resource"))

    print(f"✓ Root con 2 submódulos vacíos y 1 recurso: {root}")

    assert root.count_resources() == 1, f"❌ Debería tener 1 recurso: {root.count_resources()}"

    exported = root.export()
    assert len(exported["resource"]) == 1, "❌ Exportación incorrecta"

    print("✅ Validación exitosa: submódulos vacíos se manejan correctamente")

if __name__ == "__main__":
    test_basic_submodule()
    test_nested_hierarchy()
    test_mixed_content()
    test_export_structure()
    test_empty_submodules()

    print("\n" + "="*50)
    print("✅ TODOS LOS TESTS PASARON CORRECTAMENTE")
    print("="*50)
