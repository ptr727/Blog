#!/usr/bin/env bash
# Usage: deploy/make-release.sh [deploy-root] [version]

set -euo pipefail

# Directories this script creates come from mkdir and inherit the caller's umask.
# Under umask 077 they land 700, and Caddy runs as an unrelated user that cannot then traverse them.
umask 022

KEEP_RELEASES=10

usage() {
	echo "usage: $0 [deploy-root] [version]" >&2
	echo "       deploy-root defaults to DEPLOY_ROOT, from the environment or secrets/.env" >&2
	exit 2
}

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# The deploy root and the base URL are the only host-specific values, and they pair per environment.
# CI passes both explicitly, and a local run reads them from an untracked file under secrets/.
# That directory is gitignored whole, so nothing naming this machine reaches a public repo.
#
# ENV_FILE selects which environment a local run targets, and sourcing is deliberately not
# conditional on the variable being unset: `set -a` exports every assignment in the file, so a
# DEPLOY_ROOT exported by the caller is overwritten rather than respected. Pointing ENV_FILE at
# the environment's own file is therefore the only way to switch environments, and passing the
# root as the first argument is the only way to override one, because that is read after this.
DEFAULT_ENV_FILE="$REPO/secrets/.env"
ENV_FILE="${ENV_FILE:-$DEFAULT_ENV_FILE}"
if [ -f "$ENV_FILE" ]; then
	echo "==> environment: $ENV_FILE"
	set -a
	# shellcheck disable=SC1090,SC1091
	. "$ENV_FILE"
	set +a
elif [ "$ENV_FILE" != "$DEFAULT_ENV_FILE" ]; then
	# The default file is optional, because CI passes every value explicitly and reads no file.
	# A file named on the command line is not: a typo there would otherwise fall through to
	# whatever the ambient environment holds, which on this host is the other site's root.
	echo "environment file not found: $ENV_FILE" >&2
	exit 1
fi

ROOT="${1:-${DEPLOY_ROOT:-}}"
[ -n "$ROOT" ] || usage

# CI passes the version so a release directory traces back to a commit rather than to a clock.
VERSION="${2:-$(date -u +%Y%m%d-%H%M%S)}"

command -v hugo >/dev/null || {
	echo "hugo not found on PATH" >&2
	exit 1
}

cd "$REPO"

# Hugo maps HUGO_<KEY> onto config, so HUGO_BASEURL overrides hugo.yaml with no flag.
# A mirror built without it serves canonical tags, feed links, and permalinks pointing at production.
# The build gate passes either way, so the effective value is logged rather than left implicit.
effective_base="$(hugo config | sed -n 's/^baseurl = //p' | tr -d "'")"
if [ -n "${HUGO_BASEURL:-}" ]; then
	echo "==> baseURL: $effective_base (overridden by HUGO_BASEURL)"
else
	echo "==> baseURL: $effective_base (from hugo.yaml)"
fi

echo "==> building"
rm -rf public
hugo --gc --minify --panicOnWarning

echo "==> verifying the URL contract"
checks/check-url-parity.py public

echo "==> precompressing"
# Text only, because JPEG, PNG, and MP4 are already compressed.
# A compressed sibling larger than the original is worse than none.
# The Caddyfile serves precompressed br gzip, so a missing brotli binary quietly degrades every text response.
have_brotli=0
if command -v brotli >/dev/null; then have_brotli=1; fi

find public -type f \( -name '*.html' -o -name '*.css' -o -name '*.js' \
	-o -name '*.svg' -o -name '*.xml' -o -name '*.json' -o -name '*.txt' \) -print0 |
	while IFS= read -r -d '' f; do
		gzip -9 -k -f "$f"
		# A false test as the last command in a loop body exits the loop non-zero, and pipefail then ends the script.
		# The if form is required here because this branch exists to tolerate a missing binary.
		if [ "$have_brotli" = 1 ]; then
			brotli -q 11 -k -f "$f"
		fi
	done

n_gz=$(find public -name '*.gz' | wc -l)
n_br=$(find public -name '*.br' | wc -l)
echo "    $n_gz gzip, $n_br brotli"
if [ "$have_brotli" = 0 ]; then
	if [ "${REQUIRE_BROTLI:-0}" = 1 ]; then
		echo "REQUIRE_BROTLI is set but brotli is not on PATH, refusing to ship gzip-only" >&2
		exit 1
	fi
	echo "    WARNING: brotli not on PATH. The Caddyfile advertises 'precompressed br gzip'," >&2
	echo "             so every text response falls back to gzip. Install brotli, or set" >&2
	echo "             REQUIRE_BROTLI=1 to make this a hard failure." >&2
fi

STAGE="$ROOT/releases/$VERSION"
if [ -e "$STAGE" ]; then
	echo "release $VERSION already exists at $STAGE" >&2
	exit 1
fi
mkdir -p "$ROOT/releases"

# Hard-link unchanged files so the static tree is stored once across the retained releases.
mkdir -p "$STAGE"
PREV="$(readlink "$ROOT/current" 2>/dev/null || true)"
LINK_SITE=()
LINK_MAPS=()
# A hard link keeps the mode and ownership of the inode it points at.
# A full copy mints fresh inodes, which is the only way to drop a bad one out of the release chain.
if [ "${NO_LINK_DEST:-0}" = 1 ]; then
	echo "==> NO_LINK_DEST set: full copy, no hard links from the previous release"
	PREV=""
fi
if [ -n "$PREV" ] && [ -d "$ROOT/$PREV" ]; then
	echo "==> hard-linking unchanged files from $PREV"
	[ -d "$ROOT/$PREV/site" ] && LINK_SITE=(--link-dest="$ROOT/$PREV/site")
	[ -d "$ROOT/$PREV/maps" ] && LINK_MAPS=(--link-dest="$ROOT/$PREV/maps")
fi

echo "==> installing release $VERSION"
# --delete drops files removed since the previous release, which --link-dest would otherwise carry forward.
# --chmod normalizes modes, because Caddy runs as an unrelated user and reads through the world bits alone.
# --no-g lets the setgid parent assign the group rather than stamping the source group onto the tree.
# D2755 keeps setgid, so the group propagates below the first directory rsync creates.
rsync -a --no-g --chmod=D2755,F644 --delete "${LINK_SITE[@]}" public/ "$STAGE/site/"
rsync -a --no-g --chmod=D2755,F644 --delete "${LINK_MAPS[@]}" "$REPO/deploy/maps/" "$STAGE/maps/"
install -m 644 "$REPO/deploy/Caddyfile" "$STAGE/Caddyfile"

# --chmod and --no-g govern only the files rsync newly transfers.
# A file supplied by --link-dest keeps its original inode's mode, so the result is inspected rather than assumed.
bad_files=$(find "$STAGE/site" "$STAGE/maps" -type f ! -perm -o=r | head -20)
bad_dirs=$(find "$STAGE/site" "$STAGE/maps" -type d ! -perm -o=x | head -20)
if [ -n "$bad_files" ] || [ -n "$bad_dirs" ]; then
	echo "release is not world-readable, so Caddy would 403 on these paths:" >&2
	# Each value holds many lines, and the substitution prefixes every one of them.
	# Parameter expansion replaces within a single string, so it does not express this.
	# shellcheck disable=SC2001
	if [ -n "$bad_files" ]; then echo "$bad_files" | sed 's/^/  file /' >&2; fi
	# shellcheck disable=SC2001
	if [ -n "$bad_dirs" ]; then echo "$bad_dirs" | sed 's/^/  dir  /' >&2; fi
	echo "if these arrived via --link-dest, rebuild once with NO_LINK_DEST=1 to break the chain" >&2
	exit 1
fi

# A link count above 1 means the file is shared with the previous release.
# Without sharing every release costs a full copy, which a compressing filesystem hides from du.
if [ -n "$PREV" ] && [ -d "$ROOT/$PREV/site" ]; then
	shared=$(find "$STAGE/site" -type f -links +1 | wc -l)
	total=$(find "$STAGE/site" -type f | wc -l)
	echo "==> $shared of $total files hard-linked from $PREV"
	if [ "$shared" -eq 0 ]; then
		echo "hard-linking produced no shared files, so every release would cost a full copy" >&2
		exit 1
	fi
fi

# Replacing an existing symlink to a directory in place is not atomic and can put the new link inside the old target.
# A temporary link renamed over the old one is a single rename, so a request never sees a half-written current.
echo "==> swapping current -> releases/$VERSION"
ln -sfn "releases/$VERSION" "$ROOT/.current.tmp"
mv -Tf "$ROOT/.current.tmp" "$ROOT/current"

echo "==> pruning to the newest $KEEP_RELEASES releases"
mapfile -t all < <(find "$ROOT/releases" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)
target="$(basename "$(readlink "$ROOT/current")")"
removed=0
if [ "${#all[@]}" -gt "$KEEP_RELEASES" ]; then
	for old in "${all[@]:0:$((${#all[@]} - KEEP_RELEASES))}"; do
		# Never prune the release current points at, whatever the sort order says.
		[ "$old" = "$target" ] && continue
		rm -rf "${ROOT:?}/releases/$old"
		removed=$((removed + 1))
	done
fi

# A prune that silently keeps everything is a disk-full outage later.
remaining=$(find "$ROOT/releases" -mindepth 1 -maxdepth 1 -type d | wc -l)
if [ "$remaining" -gt "$KEEP_RELEASES" ]; then
	echo "prune failed: $remaining releases remain, expected at most $KEEP_RELEASES" >&2
	exit 1
fi
[ -d "$ROOT/current/site" ] || {
	echo "current/ does not resolve to a release" >&2
	exit 1
}

echo "==> done: $VERSION live, $remaining release(s) retained, $removed pruned"
