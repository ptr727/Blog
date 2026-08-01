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
trap 'rm -f "$FAILED"' EXIT

# Invoked indirectly, through `export -f` and the `xargs bash -c` calls below.
# shellcheck disable=SC2329
check_render() {
	local url="$1" code
	code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 30 "$BASE$url")
	[ "$code" = "200" ] || echo "render $url expected 200, got $code" >>"$FAILED"
}

# Invoked indirectly, the same way as check_render above.
# shellcheck disable=SC2329
check_redirect() {
	local url="$1" code dest dcode
	code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 30 "$BASE$url")
	case "$code" in
	301 | 308) ;;
	*)
		echo "redirect $url expected 301, got $code" >>"$FAILED"
		return
		;;
	esac
	# A redirect to a 404 is a broken redirect, so the destination is followed rather than trusted.
	dest=$(curl -s -o /dev/null -w '%{redirect_url}' --max-time 30 "$BASE$url")
	dcode=$(curl -s -o /dev/null -w '%{http_code}' --max-time 30 "$dest")
	# The media rule lands on an image, and a directory gains a trailing slash, so both answers are accepted.
	case "$dcode" in
	200 | 301 | 308) ;;
	*) echo "redirect $url -> $dest destination answered $dcode" >>"$FAILED" ;;
	esac
}

export -f check_render check_redirect
export BASE FAILED

echo "==> $BASE"

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
