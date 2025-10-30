"""Patrón Builder
Construye de manera fluida configuraciones Terraform locales combinando los patrones Factory, Prototype y Composite.
"""

from typing import Dict, Any
import os
import json

from .factory import NullResourceFactory
from .composite import CompositeModule
from .prototype import ResourcePrototype

class InfrastructureBuilder:
    """Builder fluido que combina los patrones Factory, Prototype y Composite para crear módulos Terraform."""

    def __init__(self, env_name: str) -> None:
        """
        Inicializa el builder con un nombre de entorno y una instancia de módulo compuesto.
        """
        self.env_name = env_name
        self._module = CompositeModule(name=env_name)

    #  Métodos de construcción (steps) 

    def build_null_fleet(self, count: int = 5) -> "InfrastructureBuilder":
        """
        Construye una flota de `null_resource` clonados a partir de un prototipo base.
        Cada recurso tiene un trigger que lo identifica por índice, y un nombre válido.
        """
        # Se crea un prototipo reutilizable a partir de un recurso null de fábrica
        base_proto = ResourcePrototype(
            NullResourceFactory.create("placeholder")
        )

        for i in range(count):
            def mutator(d: Dict[str, Any], idx=i) -> None:
                """
                Función mutadora: modifica el nombre del recurso clonado
                e inserta un trigger identificador con el índice correspondiente.
                """
                res_block = d["resource"][0]["null_resource"][0]
                # Nombre original del recurso (por defecto "placeholder")
                original_name = next(iter(res_block.keys()))
                # Nuevo nombre válido: empieza con letra y contiene índice
                new_name = f"{original_name}_{idx}"
                # Renombramos la clave en el dict
                res_block[new_name] = res_block.pop(original_name)
                # Añadimos el trigger de índice
                res_block[new_name][0]["triggers"]["index"] = idx

            # Clonamos el prototipo y aplicamos la mutación
            clone = base_proto.clone(mutator).data
            # Agregamos el recurso clonado al módulo compuesto
            self._module.add(clone)

        return self

    def add_custom_resource(self, name: str, triggers: Dict[str, Any]) -> "InfrastructureBuilder":
        """
        Agrega un recurso null personalizado al módulo compuesto.

        Args:
            name: nombre del recurso.
            triggers: diccionario de triggers personalizados.
        Returns:
            self: permite encadenar llamadas.
        """
        self._module.add(NullResourceFactory.create(name, triggers))
        return self

    def build_group(self, group_name: str, resource_names: list, tags: Dict[str, Any] = None) -> "InfrastructureBuilder":
        """
        Crea un submódulo (grupo) de recursos con tags comunes.

        Este método utiliza la funcionalidad de submódulos de CompositeModule para organizar
        recursos relacionados bajo un grupo lógico. Todos los recursos del grupo comparten
        los mismos tags, facilitando la organización y el filtrado en Terraform.

        Args:
            group_name: nombre del grupo/submódulo.
            resource_names: lista de nombres de recursos a incluir en el grupo.
            tags: diccionario de tags comunes para todos los recursos del grupo.

        Returns:
            self: permite encadenar llamadas.

        Ejemplo:
            builder.build_group("web_tier", ["web1", "web2"], {"tier": "frontend", "env": "prod"})
        """
        tags = tags or {}

        # Crear submódulo para el grupo
        group_module = CompositeModule(name=group_name)

        # Agregar recursos al grupo con tags comunes
        for resource_name in resource_names:
            # Crear triggers que incluyen los tags del grupo
            triggers = {"group": group_name}
            triggers.update(tags)

            # Crear recurso y agregarlo al submódulo
            resource = NullResourceFactory.create(resource_name, triggers)
            group_module.add(resource)

        # Agregar el submódulo al módulo principal
        self._module.add_submodule(group_module)

        return self

    #  Método final (exportación) 

    def export(self, path: str) -> None:
        """
        Exporta el módulo compuesto a un archivo JSON compatible con Terraform.

        Args:
            path: ruta de destino del archivo `.tf.json`.
        """
        data = self._module.export()

        # Asegura que el directorio destino exista
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # Escribe el archivo con indentación legible
        with open(path, "w") as f:
            json.dump(data, f, indent=4)

        print(f"[Builder] Terraform JSON escrito en: {path}")
