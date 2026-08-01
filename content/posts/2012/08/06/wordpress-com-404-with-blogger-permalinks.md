---
title: WordPress.com 404 With Blogger Permalinks
date: '2012-08-07T00:02:52+00:00'
url: /2012/08/06/wordpress-com-404-with-blogger-permalinks/
categories:
- cloud
- problem
- solution
tags:
- blogger
- wordpress
post_id: '241'
---
Part of the research I did before [migrating from Blogger to WordPress.com](/2012/07/15/from-blogger-to-wordpress/), was to make sure that current Blogger permalinks will resolve correctly once the old posts were imported into WordPress.com. At the time all seemed fine, but soon after migrating, I received alerts from [Google Webmaster Tools](http://www.google.com/webmasters/tools/) that there is an increase in site errors, specifically 404 errors.

Some background: [Permalinks](http://en.wikipedia.org/wiki/Permalink) are the URL’s that point directly to specific posts on the blog. These URL’s are known by search engines, are shared on forums, and are basically the static address of posts. Blogger and WordPress.com use different styles of permalinks. WordPress.com allows some [customization of permalinks](http://codex.wordpress.org/Using_Permalinks), but unlike WordPress.org, there is no support for custom plugins to handle rewrites for permalinks, 302’s or 404’s.

Although not documented anywhere, WordPress.com [does support](http://en.forums.wordpress.com/topic/migrate-from-blogger-with-custom-domain-name-and-keep-seo) Blogger style permalinks, and will correctly redirect the Blogger style link to the WordPress.com style page. As an example, see the links below, one for Blogger and one for WordPress.com:

`http://blogdotinsanegenius.blogspot.com/2012/06/looks-can-be-deceiving.html
/2012/06/looks-can-be-deceiving`

Search engines will know the link using the old blogger style URL, and both styles of links will correctly resolve to the current page:

`/2012/06/19/looks-can-be-deceiving
/2012/06/looks-can-be-deceiving.html`

So why is it that Google Webmaster Tools reported a suddenly spike in 404’s?

[![Google.404.1](/media/2012/08/google-404-1_thumb.png)](/media/2012/08/google-404-1.png)

By reviewing the links that report 404, I noticed that the permalink format of certain posts on WordPress.com was slightly different to the Blogger permalinks.

`http://blogdotinsanegenius.blogspot.com/2009/10/hitachi-a7k2000-and-seagate-barracude.html
http://blogdotinsanegenius.blogspot.com/2010/05/zotac-xboxhd-id11-mkv-h264-video.html
http://blogdotinsanegenius.blogspot.com/2008/03/printing-from-network.html` `/2009/10/11/hitachi-ultrastar-and-seagate-barracude-lp-2tb-drives/
/2010/05/28/zotac-xboxhd-id11-mkv-h-264-video-playback-performance/
/2008/03/30/printing-from-the-network/`

Notice the difference? Blogger appears to keep links short, and remove words like “the” and “and”.

I contacted WordPress.com support, and they provided a manual [solution](http://en.forums.wordpress.com/topic/migrate-from-blogger-with-custom-domain-name-and-keep-seo). They suggested that I modify the “slug” of each 404 post to match the Blogger style permalink.

[![Slug](/media/2012/08/slug_thumb.png)](/media/2012/08/slug.png)

This resolved the problem with the top 404’s, but I would have expected the Blogger import plugin to take care of this for me.

But, I soon received another alert email from Google Webmaster Tools, and this time the 404 posts looked a bit different.

[![Google.404.2](/media/2012/08/google-404-2_thumb.png)](/media/2012/08/google-404-2.png)

Notice that all the links contain parameters in the URL (I think these are old style Google Analytics parameters), and without the parameter the redirect works, but with any parameters the redirect fails.

`/2009/09/western-digital-re4-gp-2tb-drive.html
/2009/09/western-digital-re4-gp-2tb-drive.html?m=1`

I again contacted WordPress.com support, and I am still awaiting a resolution.

_\[Update: 9 August 2012\]_ _Just got an email from WordPress.com support, the problem with parameters is fixed, thank you._
