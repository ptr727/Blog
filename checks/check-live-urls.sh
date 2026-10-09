#!/usr/bin/env bash
# Usage: checks/check-live-urls.sh <base-url>
#        checks/check-live-urls.sh --print-sample
# Verifies the URL contract against a running server, which is the only thing that exercises the redirects.

set -uo pipefail

PRINT_SAMPLE=''
BASE="${1:-}"
if [ "$BASE" = "--print-sample" ]; then
	PRINT_SAMPLE=1
	BASE=''
else
	[ -n "$BASE" ] || {
		echo "usage: $0 <base-url> | --print-sample" >&2
		exit 2
	}
fi
BASE="${BASE%/}"

case "${SAMPLE_CONTRACT:-}" in
'' | 1) ;;
*)
	echo "FAIL SAMPLE_CONTRACT takes 1 or nothing -- got '$SAMPLE_CONTRACT'" >&2
	exit 2
	;;
esac
SAMPLE="${SAMPLE_CONTRACT:-}"
[ -n "$PRINT_SAMPLE" ] && SAMPLE=1

CHECKS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARALLEL="${PARALLEL:-16}"

# A truncated list otherwise turns this into a gate that passes while checking almost nothing.
declare -A FLOOR=(["golden-urls.txt"]=320 ["redirect-urls.txt"]=900 ["golden-media-live.txt"]=8)
for list in golden-urls.txt redirect-urls.txt golden-media-live.txt; do
	# The count is validated before it is compared.
	# An unreadable list makes `grep -c` yield nothing, and `[ "" -lt N ]` is a syntax error that evaluates false, so the guard against a truncated list would itself be skipped and the run would pass having checked nothing.
	[ -r "$CHECKS/$list" ] || {
		echo "FAIL $list: not readable at $CHECKS/$list" >&2
		exit 1
	}
	n=$(grep -c . "$CHECKS/$list")
	case "$n" in
	'' | *[!0-9]*)
		echo "FAIL $list: could not count URLs, got '$n'" >&2
		exit 1
		;;
	esac
	if [ "$n" -lt "${FLOOR[$list]}" ]; then
		echo "FAIL $list: $n URLs, expected at least ${FLOOR[$list]} - the list has been truncated" >&2
		exit 1
	fi
done

FAMILY_PAGES=("/|The Viljoen Family" "/en/|The Viljoen Family" "/af/|Die Viljoen-familie")

# Production's edge bans a client that requests more than 40 distinct pages in a burst, so its deploy checks a few URLs per class rather than the whole contract.
# Staging and the local mirrors check every URL, which is where the contract itself is proven.
SAMPLE_PER_CLASS=1
SAMPLE_MAX_PATHS=30
SAMPLE_MAX_STATICS=8

# Each classifier sets CLASS rather than printing it, since a subshell per URL costs seconds across the redirect list.
# The redirect classes are the rows of deploy/README.md's table, tested in the Caddyfile's order, because two of its patterns overlap.
# shellcheck disable=SC2329 # invoked through sample_list
redirect_class() {
	local url="$1" path="${1%%\?*}" query='' date='/[0-9]{4}/[0-9]{2}/[0-9]{2}/[^/]+'
	[ "$path" = "$url" ] || query="${url#*\?}"
	local feed_type="^(${date}(/[^/]+)?|/(tag|category|author)/[^/]+|/comments|/about)?/feed/(atom|rss|rss2|rdf)/?$"
	local post_child_feed="^${date}/[^/]+/feed/?$" post_child="^${date}/[^/]+/?$"
	local blogger_archive='^/[0-9]{4}_[0-9]{2}_01_archive\.html$' blogger_page='^/p/[^/]+\.html$'
	local date_archive='^/[0-9]{4}(/[0-9]{2})?(/page/[0-9]+)?/?$' author='^/author/[^/]+(/(page/[0-9]+|feed))?/?$'
	if [[ "&$query" == *'&p='* ]]; then
		CLASS='@post_id'
	elif [[ $path =~ $feed_type ]]; then
		CLASS='@feed_type'
	elif [[ $path =~ $post_child_feed ]]; then
		CLASS='@post_child_feed'
	elif [[ $path =~ $post_child ]]; then
		CLASS='@post_child'
	elif [[ $path =~ ^/(tag|category)/[^/]+/feed/?$ ]]; then
		CLASS='@term_feed'
	elif [[ $path =~ ^/(feed|comments/feed|about/feed)/?$ ]]; then
		CLASS='@site_feed'
	elif [[ $path =~ ^/feeds/posts/default/?$ ]]; then
		CLASS='@blogger_feed'
	elif [[ $path =~ $blogger_archive ]]; then
		CLASS='@blogger_archive'
	elif [[ $path =~ $blogger_page ]]; then
		CLASS='@blogger_page'
	elif [[ $path =~ $date_archive ]]; then
		CLASS='@date_archive'
	elif [[ $path =~ $author ]]; then
		CLASS='@author'
	# The four map classes share one directive, and their key shapes tell them apart.
	elif [[ $path =~ ^/feeds/[^/]+/comments/default/?$ ]]; then
		CLASS='@mapped via blogger.map (comment feed)'
	elif [[ $path == *.html ]]; then
		CLASS='@mapped via blogger.map (post)'
	elif [[ $path =~ ^/(tag|category)/[^/]+/?$ ]]; then
		CLASS='@mapped via terms.map'
	else
		CLASS='@mapped via slugs.map'
	fi
}

# A shape nothing here names lands in its own class, so a new kind of page is sampled rather than skipped.
# shellcheck disable=SC2329 # invoked through sample_list
render_class() {
	local url="$1" post='^/[0-9]{4}/[0-9]{2}/[0-9]{2}/[^/]+/$'
	if [ "$url" = / ]; then
		CLASS='home'
	elif [[ $url =~ ^/page/[0-9]+/$ ]]; then
		CLASS='home pagination'
	elif [[ $url =~ $post ]]; then
		CLASS='post'
	elif [[ $url =~ ^/tag/[^/]+/$ ]]; then
		CLASS='tag archive'
	elif [[ $url =~ ^/category/[^/]+/$ ]]; then
		CLASS='category archive'
	elif [[ $url =~ ^/(tag|category)/[^/]+/page/[0-9]+/$ ]]; then
		CLASS='term pagination'
	elif [[ $url =~ ^/[^/]+/$ ]]; then
		CLASS='page'
	else
		CLASS='other'
	fi
}

# shellcheck disable=SC2329 # invoked through sample_list
media_class() {
	case "$1" in
	/media/*) CLASS='media' ;;
	/external/*) CLASS='external' ;;
	/wp-content/uploads/*) CLASS='legacy upload' ;;
	*) CLASS='other' ;;
	esac
}

# Appends "<kind><TAB><class><TAB><class size><TAB><url>" to SAMPLE_PLAN for the first SAMPLE_PER_CLASS URLs of each class.
# File order rather than a random pick, so two runs of one release request the same URLs and a failure reproduces.
sample_list() {
	local kind="$1" classify="$2" file="$3" url class
	local -A size=() taken=()
	local -a order=() picks=()
	while IFS= read -r url; do
		[ -n "$url" ] || continue
		"$classify" "$url"
		[ -n "${size[$CLASS]:-}" ] || order+=("$CLASS")
		size[$CLASS]=$((${size[$CLASS]:-0} + 1))
		if [ "${taken[$CLASS]:-0}" -lt "$SAMPLE_PER_CLASS" ]; then
			taken[$CLASS]=$((${taken[$CLASS]:-0} + 1))
			picks+=("$CLASS"$'\t'"$url")
		fi
	done <"$file"
	for url in "${picks[@]}"; do
		class="${url%%$'\t'*}"
		SAMPLE_PLAN+=("$kind"$'\t'"$class"$'\t'"${size[$class]}"$'\t'"${url#*$'\t'}")
	done
}

if [ -n "$SAMPLE" ]; then
	SAMPLE_PLAN=()
	sample_list render render_class "$CHECKS/golden-urls.txt"
	sample_list redirect redirect_class "$CHECKS/redirect-urls.txt"
	sample_list media media_class "$CHECKS/golden-media-live.txt"
	for page in "${FAMILY_PAGES[@]}"; do
		SAMPLE_PLAN+=("family"$'\t'"family page"$'\t'"${#FAMILY_PAGES[@]}"$'\t'"${page%%|*}")
	done

	# The budget counts what the edge counts, distinct non-static paths per host, with the preflight's / among them.
	# A sampled redirect is not followed, so each costs one path, and a media URL costs at most two requests, since a legacy one takes a hop.
	declare -A sample_paths=(["blog /"]=1)
	sample_statics=0
	for entry in "${SAMPLE_PLAN[@]}"; do
		IFS=$'\t' read -r kind _ _ url <<<"$entry"
		case "$kind" in
		media) sample_statics=$((sample_statics + 2)) ;;
		family) sample_paths["family $url"]=1 ;;
		*) sample_paths["blog $url"]=1 ;;
		esac
	done
	if [ -n "$PRINT_SAMPLE" ]; then
		printf '%s\n' "${SAMPLE_PLAN[@]}"
		printf 'budget\tdistinct non-static paths\t%s\t%s\n' "${#sample_paths[@]}" "$SAMPLE_MAX_PATHS"
		printf 'budget\tstatic requests\t%s\t%s\n' "$sample_statics" "$SAMPLE_MAX_STATICS"
	fi
	# Asserted before the first request, so a later edit that grows the sample fails here rather than getting the runner banned.
	if [ "${#sample_paths[@]}" -gt "$SAMPLE_MAX_PATHS" ] || [ "$sample_statics" -gt "$SAMPLE_MAX_STATICS" ]; then
		echo "FAIL the sample would request ${#sample_paths[@]} distinct non-static paths and $sample_statics statics, over its budget of $SAMPLE_MAX_PATHS and $SAMPLE_MAX_STATICS" >&2
		exit 1
	fi
	[ -n "$PRINT_SAMPLE" ] && exit 0
fi

FAILED="$(mktemp)"
CURLERR="$(mktemp)"
CURLRC=""
FAMILY_CURLRC=""
CHECKRC="$(mktemp)"
FAMILY_BODY="$(mktemp)"
FAMILY_HEAD="$(mktemp)"
SAMPLE_DIR=""
trap 'rm -f "$FAILED" "$CURLERR" "$CHECKRC" "$FAMILY_BODY" "$FAMILY_HEAD" ${CURLRC:+"$CURLRC"} ${FAMILY_CURLRC:+"$FAMILY_CURLRC"}; [ -z "$SAMPLE_DIR" ] || rm -rf "$SAMPLE_DIR"' EXIT

RENDER_SRC="$CHECKS/golden-urls.txt"
REDIRECT_SRC="$CHECKS/redirect-urls.txt"
MEDIA_SRC="$CHECKS/golden-media-live.txt"
if [ -n "$SAMPLE" ]; then
	SAMPLE_DIR="$(mktemp -d)"
	RENDER_SRC="$SAMPLE_DIR/render" REDIRECT_SRC="$SAMPLE_DIR/redirect" MEDIA_SRC="$SAMPLE_DIR/media"
	for entry in "${SAMPLE_PLAN[@]}"; do
		IFS=$'\t' read -r kind _ _ url <<<"$entry"
		[ "$kind" = family ] || printf '%s\n' "$url" >>"$SAMPLE_DIR/$kind"
	done
	echo "==> sampling the contract by class, ${#sample_paths[@]} distinct non-static paths"
fi

# Every request this script makes announces itself as synthetic, so the server's log can be filtered down to real visitors with one clause.
# Agreed with the host side, whose Traefik captures the field.
#
# The value carries provenance rather than a boolean, `<source>/<id>`, because "which run produced this 404" is then a one-line query against the log.
#
# The run attempt is part of the id deliberately.
# A re-run of a failed workflow keeps the same GITHUB_RUN_ID and gets a new GITHUB_RUN_ATTEMPT, so the id alone would merge a retried run into the run it was retrying, which is exactly the case someone reads the log to understand.
#
# It is forgeable and it gates nothing.
# Absence of the header is not proof of a human either: a scanner sends no header and neither does a forged request.
# It must never reach auth, rate limiting, robots handling, or caching.
if [ -z "${CHECK_TAG:-}" ]; then
	if [ -n "${GITHUB_RUN_ID:-}" ]; then
		CHECK_TAG="github/${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT:-1}"
	else
		CHECK_TAG="proxmox/manual"
	fi
fi
# Validated before it is written, because this lands in a curl config file and a curl config file is a list of options rather than a list of headers.
# A value carrying a newline ends the header line and starts a new directive, so an override could add an option nobody typed.
# A value carrying a double quote ends the quoted string with the same result.
# A tag never needs either, so refusing both loses nothing.
#
# The shape is enforced and not merely described, because the whole value of provenance over a boolean is that the log can be grouped by source, and `select(.tag | startswith("github/"))` is only reliable if every tag actually has a source half.
# A charset check alone would accept `smoke`, `/smoke` and `a/b/c`, each of which reads as conforming and breaks that query.
# Exactly one slash, both halves non-empty, from a deliberately narrow character set.
#
# The range `A-Za-z0-9` is collation-dependent, so the allowlist below is only ASCII-strict because `globasciiranges` happens to be on.
# Set explicitly rather than inherited, since a guarantee resting on a build default is not a guarantee.
# Demonstrated rather than assumed: with the option off, under en_US.UTF-8, both `a` followed by e-acute (U+00E9) and `a` followed by its capital (U+00C9) are ACCEPTED by this pattern, and with it on they are rejected.
# Checked, because this script runs under `set -uo pipefail` and not `-e`, so an unsupported option would print to stderr, return 1, and be stepped straight over, leaving the validation locale-dependent underneath a comment promising it is not.
# `shopt` returns 1 on an unknown option name, which is what makes this testable rather than decorative.
shopt -s globasciiranges || {
	echo "FAIL this shell does not support globasciiranges, so the character allowlist below would be locale-dependent" >&2
	exit 2
}
case "$CHECK_TAG" in
*[!A-Za-z0-9._/-]*)
	echo "FAIL CHECK_TAG may contain only letters, digits, and the characters '. _ - /' -- got '$CHECK_TAG'" >&2
	exit 2
	;;
*/*/*)
	echo "FAIL CHECK_TAG takes exactly one slash, as <source>/<id> -- got '$CHECK_TAG'" >&2
	exit 2
	;;
/* | */)
	echo "FAIL CHECK_TAG needs a non-empty half either side of the slash -- got '$CHECK_TAG'" >&2
	exit 2
	;;
*/*) ;;
*)
	echo "FAIL CHECK_TAG must be <source>/<id>, such as proxmox/media-dev -- got '$CHECK_TAG'" >&2
	exit 2
	;;
esac
printf 'header = "X-Blog-Check: %s"\n' "$CHECK_TAG" >"$CHECKRC"
echo "==> tagging requests X-Blog-Check: $CHECK_TAG"

# A resource access token opens the proxy's auth gate.
# It goes into a curl config file because bash cannot export an array to the parallel checks.
# A command line is also world-readable in ps output, and every request would carry it.
# Sets the variable named by the third argument to the file's path, and leaves it empty for a public site that sets neither half of the pair.
token_rc() {
	local id_name="$1" token_name="$2" rc_name="$3" name
	if [ -n "${!id_name:-}" ] && [ -n "${!token_name:-}" ]; then
		# Same hazard as CHECK_TAG above and the same reason, but a narrower rule, because the grammar of a credential is the issuer's to define and not this script's.
		# Only a line ending is refused, since no HTTP header value can carry one, so a token containing one is a paste accident rather than a token.
		# Reported without echoing the value, since it is a secret and the finding is its shape.
		#
		# Carriage return counts as a line ending here as much as newline does.
		# Header injection is classically CRLF, and a lone CR is enough on its own, so refusing LF while allowing CR would leave the shape this guard exists for.
		for name in "$id_name" "$token_name"; do
			case "${!name}" in
			*$'\n'* | *$'\r'*)
				echo "FAIL $name contains a newline or a carriage return, neither of which can appear in an HTTP header value" >&2
				return 2
				;;
			esac
		done
		# Assigned before the token is written, so no file holding a token escapes the exit trap.
		printf -v "$rc_name" '%s' "$(mktemp)"
		chmod 600 "${!rc_name}"
		# A backslash or a double quote is legal in a header, but curl reads each as special inside a quoted config value, so each is escaped rather than refused.
		local id_value="${!id_name}" token_value="${!token_name}"
		id_value="${id_value//\\/\\\\}" token_value="${token_value//\\/\\\\}"
		printf 'header = "P-Access-Token-Id: %s"\nheader = "P-Access-Token: %s"\n' \
			"${id_value//\"/\\\"}" "${token_value//\"/\\\"}" >"${!rc_name}"
	elif [ -n "${!id_name:-}" ] || [ -n "${!token_name:-}" ]; then
		# Half a credential is a typo rather than a choice, and it would otherwise fail as an outage.
		echo "FAIL set both $id_name and $token_name, or neither" >&2
		return 2
	fi
}

token_rc SITE_AUTH_TOKEN_ID SITE_AUTH_TOKEN CURLRC || exit 2

# A token opens exactly one proxy resource, so the family host needs a pair of its own.
FAMILY_BASE="${SITE_EXTRA_BASE_URL:-}"
FAMILY_BASE="${FAMILY_BASE%/}"
token_rc SITE_EXTRA_AUTH_TOKEN_ID SITE_EXTRA_AUTH_TOKEN FAMILY_CURLRC || exit 2
if [ -n "$FAMILY_CURLRC" ] && [ -z "$FAMILY_BASE" ]; then
	echo "FAIL SITE_EXTRA_AUTH_TOKEN_ID and SITE_EXTRA_AUTH_TOKEN are set, but SITE_EXTRA_BASE_URL is not" >&2
	exit 2
fi

# A token sent over plain HTTP is readable by anyone on the path, so a pair is only ever sent to an HTTPS origin.
for pair in "CURLRC BASE SITE_AUTH_TOKEN" "FAMILY_CURLRC FAMILY_BASE SITE_EXTRA_AUTH_TOKEN"; do
	read -r rc_name base_name token_name <<<"$pair"
	[ -n "${!rc_name}" ] || continue
	# Lowercase only, since the same-origin tests below compare against the lowercase scheme curl reports.
	case "${!base_name}" in
	https://*) ;;
	*)
		echo "FAIL ${token_name}_ID and $token_name are set, but ${!base_name} does not start with https://, so the token could travel in the clear" >&2
		exit 2
		;;
	esac
done
[ -n "$CURLRC" ] && echo "==> sending a Pangolin access token"

# Assembled once here rather than per request, since it is the same for every call.
# The check tag is unconditional and the token is not, which is why they are two files rather than one.
# Every request should be attributable.
# Only a same-origin request may carry the credential, and folding them together would make the tag inherit that restriction for no reason, or the token lose it, depending on which way it was folded.
AUTH=(-K "$CHECKRC")
[ -n "$CURLRC" ] && AUTH+=(-K "$CURLRC")

# Every curl call passes -q first, the only position where curl skips the user's .curlrc.

# Invoked indirectly, through `export -f` and the `xargs bash -c` calls below.
# shellcheck disable=SC2329
# Retries only a request that got no status line, since a live server drops the odd connection.
# A real status is never retried, because one that clears on a second try is still a fault this check reports.
curl_retry() {
	local out rc=0
	out=$(curl "$@") || rc=$?
	case "$out" in
	'' | 000*)
		sleep 2
		rc=0
		out=$(curl "$@") || rc=$?
		;;
	esac
	printf '%s\n' "$out"
	return "$rc"
}

# Invoked indirectly, the same way as curl_retry above.
# shellcheck disable=SC2329
transfer_failure() {
	local code="$1" rc="$2"
	if [ "${code:-000}" = "000" ]; then
		echo "gave no HTTP response after one retry: curl exit $rc, transport error or timeout"
	elif [ "$rc" -ne 0 ]; then
		echo "answered $code but the transfer failed: curl exit $rc"
	fi
}

# Invoked indirectly, the same way as curl_retry above.
# shellcheck disable=SC2329
check_render() {
	local url="$1" code why rc=0 auth=(-K "$CHECKRC")
	[ -n "$CURLRC" ] && auth+=(-K "$CURLRC")
	code=$(curl_retry -q -s -o /dev/null -w '%{http_code}' --max-time 30 "${auth[@]}" "$BASE$url") || rc=$?
	why=$(transfer_failure "$code" "$rc")
	if [ -n "$why" ]; then
		echo "render $url $why" >>"$FAILED"
		return
	fi
	[ "$code" = "200" ] || echo "render $url expected 200, got $code" >>"$FAILED"
}

# Invoked indirectly, the same way as check_render above.
# shellcheck disable=SC2329
# The build gate proves the media SET against files on disk.
# It cannot prove the files reached the server or that the server can read them, and until this ran the live check requested pages and redirects and never an image.
#
# Status alone is most of the value: a file lost in transfer answers 404, and one whose mode went wrong answers 403.
# The byte count catches the remaining case, a file that arrived truncated to nothing, which still answers 200.
# Content type is asserted because a server misconfigured into serving an error page for a missing asset answers 200 as well.
check_media() {
	local url="$1" what="media $1" out code len target type why rc=0 auth=(-K "$CHECKRC") target_auth=(-K "$CHECKRC")
	[ -n "$CURLRC" ] && auth+=(-K "$CURLRC")
	# The redirect URL gets a line of its own, because an empty one would let read shift the type into its place.
	local format='%{http_code} %{size_download}\n%{redirect_url}\n%{content_type}\n'
	# Command substitution rather than `read < <(...)`, because process substitution discards curl's exit status.
	out=$(curl_retry -q -s -o /dev/null -w "$format" --max-time 30 "${auth[@]}" "$BASE$url") || rc=$?
	{
		read -r code len
		read -r target
		read -r type
	} <<<"$out"
	# One hop is followed rather than passed to curl -L, because -L would carry the credential to wherever the rule points.
	# The legacy /wp-content/uploads/ entries reach the image through the @uploads rule, and what this proves is that the image arrives, not that the hop happened.
	case "$code" in
	301 | 308)
		why=$(transfer_failure "$code" "$rc")
		if [ -n "$why" ]; then
			echo "$what $why" >>"$FAILED"
			return
		fi
		if [ -z "$target" ]; then
			echo "$what answered $code with no usable Location" >>"$FAILED"
			return
		fi
		# Same origin boundary as check_redirect, and for the same reason: a rule that one day points off-site must not mail the token there.
		# A bare prefix would also accept a lookalike host registered as an attacker's subdomain.
		if [ -n "$CURLRC" ]; then
			case "$target" in
			"$BASE" | "$BASE"/*) target_auth+=(-K "$CURLRC") ;;
			esac
		fi
		what="media $url -> $target"
		rc=0
		out=$(curl_retry -q -s -o /dev/null -w "$format" --max-time 30 "${target_auth[@]}" "$target") || rc=$?
		{
			read -r code len
			read -r _
			read -r type
		} <<<"$out"
		;;
	esac
	why=$(transfer_failure "$code" "$rc")
	if [ -n "$why" ]; then
		echo "$what $why" >>"$FAILED"
		return
	fi
	if [ "$code" != "200" ]; then
		echo "$what expected 200, got $code" >>"$FAILED"
		return
	fi
	if [ "${len:-0}" -eq 0 ]; then
		echo "$what answered 200 with an empty body" >>"$FAILED"
		return
	fi
	case "$type" in
	image/*) ;;
	*) echo "$what answered 200 as $type, expected an image" >>"$FAILED" ;;
	esac
}

# Invoked indirectly, the same way as check_render above.
# shellcheck disable=SC2329
check_redirect() {
	local url="$1" out code dest dcode why rc=0 auth=(-K "$CHECKRC") dest_auth=(-K "$CHECKRC")
	[ -n "$CURLRC" ] && auth+=(-K "$CURLRC")
	# One request reads both fields, so a second fetch failing in transit cannot pass an empty destination on as a broken target.
	out=$(curl_retry -q -s -o /dev/null -w '%{http_code} %{redirect_url}\n' --max-time 30 "${auth[@]}" "$BASE$url") || rc=$?
	read -r code dest <<<"$out"
	why=$(transfer_failure "$code" "$rc")
	if [ -n "$why" ]; then
		echo "redirect $url $why" >>"$FAILED"
		return
	fi
	case "$code" in
	301 | 308) ;;
	*)
		echo "redirect $url expected 301 or 308, got $code" >>"$FAILED"
		return
		;;
	esac
	if [ -z "$dest" ]; then
		echo "redirect $url answered $code with no usable Location" >>"$FAILED"
		return
	fi
	# A sampled run proves the rule fired and leaves the destination to the full contract, which halves its paths.
	[ -n "$SAMPLE" ] && return
	# A redirect to a 404 is a broken redirect, so the destination is followed rather than trusted.
	# The credential is only ever sent to the origin it belongs to.
	# A rule that one day redirects off-site must not mail the token there.
	# The match needs an origin boundary, since a bare prefix also accepts a host that merely starts with this one, such as a lookalike registered as an attacker's subdomain.
	if [ -n "$CURLRC" ]; then
		case "$dest" in
		"$BASE" | "$BASE"/*) dest_auth+=(-K "$CURLRC") ;;
		esac
	fi
	rc=0
	dcode=$(curl_retry -q -s -o /dev/null -w '%{http_code}' --max-time 30 "${dest_auth[@]}" "$dest") || rc=$?
	why=$(transfer_failure "$dcode" "$rc")
	if [ -n "$why" ]; then
		echo "redirect $url -> $dest destination $why" >>"$FAILED"
		return
	fi
	# The media rule lands on an image, and a directory gains a trailing slash, so both answers are accepted.
	case "$dcode" in
	200 | 301 | 308) ;;
	*) echo "redirect $url -> $dest destination answered $dcode" >>"$FAILED" ;;
	esac
}

export -f curl_retry transfer_failure check_render check_redirect check_media
export BASE FAILED CURLRC CHECKRC SAMPLE

echo "==> $BASE"

# One request before the rest, because an auth gate turns a bad credential into a total failure.
# Otherwise the output reads as a vanished site rather than a wrong token.
# Transport failures are separated from HTTP ones, since a name that does not resolve otherwise reports as a status code and gets diagnosed as a credential or a symlink.
if ! preflight_headers=$(curl -q -sS -o /dev/null -D- -w '%{http_code}' --max-time 30 "${AUTH[@]}" "$BASE/" 2>"$CURLERR"); then
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
		echo "     SITE_AUTH_TOKEN_ID and SITE_AUTH_TOKEN" >&2
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
	headers=$(curl -q -sS -o /dev/null -D- --max-time 30 "${AUTH[@]}" "$BASE/" 2>"$CURLERR") || return 1
	printf '%s' "$headers" | grep -i '^x-blog-release:' | tr -d '\r' | sed 's/^[^:]*: *//'
	# Explicit, because pipefail carries grep's no-match status out of the function, which would report a reachable host serving no release header as unreachable.
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
		echo "     Run by hand, first rule out a wrong EXPECT_RELEASE. A VPS deploy names its" >&2
		echo "     release after its run rather than a commit, so pass the id the Deploy site" >&2
		echo "     job logged, which ends in the run id and attempt. The Validate sources job" >&2
		echo "     logs a bare timestamp first, and that id never matches." >&2
		exit 1
	fi
	echo "==> rules from release $got_release${waited:+ (after ${waited}s)}"
elif [ -n "$got_release" ]; then
	echo "==> rules from release $got_release"
fi

n_render=$(grep -c . "$RENDER_SRC")
echo "==> checking $n_render URLs that must render"
grep . "$RENDER_SRC" | xargs -P "$PARALLEL" -I{} bash -c 'check_render "$@"' _ {}

n_redirect=$(grep -c . "$REDIRECT_SRC")
echo "==> checking $n_redirect URLs that must redirect${SAMPLE:+, without following them}"
grep . "$REDIRECT_SRC" | xargs -P "$PARALLEL" -I{} bash -c 'check_redirect "$@"' _ {}

n_media=$(grep -c . "$MEDIA_SRC")
echo "==> checking $n_media media URLs that must be served as images"
grep . "$MEDIA_SRC" | xargs -P "$PARALLEL" -I{} bash -c 'check_media "$@"' _ {}

# The title tells the family page from the blog, since one container answers both and an unknown host falls through to the blog with a 200.
# X-Blog-Env still tells one environment from another, and the family host is a proxy rule of its own that can aim at the wrong container.
# Sending no Accept-Language keeps / from redirecting to /af/.
n_family=0
if [ -n "$FAMILY_BASE" ]; then
	family_auth=(-K "$CHECKRC")
	family_hint=", so check the family pair is valid for this resource"
	if [ -n "$FAMILY_CURLRC" ]; then
		family_auth+=(-K "$FAMILY_CURLRC")
	else
		family_hint=", and no family token was sent"
	fi
	echo "==> checking the family site at $FAMILY_BASE"
	for page in "${FAMILY_PAGES[@]}"; do
		page_path="${page%%|*}"
		title="${page#*|}"
		n_family=$((n_family + 1))
		if ! code=$(curl -q -sS -o "$FAMILY_BODY" -D "$FAMILY_HEAD" -w '%{http_code}' --max-time 30 "${family_auth[@]}" "$FAMILY_BASE$page_path" 2>"$CURLERR"); then
			echo "family $page_path could not be reached: $(head -1 "$CURLERR")" >>"$FAILED"
		elif [ "$code" != "200" ]; then
			# The gate answers a missing or wrong token by redirecting to its login page.
			hint="$family_hint"
			[ "$code" = "302" ] || hint=""
			echo "family $page_path expected 200, got $code$hint" >>"$FAILED"
		elif ! grep -qF "<title>$title</title>" "$FAMILY_BODY"; then
			echo "family $page_path answered without the title '$title', so another site served it" >>"$FAILED"
		else
			got_env=$(grep -i '^x-blog-env:' "$FAMILY_HEAD" | tr -d '\r' | sed 's/^[^:]*: *//')
			family_release=$(grep -i '^x-blog-release:' "$FAMILY_HEAD" | tr -d '\r' | sed 's/^[^:]*: *//')
			if [ -n "${EXPECT_SITE_ENV:-}" ] && [ "$got_env" != "$EXPECT_SITE_ENV" ]; then
				echo "family $page_path is served by '${got_env:-<no X-Blog-Env header>}', expected '$EXPECT_SITE_ENV'" >>"$FAILED"
			fi
			if [ -n "${EXPECT_RELEASE:-}" ] && [ "$family_release" != "$EXPECT_RELEASE" ]; then
				echo "family $page_path is from release '${family_release:-<no X-Blog-Release header>}', expected '$EXPECT_RELEASE'" >>"$FAILED"
			fi
		fi
	done
else
	echo "==> SITE_EXTRA_BASE_URL is unset, so the family site is not checked"
fi

# A count of zero exits non-zero, so a fallback that echoes would append a second zero.
# Swallowing only the exit status keeps the printed count usable.
failures=$(grep -c . "$FAILED" 2>/dev/null || true)
if [ "$failures" -eq 0 ]; then
	echo "PASS - $((n_render + n_redirect + n_media + n_family)) ${SAMPLE:+sampled }URLs honored"
	exit 0
fi

echo
echo "FAIL - $failures of $((n_render + n_redirect + n_media + n_family)) ${SAMPLE:+sampled }URLs"
sort "$FAILED" | head -40
[ "$failures" -gt 40 ] && echo "... and $((failures - 40)) more"
exit 1
