# `install`

Runs `present`, then creates the configured sites, enables those sites, and starts Nginx. Site creation applies the selected website/proxy/manual configuration, server records and required self-signed certificates; site data and log directories are created as part of site configuration. HTTPS proxy trust validation is performed before changes, and Nginx configuration is tested before service start.

This workflow does not set systemd boot enablement. It does not remove unlisted sites or site data.
