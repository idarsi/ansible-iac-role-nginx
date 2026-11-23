# Testing

## Automated matrix

| Platform/image | Ansible or application versions | Molecule scenarios | Main coverage |
|---|---|---|---|
| Rocky Linux 9 UBI init (`docker.io/rockylinux/rockylinux:9-ubi-init`, `sleep infinity`, nonprivileged) | Shared `ansible-current` / `ansible-next` intent; runtime pending | `podman-blueprint-validation` (manual, optional managed) | Pure blueprint validation, exact rejection errors, package/path/sentinel preservation, default Molecule idempotence |
| Rocky Linux 9 (`quay.io/rockylinux/rockylinux:9`) | ansible-core 2.21.3; nginx stable | `podman-validation` | Validation and no-mutation contract |
| Rocky Linux 9 UBI init (`docker.io/rockylinux/rockylinux:9-ubi-init`) | ansible-core 2.21.3; nginx stable | `podman-guardrails`, `podman-lifecycle`, `podman-check-mode`, `podman-functional` | Ownership safety, all public transitions, check-mode safety, TLS/redirect behavior, repository defaults, and idempotence |
| Rocky Linux 9 and 10 UBI init (`docker.io/rockylinux/rockylinux:{9,10}-ubi-init`) | ansible-core 2.21.3; nginx stable | `podman-platform-matrix` | Baseline installation, `nginx -t`, enabled site, service behavior, and idempotence |
| Rocky Linux 10 KVM guest (shared test-environment Kickstart) | ansible-core 2.21.3; nginx stable; SELinux enforcing | `kvm-selinux` (manual) | Policy persistence, role-managed content label, HTTP access, and idempotence |

Rocky Linux 9 and 10 are automatically tested by the scheduled
`podman-platform-matrix` scenario. RHEL 9/10 are supported by the role but are not
automatically covered here.

## Scenario coverage

* `podman-blueprint-validation` accepts minimal, website and proxy blueprints in
  `state: "validate"` and rejects representative root/collection types, unsafe
  names, duplicate sites and unsafe directory paths with exact messages. Only
  `prepare` writes fixtures and the baseline. Converge and its default Molecule
  idempotence repeat perform validation only; verify compares installed RPMs,
  role-owned path metadata and sentinel checksum/permissions with that baseline.
  It requires no systemd, package installation, service startup or port exposure.
  It does not replace the broader legacy validation regressions or establish
  Nginx runtime/service coverage. New runtime acceptance is pending.

* `podman-validation` checks valid input, invalid site/TLS/repository paths, duplicate
  and reserved server-level locations, supported states, and validation-only preservation of the
  pre-existing package, service, and role-managed path state. It also rejects
  a string value for the `sites` collection and mapping values for all five
  public collections with actionable type errors. It also rejects relative,
  parent-traversal, and Nginx-injection values for all three managed
  directory variables before host mutation. It also rejects directory, file,
   and bind source/target traversal and unsafe paths in both validation and
   absent states, with exact failure messages and preservation of pre-existing
   state. It also renders a custom DNF repository section without contacting an
   external repository. Proxy tests verify access-rule ordering, quoted
   authentication realms, conditional CA-file preflight, and same-run managed
   CA files. Functional coverage validates separate HTTP and HTTPS proxy
   locations containing `auth_request` and `internal`, and runs `nginx -t` on
   the generated configuration. Check-mode fixtures include the public test CA and execute the production present and
  absent package dispatch paths using the hardcoded test-only `nginx-core`
  override. Both package operations run in check mode without installing or
  removing a package. The baseline
  fixture file written by the test harness is intentionally excluded.
  The scenario intentionally omits Molecule's idempotence phase: the
  check-mode package-present fixture correctly predicts a change on every run
  because `nginx-core` is never installed. Production idempotence is covered
  by the lifecycle and functional scenarios.
* `podman-guardrails` verifies uninstall confirmation, external repository/site and
  unrelated-file preservation, manifest ownership filtering, preservation of an
  unmanaged nested file below a manifest-owned directory after opt-in owned
  cleanup, and absent-state rejection of wrong markers and corrupt manifests
  without package or repository mutation.
* `podman-lifecycle` verifies public `present`, `absent`, `uninstall`, site/location
  present/absent, enable/disable, and service stopped/started transitions.
  It verifies that the `started` state preserves a service's disabled boot
  enablement. A test-only systemd drop-in replaces `ExecReload` with an atomic
  counting wrapper around the real `/usr/sbin/nginx -s reload` command. The
  scenario proves that a valid configuration change increments the direct
  reload count exactly once and replaces workers, while failed validation does
  not increment the count. An `always` cleanup restores the original unit.
  For repeated location removal it compares the rendered file content before
  and after the repeat. For repeated public absent and site absent it compares
  the observed package/path existence results. For repeated present it compares
  the managed site's SHA-256 checksum before and after convergence. These are
  observable idempotence checks; `verify.yml` does not assert a systematic
  Ansible `changed=0` result for the repeated role invocations.
* `podman-check-mode` first rejects a root-canonicalizing path in absent state even in check mode and
  asserts the `CANONICAL_PATH_PROTECTED_ROOT` error code and message. It then
  compares package presence, service state, and managed file
  existence, checksums, and modes before and after representative check+diff
  convergence. It separately compares the repository path and content; the
  repository is expected to remain absent because check mode does not preview
  that repository operation. Its file fixture passes fake secret-bearing
  content through the shared filesystem wrapper under `--diff`; the wrapper
  applies `no_log` and disables diffs for the entire shared include path.
  OpenSSL key generation and repository/package
  command behavior are not claimed as safely previewable, but the test proves
  that this limitation does not mutate the repository path.
* `podman-functional` manages a valid public self-signed test CA through the blueprint,
  renders it as an HTTPS upstream trust store in the same install run, runs
  `nginx -t`, checks HTTPS/GPG repository defaults and private
  key mode `0600`, and verifies local HTTP-to-HTTPS redirect plus an actual
  HTTPS reverse-proxy response from a test-only backend on `127.0.0.1:8081`.
* `podman-platform-matrix` repeats the baseline on Rocky Linux 9 and 10. Privileged
  systemd and the cgroup mount are test-only Podman settings.
* `kvm-selinux` is a manual full-VM scenario, not part of pull-request or
  scheduled CI. It fails immediately unless SELinux is enabled and enforcing,
  installs the guest's test-only `policycoreutils-python-utils` prerequisite
  (which provides `semanage` on Rocky Linux 10), installs a website with
  role-managed content explicitly assigned
  `httpd_sys_content_t`, checks the effective file context, requests that file
  through Nginx, and runs Molecule's idempotence phase. The guest is disposable;
  Molecule teardown removes it and all guest-local policy changes.

The validation and functional scenarios do not execute `restorecon` in their
non-SELinux/container environments. Production `restorecon` errors fail the
convergence. SELinux runtime assertions are covered only by the manual KVM
scenario; the suite does not infer restorecon coverage from
`virtualization_type` facts.

## Commands

CI parses the documentation inventory example with `ansible-inventory` and
syntax-checks the documentation playbook example with `ANSIBLE_ROLES_PATH=..`
so it resolves this checkout as the role.
These checks validate the examples without connecting to or changing a host.

CI installs the pinned `containers.podman` collection from the repository
root `requirements.yml` after installing the Python test tools. This collection
provides the `containers.podman.podman_login` and
`containers.podman.podman_network` modules used by Molecule's Podman plugin.
Version 1.20.2 supports the repository's pinned ansible-core 2.21.3 (and is
also available in the shared verification environment).

Use an existing pinned shared environment for local checks. Set the checkout
path for your installation; do not create a role-local venv or install/upgrade
shared Python dependencies. Initialize the documented `tasks/shared` submodule.
The current shared lane is Core 2.20.8, not the historical CI pin 2.21.3 above.
Report missing or incompatible tooling instead of changing the environment.

```bash
export IDARSI_TEST_ENVIRONMENT="/path/to/idarsi-ansible-test-environments"
source "$IDARSI_TEST_ENVIRONMENT/.venv/ansible-current/bin/activate"
ansible-playbook --syntax-check -i localhost, -c local molecule/podman-validation/converge.yml
ANSIBLE_ROLES_PATH=.. ansible-lint --profile production
molecule test -s podman-validation
molecule test -s podman-guardrails
molecule test -s podman-lifecycle
molecule test -s podman-check-mode
molecule test -s podman-functional
molecule test -s podman-platform-matrix
```

For the manual SELinux KVM scenario, prepare the shared environment's KVM
backend as documented by `idarsi-ansible-test-environments` (hardware
virtualization, `/dev/kvm`, libvirt access, and its Rocky 10 install source are
required), activate the shared Ansible environment, then run:

```bash
export IDARSI_TEST_ENVIRONMENT="/path/to/idarsi-ansible-test-environments"
source "$IDARSI_TEST_ENVIRONMENT/.venv/ansible-current/bin/activate"
export IDARSI_TEST_KVM_INSTALL_SOURCE_ROCKY10="<Rocky 10 ISO or install-tree path>"
molecule test -s kvm-selinux
```

Set `IDARSI_TEST_KVM_INSTALL_SOURCE_ROCKY10` to the local Rocky 10 ISO or
install-tree path selected/prepared as described in the shared environment's
`docs/kvm-molecule.md` and `install.sh` documentation. The scenario consumes
that value and the shared KVM create/destroy playbooks. It is excluded from CI because it requires
a full libvirt/KVM guest. Failed guest creation invokes shared cleanup; normal
Molecule teardown destroys the disposable guest.

When running Molecule in a clean environment, install the declared Ansible
collection before the scenarios:

```bash
ansible-galaxy collection install --requirements-file requirements.yml \
  --collections-path /path/to/resolved/context/collections
```

Pull requests run syntax, production-profile lint, validation, guardrails,
lifecycle, check-mode, and functional scenarios on Rocky Linux 9. The Rocky
Linux 9/10 platform matrix runs on the scheduled workflow and on any manual
`workflow_dispatch` (the workflow has no dispatch inputs). Check mode is
asserted only for Ansible-managed state; command-based key generation and
repository/package operations remain
documented limits.

The CI actions use immutable commit SHAs. Container images retain explicit
Rocky Linux version tags rather than registry digests: these images are
multi-architecture and the repository's scheduled platform matrix follows
the maintained Rocky 9/10 image tags. Updating a digest on every image
refresh would make the matrix stale without providing a durable platform
contract; image tags and scenario results are therefore the maintained
boundary.

## Optional managed execution and standalone lifecycle

Root `role-test.json` covers all eight scenarios and all three controller lanes.
Only `podman-blueprint-validation` declares `execution.backend: "podman"`.
The five privileged/systemd Podman scenarios remain exclusive legacy tests,
as do `kvm-selinux` and `podman-validation`. The latter has a custom sequence
without idempotence and broader package/check-mode fixtures; it is not relabeled
as managed. Current and next entries declare test intent, not passing evidence;
next is a forward-compatibility probe. The minimum lane is outside this
integration's scope, not known incompatible or a new role minimum. Target OS
support is unchanged. Avoid branch-bulk selection when only managed work is wanted.

Use the shared helper from
[`cc777691026cf300089b8d53760555987c62ce7f`](https://github.com/idarsi/idarsi-ansible-test-environments/tree/cc777691026cf300089b8d53760555987c62ce7f)
or a separately reviewed compatible revision supporting
`idarsi.scenario-context/v1` and both `direct` and `supervised` lifecycle modes.
The immutable committed example and managed playbooks at that revision are the
integration baseline, not unrelated uncommitted helper recovery work.
See its [isolated-runs contract](https://github.com/idarsi/idarsi-ansible-test-environments/blob/cc777691026cf300089b8d53760555987c62ce7f/docs/isolated-test-runs.md)
and the optional TUI checkout's `MANAGED_ROLE_GUIDE.md` and `METADATA.md`.
Local execution against a dirty helper checkout must be recorded as dirty-helper
evidence, never acceptance of the pristine pinned revision.

The image supplies Python; it runs `sleep infinity`, not systemd. Shared helpers
require Linux procfs, flock, pidfds, `ip`, local **rootless Podman and successful
local `qemu:///system` libvirt discovery**, even for this Podman-only scenario.
No privileged containers, host mounts/namespaces, extra capabilities or published
ports are requested. Missing prerequisites block execution; this integration
does not authorize host installation, privilege changes or service reconfiguration.
Role-specific collections belong in `requirements.yml`, not the shared venv.
For dependency bootstrap, use `scenario-context resolve`'s
`collections_directory`, preserving the scenario's exact safe-files glob.

From the role root, after activating the shared environment as above:

```bash
"$IDARSI_TEST_ENVIRONMENT/scripts/scenario-context" capabilities \
  --backend podman --scenario podman-blueprint-validation --role "$PWD"
"$IDARSI_TEST_ENVIRONMENT/scripts/scenario-context" resolve \
  --backend podman --scenario podman-blueprint-validation --role "$PWD"
molecule test -s podman-blueprint-validation
```

Direct Molecule remains independent of the TUI or supervisor. To retain a
container and execute phases separately (including the prepare-only fixtures):

```bash
molecule create -s podman-blueprint-validation &&
molecule prepare -s podman-blueprint-validation &&
molecule converge -s podman-blueprint-validation &&
molecule idempotence -s podman-blueprint-validation &&
molecule verify -s podman-blueprint-validation &&
molecule destroy -s podman-blueprint-validation
```

Direct same-context concurrency is unsupported. The shared helper owns direct
identities and optional supervised UUID/ephemeral/collections isolation.
Invalid or partial `IDARSI_RUN_ID`/`IDARSI_HANDOFF*` context must fail closed
before mutation, never fall back to direct. Do not manufacture handoff values.

Use the existing TUI environment and suffix selector `--role nginx`, not the
repository name. Planning is read-only and not backend readiness evidence:

```bash
export ROLES_DIR="/path/to/roles"
idarsi-tests-run list --role nginx --roles-dir "$ROLES_DIR" \
  --environment-repository "$IDARSI_TEST_ENVIRONMENT"
idarsi-tests-run plan --role nginx --roles-dir "$ROLES_DIR" \
  --environment-repository "$IDARSI_TEST_ENVIRONMENT" \
  --cell podman-blueprint-validation whole_scenario 'whole scenario' ansible-current
idarsi-tests-run run --role nginx --roles-dir "$ROLES_DIR" \
  --environment-repository "$IDARSI_TEST_ENVIRONMENT" \
  --cell podman-blueprint-validation whole_scenario 'whole scenario' ansible-current \
  --expect-sha FULL_APPROVED_COMMIT_SHA --yes
```

Replace the SHA with the exact committed ref approved by plan; add `--branch`
consistently for another local branch. GUI execution requires explicitly
selecting that cell, previewing and confirming it; preview is not execution
evidence. Record actual worker output, tested SHA/dirty qualification, helper
revision, controller lane, origin (`cli` versus `tui_gui`) and authoritative
cleanup separately. Only original-context `test-run inspect UUID` reporting
`cleaned` proves cleanup, not worker exit or a missing guest name. Follow the
shared recovery contract on uncertainty; never purge journals/resources or
force-unlock retained admission.

No new managed scenario is added to CI: the existing workflow does not provision
or pin both shared discovery prerequisites. Developer parse/contract/syntax
checks are not direct, retained-phase, supervised CLI, actual GUI, next-lane,
invalid-handoff, concurrency, interruption or cleanup runtime acceptance.
Those checks remain tester/operator responsibilities; all new runtime results
are **pending**, not passes.

### Tester preflight evidence

The tester checked `update/optional-managed-molecule` at base
`50483665786006730a75993c44003d65cada965a` with dirty, uncommitted role changes,
helper `cc777691026cf300089b8d53760555987c62ce7f` with tracked/untracked recovery
changes, and clean TUI `1bbd987759ceeb779db85ee2dde1588756eaa119`.
This is not pristine pinned-helper acceptance.

From the role root with the existing shared `ansible-current` environment
activated, these read-only checks exited **0**:

```bash
"$IDARSI_TEST_ENVIRONMENT/scripts/scenario-context" capabilities \
  --backend podman --scenario podman-blueprint-validation --role "$PWD"
"$IDARSI_TEST_ENVIRONMENT/scripts/scenario-context" resolve \
  --backend podman --scenario podman-blueprint-validation --role "$PWD"
PYTHONPATH="$IDARSI_TEST_ENVIRONMENT/scripts" python -B -c \
  'from isolated_runs.discovery import discover; networks=discover(); print("PASS:",len(networks))'
```

Capabilities/resolve reported direct and supervised modes with
`generation: null`; strict backend discovery returned 44 prefixes. In the existing TUI
environment, from its checkout, the first two commands below exited **0** and selected
the intended whole-scenario current cell. Planning reported
`runtime_preflight_completed: false`.

```bash
python -m automation_cli list --role nginx --roles-dir "$ROLES_DIR" \
  --environment-repository "$IDARSI_TEST_ENVIRONMENT"
python -m automation_cli plan --role nginx --roles-dir "$ROLES_DIR" \
  --environment-repository "$IDARSI_TEST_ENVIRONMENT" \
  --cell podman-blueprint-validation whole_scenario 'whole scenario' ansible-current
python -m automation_cli admission inspect --json
```

The last command exited **3**, reporting `blocked: true` and
`Admission busy or unsafe/missing state`. Unrelated generations were
running/cleaning/cleanup_failed. No bypass or allocation was attempted; final
scenario-context inspection still reported `generation: null`. Direct and
retained lifecycle, idempotence, invalid-handoff rejection, supervised CLI,
actual GUI and next-lane acceptance remain **blocked/unproven**, not role-test
failures. No new generation was created and no cleanup was performed or claimed
for unrelated resources.
