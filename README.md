ANSIBLE-IAC-ROLE-NGINX
======================
**COPYRIGHT** 2025 ^(ida|arsi)$ collective  
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
Installing Nginx                | present             |
Creating site configuration     | site_present        |
Enabling site configuration     | site_enabled        |
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

Usage
=====

iac_blueprint inventory structure
---------------------------------

Top-level structure:

```yaml
iac_blueprint:
  nginx:
    sites:
      - name: <site_name>                                 # site specific name
        ssl_certificate_type: <certificate_type>          # none|selfsigned (default: none)
        autoconfigure: <autoconfigure_type>               # none|website|proxy (default: website)
        redirect_to: <url>                                # if autoconfigure is proxy this
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
```
