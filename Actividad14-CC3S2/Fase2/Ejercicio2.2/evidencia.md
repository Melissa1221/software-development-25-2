# Ejercicio 2.2: TimestampedNullResourceFactory

## Implementación

Se creó la clase `TimestampedNullResourceFactory` que hereda de `NullResourceFactory` en `iac_patterns/factory.py:47-84`.

```python
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
        triggers.setdefault("factory_uuid", str(uuid.uuid4()))
        triggers.setdefault("timestamp", datetime.utcnow().strftime(timestamp_format))

        return {
            "resource": [{
                "null_resource": [{
                    name: [{
                        "triggers": triggers
                    }]
                }]
            }]
        }
```

## Validación

El test valida cinco aspectos principales de la factory especializada. El formato por defecto genera timestamps en el patrón legible `2025-10-30 16:03:30`. Los formatos personalizados como `%d/%m/%Y` producen resultados como `30/10/2025`.

Se compara con la factory original que usa formato ISO estándar. Cada llamada genera UUIDs únicos para garantizar identificadores diferentes. Los triggers personalizados que se pasan como parámetros se conservan correctamente en el recurso final.

## Resultados

```
[OK] Timestamp con formato por defecto: 2025-10-30 16:03:30
[OK] Formato válido: ^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$

[OK] Timestamp con formato personalizado: 30/10/2025
[OK] Formato válido: ^\d{2}/\d{2}/\d{4}$

[OK] Timestamp ISO de NullResourceFactory: 2025-10-30T16:03:30.669500
[OK] Formato ISO válido

[OK] UUID en TimestampedFactory: bb796d5e-1563-4359-b2e8-e45f9c302913
[OK] UUID en TimestampedFactory (custom): 5d6dd707-4aef-4fac-86e4-90ffe2df2bb0

[OK] Triggers personalizados conservados: {'region': 'us-east-1', 'environment': 'production',
  'factory_uuid': '9e8c7f68-af79-4143-a9e0-17f8cea64f9e', 'timestamp': '20251030'}
[OK] Timestamp compacto válido: 20251030

[OK] Todas las validaciones pasaron correctamente
```

## Utilidad

Esta especialización del patrón Factory permite generar timestamps legibles por humanos en logs y outputs de Terraform. Es especialmente útil para auditorías y reportes donde el formato ISO puede ser menos intuitivo. Al heredar de la clase base, mantiene toda la funcionalidad original mientras extiende el comportamiento de forma limpia.
