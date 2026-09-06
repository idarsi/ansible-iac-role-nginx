# ansible-iac-role-nginx

An Ansible role for secure, declarative Nginx installation, virtual hosts,
locations, certificates, filesystem resources, bind mounts, cron jobs, and
service lifecycle.

## Support and security defaults

The supported platforms are Rocky Linux 9/10 and Red Hat Enterprise Linux
9/10. Rocky Linux 9 and 10 are tested in the scheduled platform matrix; the
pull-request functional matrix uses Rocky Linux 9. RHEL is supported but is
not automatically covered by this repository's Molecule matrix. See
[TESTING.md](TESTING.md).

Nginx uses the HTTPS `nginx-stable` repository by default; override its section
name with `iac_dnf_repo_name`. DNF certificate and GPG
verification are enabled by default. The role writes private keys as root with
mode `0600`, validates configuration with `nginx -t` before starting Nginx,
and only notifies the validation handler when configuration changes. The
preferred repository settings are `iac_dnf_sslverify`,
`iac_dnf_validate_certs`, and `iac_dnf_disable_gpg_check`; the corresponding
legacy `dnf_*` names remain supported.

## States

The default state is `present`.

| State | Meaning |
|---|---|
| `validate` | Validate the complete blueprint without installing packages, writing files, or changing services. |
| `present` | Converge packages, repository, shared configuration, filesystem resources, binds, and cron. |
| `install` | `present`, then create/enable configured sites and start Nginx. |
| `absent` | Stop Nginx, remove declared shared resources and the package, and remove the repository only when the ownership pair permits it. |
| `uninstall` | Destructive removal; requires `nginx_uninstall_confirm: true`. Configuration removal also requires `nginx_uninstall_remove_config: true`. |
| `site_present` / `site_absent` | Create or remove a named site's role-managed configuration and unified enablement link. Site data directories and certificates are retained by `site_absent`. |
| `site_enabled` / `site_disabled` | Create or remove the named site's unified enablement link. |
| `location_present` / `location_absent` | Render or omit the declared locations for a site. |
| `started` / `stopped` | Start or stop the service without changing boot enablement. |

Unknown states fail before convergence. Uninstall never removes an existing
`nginx_etc_directory` unless the role-created marker and validated ownership
manifest are present; externally managed paths are preserved.

## Blueprint contract

The required root is a mapping containing `iac_blueprint.nginx`. All resource
collections below are lists and may be omitted unless they are needed.

```yaml
iac_blueprint:
  nginx:
    sites: []
    directories: []
    files: []
    binds: []
    cron: []
```

### Sites, servers, and locations

`sites` records require a unique safe `name` containing only letters, numbers,
`.` and `-`. The site defaults are `autoconfigure: "website"` and
`ssl_certificate_type: "selfsigned"` (these defaults can be changed with
`nginx_default_site_autoconfigure` and
`nginx_default_ssl_certificate_type`). Supported site fields are:

* `autoconfigure`: `"none"`, `"website"`, or `"proxy"`.
* `ssl_certificate_type`: `"none"` or `"selfsigned"`.
* `proxy_pass`: required for the `proxy` preset and restricted to an HTTP(S)
  URL without whitespace or Nginx metacharacters.
* `servers`: a list of manual server records.
* `locations`: site-level location records.

Manual `servers` require `listen` and may set `server_name`, certificate
fields, and other Nginx directives. An SSL listener requires both
`ssl_certificate` and `ssl_certificate_key`; they must be files directly under
the configured public/private certificate directories. Each server may have a
`locations` list. A location requires a non-empty path beginning with `/` and
may use `autoconfigure: "proxy"` with a required HTTP(S) `redirect_to`, or may
contain free-form Nginx directive fields. Location paths must be unique within
their collection. The proxy preset owns `/`, so `/` cannot be declared as an
additional proxy-site location.

```yaml
iac_blueprint:
  nginx:
    sites:
      - name: "example.org"
        autoconfigure: "website"
        ssl_certificate_type: "selfsigned"
      - name: "app.example.org"
        autoconfigure: "proxy"
        ssl_certificate_type: "selfsigned"
        proxy_pass: "http://127.0.0.1:3000"
        locations:
          - path: "/api"
            autoconfigure: "proxy"
            redirect_to: "http://127.0.0.1:3000/api"
```

For a fully manual HTTP site, use `autoconfigure: "none"` and
`ssl_certificate_type: "none"`:

```yaml
iac_blueprint:
  nginx:
    sites:
      - name: "manual.example.org"
        autoconfigure: "none"
        ssl_certificate_type: "none"
        servers:
          - listen: "8080"
            server_name: "manual.example.org"
            locations:
              - path: "/healthz"
                return: "200 ok"
```

Directive keys must be identifier-like names and directive values may not
contain `;`, `{`, `}`, `#`, or line breaks. This validation applies to server
and location records.

### Directories and files

`directories` records require `path`; `files` records require `path` and string
`content`. Both paths must be absolute, non-root paths with at least two path
components. Both support optional string octal `mode` (`0755` by default for
directories, `0644` for files), `owner`, and `group`. Ownership values are
passed to Ansible's filesystem modules and must name suitable existing system
accounts; the role does not invent accounts or widen permissions. Optional
`selinux` records require `setype` and may set `recursive` for directories.
Traversal components, empty components, broad parent paths, and protected
paths such as `/etc/passwd` are rejected before any mutation. Safe paths such
as `/srv/data` and `/var/www` remain valid.

```yaml
iac_blueprint:
  nginx:
    directories:
      - path: "/srv/example/cache"
        owner: "nginx"
        group: "nginx"
        mode: "0750"
    files:
      - path: "/etc/nginx/conf.d/example-extra.conf"
        content: "client_max_body_size 10m;\n"
        owner: "root"
        group: "root"
        mode: "0644"
```

The preflight contract requires inline `content` for file records; source-only
file records are not a valid public blueprint. Destructive `absent` handling
removes only the declared filesystem records, so do not declare paths owned by
another application.

### Binds

Each `binds` record requires distinct absolute `source` and `target` paths;
the target cannot be `/`. The source directory is created if needed and the
target must be absent or a directory. Optional `owner`, `group`, and octal
`mode` apply to the source directory. Optional `move_from_target: true` allows
one-time migration only when source or target is empty, then persists and
activates the bind in `/etc/fstab`.
The same traversal, empty-component, broad-parent, and protected-path
guardrails apply independently to both source and target.

```yaml
iac_blueprint:
  nginx:
    binds:
      - source: "/srv/nginx-cache"
        target: "/var/cache/nginx"
        owner: "nginx"
        group: "nginx"
        mode: "0750"
        move_from_target: false
```

### Cron

Each `cron` record requires string `name` and `job`. Set `cron_file` explicitly
to a safe filename (letters, numbers, `.`, `_`, and `-`); `user` defaults to
`root`. The records also support Ansible cron schedule fields `special_time`,
`minute`, `hour`, `day`, `month`, `weekday`, and `state` (`present` or
`absent`).

```yaml
iac_blueprint:
  nginx:
    cron:
      - name: "nginx certificate check"
        user: "root"
        job: "/usr/local/sbin/check-nginx-certificates"
        minute: "15"
        hour: "3"
        cron_file: "nginx-maintenance"
```

## Paths and operational variables

The main configurable paths are `nginx_etc_directory`, `nginx_log_directory`,
`nginx_www_directory`, `nginx_public_key_directory`, and
`nginx_private_key_directory`. The three Nginx managed directory paths must be
absolute and consist only of safe path components (`A-Z`, `a-z`, numbers, `.`,
`_`, and `-`); relative paths, `..`, and Nginx/shell metacharacters are rejected
before any host changes or template rendering. The certificate directories are restricted to
`/etc/pki/tls/certs` and `/etc/pki/tls/private` (optionally one safe child).
The repository path is restricted to `/etc/yum.repos.d/*.repo`; the package and
repository identifiers are also validated. Do not use `/`, `..`, shell
fragments, or broad unmanaged paths.

## Testing and development

Use the shared task library when cloning this repository:

```bash
git clone --recurse-submodules https://github.com/idarsi/ansible-iac-role-nginx.git
```

See [TESTING.md](TESTING.md) for the tested matrix, observable lifecycle
checks, and commands. See [CONTRIBUTING.md](CONTRIBUTING.md) for development
workflow.
