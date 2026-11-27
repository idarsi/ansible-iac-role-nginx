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
STEPS = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())["jobs"][
    "checks"
]["steps"]
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
if name == "sg":
    assert not inside
    assert args == ["libvirt", "-c", "bash -Eeuo pipefail"], args
    os.environ["MOCK_INSIDE"] = "yes"
    sys.exit(subprocess.run(["/bin/bash", "-Eeuo", "pipefail"]).returncode)
assert inside, f"{name} called outside credential wrapper"
event = name + " " + " ".join(args)
with open(os.environ["MOCK_LOG"], "a") as stream:
    stream.write(json.dumps(event) + "\n")
if len(Path(os.environ["MOCK_LOG"]).read_text().splitlines()) == int(
    os.environ["MOCK_FAIL_AT"]
):
    sys.exit(37)
if name == "id":
    assert args in ([], ["-u"], ["-g"]), args
    print(os.environ["MOCK_UID"] if args == ["-u"]
          else os.environ["MOCK_GID"] if args == ["-g"]
          else "uid=1001(runner) gid=108(libvirt)")
elif name == "getent":
    assert args == ["group", "libvirt"], args
    print("libvirt:x:108:runner")
elif name == "podman":
    assert args in (["--remote=false", "info"],
                    ["--remote=false", "network", "ls", "--format", "json"]), args
    print("[]" if "network" in args else "mock rootless info")
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
        self, failure: int = 0, uid: str = "1001", gid: str = "108"
    ) -> tuple[subprocess.CompletedProcess, list]:
        """Run only the extracted managed step with an isolated fake PATH."""
        with tempfile.TemporaryDirectory(prefix="nginx-ci-mock-") as directory:
            base = Path(directory)
            (base / "bash").symlink_to("/bin/bash")
            (base / "scripts").mkdir()
            for name in (
                "sg", "id", "getent", "podman", "virsh", "scenario-context",
                "python", "ansible-galaxy", "molecule",
            ):
                executable = base / name
                executable.write_text(f"#!{sys.executable}\n{MOCK}")
                executable.chmod(0o700)
            (base / "scripts/scenario-context").symlink_to(base / "scenario-context")
            log = base / "calls.jsonl"
            log.touch()
            result = subprocess.run(
                ["/bin/bash", "-Eeuo", "pipefail", "-c", SCRIPT],
                cwd=ROOT,
                env={
                    "PATH": directory,
                    "IDARSI_TEST_ENVIRONMENT": directory,
                    "MOCK_LOG": str(log),
                    "MOCK_FAIL_AT": str(failure),
                    "MOCK_UID": uid,
                    "MOCK_GID": gid,
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
                    line.strip().startswith(("podman ", "virsh ", "sg ")), line
                )

    def test_success_and_fail_fast_at_each_boundary(self):
        result, calls = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = ["id -u", "getent group libvirt", "id -g", "id ",
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

    def test_root_and_wrong_primary_group_rejected_before_discovery(self):
        for uid, gid, expected in (
            ("0", "108", ["id -u"]),
            ("1001", "1001", ["id -u", "getent group libvirt", "id -g"]),
        ):
            with self.subTest(uid=uid, gid=gid):
                result, calls = self.run_script(uid=uid, gid=gid)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(calls, expected)
                self.assertIn("exit 1", result.stderr)


if __name__ == "__main__":
    unittest.main()
