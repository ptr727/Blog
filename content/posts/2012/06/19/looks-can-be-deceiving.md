---
title: Looks can be deceiving
date: '2012-06-20T05:28:00+00:00'
url: /2012/06/19/looks-can-be-deceiving/
categories:
- review
tags:
- amazon
- blogger
- google
- live
- microsoft
- wordpress
post_id: '130'
---
It has been almost two weeks since I [switched to using Blogger’s new dynamic template](/2012/06/blogger-dynamic-templates.html).

Browsing the site with the new template works really well; it uses most of the available browser real estate, it looks good on an iPad, it feels nice and fluid, but it also has problems.

For some reason my AdSense integration stopped working, and the AdSense site said my account needs to be verified. AdSense was working fine in the old template, so something in the new template, or switching to the new template, must have triggered this. I’ve had AdSense for almost a year, and in that time I’ve not even made enough for Google to trigger a payment. In order to verify my account, I had to enter a PIN they mailed me on a postcard, entered the amount of a test transfer in my bank account, and entered a PIN read to me on my phone. Two days after the verification steps were completed ads started showing up again.

Very few widgets support the dynamic template, and the options are limited to a handful of very basic widgets.

One of the supported widgets is the label cloud, and as I was configuring it, I decided to do some label cleanup. In the process I noticed that the new Blogger management interface is terrible at editing labels, and that direct links to labels no longer work.

In the old Blogger management interface it was easy and obvious how to add and remove labels, although renaming has never been supported. In the new interface there is only an add option, and to remove a tag, you have to add the same tag again to remove it, I discovered this by accident, as all the Blogger help still refers to the old management interface. Same as the old interface, you can filter all posts that contain a certain label, and then you can select one or more of those posts, and then add, or add again to remove, labels. Now, when a post has been selected, and you change the filter, that post does not get unselected, and when you then apply a label to a visibly selected post, it also applies to any previously selected posts that are not currently in the filter view. This is just silly.

Since I changed some of the labels, and I know that links to labels are case sensitive, this is another silly thing I never understood as label creation and editing is case insensitive, I wanted to test a label link. When clicking a label in the cloud widget on the main blog page, the link works fine, but when you directly navigate to a label link, you get a blank page. Not good.

Since I was so disappointed in only making a few dollars in a year of serving AdSense ads, I decided to create an Amazon Associates account, tag my links to Amazon products, and  show some Amazon ads, hoping I can at least recover the cost of the domain registration fees. It turns out that Blogger no longer natively supports Amazon ads, seems a bit anti-competitive to me, but that’s the nature of their business. Ok, you can host Amazon ads by using HTML in your template, but, the dynamic template does not support any customization, and it does not support any HTML widgets.

That leaves me to using just tagged links to Amazon pages, that is easy enough, just a bit of re-editing old pages. A friend suggested I use [Bitly](http://bitly.com/) to shorten my Amazon tagged links, that way I can do link tracking, and since adding Bitly I’ve had … 3 clicks, seems I’ll have to keep paying those domain fees after all.

That same friend was kind enough to [remind me](http://marketingwithsara.com/amazon/warning-to-all-affiliate-marketers) of my associate obligation, to make it clear to users that I’m an Amazon associate, by adding legalese to my site. Something I would normally do in the footer, but wait, you guessed it, the dynamic template does not support any customization, and all I can do is add the text directly to every post.

Since that is a hassle, here is what I need to say, so I’ll just say it here to get some coverage:

> blog.insanegenius.com is a participant in the Amazon Services LLC Associates Program, an affiliate advertising program designed to provide a means for sites to earn advertising fees by advertising and linking to amazon.com.

Reading the blog on the iPad is a pleasant experience, but, the sidebar widgets that pop out are clearly designed for a mouse, not a finger, as such it is next to impossible to get them to pop out.

I use [Windows Live Writer](http://windows.microsoft.com/en-US/windows-live/essentials-other-programs) to author my blog posts, it is a great app, and the integrated image posting and sizing is so much easier than any alternatives I’ve tested. Unfortunately, the WYSIWIG functionality does not work with dynamic templates. In order to retrieve the blog template, WLW will make a test post, read the template, and then delete the test post. After making the test post, WLW times out reading the post, but at least it deletes it.

There are some rumblings that WLW may be discontinued, based on its absence from the [Windows 8 Metro lineup of Live apps](http://windowsteamblog.com/windows_live/b/windowslive/archive/2011/09/21/a-preview-of-windows-live-for-windows-8.aspx), and in support from the user community, there is a [petition to not kill WLW](http://www.petitionbuzz.com/petitions/dontkillwlw).

A blog subscriber notified me that he was getting some “temporary post” titled posts in his feed. I’ve seen these before in Google Reader, even from Microsoft’s own MSDN and TechNet blogs. It seems that [FeedBurner](http://feedburner.google.com/) is so hasty that it streams the temporary post created by WLW before WLW had a chance to delete it. No harm, it just looks odd in the stream.

By now I was  pretty fed up with Blogger and the dynamic template, and I started looking for alternative and free blog hosting. There really seems to be only one free and feature rich alternative, and that is [WordPress.com](http://wordpress.com/). WordPress has an easy to use Blogger importer, that imports posts, comments, and settings. Check out [my blog in WordPress format](/). There is one catch, the free .com version of WordPress does not allow direct advertising, they do the advertising for their own revenue. Not that it really matters as the few dollars I stand to loose is well worth it if I don’t need to deal with Blogger.

I am still hopeful that Google will step up to the plate and fix Blogger and dynamic templates, but at least I know there is an easy migration path to WordPress.


