"""
Test de validación para el método build_group() del Builder.
Verifica que se puedan crear grupos de recursos con tags comunes.
"""

import sys
from pathlib import Path
import json
import tempfile
import os

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from iac_patterns.builder import InfrastructureBuilder

def test_single_group():
    """Valida creación de un grupo simple"""

    print("=== Test 1: Grupo simple ===\n")

    builder = InfrastructureBuilder(env_name="production")

    # Crear grupo de servidores web
    builder.build_group(
        group_name="web_tier",
        resource_names=["web1", "web2", "web3"],
        tags={"tier": "frontend", "env": "prod"}
    )

    # Exportar a archivo temporal
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test.tf.json")
        builder.export(output_path)

        # Leer y validar
        with open(output_path) as f:
            data = json.load(f)

        print(f"✓ Recursos exportados: {len(data['resource'])}")
        assert len(data["resource"]) == 3, f"❌ Esperaba 3 recursos, obtuvo {len(data['resource'])}"

        # Validar que todos los recursos tienen los tags correctos
        for resource in data["resource"]:
            null_res = resource["null_resource"][0]
            res_name = list(null_res.keys())[0]
            triggers = null_res[res_name][0]["triggers"]

            print(f"  └─ {res_name}: triggers = {triggers}")

            assert triggers["group"] == "web_tier", f"❌ Tag 'group' incorrecto en {res_name}"
            assert triggers["tier"] == "frontend", f"❌ Tag 'tier' incorrecto en {res_name}"
            assert triggers["env"] == "prod", f"❌ Tag 'env' incorrecto en {res_name}"

    print("✅ Validación exitosa: grupo simple funciona\n")

def test_multiple_groups():
    """Valida múltiples grupos en un mismo builder"""

    print("=== Test 2: Múltiples grupos ===\n")

    builder = InfrastructureBuilder(env_name="multi_tier")

    # Grupo de frontend
    builder.build_group(
        group_name="frontend",
        resource_names=["nginx", "react_app"],
        tags={"tier": "web", "public": "true"}
    )

    # Grupo de backend
    builder.build_group(
        group_name="backend",
        resource_names=["api_server", "worker"],
        tags={"tier": "application", "public": "false"}
    )

    # Grupo de base de datos
    builder.build_group(
        group_name="database",
        resource_names=["postgres"],
        tags={"tier": "data", "public": "false"}
    )

    # Exportar
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "multi.tf.json")
        builder.export(output_path)

        with open(output_path) as f:
            data = json.load(f)

        total_resources = len(data["resource"])
        print(f"✓ Total de recursos: {total_resources}")
        assert total_resources == 5, f"❌ Esperaba 5 recursos (2+2+1)"

        # Contar recursos por grupo
        groups = {"frontend": 0, "backend": 0, "database": 0}
        for resource in data["resource"]:
            null_res = resource["null_resource"][0]
            res_name = list(null_res.keys())[0]
            triggers = null_res[res_name][0]["triggers"]
            group = triggers["group"]
            groups[group] += 1

        print(f"✓ Distribución por grupo: {groups}")
        assert groups["frontend"] == 2, "❌ Frontend debería tener 2 recursos"
        assert groups["backend"] == 2, "❌ Backend debería tener 2 recursos"
        assert groups["database"] == 1, "❌ Database debería tener 1 recurso"

    print("✅ Validación exitosa: múltiples grupos funcionan\n")

def test_mixed_resources_and_groups():
    """Valida mezcla de recursos directos y grupos"""

    print("=== Test 3: Recursos mixtos ===\n")

    builder = InfrastructureBuilder(env_name="mixed")

    # Agregar recurso directo
    builder.add_custom_resource("monitoring", {"type": "prometheus"})

    # Agregar grupo
    builder.build_group(
        group_name="compute",
        resource_names=["server1", "server2"],
        tags={"type": "compute"}
    )

    # Agregar otro recurso directo
    builder.add_custom_resource("load_balancer", {"type": "lb"})

    # Exportar
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "mixed.tf.json")
        builder.export(output_path)

        with open(output_path) as f:
            data = json.load(f)

        print(f"✓ Total recursos: {len(data['resource'])}")
        assert len(data["resource"]) == 4, "❌ Debería haber 4 recursos totales"

        # Identificar tipos
        grouped = 0
        standalone = 0

        for resource in data["resource"]:
            null_res = resource["null_resource"][0]
            res_name = list(null_res.keys())[0]
            triggers = null_res[res_name][0]["triggers"]

            if "group" in triggers:
                grouped += 1
            else:
                standalone += 1

        print(f"✓ Recursos agrupados: {grouped}")
        print(f"✓ Recursos standalone: {standalone}")

        assert grouped == 2, "❌ Debería haber 2 recursos agrupados"
        assert standalone == 2, "❌ Debería haber 2 recursos standalone"

    print("✅ Validación exitosa: recursos mixtos funcionan\n")

def test_chaining():
    """Valida encadenamiento fluido de métodos"""

    print("=== Test 4: Encadenamiento fluido ===\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "chained.tf.json")

        # Construir todo en una sola expresión fluida
        (InfrastructureBuilder(env_name="chained")
            .build_group("group1", ["a", "b"], {"env": "dev"})
            .build_group("group2", ["c"], {"env": "prod"})
            .add_custom_resource("global", {"scope": "all"})
            .export(output_path))

        # Validar que se generó correctamente
        with open(output_path) as f:
            data = json.load(f)

        print(f"✓ Recursos exportados: {len(data['resource'])}")
        assert len(data["resource"]) == 4, "❌ Encadenamiento no funcionó"

    print("✅ Validación exitosa: encadenamiento fluido funciona\n")

def test_empty_group():
    """Valida manejo de grupos vacíos"""

    print("=== Test 5: Grupo vacío ===\n")

    builder = InfrastructureBuilder(env_name="empty_test")

    # Crear grupo vacío
    builder.build_group("empty_group", [], {"tag": "value"})

    # Agregar grupo con contenido
    builder.build_group("full_group", ["resource1"], {"tag": "value"})

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "empty.tf.json")
        builder.export(output_path)

        with open(output_path) as f:
            data = json.load(f)

        print(f"✓ Total recursos (grupo vacío ignorado): {len(data['resource'])}")
        assert len(data["resource"]) == 1, "❌ Grupo vacío no debería generar recursos"

    print("✅ Validación exitosa: grupos vacíos se manejan correctamente\n")

if __name__ == "__main__":
    test_single_group()
    test_multiple_groups()
    test_mixed_resources_and_groups()
    test_chaining()
    test_empty_group()

    print("="*50)
    print("✅ TODOS LOS TESTS PASARON CORRECTAMENTE")
    print("="*50)
