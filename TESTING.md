# Testing

## Focused PID-label regression update

Campaign 345 at clean role `6075aa3` and clean helper `491320f` reached
`kvm-rocky10-selinux` verification in current/next, exiting 2 with cleanup
`cleaned`. The explicit stopped-service assertion and `matchpathcon -V` passed.
After task/block preview passed, the real handler flush skipped `nginx -t`
and actual restorecon, although the safe probe predicted a change; the
`nginx_pid_relabel.changed` assertion then failed. Diagnostics were enabled,
but `items: []` supplies neither PID/AVC evidence nor proof of service success.

Native-engine reproduction confirms that preview `include_role` invocations
re-register the role's handlers with inherited check mode in the same play.
The later real notification therefore selects preview handlers. The fixture
now directly includes the unchanged production validation task file for all
previews, retaining task/block inheritance without replacing handlers. Normal
role inclusions, real notification/flush order, changed assertions,
`matchpathcon`, PID metadata and live-master assertions are unchanged. Both
Rocky 9 lifecycle and Rocky 10 SELinux reuse this corrected fixture.

The host-free regression exercises normal role-handler registration, actual
fixture task preview, block preview, real notification/flush and a repeat.
Synthetic PID context remains incorrect during both previews, changes only
during real repair, and stays correct with no second predicted repair.
A negative control retains the original preview role inclusions and requires
the observed real-handler check flags (true/false/true for nginx/probe/repair)
and changed-assertion failure. Both controls pass on current/next. This is
native-engine/mock evidence only; corrected guest acceptance remains pending.
Production tasks and effective check-mode inheritance are unchanged.

Campaign 344 at clean role `cae9ff20770bf9ba0923432a5131f0f7ee24aa6d`
reached `kvm-rocky10-selinux` verification in both current/next lanes after
converge and idempotence passed. Both workers exited 2, with cleanup `cleaned`.
The stopped-PID fixture failed its literal `service_facts` state `stopped`
assertion after explicit stop and successful notified validation/relabel;
reload was skipped. The actual service state was not printed. Upstream
service-facts unit-file fallback can expose raw `inactive` rather than the
listed-unit normalized `stopped`; this is a likely fixture portability defect,
not a proven guest state or new production PID defect. The earlier unsafe-PID
failure was expected and rescued.

The working-tree correction reads only `systemctl show` ActiveState/SubState
using fixed argv and requires exactly `inactive`/`dead`, independent of property
order. Missing, duplicate or malformed properties fail with actual properties
and PID metadata. The empty regular, non-symlink PID assertion and later label,
preview, repair and live-master checks remain. Native-engine mocks exercise
both service-facts spellings and reject running/failed/activating states and
invalid properties without executing systemctl. Production tasks are unchanged.
This correction has no guest acceptance yet; campaign 344 is not a runtime
pass of the corrected working tree.

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
| `podman-rocky9-validation` | Nonprivileged Podman / Rocky 9 UBI init | `nginx-validation-rocky9` | Broader validation and path/security/logging regressions; package bindings covered by native mocked CI |
| `kvm-rocky9-guardrails` | KVM / Rocky 9 | `nginx-guardrails-rocky9` | Confirmation, ownership filtering, external-file preservation, corrupt-manifest/wrong-marker rejection |
| `kvm-rocky9-lifecycle` | KVM / Rocky 9 | `nginx-lifecycle-rocky9` | Public transitions, handler reload count, service enablement, observable repeat convergence |
| `kvm-rocky9-check-mode` | KVM / Rocky 9 | `nginx-check-mode-rocky9` | Real package-override solver checks in prepare, then check+diff package/service/file/repository nonmutation and secret handling |
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
  service and filesystem nonmutation assertions. Real DNF package-override
  checks now belong to KVM preparation; hosted CI retains native-engine argument
  and control-flow checks with DNF alone mocked. The custom repository rendering
  does not contact a repository.
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
  Check-mode's new `prepare.yml` runs the unchanged package-override fixture and
  all its original baseline/result/nonmutation assertions before installation.
  It requires the distinct `nginx-core` fixture initially absent, predicts
  installation for present and no change for absent, and verifies it remains
  absent; it never removes packages to manufacture that premise.
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
[`7fc510d05cfce04e6dc60d70285e8ed9eee725e5`](https://github.com/idarsi/idarsi-ansible-test-environments/tree/7fc510d05cfce04e6dc60d70285e8ed9eee725e5),
supporting `idarsi.scenario-context/v1` and `direct` plus `supervised` lifecycle
modes. A separately reviewed compatible revision is possible; record its exact
SHA and dirty qualification. Do not relabel dirty-helper results as acceptance
of the pristine pin. See its
[isolated-run contract](https://github.com/idarsi/idarsi-ansible-test-environments/blob/7fc510d05cfce04e6dc60d70285e8ed9eee725e5/docs/isolated-test-runs.md),
and the optional TUI's `MANAGED_ROLE_GUIDE.md` and `METADATA.md`.

This exact helper code revision was published on 2026-11-27 through
`update/config-bridge-stdout` (documentation tip `21a8d96`); CI pins the tested
code revision, not that later documentation commit. Helper campaign 351 records
bounded ansible-current acceptance of the two previously failed nginx cells
at role `2c855f7`, not a full-suite or GitHub CI pass. Historical producing
revisions below remain unchanged.

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
its disposable `ubuntu-24.04` runner and runs the two nonprivileged managed Podman
scenarios as the unprivileged runner. Collections are installed into resolved
per-context directories. All Podman initialization, Podman/libvirt discovery,
context resolution, private collection installation and both complete
`molecule test` lifecycles run inside one same-user `sudo -n -H -u` shell,
refreshing supplementary libvirt membership without changing the runner's
passwd primary GID. No login shell or preserved-group option is used.
An explicit post-drop environment allowlist retains setup-python's `PATH` and
`LD_LIBRARY_PATH`, the helper path and expected runner UID. `XDG_RUNTIME_DIR`
is retained only when nonempty in the outer runner environment; otherwise it
is explicitly unset, leaving Podman's ordinary runtime-directory selection
unchanged. No runtime directory is created or required before Podman starts.
Inside that target-user shell, the inherited umask is logged and then set to
`077` before backend readiness, helper resolution, collection bootstrap or
Molecule. This governs new private-context directories; it does not repair
existing permissions or relax the helper's ownership/mode checks.
The shell asserts nonroot real/effective UID, passwd primary real/effective
GID, passwd username/HOME and exact numeric supplementary libvirt membership,
prints runner identity and local discovery, and reports the original failure
status and shell line without retries, recovery or ignored destroy errors.
The existing privileged package/service/group setup remains separate and
unchanged. Host setup in this workflow is not authorization to
modify a developer's host. This configuration has **not** completed successfully
or been accepted as a GitHub CI pass for the migration.

Run [`45961030496`](https://github.com/idarsi/ansible-iac-role-nginx/actions/runs/45961030496)
at role `2c855f7e2e17a48c02d7aeedf2f5aba223706af2` passed documentation,
syntax and lint checks, then failed fetching unpublished helper
`cc777691026cf300089b8d53760555987c62ce7f` (`not our ref`, exit 128), before
backend setup or scenario execution. The current pin uses the published tested
revision above. Replacement CI acceptance remains pending; this publication
fix adds no runtime credit and does not change Beta / 66% maturity.

Run [`45966106121`](https://github.com/idarsi/ansible-iac-role-nginx/actions/runs/45966106121)
at role `a1b5b8a3e520679db29c847e8a56c7c51aed4cdb` fetched the published
helper and passed blueprint checks, but final destroy failed with
`rootless netns: kill network process: permission denied`. The hosted runner
reported Ubuntu 26.04.1, kernel 7, Podman 5.7.0, netavark 1.16.1,
aardvark-dns 1.16.0 and pasta (not slirp). Podman initialization previously
ran before `sg libvirt`, while lifecycle execution ran inside it. A primary-GID
context mismatch is plausible; neither a kernel regression nor the precise
PID-file-read versus process-kill failure is established. The first workflow
correction moved initialization and lifecycles into one `sg libvirt` context;
it does not repair that failed runner's retained state. Fresh hosted CI
acceptance remains pending.

Run [`45979780346`](https://github.com/idarsi/ansible-iac-role-nginx/actions/runs/45979780346)
at role `06d5789ae062a3cda58511c4b9ca748333624a9a` failed at initial
`podman --remote=false info` before any scenario (exit 125). The runner had
UID 1001 and primary GID 980 (`libvirt`), but passwd primary GID 1001.
`newuidmap` rejected the target process ownership with the mismatched GID.
This proves that the `sg` primary-GID change is unsuitable for this runner's
rootless initialization. The follow-up refreshes supplementary groups using
same-user sudo while retaining the passwd primary GID and one consistent
backend context. It does not prove the original final-destroy error resolved;
fresh hosted lifecycle/cleanup acceptance remains pending.

Run [`45981011685`](https://github.com/idarsi/ansible-iac-role-nginx/actions/runs/45981011685)
at role `46073c0e199acdd4957659d68e15ec6a17289780` passed the corrected
same-user credential assertions, but final rootless network teardown still
failed. The workflow retains that credential refresh and pins the maintained
Ubuntu 24.04 LTS image as a compatibility baseline.
[Runner-images issue 15182, maintainer comment 6493085515](https://github.com/actions/runner-images/issues/15182#issuecomment-6493085515)
reproduces the exact permission-denied teardown error on Ubuntu 26.04 on both
architectures, with AppArmor denying Podman's SIGTERM to pasta; Ubuntu 24.04
controls pass. The failed runner's Podman 5.7/passt January 2026 versions match
the upstream report, but this run has no runner-specific AppArmor audit capture:
the match is high confidence, not direct proof. Upstream fix
[15184](https://github.com/actions/runner-images/pull/15184) remains open/unmerged
as of this correction. No AppArmor/security-policy relaxation or network-backend
override is applied here. Ubuntu 24.04's current image inventory has Podman
4.9.3 with default slirp4netns and the required libvirt interfaces. Its kernel
can also be 7; this is not a kernel-7 avoidance claim or a package-version pin.
Fresh hosted acceptance of the new baseline remains pending.

Run [`45986450582`](https://github.com/idarsi/ansible-iac-role-nginx/actions/runs/45986450582)
at role `e34900ef754c1cda638b24eb7290d9625fb1448c` reached resolved private
collection bootstrap on Ubuntu 24.04; Galaxy reported nothing to do, then
Molecule's initial destroy failed with `Unsafe Molecule collection destination`
before resources were created. The published helper checks existing ephemeral
and collections directories for matching EUID, directory type and no group/other
write bits. Its restrictive umask applies only in its own child process.
Ansible Core 2.21.3's Galaxy CLI creates the output directory before its
nothing-to-do result; it therefore can create a group-writable directory under
an inherited `0002` mask outside the helper. This is a source-backed
high-confidence mechanism, not an observed historical mode: that run did not
log destination ownership/type/mode or its caller umask.

The follow-up sets `umask 077` in the target-user shell itself, rather than
relying on an outer shell's mask surviving sudo/PAM. Immediately before and
after Galaxy bootstrap, bounded read-only Python diagnostics `lstat` only the
resolved collections path and its inferred ephemeral parent. Fixed labels
report existence, object type, UID/GID and permission mode; missing paths are
expected, while other errors emit a finite errno/status and fail. No path,
file contents, environment dump, recursive walk or permission repair is logged
or performed. Installation remains private to the resolved context, with
existing helper locking and `driver.safe_files` unchanged.
Fresh hosted acceptance remains pending. This early refusal does **not**
verify the Ubuntu 24.04 teardown workaround or provide cleanup/runtime credit.

Run [`45988385250`](https://github.com/idarsi/ansible-iac-role-nginx/actions/runs/45988385250)
at role `8d84ff8bb79823001944f0036fc606de99fdab8a` passed the blueprint
scenario's full lifecycle. The broader validation scenario passed create,
converge and idempotence, then failed verify because real DNF check-mode
metadata resolution could not resolve Rocky BaseOS mirrors (Curl error 6),
before the package-binding assertions. Automatic destroy passed; the final
absence gates were not reached. The DNS failure's cause remains unknown:
the pinned helper creates an ordinary labelled subnet/gateway network without
`--internal`, not an intentionally internal network.

Check mode does not make a real DNF solver offline. The entire two-state
package-override block and helper therefore move from Podman verification to
`kvm-rocky9-check-mode` preparation, where real package/repository behavior
belongs. Existing KVM converge/verify behavior remains unchanged. Actual
current-controller KVM acceptance of that new preparation and replacement
hosted Podman acceptance remain pending; historical KVM passes do not transfer.
No network/DNS policy or role implementation change is justified by this error.

Hosted CI now requires this portable native-engine regression:

```bash
python -B -m unittest discover -s tests -p test_nginx_package_dispatch.py -v
```

It copies unchanged production dispatch/present/absent and logging includes into
temporary fixtures, runs Ansible's CLI using the active `sys.executable`, and
intercepts only DNF actions. A fail-closed connection plugin rejects all host
connections, commands and transfers. Native include/assert/register/check-mode
semantics verify both states, a distinct override's exact secure DNF arguments,
invalid-state rejection, injected DNF failures and a hardcoded-default negative
control. This proves bindings/control flow, not package availability, solver
behavior or nonmutation on a guest.

The escaping-source symlink fixture is also corrected to create and clean up
on the controller checkout (`delegate_to: localhost`, `become: false`), where
the role's realpath validation reads it, rather than an unmounted guest path.
A pre-block non-following stat/assert refuses a pre-existing fixture; the
original rejection/rescue and unconditional `always` cleanup are retained.
Cheap source assertions cover placement/cleanup without creating a controller
checkout fixture. Unsafe-CA and other negative validation assertions remain.

After both full scenarios succeed, the same nonroot shell performs read-only
absence checks for containers and networks with the pinned helper's exact
`io.idarsi.test-run` label, printing remaining container IDs and network names
and rejecting any leftovers.
It also rejects runner-UID `pasta`, `passt` or `slirp4netns` processes by exact
name (PID-only output). This process-name check is valid **only on the fresh,
dedicated disposable CI runner**, not a shared developer host. Podman query
errors fail; pgrep exit 1 alone means no match, while operational errors retain
their original status. These checks catch leftovers even when older Podman
reports a network-helper error nonfatally. They perform no removal, kill,
recovery or retry and are an additional CI absence gate, not authoritative
helper cleanup-manifest proof.

The host-free regression extracts the actual managed-step shell from workflow
YAML. A temporary allowlisted PATH mocks `sudo`, identity lookup, Podman, virsh,
the helper, JSON parsing, collection installation, Molecule and process-name
queries; unknown commands
fail closed. It never executes the prerequisite step or a real backend.
It checks initialization/discovery and both full scenario commands in order,
and original nonzero status/no subsequent calls on each boundary failure.
It rejects wrong real/effective UID/GID, the former `sg` primary GID even with
valid libvirt membership, incorrect username/HOME, missing supplementary groups
and substring-only group matches before discovery. Runtime-directory environment
tests cover both explicit preservation and absence without directory creation.
The runner label is asserted. Cleanup checks must follow both successful
lifecycles, reject container/network/process leftovers and preserve query-error
status (including pgrep exit 2); pgrep exit 1 is the successful absence case.
Inherited `0002`, `0022` and `0077` masks are applied only to spawned test
processes. Every mocked helper/Galaxy/Molecule boundary must see `0077`;
the fake Galaxy creates a real disposable fixture directory and emits its
nothing-to-do result. The actual diagnostic Python runs only against those
fixtures, requiring private `0700` metadata before/after bootstrap and proving
fixture contents are not printed. No real helper or collection installer runs.
CI runs it before backend setup. From an existing approved controller
environment (existing PyYAML plus Python standard library only):

```bash
python -B -m unittest discover -s tests -p test_ci_backend_context.py -v
```

This is shell-control-flow/mock evidence, not Podman, cleanup or guest
acceptance. No local backend execution or GitHub rerun is part of this correction.

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
