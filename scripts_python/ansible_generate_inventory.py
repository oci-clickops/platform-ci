#!/usr/bin/env python3
"""
Generate dynamic Ansible inventory from Terraform state
Only for ADB resources (VM operations removed from MVP scope)
"""

import os
import sys
import json
from common import load_json, save_json, print_error, print_success
from config import get_inventory_path, get_terraform_state_key
from oci_cli_utils import download_from_bucket


def download_terraform_state(namespace, bucket, config_path):
    """Download terraform.tfstate from OCI bucket"""
    # Build state key
    state_key = get_terraform_state_key(bucket, config_path)

    print(f"Loading Terraform state from OCI Object Storage...")
    print(f"   Namespace: {namespace}")
    print(f"   Bucket: {bucket}")
    print(f"   Key: {state_key}")

    # Download using CLI
    content = download_from_bucket(namespace, bucket, state_key)

    if content:
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print_error(f"Invalid JSON in Terraform state: {e}")
            return None
    else:
        return None


def parse_adb_resources(state_data):
    """
    Parse Terraform state to extract ADB information
    
    Returns dict of display_name → adb_info
    """
    adb_map = {}

    if not state_data:
        return adb_map

    # Parse resources section
    resources = state_data.get('resources', [])

    for resource in resources:
        resource_type = resource.get('type')
        resource_name = resource.get('name')
        
        # Only process ADB resources
        if resource_type == 'oci_database_autonomous_database':
            instances = resource.get('instances', [])
            
            for instance in instances:
                attrs = instance.get('attributes', {})
                display_name = attrs.get('display_name', resource_name)
                
                adb_map[display_name] = {
                    'ocid': attrs.get('id'),
                    'db_name': attrs.get('db_name'),
                    'state': attrs.get('lifecycle_state'),
                    'freeform_tags': attrs.get('freeform_tags', {})
                }

    return adb_map


def build_ansible_inventory(manifest, adb_map):
    """
    Build Ansible inventory for ADB resources only
    
    Returns inventory in JSON format
    """
    inventory = {
        '_meta': {
            'hostvars': {}
        },
        'all': {
            'children': ['adb_instances']
        },
        'adb_instances': {
            'hosts': []
        }
    }

    targets = manifest.get('targets', {})
    adb_resources = targets.get('adb_resources', [])
    
    for adb_target in adb_resources:
        # Use display_name as key (matching Terraform)
        logical_key = adb_target.get('display_name')

        if logical_key in adb_map:
            adb_info = adb_map[logical_key]

            # Add to inventory
            inventory['adb_instances']['hosts'].append(logical_key)

            # Set host vars (runs locally via OCI CLI)
            inventory['_meta']['hostvars'][logical_key] = {
                'ansible_connection': 'local',
                'oci_ocid': adb_info.get('ocid'),
                'oci_state': adb_info.get('state'),
                'db_name': adb_info.get('db_name'),
                'action': adb_target.get('action'),
                'wait_for_state': adb_target.get('wait_for_state', True),
                'timeout_minutes': adb_target.get('timeout_minutes', 30),
                'resource_tags': adb_info.get('freeform_tags', {})
            }
        else:
            # Resource not found - critical error
            print("")
            print("="*60)
            print(f"❌ ERROR: No se encontró la base de datos '{logical_key}'")
            print("="*60)
            print(f"📋 Recursos ADB disponibles en Terraform state:")
            if adb_map:
                for name in adb_map.keys():
                    print(f"   - {name}")
            else:
                print("   (ninguno - ejecuta terraform apply primero)")
            print("")
            print("💡 Soluciones:")
            print("   1. Verifica que 'display_name' en el manifest coincida exactamente")
            print("   2. O ejecuta 'terraform apply' primero si la DB es nueva")
            print("")
            sys.exit(1)

    return inventory


def main():
    """Main function - generate dynamic Ansible inventory"""

    # Step 1: Get arguments
    if len(sys.argv) != 5:
        print_error("Missing required arguments")
        print("Usage: ansible_generate_inventory.py <cloud> <bucket> <config-path> <operation-file>")
        sys.exit(1)

    cloud = sys.argv[1]
    bucket = sys.argv[2]
    config_path = sys.argv[3]
    operation_file = sys.argv[4]

    # Step 2: Get namespace
    namespace = os.environ.get('STATE_NAMESPACE')
    if not namespace:
        print_error("STATE_NAMESPACE environment variable not set")
        sys.exit(1)

    # Step 3: Only OCI supported
    if cloud != 'oci':
        print_error(f"{cloud} not yet implemented")
        sys.exit(1)

    print("Generating dynamic inventory...")

    # Step 4: Download and parse Terraform state
    state_data = download_terraform_state(namespace, bucket, config_path)
    adb_map = parse_adb_resources(state_data)

    print_success(f"Found {len(adb_map)} ADB resources in Terraform state")

    # Step 5: Load operation manifest
    manifest = load_json(operation_file)

    # Step 6: Build inventory
    inventory = build_ansible_inventory(manifest, adb_map)

    # Step 7: Save to file
    inventory_path = get_inventory_path()
    save_json(inventory_path, inventory)

    adb_count = len(inventory['adb_instances']['hosts'])
    print_success(f"Generated inventory: {adb_count} ADB hosts")
    print(f"   Saved to: {inventory_path}")


if __name__ == "__main__":
    main()
