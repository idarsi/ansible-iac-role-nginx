# Maturity reassessment

**Maturity: Beta. RC readiness: 66% (66.5/100, rounded down).**

This independent evidence-based reassessment retains the existing criterion
scores for the pre-migration baseline
`c2f1c3543eff2dca0c27785403de29791d7f4c86`. The working-tree migration on
`update/optional-managed-molecule` is source-reviewed only. No runtime tests
were run at the user's request. All eight renamed/migrated scenarios await
runtime acceptance and receive no additional credit; historical results retain
their original SHA and scenario IDs and do not transfer to this migration.
The revised score is not evidence that the new tests failed or caused a
regression.

## Scorecard

Focused PID reconciliation/handler-graph reassessment (2026-11-26): assessed ref is the
uncommitted working tree after clean `e7476e6` on
`update/optional-managed-molecule`. The full criterion scorecard below is
retained at **66.5/100 → 66%, Beta**. Shared validation, narrow active-policy
PID relabeling, dry-run handling and additional enforcing-guest assertions
improve source-level recovery intent, but provide no new runtime acceptance.
No criterion multiplier changes: recovery, lifecycle, platforms and functional
testing remain partial; static checks do not earn guest-runtime credit. The
observed campaign 341 EACCES/protocol failure lacks an actual AVC/label capture,
so this is not a confirmed SELinux root-cause finding. Existing evidence gaps
and the Beta cap remain unchanged. The smallest next evidence increment is an
authorized enforcing Rocky 9/10 run of the updated existing scenarios, including
idempotence/check-mode and live-PID preservation, followed by the missing RHEL
and lifecycle coverage. No RC or production-readiness approval is claimed.

The focused follow-up separates an always-safe `restorecon -n -v` probe from
an inheriting mutating command, covering non-CLI check-mode overrides, and
recognizes only exact relabel messages instead of arbitrary stdout.
Targeted source/native-command mocks include administrator-customized labels
and CLI-false inherited previews. These checks close source-level review
findings but supply no guest-runtime evidence or criterion score increase.

Campaign 342 reached notified validation and exposed the unsupported nested
handler blocks after the PID repair had succeeded. The focused follow-up
flattens both blocks without changing policy or service semantics. Native
engine tests now actually notify/flush the copied production handler graph
with mocked host actions and a forbidden transport, including a negative
control that reproduces the original block error. These current/next
source/mock checks do not establish guest acceptance. Beta / 66% and every
criterion score remain unchanged; no runtime or production claim is added.

| Category | Criterion scores | Subtotal |
|---|---|---|
| Scope | Purpose 3/3; inputs 2.5/5; support 2/4 | 7.5/12 |
| Functionality | Core 8/8; lifecycle 3/6; platforms 1.5/3; rerun 1.5/3 | 14/20 |
| Safety | Preflight 3/6; secure defaults 6/6; destructive safety 2.5/5; check mode 3/3 | 14.5/20 |
| Convergence | Idempotence 5/5; transitions 2/4; recovery 2/4 | 9/13 |
| Tests | Static 3/3; validation 2/4; functional 3/6; idempotence 4/4; lifecycle 2/4; matrix 1.5/3; CI enforcement 0/1 | 15.5/25 |
| Documentation | Operator 2/4; testing 1/2; contribution 2/2; metadata 1/2 | 6/10 |
| **Total** | | **66.5/100** |

## Evidence and limitations

The historical scheduled CI run at
`50483665786006730a75993c44003d65cada965a`,
[`44898161095`](https://github.com/idarsi/ansible-iac-role-nginx/actions/runs/44898161095)
on 2026-11-21 passed syntax, lint and the six existing Podman scenarios,
including the original `podman-platform-matrix` Rocky Linux 9/10 scenario.
This is not a pass of the renamed managed KVM scenarios. The branch has no
protection or rulesets requiring these checks, so configured CI is not enforced
merge policy.

RHEL 9/10 and SELinux runtime acceptance, bind/cron lifecycle and recovery
coverage remain gaps. These gaps and the pre-existing discrepancies below
retain the Beta cap:

- The README bind example targeting `/var/cache/nginx` conflicts with the
  canonical-path descendants guard.
- Inline-only file-content documentation contradicts accepted source-only
  implementation.
- The guardrails claim of opt-in configuration cleanup is not demonstrated:
  its fixture never sets `nginx_uninstall_remove_config: true`.
- Manifest cleanup deletion lists have insufficient scope, traversal and
  canonical-path checks.
- Optional-field preflight validation is incomplete.

These are pre-existing assessment findings, not changes introduced or fixed by
the managed-test task. This assessment is not a full security audit and does
not demonstrate a High-severity exploit.

## Historical summary

The previous README reported **Beta / 94%** with an incomplete scorecard,
associated with commit `6723d2b` and older assessed ref
`6fb36d595090873a6ebf375b43e8700d62c5073e`. That value is retained here as
historical context, not current acceptance. The present score uses the explicit
criterion scores and evidence above.
