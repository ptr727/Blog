---
title: Yet Another Cloudflare Traefik Let's Encrypt Guide
date: '2024-05-29T18:45:00+00:00'
url: /2024/05/29/yet-another-cloudflare-traefik-lets-encrypt-guide/
categories:
- homeautomation
- network
- solution
tags:
- cloudflare
- security
- traefik
post_id: '2831'
---
There are many good guides on the internet on how to use and configure [Cloudflare Tunnels](https://www.cloudflare.com/products/tunnel/), [Traefik](https://traefik.io/), and [Let's Encrypt](https://letsencrypt.org/), using [wildcard certificates](https://en.wikipedia.org/wiki/Wildcard_certificate), and [Cloudflare Access](https://www.cloudflare.com/zero-trust/products/access/), for authenticated home lab network access.

This is yet another such guide, but using a single wildcard subdomain for remote homelab access. An advantage of using a wildcard subdomain is that the Cloudflare DNS and Tunnel and Access configuration only needs to be done once, and thereafter all access changes can be controlled through local homelab Traefik configuration. Another advantage is that services being exposed are not directly inferable by looking at DNS record names.

Following are basic setup steps, refer to detailed online guides for specific configurations, the steps call out the important highlights, replace domain names based on your own setup:

- Public domain `foo.net` serviced by [Cloudflare DNS](https://www.cloudflare.com/application-services/products/dns/).
  - Local domain on home network configured as `home.foo.net` in DHCP server or host configuration. I.e. all devices on the home network will be named `something.home.foo.net`.
  - DNS for `home.foo.net` will be served by your local DNS server. Typically most services will be `CNAME` entries pointing to an `A` record for the docker host or the Traefik server.
  - Other `VLAN` s would be on different subdomains, e.g. `guests.foo.net`, and can be routed accordingly.
- [Traefik](https://traefik.io/) configured and deployed on your homelab docker server.
  - Local DNS should be configured with a `CNAME` or `A` record to point to your traffic container at `traefik.home.foo.net`.
  - Configure [TLS](https://doc.traefik.io/traefik/routing/entrypoints/#tls) domains. Set `main` as `foo.net`, and `sans` as `*.foo.net`, `*.home.foo.net`, `*.lab.foo.net`. This will be used when creating the SSL certificate.
  - Configure [ACME certificate resolvers](https://doc.traefik.io/traefik/https/acme/) for Cloudflare DNS. Set `delayBeforeCheck: 60` and `disablePropagationCheck: true` to avoid timeouts during domain ownership validation when using Cloudflare.
  - Configure a [WhoAmI](https://hub.docker.com/r/containous/whoami) container fronted by Traefik, we will use this for testing and Tunnel bootstrapping. Set ``traefik.http.routers.whoami.rule: "PathPrefix(`/whoami`) || Host(`whoami.home.foo.net`) || Host(`whoami.foo.net`) || Host(`whoami.lab.foo.net`)"`` This will allow the container to service traffic destined to `whoami.foo.net`, `whoami.lab.foo.net`, and `whoami.home.foo.net`.
  - Add a local `CNAME` DNS entry for `whoami.home.foo.net` pointing to the Traefik instance at `traefik.home.foo.net`. The `whoami.foo.net`, and `whoami.lab.foo.net` entries will be configured later in Cloudflare DNS.
  - Make sure that `https://whoami.lab.foo.net` can be accessed locally and that the certificate is valid.
- [Cloudflare Tunnel](https://www.cloudflare.com/products/tunnel/) configured and deployed on your homelab docker server.
  - Tunnels offer several benefits over bespoke solutions:
    - There is no need to open any ports for ingress traffic on your firewall, the tunnel service makes an outbound connection to regional Cloudflare proxy servers.
    - Tunnels are fronted by Cloudflare proxies providing security and SSL termination with public certificates.
    - Tunnels can be protected with access control.
  - [Create a Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) and deploy as a docker container. Other than the auth token required in the docker configuration, all other configuration for the tunnel is done remotely using the Cloudflare console.
- [Cloudflare Access](https://www.cloudflare.com/zero-trust/products/access/) configured to authenticate remote access.
  - Configure Access before configuring public hostname tunnels so that any public hostname can be protected by Access when it gets created and before it goes live.
  - Configure identity providers in [Authentication](https://developers.cloudflare.com/cloudflare-one/identity/idp-integration/) settings, OTP is the easiest and requires no setup, other providers like Google, Facebook, LinkedIn, GitHub requires minimal additional configuration.
  - Create an Access Group to simplify configuration management. Create a group using emails as Selector and add all your allowed email addresses, e.g. your personal emails and work email. The email addresses can be served by any identify provider that authenticates using that email address, e.g. a GMail email can be used with OTP or Google or GitHub or LinkedIn or Facebook, etc.
- Create a `whoami.foo.net` [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) to the WhoAmI container.
  - Creating this tunnel first helps with the later wildcard tunnel configuration, as the Cloudflare tunnel workflow does not directly support wildcard tunnel DNS setup.
  - In the Tunnel configuration create a new public hostname for `whoami.foo.net` and point it to `https://whoami.home.foo.net`.
  - In additional settings for TLS enable "No TLS Verify" and "HTTP2 connection". ("No TLS Verify" is not strictly required if Traefik always serves valid SSL certs)
  - In additional settings for Access enable "Protect with Access" and select the Access configuration created.
  - The Cloudflare workflow will automatically create the required DNS `CNAME` entries for `whoami.foo.net`.
  - Access `https://whoami.foo.net` from your browser, make sure that you are prompted to authenticate before the page is served.
- Create a `*.lab.foo.net` wildcard tunnel.
  - The Cloudflare tunnel workflow does not directly support wildcard tunnel creation, so it is easiest to first create an explicit public hostname, and then copy the tunnel configuration.
  - Create a `*.lab.foo.net` `CNAME` in Cloudflare DNS, pointing to the Cloudflare Tunnel, use the `whoami` `CNAME` record to copy the tunnel FQDN.
  - In the Tunnel configuration create a new public hostname for `*.lab.foo.net` and point it to `https://traefik.home.foo.net`.
  - Apply the same additional settings, "No TLS Verify", "HTTP2 connection", and "Protect with Access".
  - Access `https://whoami.lab.foo.net` from your browser, make sure that you are prompted to authenticate before the page is served. If you previously authenticated you may not be asked to authenticate again, clear cookies or test from incognito or from a different browser to be sure authentication is enabled.
  - You can now delete the `whoami.foo.net` tunnel.

The Cloudflare configuration is now set, and all further changes can be made locally in Traefik settings by exposing more services to the `lab.foo.net` domain.

E.g. to expose your [Portainer](https://github.com/portainer/portainer) instance to the internet, just modify the HTTP routers rule to include the `lab.foo.net` domain, no Cloudflare changes required, i.e. ``traefik.http.routers.portainer.rule: "Host(`portainer.home.foo.net`) || Host(`portainer.lab.foo.net`)"``. Portainer will now be accessible from the internet via `https://portainer.lab.foo.net` with authenticated access, and locally via `https://portainer.home.foo.net` without authentication required.

Following are configuration code snippets. I use Ansible for deployment, easy enough to convert to the Task files and variables to Docker Compose.

Traefik static YAML config:

```
entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
  websecure:
    address: ":443"
    asDefault: true
    http:
      tls:
        certresolver: "cloudflare"
        domains:
          - main: "foo.net"
            sans:
              - "*.foo.net"
              - "*.home.foo.net"
              - "*.lab.foo.net"

certificatesResolvers:
  cloudflare:
    acme:
      email: "your cloudflare email"
      storage: "/config/acme.json"
      dnsChallenge:
        provider: cloudflare
        delayBeforeCheck: 60
        disablePropagationCheck: true
```

Traefik Ansible container YAML:

```
---
- name: "Create Traefik directory"
  register: configuration
  ansible.builtin.file:
    path: "{{ appdata_dir }}/traefik/config"
    state: directory
    mode: "ugo+rwx"
    owner: nobody
    group: users
    recurse: true

- name: "Copy Traefik Config"
  register: configuration
  ansible.builtin.copy:
    src: "{{ item.src }}"
    dest: "{{ item.dst }}"
  with_items:
    - {
        src: "traefik/",
        dst: "{{ appdata_dir }}/traefik/config/"
      }

- name: "Create Cloudflare ACME file"
  register: configuration
  ansible.builtin.file:
    path: "{{ appdata_dir }}/traefik/config/acme.json"
    state: touch
    mode: "0600"

- name: "Stop Traefik"
  when: configuration.changed
  community.docker.docker_container:
    name: traefik
    state: stopped

- name: "Install Traefik"
  community.docker.docker_container:
    name: traefik
    image: docker.io/traefik:latest
    pull: yes
    hostname: "traefik"
    domainname: "{{ ansible_domain }}"
    restart_policy: unless-stopped
    command:
      - "--configfile=/config/traefik.yml"
    env:
      TZ: "{{ local_timezone }}"
      # CloudFlare DNS Zone API for Let's Encrypt
      CF_DNS_API_TOKEN: "{{ cloudflare_dns_token }}"
    volumes:
      - "{{ appdata_dir }}/traefik/config:/config"
      - "/var/run/docker.sock:/var/run/docker.sock"
    networks:
      - name: "{{ docker_local_network }}"
    etc_hosts:
      # Set host IP for containers using "host" network mode
      "host.docker.internal": "{{ ansible_default_ipv4.address }}"
    published_ports:
      - 80:80 # web
      - 443:443 # websecure
      - 8080:8080 # api
    labels:
      traefik.enable: "true"
      traefik.http.routers.traefik.rule: "Host(`traefik.{{ ansible_domain }}`) || Host(`traefik-{{ ansible_fqdn }}`)"
      traefik.http.routers.traefik.service: "api@internal"

```

WhoAmI Ansible container YAML:

```
---
- name: "Install WhoAmI"
  community.docker.docker_container:
    name: whoami
    image: docker.io/containous/whoami:latest
    pull: yes
    hostname: "whoami"
    domainname: "{{ ansible_domain }}"
    restart_policy: unless-stopped
    user: "{{ user_id }}:{{ group_id }}"
    env:
      TZ: "{{ local_timezone }}"
    networks:
      - name: "{{ docker_local_network }}"
    # published_ports:
    # - 80:80 # HTTP
    labels:
      traefik.enable: "true"
      traefik.http.routers.whoami.rule: "PathPrefix(`/whoami`) || Host(`whoami.{{ ansible_domain }}`) || Host(`whoami.{{ external_domain }}`) || Host(`whoami.{{ external_service_domain }}`)"

```
