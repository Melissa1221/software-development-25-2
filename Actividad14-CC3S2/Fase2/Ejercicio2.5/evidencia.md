# Ejercicio 2.5: Método build_group() en Builder

## Implementación

Se agregó el método `build_group()` a la clase `InfrastructureBuilder` en `iac_patterns/builder.py:71-108`. Este método utiliza la funcionalidad de submódulos implementada en el Ejercicio 2.4 para organizar recursos relacionados bajo grupos lógicos.

```python
def build_group(self, group_name: str, resource_names: list,
                tags: Dict[str, Any] = None) -> "InfrastructureBuilder":
    """
    Crea un submódulo (grupo) de recursos con tags comunes.

    Este método utiliza la funcionalidad de submódulos de CompositeModule para organizar
    recursos relacionados bajo un grupo lógico. Todos los recursos del grupo comparten
    los mismos tags, facilitando la organización y el filtrado en Terraform.

    Args:
        group_name: nombre del grupo/submódulo.
        resource_names: lista de nombres de recursos a incluir en el grupo.
        tags: diccionario de tags comunes para todos los recursos del grupo.

    Returns:
        self: permite encadenar llamadas.

    Ejemplo:
        builder.build_group("web_tier", ["web1", "web2"], {"tier": "frontend", "env": "prod"})
    """
    tags = tags or {}

    # Crear submódulo para el grupo
    group_module = CompositeModule(name=group_name)

    # Agregar recursos al grupo con tags comunes
    for resource_name in resource_names:
        # Crear triggers que incluyen los tags del grupo
        triggers = {"group": group_name}
        triggers.update(tags)

        # Crear recurso y agregarlo al submódulo
        resource = NullResourceFactory.create(resource_name, triggers)
        group_module.add(resource)

    # Agregar el submódulo al módulo principal
    self._module.add_submodule(group_module)

    return self
```

## Características

El método proporciona organización lógica agrupando recursos relacionados bajo un nombre común. Todos los recursos del grupo heredan automáticamente los mismos tags configurados. La interfaz fluida retorna `self` permitiendo encadenar múltiples llamadas. La integración completa con submódulos usa `CompositeModule.add_submodule()` implementado en el Ejercicio 2.4.

## Validación

Los tests validan cinco escenarios clave del método. Los grupos simples prueban conjuntos básicos de recursos con tags compartidos. Los múltiples grupos verifican que varios grupos coexistan en un mismo builder.

El contenido mixto valida la combinación de recursos agrupados y standalone. El encadenamiento fluido confirma que las llamadas se pueden concatenar en una sola expresión. Los grupos vacíos prueban el manejo correcto cuando no hay recursos internos.

## Resultados

### Test 1: Grupo simple

```python
builder.build_group(
    group_name="web_tier",
    resource_names=["web1", "web2", "web3"],
    tags={"tier": "frontend", "env": "prod"}
)
```

**Triggers generados:**
```
web1: {'group': 'web_tier', 'tier': 'frontend', 'env': 'prod', ...}
web2: {'group': 'web_tier', 'tier': 'frontend', 'env': 'prod', ...}
web3: {'group': 'web_tier', 'tier': 'frontend', 'env': 'prod', ...}
```

### Test 2: Múltiples grupos

Creación de infraestructura multi-tier:

```python
builder.build_group("frontend", ["nginx", "react_app"],
                   {"tier": "web", "public": "true"})
builder.build_group("backend", ["api_server", "worker"],
                   {"tier": "application", "public": "false"})
builder.build_group("database", ["postgres"],
                   {"tier": "data", "public": "false"})
```

**Distribución:** `{'frontend': 2, 'backend': 2, 'database': 1}`

### Test 4: Encadenamiento fluido

```python
(InfrastructureBuilder(env_name="chained")
    .build_group("group1", ["a", "b"], {"env": "dev"})
    .build_group("group2", ["c"], {"env": "prod"})
    .add_custom_resource("global", {"scope": "all"})
    .export(output_path))
```

[OK] **4 recursos exportados correctamente**

### Todos los tests

```
[OK] Validación exitosa: grupo simple funciona
[OK] Validación exitosa: múltiples grupos funcionan
[OK] Validación exitosa: recursos mixtos funcionan
[OK] Validación exitosa: encadenamiento fluido funciona
[OK] Validación exitosa: grupos vacíos se manejan correctamente

==================================================
[OK] TODOS LOS TESTS PASARON CORRECTAMENTE
==================================================
```

## Utilidad

El método `build_group()` facilita la organización de infraestructura compleja en grupos lógicos. Es especialmente útil para arquitecturas multi-tier donde se separan frontend, backend y database en grupos distintos. También sirve para entornos múltiples agrupando recursos por entorno como dev, staging o prod.

Las regiones geográficas se organizan fácilmente creando grupos por región como us-east-1 o us-west-2. Los equipos pueden agrupar sus recursos bajo su responsabilidad para mejor gestión.

Todos los recursos de un grupo comparten tags comunes. Esto facilita el filtrado en consolas de cloud providers. Las políticas de seguridad basadas en tags se aplican automáticamente. La facturación y cost tracking se simplifica por grupo. La gestión de permisos IAM se centraliza usando los tags compartidos.

La integración con el patrón Composite (submódulos) permite que estos grupos se exporten correctamente en un único archivo Terraform JSON válido.
