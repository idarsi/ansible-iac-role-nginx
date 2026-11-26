"""Source and mocked-module checks; no commands, guests or backends are run."""

from pathlib import Path
import re
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
POLICY_TASKS = TASKS[2]["block"][1]["block"]
PROBE, REPAIR = POLICY_TASKS[-2:]
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
        self.assertEqual(REPAIR["when"], PROBE["changed_when"])
        self.assertEqual(PROBE["environment"]["LC_ALL"], "C")
        self.assertEqual(REPAIR["environment"]["LC_ALL"], "C")


if __name__ == "__main__":
    unittest.main()
