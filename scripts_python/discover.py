#!/usr/bin/env python3
"""
Discovery de configuración - terraform o ansible
Uso:
    python3 discover.py terraform <cloud> <bucket>
    python3 discover.py ansible <cloud> <operation-file> <bucket>
"""

import os
import sys
import glob
from common import write_github_env, print_error, print_success
from discovery_functions import (
    discover_terraform_backend,
    write_terraform_outputs,
    discover_ansible_operation,
    write_ansible_outputs
)


def find_region_folder(cloud):
    """
    Encontrar la primera carpeta bajo el cloud
    Ejemplo: oci/eu-frankfurt-1 → retorna "oci/eu-frankfurt-1"
    """
    # Buscar carpetas bajo cloud
    pattern = os.path.join(cloud, "*")
    folders = glob.glob(pattern)
    
    # Filtrar solo directorios
    folders = [f for f in folders if os.path.isdir(f)]
    
    # Retornar el primero
    if folders:
        return folders[0]
    else:
        return None


def terraform_command(args):
    """Discovery para Terraform"""
    # Step 1: Parsear argumentos
    if len(args) != 3:
        print_error("Argumentos incorrectos para 'terraform'")
        print("Uso: discover.py terraform <cloud> <bucket>")
        sys.exit(1)
    
    cloud = args[1]
    bucket = args[2]
    
    # Step 2: Buscar carpeta de región
    config_path = find_region_folder(cloud)
    
    if not config_path:
        print_error(f"No se encontró carpeta de región en {cloud}/")
        print(f"Estructura esperada: {cloud}/region-name/")
        sys.exit(1)
    
    # Step 3: Ejecutar discovery
    results = discover_terraform_backend(bucket, config_path)
    
    # Step 4: Escribir outputs
    write_terraform_outputs(results)
    
    # Step 5: Escribir env vars adicionales
    write_github_env("CONFIG_SUBPATH", results['config_subpath'])
    write_github_env("BUCKET_NAME", bucket)
    write_github_env("STATE_KEY", results['state_key'])
    
    # Step 6: Mostrar resumen
    print_success("Backend config listo:")
    print(f"   Path: {results['config_subpath']}")
    print(f"   Bucket: {bucket}")
    print(f"   Región: {results['region']}")
    print(f"   State: {results['state_key']}")


def ansible_command(args):
    """Discovery para Ansible"""
    # Step 1: Parsear argumentos
    if len(args) != 4:
        print_error("Argumentos incorrectos para 'ansible'")
        print("Uso: discover.py ansible <cloud> <operation-file> <bucket>")
        sys.exit(1)
    
    cloud = args[1]
    operation_file = args[2]
    bucket = args[3]
    
    print(f"Descubriendo operación Ansible...")
    print(f"   Cloud: {cloud}")
    print(f"   Archivo: {operation_file}")
    
    # Step 2: Ejecutar discovery
    results = discover_ansible_operation(cloud, bucket, operation_file)
    
    # Step 3: Escribir outputs (incluye env vars)
    write_ansible_outputs(results)
    
    # Step 4: Mostrar resumen
    from discovery_functions import extract_region
    region = extract_region(results['config_subpath'])
    
    print_success("Discovery completo:")
    print(f"   Tipo: {results['operation_type']}")
    print(f"   Path: {results['config_subpath']}")
    print(f"   Región: {region}")
    print(f"   Targets: {results['target_count']}")
    print(f"   State: {results['state_key']}")


def main():
    """Main - router para subcomandos"""
    # Step 1: Verificar argumentos
    if len(sys.argv) < 2:
        print_error("Falta subcomando")
        print("")
        print("Uso:")
        print("  discover.py terraform <cloud> <bucket>")
        print("  discover.py ansible <cloud> <operation-file> <bucket>")
        print("")
        print("Ejemplos:")
        print("  discover.py terraform oci clickops-common-bucket")
        print("  discover.py ansible oci oci/region/ansible/op.json clickops-common-bucket")
        sys.exit(1)
    
    # Step 2: Ejecutar subcomando
    subcommand = sys.argv[1]
    
    if subcommand == 'terraform':
        terraform_command(sys.argv[1:])
    elif subcommand == 'ansible':
        ansible_command(sys.argv[1:])
    else:
        print_error(f"Subcomando desconocido: {subcommand}")
        print("Subcomandos válidos: terraform, ansible")
        sys.exit(1)


if __name__ == "__main__":
    main()
