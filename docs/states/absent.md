# `absent`

Stops Nginx if its service is installed, removes only declared cron, bind, and filesystem resources, and removes the configured Nginx package. The configured repository file is removed only when the configured repository path is listed in the ownership manifest and the existing ownership safeguards (the role's marker and validated manifest) establish that the role owns it. It does not remove Nginx configuration wholesale, site data, certificates, or unrelated files; paths outside the declared resource scope are preserved.

Filesystem path and ownership preflights apply before removal. This is narrower than `uninstall` and does not require the uninstall confirmation flag.
