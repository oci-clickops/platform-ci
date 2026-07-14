import re
import unittest
from pathlib import Path


WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "terraform-shared.yaml"
)


class TerraformWorkflowTests(unittest.TestCase):
    def test_apply_uses_the_saved_binary_plan(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        apply_step = re.search(
            r"      - name: Terraform apply\n(?P<body>.*?)(?=\n      #|\Z)",
            workflow,
            flags=re.DOTALL,
        )

        self.assertIsNotNone(apply_step)
        body = apply_step.group("body")
        self.assertIn(
            "terraform -chdir=ORCH apply -auto-approve -no-color tfplan.binary",
            body,
        )
        self.assertNotIn("steps.vars.outputs.extra", body)
        self.assertNotIn("steps.vars.outputs.var_files", body)


if __name__ == "__main__":
    unittest.main()
