# `site_enabled`

For each declared site, ensures the site configuration is enabled. Website/proxy autoconfiguration renders its configuration before creating enablement; manual server records are enabled through the role's server tasks. It may therefore create or update site configuration as well as its enablement link. It does not install Nginx or start the service.
