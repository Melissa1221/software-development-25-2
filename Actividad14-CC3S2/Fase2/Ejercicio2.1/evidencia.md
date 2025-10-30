# Ejercicio 2.1: Método reset() en Singleton

## Implementación

Se agregó el método `reset()` a la clase `ConfigSingleton` en `iac_patterns/singleton.py:69-74`.

```python
def reset(self) -> None:
    """
    Limpia el diccionario de settings pero mantiene created_at intacto.
    Útil para resetear configuración sin perder la referencia temporal de creación.
    """
    self.settings.clear()
```

## Validación

El test ejecuta cuatro validaciones principales. Primero verifica que el método `reset()` limpia completamente el diccionario `settings`. Luego confirma que el timestamp `created_at` permanece sin cambios después del reset.

También valida que se puede agregar nueva configuración después de ejecutar reset. Finalmente comprueba que el patrón Singleton sigue funcionando correctamente y mantiene la misma instancia.

## Resultados

```
[OK] Settings antes de reset: {'database': 'postgres', 'port': 5432, 'host': 'localhost'}
[OK] created_at original: 2025-10-30T16:02:33.993920+00:00
[OK] Settings después de reset: {}
[OK] created_at después de reset: 2025-10-30T16:02:33.993920+00:00
[OK] Se puede agregar configuración después de reset: {'new_config': 'value'}
[OK] Singleton mantiene instancia única: c1 is c2 = True

[OK] Todas las validaciones pasaron correctamente
```

## Utilidad

Este método es útil para resetear la configuración del sistema sin perder la referencia temporal de cuándo se creó la instancia Singleton. Permite limpiar configuraciones entre diferentes ciclos de ejecución manteniendo la consistencia del patrón.
