#!/usr/bin/env python3
"""
Utilidades para ansible_inventory.py
"""

import os
import sys
import json
import subprocess
import tempfile


def load_json(file_path):
    """Cargar archivo JSON."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Archivo no encontrado: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: JSON inválido en {file_path}: {e}")
        sys.exit(1)


def save_json(file_path, data):
    """Guardar datos en archivo JSON."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)


def get_inventory_path():
    """Obtener path del archivo de inventario."""
    work_temp = os.environ.get('WORK_TEMP', '/tmp')
    return os.path.join(work_temp, "inventory.json")


def get_terraform_state_key(bucket, config_path):
    """Construir key del state de Terraform."""
    return f"{bucket}/{config_path}/terraform.tfstate"


def download_from_bucket(namespace, bucket, object_name):
    """
    Descargar objeto de OCI Object Storage.
    Retorna: contenido string o None si no existe.
    """
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp:
        tmp_path = tmp.name

    command = [
        'oci', 'os', 'object', 'get',
        '--namespace', namespace,
        '--bucket-name', bucket,
        '--name', object_name,
        '--file', tmp_path
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode == 0:
        with open(tmp_path, 'r') as f:
            content = f.read()
        os.remove(tmp_path)
        return content
    else:
        if 'NotAuthorizedOrNotFound' in result.stderr or '404' in result.stderr:
            print(f"ℹ️  Objeto no encontrado: {object_name}")
        else:
            print(f"❌ Error descargando: {result.stderr}")

        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return None
