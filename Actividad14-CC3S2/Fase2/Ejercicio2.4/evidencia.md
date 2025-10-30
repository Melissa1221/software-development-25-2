# Ejercicio 2.4: Submódulos en Composite

## Implementación

Se extendió la clase `CompositeModule` en `iac_patterns/composite.py` para soportar submódulos anidados, permitiendo crear jerarquías complejas de recursos.

### Cambios principales

El constructor ahora acepta un parámetro `name` que permite identificar cada módulo en la jerarquía. El tipado de `_children` se volvió flexible para aceptar tanto diccionarios de recursos como instancias de `CompositeModule`.

Se agregó el método `add_submodule()` que proporciona una API explícita para agregar submódulos. El método `export()` fue modificado para manejar submódulos de forma recursiva. Finalmente se implementó `count_resources()` que cuenta recursos en toda la jerarquía de submódulos.

```python
class CompositeModule:
    def __init__(self, name: str = "root") -> None:
        self.name = name
        self._children: List[Union[Dict[str, Any], "CompositeModule"]] = []

    def add_submodule(self, submodule: "CompositeModule") -> None:
        """Agrega un submódulo al módulo actual."""
        if not isinstance(submodule, CompositeModule):
            raise TypeError("submodule debe ser una instancia de CompositeModule")
        self._children.append(submodule)

    def export(self) -> Dict[str, Any]:
        """Exporta recursivamente todos los recursos de submódulos."""
        aggregated: Dict[str, Any] = {"resource": []}

        for child in self._children:
            if isinstance(child, CompositeModule):
                # Exportar submódulo recursivamente
                submodule_export = child.export()
                aggregated["resource"].extend(submodule_export.get("resource", []))
            else:
                # Agregar recurso directo
                aggregated["resource"].extend(child.get("resource", []))

        return aggregated

    def count_resources(self) -> int:
        """Cuenta recursivamente recursos en submódulos."""
        total = 0
        for child in self._children:
            if isinstance(child, CompositeModule):
                total += child.count_resources()
            else:
                total += len(child.get("resource", []))
        return total
```

## Validación

Los tests cubren cinco escenarios diferentes. La agregación básica verifica submódulos de primer nivel funcionando correctamente. Las jerarquías multinivel prueban módulos anidados en tres o más niveles de profundidad.

El contenido mixto valida que recursos directos y submódulos puedan coexistir en el mismo padre. La estructura exportada confirma que el JSON generado es válido para Terraform. Los submódulos vacíos verifican el manejo correcto de módulos sin recursos internos.

## Resultados

### Test 2: Jerarquías multinivel

Se creó una estructura de 3 niveles simulando infraestructura multi-región:

```
cloud_infrastructure (4 recursos totales)
├─ us-east-1 (3 recursos)
│  ├─ compute (2 recursos: ec2_1, ec2_2)
│  └─ storage (1 recurso: s3_bucket)
└─ us-west-2 (1 recurso)
   └─ compute (1 recurso: ec2_3)
```

**Output:**
```
[OK] Módulo raíz: CompositeModule(name='cloud_infrastructure', children=2, resources=4)
[OK] us-east-1: CompositeModule(name='us-east-1', children=2, resources=3)
[OK] us-west-2: CompositeModule(name='us-west-2', children=1, resources=1)
```

### Test 3: Contenido mixto

```python
mixed = CompositeModule(name="mixed_module")
mixed.add(NullResourceFactory.create("direct_resource"))  # Recurso directo

sub = CompositeModule(name="submodule")
sub.add(NullResourceFactory.create("sub_resource_1"))
sub.add(NullResourceFactory.create("sub_resource_2"))
mixed.add_submodule(sub)  # Submódulo

mixed.add(NullResourceFactory.create("another_direct"))  # Otro directo
```

**Result:** `CompositeModule(name='mixed_module', children=3, resources=4)`

### Todos los tests

```
[OK] Validación exitosa: submódulos básicos funcionan
[OK] Validación exitosa: jerarquías multinivel funcionan
[OK] Validación exitosa: contenido mixto funciona
[OK] Validación exitosa: estructura Terraform válida
[OK] Validación exitosa: submódulos vacíos se manejan correctamente

==================================================
[OK] TODOS LOS TESTS PASARON CORRECTAMENTE
==================================================
```

## Utilidad

El soporte de submódulos permite organizar infraestructura compleja de forma jerárquica. Por ejemplo, se pueden crear módulos por región, por entorno (dev/staging/prod), por tipo de servicio (compute/storage/network), o cualquier combinación de estos criterios. La exportación recursiva garantiza que toda la jerarquía se aplane correctamente en un único archivo Terraform JSON válido.

Esta extensión del patrón Composite es especialmente útil para organizaciones con infraestructura distribuida en múltiples regiones o proyectos, permitiendo reutilización de módulos y composición flexible.
