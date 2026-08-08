#!/usr/bin/env bash
# Usage: checks/check-live-urls.sh <base-url>
# Verifies the URL contract against a running server, which is the only thing that exercises the redirects.

set -uo pipefail

BASE="${1:-}"
[ -n "$BASE" ] || {
	echo "usage: $0 <base-url>" >&2
	exit 2
}
BASE="${BASE%/}"

CHECKS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARALLEL="${PARALLEL:-16}"

# A truncated list otherwise turns this into a gate that passes while checking almost nothing.
declare -A FLOOR=(["golden-urls.txt"]=320 ["redirect-urls.txt"]=900 ["golden-media-live.txt"]=8)
for list in golden-urls.txt redirect-urls.txt golden-media-live.txt; do
	n=$(grep -c . "$CHECKS/$list")
	if [ "$n" -lt "${FLOOR[$list]}" ]; then
		echo "FAIL $list: $n URLs, expected at least ${FLOOR[$list]} - the list has been truncated" >&2
		exit 1
	fi
done

FAILED="$(mktemp)"
CURLERR="$(mktemp)"
CURLRC=""
trap 'rm -f "$FAILED" "$CURLERR" ${CURLRC:+"$CURLRC"}' EXIT

# A resource access token opens the proxy's auth gate.
# It goes into a curl config file because bash cannot export an array to the parallel checks.
# A command line is also world-readable in ps output, and this runs 1,245 of them.
if [ -n "${PANGOLIN_ACCESS_TOKEN_ID:-}" ] && [ -n "${PANGOLIN_ACCESS_TOKEN:-}" ]; then
	CURLRC="$(mktemp)"
	chmod 600 "$CURLRC"
	printf 'header = "P-Access-Token-Id: %s"\nheader = "P-Access-Token: %s"\n' \
		"$PANGOLIN_ACCESS_TOKEN_ID" "$PANGOLIN_ACCESS_TOKEN" >"$CURLRC"
	echo "==> sending a Pangolin access token"
elif [ -n "${PANGOLIN_ACCESS_TOKEN_ID:-}" ] || [ -n "${PANGOLIN_ACCESS_TOKEN:-}" ]; then
	# Half a credential is a typo rather than a choice, and it would otherwise fail as an outage.
	echo "FAIL set both PANGOLIN_ACCESS_TOKEN_ID and PANGOLIN_ACCESS_TOKEN, or neither" >&2
	exit 2
fi

# Assembled once here rather than per request, since it is the same for every call.
AUTH=()
[ -n "$CURLRC" ] && AUTH=(-K "$CURLRC")

# Invoked indirectly, through `export -f` and the `xargs bash -c` calls below.
# shellcheck disable=SC2329
check_render() {
	local url="$1" code auth=()
	[ -n "$CURLRC" ] && auth=(-K "$CURLRC")
	code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 30 "${auth[@]}" "$BASE$url")
	[ "$code" = "200" ] || echo "render $url expected 200, got $code" >>"$FAILED"
}

# Invoked indirectly, the same way as check_render above.
# shellcheck disable=SC2329
# The build gate proves the media SET against files on disk. It cannot prove the files
# reached the server or that the server can read them, and until this ran the live check
# requested pages and redirects and never an image.
#
# Status alone is most of the value: a file lost in transfer answers 404, and one whose
# mode went wrong answers 403. The byte count catches the remaining case, a file that
# arrived truncated to nothing, which still answers 200. Content type is asserted because a
# server misconfigured into serving an error page for a missing asset answers 200 as well.
check_media() {
	local url="$1" code len type target auth=() target_auth=()
	[ -n "$CURLRC" ] && auth=(-K "$CURLRC")
	target="$BASE$url"
	target_auth=("${auth[@]}")
	# One hop is followed rather than passed to curl -L, because -L would carry the
	# credential to wherever the rule points. The legacy /wp-content/uploads/ entries reach
	# the image through the @uploads rule, and what this proves is that the image arrives,
	# not that the hop happened.
	code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 30 "${auth[@]}" "$target")
	case "$code" in
	301 | 308)
		target=$(curl -s -o /dev/null -w '%{redirect_url}' --max-time 30 "${auth[@]}" "$target")
		# Same origin boundary as check_redirect, and for the same reason: a rule that one
		# day points off-site must not mail the token there. A bare prefix would also accept
		# a lookalike host registered as an attacker's subdomain.
		target_auth=()
		if [ -n "$CURLRC" ]; then
			case "$target" in
			"$BASE" | "$BASE"/*) target_auth=(-K "$CURLRC") ;;
			esac
		fi
		;;
	esac
	# Command substitution rather than `read < <(...)`, because process substitution discards
	# curl's exit status. It still fails closed either way, since curl writes 000 for
	# http_code on a transport error, measured against a refused connection, a DNS failure
	# and a timeout. What the status buys is a message that says which of the two happened,
	# rather than leaving a reader to infer it from a bare 000.
	local out rc=0
	out=$(curl -s -o /dev/null \
		-w '%{http_code} %{size_download} %{content_type}\n' \
		--max-time 30 "${target_auth[@]}" "$target") || rc=$?
	read -r code len type <<<"$out"
	if [ "$rc" -ne 0 ] || [ "${code:-000}" = "000" ]; then
		echo "media $url no HTTP response: curl exit $rc, transport error or timeout" >>"$FAILED"
		return
	fi
	if [ "$code" != "200" ]; then
		echo "media $url expected 200, got $code" >>"$FAILED"
		return
	fi
	if [ "${len:-0}" -eq 0 ]; then
		echo "media $url answered 200 with an empty body" >>"$FAILED"
		return
	fi
	case "$type" in
	image/*) ;;
	*) echo "media $url answered 200 as $type, expected an image" >>"$FAILED" ;;
	esac
}

# Invoked indirectly, the same way as check_render above.
# shellcheck disable=SC2329
check_redirect() {
	local url="$1" code dest dcode auth=() dest_auth=()
	[ -n "$CURLRC" ] && auth=(-K "$CURLRC")
	code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 30 "${auth[@]}" "$BASE$url")
	case "$code" in
	301 | 308) ;;
	*)
		echo "redirect $url expected 301 or 308, got $code" >>"$FAILED"
		return
		;;
	esac
	# A redirect to a 404 is a broken redirect, so the destination is followed rather than trusted.
	dest=$(curl -s -o /dev/null -w '%{redirect_url}' --max-time 30 "${auth[@]}" "$BASE$url")
	# The credential is only ever sent to the origin it belongs to.
	# A rule that one day redirects off-site must not mail the token there.
	# The match needs an origin boundary, since a bare prefix also accepts a host that merely
	# starts with this one, such as a lookalike registered as an attacker's subdomain.
	if [ -n "$CURLRC" ]; then
		case "$dest" in
		"$BASE" | "$BASE"/*) dest_auth=(-K "$CURLRC") ;;
		esac
	fi
	dcode=$(curl -s -o /dev/null -w '%{http_code}' --max-time 30 "${dest_auth[@]}" "$dest")
	# The media rule lands on an image, and a directory gains a trailing slash, so both answers are accepted.
	case "$dcode" in
	200 | 301 | 308) ;;
	*) echo "redirect $url -> $dest destination answered $dcode" >>"$FAILED" ;;
	esac
}

export -f check_render check_redirect check_media
export BASE FAILED CURLRC

echo "==> $BASE"

# One request before the 1,245, because an auth gate turns a bad credential into a total failure.
# Otherwise the output reads as a vanished site rather than a wrong token.
# Transport failures are separated from HTTP ones, since a name that does not resolve otherwise
# reports as a status code and gets diagnosed as a credential or a symlink.
if ! preflight_headers=$(curl -sS -o /dev/null -D- -w '%{http_code}' --max-time 30 "${AUTH[@]}" "$BASE/" 2>"$CURLERR"); then
	echo "FAIL preflight: $BASE/ could not be reached, so nothing below was checked" >&2
	sed 's/^/     /' "$CURLERR" >&2
	exit 1
fi
preflight="${preflight_headers##*$'\n'}"
header_of() { printf '%s' "$preflight_headers" | grep -i "^$1:" | tr -d '\r' | sed 's/^[^:]*: *//'; }

if [ "$preflight" != "200" ]; then
	echo "FAIL preflight: $BASE/ answered $preflight, expected 200" >&2
	# Own headers with no content behind them is the signature of a dangling current symlink.
	# Caddy retains the last good config when the import disappears, so the headers stay correct.
	# Reporting that as a release mismatch would send someone hunting a deploy that did land.
	if [ -n "$(header_of x-blog-release)$(header_of x-blog-env)" ] && [ "$preflight" = "404" ]; then
		echo "     the server is up and holding a config, but serving no content, so 'current'" >&2
		echo "     probably points at a release that is not on disk. Caddy keeps its last good" >&2
		echo "     config when the import vanishes, which is why the headers below still look" >&2
		echo "     right: env=$(header_of x-blog-env) release=$(header_of x-blog-release)" >&2
	elif [ -n "$CURLRC" ]; then
		echo "     a token was sent, so check the pair is valid for this resource" >&2
	else
		echo "     no token was sent. If this site is behind the auth gate, set" >&2
		echo "     PANGOLIN_ACCESS_TOKEN_ID and PANGOLIN_ACCESS_TOKEN" >&2
	fi
	exit 1
fi

# Nothing in a response body says which environment answered.
# A proxy rule aimed at the wrong container returns a healthy 200 under the right hostname.
if [ -n "${EXPECT_SITE_ENV:-}" ]; then
	got_env=$(printf '%s' "$preflight_headers" | grep -i '^x-blog-env:' | tr -d '\r' | sed 's/^[^:]*: *//')
	if [ "$got_env" != "$EXPECT_SITE_ENV" ]; then
		echo "FAIL preflight: $BASE/ is served by '${got_env:-<no X-Blog-Env header>}', expected '$EXPECT_SITE_ENV'" >&2
		echo "     the hostname resolved to the wrong environment's container, or SITE_ENV is" >&2
		echo "     unset on it. Checking the URL contract now would test the wrong site." >&2
		exit 1
	fi
	echo "==> served by $got_env"
fi

# Nothing else proves the rules answering are the ones just shipped, as no deploy restarts Caddy.
# A stale config serves the previous release's rules while the new content is already live.
# Returns non-zero on a transport failure, and empty on a reply carrying no release header.
# Collapsing the two would report an unreachable host as a config that never reloaded.
read_release() {
	local headers
	headers=$(curl -sS -o /dev/null -D- --max-time 30 "${AUTH[@]}" "$BASE/" 2>"$CURLERR") || return 1
	printf '%s' "$headers" | grep -i '^x-blog-release:' | tr -d '\r' | sed 's/^[^:]*: *//'
	# Explicit, because pipefail carries grep's no-match status out of the function, which would
	# report a reachable host serving no release header as unreachable.
	return 0
}

got_release=$(printf '%s' "$preflight_headers" | grep -i '^x-blog-release:' | tr -d '\r' | sed 's/^[^:]*: *//')
if [ -n "${EXPECT_RELEASE:-}" ]; then
	# The reload is asynchronous, so a check run straight after a deploy races it.
	# Content is live instantly, while rules change on the next poll.
	# The timeout still catches a container that is not watching, which never converges.
	waited=0
	while [ "$got_release" != "$EXPECT_RELEASE" ] && [ "$waited" -lt "${RELOAD_TIMEOUT:-30}" ]; do
		sleep 1
		waited=$((waited + 1))
		if ! got_release=$(read_release); then
			echo "FAIL: $BASE/ became unreachable after ${waited}s of waiting for the reload" >&2
			sed 's/^/     /' "$CURLERR" >&2
			exit 1
		fi
	done
	if [ "$got_release" != "$EXPECT_RELEASE" ]; then
		echo "FAIL preflight: after ${waited}s the rules are from release '${got_release:-<no X-Blog-Release header>}', expected '$EXPECT_RELEASE'" >&2
		echo "     The content symlink moved but the config never followed, so the redirects" >&2
		echo "     below would be checked against a config that was never deployed, and would" >&2
		echo "     pass. Two causes, and the second is the likelier one on a server that has" >&2
		echo "     been working:" >&2
		echo "       - the container is not running 'caddy run --watch' at all; or" >&2
		echo "       - it is, and the watcher is dead. It stops watching permanently after one" >&2
		echo "         failed config load, logs nothing further, and reports healthy throughout." >&2
		echo "         Anything that broke 'current' even briefly, including a test, does this." >&2
		echo "         Only a container restart re-arms it." >&2
		exit 1
	fi
	echo "==> rules from release $got_release${waited:+ (after ${waited}s)}"
elif [ -n "$got_release" ]; then
	echo "==> rules from release $got_release"
fi

n_render=$(grep -c . "$CHECKS/golden-urls.txt")
echo "==> checking $n_render URLs that must render"
grep . "$CHECKS/golden-urls.txt" | xargs -P "$PARALLEL" -I{} bash -c 'check_render "$@"' _ {}

n_redirect=$(grep -c . "$CHECKS/redirect-urls.txt")
echo "==> checking $n_redirect URLs that must redirect"
grep . "$CHECKS/redirect-urls.txt" | xargs -P "$PARALLEL" -I{} bash -c 'check_redirect "$@"' _ {}

n_media=$(grep -c . "$CHECKS/golden-media-live.txt")
echo "==> checking $n_media media URLs that must be served as images"
grep . "$CHECKS/golden-media-live.txt" | xargs -P "$PARALLEL" -I{} bash -c 'check_media "$@"' _ {}

# A count of zero exits non-zero, so a fallback that echoes would append a second zero.
# Swallowing only the exit status keeps the printed count usable.
failures=$(grep -c . "$FAILED" 2>/dev/null || true)
if [ "$failures" -eq 0 ]; then
	echo "PASS - $((n_render + n_redirect + n_media)) URLs honored"
	exit 0
fi

echo
echo "FAIL - $failures of $((n_render + n_redirect + n_media)) URLs"
sort "$FAILED" | head -40
[ "$failures" -gt 40 ] && echo "... and $((failures - 40)) more"
exit 1
