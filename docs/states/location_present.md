# `location_present`

For each declared site, ensures the declared locations are included by invoking that site's configuration rendering path. This can rewrite the site's configuration and perform its normal site setup; it is not a narrow in-place edit of a location block. It does not install Nginx or start the service. HTTPS proxy prerequisites are checked before state work.
