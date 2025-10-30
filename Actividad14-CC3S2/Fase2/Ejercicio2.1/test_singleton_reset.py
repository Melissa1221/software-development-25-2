"""
Test de validación para el método reset() del Singleton.
Verifica que reset() limpie settings pero mantenga created_at intacto.
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path para importar iac_patterns
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from iac_patterns.singleton import ConfigSingleton

def test_reset():
    """Valida que reset() limpie settings pero preserve created_at"""

    # Crear instancia y guardar timestamp original
    c1 = ConfigSingleton(env_name="test")
    original_created = c1.created_at

    # Agregar configuraciones
    c1.set("database", "postgres")
    c1.set("port", 5432)
    c1.set("host", "localhost")

    print(f"✓ Settings antes de reset: {c1.settings}")
    print(f"✓ created_at original: {original_created}")

    # Ejecutar reset
    c1.reset()

    # Validar que settings está vacío
    assert c1.settings == {}, f"❌ settings no está vacío: {c1.settings}"
    print(f"✓ Settings después de reset: {c1.settings}")

    # Validar que created_at se mantiene
    assert c1.created_at == original_created, f"❌ created_at cambió: {c1.created_at}"
    print(f"✓ created_at después de reset: {c1.created_at}")

    # Verificar que se puede seguir usando después del reset
    c1.set("new_config", "value")
    assert c1.get("new_config") == "value", "❌ No se puede agregar config después de reset"
    print(f"✓ Se puede agregar configuración después de reset: {c1.settings}")

    # Verificar que es la misma instancia (patrón Singleton)
    c2 = ConfigSingleton()
    assert c2 is c1, "❌ No es la misma instancia (Singleton roto)"
    assert c2.settings == c1.settings, "❌ Las configuraciones no son compartidas"
    print(f"✓ Singleton mantiene instancia única: c1 is c2 = {c1 is c2}")

    print("\n✅ Todas las validaciones pasaron correctamente")

if __name__ == "__main__":
    test_reset()
