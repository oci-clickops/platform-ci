#!/usr/bin/env python3
"""
Funciones para manejar el estado de Ansible (sin clases)
Cada función hace UNA cosa y es fácil de entender
"""

import json
import os
from datetime import datetime
from common import print_error, print_success, print_info, save_json
from config import get_work_temp
from oci_cli_utils import download_from_bucket, upload_to_bucket


def load_state_from_bucket(cloud, bucket, namespace, state_key):
    """
    Cargar estado desde el bucket de OCI
    
    Args:
        cloud: oci o azure
        bucket: nombre del bucket
        namespace: namespace de OCI
        state_key: ruta del archivo en el bucket
    
    Returns:
        dict con el estado (existente o nuevo vacío)
    """
    
    # Step 1: Verificar que sea OCI (Azure no implementado)
    if cloud != 'oci':
        print_info(f"{cloud} no implementado, creando estado vacío")
        return {
            "version": "1.0.0",
            "last_updated": None,
            "resources": {}
        }
    
    # Step 2: Descargar archivo del bucket usando CLI
    content = download_from_bucket(namespace, bucket, state_key)
    
    # Step 3: Si existe, parsearlo; si no, crear nuevo
    if content:
        try:
            state = json.loads(content)
            print_success(f"Estado cargado desde {state_key}")
            return state
        except json.JSONDecodeError as e:
            print_error(f"JSON inválido en el estado: {e}")
            raise
    else:
        print_info(f"No existe estado en {state_key}, creando nuevo")
        return {
            "version": "1.0.0",
            "last_updated": None,
            "resources": {}
        }


def update_state_with_manifest(state, manifest):
    """
    Actualizar estado con los resultados de una operación
    
    Args:
        state: estado actual (dict)
        manifest: manifest de la operación (dict)
    
    Returns:
        estado actualizado (dict)
    """
    
    # Step 1: Obtener timestamp actual
    current_time = datetime.utcnow().isoformat() + 'Z'
    state['last_updated'] = current_time
    
    # Step 2: Obtener datos del manifest
    operation_type = manifest.get('operation_type')
    operation_version = manifest.get('operation_version', '1.0.0')
    targets = manifest.get('targets', {})
    
    # Step 3: Procesar recursos de VM (si hay)
    vm_resources = targets.get('vm_resources', [])
    for vm_target in vm_resources:
        logical_key = vm_target.get('logical_key')
        
        # Crear entrada si no existe
        if logical_key not in state['resources']:
            state['resources'][logical_key] = {'operations': {}}
        
        # Construir info de agentes
        agents_info = {}
        for agent in vm_target.get('agents', []):
            agent_type = agent.get('type')
            agents_info[agent_type] = {
                'version': agent.get('version'),
                'installed_at': current_time
            }
        
        # Actualizar operación
        state['resources'][logical_key]['operations'][operation_type] = {
            'completed': current_time,
            'status': 'success',
            'version': operation_version,
            'agents': agents_info
        }
    
    # Step 4: Procesar recursos de ADB (si hay)
    adb_resources = targets.get('adb_resources', [])
    for adb_target in adb_resources:
        # Usar display_name como clave
        logical_key = adb_target.get('display_name')
        action = adb_target.get('action')
        
        # Crear entrada si no existe
        if logical_key not in state['resources']:
            state['resources'][logical_key] = {'operations': {}}
        
        # Actualizar operación
        state['resources'][logical_key]['operations'][operation_type] = {
            'completed': current_time,
            'status': 'success',
            'action': action,
            'version': operation_version
        }
    
    return state


def save_state_to_bucket(cloud, bucket, namespace, state_key, state):
    """
    Guardar estado en el bucket de OCI
    
    Args:
        cloud: oci o azure
        bucket: nombre del bucket
        namespace: namespace de OCI
        state_key: ruta del archivo en el bucket
        state: estado a guardar (dict)
    
    Returns:
        True si tuvo éxito, False si falló
    """
    
    # Step 1: Verificar que sea OCI
    if cloud != 'oci':
        print_error(f"{cloud} no implementado")
        return False
    
    # Step 2: Convertir estado a JSON
    state_json = json.dumps(state, indent=2)
    
    # Step 3: Subir al bucket usando CLI
    success = upload_to_bucket(namespace, bucket, state_key, state_json)
    
    if success:
        print_success(f"Estado guardado en {state_key}")
    else:
        print_error("Error guardando estado")
    
    return success


def save_state_to_file(state, filename='ansible-state.json'):
    """
    Guardar estado en archivo local (para debugging)
    
    Args:
        state: estado a guardar (dict)
        filename: nombre del archivo (default: ansible-state.json)
    
    Returns:
        ruta donde se guardó
    """
    # Step 1: Construir path completo
    temp_path = os.path.join(get_work_temp(), filename)
    
    # Step 2: Guardar usando función compartida
    save_json(temp_path, state)
    
    return temp_path
