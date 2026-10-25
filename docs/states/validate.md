# `validate`

Runs the role's blueprint and state validation, including schema, cross-record, security, and destructive-uninstall checks where applicable. It does not probe host runtime state or dispatch state-specific changes. It does not install packages, write files, or change services. `validate` is still subject to the supported OS and required blueprint execution-context checks.
