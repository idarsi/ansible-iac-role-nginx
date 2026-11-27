"""Exercise the actual CI shell with fake backends; never execute host setup."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ("podman-rocky9-blueprint-validation", "podman-rocky9-validation")
CHECKS = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())["jobs"][
    "checks"
]
STEPS = CHECKS["steps"]
SCRIPT = next(
    step["run"]
    for step in STEPS
    if step.get("name") == "Managed nonprivileged validation scenarios"
)

# PATH contains only these fakes and bash. Unknown commands fail closed; the
# prerequisite/setup step is inspected as text, never executed.
MOCK = r'''
import json
import os
from pathlib import Path
import subprocess
import sys

name, args = Path(sys.argv[0]).name, sys.argv[1:]
inside = os.environ.get("MOCK_INSIDE") == "yes"
if name == "sudo":
    assert not inside
    assert args[:8] == [
        "-n", "-H", "-u", "runner", "--", "/usr/bin/env", "-u", "XDG_RUNTIME_DIR"
    ], args
    assignments = (["XDG_RUNTIME_DIR=" + os.environ["XDG_RUNTIME_DIR"]]
                   if os.environ.get("XDG_RUNTIME_DIR") else [])
    assignments += [
        "PATH=" + os.environ["PATH"],
        "LD_LIBRARY_PATH=" + os.environ["LD_LIBRARY_PATH"],
        "IDARSI_TEST_ENVIRONMENT=" + os.environ["IDARSI_TEST_ENVIRONMENT"],
        "EXPECTED_RUNNER_UID=1001",
    ]
    assert args[8:] == assignments + ["/bin/bash", "-Eeuo", "pipefail"], args
    os.environ.pop("XDG_RUNTIME_DIR", None)
    for assignment in assignments:
        key, value = assignment.split("=", 1)
        os.environ[key] = value
    os.environ["MOCK_INSIDE"] = "yes"
    os.environ["HOME"] = os.environ["MOCK_HOME"]
    sys.exit(subprocess.run(["/bin/bash", "-Eeuo", "pipefail"]).returncode)
if not inside and name == "id":
    assert args in (["-un"], ["-u"]), args
    print("runner" if args == ["-un"] else "1001")
    sys.exit(0)
assert inside, f"{name} called outside credential wrapper"
if name in ("podman", "virsh", "scenario-context", "ansible-galaxy", "molecule",
            "pgrep"):
    assert os.environ["MOCK_UID"] == os.environ["MOCK_REAL_UID"] == "1001"
    assert os.environ["MOCK_GID"] == os.environ["MOCK_REAL_GID"] == "1001"
    assert "980" in os.environ["MOCK_GROUPS"].split()
    assert os.environ["HOME"] == "/mock/runner"
    assert os.environ.get("XDG_RUNTIME_DIR") == (
        os.environ["MOCK_XDG"] or None
    )
    assert os.environ["LD_LIBRARY_PATH"] == "/mock/python libraries"
event = name + " " + " ".join(args)
with open(os.environ["MOCK_LOG"], "a") as stream:
    stream.write(json.dumps(event) + "\n")
if len(Path(os.environ["MOCK_LOG"]).read_text().splitlines()) == int(
    os.environ["MOCK_FAIL_AT"]
):
    sys.exit(37)
if name == "id":
    assert args in ([], ["-un"], ["-u"], ["-ru"], ["-g"], ["-rg"], ["-G"]), args
    print(os.environ["MOCK_UID"] if args == ["-u"]
          else os.environ["MOCK_REAL_UID"] if args == ["-ru"]
          else os.environ["MOCK_GID"] if args == ["-g"]
          else os.environ["MOCK_REAL_GID"] if args == ["-rg"]
          else os.environ["MOCK_GROUPS"] if args == ["-G"]
          else os.environ["MOCK_NAME"] if args == ["-un"]
          else "uid=1001(runner) gid=1001(runner) groups=1001,980(libvirt)")
elif name == "getent":
    assert args in (["group", "libvirt"], ["passwd", os.environ["MOCK_UID"]]), args
    print("libvirt:x:980:runner" if args[0] == "group"
          else "runner:x:1001:1001::/mock/runner:/bin/bash")
elif name == "podman":
    assert args in (["--remote=false", "info"],
                    ["--remote=false", "network", "ls", "--format", "json"],
                    ["--remote=false", "ps", "--all", "--quiet",
                     "--filter", "label=io.idarsi.test-run"],
                    ["--remote=false", "network", "ls", "--quiet",
                     "--filter", "label=io.idarsi.test-run"]), args
    if "--quiet" in args:
        print(os.environ["MOCK_CONTAINERS" if "ps" in args else "MOCK_NETWORKS"])
    else:
        print("[]" if "network" in args else "mock rootless info")
elif name == "pgrep":
    assert args == ["-u", "1001", "-x", "pasta|passt|slirp4netns"], args
    rc = int(os.environ["MOCK_PGREP_RC"])
    if rc == 0:
        print("98765")
    sys.exit(rc)
elif name == "virsh":
    assert args == ["--connect", "qemu:///system", "net-list", "--all"], args
elif name == "scenario-context":
    assert args[:4] == ["resolve", "--backend", "podman", "--scenario"], args
    assert args[4] in ("podman-rocky9-blueprint-validation",
                       "podman-rocky9-validation"), args
    assert args[5:] == ["--role", os.getcwd()], args
    print(json.dumps({"collections_directory": "/mock/" + args[4]}))
elif name == "python":
    assert args == ["-c",
        'import json,sys; print(json.load(sys.stdin)["collections_directory"])'], args
    print(json.load(sys.stdin)["collections_directory"])
elif name == "ansible-galaxy":
    assert args[:5] == ["collection", "install", "--requirements-file",
                        "requirements.yml", "--collections-path"], args
    assert args[5] in ("/mock/podman-rocky9-blueprint-validation",
                       "/mock/podman-rocky9-validation"), args
elif name == "molecule":
    assert args in (["test", "-s", "podman-rocky9-blueprint-validation"],
                    ["test", "-s", "podman-rocky9-validation"]), args
else:
    raise AssertionError(f"Unexpected command: {name}")
'''


class BackendContextTests(unittest.TestCase):
    """Check credential consistency, order and original failure propagation."""

    def run_script(
        self, failure: int = 0, uid: str = "1001", gid: str = "1001",
        groups: str = "1001 980", name: str = "runner",
        real_uid: str = "1001", real_gid: str = "1001",
        home: str = "/mock/runner", xdg: str = "",
        containers: str = "", networks: str = "", pgrep_rc: int = 1,
    ) -> tuple[subprocess.CompletedProcess, list]:
        """Run only the extracted managed step with an isolated fake PATH."""
        with tempfile.TemporaryDirectory(prefix="nginx-ci-mock ' $-") as directory:
            base = Path(directory)
            (base / "bash").symlink_to("/bin/bash")
            (base / "scripts").mkdir()
            for command_name in (
                "sudo", "id", "getent", "podman", "virsh", "scenario-context",
                "python", "ansible-galaxy", "molecule", "pgrep",
            ):
                executable = base / command_name
                executable.write_text(f"#!{sys.executable}\n{MOCK}")
                executable.chmod(0o700)
            (base / "scripts/scenario-context").symlink_to(base / "scenario-context")
            log = base / "calls.jsonl"
            log.touch()
            result = subprocess.run(
                ["/bin/bash", "-Eeuo", "pipefail", "-c", SCRIPT],
                cwd=ROOT,
                env={
                    **({"XDG_RUNTIME_DIR": xdg} if xdg else {}),
                    "PATH": directory,
                    "IDARSI_TEST_ENVIRONMENT": directory,
                    "LD_LIBRARY_PATH": "/mock/python libraries",
                    "MOCK_LOG": str(log),
                    "MOCK_FAIL_AT": str(failure),
                    "MOCK_UID": uid,
                    "MOCK_GID": gid,
                    "MOCK_GROUPS": groups,
                    "MOCK_NAME": name,
                    "MOCK_REAL_UID": real_uid,
                    "MOCK_REAL_GID": real_gid,
                    "MOCK_HOME": home,
                    "MOCK_XDG": xdg,
                    "MOCK_CONTAINERS": containers,
                    "MOCK_NETWORKS": networks,
                    "MOCK_PGREP_RC": str(pgrep_rc),
                },
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            calls = [json.loads(line) for line in log.read_text().splitlines()]
            return result, calls

    def test_no_backend_initialization_outside_wrapper(self):
        for step in STEPS:
            if step.get("name") == "Managed nonprivileged validation scenarios":
                continue
            for line in step.get("run", "").splitlines():
                self.assertFalse(
                    line.strip().startswith(("podman ", "virsh ", "sg ", "pgrep ")),
                    line,
                )

    def test_runner_uses_maintained_compatibility_baseline(self):
        self.assertEqual(CHECKS["runs-on"], "ubuntu-24.04")

    def test_success_and_fail_fast_at_each_boundary(self):
        result, calls = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = ["id -u", "id -ru", "getent passwd 1001", "id -un",
                    "id -g", "id -rg",
                    "getent group libvirt", "id -G", "id ",
                    "podman --remote=false info",
                    "podman --remote=false network ls --format json",
                    "virsh --connect qemu:///system net-list --all"]
        for scenario in SCENARIOS:
            expected.extend([
                f"scenario-context resolve --backend podman --scenario {scenario} "
                f"--role {ROOT}",
                'python -c import json,sys; print(json.load(sys.stdin)'
                '["collections_directory"])',
                "ansible-galaxy collection install --requirements-file "
                f"requirements.yml --collections-path /mock/{scenario}",
                f"molecule test -s {scenario}",
            ])
        expected.extend([
            "podman --remote=false ps --all --quiet "
            "--filter label=io.idarsi.test-run",
            "podman --remote=false network ls --quiet "
            "--filter label=io.idarsi.test-run",
            "pgrep -u 1001 -x pasta|passt|slirp4netns",
        ])
        self.assertEqual(calls, expected)
        # Includes initialization, both discoveries, resolution, JSON parsing,
        # private collection install and full Molecule lifecycle boundaries.
        for index, failure in enumerate(expected):
            with self.subTest(failure=failure):
                result, calls = self.run_script(index + 1)
                self.assertEqual(result.returncode, 37, result.stderr)
                self.assertEqual(calls, expected[:index + 1])
                self.assertIn("exit 37", result.stderr)
                self.assertRegex(result.stderr, r"line [0-9]+")

    def test_cleanup_absence_gate_rejects_leftovers_and_query_errors(self):
        result, success_calls = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        for overrides, rc, last_call in (
            ({"containers": "container-fixture"}, 1, success_calls[-2]),
            ({"networks": "network-fixture"}, 1, success_calls[-2]),
            ({"pgrep_rc": 0}, 1, success_calls[-1]),
            ({"pgrep_rc": 2}, 2, success_calls[-1]),
        ):
            with self.subTest(overrides=overrides):
                result, calls = self.run_script(**overrides)
                self.assertEqual(result.returncode, rc, result.stderr)
                self.assertEqual(calls, success_calls[:success_calls.index(last_call) + 1])
                self.assertIn(f"molecule test -s {SCENARIOS[1]}", calls)
                if "containers" in overrides:
                    self.assertIn("container-fixture", result.stdout)
                if "networks" in overrides:
                    self.assertIn("network-fixture", result.stdout)
                if overrides.get("pgrep_rc") == 0:
                    self.assertIn("98765", result.stdout)

    def test_invalid_credentials_rejected_before_discovery(self):
        identity = ["id -u", "id -ru", "getent passwd 1001", "id -un",
                    "id -g", "id -rg"]
        membership = identity + ["getent group libvirt", "id -G"]
        for overrides, expected in (
            ({"uid": "0"}, ["id -u"]),
            ({"uid": "1002"}, ["id -u"]),
            ({"real_uid": "0"}, ["id -u", "id -ru"]),
            ({"name": "other"}, identity[:4]),
            # Old sg primary GID fails even with valid libvirt membership.
            ({"gid": "980", "real_gid": "980"}, identity),
            ({"real_gid": "980"}, identity),
            ({"home": "/root"}, identity),
            ({"groups": "1001"}, membership),
            # A substring is not numeric supplementary membership.
            ({"groups": "1001 1980"}, membership),
        ):
            with self.subTest(overrides=overrides):
                result, calls = self.run_script(**overrides)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(calls, expected)
                self.assertIn("exit 1", result.stderr)

    def test_explicit_runtime_directory_preserved_without_creating_one(self):
        result, _ = self.run_script(xdg="/mock/existing runner runtime")
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
