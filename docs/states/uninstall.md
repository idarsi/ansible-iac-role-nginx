# `uninstall`

Performs the orderly teardown: validates role ownership, stops Nginx, disables and removes manifest-owned configured sites, then runs `absent` to remove declared shared resources and the package. It requires `nginx_uninstall_confirm: true`; without it validation fails before state work.

Configuration cleanup is separately opt-in with `nginx_uninstall_remove_config: true`. When enabled, it removes only validated configuration paths listed as role-owned in the ownership manifest; without it, configuration is preserved. The ownership marker/manifest are required for guarded cleanup, and externally managed paths are not claimed. Site data directories and certificates are not removed by site removal.
