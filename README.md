> **Maturity State: Beta**<br>
> **RC Readiness: 82%**
>
> **Assessed ref/evidence:** Branch `security-hardening-2026-09`, commit
> `739bc2c`, current working tree. Validation Molecule PASS across all phases
> (`ok=513 changed=5 failed=0`); lifecycle Molecule PASS across all phases on
> Rocky Linux 9 (`ok=1010 changed=19 failed=0`); static syntax and production
> lint checks PASS. The validation scenario includes the staged, tracked-for-
> delivery `molecule/validation/tasks/security_proxy_validation.yml`; its
> security-regression evidence is included in the current test delivery.
>
> **Scorecard:** Scope and public contract `10/12`; functional completeness
> `17/20`; validation and safety `17.5/20`; convergence and recovery `11/13`;
> automated testing and CI `18/25`; documentation and release hygiene
> `9/10`. Total `82.5%`, rounded down to **82%**.
>
> **Mandatory cap:** Beta, because the declared RHEL 9/10 support has no
> automated RHEL evidence and the scheduled Rocky 9/10 matrix is not part of
> the pull-request checks. The numeric result is also in the Beta band.
>
> **RC blockers and smallest next steps:** Publish current guardrail,
> functional, check-mode, and Rocky 9/10 matrix results; add reproducible RHEL
> 9/10 evidence or narrow the support contract; add role metadata. SELinux-
> enabled behavior remains an explicitly documented but untested path.

| Category | Score | Evidence-based breakdown |
|---|---:|---|
| Scope and public contract | 10/12 | Purpose 3/3; inputs and states 5/5; support contract 2/4 because RHEL is declared but not automatically tested. |
| Functional completeness | 17/20 | Core convergence 8/8; lifecycle 6/6; platform/dependency handling 1.5/3; failure/rerun behavior 1.5/3. |
| Validation and safety | 17.5/20 | Preflight 6/6; secure behavior 6/6; destructive guardrails 2.5/5; check/diff behavior 3/3 with documented command/repository limits. |
| Convergence and recovery | 11/13 | Idempotent convergence 5/5; state transitions 4/4; operational recovery 2/4. |
| Automated testing and CI | 18/25 | Static checks 3/3; input validation 4/4; functional verification 3/6; idempotence 4/4; lifecycle/guardrails 2/4; platform matrix 1.5/3; CI enforcement 0.5/1 because no green CI result for this ref was supplied. |
| Documentation and release hygiene | 9/10 | Operator documentation 4/4; test/limitations 2/2; contribution contract 2/2; metadata 1/2 because role metadata is absent. |

**Production-review status:** Not applicable; the role is not a Release
 Candidate. This assessment updates `README.md`; the security regression test
 is staged for tracked delivery, and no commit has been created.

ANSIBLE-IAC-ROLE-NGINX
======================
**COPYRIGHT** 2026 Idarsi collective
**LICENSE** MIT License [LICENSE](LICENSE)
**AUTHORS**
- Idarsi collective

Overview
--------

An Ansible role for secure, declarative Nginx installation, virtual hosts,
locations, certificates, filesystem resources, bind mounts, cron jobs, and
service lifecycle.

Support and security defaults
-----------------------------

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
proxy preset enables upstream TLS certificate verification by default for HTTPS
upstreams (`nginx_proxy_ssl_verify: true`) and renders location access-control
directives such as `deny`, `allow`, and `auth_basic`.
preferred repository settings are `iac_dnf_sslverify`,
`iac_dnf_validate_certs`, and `iac_dnf_disable_gpg_check`; the corresponding
legacy `dnf_*` names remain supported.

States
------

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
The role also resolves managed paths with `realpath -m` before mutation to
detect parent-symlink resolution into protected roots. This is a preflight
guard, not an atomic protection against a privileged actor changing a parent
symlink between validation and the filesystem operation.

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
