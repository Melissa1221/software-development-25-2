"""
Test de validación para mutadores de recursos.
Verifica que convert_null_to_local_file transforme correctamente los recursos.
"""

import sys
from pathlib import Path
import json

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from iac_patterns.factory import NullResourceFactory
from iac_patterns.prototype import ResourcePrototype
from iac_patterns.mutators import convert_null_to_local_file, rename_resource, add_trigger

def test_null_to_local_file():
    """Valida conversión de null_resource a local_file"""

    print("=== Test 1: Conversión null_resource → local_file ===\n")

    # Crear recurso null_resource base
    base = NullResourceFactory.create("app_server")
    print(f"✓ Recurso base (null_resource) creado:")
    print(json.dumps(base, indent=2))

    # Clonar y aplicar mutación
    proto = ResourcePrototype(base)
    cloned = proto.clone(lambda d: convert_null_to_local_file(
        d,
        filename="app_config.txt",
        content="Application configuration"
    ))

    print(f"\n✓ Recurso clonado y mutado (local_file):")
    print(json.dumps(cloned.data, indent=2))

    # Validaciones
    assert "resource" in cloned.data, "❌ Clave 'resource' no existe"

    resource_block = cloned.data["resource"][0]
    assert "local_file" in resource_block, "❌ No se creó local_file"
    assert "null_resource" not in resource_block, "❌ null_resource sigue presente"

    local_file = resource_block["local_file"][0]
    file_name = list(local_file.keys())[0]
    assert file_name == "app_server_file", f"❌ Nombre incorrecto: {file_name}"

    config = local_file[file_name][0]
    assert config["filename"] == "app_config.txt", "❌ filename incorrecto"
    assert config["content"] == "Application configuration", "❌ content incorrecto"
    assert config["file_permission"] == "0644", "❌ file_permission incorrecto"

    print("\n✅ Validación exitosa: null_resource → local_file")

def test_rename_resource():
    """Valida renombrado de recursos"""

    print("\n=== Test 2: Renombrado de recursos ===\n")

    base = NullResourceFactory.create("old_name")
    print(f"✓ Recurso original con nombre 'old_name'")

    proto = ResourcePrototype(base)
    cloned = proto.clone(lambda d: rename_resource(d, "old_name", "new_name"))

    print(f"✓ Recurso renombrado a 'new_name'")

    resource_block = cloned.data["resource"][0]["null_resource"][0]
    assert "new_name" in resource_block, "❌ Nuevo nombre no existe"
    assert "old_name" not in resource_block, "❌ Nombre viejo sigue presente"

    print("✅ Validación exitosa: renombrado correcto")

def test_add_trigger():
    """Valida agregación de triggers"""

    print("\n=== Test 3: Agregar triggers ===\n")

    base = NullResourceFactory.create("server")
    original_proto = ResourcePrototype(base)

    # Agregar trigger de región
    cloned = original_proto.clone(lambda d: add_trigger(d, "region", "us-west-2"))

    print(f"✓ Trigger 'region' agregado")

    triggers = cloned.data["resource"][0]["null_resource"][0]["server"][0]["triggers"]
    assert "region" in triggers, "❌ Trigger 'region' no agregado"
    assert triggers["region"] == "us-west-2", "❌ Valor de trigger incorrecto"

    # Verificar que los triggers por defecto siguen presentes
    assert "factory_uuid" in triggers, "❌ factory_uuid eliminado"
    assert "timestamp" in triggers, "❌ timestamp eliminado"

    print(f"✓ Triggers actuales: {triggers}")
    print("✅ Validación exitosa: trigger agregado correctamente")

def test_immutability():
    """Valida que el prototipo original no se modifica"""

    print("\n=== Test 4: Inmutabilidad del prototipo ===\n")

    base = NullResourceFactory.create("immutable_test")
    proto = ResourcePrototype(base)

    # Obtener estructura original
    original_type = list(proto.data["resource"][0].keys())[0]
    print(f"✓ Tipo original: {original_type}")

    # Crear múltiples clones con mutaciones
    clone1 = proto.clone(lambda d: convert_null_to_local_file(d, "file1.txt", "content1"))
    clone2 = proto.clone(lambda d: rename_resource(d, "immutable_test", "renamed"))

    # Verificar que el original sigue siendo null_resource
    assert original_type in proto.data["resource"][0], "❌ Prototipo original fue modificado"
    print(f"✓ Prototipo original intacto: {original_type}")

    # Verificar que los clones son independientes
    assert "local_file" in clone1.data["resource"][0], "❌ Clone1 no tiene local_file"
    assert "null_resource" in clone2.data["resource"][0], "❌ Clone2 no tiene null_resource"

    print("✅ Validación exitosa: inmutabilidad preservada")

if __name__ == "__main__":
    test_null_to_local_file()
    test_rename_resource()
    test_add_trigger()
    test_immutability()

    print("\n" + "="*50)
    print("✅ TODOS LOS TESTS PASARON CORRECTAMENTE")
    print("="*50)
