# `site_absent`

For each declared site, removes its enablement link and configuration (including legacy split configurations) only when the ownership manifest records that site as role-managed, then updates the manifest. Invalid ownership metadata causes guarded removal to fail. A site not recorded as role-owned is preserved.

This state does not remove the site's web-root or log directories, certificates, or other site data, and does not stop Nginx.
