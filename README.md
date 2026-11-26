> **Maturity State: Beta**
>
> **RC Readiness: 66%**

See the [evidence-based maturity reassessment](docs/maturity-assessment.md).
The focused stopped-PID fixture assessment covers `cae9ff2` plus working-tree changes;
native-engine mocks are source-level evidence, not guest/runtime acceptance.
The previous 94% summary is historical, not the current score; this reassessment
is not a regression caused by the optional managed-test integration.

See the executable [inventory example](docs/inventory-example.yml) and
[playbook example](docs/playbook-example.yml) for a minimal installation.

ANSIBLE-IAC-ROLE-NGINX
======================
**COPYRIGHT** 2026 ^(ida|arsi)$ collective
**LICENSE** MIT License [LICENSE](LICENSE)
**AUTHORS**
- Arsi Atomi <arsi@porkkana.org>

Overview
--------

An Ansible role for secure, declarative Nginx installation, virtual hosts,
locations, certificates, filesystem resources, bind mounts, cron jobs, and
service lifecycle.

Support and security defaults
-----------------------------

The supported platforms are Rocky Linux 9/10 and Red Hat Enterprise Linux
9/10. Historical Podman CI covered Rocky Linux 9/10; the renamed managed KVM
matrix is source-reviewed only and awaits runtime acceptance. Current CI
configures two Rocky Linux 9 validation scenarios; full host/service coverage
requires a provisioned KVM runner and remains manual/pending. RHEL is supported
but is not automatically covered by this repository's Molecule matrix. See
[TESTING.md](TESTING.md).

Nginx uses the HTTPS `nginx-stable` repository by default; override its section
name with `iac_dnf_repo_name`. DNF certificate and GPG
verification are enabled by default. The role writes private keys as root with
mode `0600`, validates configuration with `nginx -t` before starting Nginx,
and only notifies the validation handler when configuration changes. The
explicit start and notified validation paths share a defensive PID-file
reconciliation step: after successful `nginx -t`, SELinux-enabled hosts restore
the active policy's default context on an existing `/run/nginx.pid`. The role
rejects symlinks, nonregular objects and multiply linked files, leaves absent
files alone, and never deletes/truncates the PID file or changes its contents,
owner or mode. It does not relabel `/run` recursively or hardcode a policy type.
An existing live master is preserved; notified reload still requires a running
service. Check mode skips `nginx -t` (which can create a PID file) and uses
`restorecon -n -v` only on an existing safe file, reporting predicted changes.
The safe probe always uses `-n`; the separate mutating command inherits Ansible
check mode, including task/play/block overrides when CLI check mode is off.
Only exact policy relabel/preview messages report a repair; informational
messages about administrator-customized labels do not count as changes, and
the role does not force overrides of those customizations.
The target distribution's `policycoreutils` package must provide executable
`/usr/sbin/restorecon`; missing tools and relabel failures stop convergence.
The fixed root-owned `/run` path is trusted; these checks are not atomic against
a privileged actor replacing the object between inspection and use.
This is defensive convergence, not proof that SELinux caused the observed
startup failure: its actual AVC and PID-file label were not captured.

The proxy preset enables upstream TLS certificate verification by default for HTTPS
upstreams (`nginx_proxy_ssl_verify: true`). The trust store defaults to the
system CA bundle at `nginx_proxy_ssl_trusted_certificate:
"/etc/pki/tls/certs/ca-bundle.crt"`; set this to another safe absolute CA file
when upstreams use a private CA. When an HTTPS upstream uses verification, the
file must already be a readable regular file, or be declared in
`iac_blueprint.nginx.files` so `state: "install"` creates it before site
rendering. Proxy locations inherit site-level `deny`,
`allow`, `auth_basic`, and `auth_basic_user_file` values unless they explicitly
override the corresponding directive. Access-control directives preserve their
blueprint mapping order because Nginx evaluates `allow` and `deny` on a
first-match basis. A location that defines both `allow` and `deny` completely
replaces the inherited rule pair and uses its own mapping order. With a partial
location override, inherited directives retain their site positions, matching
location keys replace values in those positions, and location-only directives
are appended in location mapping order. `auth_basic` and
`auth_basic_user_file` are inherited and overridden independently; after a
complete location rule-pair override, these authentication directives follow
the location rule pair in their inherited order.
Preferred repository settings are `iac_dnf_sslverify`,
`iac_dnf_validate_certs`, and `iac_dnf_disable_gpg_check`; the corresponding
legacy `dnf_*` names remain supported.

States
------

The default state is `present`.

| State | Meaning |
|---|---|
| [`validate`](docs/states/validate.md) | Validate the complete blueprint without installing packages, writing files, or changing services. |
| [`present`](docs/states/present.md) | Converge packages, repository, shared configuration, filesystem resources, binds, and cron. |
| [`install`](docs/states/install.md) | `present`, then create/enable configured sites and start Nginx. |
| [`absent`](docs/states/absent.md) | Stop Nginx, remove declared shared resources and the package, and remove the repository only when the ownership pair permits it. |
| [`uninstall`](docs/states/uninstall.md) | Destructive removal; requires `nginx_uninstall_confirm: true`. Configuration removal also requires `nginx_uninstall_remove_config: true`. |
| [`site_present`](docs/states/site_present.md) | Create a named site's role-managed configuration; site data directories and certificates are retained when removing the site. |
| [`site_absent`](docs/states/site_absent.md) | Remove named site's role-owned configuration and enablement link; site data directories and certificates are retained. |
| [`site_enabled`](docs/states/site_enabled.md) | Ensure configured named site's server configuration is enabled. |
| [`site_disabled`](docs/states/site_disabled.md) | Ensure configured named site's server configuration is disabled. |
| [`location_present`](docs/states/location_present.md) | Render the declared locations for a site. |
| [`location_absent`](docs/states/location_absent.md) | Render the site's configuration without its declared locations. |
| [`started`](docs/states/started.md) | Start Nginx without changing boot enablement. |
| [`stopped`](docs/states/stopped.md) | Stop Nginx when installed, without removing it or changing boot enablement. |

Unknown states fail before convergence. Uninstall never removes an existing
`nginx_etc_directory` unless the role-created marker and validated ownership
manifest are present; externally managed paths are preserved.

Blueprint contract
------------------

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

Sites, servers, and locations
-----------------------------

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
 additional proxy-site location. The supported location security fields are:

  * `proxy_set_header`: a string (`"Header value"`) or list of strings. Lists
    render one repeated directive per entry; values must be strings without
    Nginx directive delimiters or line breaks.
  * `auth_request`: a local absolute URI beginning with `/`. Only
   `A-Za-z0-9._~!$&()*+,=:@%/?-` are allowed; schemes, whitespace, semicolons,
   braces, comments, and line breaks are rejected.
 * `internal`: boolean `true` or the empty string `""`, both rendered as the
   Nginx directive `internal;`. A location cannot bypass schema validation.

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

Directories and files
---------------------

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
For states that inspect or change host state, the role resolves managed paths
with `realpath -m` before state work to detect parent-symlink resolution into
protected roots. The `validate` state intentionally performs no host-runtime
probes. This is a preflight guard, not an atomic protection against a
privileged actor changing a parent symlink between validation and the
filesystem operation.

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

Binds
-----

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

Cron
----

Each `cron` record requires string `name` and `job`. Set `cron_file` explicitly
to a portable `/etc/cron.d` filename containing only letters, numbers, `_`, and
`-`; dots, `.` and `..` are rejected. `user` defaults to
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

Paths and operational variables
-------------------------------

The main configurable paths are `nginx_etc_directory`, `nginx_log_directory`,
`nginx_www_directory`, `nginx_public_key_directory`, and
`nginx_private_key_directory`. The three Nginx managed directory paths must be
absolute and consist only of safe path components (`A-Z`, `a-z`, numbers, `.`,
`_`, and `-`); relative paths, `..`, and Nginx/shell metacharacters are rejected
before any host changes or template rendering. The certificate directories are restricted to
`/etc/pki/tls/certs` and `/etc/pki/tls/private` (optionally one safe child).
The repository path is restricted to `/etc/yum.repos.d/*.repo`; the package and
repository identifiers are also validated. `iac_dnf_main_package` is used for
both installation and removal of the Nginx package. SELinux relabeling runs
only when SELinux is enabled; test containers are intentionally skipped, while
real `restorecon` failures stop convergence. Do not use `/`, `..`, shell
fragments, or broad unmanaged paths.

Testing and development
-----------------------

Use the shared task library when cloning this repository:

```bash
git clone --recurse-submodules https://github.com/idarsi/ansible-iac-role-nginx.git
```

See [TESTING.md](TESTING.md) for the tested matrix, observable lifecycle
checks, and commands. See [CONTRIBUTING.md](CONTRIBUTING.md) for development
workflow.

All eight scenarios support ordinary direct Molecule execution and declare
optional TUI-managed whole-scenario execution: two nonprivileged Rocky Linux 9
Podman validation scenarios and six KVM scenarios, including the complete
Rocky Linux 9/10 matrix. See `TESTING.md` for exact IDs and prerequisites.
The migration working tree is source-reviewed only; no runtime tests were run
at the user's request. Historical evidence retains its original SHA and IDs
and does not transfer to renamed or migrated scenarios. The Beta / 66% maturity
score is unchanged; metadata is test intent, not runtime acceptance.
