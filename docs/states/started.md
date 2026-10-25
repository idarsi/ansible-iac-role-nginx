# `started`

Tests the installed Nginx configuration with `/usr/sbin/nginx -t`, then ensures the Nginx systemd service is running. This does not install Nginx, converge the complete blueprint, or change boot-time enablement. Invalid configuration prevents the service start.
