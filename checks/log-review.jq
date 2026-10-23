def path: (.RequestPath // "") | split("?")[0] | ascii_downcase;

# Shapes neither site serves, so a match is never a finding.
def scanner:
  path | test(
    "\\.(php[0-9]?|phtml|asp|aspx|jsp|cgi|pl|py|sh|env|git|svn|sql|bak|old|orig|swp|save|tar|gz|tgz|bz2|rar|7z|ya?ml|toml|ini|log|conf|cfg|config|pem|key|crt|db|sqlite|mdb|dll|exe|jar|war|tf|tfvars|tfstate|map|alfa|axd|suspected|example|htaccess|htpasswd)(/|~|$)"
    + "|/\\.[a-z0-9_.-]+"
    + "|^/(wp-admin|wp-includes|wp-json|wp-login|xmlrpc|wp[0-9]?|wordpress|cgi-bin|@fs|@vite|proc|etc|var|bin|backups?|bak|tmp|temp|logs?|api|admin|administrator|config|vendor|node_modules|phpmyadmin|pma|_profiler|actuator|console|manager|debug|_debug|_ignition|server-status|owa|ecp|autodiscover|remote|boaform|hnap1|geoserver|v1|v2|graphql|swagger|userfiles|cms|dashboard|_next|_astro|_static|_image|alfa_data|alfacgiapi|ipfs|webhooks?|webhook-test|langflow|flowise|metabase|mb|bi|analytics|inngest|mcp|sse|uploads|files|sites|site|site1|web|website|home|portal|old|new|panel|register|auth|users?|static|public|keys|dist|plugins|demo|test|go|shop|store|blog|blog2|press|news|main|content|images|img|icon|us|de|fr)(/|$)"
    + "|^/(id_[a-z0-9]+|env|private-key|credentials|secure|signup|sign-in|signin|login|account|reset-password|forgot-password|backoffice|exec-py|functionrouter|read-document|form|z9x8c7v6b5-[^/]*)(/|$)"
    + "|wp-content/(plugins|themes|mu-plugins|cache|upgrade|languages|debug|updraft|backup)"
    + "|woocommerce_|give_stripe|wp2shell|opt_woocommerce|wlwmanifest"
    + "|^/(ads|app-ads|llms|ai|security|humans|servers|info|dedi|vps|ssh|logins)\\.txt$"
    + "|^/media/?$|^/media/(wp|wc-|backup|woocommerce)|^/dockerfile$|-nonexistent\\.txt$|^/[0-9a-f-]{36}\\.html$"
    + "|^/m-?[0-9.]+%20|^/translate%28"
    + "|^/(?!index\\.json$)[^/]+\\.json$|^/(?!site\\.js$)[^/]+\\.js$|^/[^/]+\\.zip$|apple-touch-icon-"
  );

select(.["request_X-Blog-Check"] == null)
| select(.RequestHost == $blog or .RequestHost == $family)
| select(.DownstreamStatus == 404)
| select(scanner | not)
# Behind a proxy ClientHost is the forwarded chain, and its last element is the address the edge saw.
| .ClientHost |= (if . == null then . else (split(",") | last // "" | ltrimstr(" ")) end)
