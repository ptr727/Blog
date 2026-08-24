# .secrets

Nothing under this directory holds a real value except [`example.env`](./example.env), the
tracked template, and this catalog. `.gitignore` un-ignores exactly those two paths and ignores
everything else here, so a fresh checkout documents its own required shape without ever
exposing one.

## Real values live on the host, never in the checkout

The documented local convention is `~/.secrets/`, not this directory. CI supplies the same
values directly from the GitHub Environment instead, reading no file here at all.
`ENV_FILE=<name> deploy/make-release.sh` resolves a relative `ENV_FILE` against `$HOME/.secrets`,
refuses a traversing one, and defaults to `~/.secrets/Blog.local.production.env`. An absolute
`ENV_FILE` is honored as given rather than resolved against `~/.secrets/`, an escape hatch rather
than the documented shape.
`~/.secrets/` is shared across every repo on the host, so each of this repo's files carries the
`Blog.` prefix:

| File | Selects |
| --- | --- |
| `~/.secrets/Blog.local.production.env` | The default, read when `ENV_FILE` is unset. |
| `~/.secrets/Blog.local.staging.env` | The local staging mirror. |
| `~/.secrets/Blog.vps.production.env` | The VPS production environment. |
| `~/.secrets/Blog.vps.staging.env` | The VPS staging environment. |

Every value each file holds, and what reads it, is described once in
[`ENVIRONMENT.md`](../ENVIRONMENT.md). Start a new one from [`example.env`](./example.env).
