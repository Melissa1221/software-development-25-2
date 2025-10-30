# Desafío 3.2: Implementación del Patrón Adapter

## Descripción

Se implementaron dos adapters que convierten configuraciones de otros sistemas de IaC al formato Terraform JSON que maneja nuestro sistema. El primero es AnsibleToTerraformAdapter que convierte playbooks de Ansible. El segundo es CloudFormationToTerraformAdapter que convierte templates de AWS CloudFormation.

## Implementación

### AnsibleToTerraformAdapter

Convierte tasks de Ansible a recursos Terraform equivalentes.

El adapter mapea módulos de Ansible a tipos de recursos Terraform. Los comandos `command` y `shell` se convierten a `null_resource` con provisioner `local-exec`. Los módulos de archivos como `file`, `template` y `copy` se transforman en recursos `local_file`.

```python
class AnsibleToTerraformAdapter:
    MODULE_MAPPING = {
        "command": "null_resource",
        "shell": "null_resource",
        "file": "local_file",
        "template": "local_file",
        "copy": "local_file",
    }

    def adapt(self) -> Dict[str, Any]:
        """Convierte el playbook Ansible a formato Terraform JSON."""
        terraform_resources = []

        for play in self.ansible_data:
            if "tasks" not in play:
                continue

            for task in play["tasks"]:
                resource = self._convert_task(task)
                if resource:
                    terraform_resources.append(resource)

        return {"resource": terraform_resources}
```

### CloudFormationToTerraformAdapter

Convierte templates de CloudFormation a Terraform.

El adapter mapea tipos de recursos CloudFormation a sus equivalentes Terraform. Las instancias EC2 se convierten a `aws_instance`. Los buckets S3 se transforman en `aws_s3_bucket`. Las funciones Lambda se mapean a `aws_lambda_function`.

```python
class CloudFormationToTerraformAdapter:
    RESOURCE_MAPPING = {
        "AWS::EC2::Instance": "aws_instance",
        "AWS::S3::Bucket": "aws_s3_bucket",
        "AWS::Lambda::Function": "aws_lambda_function",
    }

    def adapt(self) -> Dict[str, Any]:
        """Convierte el template CloudFormation a formato Terraform JSON."""
        terraform_resources = []

        resources = self.cfn_template.get("Resources", {})

        for resource_name, resource_def in resources.items():
            cfn_type = resource_def.get("Type")
            terraform_type = self.RESOURCE_MAPPING.get(cfn_type)

            if terraform_type:
                properties = resource_def.get("Properties", {})
                # Construir recurso Terraform...
                terraform_resources.append(resource)

        return {"resource": terraform_resources}
```

## Validación

### Test 1: Ansible command module

**Input (Ansible YAML):**
```yaml
- name: Configure servers
  hosts: all
  tasks:
    - name: Install nginx
      command: apt-get install -y nginx

    - name: Start service
      shell: systemctl start nginx
```

**Output (Terraform JSON):**
```json
{
  "resource": [
    {
      "null_resource": [{
        "install_nginx": [{
          "triggers": {
            "ansible_module": "command",
            "command": "apt-get install -y nginx"
          },
          "provisioner": [{
            "local-exec": {
              "command": "apt-get install -y nginx"
            }
          }]
        }]
      }]
    },
    {
      "null_resource": [{
        "start_service": [{
          "triggers": {
            "ansible_module": "shell",
            "command": "systemctl start nginx"
          },
          "provisioner": [{
            "local-exec": {
              "command": "systemctl start nginx"
            }
          }]
        }]
      }]
    }
  ]
}
```

### Test 2: Ansible file module

**Input:**
```yaml
- name: Create config file
  file:
    path: /etc/app/config.ini
    content: |
      [database]
      host=localhost
      port=5432
    mode: '0600'
```

**Output:**
```json
{
  "resource": [{
    "local_file": [{
      "create_config_file": [{
        "filename": "/etc/app/config.ini",
        "content": "[database]\nhost=localhost\nport=5432\n",
        "file_permission": "0600"
      }]
    }]
  }]
}
```

### Test 4: CloudFormation adapter

**Input (CFN):**
```json
{
  "Resources": {
    "MyBucket": {
      "Type": "AWS::S3::Bucket",
      "Properties": {
        "BucketName": "my-unique-bucket-name",
        "VersioningConfiguration": {
          "Status": "Enabled"
        }
      }
    }
  }
}
```

**Output (Terraform):**
```json
{
  "resource": [{
    "aws_s3_bucket": [{
      "mybucket": [{
        "BucketName": "my-unique-bucket-name",
        "VersioningConfiguration": {
          "Status": "Enabled"
        },
        "_cfn_type": "AWS::S3::Bucket"
      }]
    }]
  }]
}
```

### Resultados completos

```
[OK] Validación exitosa: command module convertido correctamente
[OK] Validación exitosa: file module convertido correctamente
[OK] Validación exitosa: múltiples tasks convertidas
[OK] Validación exitosa: CloudFormation convertido correctamente
[OK] Validación exitosa: playbook vacío manejado correctamente

==================================================
[OK] TODOS LOS TESTS PASARON CORRECTAMENTE
==================================================
```

## Utilidad del Patrón Adapter

El patrón Adapter es crucial para facilitar migraciones entre sistemas de IaC. Permite migración gradual convirtiendo configuraciones existentes sin reescribir todo manualmente. Facilita la interoperabilidad integrando herramientas de diferentes ecosistemas.

Permite reutilizar configuraciones legacy sin abandonarlas completamente. Unifica infraestructura de múltiples fuentes en un formato único declarativo.

### Casos de uso reales

Los equipos que usan Ansible para configuración pueden migrar gradualmente a Terraform. La infraestructura AWS en CloudFormation se puede convertir para adoptar estrategias multi-cloud. Los pipelines legacy de Puppet o Chef se modernizan transformándolos a Terraform sin perder funcionalidad.

### Limitaciones

Esta implementación es simplificada y cubre casos básicos. En producción se necesitaría mapeo más completo de módulos y recursos. El manejo de variables y referencias entre recursos es esencial.

La validación de sintaxis y estructura garantizaría conversiones correctas. Los logs de advertencia informarían sobre conversiones parciales. El soporte para recursos específicos de cada proveedor ampliaría la cobertura del adapter.

## Conclusión

El patrón Adapter implementado demuestra cómo abstraer diferencias entre sistemas de IaC, facilitando la adopción de Terraform y la consolidación de infraestructura heterogénea bajo un único framework declarativo.
