"""Fail closed if a regression ever attempts host transport or module execution."""

from ansible.plugins.connection import ConnectionBase


class Connection(ConnectionBase):
    transport = "pid_no_connection"
    has_pipelining = False

    def _connect(self):
        raise AssertionError("Host connection forbidden")

    def exec_command(self, cmd, in_data=None, sudoable=True):
        raise AssertionError("Host command forbidden")

    def put_file(self, in_path, out_path):
        raise AssertionError("Host upload forbidden")

    def fetch_file(self, in_path, out_path):
        raise AssertionError("Host download forbidden")

    def close(self):
        pass
