# Desafío 3.1: Comparativa Factory vs Prototype

## Cuándo usar cada patrón

Los patrones Factory y Prototype resuelven el problema de creación de objetos, pero desde perspectivas diferentes y con casos de uso complementarios.

### Patrón Factory

El patrón Factory es ideal cuando necesitas **crear objetos desde cero** con configuraciones específicas pero predecibles. Encapsula toda la lógica de inicialización en un solo lugar, garantizando que los objetos se creen con valores consistentes.

En el contexto de IaC, `NullResourceFactory` se usa cuando necesitas generar recursos Terraform nuevos con triggers únicos (UUID y timestamp). La factory asegura que cada recurso tenga la estructura correcta y los valores por defecto apropiados. Es perfecta para generar recursos frescos donde la configuración inicial es conocida pero los valores específicos (como UUIDs) deben ser únicos.

**Ventajas:** Centralización de lógica, fácil extensión mediante herencia (como `TimestampedNullResourceFactory`), y garantía de consistencia estructural.

**Desventajas:** Menos flexible para variaciones complejas. Si necesitas 10 variantes de un recurso con pequeños cambios, necesitarías 10 factories diferentes o parámetros muy complejos.

### Patrón Prototype

El patrón Prototype brilla cuando necesitas **crear variaciones de un objeto existente**. En lugar de especificar toda la configuración desde cero, partes de una plantilla y la modificas según sea necesario.

En nuestro sistema, `ResourcePrototype` permite clonar un recurso base y aplicar mutaciones específicas. Esto es ideal para escalar infraestructura: creas un recurso prototipo perfectamente configurado y luego generas múltiples copias con pequeños ajustes (como cambiar nombres o agregar triggers específicos).

**Ventajas:** Extremadamente eficiente para generar variaciones, preserva inmutabilidad del original, y permite transformaciones complejas mediante mutadores personalizados.

**Desventajas:** Requiere un objeto base válido previo. No es útil para crear el primer objeto desde cero.

### Complementariedad

En la práctica, estos patrones se complementan perfectamente. El patrón típico es:

1. **Factory crea el prototipo**: Usar Factory para generar el recurso base inicial
2. **Prototype escala con variaciones**: Usar Prototype para clonar y variar ese base

Por ejemplo, en `InfrastructureBuilder.build_null_fleet()`:

```python
base_proto = ResourcePrototype(NullResourceFactory.create("placeholder"))
for i in range(count):
    clone = base_proto.clone(mutator).data
    self._module.add(clone)
```

La Factory garantiza estructura consistente, mientras Prototype permite escalabilidad eficiente.

## Conclusión

Factory es para creación inicial consistente. Prototype es para replicación eficiente con variaciones. Juntos forman un sistema poderoso para generación masiva de infraestructura.

---

**Palabras:** ~320
