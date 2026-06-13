import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts_python" / "prepare_var_files.py"


class PrepareVarFilesTests(unittest.TestCase):
    def test_copies_json_files_and_substitutes_environment_placeholders(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_dir = root / "oci" / "eu-frankfurt-1"
            (config_dir / "database").mkdir(parents=True)
            (config_dir / "ansible").mkdir()
            output_dir = root / "prepared"

            source_file = config_dir / "database" / "database.json"
            source_file.write_text(
                json.dumps(
                    {
                        "autonomous_databases_configuration": {
                            "autonomous_databases": {
                                "ADB-PROD-PROJ1-01-KEY": {
                                    "admin_password": "__ADB_ADMIN_PASSWORD__"
                                }
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            (config_dir / "ansible" / "adb-lifecycle.json").write_text("{}", encoding="utf-8")

            env = os.environ.copy()
            env["ADB_ADMIN_PASSWORD"] = "ExampleSecret#2026"

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(config_dir), str(output_dir)],
                env=env,
                check=False,
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("-var-file", result.stdout)
            prepared_file = output_dir / "database" / "database.json"
            self.assertTrue(prepared_file.exists())
            self.assertFalse((output_dir / "ansible" / "adb-lifecycle.json").exists())
            self.assertEqual(
                json.loads(prepared_file.read_text(encoding="utf-8"))[
                    "autonomous_databases_configuration"
                ]["autonomous_databases"]["ADB-PROD-PROJ1-01-KEY"]["admin_password"],
                "ExampleSecret#2026",
            )
            self.assertEqual(source_file.read_text(encoding="utf-8").count("__ADB_ADMIN_PASSWORD__"), 1)

    def test_fails_when_placeholder_has_no_environment_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_dir = root / "oci" / "eu-frankfurt-1"
            config_dir.mkdir(parents=True)
            output_dir = root / "prepared"
            (config_dir / "database.json").write_text(
                '{"key": "__MISSING_SECRET__"}',
                encoding="utf-8",
            )

            env = os.environ.copy()
            env.pop("MISSING_SECRET", None)

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(config_dir), str(output_dir)],
                env=env,
                check=False,
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("__MISSING_SECRET__", result.stderr)

    def test_substitutes_placeholders_from_secret_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_dir = root / "oci" / "eu-frankfurt-1"
            config_dir.mkdir(parents=True)
            output_dir = root / "prepared"
            (config_dir / "database.json").write_text(
                json.dumps(
                    {
                        "autonomous_databases_configuration": {
                            "autonomous_databases": {
                                "ADB-PROD-PROJ1-01-KEY": {
                                    "admin_password": "__ADB_PROD_PROJ1_01_ADMIN_PASSWORD__"
                                },
                                "ADB-PROD-PROJ1-02-KEY": {
                                    "admin_password": "__ADB_PROD_PROJ1_02_ADMIN_PASSWORD__"
                                },
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            env = os.environ.copy()
            env["GITOPS_SECRET_VALUES"] = json.dumps(
                {
                    "ADB_PROD_PROJ1_01_ADMIN_PASSWORD": "FirstSecret#2026",
                    "ADB_PROD_PROJ1_02_ADMIN_PASSWORD": "SecondSecret#2026",
                }
            )

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(config_dir), str(output_dir)],
                env=env,
                check=False,
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            prepared = json.loads((output_dir / "database.json").read_text(encoding="utf-8"))
            adbs = prepared["autonomous_databases_configuration"]["autonomous_databases"]
            self.assertEqual(adbs["ADB-PROD-PROJ1-01-KEY"]["admin_password"], "FirstSecret#2026")
            self.assertEqual(adbs["ADB-PROD-PROJ1-02-KEY"]["admin_password"], "SecondSecret#2026")


if __name__ == "__main__":
    unittest.main()
