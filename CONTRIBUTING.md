# Contributing

Keep the public `iac_blueprint.nginx` contract backward compatible. Add or
update validation, documentation, and Molecule coverage with every public
field or state change. All repository text must be written in English.

Use the shared test environment and Podman. Do not create a project-local
virtual environment or weaken security defaults to make a test pass.

Before submitting a change, run the targeted syntax and lint checks described
in `TESTING.md`. Destructive states must retain explicit confirmation and
ownership guardrails.
