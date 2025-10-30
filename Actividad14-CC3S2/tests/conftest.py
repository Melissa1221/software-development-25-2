"""
Configuración de pytest con fixtures reutilizables para todos los tests.
"""

import pytest
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from iac_patterns.singleton import ConfigSingleton
from iac_patterns.factory import NullResourceFactory, TimestampedNullResourceFactory
from iac_patterns.prototype import ResourcePrototype
from iac_patterns.composite import CompositeModule
from iac_patterns.builder import InfrastructureBuilder


@pytest.fixture
def singleton_instance():
    """Fixture que proporciona una instancia limpia de ConfigSingleton."""
    instance = ConfigSingleton(env_name="test")
    instance.reset()  # Limpiar cualquier config previa
    yield instance
    instance.reset()  # Limpiar después del test


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


@pytest.fixture
def builder_instance():
    """Fixture que proporciona un InfrastructureBuilder."""
    return InfrastructureBuilder(env_name="test_env")


@pytest.fixture
def sample_triggers():
    """Fixture que proporciona triggers de ejemplo."""
    return {
        "environment": "test",
        "region": "us-east-1",
        "owner": "devops"
    }


@pytest.fixture
def ansible_playbook_yaml():
    """Fixture que proporciona un playbook Ansible de ejemplo."""
    return """
- name: Test playbook
  hosts: all
  tasks:
    - name: Run command
      command: echo "Hello World"

    - name: Create file
      file:
        path: /tmp/test.txt
        content: "Test content"
        mode: '0644'
"""


@pytest.fixture
def cloudformation_template():
    """Fixture que proporciona un template CloudFormation de ejemplo."""
    return {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Resources": {
            "TestBucket": {
                "Type": "AWS::S3::Bucket",
                "Properties": {
                    "BucketName": "test-bucket"
                }
            }
        }
    }
