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
declare -A FLOOR=(["golden-urls.txt"]=320 ["redirect-urls.txt"]=900)
for list in golden-urls.txt redirect-urls.txt; do
	n=$(grep -c . "$CHECKS/$list")
	if [ "$n" -lt "${FLOOR[$list]}" ]; then
		echo "FAIL $list: $n URLs, expected at least ${FLOOR[$list]} - the list has been truncated" >&2
		exit 1
	fi
done

FAILED="$(mktemp)"
CURLRC=""
trap 'rm -f "$FAILED" ${CURLRC:+"$CURLRC"}' EXIT

# Staging sits behind Pangolin's auth gate, which a resource access token opens.
# The token pair goes into a curl config file rather than onto the command line, for two reasons.
# The check functions run under `export -f` and `xargs bash -c`, and bash cannot export an array,
# so a pair of -H arguments has no way to reach them intact. A command line is also world-readable
# in ps output for as long as the process lives, and this runs 1,245 of them.
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
check_redirect() {
	local url="$1" code dest dcode auth=() dest_auth=()
	[ -n "$CURLRC" ] && auth=(-K "$CURLRC")
	code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 30 "${auth[@]}" "$BASE$url")
	case "$code" in
	301 | 308) ;;
	*)
		echo "redirect $url expected 301, got $code" >>"$FAILED"
		return
		;;
	esac
	# A redirect to a 404 is a broken redirect, so the destination is followed rather than trusted.
	dest=$(curl -s -o /dev/null -w '%{redirect_url}' --max-time 30 "${auth[@]}" "$BASE$url")
	# Every destination in the contract is same-origin, and the credential is only ever sent to
	# the origin it belongs to. A rule that one day redirects off-site must not mail the token there.
	[ -n "$CURLRC" ] && [ "${dest#"$BASE"}" != "$dest" ] && dest_auth=(-K "$CURLRC")
	dcode=$(curl -s -o /dev/null -w '%{http_code}' --max-time 30 "${dest_auth[@]}" "$dest")
	# The media rule lands on an image, and a directory gains a trailing slash, so both answers are accepted.
	case "$dcode" in
	200 | 301 | 308) ;;
	*) echo "redirect $url -> $dest destination answered $dcode" >>"$FAILED" ;;
	esac
}

export -f check_render check_redirect
export BASE FAILED CURLRC

echo "==> $BASE"

# One request before the 1,245, because an auth gate turns a bad credential into a total failure.
# Without this the output is 1,245 lines saying the site is gone, when the site is fine and the
# token is wrong, and the two are indistinguishable from the far end of a CI log.
preflight=$(curl -s -o /dev/null -w '%{http_code}' --max-time 30 "${AUTH[@]}" "$BASE/")
if [ "$preflight" != "200" ]; then
	echo "FAIL preflight: $BASE/ answered $preflight, expected 200" >&2
	if [ -n "$CURLRC" ]; then
		echo "     a token was sent, so check the pair is valid for this resource" >&2
	else
		echo "     no token was sent. If this site is behind the auth gate, set" >&2
		echo "     PANGOLIN_ACCESS_TOKEN_ID and PANGOLIN_ACCESS_TOKEN" >&2
	fi
	exit 1
fi

n_render=$(grep -c . "$CHECKS/golden-urls.txt")
echo "==> checking $n_render URLs that must render"
grep . "$CHECKS/golden-urls.txt" | xargs -P "$PARALLEL" -I{} bash -c 'check_render "$@"' _ {}

n_redirect=$(grep -c . "$CHECKS/redirect-urls.txt")
echo "==> checking $n_redirect URLs that must redirect"
grep . "$CHECKS/redirect-urls.txt" | xargs -P "$PARALLEL" -I{} bash -c 'check_redirect "$@"' _ {}

# A count of zero exits non-zero, so a fallback that echoes would append a second zero.
# Swallowing only the exit status keeps the printed count usable.
failures=$(grep -c . "$FAILED" 2>/dev/null || true)
if [ "$failures" -eq 0 ]; then
	echo "PASS - $((n_render + n_redirect)) URLs honored"
	exit 0
fi

echo
echo "FAIL - $failures of $((n_render + n_redirect)) URLs"
sort "$FAILED" | head -40
[ "$failures" -gt 40 ] && echo "... and $((failures - 40)) more"
exit 1
