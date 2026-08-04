# Blog

Pieter Viljoen's blog, and the tooling that builds, verifies, and deploys it.

## Release History

- Version 1.0:
  - The blog's content, media, URL contract, and deploy tooling live in one repository, under version control and gated by CI.
  - 108 posts and 2 pages as Hugo content, in a tree that mirrors the URLs it serves, with 778 media files carried at their original bytes.
  - The URL contract as committed ground truth: 328 addresses that must render, 917 that must redirect, and 778 legacy image URLs that must resolve, each verified with a live request rather than predicted.
  - CI gates that contract on every pull request, alongside the doc, shell, and workflow linters, with the Hugo version pinned by checksum so a build is reproducible.
  - A self-contained release bundle carrying the site, the web-server config, and the redirect maps together, so a rollback reverts the rules and the content they refer to as one unit.
  - The site is not yet serving its public address. This release is the source and its pipeline, not the cutover.
