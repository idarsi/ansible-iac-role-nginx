# `present`

Ensures the Nginx prerequisites (`dnf-plugins-core` and `openssl`), configured repository and Nginx package are present, and converges the shared Nginx configuration and standard directories. It applies declared directories, files, bind mounts, and cron records when provided. It does not create or enable the declared virtual-host sites, nor does it start Nginx. Configuration changes notify validation; it does not promise full site convergence.

When the role has no pre-existing Nginx configuration directory, it establishes its ownership marker and manifest for later guarded cleanup. Existing configuration is not thereby claimed as role-owned.
