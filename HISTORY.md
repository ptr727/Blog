# Blog

Pieter Viljoen's blog, and the tooling that builds, verifies, and deploys it.

The blog's public address is [blog.insanegenius.com][blog-link].

## Release History

- Version 1.0:
  - The blog moved from WordPress to a Hugo site built and verified by GitHub Actions and served by Caddy. The public addresses cut over separately.
  - 108 posts, 2 static pages, 778 media files, converted to a Hugo site in a tree that mirrors the original URLs.
  - Personal data gates: image metadata stripped to an allowlist, archive redactions declared in a manifest and verified by hash, and the text of the pages and new posts scanned for addresses, coordinates, and other identifiers.
  - Publishes a self-contained release bundle carrying the site, the web-server config, and the redirect maps together, so a rollback reverts the rules and the content they refer to as one unit.
  - The Viljoen family page moved off the blog to its own bilingual site at viljoen.family, shipped and served with the blog.

<!-- External -->

[blog-link]: https://blog.insanegenius.com
