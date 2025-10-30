# Fase 1: Exploración y Análisis de Patrones

## 1. Singleton

### ¿Cómo SingletonMeta garantiza una sola instancia?

`SingletonMeta` es una metaclase que controla la creación de instancias de cualquier clase que la use. El mecanismo funciona mediante el método `__call__` que se ejecuta cuando se intenta crear una nueva instancia.

La metaclase mantiene un diccionario `_instances` que almacena las instancias únicas de cada clase. Cuando se intenta crear una instancia, primero verifica si ya existe en este diccionario. Si no existe, la crea y la guarda. Si ya existe, simplemente retorna la instancia existente.

```python
class SingletonMeta(type):
    _instances: dict = {}
    _lock: threading.Lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]
```

### Rol del lock

El `lock` (threading.Lock) garantiza seguridad en entornos multihilo. Sin el lock, dos hilos podrían verificar simultáneamente que no existe una instancia y crear dos instancias diferentes, rompiendo el patrón Singleton.

El contexto `with cls._lock` asegura que solo un hilo a la vez pueda ejecutar el código de verificación y creación. Esto previene condiciones de carrera donde múltiples hilos intentan crear la instancia simultáneamente.

---

## 2. Factory

### Encapsulación de la creación de null_resource

`NullResourceFactory` encapsula toda la lógica necesaria para crear un recurso `null_resource` válido para Terraform. En lugar de construir manualmente el diccionario en cada lugar donde se necesite, el factory lo genera con una estructura consistente.

```python
class NullResourceFactory:
    @staticmethod
    def create(name: str, triggers: dict = None) -> dict:
        triggers = triggers or {
            "factory_uuid": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat()
        }
        return {
            "resource": {
                "null_resource": {
                    name: {"triggers": triggers}
                }
            }
        }
```

El método estático `create()` acepta un nombre y triggers opcionales. Si no se proporcionan triggers, genera automáticamente un UUID único y un timestamp, garantizando que cada recurso sea diferenciable.

### Propósito de los triggers

Los triggers en `null_resource` sirven para forzar la recreación del recurso cuando cambian sus valores. Terraform compara los triggers del estado actual con los de la configuración deseada. Si detecta cambios, destruye y recrea el recurso.

El UUID y timestamp aseguran unicidad: cada vez que se genera un recurso, tiene identificadores únicos que Terraform puede rastrear. Esto es útil para forzar ejecuciones de provisioners o para simular recursos que necesitan actualizarse.

---

## 3. Prototype

### Proceso de clonación profunda

El patrón Prototype permite crear copias independientes de un objeto plantilla sin afectar el original. El proceso usa `copy.deepcopy()` que realiza una copia recursiva de todo el árbol de objetos.

```python
class ResourcePrototype:
    def __init__(self, template: dict):
        self.template = template

    def clone(self, mutator: Callable[[dict], None]) -> dict:
        new_copy = deepcopy(self.template)
        mutator(new_copy)
        return new_copy
```

El flujo es:
1. Se crea un prototipo con una plantilla base (template)
2. Al llamar `clone()`, se hace una copia profunda del template
3. Se aplica una función mutador que personaliza la copia
4. Se retorna la copia modificada

La copia profunda asegura que modificaciones en el clon no afecten al template original ni a otros clones previos.

### Rol del mutator

El `mutator` es una función que recibe el diccionario clonado y lo modifica en el lugar. Esto permite personalizar cada clon de forma flexible sin duplicar código.

Por ejemplo, para renombrar recursos:

```python
def mutator(block):
    res = block["resource"]["null_resource"].pop("app")
    block["resource"]["null_resource"]["app_0"] = res
```

Este mutator extrae el recurso con clave "app" y lo renombra a "app_0". Cada clon puede tener su propio mutator, generando variaciones del prototipo original.

---

## 4. Composite

### Agregación de múltiples bloques

`CompositeModule` implementa el patrón Composite para tratar múltiples bloques de configuración como una unidad lógica. Mantiene una lista de hijos (children) que representan bloques individuales.

```python
class CompositeModule:
    def __init__(self):
        self.children: List[Dict] = []

    def add(self, block: Dict):
        self.children.append(block)

    def export(self) -> Dict:
        merged: Dict = {"resource": {}}
        for child in self.children:
            for rtype, resources in child["resource"].items():
                merged["resource"].setdefault(rtype, {}).update(resources)
        return merged
```

El método `add()` agrega bloques a la colección. El método `export()` combina todos los bloques hijos en un solo diccionario JSON válido para Terraform.

### Proceso de merge

El merge funciona iterando sobre cada hijo y extrayendo sus recursos por tipo (ej. "null_resource", "local_file"). Para cada tipo de recurso, usa `setdefault()` para crear la clave si no existe, y luego `update()` para fusionar los recursos de ese hijo.

Esto permite que múltiples bloques con diferentes recursos se combinen en un solo archivo `main.tf.json` sin conflictos, siempre que los nombres de recursos sean únicos.

---

## 5. Builder

### Orquestación de patrones

`InfrastructureBuilder` actúa como director que coordina Factory, Prototype y Composite para generar infraestructura compleja de forma fluida.

```python
class InfrastructureBuilder:
    def __init__(self):
        self.module = CompositeModule()

    def build_null_fleet(self, count: int):
        base = NullResourceFactory.create("app")
        proto = ResourcePrototype(base)
        for i in range(count):
            def mutator(block):
                res = block["resource"]["null_resource"].pop("app")
                block["resource"]["null_resource"][f"app_{i}"] = res
            self.module.add(proto.clone(mutator))
        return self

    def export(self, path: str = "terraform/main.tf.json"):
        with open(path, "w") as f:
            json.dump(self.module.export(), f, indent=2)
```

### Flujo completo

1. **Factory**: Crea un recurso base usando `NullResourceFactory.create("app")`
2. **Prototype**: Envuelve el recurso base en un `ResourcePrototype`
3. **Clone + Mutator**: Para cada iteración, clona el prototipo y aplica un mutator que renombra el recurso (app → app_0, app_1, etc.)
4. **Composite**: Cada clon se agrega al `CompositeModule` usando `add()`
5. **Export**: Finalmente, `export()` fusiona todos los recursos del composite y escribe el JSON a disco

Este patrón permite generar N recursos similares pero personalizados con mínimo código y máxima flexibilidad. La interfaz fluida (retorna `self`) permite encadenar llamadas como `builder.build_null_fleet(15).export()`.

---

## Diagrama UML Simplificado

```
┌─────────────────────────┐
│   SingletonMeta         │
│   (metaclass)           │
│─────────────────────────│
│ + _instances: dict      │
│ + _lock: Lock           │
│ + __call__()            │
└─────────────────────────┘
         △
         │ metaclass
         │
┌─────────────────────────┐
│   ConfigSingleton       │
│─────────────────────────│
│ + env_name: str         │
│ + settings: dict        │
│ + created_at: str       │
└─────────────────────────┘

┌─────────────────────────┐
│ NullResourceFactory     │
│─────────────────────────│
│ + create(name, triggers)│
└─────────────────────────┘

┌─────────────────────────┐
│   ResourcePrototype     │
│─────────────────────────│
│ + template: dict        │
│ + clone(mutator)        │
└─────────────────────────┘

┌─────────────────────────┐
│   CompositeModule       │
│─────────────────────────│
│ + children: List[Dict]  │
│ + add(block)            │
│ + export()              │
└─────────────────────────┘

┌─────────────────────────┐
│ InfrastructureBuilder   │
│─────────────────────────│
│ + module: Composite     │
│ + build_null_fleet()    │
│ + export(path)          │
└────┬────────────────────┘
     │ usa
     ├──→ NullResourceFactory
     ├──→ ResourcePrototype
     └──→ CompositeModule
```

### Flujo de interacción

```
Builder
  │
  ├─→ Factory.create("app")  ──→ recurso_base
  │
  ├─→ Prototype(recurso_base)  ──→ prototipo
  │
  └─→ for i in range(count):
        ├─→ prototipo.clone(mutator)  ──→ clon_i
        │
        └─→ Composite.add(clon_i)

  ├─→ Composite.export()  ──→ merged_dict
  │
  └─→ write to JSON file
```

---

## Conclusión

Los cinco patrones trabajan en conjunto para generar infraestructura de forma modular y escalable:

- **Singleton** centraliza la configuración global
- **Factory** estandariza la creación de recursos
- **Prototype** permite clonación eficiente con variaciones
- **Composite** agrupa múltiples recursos en una unidad
- **Builder** orquesta todo el proceso con una API fluida

Esta arquitectura facilita el mantenimiento, testing y extensión del código generador de infraestructura.
