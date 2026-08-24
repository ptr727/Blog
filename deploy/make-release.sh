#!/usr/bin/env bash
# Usage: deploy/make-release.sh [deploy-root] [version]

set -euo pipefail

# Directories this script creates come from mkdir and inherit the caller's umask.
# Under umask 077 they land 700, and Caddy runs as an unrelated user that cannot then traverse them.
umask 022

KEEP_RELEASES=10

usage() {
	echo "usage: $0 [deploy-root] [version]" >&2
	echo "       deploy-root defaults to DEPLOY_ROOT, from the environment or \$ENV_FILE" >&2
	echo "       ENV_FILE defaults to ~/.secrets/Blog.local.production.env, and a relative path resolves against ~/.secrets" >&2
	echo "       deploy-root is required when the environment file sets DEPLOY_SSH_HOST, since that root is on another host" >&2
	exit 2
}

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# The release upstream replaced `git whatchanged` with `git log`. Anything older restores
# nothing and exits 0, so this is the floor rather than a preference.
MTIME_MIN=2025.08

# The deploy root and the base URL are the only host-specific values, and they pair per environment.
# ENV_FILE selects the environment, because `set -a` overwrites a value the caller exported.
# The first argument overrides the root, being read after this.
# Files are named ~/.secrets/Blog.<server>.<environment>.env, both words spelled out, so the default names the environment it actually selects rather than being the one file whose name says nothing.
# The leading Blog segment disambiguates this repo's files in ~/.secrets, since other repos on the same host also write there.
DEFAULT_ENV_FILE="$HOME/.secrets/Blog.local.production.env"
ENV_FILE="${ENV_FILE:-$DEFAULT_ENV_FILE}"
# A relative name resolves against ~/.secrets, so it means the same from any working directory.
# Traversal is refused rather than resolved, since a relative name is meant to reach ~/.secrets.
case "$ENV_FILE" in
/*) ;;
*..*)
	echo "ENV_FILE must not traverse: $ENV_FILE" >&2
	exit 1
	;;
*) ENV_FILE="$HOME/.secrets/$ENV_FILE" ;;
esac
if [ -f "$ENV_FILE" ]; then
	echo "==> environment: $ENV_FILE"
	set -a
	# shellcheck disable=SC1090,SC1091
	. "$ENV_FILE"
	set +a
elif [ "$ENV_FILE" != "$DEFAULT_ENV_FILE" ]; then
	# The default file is optional, because CI passes every value explicitly and reads no file.
	# A named file is not, since a typo would fall through to the other environment's root.
	echo "environment file not found: $ENV_FILE" >&2
	exit 1
fi

# Hugo maps HUGO_<KEY> onto config natively, and only that name, so this is the one place SITE_BASE_URL becomes the name Hugo actually reads.
# CI reads no env file here, it already has SITE_BASE_URL in the process environment, so this bridge covers both callers alike.
# The unset branch matters too: an inherited HUGO_BASEURL left over from an older shell export would otherwise survive an unset SITE_BASE_URL and quietly win, since Hugo gives the environment variable precedence over hugo.yaml.
if [ -n "${SITE_BASE_URL:-}" ]; then
	export HUGO_BASEURL="$SITE_BASE_URL"
else
	unset HUGO_BASEURL
fi

# This script installs to a local path, so a remote environment's DEPLOY_ROOT would be built here.
# The guard is on the fallback rather than the variable.
# An explicit first argument names a local path and is always honoured, which is what CI passes.
ROOT_ARG="${1:-}"
if [ -z "$ROOT_ARG" ] && [ -n "${DEPLOY_SSH_HOST:-}" ]; then
	echo "$ENV_FILE names DEPLOY_SSH_HOST=$DEPLOY_SSH_HOST, so its DEPLOY_ROOT is a path on that" >&2
	echo "host and this script would create it here instead. Pass a local path as the first" >&2
	echo "argument to assemble a bundle for shipping, or use a local environment file." >&2
	exit 1
fi

ROOT="${ROOT_ARG:-${DEPLOY_ROOT:-}}"
[ -n "$ROOT" ] || usage

# CI passes the version so a release directory traces back to a commit rather than to a clock.
VERSION="${2:-$(date -u +%Y%m%d-%H%M%S)}"

# Constrained because the value becomes a directory name, a symlink target, and a sed replacement.
# A separator or a traversal would place the release outside releases/ or corrupt the stamp.
case "$VERSION" in
"" | *[!A-Za-z0-9._-]* | *..* | -*)
	echo "version must be one or more of A-Z a-z 0-9 . _ -, without '..' or a leading '-'" >&2
	exit 1
	;;
esac

command -v hugo >/dev/null || {
	echo "hugo not found on PATH" >&2
	exit 1
}

cd "$REPO"

# Git stores no mtimes, so a checkout stamps every file with the moment it was written.
# Without restoring them a release links nothing against the previous one.
# MTIME_RESTORED skips only the restore, for a caller that has already done it.
# The assertion below always runs, so a caller claiming this wrongly still fails.
if [ "${MTIME_RESTORED:-0}" = 1 ]; then
	echo "==> skipping the restore: MTIME_RESTORED says the caller did it, still asserting below"
else
	# How the tool was installed decides which invocation form resolves, so both are tried.
	# The first form meeting MTIME_MIN wins, since a stale install must not veto a current one.
	# Below MTIME_MIN it calls `git whatchanged`, which current git refuses, and it exits 0 anyway.
	# Versions are YYYY.MM, so dropping the dot compares them as integers.
	mtime_probe() {
		# An unmatched grep would abort the script here, leaving the checks below unreachable.
		"$@" --version 2>/dev/null | grep -oE '[0-9]{4}\.[0-9]{2}' | head -1 || true
	}

	MTIME_CMD=()
	mtime_version=""
	mtime_found=""
	for mtime_form in bare subcommand; do
		mtime_try=()
		case "$mtime_form" in
		bare) command -v git-restore-mtime >/dev/null 2>&1 && mtime_try=(git-restore-mtime) ;;
		subcommand) git restore-mtime --version >/dev/null 2>&1 && mtime_try=(git restore-mtime) ;;
		esac
		[ ${#mtime_try[@]} -gt 0 ] || continue

		mtime_try_version="$(mtime_probe "${mtime_try[@]}")"
		if [ -z "$mtime_try_version" ]; then
			mtime_found="${mtime_found}${mtime_found:+, }${mtime_try[*]} (no version reported)"
			continue
		fi
		mtime_found="${mtime_found}${mtime_found:+, }${mtime_try[*]} $mtime_try_version"
		if [ "${mtime_try_version//./}" -ge "${MTIME_MIN//./}" ]; then
			MTIME_CMD=("${mtime_try[@]}")
			mtime_version="$mtime_try_version"
			break
		fi
	done

	if [ ${#MTIME_CMD[@]} -eq 0 ]; then
		if [ -z "$mtime_found" ]; then
			echo "git-restore-mtime not found, as either 'git-restore-mtime' or 'git restore-mtime'" >&2
		else
			echo "no usable git-restore-mtime: found $mtime_found, and $MTIME_MIN or newer is required" >&2
			echo "  before $MTIME_MIN it calls 'git whatchanged', which current git refuses to run, so it" >&2
			echo "  restores nothing and still exits 0 -- every release would silently be a full copy" >&2
		fi
		echo "  it is what makes --link-dest able to link, and a release built without it is a full copy" >&2
		echo "  install git-tools $MTIME_MIN or newer, from https://github.com/MestreLion/git-tools" >&2
		exit 1
	fi

	echo "==> restoring file mtimes with ${MTIME_CMD[*]} $mtime_version"
	"${MTIME_CMD[@]}" static
fi

# The restore is asserted because a failing one reports success and does nothing.
# A restored file cannot be newer than the commit it was dated from.
# Uncommitted paths are excluded, since a working tree may hold one newer than any commit.
mtime_bound="$(git log -1 --format=%ct)"

# An empty porcelain list means every file under static/ is tracked and unchanged.
# A rename emits two NUL records, `XY <new>` then a bare `<old>`, so the second is consumed here.
# Both halves are excluded, since both are uncommitted.
declare -A mtime_dirty=()
while IFS= read -r -d '' entry; do
	mtime_dirty["${entry:3}"]=1
	case "${entry:0:1}" in
	R | C) IFS= read -r -d '' mtime_orig && mtime_dirty["$mtime_orig"]=1 ;;
	esac
done < <(git status --porcelain -z -- static)

if [ ${#mtime_dirty[@]} -eq 0 ]; then
	mtime_newest=$(find static -type f -printf '%T@\n' | sort -n | tail -1 | cut -d. -f1)
else
	echo "==> ${#mtime_dirty[@]} uncommitted path(s) under static/, excluded from the mtime check"
	mtime_newest=0
	while IFS= read -r -d '' f; do
		[ -n "${mtime_dirty[$f]:-}" ] && continue
		t=$(stat -c %Y "$f")
		[ "$t" -gt "$mtime_newest" ] && mtime_newest=$t
	done < <(git ls-files -z -- static)
fi

if [ "$mtime_newest" -gt "$mtime_bound" ]; then
	echo "mtime restore did nothing: static/ holds unmodified files newer than HEAD's commit," >&2
	echo "  so they still carry their checkout time and --link-dest will link nothing" >&2
	exit 1
fi
echo "==> mtimes restored, newest $mtime_newest against HEAD $mtime_bound"

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

# Stamp the release into the config it ships with, so a response names the rules answering.
# A stale config otherwise passes the URL contract against rules that were never shipped.
# Asserted before substituting, because sed reports success when it matches nothing.
# A Caddyfile that lost the placeholder would otherwise ship unstamped, and the live check would
# then blame a dead config watcher for a bundle that never carried a release id.
if ! grep -q "@@RELEASE@@" "$REPO/deploy/Caddyfile"; then
	echo "deploy/Caddyfile carries no @@RELEASE@@ placeholder to stamp" >&2
	exit 1
fi
sed -i "s/@@RELEASE@@/$VERSION/" "$STAGE/Caddyfile"
if grep -q "@@RELEASE@@" "$STAGE/Caddyfile"; then
	echo "release stamp was not substituted into the shipped Caddyfile" >&2
	exit 1
fi

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
