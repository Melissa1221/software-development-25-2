"""
Test de validación para TimestampedNullResourceFactory.
Verifica que el timestamp se genera en el formato personalizado.
"""

import sys
from pathlib import Path
import re

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from iac_patterns.factory import NullResourceFactory, TimestampedNullResourceFactory

def test_timestamped_factory():
    """Valida que TimestampedNullResourceFactory use formato personalizado"""

    # Test 1: Formato por defecto '%Y-%m-%d %H:%M:%S'
    resource1 = TimestampedNullResourceFactory.create("test_server")
    timestamp1 = resource1["resource"][0]["null_resource"][0]["test_server"][0]["triggers"]["timestamp"]

    print(f"✓ Timestamp con formato por defecto: {timestamp1}")

    # Validar que coincide con el patrón YYYY-MM-DD HH:MM:SS
    pattern_default = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
    assert re.match(pattern_default, timestamp1), f"❌ Formato incorrecto: {timestamp1}"
    print(f"✓ Formato válido: {pattern_default}")

    # Test 2: Formato personalizado '%d/%m/%Y'
    resource2 = TimestampedNullResourceFactory.create(
        "custom_server",
        timestamp_format="%d/%m/%Y"
    )
    timestamp2 = resource2["resource"][0]["null_resource"][0]["custom_server"][0]["triggers"]["timestamp"]

    print(f"\n✓ Timestamp con formato personalizado: {timestamp2}")

    # Validar formato DD/MM/YYYY
    pattern_custom = r'^\d{2}/\d{2}/\d{4}$'
    assert re.match(pattern_custom, timestamp2), f"❌ Formato incorrecto: {timestamp2}"
    print(f"✓ Formato válido: {pattern_custom}")

    # Test 3: Comparar con NullResourceFactory original (formato ISO)
    resource3 = NullResourceFactory.create("standard_server")
    timestamp3 = resource3["resource"][0]["null_resource"][0]["standard_server"][0]["triggers"]["timestamp"]

    print(f"\n✓ Timestamp ISO de NullResourceFactory: {timestamp3}")

    # Validar que el ISO tiene formato YYYY-MM-DDTHH:MM:SS.ffffff
    pattern_iso = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}$'
    assert re.match(pattern_iso, timestamp3), f"❌ Formato ISO incorrecto: {timestamp3}"
    print(f"✓ Formato ISO válido")

    # Test 4: Verificar que ambas factories incluyen UUID
    uuid1 = resource1["resource"][0]["null_resource"][0]["test_server"][0]["triggers"]["factory_uuid"]
    uuid2 = resource2["resource"][0]["null_resource"][0]["custom_server"][0]["triggers"]["factory_uuid"]

    print(f"\n✓ UUID en TimestampedFactory: {uuid1}")
    print(f"✓ UUID en TimestampedFactory (custom): {uuid2}")
    assert uuid1 != uuid2, "❌ Los UUIDs no son únicos"

    # Test 5: Verificar triggers personalizados
    custom_triggers = {"region": "us-east-1", "environment": "production"}
    resource4 = TimestampedNullResourceFactory.create(
        "prod_server",
        triggers=custom_triggers,
        timestamp_format="%Y%m%d"
    )
    triggers4 = resource4["resource"][0]["null_resource"][0]["prod_server"][0]["triggers"]

    print(f"\n✓ Triggers personalizados conservados: {triggers4}")
    assert triggers4["region"] == "us-east-1", "❌ Trigger region no se conservó"
    assert triggers4["environment"] == "production", "❌ Trigger environment no se conservó"
    assert "factory_uuid" in triggers4, "❌ UUID no agregado"
    assert "timestamp" in triggers4, "❌ Timestamp no agregado"

    # Validar formato YYYYMMDD
    pattern_compact = r'^\d{8}$'
    assert re.match(pattern_compact, triggers4["timestamp"]), f"❌ Formato compacto incorrecto: {triggers4['timestamp']}"
    print(f"✓ Timestamp compacto válido: {triggers4['timestamp']}")

    print("\n✅ Todas las validaciones pasaron correctamente")

if __name__ == "__main__":
    test_timestamped_factory()
