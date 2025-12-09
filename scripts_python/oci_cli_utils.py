#!/usr/bin/env python3
"""
OCI CLI utility functions - Simple wrappers for OCI CLI commands
No Python SDK required, just calls oci CLI
"""

import subprocess
import json
import os
import tempfile


def run_oci_command(command):
    """
    Ejecutar comando OCI CLI
    
    Args:
        command: lista de argumentos ['oci', 'os', 'object', 'get', ...]
    
    Returns:
        (success, output) - tuple con bool y string
    """
    # Step 1: Ejecutar comando
    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )
    
    # Step 2: Verificar resultado
    if result.returncode == 0:
        return True, result.stdout
    else:
        return False, result.stderr


def download_from_bucket(namespace, bucket, object_name):
    """
    Descargar objeto de OCI Object Storage usando CLI
    
    Args:
        namespace: OCI namespace
        bucket: nombre del bucket
        object_name: ruta del objeto
    
    Returns:
        string con contenido o None si no existe
    """
    # Step 1: Crear archivo temporal
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp:
        tmp_path = tmp.name
    
    # Step 2: Descargar con OCI CLI
    command = [
        'oci', 'os', 'object', 'get',
        '--namespace', namespace,
        '--bucket-name', bucket,
        '--name', object_name,
        '--file', tmp_path
    ]
    
    success, output = run_oci_command(command)
    
    # Step 3: Leer contenido si tuvo éxito
    if success:
        with open(tmp_path, 'r') as f:
            content = f.read()
        os.remove(tmp_path)
        return content
    else:
        # Verificar si es 404 (not found)
        if 'NotAuthorizedOrNotFound' in output or '404' in output:
            print(f"Note: Object not found: {object_name}")
        else:
            print(f"Error downloading: {output}")
        
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return None


def upload_to_bucket(namespace, bucket, object_name, content):
    """
    Subir contenido a OCI Object Storage usando CLI
    
    Args:
        namespace: OCI namespace
        bucket: nombre del bucket
        object_name: ruta del objeto
        content: string con contenido a subir
    
    Returns:
        True si tuvo éxito, False si falló
    """
    # Step 1: Escribir a archivo temporal
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    # Step 2: Subir con OCI CLI
    command = [
        'oci', 'os', 'object', 'put',
        '--namespace', namespace,
        '--bucket-name', bucket,
        '--name', object_name,
        '--file', tmp_path,
        '--force'
    ]
    
    success, output = run_oci_command(command)
    
    # Step 3: Limpiar archivo temporal
    os.remove(tmp_path)
    
    if success:
        print(f"Uploaded: {object_name}")
        return True
    else:
        print(f"Error uploading: {output}")
        return False


def update_instance_tags(instance_id, new_tags):
    """
    Actualizar tags de una instancia de Compute
    
    Args:
        instance_id: OCID de la instancia
        new_tags: dict con tags a agregar/actualizar
    
    Returns:
        True si tuvo éxito, False si falló
    """
    # Step 1: Obtener tags actuales
    command_get = [
        'oci', 'compute', 'instance', 'get',
        '--instance-id', instance_id,
        '--query', 'data."freeform-tags"'
    ]
    
    success, output = run_oci_command(command_get)
    
    if not success:
        print(f"Error getting current tags: {output}")
        return False
    
    # Step 2: Parsear tags actuales
    try:
        current_tags = json.loads(output)
    except:
        current_tags = {}
    
    # Step 3: Merge tags
    updated_tags = {**current_tags, **new_tags}
    
    # Step 4: Actualizar instancia
    command_update = [
        'oci', 'compute', 'instance', 'update',
        '--instance-id', instance_id,
        '--freeform-tags', json.dumps(updated_tags),
        '--force'
    ]
    
    success, output = run_oci_command(command_update)
    
    if success:
        print(f"Updated tags for instance {instance_id}")
        return True
    else:
        print(f"Error updating tags: {output}")
        return False


def update_adb_tags(adb_id, new_tags):
    """
    Actualizar tags de Autonomous Database
    
    Args:
        adb_id: OCID de la ADB
        new_tags: dict con tags a agregar/actualizar
    
    Returns:
        True si tuvo éxito, False si falló
    """
    # Step 1: Obtener tags actuales
    command_get = [
        'oci', 'db', 'autonomous-database', 'get',
        '--autonomous-database-id', adb_id,
        '--query', 'data."freeform-tags"'
    ]
    
    success, output = run_oci_command(command_get)
    
    if not success:
        print(f"Error getting current ADB tags: {output}")
        return False
    
    # Step 2: Parsear tags actuales
    try:
        current_tags = json.loads(output)
    except:
        current_tags = {}
    
    # Step 3: Merge tags
    updated_tags = {**current_tags, **new_tags}
    
    # Step 4: Actualizar ADB
    command_update = [
        'oci', 'db', 'autonomous-database', 'update',
        '--autonomous-database-id', adb_id,
        '--freeform-tags', json.dumps(updated_tags),
        '--force'
    ]
    
    success, output = run_oci_command(command_update)
    
    if success:
        print(f"Updated tags for ADB {adb_id}")
        return True
    else:
        print(f"Error updating ADB tags: {output}")
        return False
