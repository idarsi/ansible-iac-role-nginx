"""Native package-dispatch bindings with DNF mocked and transport forbidden."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
OVERRIDE = "distinct-package-fixture"


class PackageDispatchTests(unittest.TestCase):
    """Exercise unchanged production includes, arguments and native assertions."""

    def run_dispatch(self, states=("present", "absent"), failure="", hardcoded=False):
        """Copy production files into one disposable, connection-forbidden run."""
        parent = "/tmp/opencode" if Path("/tmp/opencode").is_dir() else None
        with tempfile.TemporaryDirectory(prefix="nginx-package-", dir=parent) as directory:
            root = Path(directory)
            (root / "tasks/shared").mkdir(parents=True)
            for name in ("package_dispatch.yml", "package_present.yml",
                         "package_absent.yml", "log_write.yml"):
                shutil.copyfile(ROOT / "tasks" / name, root / "tasks" / name)
            shutil.copyfile(ROOT / "tasks/shared/log_write.yml",
                            root / "tasks/shared/log_write.yml")
            if hardcoded:
                dispatch = root / "tasks/package_dispatch.yml"
                dispatch.write_text(dispatch.read_text().replace(
                    "{{ iac_dnf_main_package }}", "nginx"
                ))
            shutil.copyfile(ROOT / "tests/fixtures/package_engine.py",
                            root / "package_engine.py")
            (root / "connection_plugins").mkdir()
            shutil.copyfile(ROOT / "tests/fixtures/pid_no_connection.py",
                            root / "connection_plugins/pid_no_connection.py")
            tasks = []
            for state in states:
                tasks.extend([
                    {"name": f"Native {state} dispatch under inherited check mode",
                     "check_mode": True, "block": [
                         {"ansible.builtin.include_tasks": "tasks/package_dispatch.yml",
                          "vars": {"iac_package_state": state}},
                         {"ansible.builtin.assert": {"that": [
                             "iac_package_operation.mock_name == iac_dnf_main_package",
                             "not (iac_package_operation.failed | default(false))",
                             "iac_package_operation.changed"
                             if state == "present" else
                             "not iac_package_operation.changed",
                         ]}},
                     ]},
                ])
            play = [{
                "name": "Host-free production package dispatch",
                "hosts": "fixture", "gather_facts": False,
                "connection": "pid_no_connection",
                "vars": {
                    "iac_dnf_main_package": OVERRIDE,
                    "iac_dnf_sslverify": True, "iac_dnf_validate_certs": True,
                    "iac_dnf_disable_gpg_check": False,
                    "iac_ansible_report": False, "mock_fail_state": failure,
                },
                "tasks": tasks,
            }]
            (root / "play.yml").write_text(yaml.safe_dump(play))
            (root / "ansible.cfg").write_text(
                "[defaults]\nconnection_plugins=./connection_plugins\n"
                "retry_files_enabled=False\n"
            )
            audit = root / "audit.jsonl"
            env = {key: value for key, value in os.environ.items()
                   if not key.startswith("ANSIBLE_")}
            env.update(
                ANSIBLE_CONFIG=str(root / "ansible.cfg"), ANSIBLE_NOCOLOR="1",
                PACKAGE_MOCK_AUDIT=str(audit), PYTHONDONTWRITEBYTECODE="1",
            )
            result = subprocess.run(
                [sys.executable, "-B", "package_engine.py", "-i", "fixture,", "play.yml"],
                cwd=root, env=env, text=True, capture_output=True, timeout=30, check=False,
            )
            calls = [json.loads(line) for line in audit.read_text().splitlines()] \
                if audit.exists() else []
            return result, calls

    def test_both_states_bind_exact_secure_arguments_and_inherit_check_mode(self):
        result, calls = self.run_dispatch()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(calls, [
            {"check": True, "args": {
                "name": OVERRIDE, "state": state, "sslverify": True,
                "validate_certs": True, "disable_gpg_check": False,
            }} for state in ("present", "absent")
        ])

    def test_invalid_state_rejected_before_dnf(self):
        result, calls = self.run_dispatch(states=("invalid",))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, [])
        self.assertIn("The package dispatch state must be present or absent.",
                      result.stdout + result.stderr)

    def test_dnf_failure_is_not_hidden_or_followed_by_another_state(self):
        for state in ("present", "absent"):
            with self.subTest(state=state):
                result, calls = self.run_dispatch(states=(state, "present"), failure=state)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(len(calls), 1)
                self.assertEqual(calls[0]["args"]["state"], state)
                self.assertIn("Injected DNF boundary failure", result.stdout + result.stderr)

    def test_hardcoded_default_negative_control_is_caught(self):
        result, calls = self.run_dispatch(hardcoded=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["args"]["name"], "nginx")
        self.assertIn("iac_package_operation.mock_name == iac_dnf_main_package",
                      result.stdout + result.stderr)

    def test_controller_symlink_fixture_retains_guard_rescue_and_always_cleanup(self):
        tasks = yaml.safe_load((
            ROOT / "molecule/podman-rocky9-validation/tasks/security_proxy_validation.yml"
        ).read_text())
        index = next(i for i, task in enumerate(tasks)
                     if task["name"] == "Reject a role files symlink that resolves outside files")
        inspect, guard, block = tasks[index - 2:index + 1]
        self.assertFalse(inspect["ansible.builtin.stat"]["follow"])
        self.assertEqual(guard["ansible.builtin.assert"]["that"],
                         ["not security_validation_escape_fixture.stat.exists"])
        for task in (inspect, block["block"][0], block["always"][0]):
            self.assertEqual(task["delegate_to"], "localhost")
            self.assertIs(task["become"], False)
        self.assertEqual(block["block"][0]["ansible.builtin.file"]["state"], "link")
        self.assertEqual(block["always"][0]["ansible.builtin.file"]["state"], "absent")
        self.assertEqual(block["block"][1]["vars"]["state"], "validate")
        self.assertIs(block["rescue"][0]["ansible.builtin.set_fact"][
            "security_validation_symlink_escape_rejected"], True)


    def test_real_package_override_fixture_belongs_to_kvm_prepare(self):
        scenario = ROOT / "molecule/kvm-rocky9-check-mode"
        play, = yaml.safe_load((scenario / "prepare.yml").read_text())
        self.assertEqual(play["hosts"], "all")
        self.assertIs(play["become"], True)
        self.assertIs(play["gather_facts"], True)
        tasks = play["tasks"]
        self.assertEqual(tasks[0]["ansible.builtin.set_fact"], {
            "validation_documented_default_package": "nginx",
            "iac_dnf_main_package": "nginx-core",
            "validation_package_fixture_name": "nginx-core",
        })
        self.assertIn("validation_package_fixture_name not in ansible_facts.packages",
                      tasks[2]["ansible.builtin.assert"]["that"])
        self.assertEqual([
            task["vars"]["validation_package_state"] for task in tasks
            if task.get("ansible.builtin.include_tasks") == "tasks/package_override.yml"
        ], ["present", "absent"])
        self.assertEqual(tasks[-1]["ansible.builtin.assert"]["that"],
                         ["validation_package_fixture_name not in ansible_facts.packages"])
        self.assertEqual(sum("ansible.builtin.package_facts" in task for task in tasks), 2)
        helper = yaml.safe_load((scenario / "tasks/package_override.yml").read_text())
        self.assertEqual(helper[1]["ansible.builtin.include_role"]["tasks_from"],
                         "package_dispatch")
        self.assertIs(helper[1]["ansible.builtin.include_role"]["apply"]["check_mode"], True)
        validation = ROOT / "molecule/podman-rocky9-validation"
        self.assertNotIn("package_override.yml", (validation / "regressions.yml").read_text())
        self.assertFalse((validation / "tasks/package_override.yml").exists())


if __name__ == "__main__":
    unittest.main()
