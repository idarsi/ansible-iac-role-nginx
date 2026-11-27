"""Native Ansible CLI: replace only DNF actions, never connect to a host."""

import json
import os
from unittest.mock import patch

from ansible.cli.playbook import main
from ansible.plugins.action import ActionBase
from ansible.plugins.loader import action_loader


class PackageAction(ActionBase):
    """Record fully templated arguments and return synthetic solver results."""

    def run(self, tmp=None, task_vars=None):
        assert self._task.action.rsplit(".", 1)[-1] == "dnf"
        args = self._task.args
        with open(os.environ["PACKAGE_MOCK_AUDIT"], "a", encoding="utf-8") as audit:
            audit.write(json.dumps({
                "args": args, "check": self._task.check_mode,
            }) + "\n")
        if args["state"] == (task_vars or {}).get("mock_fail_state"):
            return {"failed": True, "msg": "Injected DNF boundary failure"}
        return {"changed": args["state"] == "present", "mock_name": args["name"]}


original_get = type(action_loader).get


def mocked_get(plugin_loader, name, *args, **kwargs):
    """Keep native include/assert/register/check semantics; intercept DNF only."""
    task = kwargs.get("task")
    action = task.action if task is not None else name
    if plugin_loader.type == "action" and action.rsplit(".", 1)[-1] == "dnf":
        if kwargs.pop("class_only", False):
            return PackageAction
        kwargs.pop("collection_list", None)
        return PackageAction(*args, **kwargs)
    return original_get(plugin_loader, name, *args, **kwargs)


if __name__ == "__main__":
    with patch.object(type(action_loader), "get", new=mocked_get):
        main()
