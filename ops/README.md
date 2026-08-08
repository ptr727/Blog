# ops

Tooling that runs on the **backup host**, not on the web server and not in CI. One thing lives here today: the pull that copies the VPS's backup set and its access logs off the VPS.

| File | Installs to |
| --- | --- |
| `install.sh` | nothing, it does the installing |
| `vps-backup-pull` | `/usr/local/bin/vps-backup-pull` |
| `vps-backup-pull.service` | `/etc/systemd/system/` |
| `vps-backup-pull.timer` | `/etc/systemd/system/` |
| `vps-backup-pull.env.example` | `/etc/vps-backup-pull.env` |
| `vps-backup-pull.service.d-local.conf.example` | `/etc/systemd/system/vps-backup-pull.service.d/local.conf` |

**The last two are required, not optional, and `install.sh` generates both.** Nothing in this directory names a machine, so the address, the destination paths, and the account are supplied at install time from values this repository already holds. A missing value stops the pull with the name of what is missing rather than falling back to something plausible, since a wrong-but-valid destination is a backup nobody can find. The two `.example` files document the format and are not the install path.

## What it does

Three legs, each skippable, in one direction only:

| Leg | From the VPS | To the backup host |
| --- | --- | --- |
| archives | the encrypted backup set | `DEST` |
| host config | the same non-secret files in plaintext | `DEST/hostconfig` |
| access logs | the rotated edge logs | `LOG_DEST` |

**It is a pull rather than a push, and that is a security property rather than a convenience.** The backup host holds a key the VPS trusts, and the VPS holds no credential reaching anything else. A push would have to invert that, so a compromise of the web server would reach the backups that exist to survive it.

**The plaintext host-config leg exists so a rebuild does not need the encryption key.** That key is not on the backup host and must never be put there, because beside the ciphertext it would make the encryption decorative. The file list is fetched from the VPS rather than duplicated here, so it tracks the host instead of drifting from a copy.

**The log leg is the one with a deadline.** Those logs are deliberately excluded from the encrypted archives, because that set is many full copies with no dedupe and an append-only file would be multiplied across all of them for no recovery benefit. So the VPS's own retention window is the only copy until this runs.

## Three behaviors that look like bugs and are not

- **`--delete` never reaches the log leg**, whatever is passed. It exists to mirror the VPS's archive window, and applying it to an append-only record would delete the only remaining copy at exactly the moment it became the only one. The option array is copied before `--delete` is appended, rather than filtered afterwards, because a filter is a thing to get wrong later.
- **Today's live log is never fetched.** It is still being appended to, so a copy is a torn prefix that the next run fetches again. Rotation is what makes a file eligible. Read the live file over SSH when the analysis covers today.
- **Nothing prunes the destination.** Because the log leg passes no `--delete`, anything the VPS renames or re-compresses after it has been pulled keeps its old name on the backup host permanently, and a count that walks the tree by filename double-counts the overlap. **Read a date from a line's `StartUTC`, never from the filename holding it.** The VPS keeps an append-only `RECONCILE.md` inside the archive directory so a rename travels with the data it explains.

## Install

```sh
ops/install.sh --check    # derive, validate, print, write nothing
ops/install.sh            # the same, then install
```

**Nothing is typed twice.** The address, both destinations, and the account are already known to this checkout, so `install.sh` derives them rather than asking: `VPS_SSH_HOST`, `BACKUP_ARCHIVE_ROOT` and `LOG_ARCHIVE_ROOT` come from `secrets/<server>.<environment>.env` under the names the log review uses, the account is whoever runs the script, the group is read from the destination, and the mount is resolved with `findmnt`. That is also what keeps the two vocabularies from drifting, since one is generated from the other rather than maintained beside it.

**Run it as the account that will own the backup, not under `sudo`.** It refuses to start as root, because that account's name and its SSH key are what the unit is built around. It calls `sudo` itself for the steps that need it, so expect one password prompt.

**Two derivations are worth knowing, because the obvious answer is wrong for both.** The group comes from the destination rather than from `id -gn`, since `Group=` sets the process's primary group and the account's own group is usually not the one owning the backup tree. And `RequiresMountsFor=` needs the mount point rather than the destination path below it.

**`--check` needs no root and writes nothing.** It prints both generated files, reports whether each would be created or already matches, and proves the VPS answers over SSH. Run it first. It reports "needs root to compare" rather than "already correct" when it cannot read an existing file, because an installer that claims agreement it could not verify is the failure this is written against.

Re-running is safe and is how a changed value is applied. A file that already matches is reported and left alone, and one that differs stops the run until `--force`.

**The timer's hour sits behind both producers on the VPS rather than beside them**, because the VPS rotates its log and writes its archive at times of its own. Pulling before the day's archive exists fetches the previous one and reports success, which is the failure mode that looks like a working backup. `Persistent=true` covers a host that was powered off when the timer should have fired.

**Run it as the account that owns the destination, never under `sudo`.** It authenticates with that user's SSH key and writes into a tree that user owns. Under `sudo` it uses root's identity, which the VPS does not trust, and starts mixing root-owned files into a user-owned backup tree. That is why it installs to `bin/` rather than `sbin/`, why the drop-in sets `User=`, and why the script refuses to start as root rather than warning about it.

## Checking it, without trusting anything written down

```sh
journalctl -u vps-backup-pull.service -o short-iso | grep done
systemctl list-timers vps-backup-pull.timer --all
```

**A journal with one entry is not evidence of one copy.** The script can be run directly as well as by its timer, and a direct run writes no service record. Directory mtimes on the backup host are the copy times, where the file mtimes are the VPS's, so those are what to read when establishing when something arrived.

## Variables

Every path is a variable, so a host states its own layout rather than editing a file git owns. They are listed with their meanings in [`vps-backup-pull.env.example`](./vps-backup-pull.env.example), and the two `systemd` settings that cannot come from an environment file are in [`vps-backup-pull.service.d-local.conf.example`](./vps-backup-pull.service.d-local.conf.example).

**Two of them are named a second time in Blog's own `secrets/` file, and the pairs must agree.** This side writes, and the log review reads. `DEST` here is `BACKUP_ARCHIVE_ROOT` there, and `LOG_DEST` here is `LOG_ARCHIVE_ROOT` there. The correspondence, and why the two vocabularies exist rather than one, is in [`OPERATIONS.md`](../OPERATIONS.md) "Working With the VPS".

## This directory is the source

Edit the copy here and install it. Nothing else is a source, and a copy found on a host is an installed artifact rather than a place to make a change.
