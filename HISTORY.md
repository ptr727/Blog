# Blog

Pieter Viljoen's blog, and the tooling that builds, verifies, and deploys it.

The blog's public address is [blog.insanegenius.com][blog-link].

> Until its DNS records are cut over, that address still serves the old WordPress site, and the site this repository builds is served at `blog.insanegenius.net`.

## Release History

- Version 1.0:
  - The blog moved from WordPress to a Hugo site built and verified by GitHub Actions and served by Caddy. The public address cuts over separately.
  - 108 posts, 2 static pages, 778 media files, converted to a Hugo site in a tree that mirrors the original URLs.
  - Personal data gates: image metadata stripped to an allowlist, declared redactions of faces, addresses, and serial numbers verified by hash, and new posts' text scanned for addresses, coordinates, and other identifiers.
  - Publishes a self-contained release bundle carrying the site, the web-server config, and the redirect maps together, so a rollback reverts the rules and the content they refer to as one unit.

<!-- External -->

[blog-link]: https://blog.insanegenius.com
