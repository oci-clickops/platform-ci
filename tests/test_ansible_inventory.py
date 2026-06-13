import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts_python"
sys.path.insert(0, str(SCRIPTS_DIR))

from ansible_inventory import build_compute_inventory  # noqa: E402


class AnsibleInventoryTests(unittest.TestCase):
    def test_compute_inventory_sets_ssh_user_and_private_key_defaults(self):
        manifest = {
            "operation_type": "deploy-agent",
            "agent_type": "demo-agent",
            "agent_version": "1.0.0",
            "targets": [{"display_name": "vm-gitops-demo3-web-01"}],
        }
        compute_map = {
            "vm-gitops-demo3-web-01": {
                "ocid": "ocid1.instance.oc1.eu-frankfurt-1.example",
                "private_ip": "10.0.65.10",
                "state": "RUNNING",
                "shape": "VM.Standard.A1.Flex",
                "freeform_tags": {},
            }
        }

        with patch.dict(os.environ, {}, clear=True):
            inventory = build_compute_inventory(manifest, compute_map)

        host = inventory["compute_instances"]["hosts"]["vm-gitops-demo3-web-01"]
        self.assertEqual(host["ansible_connection"], "ssh")
        self.assertEqual(host["ansible_user"], "opc")
        self.assertEqual(host["ansible_ssh_private_key_file"], "/home/opc/.ssh/oci_vm_key")

    def test_compute_inventory_allows_ssh_overrides_from_environment(self):
        manifest = {
            "operation_type": "deploy-agent",
            "targets": [{"display_name": "vm-gitops-demo3-web-01"}],
        }
        compute_map = {
            "vm-gitops-demo3-web-01": {
                "ocid": "ocid1.instance.oc1.eu-frankfurt-1.example",
                "private_ip": "10.0.65.10",
                "state": "RUNNING",
                "shape": "VM.Standard.A1.Flex",
                "freeform_tags": {},
            }
        }

        with patch.dict(
            os.environ,
            {
                "COMPUTE_ANSIBLE_USER": "oracle",
                "COMPUTE_SSH_PRIVATE_KEY_FILE": "/opt/keys/project1",
            },
            clear=True,
        ):
            inventory = build_compute_inventory(manifest, compute_map)

        host = inventory["compute_instances"]["hosts"]["vm-gitops-demo3-web-01"]
        self.assertEqual(host["ansible_user"], "oracle")
        self.assertEqual(host["ansible_ssh_private_key_file"], "/opt/keys/project1")


if __name__ == "__main__":
    unittest.main()
