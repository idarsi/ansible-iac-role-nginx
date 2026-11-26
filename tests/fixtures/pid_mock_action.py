"""Host-free action boundary for the native production-handler regression."""

import json
import os

from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    """Return synthetic facts/results without invoking modules or connections."""

    def run(self, tmp=None, task_vars=None):
        variables = task_vars or {}
        action = self._task.action.rsplit(".", 1)[-1]
        args = self._task.args
        check = self._task.check_mode
        with open(os.environ["PID_MOCK_AUDIT"], "a", encoding="utf-8") as audit:
            audit.write(json.dumps({"action": action, "args": args, "check": check}) + "\n")
        if action == "stat":
            if args["path"] == "/usr/sbin/restorecon":
                return {"stat": {"exists": True, "executable": True}}
            return {"stat": variables["mock_pid"]}
        if action == "service_facts":
            return {"ansible_facts": {"services": {
                "nginx.service": {"state": variables["mock_service"]}
            }}}
        if action in ("systemd_service", "systemd"):
            return {"changed": not check}
        if action == "command":
            argv = args.get("argv", [])
            if argv and argv[0] == "/usr/bin/systemctl":
                if argv != ["/usr/bin/systemctl", "show", "--property=ActiveState",
                            "--property=SubState", "nginx.service"]:
                    raise AssertionError(f"Unexpected systemctl command: {argv}")
                lines = variables["mock_systemd_properties"]
                return {"rc": 0, "stdout": "\n".join(lines), "stdout_lines": lines}
            if check:
                return {"skipped": True, "stdout": "", "rc": 0}
            if not argv:
                return {
                    "failed": variables["mock_failure"],
                    "rc": 1 if variables["mock_failure"] else 0,
                    "stdout": "",
                }
            prefix = "Would relabel" if "-n" in argv else "Relabeled"
            return {"rc": 0, "stdout": f"{prefix} /run/nginx.pid from a:b:c:s0 to a:b:d:s0"}
        raise AssertionError(f"Unmocked action: {action}")
