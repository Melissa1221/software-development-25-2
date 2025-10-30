"""Patrón Adapter

Adapta formatos de configuración de otros sistemas de IaC (como Ansible, Puppet, CloudFormation)
al formato Terraform JSON que maneja nuestro sistema.
"""

from typing import Dict, Any, List
import yaml


class AnsibleToTerraformAdapter:
    """
    Adaptador que convierte tasks de Ansible playbooks al formato Terraform JSON.

    Ansible usa un formato YAML con tasks que ejecutan módulos. Este adapter
    traduce tasks comunes de Ansible a recursos Terraform equivalentes.
    """

    # Mapeo de módulos Ansible a tipos de recursos Terraform
    MODULE_MAPPING = {
        "command": "null_resource",
        "shell": "null_resource",
        "file": "local_file",
        "template": "local_file",
        "copy": "local_file",
    }

    def __init__(self, ansible_yaml: str) -> None:
        """
        Inicializa el adapter con un string YAML de Ansible.

        Args:
            ansible_yaml: String con contenido de playbook Ansible en formato YAML.
        """
        self.ansible_data = yaml.safe_load(ansible_yaml)

    def adapt(self) -> Dict[str, Any]:
        """
        Convierte el playbook Ansible a formato Terraform JSON.

        Returns:
            Diccionario con estructura Terraform JSON válida.
        """
        terraform_resources = []

        # Procesar cada play en el playbook
        for play in self.ansible_data:
            if "tasks" not in play:
                continue

            # Convertir cada task
            for task in play["tasks"]:
                resource = self._convert_task(task)
                if resource:
                    terraform_resources.append(resource)

        return {"resource": terraform_resources}

    def _convert_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convierte una task individual de Ansible a recurso Terraform.

        Args:
            task: Diccionario representando una task de Ansible.

        Returns:
            Diccionario con recurso Terraform o None si no se puede convertir.
        """
        # Obtener el nombre de la task
        task_name = task.get("name", "unnamed_task").lower().replace(" ", "_")

        # Identificar el módulo Ansible usado
        ansible_module = None
        module_args = {}

        for key, value in task.items():
            if key in self.MODULE_MAPPING:
                ansible_module = key
                module_args = value if isinstance(value, dict) else {"cmd": value}
                break

        if not ansible_module:
            return None

        # Mapear al tipo de recurso Terraform
        terraform_type = self.MODULE_MAPPING[ansible_module]

        # Construir el recurso según el tipo
        if terraform_type == "null_resource":
            return self._build_null_resource(task_name, ansible_module, module_args)
        elif terraform_type == "local_file":
            return self._build_local_file(task_name, module_args)

        return None

    def _build_null_resource(self, name: str, module: str,
                            args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construye un recurso null_resource para comandos de Ansible.

        Args:
            name: Nombre del recurso.
            module: Módulo Ansible original (command/shell).
            args: Argumentos del módulo Ansible.

        Returns:
            Diccionario con recurso null_resource.
        """
        # Extraer el comando
        command = args.get("cmd") or args.get("_raw_params", "")

        return {
            "null_resource": [{
                name: [{
                    "triggers": {
                        "ansible_module": module,
                        "command": command,
                    },
                    "provisioner": [{
                        "local-exec": {
                            "command": command
                        }
                    }]
                }]
            }]
        }

    def _build_local_file(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construye un recurso local_file para operaciones de archivo de Ansible.

        Args:
            name: Nombre del recurso.
            args: Argumentos del módulo Ansible.

        Returns:
            Diccionario con recurso local_file.
        """
        # Extraer path y contenido
        dest = args.get("dest") or args.get("path", f"/tmp/{name}")
        content = args.get("content", "")
        src = args.get("src", "")

        # Si hay src pero no content, indicarlo en el contenido
        if src and not content:
            content = f"# Source: {src}"

        return {
            "local_file": [{
                name: [{
                    "filename": dest,
                    "content": content,
                    "file_permission": args.get("mode", "0644")
                }]
            }]
        }


class CloudFormationToTerraformAdapter:
    """
    Adaptador que convierte templates de CloudFormation al formato Terraform JSON.

    Implementación simplificada que maneja recursos básicos.
    """

    # Mapeo simplificado de recursos CloudFormation a Terraform
    RESOURCE_MAPPING = {
        "AWS::EC2::Instance": "aws_instance",
        "AWS::S3::Bucket": "aws_s3_bucket",
        "AWS::Lambda::Function": "aws_lambda_function",
    }

    def __init__(self, cfn_template: Dict[str, Any]) -> None:
        """
        Inicializa el adapter con un template de CloudFormation.

        Args:
            cfn_template: Diccionario con template CloudFormation.
        """
        self.cfn_template = cfn_template

    def adapt(self) -> Dict[str, Any]:
        """
        Convierte el template CloudFormation a formato Terraform JSON.

        Returns:
            Diccionario con estructura Terraform JSON.
        """
        terraform_resources = []

        resources = self.cfn_template.get("Resources", {})

        for resource_name, resource_def in resources.items():
            cfn_type = resource_def.get("Type")
            terraform_type = self.RESOURCE_MAPPING.get(cfn_type)

            if terraform_type:
                # Convertir propiedades CFN a argumentos Terraform
                properties = resource_def.get("Properties", {})

                resource = {
                    terraform_type: [{
                        resource_name.lower(): [{
                            # Simplificación: pasar properties directamente
                            # En producción, se necesitaría mapeo detallado por tipo
                            **properties,
                            "_cfn_type": cfn_type  # Metadata para referencia
                        }]
                    }]
                }

                terraform_resources.append(resource)

        return {"resource": terraform_resources}
