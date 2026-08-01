# Blog <!-- omit from toc -->

Pieter Viljoen's blog, and the tooling that builds, verifies, and deploys it.

## Build and Distribution <!-- omit from toc -->

- **Source Code**: [GitHub][blog-link], holding the source, issues, discussions, and CI/CD pipelines.
- **Versioned Releases**: [GitHub Releases][releases-link], version-tagged source archives.

The site itself is not distributed as a package. It is built from this source and deployed to a host over SSH, so a release here is a tagged snapshot of the source rather than an artifact to install.

### Build Status <!-- omit from toc -->

[![Releases Build][releases-build-shield]][actions-link]\
[![Last Commit][last-commit-shield]][commits-link]\
[![License][license-shield]][license]

### Releases <!-- omit from toc -->

[![GitHub Release][github-release-shield]][releases-link]\
[![GitHub Pre-Release][github-pre-release-shield]][releases-link]

### Release Notes <!-- omit from toc -->

**Version: 1.0**:

**Summary**:

- First public release. The content, media, URL contract, and deploy tooling are published as a repository for the first time.
- The URL contract is committed ground truth and gated in CI: 328 addresses that must render, 917 that must redirect, and 778 legacy image URLs that must resolve.
- The site is not yet serving its public address. This release is the source and its pipeline, not the cutover.

See [Release History][history] for the full history.

## Table of Contents <!-- omit from toc -->

- [Use Cases](#use-cases)
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

The site answers far more addresses than it renders pages, because it has served the same domain across earlier platforms whose address shapes are still in search indexes and in other people's links. The extra addresses are redirects the web server satisfies, and they are why the contract is enforced rather than assumed: a missing page is obvious, while a missing redirect is silent and surfaces months later as traffic that stopped arriving. Two gates cover it. One checks the built output before a release is installed, and one checks a running server, because a redirect is the server's job and no build can prove it.

Deployment is a release directory plus a symlink. A build is installed alongside its predecessors, verified, and made live by swapping one link, so a rollback is the same swap in reverse. See [OPERATIONS.md][operations].

## Configuration

| Path | Holds |
| --- | --- |
| [`hugo.yaml`][hugo-config] | site configuration, taxonomy URLs, and the feed name |
| [`checks/`][checks] | the URL contract and the gates that enforce it |
| [`deploy/`][deploy] | the release script, the web-server config, and the redirect maps |

Deploy paths, environment variables, and the server layout are documented in [OPERATIONS.md][operations].

## Questions or Issues

To discuss a post, use [Discussions][discussions-link]. The site itself carries no comment system, deliberately: comments on the old platform were closed years ago, and a static site has nowhere to put them without adding a third-party service that outlives its usefulness. Discussions gives a reader somewhere to respond without the site taking on a moving part.

For a defect in the site or the tooling, such as a broken link, a missing redirect, or a page that renders wrongly, open an issue on [the repository][blog-link].

## Development Environment Setup

The required tools and their install commands are listed in [deploy/README.md][deploy-readme]. Hugo must be the extended build.

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

The deploy root and the base URL come from an untracked `secrets/.env`, copied from [deploy/env.example][env-example]. The whole `secrets/` directory is gitignored, so host-specific values stay out of the published history.

Commits are signed. A greenfield repository signs from its first commit, because the branch ruleset rejects unsigned history and re-signing it afterwards needs a force push the ruleset also blocks.

## 3rd Party Tools

| Tool | Role | License |
| --- | --- | --- |
| [Hugo][hugo-link] | static site generator | Apache-2.0 |
| [PaperMod][papermod-link] | theme, vendored under `themes/` | MIT |
| [Caddy][caddy-link] | web server, serving the built site and the redirects | Apache-2.0 |

## License

See [LICENSE][license].

<!-- Shields -->

[github-pre-release-shield]: https://img.shields.io/github/v/release/ptr727/Blog?include_prereleases&label=GitHub%20Pre-Release&logo=github
[github-release-shield]: https://img.shields.io/github/v/release/ptr727/Blog?logo=github&label=GitHub%20Release
[last-commit-shield]: https://img.shields.io/github/last-commit/ptr727/Blog?logo=github&label=Last%20Commit
[license-shield]: https://img.shields.io/github/license/ptr727/Blog?label=License
[releases-build-shield]: https://img.shields.io/github/actions/workflow/status/ptr727/Blog/publish-release.yml?event=workflow_dispatch&logo=github&label=Releases%20Build

<!-- Workflow -->

[actions-link]: https://github.com/ptr727/Blog/actions

<!-- Repo -->

[blog-link]: https://github.com/ptr727/Blog
[checks]: ./checks/
[commits-link]: https://github.com/ptr727/Blog/commits
[deploy]: ./deploy/
[deploy-readme]: ./deploy/README.md
[discussions-link]: https://github.com/ptr727/Blog/discussions
[env-example]: ./deploy/env.example
[history]: ./HISTORY.md
[hugo-config]: ./hugo.yaml
[license]: ./LICENSE
[operations]: ./OPERATIONS.md
[releases-link]: https://github.com/ptr727/Blog/releases

<!-- External -->

[caddy-link]: https://caddyserver.com/
[hugo-link]: https://gohugo.io/
[papermod-link]: https://github.com/adityatelange/hugo-PaperMod
