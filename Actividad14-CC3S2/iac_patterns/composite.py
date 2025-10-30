"""Patrón Composite
Permite tratar múltiples recursos Terraform como una única unidad lógica o módulo compuesto.
"""

from typing import List, Dict, Any, Union

class CompositeModule:
    """
    Clase que agrega múltiples diccionarios de recursos Terraform como un módulo lógico único.
    Sigue el patrón Composite, donde se unifican estructuras individuales en una sola jerarquía.

    Soporta submódulos anidados, permitiendo construir jerarquías complejas de recursos.
    """

    def __init__(self, name: str = "root") -> None:
        """
        Inicializa la estructura compuesta como una lista vacía de recursos hijos.
        Cada hijo puede ser un diccionario de recursos o un CompositeModule anidado.

        Args:
            name: Nombre del módulo (útil para debugging y organización).
        """
        self.name = name
        self._children: List[Union[Dict[str, Any], "CompositeModule"]] = []

    def add(self, child: Union[Dict[str, Any], "CompositeModule"]) -> None:
        """
        Agrega un recurso o submódulo al módulo compuesto.

        Args:
            child: Puede ser un diccionario de recurso o un CompositeModule anidado.
        """
        self._children.append(child)

    def add_submodule(self, submodule: "CompositeModule") -> None:
        """
        Agrega un submódulo al módulo actual.

        Este método es equivalente a add() pero con nombre explícito para mayor claridad.

        Args:
            submodule: CompositeModule a agregar como hijo.
        """
        if not isinstance(submodule, CompositeModule):
            raise TypeError("submodule debe ser una instancia de CompositeModule")
        self._children.append(submodule)

    def export(self) -> Dict[str, Any]:
        """
        Exporta todos los recursos agregados a un único diccionario.

        Si hay submódulos anidados, exporta recursivamente todos sus recursos.
        Esta estructura se puede serializar directamente a un archivo Terraform JSON válido.

        Returns:
            Un diccionario con todos los recursos combinados bajo la clave "resource".
        """
        aggregated: Dict[str, Any] = {"resource": []}

        for child in self._children:
            if isinstance(child, CompositeModule):
                # Si es un submódulo, exportarlo recursivamente y combinar recursos
                submodule_export = child.export()
                aggregated["resource"].extend(submodule_export.get("resource", []))
            else:
                # Si es un diccionario de recurso, agregarlo directamente
                aggregated["resource"].extend(child.get("resource", []))

        return aggregated

    def count_resources(self) -> int:
        """
        Cuenta el total de recursos en este módulo y todos sus submódulos.

        Returns:
            Número total de recursos.
        """
        total = 0
        for child in self._children:
            if isinstance(child, CompositeModule):
                total += child.count_resources()
            else:
                total += len(child.get("resource", []))
        return total

    def __repr__(self) -> str:
        """Representación en string del módulo para debugging"""
        return f"CompositeModule(name='{self.name}', children={len(self._children)}, resources={self.count_resources()})"
