# Actividad 14: Patrones de Diseño para Infraestructura como Código

## Descripción del Proyecto

Este proyecto implementa un generador de configuración Terraform usando patrones de diseño clásicos de software. El sistema permite generar infraestructura declarativa mediante la composición de patrones Singleton, Factory, Prototype, Composite, Builder y Adapter.

## Estructura del Proyecto

```
Actividad14-CC3S2/
├── iac_patterns/               # Módulos de patrones de diseño
│   ├── singleton.py           # Patrón Singleton (config global)
│   ├── factory.py             # Patrón Factory (creación de recursos)
│   ├── prototype.py           # Patrón Prototype (clonación de recursos)
│   ├── composite.py           # Patrón Composite (agregación de recursos)
│   ├── builder.py             # Patrón Builder (construcción fluida)
│   ├── mutators.py            # Funciones mutadoras para Prototype
│   └── adapter.py             # Patrón Adapter (conversión de formatos)
├── tests/                      # Suite de tests con pytest
│   ├── conftest.py            # Fixtures compartidas
│   └── test_all_patterns.py  # Tests de todos los patrones
├── Fase1/                      # Análisis de patrones
│   └── Entregable_Fase1.md    # Explicación detallada de 5 patrones
├── Fase2/                      # Ejercicios de extensión
│   ├── Ejercicio2.1/          # reset() en Singleton
│   ├── Ejercicio2.2/          # TimestampedNullResourceFactory
│   ├── Ejercicio2.3/          # Mutadores con local_file
│   ├── Ejercicio2.4/          # Submódulos en Composite
│   └── Ejercicio2.5/          # build_group() en Builder
├── Fase3/                      # Desafíos avanzados
│   ├── Desafio3.1_Comparativa.md        # Factory vs Prototype
│   ├── Desafio3.2_Adapter_evidencia.md  # Implementación Adapter
│   └── Desafio3.3_Pytest_evidencia.md   # Suite de tests
├── terraform/                  # Archivos Terraform generados
└── README.md                   # Este archivo
```

## Instalación

### Requisitos

- Python 3.9+
- Terraform 1.5+ (para validar salida generada)
- PyYAML (para adapter de Ansible)
- pytest (para ejecutar tests)

### Setup

```bash
# Clonar el repositorio
cd Actividad14-CC3S2

# Instalar dependencias
pip install pyyaml pytest pytest-cov

# Verificar instalación
python3 -m pytest tests/ -v
```

## Patrones Implementados

### 1. Singleton

**Propósito:** Garantizar una única instancia de configuración global.

**Características:**
- Thread-safe con `threading.Lock`
- Método `reset()` para limpiar configuración
- Preserva timestamp de creación

**Ejemplo:**
```python
from iac_patterns.singleton import ConfigSingleton

config = ConfigSingleton(env_name="production")
config.set("database", "postgres")
config.set("port", 5432)

# Otra referencia obtiene la misma instancia
another_ref = ConfigSingleton()
print(another_ref.get("database"))  # "postgres"
```

### 2. Factory

**Propósito:** Encapsular creación de recursos Terraform con configuración consistente.

**Características:**
- Genera UUID únicos automáticamente
- Agrega timestamps a todos los recursos
- Extensible mediante herencia (`TimestampedNullResourceFactory`)

**Ejemplo:**
```python
from iac_patterns.factory import NullResourceFactory, TimestampedNullResourceFactory

# Factory estándar
resource = NullResourceFactory.create("web_server", {"region": "us-east-1"})

# Factory con timestamp personalizado
resource = TimestampedNullResourceFactory.create(
    "app_server",
    timestamp_format="%Y-%m-%d %H:%M:%S"
)
```

### 3. Prototype

**Propósito:** Clonar recursos existentes y aplicar variaciones mediante mutadores.

**Características:**
- Deep copy para inmutabilidad
- Mutadores personalizables
- Funciones mutadoras reutilizables en `mutators.py`

**Ejemplo:**
```python
from iac_patterns.prototype import ResourcePrototype
from iac_patterns.mutators import rename_resource, convert_null_to_local_file

base = NullResourceFactory.create("base_app")
proto = ResourcePrototype(base)

# Clonar con renombrado
clone1 = proto.clone(lambda d: rename_resource(d, "base_app", "app_instance_1"))

# Clonar y convertir a local_file
clone2 = proto.clone(lambda d: convert_null_to_local_file(
    d, filename="/etc/config.txt", content="Config data"
))
```

### 4. Composite

**Propósito:** Tratar múltiples recursos como una unidad lógica, con soporte para jerarquías anidadas.

**Características:**
- Submódulos anidados recursivos
- Método `count_resources()` para contar recursivamente
- Export recursivo a JSON válido

**Ejemplo:**
```python
from iac_patterns.composite import CompositeModule

root = CompositeModule(name="infrastructure")

# Submódulo de red
network = CompositeModule(name="network")
network.add(NullResourceFactory.create("vpc"))
network.add(NullResourceFactory.create("subnet"))

# Submódulo de aplicación
app = CompositeModule(name="application")
app.add(NullResourceFactory.create("server"))

# Jerarquía
root.add_submodule(network)
root.add_submodule(app)

print(f"Total recursos: {root.count_resources()}")  # 3
exported = root.export()  # Todos los recursos en un JSON
```

### 5. Builder

**Propósito:** Orquestar Factory, Prototype y Composite con interfaz fluida.

**Características:**
- Método `build_null_fleet()` para generar N recursos
- Método `build_group()` para agrupar recursos con tags comunes
- Encadenamiento fluido de llamadas
- Export directo a archivos `.tf.json`

**Ejemplo:**
```python
from iac_patterns.builder import InfrastructureBuilder

(InfrastructureBuilder(env_name="production")
    .build_null_fleet(count=10)
    .build_group("web_tier", ["nginx", "haproxy"], {"tier": "frontend"})
    .build_group("data_tier", ["postgres", "redis"], {"tier": "backend"})
    .add_custom_resource("monitoring", {"type": "prometheus"})
    .export("terraform/main.tf.json"))
```

### 6. Adapter

**Propósito:** Convertir configuraciones de otros sistemas IaC (Ansible, CloudFormation) a Terraform JSON.

**Características:**
- `AnsibleToTerraformAdapter` para playbooks de Ansible
- `CloudFormationToTerraformAdapter` para templates AWS
- Mapeo extensible de recursos

**Ejemplo:**
```python
from iac_patterns.adapter import AnsibleToTerraformAdapter

ansible_yaml = """
- name: Setup server
  hosts: all
  tasks:
    - name: Install nginx
      command: apt-get install -y nginx
"""

adapter = AnsibleToTerraformAdapter(ansible_yaml)
terraform_json = adapter.adapt()
```

## Ejercicios Implementados

### Fase 2: Extensiones

#### Ejercicio 2.1: reset() en Singleton
- Método que limpia `settings` pero preserva `created_at`
- Útil para resetear configuración entre ciclos
- [Evidencia](Fase2/Ejercicio2.1/evidencia.md)

#### Ejercicio 2.2: TimestampedNullResourceFactory
- Factory especializada con formato de timestamp personalizado
- Hereda de `NullResourceFactory`
- Soporta cualquier formato strftime
- [Evidencia](Fase2/Ejercicio2.2/evidencia.md)

#### Ejercicio 2.3: Mutadores con local_file
- Función `convert_null_to_local_file()` para transformar recursos
- Funciones adicionales: `rename_resource()`, `add_trigger()`
- Módulo `mutators.py` con funciones reutilizables
- [Evidencia](Fase2/Ejercicio2.3/evidencia.md)

#### Ejercicio 2.4: Submódulos en Composite
- Soporte para `CompositeModule` anidados
- Método `add_submodule()` explícito
- Export recursivo multinivel
- [Evidencia](Fase2/Ejercicio2.4/evidencia.md)

#### Ejercicio 2.5: build_group() en Builder
- Método para crear grupos de recursos con tags comunes
- Usa submódulos del Ejercicio 2.4
- Ideal para organización por tier/región/equipo
- [Evidencia](Fase2/Ejercicio2.5/evidencia.md)

### Fase 3: Desafíos

#### Desafío 3.1: Comparativa Factory vs Prototype
- Análisis de 300 palabras sobre cuándo usar cada patrón
- Discusión de complementariedad
- [Documento completo](Fase3/Desafio3.1_Comparativa.md)

#### Desafío 3.2: Implementación de Adapter
- Adapter para Ansible (command, shell, file modules)
- Adapter para CloudFormation (S3, Lambda, EC2)
- Tests completos de conversión
- [Evidencia](Fase3/Desafio3.2_Adapter_evidencia.md)

#### Desafío 3.3: Suite de Tests con Pytest
- 32 tests organizados por patrón
- Fixtures reutilizables en `conftest.py`
- Tests parametrizados y de integración
- 100% de tests pasando
- [Evidencia](Fase3/Desafio3.3_Pytest_evidencia.md)

## Uso del Sistema

### Ejemplo Básico: Generar Flota de Servidores

```python
from iac_patterns.builder import InfrastructureBuilder

builder = InfrastructureBuilder(env_name="staging")
builder.build_null_fleet(count=5)
builder.export("terraform/staging.tf.json")
```

### Ejemplo Avanzado: Infraestructura Multi-Tier

```python
from iac_patterns.builder import InfrastructureBuilder

(InfrastructureBuilder(env_name="production")
    # Frontend tier
    .build_group("frontend", ["nginx_1", "nginx_2", "haproxy"],
                {"tier": "web", "public": "true", "environment": "prod"})

    # Application tier
    .build_group("backend", ["api_server_1", "api_server_2", "worker_1"],
                {"tier": "app", "public": "false", "environment": "prod"})

    # Data tier
    .build_group("database", ["postgres_primary", "postgres_replica"],
                {"tier": "data", "public": "false", "environment": "prod"})

    # Monitoring
    .add_custom_resource("prometheus", {"type": "monitoring", "port": 9090})
    .add_custom_resource("grafana", {"type": "dashboard", "port": 3000})

    # Exportar
    .export("terraform/production_infrastructure.tf.json"))
```

### Ejemplo: Migración desde Ansible

```python
from iac_patterns.adapter import AnsibleToTerraformAdapter
import json

ansible_playbook = """
- name: Configure web servers
  hosts: web
  tasks:
    - name: Install nginx
      command: apt-get install -y nginx

    - name: Copy nginx config
      file:
        path: /etc/nginx/nginx.conf
        content: |
          server {
            listen 80;
            server_name example.com;
          }
        mode: '0644'

    - name: Start nginx
      shell: systemctl start nginx
"""

adapter = AnsibleToTerraformAdapter(ansible_playbook)
terraform_config = adapter.adapt()

with open("terraform/migrated_from_ansible.tf.json", "w") as f:
    json.dump(terraform_config, f, indent=2)
```

## Ejecutar Tests

```bash
# Ejecutar toda la suite
pytest tests/ -v

# Ejecutar con coverage
pytest tests/ --cov=iac_patterns --cov-report=html

# Ejecutar solo un patrón específico
pytest tests/test_all_patterns.py::TestSingleton -v

# Ejecutar con output detallado
pytest tests/ -v --tb=short
```

**Resultado esperado:**
```
============================== 32 passed in 0.05s ==============================
```

## Validar Salida con Terraform

```bash
# Generar configuración
python3 -c "
from iac_patterns.builder import InfrastructureBuilder
(InfrastructureBuilder('test')
    .build_null_fleet(5)
    .export('terraform/test.tf.json'))
"

# Validar con Terraform
cd terraform
terraform init
terraform validate
terraform plan
```

## Patrones y Arquitectura

### Flujo de Datos

```
Factory
  │
  ├──> crea recurso base
  │
  ↓
Prototype
  │
  ├──> clona con variaciones (mutators)
  │
  ↓
Composite
  │
  ├──> agrega recursos en jerarquía
  │
  ↓
Builder
  │
  ├──> orquesta todo el proceso
  │
  ↓
JSON export -> Terraform
```

### Interacción entre Patrones

1. **Singleton** mantiene configuración global accesible en todo el sistema
2. **Factory** crea recursos base con estructura consistente
3. **Prototype** clona y varía recursos eficientemente
4. **Composite** organiza recursos en jerarquías lógicas
5. **Builder** orquesta Factory + Prototype + Composite con API fluida
6. **Adapter** permite importar configuraciones de otros sistemas

## Casos de Uso Reales

### 1. Generación Masiva de Entornos

Generar 100 entornos de desarrollo idénticos:

```python
for i in range(1, 101):
    (InfrastructureBuilder(env_name=f"dev{i}")
        .build_group("app", [f"server{i}"], {"env": f"dev{i}"})
        .export(f"terraform/dev{i}/main.tf.json"))
```

### 2. Infraestructura Multi-Región

```python
regions = ["us-east-1", "us-west-2", "eu-west-1"]

root = CompositeModule(name="global")

for region in regions:
    regional = CompositeModule(name=region)
    # Agregar recursos específicos de cada región
    regional.add(NullResourceFactory.create(f"vpc_{region}"))
    root.add_submodule(regional)

# Export unificado
with open("terraform/multi_region.tf.json", "w") as f:
    json.dump(root.export(), f, indent=2)
```

### 3. Migración Gradual desde Ansible

```python
# Leer todos los playbooks existentes
playbook_files = glob.glob("ansible/*.yml")

for playbook_path in playbook_files:
    with open(playbook_path) as f:
        ansible_content = f.read()

    adapter = AnsibleToTerraformAdapter(ansible_content)
    terraform = adapter.adapt()

    output_name = Path(playbook_path).stem
    with open(f"terraform/{output_name}.tf.json", "w") as f:
        json.dump(terraform, f, indent=2)
```

## Documentación Adicional

- [Fase 1: Análisis de Patrones](Fase1/Entregable_Fase1.md) - Explicación detallada de cada patrón
- [Fase 2: Ejercicios](Fase2/) - Evidencias de extensiones implementadas
- [Fase 3: Desafíos](Fase3/) - Adapter, comparativas y tests
