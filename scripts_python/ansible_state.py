#!/usr/bin/env python3
"""
Gestión de estado de Ansible - load o update
Uso:
    python3 ansible_state.py load <cloud> <bucket> <state-key>
    python3 ansible_state.py update <cloud> <bucket> <state-key> <state-file> <operation-file>
"""

import os
import sys
from common import load_json, save_json, print_error, print_success
from config import get_ansible_state_path
from state_functions import load_state_from_bucket, update_state_with_manifest, save_state_to_bucket, save_state_to_file


def load_command(args):
    """Cargar estado desde bucket"""
    # Step 1: Parsear argumentos
    if len(args) != 4:
        print_error("Argumentos incorrectos para 'load'")
        print("Uso: ansible_state.py load <cloud> <bucket> <state-key>")
        sys.exit(1)
    
    cloud = args[1]
    bucket = args[2]
    state_key = args[3]
    
    # Step 2: Obtener namespace
    namespace = os.environ.get('STATE_NAMESPACE')
    if not namespace:
        print_error("STATE_NAMESPACE no está configurado")
        sys.exit(1)
    
    print("Cargando estado de Ansible...")
    
    # Step 3: Cargar desde bucket
    state = load_state_from_bucket(cloud, bucket, namespace, state_key)
    
    # Step 4: Guardar localmente
    state_path = get_ansible_state_path()
    save_json(state_path, state)
    
    resource_count = len(state.get('resources', {}))
    print_success(f"Estado cargado: {resource_count} recursos")
    print(f"   Guardado en: {state_path}")


def update_command(args):
    """Actualizar estado en bucket"""
    # Step 1: Parsear argumentos
    if len(args) != 6:
        print_error("Argumentos incorrectos para 'update'")
        print("Uso: ansible_state.py update <cloud> <bucket> <state-key> <state-file> <operation-file>")
        sys.exit(1)
    
    cloud = args[1]
    bucket = args[2]
    state_key = args[3]
    state_file = args[4]
    operation_file = args[5]
    
    # Step 2: Obtener namespace
    namespace = os.environ.get('STATE_NAMESPACE')
    if not namespace:
        print_error("STATE_NAMESPACE no está configurado")
        sys.exit(1)
    
    # Step 3: Cargar archivos locales
    current_state = load_json(state_file)
    manifest = load_json(operation_file)
    
    print("Actualizando estado de Ansible...")
    
    # Step 4: Actualizar estado con manifest
    updated_state = update_state_with_manifest(current_state, manifest)
    
    # Step 5: Guardar en bucket
    success = save_state_to_bucket(cloud, bucket, namespace, state_key, updated_state)
    
    if not success:
        print_error("Error guardando estado")
        sys.exit(1)
    
    # Step 6: Guardar copia debug
    debug_path = save_state_to_file(updated_state, 'ansible-state-updated.json')
    print(f"   Copia debug: {debug_path}")


def main():
    """Main - router para subcomandos"""
    # Step 1: Verificar que hay argumentos
    if len(sys.argv) < 2:
        print_error("Falta subcomando")
        print("")
        print("Uso:")
        print("  ansible_state.py load <cloud> <bucket> <state-key>")
        print("  ansible_state.py update <cloud> <bucket> <state-key> <state-file> <operation-file>")
        print("")
        print("Ejemplos:")
        print("  ansible_state.py load oci clickops-common-bucket bucket/ansible/oci/region/state.json")
        print("  ansible_state.py update oci clickops-common-bucket key /tmp/state.json operation.json")
        sys.exit(1)
    
    # Step 2: Ejecutar subcomando
    subcommand = sys.argv[1]
    
    if subcommand == 'load':
        load_command(sys.argv[1:])
    elif subcommand == 'update':
        update_command(sys.argv[1:])
    else:
        print_error(f"Subcomando desconocido: {subcommand}")
        print("Subcomandos válidos: load, update")
        sys.exit(1)


if __name__ == "__main__":
    main()
