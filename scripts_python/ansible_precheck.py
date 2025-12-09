#!/usr/bin/env python3
"""
Pre-checks antes de ejecutar operaciones Ansible
Solo ADB: verifica que targets existen en inventory
"""

import sys
from common import load_json, print_error, print_success


def main():
    """Main - verificar pre-condiciones"""

    # Step 1: Get argumentos
    if len(sys.argv) != 4:
        print_error("Missing required arguments")
        print("Usage: ansible_precheck.py <cloud> <operation-file> <inventory-file>")
        sys.exit(1)

    cloud = sys.argv[1]
    operation_file = sys.argv[2]
    inventory_file = sys.argv[3]

    # Step 2: Solo OCI soportado
    if cloud != 'oci':
        print_success(f"{cloud} pre-checks skipped (not implemented)")
        return

    print("Running pre-checks...")

    # Step 3: Cargar archivos
    manifest = load_json(operation_file)
    inventory = load_json(inventory_file)

    # Step 4: Verificar que todos los targets ADB existen en inventory
    targets = manifest.get('targets', {})
    adb_resources = targets.get('adb_resources', [])
    hostvars = inventory.get('_meta', {}).get('hostvars', {})

    missing = []
    for adb_target in adb_resources:
        logical_key = adb_target.get('display_name')
        if logical_key not in hostvars:
            missing.append(logical_key)

    # Step 5: Si faltan targets, error
    if missing:
        print("")
        print_error(f"Targets not found in inventory:")
        for name in missing:
            print(f"   - {name}")
        print("")
        print("💡 Solución: Ejecuta 'terraform apply' primero")
        sys.exit(1)

    # Step 6: Todo OK
    target_count = len(adb_resources)
    print_success(f"Pre-checks passed: {target_count} ADB targets found")


if __name__ == "__main__":
    main()
