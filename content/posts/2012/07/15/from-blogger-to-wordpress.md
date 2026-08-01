---
title: From Blogger to WordPress
date: '2012-07-15T19:48:58+00:00'
url: /2012/07/15/from-blogger-to-wordpress/
categories:
- cloud
- review
tags:
- blogger
- bluehost
- dreamhost
- wordpress
post_id: '153'
---
I outlined my concerns with Blogger in [my last post](/2012/06/19/looks-can-be-deceiving/), and after much deliberation, I decided to move my blog from [Blogger](http://www.blogger.com/) to [WordPress](http://www.wordpress.com/).

There are two main choices; use [WordPress.com](http://www.wordpress.com/) for full service blog hosting, or use [WordPress.org](http://www.wordpress.org/) and host the WordPress application at a hosting provider. Here is a summary [describing the differences](http://en.support.wordpress.com/com-vs-org/).

I decided to try both options; I created a blog a WordPress.com, and I created a self-hosted blog using WordPress.org.

Creating the blog at WordPress.com was very quick and easy.

As with Blogger, you can pick any sub-domain name for the hosted blog, as long as it is unique. On Blogger my site is [blogdotinsanegenius.blogspot.com](http://blogdotinsanegenius.blogspot.com/), and on WordPress.com my site is [blogdotinsanegenius.wordpress.com](/), not very imaginative, but descriptive and unique.

WordPress, like Blogger, allows you to [point your own domain name](http://en.support.wordpress.com/domain-mapping/map-subdomain/) to your hosted site using a CNAME record. But, unlike Blogger where it is free, WordPress.com charges $13 per year for this feature. WordPress.com offers additional paid domain services, including [domain registration](http://en.support.wordpress.com/domain-mapping/) and DNS management.

WordPress supports importing from a variety of sites and formats, including Blogger, and my posts, settings, and comments were all imported in a few minutes.

Here is the screenshot of the various import options offered:
[![Tools.Import](/media/2012/07/tools-import_thumb.png)](/media/2012/07/tools-import.png)

There are certain restrictions in using WordPress.com vs. WordPress.org, and to a lesser degree Blogger, most notably [no advertising of your own](http://en.support.wordpress.com/advertising/). WordPress.com will show their own ads, as that is their revenue model, similar to Blogger showing Google ads. But Blogger, as far as I know, does not restrict the use of other ads such as Amazon, nor do they restrict the use of affiliate links. WordPress.com specifically calls out that [Amazon affiliate links are ok](http://en.support.wordpress.com/affiliate-links/), as long as it is not the primary purpose of the site. WordPress.com offers a $30 option to [remove all of their ads](http://en.support.wordpress.com/no-ads/) from your blog.

For self-hosted WordPress I needed a hosting provider, and WordPress.org [offers some suggestions](http://wordpress.org/hosting/), probably with a revenue partnership. The world of low cost hosting is like the wild west; many brands owned by the same company, review sites owned by the hosting companies, referral programs leading to biased third party reviews, low cost signup high cost renewal, etc. I decided to try [BlueHost](http://www.bluehost.com/) and [DreamHost](http://www.dreamhost.com/), and I will give a brief review and overview of my signup and WordPress setup experience.

If you enter the BlueHost using [http://www.bluehost.com/wordpress\_hosting](http://www.bluehost.com/wordpress_hosting "http://www.bluehost.com/wordpress_hosting"), the link from the WordPress.org [hosting provider site](http://wordpress.org/hosting/), you are offered hosting at $3.95 a month, if you enter BlueHost using [http://www.bluehost.com/](http://www.bluehost.com/) you are offered the same hosting at $4.95 a month.

BlueHost does not offer a trial, but they do offer a 30 day money back guarantee. Do read [the terms](http://www.bluehost.com/terms), full refund less non-refundable fees, if cancelled within 3 days of signup.

When you go to the signup page, you have to enter a domain name, either a domain you own, or a domain you intend to buy. As I did not want restrict myself to a particular domain, I used the embedded support chat to contact support. After typing my question, and hitting the live chat button, I was redirected to a new page, where I had to select my contact option again, and then enter my question again. So basically the embedded support chat is bogus, whatever you type is thrown away, and you are directed to an outsourced chat provider.

When I finally managed to chat to an agent, they had to ask me what site I came from, another indication of the poor chat integration implementation. The agent assured me that I can change the domain any time, and their system just requires me to pick something. But, it turns out that this is not entirely true, once you remove the primary domain, you can [never add it back again](https://my.bluehost.com/cgi/help/345). I cannot imagine a technical reason for this restriction, so it may be related to avoiding a user creating a new hosting account vs. renewing an existing account at a much higher cost. To avoid any problems, I just used a domain I own but do not actively use.

The account creation and setup flow was optimized around taking my credit card information, once the account was created, it was rather confusing, starting with my login name being the domain name I selected in step one.

The first email I received, “Welcome to Bluehost! (redacted) - configure your account.”, told me that the fist step is to transfer my domain or to point my domain the the BlueHost DNS server, I did not want to do either of these. The email included links to the FTP server hosting the account, FTP username, and a link to change the password, but the change password link pointed to the main BlueHost site.

The second email I received, “Welcome to Bluehost! (redacted) - Get started now!”, included links to getting started tutorials.

The third email I received, “Welcome to Bluehost! (redacted)”, included a change your password link, and this URL was personalized, and let me create a new cPanel login password.

I proceeded to login to cPanel using my new password, and I was redirected to what I assume is the machine hosting the account, https://box835.bluehost.com:2083/frontend/bluehost/index.html. Notice that the port number is 2083, and this failed, as the network I was working on does not allow anything other that port 80 HTTP and port 443 HTTPS outbound traffic. I contacted support, who indicated I need to open port 2082 and 2083 outbound, no, I can’t do that. My own research into their own KB system gave [this link](https://my.bluehost.com/cgi/help/90), instructing me to use a [different admin URL](https://login.bluehost.com/), and this worked, using standard SSL, and no host or port specific redirects.

I wanted to map a temporary domain name to the hosting account, so that I can install, configure, and test WordPress, before committing to point my blog’s DNS entry to BlueHost. There was no convenient way to do this, I either had to use the http://\[IP\]/\[account\]/ path format, or I had to map one of my own domain names to the hosting IP address, or I had to point one of my domains to use their DNS server. And, this other domain had to be an unused domain, as I don’t want to transfer a live site before having the destination ready.

At this point I decided to try DreamHost. The main [DreamHost](http://dreamhost.com/) page lists the shared hosting as $8.95 a month, if you click on the [WordPress link](http://dreamhost.com/partners/wordpress/), you are offered the same hosting at $6.95 a month.

DreamHost offers a 2 week trial, you basically always sign up for the trial, and will only be charged if you do not cancel within 2 weeks.

The signup process is straightforward, the first thing you are asked is to create an account using your email address and select a password. After providing your credit card information, you are asked to provide a FTP username.

The first email I received, “\[redacted\] DreamHost Account Approval Notification!”, included the login information to the FTP server hosting the account, and indicated that the account is being created. The FTP password was system generated, and is different to the account password I already selected.

The second email I received, “\[redacted\] DreamHost FTP-only User Activated”, indicated that the FTP account had been successfully created.

Logging in to [cPanel](https://panel.dreamhost.com/) ran over standard HTTPS and I had no problems accessing the management portal.

The domain management portal allows you to create any number of domain to site mappings, and does not require the domain names to be mapped to or registered with DreamHost’s DNS. In order to create a sub-domain, you must first add the main-domain, even if you don’t intend to use or map it. DreamHost supports [mirror domains](http://wiki.dreamhost.com/Mirror_Domain), that allows you to use a dreamhosters.com sub-domain to point to your site. This was very convenient as it allowed me to register [blogdotinsanegenius.dreamhosters.com](http://blogdotinsanegenius.dreamhosters.com/), and use this domain for testing and configuration, and later I can use it as a CNAME for the blog’s DNS entry.

Installing WordPress was easy, DreamHost supports automatic deployment of a large number of popular applications.

Here is a screenshot of the available blogging applications:
[![DreamHost.Applications](/media/2012/07/dreamhost-applications_thumb.png)](/media/2012/07/dreamhost-applications.png)

I cannot speak to long term stability or performance, but judging based on the setup and administration process and experience, I think the $3 per month extra for DreamHost over BlueHost is well worth it.

As part of the blog migration I have to maintain existing permalinks, else search engines and users with links to content will not find the information.

As an example, consider the following permalinks:
Blogger: [http://blogdotinsanegenius.blogspot.com/2012/06/looks-can-be-deceiving.html](http://blogdotinsanegenius.blogspot.com/2012/06/looks-can-be-deceiving.html "/2012/06/looks-can-be-deceiving.html")
WordPress.com: [/2012/06/19/looks-can-be-deceiving/](/2012/06/19/looks-can-be-deceiving/ "/2012/06/19/looks-can-be-deceiving/")

Blogger and WordPress.com uses different permalink formats. Blogger uses a yyyy/mm/title.html format, where WordPress.com uses a yyyy/mm/dd/title format. WordPress.org allows the [permalink format to be changed](http://codex.wordpress.org/Using_Permalinks), and also allows [plugins](http://wordpress.org/extend/plugins/tags/permalink) to be used to convert between incoming and hosted formats.

I found many articles explaining the process of migrating from Blogger to hosted WordPress.org, but I could not find anything on similar functionality at WordPress.com. I asked about this on the WordPress user forum, and a forum user claimed that Blogger style permalinks are supported, yet I could find no information about it on WordPress site. I tested it, and it did indeed work. I contacted WordPress support to get an official answer, and they claimed it is not supported, and recommended that I use WordPress.org. The forum users’ comment was very insightful; “Most of the staff have less experience at WP.com than I do, but you can ask them.”

Another difference between Blogger and WordPress is the use of labels vs. [tags and categories](http://en.support.wordpress.com/posts/categories-vs-tags/). On Importing the site from Blogger, all the labels were converted to categories. Most of the labels really needed to be tags, and fortunately WordPress offers a bulk tag to category, and [category to tag converter](http://en.support.wordpress.com/posts/categories/).

Below are screenshots from [Windows Live Writer](http://writer.live.com/) showing Blogger style labels (categories) and WordPress style categories and tags:
[![WLW.Blogger](/media/2012/07/wlw-blogger_thumb.png)](/media/2012/07/wlw-blogger.png)[![WLW.WordPress](/media/2012/07/wlw-wordpress_thumb.png)](/media/2012/07/wlw-wordpress.png)

WordPress.com supports all the features I need, and at $45 per year for no ads and a custom domain, it is cheaper than the cheapest self-hosting, and more importantly, maintenance free.

I am posting this directly to the WordPress.com sub-domain, next I will change the blog's DNS CNAME to point to the WordPress.com sub-domain, and if all goes well, you are reading this post on [blog.insanegenius.com](/).
