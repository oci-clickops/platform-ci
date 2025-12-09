#!/usr/bin/env python3
"""
Funciones para descubrir configuración de backend (sin clases)
Cada función hace UNA cosa y es fácil de entender
"""

import os
from common import load_json, write_github_output, write_github_env, print_error, print_success, print_info


def extract_config_path(file_path):
    """
    Extraer path de configuración desde una ruta de archivo
    
    Ejemplo:
        oci/eu-frankfurt-1/compute.json → oci/eu-frankfurt-1
        azure/westeurope/network.json → azure/westeurope
    
    Args:
        file_path: ruta completa o relativa
    
    Returns:
        config path (cloud/region)
    """
    # Step 1: Normalizar path
    normalized = os.path.normpath(file_path)
    
    # Step 2: Separar en partes
    parts = normalized.split(os.sep)
    
    # Step 3: Buscar cloud provider (oci o azure)
    cloud_index = -1
    for i, part in enumerate(parts):
        if part in ['oci', 'azure']:
            cloud_index = i
            break
    
    if cloud_index == -1:
        raise ValueError(f"No se encontró cloud provider (oci/azure) en: {file_path}")
    
    # Step 4: Verificar que hay región
    if cloud_index + 1 >= len(parts):
        raise ValueError(f"No se encontró región después del cloud en: {file_path}")
    
    cloud = parts[cloud_index]
    region = parts[cloud_index + 1]
    
    # Step 5: Retornar config path
    return f"{cloud}/{region}"


def extract_region(config_path):
    """
    Extraer región desde config path
    
    Ejemplo:
        oci/eu-frankfurt-1 → eu-frankfurt-1
        azure/westeurope → westeurope
    
    Args:
        config_path: config path (cloud/region)
    
    Returns:
        región
    """
    parts = config_path.split('/')
    if len(parts) < 2:
        raise ValueError(f"Config path inválido: {config_path}")
    
    return parts[1]


def discover_terraform_backend(bucket, config_path):
    """
    Descubrir configuración de backend para Terraform
    
    Args:
        bucket: nombre del bucket
        config_path: path de configuración (ej: oci/eu-frankfurt-1)
    
    Returns:
        dict con region, config_subpath, state_key
    """
    # Step 1: Extraer región
    region = extract_region(config_path)
    print_success(f"Región detectada: {region}")
    
    # Step 2: Config subpath es igual al config_path
    config_subpath = config_path
    print_info(f"Config path: {config_subpath}")
    
    # Step 3: Construir state key para Terraform
    state_key = f"{bucket}/{config_path}/terraform.tfstate"
    print_info(f"State key: {state_key}")
    
    # Step 4: Retornar resultados
    return {
        'region': region,
        'config_subpath': config_subpath,
        'state_key': state_key
    }


def write_terraform_outputs(results):
    """
    Escribir resultados de discovery a GitHub Actions
    
    Args:
        results: dict con region, config_subpath, state_key
    """
    write_github_output('region', results['region'])
    write_github_output('config_subpath', results['config_subpath'])
    write_github_output('state_key', results['state_key'])
    write_github_env('DETECTED_REGION', results['region'])
    
    print_success("Discovery outputs escritos")


def discover_ansible_operation(cloud, bucket, operation_file):
    """
    Descubrir configuración de operación Ansible
    
    Args:
        cloud: oci o azure
        bucket: nombre del bucket
        operation_file: ruta al archivo JSON de operación
    
    Returns:
        dict con operation_type, config_subpath, state_key, target_count
    """
    # Step 1: Cargar manifest
    manifest = load_json(operation_file)
    
    # Step 2: Extraer operation type
    operation_type = manifest.get('operation_type')
    if not operation_type:
        raise ValueError("Falta 'operation_type' en el manifest")
    
    print_success(f"Operation type: {operation_type}")
    
    # Step 3: Extraer config path del archivo
    config_path = extract_config_path(operation_file)
    config_subpath = config_path
    print_info(f"Config path: {config_subpath}")
    
    # Step 4: Construir state key para Ansible
    state_key = f"{bucket}/ansible/{config_path}/ansible-state-{operation_type}.json"
    print_info(f"State key: {state_key}")
    
    # Step 5: Contar targets
    targets = manifest.get('targets', {})
    vm_count = len(targets.get('vm_resources', []))
    adb_count = len(targets.get('adb_resources', []))
    target_count = vm_count + adb_count
    
    print_info(f"Targets: {vm_count} VMs + {adb_count} ADBs = {target_count} total")
    
    # Step 6: Retornar resultados
    return {
        'operation_type': operation_type,
        'config_subpath': config_subpath,
        'state_key': state_key,
        'target_count': target_count
    }


def write_ansible_outputs(results):
    """
    Escribir resultados de discovery Ansible a GitHub Actions
    
    Args:
        results: dict con operation_type, config_subpath, state_key, target_count
    """
    write_github_output('operation_type', results['operation_type'])
    write_github_output('config_subpath', results['config_subpath'])
    write_github_output('state_key', results['state_key'])
    write_github_output('target_count', str(results['target_count']))
    
    # También escribir algunas env vars útiles
    region = extract_region(results['config_subpath'])
    write_github_env('DETECTED_REGION', region)
    write_github_env('CONFIG_SUBPATH', results['config_subpath'])
    write_github_env('OPERATION_TYPE', results['operation_type'])
    write_github_env('STATE_KEY', results['state_key'])
    
    print_success("Discovery outputs escritos")
