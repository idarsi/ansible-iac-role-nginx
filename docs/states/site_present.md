# `site_present`

For each declared site, renders its configured website, proxy, or manual server configuration under `sites-available`, creates the site's web-root and log directories, and creates a self-signed certificate when the selected certificate type is `selfsigned`. It records site ownership when role ownership tracking is available. It does not enable the site or start Nginx. Existing site files not established as role-owned are not treated as removable role-owned content.
