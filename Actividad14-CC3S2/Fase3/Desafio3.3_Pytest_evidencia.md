# Desafío 3.3: Suite de Tests con Pytest

## Descripción

Se implementó una suite completa de tests usando pytest que valida todos los patrones de diseño implementados. La suite incluye fixtures reutilizables, tests parametrizados, y tests de integración entre patrones.

## Estructura

```
tests/
├── conftest.py           # Fixtures compartidas
└── test_all_patterns.py  # Suite completa de tests
```

## Fixtures Implementadas

Las fixtures en `conftest.py` proporcionan objetos reutilizables para todos los tests:

```python
@pytest.fixture
def singleton_instance():
    """Fixture que proporciona una instancia limpia de ConfigSingleton."""
    instance = ConfigSingleton(env_name="test")
    instance.reset()
    yield instance
    instance.reset()  # Cleanup

@pytest.fixture
def base_resource():
    """Fixture que proporciona un recurso null_resource base."""
    return NullResourceFactory.create("test_resource")

@pytest.fixture
def prototype_instance(base_resource):
    """Fixture que proporciona un ResourcePrototype con recurso base."""
    return ResourcePrototype(base_resource)

@pytest.fixture
def composite_module():
    """Fixture que proporciona un CompositeModule vacío."""
    return CompositeModule(name="test_module")

# ... más fixtures para builder, adapters, etc.
```

## Tests Organizados por Patrón

### 1. Singleton Tests (7 tests)

```python
class TestSingleton:
    def test_singleton_unique_instance(self):
        """Verifica que solo existe una instancia del Singleton"""
        instance1 = ConfigSingleton()
        instance2 = ConfigSingleton()
        assert instance1 is instance2

    def test_singleton_reset(self, singleton_instance):
        """Verifica que reset() limpia settings pero preserva created_at"""
        original_created = singleton_instance.created_at
        singleton_instance.set("test", "data")

        singleton_instance.reset()

        assert singleton_instance.settings == {}
        assert singleton_instance.created_at == original_created

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
```

**Tests parametrizados** validan múltiples tipos de valores (string, int, bool, dict).

### 2. Factory Tests (7 tests)

```python
class TestFactory:
    def test_factory_unique_triggers(self):
        """Verifica que cada recurso tiene triggers únicos"""
        res1 = NullResourceFactory.create("res1")
        res2 = NullResourceFactory.create("res2")

        triggers1 = res1["resource"][0]["null_resource"][0]["res1"][0]["triggers"]
        triggers2 = res2["resource"][0]["null_resource"][0]["res2"][0]["triggers"]

        assert triggers1["factory_uuid"] != triggers2["factory_uuid"]

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
```

**Tests parametrizados** validan múltiples formatos de timestamp.

### 3. Prototype Tests (4 tests)

```python
class TestPrototype:
    def test_prototype_immutability(self, prototype_instance):
        """Verifica que el original no se modifica al clonar"""
        original_data = prototype_instance.data.copy()

        def mutator(d):
            d["modified"] = True

        clone = prototype_instance.clone(mutator)

        assert prototype_instance.data == original_data
        assert "modified" in clone.data

    def test_convert_null_to_local_file_mutator(self, base_resource):
        """Verifica mutator de conversión null_resource -> local_file"""
        proto = ResourcePrototype(base_resource)

        clone = proto.clone(lambda d: convert_null_to_local_file(
            d, filename="test.txt", content="Hello"
        ))

        assert "local_file" in clone.data["resource"][0]
        assert "null_resource" not in clone.data["resource"][0]
```

### 4. Composite Tests (4 tests)

```python
class TestComposite:
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
```

### 5. Builder Tests (4 tests)

```python
class TestBuilder:
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
```

### 6. Adapter Tests (4 tests)

```python
class TestAdapter:
    def test_ansible_adapter_command_module(self, ansible_playbook_yaml):
        """Verifica conversión de módulo command de Ansible"""
        adapter = AnsibleToTerraformAdapter(ansible_playbook_yaml)
        terraform = adapter.adapt()

        assert len(terraform["resource"]) >= 1
        assert "null_resource" in terraform["resource"][0]

    def test_cloudformation_adapter(self, cloudformation_template):
        """Verifica conversión de CloudFormation"""
        adapter = CloudFormationToTerraformAdapter(cloudformation_template)
        terraform = adapter.adapt()

        assert len(terraform["resource"]) == 1
        assert "aws_s3_bucket" in terraform["resource"][0]
```

### 7. Integration Tests (2 tests)

```python
class TestIntegration:
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

        # 3 de fleet + 2 de grupo = 5 recursos
        assert len(data["resource"]) == 5
```

## Resultados de Ejecución

```
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: /Users/melissaimannoriega/.../Actividad14-CC3S2
plugins: cov-6.3.0, anyio-4.10.0
collecting ... collected 32 items

tests/test_all_patterns.py::TestSingleton::test_singleton_unique_instance PASSED [  3%]
tests/test_all_patterns.py::TestSingleton::test_singleton_shared_state PASSED [  6%]
tests/test_all_patterns.py::TestSingleton::test_singleton_reset PASSED   [  9%]
tests/test_all_patterns.py::TestSingleton::test_singleton_set_get[database-postgres] PASSED [ 12%]
tests/test_all_patterns.py::TestSingleton::test_singleton_set_get[port-5432] PASSED [ 15%]
tests/test_all_patterns.py::TestSingleton::test_singleton_set_get[enabled-True] PASSED [ 18%]
tests/test_all_patterns.py::TestSingleton::test_singleton_set_get[config-value3] PASSED [ 21%]
tests/test_all_patterns.py::TestFactory::test_factory_creates_valid_structure PASSED [ 25%]
tests/test_all_patterns.py::TestFactory::test_factory_unique_triggers PASSED [ 28%]
tests/test_all_patterns.py::TestFactory::test_factory_custom_triggers PASSED [ 31%]
tests/test_all_patterns.py::TestFactory::test_timestamped_factory_default_format PASSED [ 34%]
tests/test_all_patterns.py::TestFactory::test_timestamped_factory_custom_formats[%Y-%m-%d-10] PASSED [ 37%]
tests/test_all_patterns.py::TestFactory::test_timestamped_factory_custom_formats[%Y%m%d-8] PASSED [ 40%]
tests/test_all_patterns.py::TestFactory::test_timestamped_factory_custom_formats[%d/%m/%Y %H:%M-16] PASSED [ 43%]
tests/test_all_patterns.py::TestPrototype::test_prototype_clone_creates_copy PASSED [ 46%]
tests/test_all_patterns.py::TestPrototype::test_prototype_immutability PASSED [ 50%]
tests/test_all_patterns.py::TestPrototype::test_prototype_mutator_applied PASSED [ 53%]
tests/test_all_patterns.py::TestPrototype::test_convert_null_to_local_file_mutator PASSED [ 56%]
tests/test_all_patterns.py::TestComposite::test_composite_add_resource PASSED [ 59%]
tests/test_all_patterns.py::TestComposite::test_composite_multiple_resources PASSED [ 62%]
tests/test_all_patterns.py::TestComposite::test_composite_submodules PASSED [ 65%]
tests/test_all_patterns.py::TestComposite::test_composite_empty_submodule PASSED [ 68%]
tests/test_all_patterns.py::TestBuilder::test_builder_fluent_interface PASSED [ 71%]
tests/test_all_patterns.py::TestBuilder::test_builder_build_null_fleet PASSED [ 75%]
tests/test_all_patterns.py::TestBuilder::test_builder_build_group PASSED [ 78%]
tests/test_all_patterns.py::TestBuilder::test_builder_mixed_resources PASSED [ 81%]
tests/test_all_patterns.py::TestAdapter::test_ansible_adapter_command_module PASSED [ 84%]
tests/test_all_patterns.py::TestAdapter::test_ansible_adapter_file_module PASSED [ 87%]
tests/test_all_patterns.py::TestAdapter::test_cloudformation_adapter PASSED [ 90%]
tests/test_all_patterns.py::TestAdapter::test_ansible_adapter_empty_playbook PASSED [ 93%]
tests/test_all_patterns.py::TestIntegration::test_factory_prototype_composite_integration PASSED [ 96%]
tests/test_all_patterns.py::TestIntegration::test_builder_uses_all_patterns PASSED [100%]

============================== 32 passed in 0.05s ============================
```

## Características de la Suite

La organización de los tests es clara y sistemática. Los tests están agrupados por patrón en clases dedicadas. Los nombres descriptivos explican exactamente qué validan. Hay separación clara entre tests unitarios y de integración.

Las fixtures proporcionan reutilización eficiente. El setup y teardown es completamente automático. Cada test recibe estado limpio garantizado. La composición de fixtures permite que unas dependan de otras.

Los tests parametrizados validan múltiples casos con el mismo código. Esto mejora la cobertura sin duplicar lógica de prueba. Los ejemplos incluyen validar diferentes tipos de valores en Singleton y múltiples formatos de timestamp en Factory.

Los tests de integración validan la interacción correcta entre patrones. Cubren escenarios realistas de uso del sistema. Verifican que el sistema completo funciona como una unidad cohesiva.

El uso de archivos temporales permite tests realistas. Los tests de Builder escriben y leen archivos reales del sistema. El cleanup es automático usando tempfile.TemporaryDirectory. La validación incluye salida JSON real de Terraform.

## Cobertura

La suite cubre todos los patrones de diseño incluyendo los cinco base más el Adapter. Los métodos agregados en los ejercicios como reset, build_group y submódulos están validados. Los casos edge como recursos vacíos y playbooks sin tasks funcionan correctamente. La integración entre patrones se verifica exhaustivamente. La estructura Terraform JSON generada es completamente válida.

## Ejecución

```bash
# Ejecutar toda la suite
pytest tests/ -v

# Ejecutar con coverage
pytest tests/ --cov=iac_patterns --cov-report=html

# Ejecutar solo una clase
pytest tests/test_all_patterns.py::TestSingleton -v

# Ejecutar con output detallado
pytest tests/ -v --tb=short
```

## Conclusión

La suite de pytest proporciona validación completa y automatizada de todos los patrones implementados. El uso de fixtures, parametrización y tests de integración asegura que el código es robusto y que los patrones interactúan correctamente entre sí. Los 32 tests pasaron exitosamente en 0.05 segundos.
