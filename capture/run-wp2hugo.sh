#!/usr/bin/env bash
# Convert the WordPress export to Hugo. Media is downloaded here because that is what
# drives absolute->relative URL rewriting, but the bytes are replaced afterwards from the
# official media tar - WordPress.com serves optimized derivatives over HTTP for some
# images, one of them at a fraction of the original's dimensions.
#
# The export is chosen by build-redirects.py --print-export rather than by a glob here, so
# the conversion and the redirect maps are provably built from the same file. An account
# holds several exports and a media-only one carries the attachments and no posts, and
# converting that one yields a site that builds and is empty. The selection cannot be
# reimplemented in shell: the test is that ONE item carries both post_type=post and
# status=publish, where two greps over a whole file would accept the media-only export.
set -Eeuo pipefail

# A `go install`ed wp2hugo lands here. $HOME rather than a literal path.
export PATH="$HOME/.local/bin:$PATH"

: "${CAPTURE_ROOT:?CAPTURE_ROOT is not set -- see example.env and ENVIRONMENT.md}"
[ -d "$CAPTURE_ROOT" ] || {
	echo "CAPTURE_ROOT is not a directory: $CAPTURE_ROOT" >&2
	exit 1
}
# Resolved to absolute before anything else, because this script cd's into it and the
# export path is worked out beforehand. A relative CAPTURE_ROOT would yield a relative
# export path that stops resolving the moment the cd happens, which reads as a missing
# export rather than as a path problem.
CAPTURE_ROOT="$(cd "$CAPTURE_ROOT" && pwd)"
export CAPTURE_ROOT

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export_xml="$("$here/build-redirects.py" --print-export)"
echo "==> export: $export_xml"

cd "$CAPTURE_ROOT"
wp2hugo \
	--source "$export_xml" \
	--output converted \
	--download-media \
	--download-all \
	--continue-on-media-download-error \
	--content-date-folder-structure year-month \
	--color-log-output=false
echo "WP2HUGO-EXIT-OK"
