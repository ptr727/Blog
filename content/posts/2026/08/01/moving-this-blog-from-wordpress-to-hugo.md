---
title: Moving This Blog From WordPress to Hugo
date: '2026-08-01T12:00:00+00:00'
url: /2026/08/01/moving-this-blog-from-wordpress-to-hugo/
categories:
- solution
- cloud
tags:
- blogger
- wordpress
- hugo
- github
- caddy
- migration
---
This blog has been quiet since May 2024, and it was still costing about $140 a year to sit there. That is a silly amount to pay for a site nobody was updating, so I moved it: the content is now a [Hugo](https://gohugo.io/) static site, the source lives on GitHub, CI builds and verifies it, and [Caddy](https://caddyserver.com/) serves it from a small VPS.

The interesting part of this migration was not Hugo. Converting the posts took an afternoon. The interesting part was that this blog has been at the same domain since 2008 across **three** platforms, and each platform left its own URL shapes behind. Getting the content across is easy. Not breaking sixteen years of inbound links is the actual job.

This post is about what that took, and about the things that silently went wrong and only showed up because I went looking.

## This is the second time I have done this

The first move is documented on this blog, which turned out to be genuinely useful fourteen years later.

- [Blogger Dynamic Templates](/2012/06/07/blogger-dynamic-templates/) and [Looks Can Be Deceiving](/2012/06/19/looks-can-be-deceiving/), where Blogger's dynamic templates broke enough things to start me looking for an exit.
- [From Blogger to WordPress](/2012/07/15/from-blogger-to-wordpress/), the actual move in July 2012, including the WordPress.com against self-hosted WordPress.org comparison.
- [WordPress.com 404 With Blogger Permalinks](/2012/08/06/wordpress-com-404-with-blogger-permalinks/), written a few weeks after, when Google Webmaster Tools started reporting a spike in 404s.

That last one is worth reading if you are migrating anything, because it is the same lesson twice. In 2012 the problem was that WordPress generated a slightly different slug than Blogger had, so `/2008/03/printing-from-network.html` did not match `/2008/03/30/printing-from-the-network/`. Blogger had dropped short words like "the" and "and" from its auto-generated slugs.

In 2026 the problem was that Blogger *also* truncated those slugs at 40 characters, which I did not know in 2012 and had to rediscover. Same root cause, same class of silent failure, fourteen years apart. The 2012 post is the reason I thought to go looking at all.

## The URL problem

The blog started on [Blogger](https://www.blogger.com/) in 2008, moved to WordPress in mid-2012, and kept the same domain through both moves. WordPress has been quietly 301-redirecting the old Blogger permalinks ever since, which I had completely forgotten about.

My first instinct was to use the sitemap as the list of URLs to preserve. The sitemap lists **111 URLs**.

The real number is **1,245**.

That gap is the whole story. The sitemap lists posts and pages. It does not list:

- 183 tag archives and 12 category archives, plus their pagination
- 83 date archives (`/2015/`, `/2015/06/`)
- 322 attachment pages, one per uploaded image
- 302 per-post comment feeds
- 12 author archive URLs
- 59 Blogger-era `.html` permalinks
- the feeds

If you are planning a migration like this, **do not trust your sitemap**. Crawl the live site, and then go looking for the things a crawl cannot find either, because nothing on the current site links to the Blogger URLs. No crawler will find them. They are only in Google's index and in other people's links.

I ended up splitting the contract in two: **328 URLs that Hugo must render**, and **917 that the web server must redirect**. Both lists are committed to the repo, and both are checked by CI.

## Actually doing it, step by step

The order matters more than the tools. Everything up to step 4 is reversible and costs nothing. Do all of it before you convert anything.

What follows is how it went. The maintained version, with the scripts, is [`capture/README.md`](https://github.com/ptr727/Blog/blob/main/capture/README.md) in the repository, and that one is kept current while this stays as written.

### 0. Decide where the inputs live, before you fetch any of them

Every step below produces a file you will still be reading months later. The crawl is the input to every check. The export is the input to every redirect map. The media tar is the only correct copy of your images. Put all of it in one directory, outside the site repository, and keep it there.

Outside the repository, because none of it belongs in a published history: it carries commenter email addresses, IP addresses, and a complete copy of a site you are about to take down. In one directory, because the tooling that derives your URL contract has to be pointed at it, and a derivation you cannot re-run is a result nobody can check.

The shape that worked here:

```text
capture/
  export/raw/         the content export, as downloaded
  export/media-tar/   the media export, unpacked
  mirror/             the crawl, as the old site served it
  inventory/          the URL and media lists derived from that crawl
```

Then record where that directory is, in the repository, alongside whatever other machine-specific values you keep out of git. That sounds too obvious to write down, which is exactly why it does not get written down: the one thing you cannot re-derive from the repository is the location of the thing everything was derived from.

Two of those four are re-fetchable from WordPress for as long as the account exists, and those two are the only things a person has to go and download. The crawl and the inventories are not re-fetchable at all, and they stop being possible the day the old hosting ends.

### 1. Capture the URL surface while the old site is still up

Do this **first**. Once you cancel the old hosting you can never reconstruct this, and it is the input to every check later.

Three sources, combined into one list, then each candidate verified with a real request:

```sh
# a. The sitemap. Necessary, nowhere near sufficient.
curl -s https://example.com/sitemap.xml | grep -oP '(?<=<loc>)[^<]+' > sitemap-urls.txt

# b. A recursive crawl. Finds only what is linked from somewhere.
# --delete-after removes the downloaded files but still leaves a directory tree
# behind, so point it at a scratch directory rather than your working one.
WORK="$(mktemp -d)"
wget --spider --recursive --level=inf --delete-after --no-directories \
     --directory-prefix="$WORK" https://example.com/ 2>&1 \
  | awk '/^--/ {print $3}' | sort -u > crawl-urls.txt
rmdir "$WORK"

# c. Verify every candidate actually answers, and record what it answers with.
while read -r url; do
  printf '%s %s\n' "$(curl -s -o /dev/null -w '%{http_code}' "$url")" "$url"
done < candidates.txt > verified.txt
```

Then **derive** what neither source can see. Date archives (`/2015/`, `/2015/06/`) are computable from your post dates. Pagination is computable from post counts at your theme's page size. Neither is linked from anywhere on a typical theme, so the crawl will not find them and the sitemap does not list them.

Sort the verified list into two buckets: things that returned 200 and must keep rendering, and things that returned 301 and must keep redirecting. That split is your contract.

**Include a URL you know does not exist, and check it 404s.** A permissive server, or a catch-all rule you did not know about, will cheerfully answer 200 or 301 for anything you invent, and then your whole verified list is worthless. On this site the check looks like:

```text
200 https://blog.insanegenius.com/2022/01/17/enom-datacenter-move-borks-dns/
301 https://blog.insanegenius.com/2012/06/looks-can-be-deceiving.html
404 https://blog.insanegenius.com/2012/06/this-url-never-existed.html
```

Three different answers to three different kinds of URL is what tells you the 200s and 301s mean something.

### 2. Export the content

On WordPress.com: **Tools, then Export, then All content, then Download Export File**. Do not filter by date or type, since a partial export is the most common way a migration quietly loses posts.

You get a WXR file, which is just XML, a few megabytes. At larger sites WordPress emails a zip containing several XML files instead, which is equally fine.

This carries post and page bodies in raw form, plus comments, categories, tags, and pointers to media. It does **not** contain the media itself, which is the next step and a genuinely separate one.

### 3. Export the media files, which is a different menu

**Tools, then Export Media Files, then Download.** This is its own item in the Tools menu, not a section of the content export page, which is easy to miss if you assume "Export" covers everything. You get a `.tar` organized into `year/month` folders.

**This step is not optional.** It is the only trustworthy copy of your images, for reasons in the media section below. It also includes *unattached* media, which is uploaded but never embedded in a post, and which the XML omits entirely.

### 4. Convert

I used [wp2hugo](https://github.com/ashishb/wp2hugo). Run it locally, never in CI, since it is a one-time operation whose output you then own and edit.

```sh
wp2hugo \
  --source path/to/export.xml \
  --output converted \
  --download-media \
  --download-all \
  --continue-on-media-download-error \
  --content-date-folder-structure year-month
```

`--download-media` is worth enabling even though you are going to throw the downloaded bytes away, because it is what drives the rewriting of absolute WordPress URLs into relative ones in the post bodies. Keep the rewrite, replace the bytes.

`--generate-nginx-config` defaults to on and produces a map of WordPress GUIDs to Hugo URLs. That is the source of the `?p=<id>` shortlink redirects, and it is worth keeping even if you are not using nginx. It is a lookup table you can translate to whatever server you end up with. Be aware that the config it emits is a stub with the rules commented out as an example. The map is the valuable part, not the config.

### 5. Replace the media from the tar

Extract the media tar over the converted media directory, then **verify by content hash**, not by file count. See the media section below for why this step is the difference between keeping your images and quietly replacing them with thumbnails.

### 6. Fix the taxonomy URLs before you look at anything else

If your old site served `/tag/` and `/category/`, singular, set the permalinks now, because every archive URL depends on it and the failure is silent. See the Hugo section below for the specific trap.

### 7. Now build, and start checking

```sh
hugo --gc --minify --panicOnWarning
```

Then check the built output against the render half of your contract, before you think about servers. Every URL that must render should exist as a built page.

What remains after that is the redirect half, which is the web server's job and the subject of most of this post.

Steps 1 and 3 are the two people skip, and they are the two that cannot be recovered later.

## The Blogger permalinks, and how I nearly got them wrong

48 of the 108 posts predate the WordPress move. Their old URLs look like `/2012/03/some-post-title.html`, with a year and month but no day.

I only discovered these existed because I noticed five posts sharing a single date and went to find out why. That is an uncomfortable thing to realize: a whole class of live, working URLs that I would have 404'd without ever knowing.

There is no way to derive the target from the source. The old URL has no day segment, so no regular expression gets you to `/2012/03/14/some-post-title/`. It has to be a lookup table. I built one from the WordPress export by taking each post's date and slug for the posts that carry Blogger metadata, which reproduced a 48-entry map.

**The map should have had 59 entries.**

Blogger truncated auto-generated slugs at 40 characters, on a whole-word boundary. So for the 11 posts whose title is long enough, the URL Blogger actually served, and therefore the one in Google's index, is the *truncated* one. That was the form missing from my map. WordPress redirects both, which is why testing a handful of the long ones by hand would have looked fine.

I verified all 11 truncated URLs return 301 on the live site, and checked a deliberately fabricated slug returns 404, to be sure I was seeing real registered redirects rather than a catch-all that makes everything look like it works. That control matters. Without it a permissive server will happily tell you every URL you invent is fine.

Two other Blogger-era shapes turned up in the same pass: `/p/<slug>.html` for static pages, and `/feeds/posts/default` for the Atom feed. Both still resolve today.

## Your export is not a complete copy of your media

The WordPress export tar had 778 media files. I ran the converter with its media-download option, got 778 files back with the same names in the same paths, and moved on.

That was wrong. **167 of those 778 files, 21% of them and 135 MB, were degraded derivatives.** WordPress.com serves optimized copies at the same URL, so a fetch over HTTP gets you a re-encoded image, not your original. One phone photo came back 205 times smaller than the original.

A file count reconciles perfectly. Every filename matches. Only a content hash against the official export catches it.

So: **get the export tar, and verify by hash.** Never populate media over HTTP from the live site, and never trust a file count as evidence that a copy is correct.

Separately, 270 images in the posts were never in any export at all, because they were hotlinked from Google's servers, left over from the Blogger era. Those are on borrowed time regardless of what I do, so I pulled them all local.

Fetching those had its own trap. A Picasa URL ending in `-h`, like `/s1600-h/`, does not serve an image. It serves an HTML wrapper page **with a 200 status**. A naive "status is 200 and the body is non-empty" check passes happily on 121 of 266 files that are actually 400-byte HTML documents. The fix is to check magic bytes rather than status codes, and to follow the `<img src>` inside the wrapper to the real image.

That is a good general rule for pulling binaries from anywhere: status codes tell you the server answered, not that it answered with what you asked for.

## Hugo specifics that cost me time

**Taxonomy URLs are the highest-risk part of a WordPress-to-Hugo move.** WordPress serves `/tag/foo/` and `/category/bar/`, singular. Hugo defaults to plural, `/tags/` and `/categories/`. That silently breaks 195 archive URLs.

The trap is in how you fix it. Hugo's taxonomy config is `singular: plural`, and the plural is *also* the front-matter key. So setting `category: category` makes Hugo look for a `category:` key in your front matter, match nothing, generate zero term pages, and still produce a plausible-looking empty `/category/` listing. Everything appears to work. Control the URL with `permalinks` instead, and leave the taxonomy names alone.

**Build with `--panicOnWarning`.** It is the difference between a gate and a suggestion. My theme, PaperMod, uses two APIs Hugo deprecated in 0.158 and upstream still ships them, so the strict build fails on the theme rather than on my content. Overriding those two templates locally was worth it to keep the flag on.

**Hugo has no built-in year or month archive.** The 83 date URLs are redirects, not pages.

## Serving it

Everything that is not a rendered page is the web server's job, so the choice of server came down to which one could express the redirects.

I evaluated static-web-server and ruled it out. Its redirect matching looks at the path only, and the query string is never an input. This blog has 110 legacy `/?p=<id>` shortlinks, so `/?p=123` would have matched `/`, redirected the homepage, and carried the query through. It also does a linear regex scan per request with no lookup primitive.

Caddy handles it in **13 redirect directives and 5 map files**. Maps are the right structure for the cases where no pattern can derive the answer: the Blogger permalinks, the `?p=` ids, and the attachment slugs.

The deploy is deliberately boring. A release is a directory containing the built site, the Caddy config, and the redirect maps *together*, and going live is swapping one symlink. Shipping the config inside the release is what makes a rollback honest, because the redirect rules and the content they point at move as one unit.

**With one catch I got wrong at first, and it is worth knowing if you build this.** Swapping the symlink reverts the *content* immediately, because the kernel resolves the link per request. It does not revert the *rules*. Caddy expands its config, including the imported map files, when it loads, and it does not watch those files afterwards. So a rollback without a reload gives you yesterday's pages served by today's redirects, which is the exact mismatch the bundle was supposed to prevent.

Worse, it makes verification lie. Change a redirect, deploy, run your checker without reloading, and the checker exercises the *old* rules and reports a pass while the thing you shipped is broken. I found this by adding a deliberate probe entry to a map, deploying it, and watching the URL keep returning 404 until I restarted the container, at which point it returned the 301 it should have all along.

The fix is one line, a restart after any deploy or rollback that touches the config. The lesson is the general one: an atomic swap is only atomic for the thing that actually reads through it per request.

Unchanged files are hard-linked from the previous release, so ten retained releases cost about 600 MB rather than 5.6 GB.

## What CI actually checks

This is the part I would recommend to anyone doing this, whatever tools you pick.

A missing page is obvious. **A missing redirect is silent**, and you find out months later when you notice traffic that stopped arriving. So the URL contract is committed to the repo as plain text, and CI fails the build if any of it stops working:

- every one of the 328 URLs that must render, still renders
- every one of the 778 legacy image URLs still resolves
- every local asset reference in the built output actually exists

There is a second check that runs against a *running server*, because a redirect is the server's job and no build can prove it. It follows each redirect to its destination and checks the destination answers, since a redirect that lands on a 404 is still broken.

Two things I would do again:

**Put a length floor on every list-driven check.** A gate that reads a list of URLs and checks each one passes perfectly if the list is truncated to nothing. Mine assert a minimum count, and I proved it by cutting the list to 50 entries that all existed. Without the floor, that passes.

**Demonstrate each gate failing before trusting it.** I deleted a post and confirmed the parity check failed. I deleted one media file and confirmed the media and asset checks failed separately. I pointed a redirect map entry at a page that does not exist and confirmed the live check caught it. A gate that has only ever passed is indistinguishable from one that checks nothing.

## Do not do this by hand

I did almost none of this manually. I ran it as a series of tasks through [Claude Code](https://claude.com/claude-code), and it is worth saying plainly that this is the kind of work it is genuinely good at.

The shape of a migration like this is dozens of small, tedious, verifiable jobs. Crawl a site and record what every URL answers. Compare 778 files by hash against a tar and list the ones that differ. Find every image reference in 110 markdown files, fetch the external ones, rewrite the references. Rebuild a lookup table from an XML export and prove it reproduces the old one byte for byte. Restructure a content tree so file paths mirror URLs. None of that is hard. All of it is exacting, and all of it is the kind of thing a human does slightly wrong at 2 AM.

Two things stood out beyond the automation.

**It found problems I had not asked it to look for.** The 167 degraded media files were caught because it hashed the downloaded copies against the export tar rather than counting them, on its own initiative. The Blogger slug truncation came from it questioning why the derived map had 48 entries when the live site answered for more. The favicons in this very repo turned out to be the WordPress logo, which it noticed while checking something else entirely.

**It corrected its own work when the correction was unflattering.** The URL parity gate initially passed against a truncated list, and rather than declare success it added a length floor and demonstrated the gate failing without it. That instinct, to distrust a passing check until it has been shown capable of failing, is the single most valuable habit in this entire migration, and it is the reason I believe the contract is actually enforced rather than merely asserted.

It is not autonomous. It needed direction on the decisions that were genuinely mine: keep the 2008 dates, do not modernize the feed GUID scheme, scope the cutover to the `blog` subdomain and never touch the apex records. And every claim it made, I made it prove. The commands in this post were re-run and verified before publishing, and one of them was wrong when first written.

But the ratio of what I directed to what I would have had to type is not close. If you are considering a migration like this and have been putting it off because of the tedium, the tedium is the part that is now cheap.

## Was it worth it

For the money, marginally. For everything else, yes. The content is now plain markdown in a git repository, the URL surface is written down and enforced instead of living inside a hosting platform, and publishing is a commit.

The one thing I would tell anyone starting this: **the migration is not the content, it is the URLs.** Budget your time accordingly. Converting 108 posts was the easy afternoon. Finding the 1,245 addresses this site is supposed to answer, and proving it still answers them, was the actual work.

The source for all of this, including the redirect rules and the URL contract, is [on GitHub](https://github.com/ptr727/Blog). If you want to discuss any of it, the repo has Discussions enabled, which is also why this post has no comment box below it.
