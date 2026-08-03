ANSIBLE-IAC-ROLE-NGINX
======================
**COPYRIGHT** 2026 ^(ida|arsi)$ collective  
**LICENSE** MIT License [LICENSE](LICENSE)  
**AUTHORS**
- Arsi Atomi <arsi@atomi.sh>  
- Arsi Atomi <arsi.atomi@valtori.fi>  

Overview
========

This Ansible role is designed to simplify and enhance the flexibility of Nginx management.

This role uses only ansible.builtin.* ansible modules and openssl and nginx cli commands.

Supported Nginx version:
- nginx-stable from Nginx repository

These operations are supported:

Operation                       | State               |
--------------------------------|---------------------|
Installing and enabling Nginx   | install             |
Installing Nginx                | present             |
Removing Nginx                  | absent              |
Removing Nginx and config       | uninstall           |
Creating site configuration     | site_present        |
Removing site configuration     | site_absent         |
Creating location configuration | location_present    |
Removing location configuration | location_absent     |
Enabling site configuration     | site_enabled        |
Disabling site configuration    | site_disabled       |
Starting Nginx service          | started             |
Stopping Nginx service          | stopped             |

Requirements
------------

- Operating system (tested on)
  - Red Hat Enterprise Linux 8
  - Rocky Linux 10
  - Rocky Linux 9
  - Rocky Linux 8

- Other components
  - Ansible 2.16 or higher

Repository checkout
-------------------

This role includes the shared task library as a Git submodule under
`tasks/shared`.

Clone the repository with submodules:

```bash
git clone --recurse-submodules https://github.com/idarsi/ansible-iac-role-nginx.git
```

If you already cloned the repository without submodules, initialize them with:

```bash
git submodule update --init --recursive
```

Usage
=====

iac_blueprint inventory structure
---------------------------------

Top-level structure:

```yaml
iac_blueprint:
  nginx:
    directories:
      - path: <directory_path>
    files:
      - path: <file_path>
        content: <file_content>
    cron:
      - name: <cron_name>
        job: <cron_job>
        minute: <cron_minute>
        hour: <cron_hour>
        cron_file: <cron_file>
    sites:
      - name: <site_name>                                 # site specific name
        ssl_certificate_type: <certificate_type>          # none|selfsigned (default: selfsigned)
        autoconfigure: <autoconfigure_type>               # none|website|proxy (default: website)
        servers:                                          # direct server {} override configuration
          - key: <value>
```

A minimal working iac_blueprint that installs Nginx with one virtual host and uses autoconfigure.

```yaml
iac_blueprint:
  nginx:
    sites:
      - name: example.org
        ssl_certificate_type: selfsigned
        autoconfigure: website
```

Same configuration done manually.

```yaml
iac_blueprint:
  nginx:
    sites:
      - name: example.org
        ssl_certificate_type: selfsigned
        servers:
          - listen: 80
            server_name: example.org
            return: 301 https://example.org$request_uri
          - listen: 443 ssl
            server_name: example.org
            ssl_certificate: /etc/pki/tls/certs/example.org.crt
            ssl_certificate_key: /etc/pki/tls/private/example.org.key
            root: /var/www/example.org/html
            index:
              - index.html
              - index.htm
            locations:
              - path: /
                try_files:
                  - $uri
                  - $uri/
                  - /index.html
```

Reverse proxy example
---------------------

This example keeps the top-level site explicit and proxies only `/api` to an upstream service.

```yaml
iac_blueprint:
  nginx:
    sites:
      - name: app.example.org
        ssl_certificate_type: selfsigned
        servers:
          - listen: 80
            server_name: app.example.org
            return: 301 https://app.example.org$request_uri
          - listen: 443 ssl
            server_name: app.example.org
            ssl_certificate: /etc/pki/tls/certs/app.example.org.crt
            ssl_certificate_key: /etc/pki/tls/private/app.example.org.key
            root: /var/www/app.example.org/html
            index:
              - index.html
            locations:
              - path: /api
                autoconfigure: proxy
                redirect_to: http://127.0.0.1:3000
              - path: /
                try_files:
                  - $uri
                  - $uri/
                  - /index.html
```

Manual location examples
------------------------

`locations` are defined under each server entry. If `autoconfigure: proxy` is set for a location, the role renders the standard proxy headers automatically. Otherwise all keys except `path` are rendered as plain Nginx directives.

```yaml
iac_blueprint:
  nginx:
    sites:
      - name: static.example.org
        servers:
          - listen: 80
            server_name: static.example.org
            root: /var/www/static.example.org/html
            locations:
              - path: /
                autoindex: true
              - path: /healthz
                return: "200 ok"
```

Sub-URL served from a dedicated filesystem path
-----------------------------------------------

This example shows a normal website where `/downloads` is served from `/srv/data/downloads` on the target host instead of the default document root.

```yaml
iac_blueprint:
  nginx:
    directories:
      - path: /srv/data/downloads
        owner: nginx
        group: nginx
        mode: "0755"
        selinux:
          setype: httpd_sys_content_t
    sites:
      - name: files.example.org
        ssl_certificate_type: selfsigned
        servers:
          - listen: 80
            server_name: files.example.org
            return: 301 https://files.example.org$request_uri
          - listen: 443 ssl
            server_name: files.example.org
            ssl_certificate: /etc/pki/tls/certs/files.example.org.crt
            ssl_certificate_key: /etc/pki/tls/private/files.example.org.key
            root: /var/www/files.example.org/html
            index:
              - index.html
            locations:
              - path: /
                try_files:
                  - $uri
                  - $uri/
                  - /index.html
              - path: /downloads/
                alias: /srv/data/downloads/
                autoindex: true
```

Shared filesystem and cron examples
-----------------------------------

The role also supports shared filesystem and cron definitions at `iac_blueprint.nginx` level.

```yaml
iac_blueprint:
  nginx:
    directories:
      - path: /var/www/shared-assets
        owner: nginx
        group: nginx
        mode: "0755"
        selinux:
          setype: httpd_sys_content_t
      - path: /var/cache/nginx/custom
        owner: nginx
        group: nginx
        mode: "0750"
    files:
      - path: /etc/nginx/conf.d/security-headers.conf
        owner: root
        group: root
        mode: "0644"
        content: |
          add_header X-Frame-Options SAMEORIGIN;
          add_header X-Content-Type-Options nosniff;
        selinux:
          setype: httpd_config_t
    cron:
      - name: nginx-logrotate-hup
        user: root
        minute: "5"
        hour: "0"
        cron_file: nginx-maintenance
        job: "systemctl reload nginx >/dev/null 2>&1"
```

State usage examples
--------------------

Typical playbook task examples:

```yaml
- name: Install Nginx package, base config, shared filesystem entries and cron
  ansible.builtin.include_role:
    name: ansible-iac-role-nginx
  vars:
    state: present

- name: Render site configuration files
  ansible.builtin.include_role:
    name: ansible-iac-role-nginx
  vars:
    state: site_present

- name: Enable configured sites
  ansible.builtin.include_role:
    name: ansible-iac-role-nginx
  vars:
    state: site_enabled

- name: Start Nginx service
  ansible.builtin.include_role:
    name: ansible-iac-role-nginx
  vars:
    state: started
```
