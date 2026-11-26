# Contributing

Keep the public `iac_blueprint.nginx` contract backward compatible. Add or
update validation, documentation, and Molecule coverage with every public
field or state change. All repository text must be written in English.

Use the pinned shared test environment documented in `TESTING.md`: rootless
Podman for the two nonprivileged validation scenarios, KVM for full-host
behavior. All eight scenarios remain directly callable with Molecule; the TUI
is optional and operates on whole scenarios. Do not create a project-local
virtual environment, upgrade shared dependencies, install host prerequisites
without authorization, or weaken security defaults to make a test pass.

Before submitting a change, run the targeted syntax and lint checks described
in `TESTING.md`. Destructive states must retain explicit confirmation and
ownership guardrails.

Renames must update metadata, sibling fixture paths, CI and current documentation.
Preserve the complete Rocky Linux 9/10 matrix and all regression assertions.
Keep destructive/check-mode regressions in verification rather than suppressing
their changes to satisfy idempotence. Record exact source/helper revisions and
controller lanes; metadata and configured CI are not execution evidence.
The current migration is static/source review only: no tests were run at the
user's request while other TUI runs were active. See `TESTING.md` for pending
runtime coverage and historical evidence qualifications.
