"""
Test de validación para el patrón Adapter.
Verifica conversión de Ansible y CloudFormation a Terraform.
"""

import sys
from pathlib import Path
import json

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from iac_patterns.adapter import AnsibleToTerraformAdapter, CloudFormationToTerraformAdapter


def test_ansible_command_module():
    """Valida conversión de módulo command de Ansible"""

    print("=== Test 1: Ansible command module ===\n")

    ansible_playbook = """
- name: Configure servers
  hosts: all
  tasks:
    - name: Install nginx
      command: apt-get install -y nginx

    - name: Start service
      shell: systemctl start nginx
"""

    adapter = AnsibleToTerraformAdapter(ansible_playbook)
    terraform = adapter.adapt()

    print(f"✓ Recursos convertidos: {len(terraform['resource'])}")
    print(json.dumps(terraform, indent=2))

    assert len(terraform["resource"]) == 2, f"❌ Esperaba 2 recursos"

    # Validar primer recurso (command)
    first_resource = terraform["resource"][0]
    assert "null_resource" in first_resource, "❌ Primer recurso debería ser null_resource"

    null_res = first_resource["null_resource"][0]
    res_name = list(null_res.keys())[0]
    config = null_res[res_name][0]

    assert "triggers" in config, "❌ Falta triggers"
    assert config["triggers"]["ansible_module"] == "command", "❌ Módulo incorrecto"
    assert "nginx" in config["triggers"]["command"], "❌ Comando incorrecto"

    # Validar provisioner
    assert "provisioner" in config, "❌ Falta provisioner"
    assert "local-exec" in config["provisioner"][0], "❌ Falta local-exec"

    print("\n✅ Validación exitosa: command module convertido correctamente\n")


def test_ansible_file_module():
    """Valida conversión de módulo file de Ansible"""

    print("=== Test 2: Ansible file module ===\n")

    ansible_playbook = """
- name: Manage files
  hosts: localhost
  tasks:
    - name: Create config file
      file:
        path: /etc/app/config.ini
        content: |
          [database]
          host=localhost
          port=5432
        mode: '0600'
"""

    adapter = AnsibleToTerraformAdapter(ansible_playbook)
    terraform = adapter.adapt()

    print(json.dumps(terraform, indent=2))

    assert len(terraform["resource"]) == 1, f"❌ Esperaba 1 recurso"

    resource = terraform["resource"][0]
    assert "local_file" in resource, "❌ Debería ser local_file"

    local_file = resource["local_file"][0]
    file_name = list(local_file.keys())[0]
    config = local_file[file_name][0]

    assert config["filename"] == "/etc/app/config.ini", "❌ Filename incorrecto"
    assert config["file_permission"] == "0600", "❌ Permisos incorrectos"

    print("\n✅ Validación exitosa: file module convertido correctamente\n")


def test_ansible_mixed_tasks():
    """Valida conversión de playbook con múltiples tipos de tasks"""

    print("=== Test 3: Ansible mixed tasks ===\n")

    ansible_playbook = """
- name: Setup application
  hosts: all
  tasks:
    - name: Update apt cache
      command: apt-get update

    - name: Create app directory
      file:
        path: /opt/myapp
        content: ""
        mode: '0755'

    - name: Download binary
      shell: curl -o /opt/myapp/app https://example.com/app

    - name: Set executable
      file:
        path: /opt/myapp/app
        mode: '0755'
"""

    adapter = AnsibleToTerraformAdapter(ansible_playbook)
    terraform = adapter.adapt()

    print(f"✓ Total recursos: {len(terraform['resource'])}")

    assert len(terraform["resource"]) == 4, f"❌ Esperaba 4 recursos"

    # Contar tipos
    null_count = sum(1 for r in terraform["resource"] if "null_resource" in r)
    file_count = sum(1 for r in terraform["resource"] if "local_file" in r)

    print(f"✓ null_resource: {null_count}")
    print(f"✓ local_file: {file_count}")

    assert null_count == 2, "❌ Debería haber 2 null_resource (command/shell)"
    assert file_count == 2, "❌ Debería haber 2 local_file"

    print("\n✅ Validación exitosa: múltiples tasks convertidas\n")


def test_cloudformation_adapter():
    """Valida conversión de CloudFormation a Terraform"""

    print("=== Test 4: CloudFormation adapter ===\n")

    cfn_template = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "Simple S3 bucket",
        "Resources": {
            "MyBucket": {
                "Type": "AWS::S3::Bucket",
                "Properties": {
                    "BucketName": "my-unique-bucket-name",
                    "VersioningConfiguration": {
                        "Status": "Enabled"
                    }
                }
            },
            "MyLambda": {
                "Type": "AWS::Lambda::Function",
                "Properties": {
                    "FunctionName": "my-function",
                    "Runtime": "python3.9",
                    "Handler": "index.handler"
                }
            }
        }
    }

    adapter = CloudFormationToTerraformAdapter(cfn_template)
    terraform = adapter.adapt()

    print(json.dumps(terraform, indent=2)[:500] + "...")

    assert len(terraform["resource"]) == 2, f"❌ Esperaba 2 recursos"

    # Buscar tipos
    types = set()
    for resource in terraform["resource"]:
        types.update(resource.keys())

    print(f"\n✓ Tipos Terraform generados: {types}")

    assert "aws_s3_bucket" in types, "❌ Falta aws_s3_bucket"
    assert "aws_lambda_function" in types, "❌ Falta aws_lambda_function"

    # Validar que se preservaron las propiedades
    for resource in terraform["resource"]:
        if "aws_s3_bucket" in resource:
            bucket = resource["aws_s3_bucket"][0]
            bucket_name = list(bucket.keys())[0]
            props = bucket[bucket_name][0]
            assert "BucketName" in props, "❌ Propiedades no preservadas"

    print("\n✅ Validación exitosa: CloudFormation convertido correctamente\n")


def test_empty_playbook():
    """Valida manejo de playbook vacío"""

    print("=== Test 5: Playbook vacío ===\n")

    ansible_playbook = """
- name: Empty playbook
  hosts: all
"""

    adapter = AnsibleToTerraformAdapter(ansible_playbook)
    terraform = adapter.adapt()

    print(f"✓ Recursos generados: {len(terraform['resource'])}")

    assert len(terraform["resource"]) == 0, "❌ No debería generar recursos"

    print("✅ Validación exitosa: playbook vacío manejado correctamente\n")


if __name__ == "__main__":
    test_ansible_command_module()
    test_ansible_file_module()
    test_ansible_mixed_tasks()
    test_cloudformation_adapter()
    test_empty_playbook()

    print("="*50)
    print("✅ TODOS LOS TESTS PASARON CORRECTAMENTE")
    print("="*50)
