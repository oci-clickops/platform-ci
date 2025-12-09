#!/usr/bin/env python3
"""
Setup de Terraform backend - genera providers.tf
Uso: python3 terraform_setup.py <cloud> <workspace-path>
"""

import os
import sys


def check_environment_variables():
    """Verificar variables de entorno necesarias"""
    required = ["BUCKET_NAME", "STATE_KEY", "STATE_NAMESPACE", "DETECTED_REGION"]
    
    for var_name in required:
        if not os.environ.get(var_name):
            print(f"❌ Error: Variable {var_name} no está configurada")
            return False
    
    return True


def get_oci_template():
    """Template de configuración OCI"""
    return """provider "oci" {
  auth                = "InstancePrincipal"
  region              = var.region
  ignore_defined_tags = ["Oracle-Tags.CreatedBy", "Oracle-Tags.CreatedOn"]
}

provider "oci" {
  auth                = "InstancePrincipal"
  alias               = "home"
  region              = var.region
  ignore_defined_tags = ["Oracle-Tags.CreatedBy", "Oracle-Tags.CreatedOn"]
}

provider "oci" {
  auth                = "InstancePrincipal"
  alias               = "secondary_region"
  region              = var.region
  ignore_defined_tags = ["Oracle-Tags.CreatedBy", "Oracle-Tags.CreatedOn"]
}

terraform {
  required_version = ">= 1.12.0"
  required_providers {
    oci = {
      source                = "oracle/oci"
      configuration_aliases = [oci.home]
    }
  }
  backend "oci" {
    bucket    = "__BUCKET__"
    key       = "__KEY__"
    namespace = "__NAMESPACE__"
    auth      = "InstancePrincipal"
    region    = "__REGION__"
  }
}
"""


def get_azure_template():
    """Template de configuración Azure"""
    return """provider "azurerm" {
  features {}
}

terraform {
  required_version = ">= 1.12.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
  backend "oci" {
    bucket    = "__BUCKET__"
    key       = "__KEY__"
    namespace = "__NAMESPACE__"
    auth      = "InstancePrincipal"
    region    = "__REGION__"
  }
}
"""


def replace_placeholders(text):
    """Reemplazar placeholders en texto"""
    text = text.replace("__BUCKET__", os.environ.get("BUCKET_NAME", ""))
    text = text.replace("__KEY__", os.environ.get("STATE_KEY", ""))
    text = text.replace("__NAMESPACE__", os.environ.get("STATE_NAMESPACE", ""))
    text = text.replace("__REGION__", os.environ.get("DETECTED_REGION", ""))
    return text


def main():
    """Main - setup backend"""
    # Step 1: Verificar argumentos
    if len(sys.argv) != 3:
        print("❌ Error: Argumentos incorrectos")
        print("Uso: terraform_setup.py <cloud> <workspace-path>")
        print("Ejemplo: terraform_setup.py oci /workspace")
        sys.exit(1)
    
    cloud = sys.argv[1]
    workspace_path = sys.argv[2]
    
    # Step 2: Verificar environment
    if not check_environment_variables():
        sys.exit(1)
    
    # Step 3: Elegir template
    if cloud == "oci":
        print("Generando configuración OCI...")
        config_text = get_oci_template()
    elif cloud == "azure":
        print("Generando configuración Azure...")
        config_text = get_azure_template()
    else:
        print(f"❌ Error: Cloud '{cloud}' no soportado")
        print("Clouds válidos: oci, azure")
        sys.exit(1)
    
    # Step 4: Reemplazar placeholders
    config_text = replace_placeholders(config_text)
    
    # Step 5: Escribir providers.tf
    orch_folder = os.path.join(workspace_path, "ORCH")
    providers_file = os.path.join(orch_folder, "providers.tf")
    
    if not os.path.exists(orch_folder):
        print(f"❌ Error: Carpeta ORCH no existe: {orch_folder}")
        sys.exit(1)
    
    with open(providers_file, 'w') as f:
        f.write(config_text)
    
    # Step 6: Formatear con terraform
    original_dir = os.getcwd()
    os.chdir(orch_folder)
    os.system("terraform fmt providers.tf")
    os.chdir(original_dir)
    
    # Step 7: Mostrar resumen
    print("")
    print("="*50)
    print("✅ Setup de Terraform completo")
    print("="*50)
    print(f"   Backend: OCI")
    print(f"   Bucket: {os.environ.get('BUCKET_NAME')}")
    print(f"   Key: {os.environ.get('STATE_KEY')}")
    print(f"   Región: {os.environ.get('DETECTED_REGION')}")
    print("="*50)


if __name__ == "__main__":
    main()
