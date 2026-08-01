<!-- omit from toc -->
# Blog

Pieter Viljoen's blog, and the tooling that builds, verifies, and deploys it.

## Build and Distribution

- **Source Code**: this repository, private.

The site is not distributed as a package. It is built from this source and deployed to a host over SSH, so there is no release artifact to download and no registry to pull from.

### Build Status

The repository is private, so status shields would not render for any reader. Build state is read from the Actions tab.

### Release Notes

See [HISTORY.md](./HISTORY.md).

## Table of Contents

- [Build and Distribution](#build-and-distribution)
- [Use Cases](#use-cases)
- [History](#history)
- [Configuration](#configuration)
- [Questions or Issues](#questions-or-issues)
- [Development Environment Setup](#development-environment-setup)
- [3rd Party Tools](#3rd-party-tools)
- [License](#license)

## Use Cases

A personal technical blog, published as a static site and served from a host the author owns. It holds the writing itself and everything needed to put it online, so the site is reproducible from this repository alone.

Three parts, each with a distinct job:

- **The content**, one file per URL, in a tree that mirrors the addresses it serves.
- **The URL contract**, the full set of addresses the site answers, and the gates that prove it still answers them.
- **The deploy tooling**, which builds a release, verifies it, and swaps it into place atomically.

The site answers far more addresses than it renders pages, and the extra ones are redirects the web server satisfies. That is what makes the contract worth enforcing: a missing page is obvious, while a missing redirect is silent and surfaces months later as traffic that stopped arriving. Two gates cover it. One checks the built output before a release is installed, and one checks a running server, because a redirect is the server's job and no build can prove it.

Deployment is a release directory plus a symlink. A build is installed alongside its predecessors, verified, and made live by swapping one link, so a rollback is the same swap in reverse. See [OPERATIONS.md](./OPERATIONS.md).

## History

Context for why the URL contract exists, rather than a description of how the site works today.

The blog has answered at the same domain since 2008, across three platforms. It started on Blogger, moved to WordPress in mid-2012, and is a Hugo static site now. Each move kept the domain and changed the address shapes underneath it, and each earlier platform's addresses are still in search indexes, in feed readers, and in other people's links.

Nothing in a static site generator reproduces those older shapes. They are preserved deliberately, as redirect rules and lookup tables that map an old address onto the page that answers it now. That is the whole reason the repository holds a URL contract and gates it in CI, rather than simply holding content.

## Configuration

| Path | Holds |
| --- | --- |
| [`hugo.yaml`](./hugo.yaml) | site configuration, taxonomy URLs, and the feed name |
| [`checks/`](./checks/) | the URL contract and the gates that enforce it |
| [`deploy/`](./deploy/) | the release script, the web-server config, and the redirect maps |

Deploy paths, environment variables, and the server layout are documented in [OPERATIONS.md](./OPERATIONS.md).

## Questions or Issues

Open an issue on this repository.

## Development Environment Setup

The required tools and their install commands are listed in [deploy/README.md](./deploy/README.md). Hugo must be the extended build.

Build the site and verify it against the URL contract:

```sh
hugo --gc --minify --panicOnWarning
checks/check-url-parity.py public
```

Build a release and verify it against a running server:

```sh
deploy/make-release.sh
checks/check-live-urls.sh "$HUGO_BASEURL"
```

The deploy root and the base URL come from an untracked `secrets/.env`, copied from [deploy/env.example](./deploy/env.example). The whole `secrets/` directory is gitignored, so host-specific values stay out of the published history.

Commits are signed. A greenfield repository signs from its first commit, because the branch ruleset rejects unsigned history and re-signing it afterwards needs a force push the ruleset also blocks.

## 3rd Party Tools

| Tool | Role | License |
| --- | --- | --- |
| [Hugo][hugo-link] | static site generator | Apache-2.0 |
| [PaperMod][papermod-link] | theme, vendored under `themes/` | MIT |
| [Caddy][caddy-link] | web server, serving the built site and the redirects | Apache-2.0 |
| [wp2hugo][wp2hugo-link] | one-time WordPress export conversion | Apache-2.0 |

## License

See [LICENSE](./LICENSE).

<!-- External -->

[caddy-link]: https://caddyserver.com/
[hugo-link]: https://gohugo.io/
[papermod-link]: https://github.com/adityatelange/hugo-PaperMod
[wp2hugo-link]: https://github.com/ashishb/wp2hugo
