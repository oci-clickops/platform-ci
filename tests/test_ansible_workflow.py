import unittest
from pathlib import Path


WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ansible-shared.yaml"


class AnsibleWorkflowTests(unittest.TestCase):
    def test_ansible_playbook_failures_are_not_swallowed(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertNotIn("|| true", workflow)
        self.assertGreaterEqual(workflow.count("ANSIBLE_STATUS=${PIPESTATUS[0]}"), 2)
        self.assertGreaterEqual(workflow.count('exit "$ANSIBLE_STATUS"'), 2)

    def test_detects_lifecycle_operations_manifests(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("lifecycle_operations", workflow)
        self.assertNotIn("grep 'ansible'", workflow)


if __name__ == "__main__":
    unittest.main()
