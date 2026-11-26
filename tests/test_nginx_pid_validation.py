"""Native engine/module regressions with host actions and transport mocked."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import yaml
from ansible.modules import command
from ansible.playbook.block import Block
from ansible.playbook.play import Play
from ansible.playbook.task import Task
from ansible.plugins.loader import init_plugin_loader
from jinja2 import Environment, StrictUndefined


ROOT = Path(__file__).resolve().parents[1]
TASKS = yaml.safe_load((ROOT / "tasks/nginx_config_test.yml").read_text())
PROBE, REPAIR = TASKS[-3:-1]
ENV = Environment(undefined=StrictUndefined)
ENV.tests["search"] = lambda text, pattern: re.search(pattern, text) is not None


class ModuleResult(Exception):
    """Capture command module results instead of exiting the test process."""

    def __init__(self, result: dict) -> None:
        super().__init__()
        self.result = result


def run_mocked_command(task: dict, effective_check_mode: bool) -> tuple[dict, Mock]:
    """Run Ansible's command control flow with all external execution mocked."""
    module = Mock()
    module.params = {
        "_uses_shell": False,
        "chdir": None,
        "executable": None,
        "_raw_params": None,
        "cmd": None,
        "argv": task["ansible.builtin.command"]["argv"],
        "creates": None,
        "removes": None,
        "stdin": None,
        "stdin_add_newline": True,
        "strip_empty_ends": True,
        "expand_argument_vars": True,
    }
    module.check_mode = task.get("check_mode", effective_check_mode)
    module.run_command.return_value = (0, b"", b"")
    module.exit_json.side_effect = lambda **result: _raise_result(result)
    module.fail_json.side_effect = AssertionError("Unexpected module failure")
    with patch.object(command, "AnsibleModule", return_value=module):
        try:
            command.main()
        except ModuleResult as result:
            return result.result, module.run_command
    raise AssertionError("Command module did not return a result")


def _raise_result(result: dict) -> None:
    raise ModuleResult(result)


class PidValidationTests(unittest.TestCase):
    """Verify actual role expressions and native Ansible preview behavior."""

    @classmethod
    def setUpClass(cls) -> None:
        init_plugin_loader()

    def test_preview_inherits_cli_play_block_and_task_modes(self) -> None:
        """CLI false plus inherited true must never execute the repair."""
        for mode in ("cli", "play", "block", "task"):
            with self.subTest(mode=mode):
                play = Play()
                if mode == "play":
                    play.check_mode = True
                parent = {"block": []}
                if mode in ("block", "task"):
                    parent["check_mode"] = True
                block = Block.load(parent, play=play)
                inherited = Task.load(REPAIR, block=block).check_mode
                effective = True if mode == "cli" else inherited
                # include_role.apply builds an inherited block, just like the
                # task-override case above. No CLI-only magic variable is used.
                cli_variables = {"ansible_check_mode": mode == "cli"}
                if mode != "cli":
                    self.assertFalse(cli_variables["ansible_check_mode"])
                self.assertTrue(effective)
                self.assertNotIn("ansible_check_mode", str(PROBE))
                self.assertNotIn("ansible_check_mode", str(REPAIR))

                preview_result, preview_run = run_mocked_command(PROBE, effective)
                self.assertFalse(preview_result.get("skipped", False))
                self.assertEqual(
                    preview_run.call_args.args[0],
                    ["/usr/sbin/restorecon", "-n", "-v", "/run/nginx.pid"],
                )
                repair_result, repair_run = run_mocked_command(REPAIR, effective)
                repair_run.assert_not_called()
                self.assertTrue(repair_result["skipped"])

                # nginx -t must likewise inherit preview mode.
                config_test = {
                    **TASKS[1],
                    "ansible.builtin.command": {"argv": ["/usr/sbin/nginx", "-t"]},
                }
                _, nginx_run = run_mocked_command(config_test, effective)
                nginx_run.assert_not_called()

    def test_normal_mode_can_execute_the_repair(self) -> None:
        self.assertNotIn("check_mode", REPAIR)
        result, run = run_mocked_command(REPAIR, False)
        self.assertFalse(result.get("skipped", False))
        self.assertEqual(
            run.call_args.args[0], ["/usr/sbin/restorecon", "-v", "/run/nginx.pid"]
        )

    def test_only_exact_policy_messages_report_changes(self) -> None:
        fixtures = [
            ("", False, False),
            ("Relabeled /run/nginx.pid from a:b:c:s0 to a:b:d:s0", False, True),
            ("Would relabel /run/nginx.pid from a:b:c:s0 to a:b:d:s0", True, False),
            (
                "/run/nginx.pid not reset as customized by admin "
                "to a:b:custom_t:s0",
                False,
                False,
            ),
            ("Relabeled /run/nginx.pid.other from x to y", False, False),
            ("Would relabel /run/nginxXpid from x to y", False, False),
            ("Info: Relabeled /run/nginx.pid from x to y", False, False),
            ("Would relabel /run/nginx.pid from x to y\nUnrelated info", True, False),
        ]
        for stdout, predicted, actual in fixtures:
            with self.subTest(stdout=stdout):
                context = {
                    "nginx_pid_restorecon": {"stdout": stdout},
                    "nginx_pid_relabel": {"stdout": stdout},
                }
                self.assertEqual(
                    ENV.compile_expression(PROBE["changed_when"])(**context),
                    predicted,
                )
                self.assertEqual(
                    ENV.compile_expression(REPAIR["changed_when"])(**context),
                    actual,
                )
        self.assertEqual(REPAIR["when"][-1], PROBE["changed_when"])
        self.assertEqual(PROBE["environment"]["LC_ALL"], "C")
        self.assertEqual(REPAIR["environment"]["LC_ALL"], "C")


class HandlerGraphTests(unittest.TestCase):
    """Actually expand notified production includes using Ansible's engine."""

    def run_graph(self, *, notified=True, service="running", failure=False,
                  preview=False, pid=None, selinux="enabled", old_blocks=False,
                  stopped_properties=None, sequence=None):
        """Copy unmodified production inputs; only replace external actions."""
        temp_parent = "/tmp/opencode" if Path("/tmp/opencode").is_dir() else None
        with tempfile.TemporaryDirectory(prefix="nginx-pid-", dir=temp_parent) as directory:
            root = Path(directory)
            (root / "tasks").mkdir()
            (root / "handlers").mkdir()
            for name in ("nginx_config_test.yml", "nginx_pid_guard.yml"):
                shutil.copyfile(ROOT / "tasks" / name, root / "tasks" / name)
            shutil.copyfile(ROOT / "handlers/main.yml", root / "handlers/main.yml")
            if old_blocks:
                # Negative control proves native handler expansion catches the
                # original shape, not merely a source assertion about blocks.
                tasks = yaml.safe_load((root / "tasks/nginx_config_test.yml").read_text())
                tasks[2:-1] = [{"name": "Old nested handler blocks", "block": [
                    {"block": tasks[2:-1]}
                ]}]
                (root / "tasks/nginx_config_test.yml").write_text(yaml.safe_dump(tasks))
            for name in ("pid_engine.py", "pid_mock_action.py"):
                shutil.copyfile(ROOT / "tests/fixtures" / name, root / name)
            connections = root / "connection_plugins"
            connections.mkdir()
            shutil.copyfile(ROOT / "tests/fixtures/pid_no_connection.py",
                            connections / "pid_no_connection.py")
            audit = root / "audit.jsonl"
            play_tasks = (
                [{"name": "Notify production validation",
                  "ansible.builtin.debug": {"msg": "synthetic configuration change"},
                  "changed_when": True, "notify": "Validate Nginx configuration"},
                 {"ansible.builtin.meta": "flush_handlers"}]
                if notified else
                [{"ansible.builtin.include_tasks": "tasks/nginx_config_test.yml"},
                 {"ansible.builtin.meta": "flush_handlers"}]
            )
            if sequence is not None:
                role = root / "roles/nginx"
                role.mkdir(parents=True)
                shutil.copytree(root / "tasks", role / "tasks")
                shutil.copytree(root / "handlers", role / "handlers")
                regression = yaml.safe_load((
                    ROOT / "molecule/kvm-rocky9-lifecycle/tasks/pid_label_regression.yml"
                ).read_text())
                previews = [
                    next(task for task in regression if task["name"] == name)
                    for name in (
                        "Preview PID label reconciliation without running nginx -t",
                        "Preview PID repair using block-inherited check mode",
                    )
                ]

                def bind_include(task):
                    """Bind actual guest fixture includes to the copied role."""
                    if "block" in task:
                        for child in task["block"]:
                            bind_include(child)
                    elif "ansible.builtin.include_role" in task:
                        task["ansible.builtin.include_role"]["name"] = str(role)
                    elif "ansible.builtin.include_tasks" in task:
                        task["ansible.builtin.include_tasks"]["file"] = str(
                            role / "tasks/nginx_config_test.yml")

                for task in previews:
                    bind_include(task)
                if sequence == "old":
                    # Preserve the original fixture as an executable negative
                    # control after the guest fixture is corrected.
                    previews = [
                        {"ansible.builtin.include_role": {
                            "name": str(role), "tasks_from": "nginx_config_test.yml",
                            "apply": {"check_mode": True}}},
                        {"check_mode": True, "block": [
                            {"ansible.builtin.include_role": {
                                "name": str(role), "tasks_from": "nginx_config_test.yml"}}
                        ]},
                    ]
                play_tasks = [
                    {"ansible.builtin.set_fact": {
                        "mock_phase": "registration"}},
                    {"ansible.builtin.include_role": {
                        "name": str(role), "tasks_from": "nginx_config_test.yml"}},
                    {"ansible.builtin.set_fact": {
                        "mock_phase": "preview"}},
                    *previews,
                    {"ansible.builtin.assert": {"that": [
                        "not ansible_check_mode", "nginx_pid_restorecon.changed",
                        "nginx_pid_relabel.skipped"]}},
                    {"ansible.builtin.set_fact": {"mock_phase": "repair"}},
                    *play_tasks,
                    {"ansible.builtin.assert": {"that": [
                        "nginx_pid_restorecon.changed", "nginx_pid_relabel.changed",
                        "not nginx_pid_relabel.skipped | default(false)"]}},
                    {"ansible.builtin.set_fact": {"mock_phase": "repeat"}},
                    *play_tasks,
                    {"ansible.builtin.assert": {"that": [
                        "not nginx_pid_restorecon.changed"]}},
                ]
            if stopped_properties is not None:
                # Exercise the actual guest status/assertion tasks, never its
                # mutating fixture setup, through the same isolated engine.
                regression = yaml.safe_load((
                    ROOT / "molecule/kvm-rocky9-lifecycle/tasks/pid_label_regression.yml"
                ).read_text())
                start = next(
                    index for index, task in enumerate(regression)
                    if task["name"] == "Inspect the PID file created by stopped-service validation"
                )
                play_tasks += regression[start:start + 3]
            play = [{
                "name": "Host-free production handler graph",
                "hosts": "fixture", "gather_facts": False,
                "connection": "pid_no_connection",
                "vars": {
                    "ansible_facts": {
                        "selinux": {"status": selinux},
                        "services": {"nginx.service": {"state": service}},
                    },
                    "iac_service_name": "nginx", "nginx_state": "started",
                    "mock_service": service, "mock_failure": failure,
                    "mock_systemd_properties": stopped_properties,
                    "mock_pid": pid if pid is not None else {
                        "exists": True, "isreg": True, "islnk": False, "nlink": 1},
                },
                "handlers": [{"ansible.builtin.import_tasks": "handlers/main.yml"}],
                "tasks": play_tasks,
            }]
            (root / "play.yml").write_text(yaml.safe_dump(play))
            (root / "ansible.cfg").write_text(
                "[defaults]\nconnection_plugins=./connection_plugins\n"
                "retry_files_enabled=False\n")
            env = {**os.environ, "ANSIBLE_CONFIG": str(root / "ansible.cfg"),
                   "PID_MOCK_AUDIT": str(audit), "ANSIBLE_NOCOLOR": "1",
                   "PYTHONDONTWRITEBYTECODE": "1"}
            args = [sys.executable, "-B", "pid_engine.py",
                    "-i", "fixture,", "play.yml"]
            if preview:
                args.append("--check")
            result = subprocess.run(args, cwd=root, env=env, text=True,
                                    capture_output=True, timeout=30, check=False)
            events = [json.loads(line) for line in audit.read_text().splitlines()] \
                if audit.exists() else []
            return result, events

    def test_actual_notify_and_shared_start_paths(self):
        for notified, service, preview in (
            (False, "running", False), (True, "running", False),
            (True, "stopped", False), (True, "running", True),
            (False, "running", True),
        ):
            with self.subTest(notified=notified, service=service, preview=preview):
                result, events = self.run_graph(
                    notified=notified, service=service, preview=preview)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                reloads = [e for e in events if e["action"] == "systemd_service"]
                self.assertEqual(len(reloads), int(notified and service == "running"))
                commands = [e for e in events if e["action"] == "command"]
                self.assertEqual(len(commands), 3)
                self.assertEqual([e["check"] for e in commands], [preview, False, preview])

    def test_failure_does_not_reload(self):
        result, events = self.run_graph(failure=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("systemd_service", [e["action"] for e in events])
        self.assertEqual(len([e for e in events if e["action"] == "command"]), 1)

    def test_preview_then_real_handler_sequence(self):
        result, events = self.run_graph(sequence="fixed", service="stopped")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        commands = [event for event in events if event["action"] == "command"]
        phases = {
            phase: [event for event in commands if event.get("phase") == phase]
            for phase in ("registration", "preview", "repair", "repeat")
        }
        self.assertEqual([e["check"] for e in phases["preview"]],
                         [True, False, True] * 2)
        self.assertTrue(all(not e["pid_correct"] for e in phases["preview"]))
        self.assertEqual([e["check"] for e in phases["repair"]], [False] * 3)
        self.assertEqual([e["check"] for e in phases["repeat"]], [False] * 2)
        self.assertTrue(all(e["pid_correct"] for e in phases["repeat"]))
        self.assertNotIn("systemd_service", [e["action"] for e in events])

    def test_negative_control_preview_role_reregisters_checked_handlers(self):
        result, events = self.run_graph(sequence="old", service="stopped")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        commands = [event for event in events if
                    event["action"] == "command" and event.get("phase") == "repair"]
        self.assertEqual([e["check"] for e in commands], [True, False, True])
        self.assertTrue(all(not e["pid_correct"] for e in commands))
        self.assertIn("nginx_pid_relabel.changed", result.stdout)

    def test_policy_gates_and_unsafe_objects(self):
        for pid, selinux, success in (
            ({"exists": False}, "enabled", True),
            (None, "disabled", True),
            ({"exists": True, "isreg": True, "islnk": False, "nlink": 2}, "enabled", False),
            ({"exists": True, "isreg": False, "islnk": True, "nlink": 1}, "enabled", False),
            ({"exists": True, "isreg": False, "islnk": False, "nlink": 1}, "enabled", False),
        ):
            with self.subTest(pid=pid, selinux=selinux):
                result, events = self.run_graph(pid=pid, selinux=selinux)
                self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
                commands = [e for e in events if e["action"] == "command"]
                self.assertEqual(len(commands), int(success))

    def test_negative_control_rejects_original_nested_blocks(self):
        result, events = self.run_graph(old_blocks=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Using a block as a handler is not supported",
                      result.stdout + result.stderr)
        self.assertNotIn("systemd_service", [e["action"] for e in events])

    def test_stopped_pid_fixture_uses_exact_systemd_properties(self):
        pid = {"exists": True, "isreg": True, "islnk": False, "nlink": 1, "size": 0}
        for service in ("stopped", "inactive"):
            for properties, success in (
                (["ActiveState=inactive", "SubState=dead"], True),
                (["SubState=dead", "ActiveState=inactive"], True),
                (["ActiveState=active", "SubState=running"], False),
                (["ActiveState=failed", "SubState=failed"], False),
                (["ActiveState=activating", "SubState=start"], False),
                ([], False),
                (["ActiveState=inactive"], False),
                (["ActiveState inactive", "SubState=dead"], False),
                (["ActiveState=inactive", "SubState=dead", "SubState=dead"], False),
            ):
                with self.subTest(service=service, properties=properties):
                    result, events = self.run_graph(
                        service=service, pid=pid, stopped_properties=properties)
                    output = result.stdout + result.stderr
                    self.assertEqual(result.returncode == 0, success, output)
                    status = [event for event in events if
                              event["args"].get("argv", [None])[0] == "/usr/bin/systemctl"]
                    self.assertEqual(len(status), 1)
                    self.assertFalse(status[0]["check"])
                    if not success:
                        self.assertIn("Actual systemd properties:", output)
                        self.assertIn("PID metadata:", output)
                        self.assertIn("SubState=dead", output)


if __name__ == "__main__":
    unittest.main()
