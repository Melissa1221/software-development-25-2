"""Patrón Factory
Encapsula la lógica de creación de objetos para recursos Terraform del tipo null_resource.
"""

from typing import Dict, Any, Optional
import uuid
from datetime import datetime

class NullResourceFactory:
    """
    Fábrica para crear bloques de recursos `null_resource` en formato Terraform JSON.
    Cada recurso incluye triggers personalizados y valores únicos para garantizar idempotencia.
    """

    @staticmethod
    def create(name: str, triggers: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Crea un bloque de recurso Terraform tipo `null_resource` con triggers personalizados.

        Args:
            name: Nombre del recurso dentro del bloque.
            triggers: Diccionario de valores personalizados que activan recreación del recurso.
                      Si no se proporciona, se inicializa con un UUID y un timestamp.

        Returns:
            Diccionario compatible con la estructura JSON de Terraform para null_resource.
        """
        triggers = triggers or {}

        # Agrega un trigger por defecto: UUID aleatorio para asegurar unicidad
        triggers.setdefault("factory_uuid", str(uuid.uuid4()))

        # Agrega un trigger con timestamp actual en UTC
        triggers.setdefault("timestamp", datetime.utcnow().isoformat())

        # Retorna el recurso estructurado como se espera en archivos .tf.json
        return {
            "resource": [{
                "null_resource": [{
                    name: [{
                        "triggers": triggers
                    }]
                }]
            }]
        }

class TimestampedNullResourceFactory(NullResourceFactory):
    """
    Fábrica especializada que hereda de NullResourceFactory y personaliza el formato de timestamp.
    Permite usar formatos de fecha legibles por humanos como '%Y-%m-%d %H:%M:%S'.
    """

    @staticmethod
    def create(name: str, triggers: Optional[Dict[str, Any]] = None,
               timestamp_format: str = "%Y-%m-%d %H:%M:%S") -> Dict[str, Any]:
        """
        Crea un recurso null_resource con timestamp en formato personalizado.

        Args:
            name: Nombre del recurso.
            triggers: Diccionario de triggers personalizados (opcional).
            timestamp_format: Formato strftime para el timestamp (por defecto: '%Y-%m-%d %H:%M:%S').

        Returns:
            Diccionario compatible con Terraform JSON incluyendo timestamp formateado.
        """
        triggers = triggers or {}

        # Agregar UUID único
        triggers.setdefault("factory_uuid", str(uuid.uuid4()))

        # Agregar timestamp con formato personalizado
        triggers.setdefault("timestamp", datetime.utcnow().strftime(timestamp_format))

        # Retornar estructura Terraform
        return {
            "resource": [{
                "null_resource": [{
                    name: [{
                        "triggers": triggers
                    }]
                }]
            }]
        }
