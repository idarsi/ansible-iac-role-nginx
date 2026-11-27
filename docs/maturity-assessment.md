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

Focused PID reconciliation/preview-order reassessment (2026-11-26): assessed ref is the
uncommitted working tree after clean `6075aa3` on
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

Campaign 344 on clean `cae9ff2` passed converge/idempotence but failed the
stopped-service fixture's literal service-facts `stopped` assertion in both Rocky 10
current/next verifiers (worker exit 2; cleanup `cleaned`). Actual service
properties were not printed, so inactive/dead remains unproven. The focused
working-tree correction requires explicit systemd `inactive`/`dead` properties
with actionable PID diagnostics, covered by isolated mocks rather than a
guest rerun. This likely fixture portability correction supplies no new
functional, lifecycle, recovery or platform acceptance. Every criterion and
the Beta cap remain unchanged: **66.5/100 → 66%, Beta**.

| Category | Criterion scores | Subtotal |
|---|---|---|
| Scope | Purpose 3/3; inputs 2.5/5; support 2/4 | 7.5/12 |
| Functionality | Core 8/8; lifecycle 3/6; platforms 1.5/3; rerun 1.5/3 | 14/20 |
| Safety | Preflight 3/6; secure defaults 6/6; destructive safety 2.5/5; check mode 3/3 | 14.5/20 |
| Convergence | Idempotence 5/5; transitions 2/4; recovery 2/4 | 9/13 |
| Tests | Static 3/3; validation 2/4; functional 3/6; idempotence 4/4; lifecycle 2/4; matrix 1.5/3; CI enforcement 0/1 | 15.5/25 |
| Documentation | Operator 2/4; testing 1/2; contribution 2/2; metadata 1/2 | 6/10 |
| **Total** | | **66.5/100** |

Campaign 345 (clean role `6075aa3`, helper `491320f`, Rocky 10 SELinux,
current/next) passed the explicit stopped-service and active-policy assertions,
then failed actual-repair change reporting after previews; exit 2 and cleanup
`cleaned`. Enabled diagnostics returned `items: []`, not PID/AVC or success
evidence. Native engine negative controls now reproduce preview role
inclusions replacing real handlers with inherited-check-mode handlers on both
controller lanes. The test-only correction directly includes production tasks
for preview without handler re-registration; the complete preview/real-flush/
idempotent-repeat sequence passes with mocked actions and forbidden transport.
This confirms a fixture-order interaction, not a production SELinux diagnosis.
No guest rerun, runtime credit or criterion change: **66.5/100 → 66%, Beta**.

## Evidence and limitations

Supplementary-group refresh reassessment (2026-11-27): assessed ref is the
working tree after `06d5789ae062a3cda58511c4b9ca748333624a9a` on
`update/optional-managed-molecule`. Hosted run
[`45979780346`](https://github.com/idarsi/ansible-iac-role-nginx/actions/runs/45979780346)
failed initial local Podman info before any scenario (exit 125): `newuidmap`
rejected process primary GID 980 against passwd GID 1001. This confirms the
`sg libvirt` primary-GID change broke rootless initialization, not that the
earlier final-destroy error's cause was established. Same-user sudo now refreshes
supplementary membership while preserving passwd primary GID, nonroot identity,
HOME and explicitly allowlisted controller environment. Source/mock checks
cover credential rejection, runtime environment preservation/absence and
fail-fast behavior, not backend cleanup acceptance. Fresh hosted CI remains
pending. All criterion scores and category subtotals are unchanged, including
CI enforcement **0/1**: **66.5/100 → 66%, Beta**. Failing CI and existing
runtime/support gaps retain the Beta cap; no production approval is claimed.

CI credential-context reassessment (2026-11-27): assessed ref is the working
tree after `a1b5b8a3e520679db29c847e8a56c7c51aed4cdb` on
`update/optional-managed-molecule`. Hosted run
[`45966106121`](https://github.com/idarsi/ansible-iac-role-nginx/actions/runs/45966106121)
fetched the published helper and passed blueprint checks, then failed final
destroy with `rootless netns: kill network process: permission denied`.
The workflow now keeps initialization, discovery, private collection installs
and both complete lifecycles inside one nonroot libvirt credential context.
A context mismatch is plausible, not a proven kernel or network-process
root cause. Focused shell mocks do not establish backend/cleanup acceptance;
fresh hosted CI remains pending. Every criterion and category subtotal above
is retained, including CI enforcement **0/1** (failing latest CI and no required
merge policy established): **66.5/100 → 66%, Beta**. The failing-CI state cap,
existing runtime/support gaps and lack of production approval remain.

Source-pin publication reassessment (2026-11-27): assessed ref is
`update/optional-managed-molecule`, working-tree pin/documentation correction
after `2c855f7e2e17a48c02d7aeedf2f5aba223706af2`. CI run
[`45961030496`](https://github.com/idarsi/ansible-iac-role-nginx/actions/runs/45961030496)
passed documentation, syntax and lint, then failed to fetch unpublished helper
`cc777691026cf300089b8d53760555987c62ce7f` before backend setup/tests.
The replacement pin is the now-published tested helper
`7fc510d05cfce04e6dc60d70285e8ed9eee725e5`, not its later documentation tip.
This corrects source availability only: no new runtime test was run for this
change and replacement GitHub CI acceptance is pending. Campaign 351's bounded
current-lane acceptance remains source-qualified in the helper's testing record;
it is not full-matrix or GitHub CI evidence. All criterion scores above remain
unchanged, including CI enforcement 0/1 (no required merge policy established):
**66.5/100 → 66%, Beta**. Existing evidence gaps and mandatory Beta caps remain;
no RC or production approval is claimed.

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
