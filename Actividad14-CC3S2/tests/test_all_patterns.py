"""
Suite completa de tests con pytest para todos los patrones de diseño.
"""

import pytest
import tempfile
import os
import json
from datetime import datetime

from iac_patterns.singleton import ConfigSingleton
from iac_patterns.factory import NullResourceFactory, TimestampedNullResourceFactory
from iac_patterns.prototype import ResourcePrototype
from iac_patterns.composite import CompositeModule
from iac_patterns.builder import InfrastructureBuilder
from iac_patterns.mutators import convert_null_to_local_file, rename_resource, add_trigger
from iac_patterns.adapter import AnsibleToTerraformAdapter, CloudFormationToTerraformAdapter


# ==================== SINGLETON TESTS ====================

class TestSingleton:
    """Tests para el patrón Singleton"""

    def test_singleton_unique_instance(self):
        """Verifica que solo existe una instancia del Singleton"""
        instance1 = ConfigSingleton()
        instance2 = ConfigSingleton()
        assert instance1 is instance2, "Las instancias deberían ser la misma"

    def test_singleton_shared_state(self, singleton_instance):
        """Verifica que el estado se comparte entre referencias"""
        singleton_instance.set("key1", "value1")

        another_ref = ConfigSingleton()
        assert another_ref.get("key1") == "value1", "El estado no se comparte"

    def test_singleton_reset(self, singleton_instance):
        """Verifica que reset() limpia settings pero preserva created_at"""
        original_created = singleton_instance.created_at
        singleton_instance.set("test", "data")

        singleton_instance.reset()

        assert singleton_instance.settings == {}, "Settings no se limpió"
        assert singleton_instance.created_at == original_created, "created_at cambió"

    @pytest.mark.parametrize("key,value", [
        ("database", "postgres"),
        ("port", 5432),
        ("enabled", True),
        ("config", {"nested": "value"})
    ])
    def test_singleton_set_get(self, singleton_instance, key, value):
        """Verifica set/get con diferentes tipos de valores"""
        singleton_instance.set(key, value)
        assert singleton_instance.get(key) == value


# ==================== FACTORY TESTS ====================

class TestFactory:
    """Tests para el patrón Factory"""

    def test_factory_creates_valid_structure(self):
        """Verifica que Factory crea estructura Terraform válida"""
        resource = NullResourceFactory.create("test")

        assert "resource" in resource
        assert isinstance(resource["resource"], list)
        assert "null_resource" in resource["resource"][0]

    def test_factory_unique_triggers(self):
        """Verifica que cada recurso tiene triggers únicos"""
        res1 = NullResourceFactory.create("res1")
        res2 = NullResourceFactory.create("res2")

        triggers1 = res1["resource"][0]["null_resource"][0]["res1"][0]["triggers"]
        triggers2 = res2["resource"][0]["null_resource"][0]["res2"][0]["triggers"]

        assert triggers1["factory_uuid"] != triggers2["factory_uuid"]
        assert "timestamp" in triggers1
        assert "timestamp" in triggers2

    def test_factory_custom_triggers(self, sample_triggers):
        """Verifica que se preservan triggers personalizados"""
        resource = NullResourceFactory.create("custom", sample_triggers)

        triggers = resource["resource"][0]["null_resource"][0]["custom"][0]["triggers"]

        assert triggers["environment"] == "test"
        assert triggers["region"] == "us-east-1"
        assert "factory_uuid" in triggers  # UUID agregado automáticamente

    def test_timestamped_factory_default_format(self):
        """Verifica formato por defecto de TimestampedNullResourceFactory"""
        resource = TimestampedNullResourceFactory.create("test")
        triggers = resource["resource"][0]["null_resource"][0]["test"][0]["triggers"]

        # Formato: YYYY-MM-DD HH:MM:SS
        timestamp = triggers["timestamp"]
        assert len(timestamp) == 19, "Formato de timestamp incorrecto"
        assert timestamp[4] == "-" and timestamp[7] == "-"
        assert timestamp[13] == ":" and timestamp[16] == ":"

    @pytest.mark.parametrize("format_string,expected_length", [
        ("%Y-%m-%d", 10),
        ("%Y%m%d", 8),
        ("%d/%m/%Y %H:%M", 16),
    ])
    def test_timestamped_factory_custom_formats(self, format_string, expected_length):
        """Verifica formatos personalizados de timestamp"""
        resource = TimestampedNullResourceFactory.create("test", timestamp_format=format_string)
        triggers = resource["resource"][0]["null_resource"][0]["test"][0]["triggers"]

        assert len(triggers["timestamp"]) == expected_length


# ==================== PROTOTYPE TESTS ====================

class TestPrototype:
    """Tests para el patrón Prototype"""

    def test_prototype_clone_creates_copy(self, prototype_instance):
        """Verifica que clone() crea una copia independiente"""
        clone = prototype_instance.clone()

        assert clone is not prototype_instance, "Clone es la misma instancia"
        assert clone.data == prototype_instance.data, "Datos no coinciden"

    def test_prototype_immutability(self, prototype_instance):
        """Verifica que el original no se modifica al clonar"""
        original_data = prototype_instance.data.copy()

        def mutator(d):
            d["modified"] = True

        clone = prototype_instance.clone(mutator)

        assert prototype_instance.data == original_data, "Original fue modificado"
        assert "modified" in clone.data, "Clone no fue mutado"

    def test_prototype_mutator_applied(self, base_resource):
        """Verifica que el mutator se aplica correctamente"""
        proto = ResourcePrototype(base_resource)

        def add_tag(d):
            triggers = d["resource"][0]["null_resource"][0]["test_resource"][0]["triggers"]
            triggers["mutated"] = True

        clone = proto.clone(add_tag)
        triggers = clone.data["resource"][0]["null_resource"][0]["test_resource"][0]["triggers"]

        assert triggers["mutated"] is True

    def test_convert_null_to_local_file_mutator(self, base_resource):
        """Verifica mutator de conversión null_resource → local_file"""
        proto = ResourcePrototype(base_resource)

        clone = proto.clone(lambda d: convert_null_to_local_file(
            d, filename="test.txt", content="Hello"
        ))

        assert "local_file" in clone.data["resource"][0]
        assert "null_resource" not in clone.data["resource"][0]


# ==================== COMPOSITE TESTS ====================

class TestComposite:
    """Tests para el patrón Composite"""

    def test_composite_add_resource(self, composite_module, base_resource):
        """Verifica que se pueden agregar recursos"""
        composite_module.add(base_resource)
        exported = composite_module.export()

        assert len(exported["resource"]) == 1

    def test_composite_multiple_resources(self, composite_module):
        """Verifica agregación de múltiples recursos"""
        for i in range(5):
            composite_module.add(NullResourceFactory.create(f"res{i}"))

        exported = composite_module.export()
        assert len(exported["resource"]) == 5

    def test_composite_submodules(self):
        """Verifica soporte de submódulos anidados"""
        root = CompositeModule(name="root")

        sub1 = CompositeModule(name="sub1")
        sub1.add(NullResourceFactory.create("res1"))
        sub1.add(NullResourceFactory.create("res2"))

        sub2 = CompositeModule(name="sub2")
        sub2.add(NullResourceFactory.create("res3"))

        root.add_submodule(sub1)
        root.add_submodule(sub2)

        assert root.count_resources() == 3
        assert sub1.count_resources() == 2

        exported = root.export()
        assert len(exported["resource"]) == 3

    def test_composite_empty_submodule(self, composite_module):
        """Verifica manejo de submódulos vacíos"""
        empty_sub = CompositeModule(name="empty")
        composite_module.add_submodule(empty_sub)

        assert composite_module.count_resources() == 0

        exported = composite_module.export()
        assert len(exported["resource"]) == 0


# ==================== BUILDER TESTS ====================

class TestBuilder:
    """Tests para el patrón Builder"""

    def test_builder_fluent_interface(self, builder_instance):
        """Verifica que los métodos retornan self para encadenamiento"""
        result = builder_instance.add_custom_resource("test", {"key": "value"})
        assert result is builder_instance, "No retorna self"

    def test_builder_build_null_fleet(self, builder_instance):
        """Verifica construcción de flota de recursos"""
        builder_instance.build_null_fleet(count=10)

        # Exportar a archivo temporal para validar
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.tf.json")
            builder_instance.export(output_path)

            with open(output_path) as f:
                data = json.load(f)

            assert len(data["resource"]) == 10

    def test_builder_build_group(self, builder_instance):
        """Verifica construcción de grupos de recursos"""
        builder_instance.build_group(
            "web_tier",
            ["web1", "web2", "web3"],
            {"tier": "frontend"}
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.tf.json")
            builder_instance.export(output_path)

            with open(output_path) as f:
                data = json.load(f)

            assert len(data["resource"]) == 3

            # Verificar tags
            for resource in data["resource"]:
                null_res = resource["null_resource"][0]
                res_name = list(null_res.keys())[0]
                triggers = null_res[res_name][0]["triggers"]
                assert triggers["group"] == "web_tier"
                assert triggers["tier"] == "frontend"

    def test_builder_mixed_resources(self, builder_instance):
        """Verifica mezcla de recursos directos y grupos"""
        (builder_instance
            .add_custom_resource("standalone", {"type": "single"})
            .build_group("group1", ["a", "b"], {"type": "grouped"})
            .add_custom_resource("another", {"type": "single"}))

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.tf.json")
            builder_instance.export(output_path)

            with open(output_path) as f:
                data = json.load(f)

            assert len(data["resource"]) == 4


# ==================== ADAPTER TESTS ====================

class TestAdapter:
    """Tests para el patrón Adapter"""

    def test_ansible_adapter_command_module(self, ansible_playbook_yaml):
        """Verifica conversión de módulo command de Ansible"""
        adapter = AnsibleToTerraformAdapter(ansible_playbook_yaml)
        terraform = adapter.adapt()

        assert len(terraform["resource"]) >= 1
        assert "null_resource" in terraform["resource"][0]

    def test_ansible_adapter_file_module(self):
        """Verifica conversión de módulo file de Ansible"""
        playbook = """
- name: File test
  hosts: all
  tasks:
    - name: Create file
      file:
        path: /tmp/test.txt
        content: "test"
        mode: '0644'
"""
        adapter = AnsibleToTerraformAdapter(playbook)
        terraform = adapter.adapt()

        assert len(terraform["resource"]) == 1
        assert "local_file" in terraform["resource"][0]

    def test_cloudformation_adapter(self, cloudformation_template):
        """Verifica conversión de CloudFormation"""
        adapter = CloudFormationToTerraformAdapter(cloudformation_template)
        terraform = adapter.adapt()

        assert len(terraform["resource"]) == 1
        assert "aws_s3_bucket" in terraform["resource"][0]

    def test_ansible_adapter_empty_playbook(self):
        """Verifica manejo de playbook vacío"""
        playbook = """
- name: Empty
  hosts: all
"""
        adapter = AnsibleToTerraformAdapter(playbook)
        terraform = adapter.adapt()

        assert len(terraform["resource"]) == 0


# ==================== INTEGRATION TESTS ====================

class TestIntegration:
    """Tests de integración entre patrones"""

    def test_factory_prototype_composite_integration(self):
        """Verifica integración Factory + Prototype + Composite"""
        # Factory crea base
        base = NullResourceFactory.create("base")

        # Prototype clona con variaciones
        proto = ResourcePrototype(base)
        clone1 = proto.clone(lambda d: rename_resource(d, "base", "variant1"))
        clone2 = proto.clone(lambda d: rename_resource(d, "base", "variant2"))

        # Composite agrega todos
        composite = CompositeModule(name="integrated")
        composite.add(clone1.data)
        composite.add(clone2.data)

        exported = composite.export()
        assert len(exported["resource"]) == 2

    def test_builder_uses_all_patterns(self):
        """Verifica que Builder orquesta todos los patrones"""
        builder = InfrastructureBuilder(env_name="full_test")

        # Factory (interno en build_null_fleet)
        builder.build_null_fleet(count=3)

        # Composite (grupos)
        builder.build_group("group1", ["a", "b"], {"env": "test"})

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "integrated.tf.json")
            builder.export(output_path)

            assert os.path.exists(output_path)

            with open(output_path) as f:
                data = json.load(f)

            # 3 de fleet + 2 de grupo = 5 recursos
            assert len(data["resource"]) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
