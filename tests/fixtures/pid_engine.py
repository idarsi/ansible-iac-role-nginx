"""Run the real CLI with an explicit allowlisted action-loader interception."""

from unittest.mock import patch

from ansible.cli.playbook import main
from ansible.plugins.loader import action_loader
from pid_mock_action import ActionModule


original_get = type(action_loader).get
MOCKED = {"command", "stat", "service_facts", "systemd_service", "systemd"}


def mocked_get(plugin_loader, name, *args, **kwargs):
    """Intercept FQCN actions too; retain native include/assert/debug/meta."""
    task = kwargs.get("task")
    action = task.action if task is not None else name
    if plugin_loader.type == "action" and action.rsplit(".", 1)[-1] in MOCKED:
        if kwargs.pop("class_only", False):
            return ActionModule
        kwargs.pop("collection_list", None)
        return ActionModule(*args, **kwargs)
    return original_get(plugin_loader, name, *args, **kwargs)


if __name__ == "__main__":
    with patch.object(type(action_loader), "get", new=mocked_get):
        main()
