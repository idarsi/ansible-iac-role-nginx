# Testing

## Automated matrix

| Platform/image | Ansible or application versions | Molecule scenarios | Main coverage |
|---|---|---|---|
| Rocky Linux 9 (`quay.io/rockylinux/rockylinux:9`) | ansible-core 2.21.3; nginx stable | `validation` | Validation and no-mutation contract |
| Rocky Linux 9 UBI init (`docker.io/rockylinux/rockylinux:9-ubi-init`) | ansible-core 2.21.3; nginx stable | `guardrails`, `lifecycle`, `check_mode`, `functional` | Ownership safety, all public transitions, check-mode safety, TLS/redirect behavior, repository defaults, and idempotence |
| Rocky Linux 9 and 10 UBI init (`docker.io/rockylinux/rockylinux:{9,10}-ubi-init`) | ansible-core 2.21.3; nginx stable | `platform-matrix` | Baseline installation, `nginx -t`, enabled site, service behavior, and idempotence |

Rocky Linux 9 and 10 are automatically tested by the scheduled
`platform-matrix` scenario. RHEL 9/10 are supported by the role but are not
automatically covered here.

## Scenario coverage

* `validation` checks valid input, invalid site/TLS/repository paths, duplicate
  and reserved server-level locations, supported states, and validation-only preservation of the
  pre-existing package, service, and role-managed path state. It also rejects
  a string value for the `sites` collection and mapping values for all five
  public collections with actionable type errors. It also rejects relative,
  parent-traversal, and Nginx-injection values for all three managed
  directory variables before host mutation. It also rejects directory, file,
   and bind source/target traversal and unsafe paths in both validation and
   absent states, with exact failure messages and preservation of pre-existing
   state. It also renders a custom DNF repository section without contacting an
  external repository. Check-mode fixtures execute the production present and
  absent package dispatch paths using the hardcoded test-only `nginx-core`
  override. Both package operations run in check mode without installing or
  removing a package. The baseline
  fixture file written by the test harness is intentionally excluded.
  The scenario intentionally omits Molecule's idempotence phase: the
  check-mode package-present fixture correctly predicts a change on every run
  because `nginx-core` is never installed. Production idempotence is covered
  by the lifecycle and functional scenarios.
* `guardrails` verifies uninstall confirmation, external repository/site and
  unrelated-file preservation, manifest ownership filtering, preservation of an
  unmanaged nested file below a manifest-owned directory after opt-in owned
  cleanup, and absent-state rejection of wrong markers and corrupt manifests
  without package or repository mutation.
* `lifecycle` verifies public `present`, `absent`, `uninstall`, site/location
  present/absent, enable/disable, and service stopped/started transitions.
  It verifies that the `started` state preserves a service's disabled boot
  enablement.
  For repeated location removal it compares the rendered file content before
  and after the repeat. For repeated public absent and site absent it compares
  the observed package/path existence results. For repeated present it compares
  the managed site's SHA-256 checksum before and after convergence. These are
  observable idempotence checks; `verify.yml` does not assert a systematic
  Ansible `changed=0` result for the repeated role invocations.
* `check_mode` compares package presence, service state, and managed file
  existence, checksums, and modes before and after representative check+diff
  convergence. It separately compares the repository path and content; the
  repository is expected to remain absent because check mode does not preview
  that repository operation. OpenSSL key generation and repository/package
  command behavior are not claimed as safely previewable, but the test proves
  that this limitation does not mutate the repository path.
* `functional` runs `nginx -t`, checks HTTPS/GPG repository defaults and private
  key mode `0600`, and verifies local HTTP-to-HTTPS redirect plus an actual
  HTTPS reverse-proxy response from a test-only backend on `127.0.0.1:8081`.
* `platform-matrix` repeats the baseline on Rocky Linux 9 and 10. Privileged
  systemd and the cgroup mount are test-only Podman settings.

The validation and functional scenarios do not execute `restorecon` in their
non-SELinux/container environments. Production `restorecon` errors fail the
convergence, but the SELinux-enabled failure path is not covered by automated
tests. The test suite does not infer restorecon coverage from
`virtualization_type` facts.

## Commands

Use the shared environment, without installing dependencies:

```bash
export PATH="$HOME/.local/share/venvs/idarsi-ansible-testing/bin:$PATH"
ansible-playbook --syntax-check -i localhost, -c local molecule/validation/converge.yml
ansible-lint --profile production
molecule test -s validation
molecule test -s guardrails
molecule test -s lifecycle
molecule test -s check_mode
molecule test -s functional
molecule test -s platform-matrix
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
