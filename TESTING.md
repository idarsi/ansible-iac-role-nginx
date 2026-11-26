# Testing

## Focused PID-label regression update

Campaign 342 at clean role `e7476e6` and helper `491320f` reached the
notified validation handler but failed with `Using a block as a handler is not
supported` (retained cells 2933–2943; worker exit 4, cleanup `cleaned`). The
working-tree follow-up flattens both blocks in the shared validation include;
each SELinux/existing-file gate remains on the applicable individual task.
The earlier PID probe/repair succeeded before this handler-expansion failure.
This is a handler-graph defect, not evidence that the PID repair failed.

The working-tree fix after `ada402d` shares configuration validation between
explicit `started` and the notified handler. After successful `nginx -t`, only
an existing regular, non-symlink, single-link `/run/nginx.pid` is eligible for
active-policy `restorecon -v` on SELinux-enabled targets. Check mode skips
`nginx -t` and uses `restorecon -n -v`; absent files are not created. No PID
content, owner or mode changes, recursive `/run` relabel, permissive policy,
allow module or proxy-boolean changes are part of this fix. Unsafe objects are
rejected before configuration testing and checked again before relabeling.
These fixed-path guards trust root-owned `/run`; they do not provide atomic
protection against concurrent privileged replacement.

The safe policy probe always runs with `-n -v`, and the separate mutating
command inherits effective Ansible check mode rather than consulting the
CLI-only `ansible_check_mode` variable. This preserves nonmutation for CLI,
play, block and task previews, while the probe reports predicted repairs.
The guest regression explicitly checks task- and block-inherited previews with
CLI check mode off against the intentionally mislabeled fixture. Only exact
`Would relabel /run/nginx.pid from ... to ...` and
`Relabeled /run/nginx.pid from ... to ...` lines count as predicted/actual
repairs. Informational administrator-customization messages do not report
changes and do not trigger a forced policy override.

Cheap source/mock verification, from the existing approved controller
environment, requires no guest, backend, collection installation or additional
Python dependency:

```bash
python -B -W error::DeprecationWarning -m unittest discover \
  -s tests -p test_nginx_pid_validation.py -v
```

This loads the actual task YAML, checks Ansible's inherited check-mode
attributes and runs the native command module with its execution boundary
mocked. Fixtures cover CLI/play/block/task previews (including CLI false),
normal-mode execution eligibility, exact changed-message recognition and an
administrator-customized informational message with zero change. It does not
prove effective guest policy, real restorecon output, service behavior or
full role/handler runtime acceptance.

The same command also runs the native Ansible playbook CLI engine in disposable
fixtures using copied production handlers and shared validation/guard tasks.
It actually notifies and flushes the handler graph, covering running/stopped
reload gating, direct pre-start shared validation, failed validation without
reload, CLI check mode, disabled SELinux, absent PID and unsafe PID objects.
A negative control reinstates nested blocks and must fail with the original
handler-expansion error. An allowlisted action-loader interception mocks
command/stat/service facts/systemd; facts and results are synthetic,
`gather_facts` is false, and a fail-closed connection plugin forbids command,
upload, download and connection operations. Nothing calls host service,
filesystem-stat modules, commands, guests or backends. This is mock/source-only
evidence on current/next controllers, not a Molecule or service runtime pass.

The existing enforcing `kvm-rocky9-lifecycle` and `kvm-rocky10-selinux` verifiers
reuse `tasks/pid_label_regression.yml` from the lifecycle scenario. Intended
assertions cover unsafe symlink rejection/target preservation, absent-PID fresh
start, stopped-handler validation without service start, intentionally
mislabeled stopped-PID repair through the handler, dry-run prediction without
mutation, repeated start/reconciliation, and live PID/master preservation
across configuration testing and notified reload. `matchpathcon -V` checks the
active policy without assuming a type. The existing instrumented lifecycle
reload test additionally checks exact live PID contents, retaining its worker
replacement/exactly-one-reload and invalid-configuration rejection assertions.
Guest-only fixtures use distribution policy tools; no new scenario, controller
dependency, shared pin or production policy exception is introduced.

**Runtime acceptance remains pending.** Developer checks are restricted to
targeted source/lint/syntax checks; no Molecule/TUI campaign, backend discovery,
guest connection or service probe was authorized. Campaign 341 at clean role
`ada402d` and helper `491320f` reported PID-open EACCES/systemd protocol failure
in current and next lanes, but the effective label and AVC were not observed.
Do not treat this defensive fix as a proven incident diagnosis or transfer
historical passes to it. Maturity remains Beta / 66%; see the assessment.

## Current matrix and acceptance boundary

All eight scenarios declare optional managed **whole-scenario** execution and
remain callable directly with Molecule, without the TUI. This migration is
source-reviewed only. **No tests or runtime/backend probes were run at the
user's request while other TUI runs were active.** Every renamed/migrated
scenario's direct, retained-phase, supervised CLI, actual GUI, idempotence,
invalid-handoff, concurrency, interruption and cleanup acceptance is pending.
Metadata is test intent, not runtime proof.

| Platform/image | Ansible or application versions | Molecule scenarios | Main coverage |
| --- | --- | --- | --- |
| Rocky 9 UBI init, `docker.io/rockylinux/rockylinux:9-ubi-init` | Shared current Core 2.20.8 / next Core 2.21.3 intent; CI Core 2.21.3 | Both `podman-rocky9-*` scenarios | Pull-request/scheduled/manual CI validation configured; migration runtime pending |
| Rocky 9 KVM installer guest | Shared current/next intent; nginx stable | Guardrails, lifecycle, check-mode, functional | Manual full-host coverage; run before release when an approved KVM host is available; runtime pending |
| Rocky 9 and 10 KVM installer guests | Shared current/next intent; nginx stable | `kvm-rocky9-rocky10-platform-matrix` | Manual full matrix before release; scheduled KVM automation pending |
| Rocky 10 KVM installer guest, SELinux enforcing | Shared current/next intent; nginx stable | `kvm-rocky10-selinux` | Manual enforcing coverage before release; runtime pending |

| Scenario | Backend / target | Literal platform names | Coverage intent |
| --- | --- | --- | --- |
| `podman-rocky9-blueprint-validation` | Nonprivileged Podman / Rocky 9 UBI init | `nginx-blueprint-validation-rocky9` | Pure validation, exact rejection errors, RPM/path/sentinel nonmutation |
| `podman-rocky9-validation` | Nonprivileged Podman / Rocky 9 UBI init | `nginx-validation-rocky9` | Broader validation, package overrides in check mode, path/security/logging regressions |
| `kvm-rocky9-guardrails` | KVM / Rocky 9 | `nginx-guardrails-rocky9` | Confirmation, ownership filtering, external-file preservation, corrupt-manifest/wrong-marker rejection |
| `kvm-rocky9-lifecycle` | KVM / Rocky 9 | `nginx-lifecycle-rocky9` | Public transitions, handler reload count, service enablement, observable repeat convergence |
| `kvm-rocky9-check-mode` | KVM / Rocky 9 | `nginx-check-mode-rocky9` | Check+diff package/service/file/repository nonmutation and secret handling |
| `kvm-rocky9-functional` | KVM / Rocky 9 | `nginx-functional-rocky9` | TLS/redirect, local reverse proxy, managed CA, repository defaults and key modes |
| `kvm-rocky9-rocky10-platform-matrix` | KVM / Rocky 9 **and** 10 | `nginx-platform-matrix-rocky9`, `nginx-platform-matrix-rocky10` | Installation, `nginx -t`, enabled site, service behavior and idempotence on both OS versions |
| `kvm-rocky10-selinux` | KVM / Rocky 10 enforcing | `nginx-selinux-kvm-rocky10` | Policy persistence, role-managed content label, HTTP content access and idempotence |

The platform matrix is one whole scenario with both platforms, not two
independent managed selections. Other scenarios each have one guest. RHEL 9/10
remain supported by the role but lack automatic coverage here. Target support
and public blueprint/state contracts are unchanged.

Root `role-test.json` covers exactly these scenarios and all three controller
lanes. Current and next include every literal platform; next is forward-
compatibility intent, not a pass or blocking-policy claim. The minimum lane
remains explicitly outside this integration's assessed scope, not known
incompatible and not a newly imposed role minimum.

## Preserved assertions and idempotence

* Blueprint validation writes fixtures/baselines only in `prepare`. Stable
  convergence validates minimal, website and proxy blueprints; verification
  compares RPMs, role-path metadata and sentinel checksum/permissions. It
  requires no systemd, package installation, service startup or published ports.
* Broader validation preserves all original type/path/site/TLS/repository,
  proxy access-order/auth/CA, cron, source-code logging and handler assertions.
  `converge` now validates a stable blueprint on every invocation. Its original
  regression playbook runs from `verify`, followed by the original package,
  service and filesystem nonmutation assertions. The absent `nginx-core`
  fixture still predicts a change in check mode; it is not installed merely to
  hide that change. The custom repository rendering does not contact a repository.
* Guardrails likewise converge a validation baseline on every invocation;
  verification runs the complete destructive regression playbook and persisted
  result assertions. It preserves external repository/site/unrelated nested
  files and tests wrong markers/corrupt manifests. The existing fixture does
  **not** set `nginx_uninstall_remove_config: true`; it does not establish
  opt-in configuration-cleanup acceptance (see the maturity assessment).
* Lifecycle now converges its actual stable installation on every invocation.
  Handler/service transition regressions moved to verification, before the
  existing public transition assertions. The test-only atomic reload counter
  still proves exactly one reload/worker replacement for valid configuration
  and none for invalid configuration; `always` restores the original unit.
  Repeated removal/present checks still compare observed files/packages/checksums;
  those verifier assertions are not a systematic `changed=0` claim.
* Check-mode and functional keep the original assertions. Check-mode uses the
  renamed functional scenario's public CA fixture; validation reads the renamed
  lifecycle handler fixture. Secret-bearing fixtures retain `no_log`/diff
  safeguards. Command-based key generation and repository/package operations
  retain their documented check-mode limits.
* Full-host cases no longer request privileged containers or host cgroup mounts.
  KVM guest plays use `become: true` for the nonroot `molecule` SSH account.
  The SELinux scenario retains its enforcing precondition,
  `policycoreutils-python-utils` prerequisite, effective file-label and HTTP
  assertions. Production `restorecon` failures remain failures.

Every scenario uses Molecule's default sequence, including idempotence; the
shared helper rejects custom `scenario.test_sequence`. No new `changed_when`
suppression or assertion weakening is used to pass idempotence.

## Prerequisites and pins

Use an existing approved shared controller environment; do not create a
role-local venv or install/upgrade shared dependencies. Initialize `tasks/shared`
with the documented recursive submodule checkout.

The helper integration baseline is immutable revision
[`cc777691026cf300089b8d53760555987c62ce7f`](https://github.com/idarsi/idarsi-ansible-test-environments/tree/cc777691026cf300089b8d53760555987c62ce7f),
supporting `idarsi.scenario-context/v1` and `direct` plus `supervised` lifecycle
modes. A separately reviewed compatible revision is possible; record its exact
SHA and dirty qualification. Do not relabel dirty-helper results as acceptance
of the pristine pin. See its
[isolated-run contract](https://github.com/idarsi/idarsi-ansible-test-environments/blob/cc777691026cf300089b8d53760555987c62ce7f/docs/isolated-test-runs.md),
and the optional TUI's `MANAGED_ROLE_GUIDE.md` and `METADATA.md`.

The repository's unchanged `requirements.txt` pins Core 2.21.3, ansible-lint
26.8.0, Molecule 26.8.0 and molecule-plugins[podman] 26.7.15.
The shared `ansible-current` pin is Core 2.20.8; the role's Core pin instead
matches the shared next lane. These are different controller contracts; do not
upgrade shared current or claim current/next acceptance from the file alone.
`requirements.yml` pins `containers.podman` 1.20.2, `ansible.posix` 2.2.2
(`seboolean`) and `community.general` 11.4.0 (`seport`). Keep collections private
to the resolved context, not in the shared Python environment; preserve existing
dependency-install locking. No collections were installed for this source review.

The helper requires Linux procfs, flock, pidfds, `ip`, local **rootless Podman
and successful local `qemu:///system` libvirt discovery**, even for Podman-only
execution. Both discovery commands must succeed; permission failures are not
empty inventories. Remote/rootful Podman is unsupported. The two Podman
scenarios use `docker.io/rockylinux/rockylinux:9-ubi-init` with Python and
`sleep infinity`, no privileged options, host mounts/namespaces, added
capabilities or published ports.

KVM needs authorized hardware virtualization, `/dev/kvm`, libvirt service/socket,
storage/network permissions and explicit installation sources. The reviewed
shared host setup targets Rocky 10 / Fedora 43/44, not hosted Ubuntu KVM.
All KVM configurations preserve installer provisioning:

* Rocky 9: `IDARSI_TEST_KVM_INSTALL_SOURCE`.
* Rocky 10: `IDARSI_TEST_KVM_INSTALL_SOURCE_ROCKY10`.
* Both: `${IDARSI_TEST_ENVIRONMENT}/examples/molecule-kvm/rocky9-10.ks.tmpl`.

Set sources to operator-prepared ISO/install-tree values as documented by the
pinned helper's `docs/kvm-molecule.md`. Kickstart provides the `molecule` user
with passwordless sudo, enforcing SELinux and a firewall allowing SSH.
Loopback HTTP checks require no firewall exemption. Do not disable SELinux or
the firewall to make the migration pass.

The functional and lifecycle scenarios have privileged guest-only `prepare.yml`
plays, separate from measured convergence/idempotence and check-mode assertions.
They require enforcing SELinux and install `selinux-policy-targeted`,
`policycoreutils-python-utils`, `python3-libselinux` and `python3-libsemanage`
from the disposable guest's official Rocky repositories. Functional preparation
uses `ansible.posix.seboolean` to persist `httpd_can_network_connect: true`
for loopback port 8081 and HTTPS upstreams, then independently ensures its active
state (including active-state drift when persistent policy was already correct).
Lifecycle preparation uses `community.general.seport` to persist/load TCP 8080
as `http_port_t`, modifying an existing alternate mapping rather than failing on
a blind add. That module is idempotent when the mapping is already correct.
The lifecycle transition playbook imports the same preparation before any role
invocation, so standalone transitions get consistent prerequisites as well.
These deliberate fixture-only policy changes do not change enforcement, the
firewall, production role defaults or blueprint. Their runtime acceptance,
including preparation rerun behavior, remains pending; source review is not
evidence of a guest policy or service pass.

Managed KVM never lazily builds shared base images. An operator-reviewed
alternative is exactly one existing `image_path` with the compatible SSH user,
instead of (not alongside) `install_source` + `kickstart`. Current role
configurations choose installers; merely exporting an image variable does not
override them. Missing prerequisites block execution; this task authorizes no
host installs, service reconfiguration or privilege changes.

## Direct commands (tester/operator only)

These are documented execution instructions, **not commands run for this
migration**. Use portable checkout paths and activate the approved lane:

```bash
export IDARSI_TEST_ENVIRONMENT="/path/to/idarsi-ansible-test-environments"
source "$IDARSI_TEST_ENVIRONMENT/.venv/ansible-current/bin/activate"
export IDARSI_TEST_KVM_INSTALL_SOURCE="/path/to/Rocky-9.iso"
export IDARSI_TEST_KVM_INSTALL_SOURCE_ROCKY10="/path/to/Rocky-10.iso"
scenario="podman-rocky9-blueprint-validation"
backend="podman" # use kvm for the six KVM scenarios
"$IDARSI_TEST_ENVIRONMENT/scripts/scenario-context" capabilities \
  --backend "$backend" --scenario "$scenario" --role "$PWD"
"$IDARSI_TEST_ENVIRONMENT/scripts/scenario-context" resolve \
  --backend "$backend" --scenario "$scenario" --role "$PWD"
```

Install the declared collections into the returned `collections_directory`
before running each context; do not guess a cache path or allocate a generation
merely to bootstrap dependencies:

```bash
ansible-galaxy collection install --requirements-file requirements.yml \
  --collections-path /path/to/resolved/context/collections
molecule test -s "$scenario"
```

Repeat the exact scenario selection for all eight IDs in the table when full
coverage is authorized. Separate retained phases are supported:

```bash
molecule create -s "$scenario" &&
molecule prepare -s "$scenario" &&
molecule converge -s "$scenario" &&
molecule idempotence -s "$scenario" &&
molecule verify -s "$scenario" &&
molecule destroy -s "$scenario"
```

`prepare` writes fixtures only where a role-owned prepare playbook exists.
Direct same-context concurrency is unsupported. The helper owns direct
identities and supervised UUID/ephemeral/collections separation. All scenarios
preserve exact `driver.safe_files`:
`${MOLECULE_EPHEMERAL_DIRECTORY}/collections/*`.
Invalid/partial `IDARSI_RUN_ID`/`IDARSI_HANDOFF*` must fail closed before mutation,
never silently fall back to direct. Do not manufacture handoff values.

## Optional TUI and supervision

Use the existing TUI environment; `--role nginx` selects the suffix, not the
repository name. For example:

```bash
export ROLES_DIR="/path/to/roles"
idarsi-tests-run list --role nginx --roles-dir "$ROLES_DIR" \
  --environment-repository "$IDARSI_TEST_ENVIRONMENT"
idarsi-tests-run plan --role nginx --roles-dir "$ROLES_DIR" \
  --environment-repository "$IDARSI_TEST_ENVIRONMENT" \
  --cell podman-rocky9-blueprint-validation whole_scenario 'whole scenario' ansible-current
idarsi-tests-run run --role nginx --roles-dir "$ROLES_DIR" \
  --environment-repository "$IDARSI_TEST_ENVIRONMENT" \
  --cell podman-rocky9-blueprint-validation whole_scenario 'whole scenario' ansible-current \
  --expect-sha FULL_APPROVED_COMMIT_SHA --yes
```

Add `--branch` consistently for another local branch. Select any of the eight
scenario IDs with the same whole-scenario target and declared lane; managed
selection never passes `--platform-name`, including for the two-guest matrix.
Native supervision is also optional:

```bash
"$IDARSI_TEST_ENVIRONMENT/scripts/test-run" run \
  --backend "$backend" --scenario "$scenario" "$PWD"
```

GUI execution requires selecting the intended cells, previewing and confirming.
Planning/preview is not backend readiness or execution evidence. Record worker
output, producing SHA/dirty state, helper SHA/dirty state, lane, origin (`cli`
versus `tui_gui`) and cleanup separately. Only original-context authoritative
`test-run inspect UUID` reporting `cleaned` proves cleanup, not worker exit or
a missing guest name. Never purge resources/journals or force-unlock retained
admission; follow the shared recovery contract.

## CI intent and pending full-host coverage

The configured workflow retains inventory/example parsing, syntax and production
lint and pins the reviewed helper. It arranges both discovery prerequisites on
its disposable Ubuntu runner and runs the two nonprivileged managed Podman
scenarios as the unprivileged runner. Collections are installed into resolved
per-context directories. Host setup in this workflow is not authorization to
modify a developer's host. This configuration has **not** been executed or
accepted as a GitHub CI pass for the migration.

The previous privileged Podman service jobs and scheduled platform-matrix job
cannot simply become hosted Ubuntu KVM jobs. Guardrails, lifecycle, check-mode,
functional, Rocky 9/10 matrix and SELinux now require manual execution on a
provisioned supported KVM host, with both installer bindings for the matrix.
The scheduled/manual workflow still runs static and Podman validation, but
does not claim full-host coverage. Restoring automated KVM coverage requires
an approved appropriately isolated runner; no software-emulation fallback or
invented scheduled KVM pass is configured.

## Historical evidence (original IDs, not migration acceptance)

Pre-migration baseline: `c2f1c3543eff2dca0c27785403de29791d7f4c86`.
The historical CI run
[`44898161095`](https://github.com/idarsi/ansible-iac-role-nginx/actions/runs/44898161095)
at `50483665786006730a75993c44003d65cada965a` on 2026-11-21 passed static checks
and the six original Podman scenarios: `podman-validation`,
`podman-guardrails`, `podman-lifecycle`, `podman-check-mode`,
`podman-functional`, `podman-platform-matrix`. The latter included Rocky 9/10.
`kvm-selinux` was manual; `podman-blueprint-validation` had no runtime pass.
These original IDs/SHA remain historical and do not transfer to the new names
or backends. See [maturity assessment](docs/maturity-assessment.md); Beta / 66%
is retained with no score increase without runtime evidence.

An earlier tester preflight used branch `update/optional-managed-molecule`,
base `50483665786006730a75993c44003d65cada965a` with dirty role changes, dirty
helper `cc777691026cf300089b8d53760555987c62ce7f` (tracked/untracked recovery
changes), and clean TUI `1bbd987759ceeb779db85ee2dde1588756eaa119`.
It was not pristine pinned-helper acceptance. From the role root in the existing
shared current environment these commands exited 0:

```bash
"$IDARSI_TEST_ENVIRONMENT/scripts/scenario-context" capabilities \
  --backend podman --scenario podman-blueprint-validation --role "$PWD"
"$IDARSI_TEST_ENVIRONMENT/scripts/scenario-context" resolve \
  --backend podman --scenario podman-blueprint-validation --role "$PWD"
PYTHONPATH="$IDARSI_TEST_ENVIRONMENT/scripts" python -B -c \
  'from isolated_runs.discovery import discover; networks=discover(); print("PASS:",len(networks))'
```

They reported direct/supervised modes, `generation: null`, and 44 prefixes.
From the existing TUI environment, list/plan exited 0 for the original current
whole-scenario cell, with `runtime_preflight_completed: false`:

```bash
python -m automation_cli list --role nginx --roles-dir "$ROLES_DIR" \
  --environment-repository "$IDARSI_TEST_ENVIRONMENT"
python -m automation_cli plan --role nginx --roles-dir "$ROLES_DIR" \
  --environment-repository "$IDARSI_TEST_ENVIRONMENT" \
  --cell podman-blueprint-validation whole_scenario 'whole scenario' ansible-current
python -m automation_cli admission inspect --json
```

The final command exited 3 (`blocked: true`, `Admission busy or unsafe/missing
state`). Unrelated generations were running/cleaning/cleanup_failed; no bypass,
allocation or cleanup was attempted or claimed. Final inspection remained
`generation: null`. That preflight did not establish lifecycle, idempotence,
supervised CLI, actual GUI, next-lane or cleanup acceptance. None of those
historical commands were repeated for this migration.
