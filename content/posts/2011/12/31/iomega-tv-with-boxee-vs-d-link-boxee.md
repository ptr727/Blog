---
title: Iomega TV With Boxee vs. D-Link Boxee Box
date: '2011-12-31T20:38:00+00:00'
url: /2011/12/31/iomega-tv-with-boxee-vs-d-link-boxee/
categories:
- review
tags:
- boxee
- dlink
- htpc
- iomega
post_id: '125'
---
Untitled Page I have yet to find the perfect media player for playing my [archived music and movie collection](/2011/04/archiving-my-cd-dvd-and-bd-collection.html).

I’ve tried building my own using small form factor computers like the [Zotac ZBOX HD-ID11](http://www.zotacusa.com/zbox-hd-id11.html) ([Amazon](http://amzn.to/KFoNjZ)), [Nano AD10](http://www.zotacusa.com/zbox-nano-ad10.html) ([Amazon](http://amzn.to/L8xtly)) and [Nano VD01](http://www.zotacusa.com/zbox-nano-vd01.html) ([Amazon](http://amzn.to/MKUhon)). I’ve tried software like [Windows Media Center](http://windows.microsoft.com/en-US/windows/products/windows-media-center), [XBMC](http://xbmc.org/), [MediaPortal](http://www.team-mediaportal.com/), and [Boxee](http://www.boxee.tv/make). I’ve tried commercial products like the [WD TV Live Plus](http://wdc.com/en/products/products.aspx?id=320) ([Amazon](http://amzn.to/LXPi44)), [Popcorn Hour C-200](http://www.popcornhour.com/onlinestore/index.php?pluginoption=catalog&mainItemId=12) ([Amazon](http://amzn.to/LOSRND)), [A-210](http://www.popcornhour.com/onlinestore/index.php?pluginoption=catalog&mainItemId=24), [PopBox 3D](http://www.popbox.com/onlinestore/index.php?pluginoption=catalog&mainItemId=2) ([Amazon](http://amzn.to/Lonhns)), [Apple TV](http://www.apple.com/appletv/), [D-Link Boxee Box](http://www.dlink.com/boxee/) ([Amazon](http://amzn.to/M99Bty)), and [Iomega TV With Boxee](http://tv.iomega.com/). But, they all have problems and shortcomings.

I currently have three [D-Link Boxee Boxes](http://amzn.to/M99Bty) in my house, the D-Link Boxee Box does have problems, but so far it is the best I’ve found. The following are some of the most annoying problems:  

- The form factor is unique, but also impractical, it looks odd, uses too much vertical space, and does not fit in with the rest of the media components.
- The fan gets loud and is audible in a quiet room. Covering the SD slot suppresses the sound somewhat.
- There is no low power standby, it is always using full power even when not in use. Apparently this is a shortcoming of the Intel CE4110 SOC platform.
- Every time Boxee releases a firmware update they break something that used to work. The most frustrating was the recent 1.2 firmware update that [broke SMB network authentication](http://jira.boxee.tv/browse/BOXEE-11038) and resulted in [poor performance causing constant network re-buffering](http://jira.boxee.tv/browse/BOXEE-11034). In the end I had to install NFS on my Windows Server 2008 R2 box to get things working again. To make it worse, there is no option to opt-out of firmware updates, even a manual install of an older version just gets auto-updated again. I don’t mind auto updating functionality in products, but I do mind if the update breaks something that used to work, and there is no way back.
- When using a [HDMI switch](http://www.monoprice.com/products/product.asp?c_id=101&cp_id=10110&cs_id=1011002&p_id=6259&seq=1&format=2), and the HDMI switch is already powered on when the Boxee powers on, [there is no sound](http://jira.boxee.tv/browse/BOXEE-7806). The HDMI switch must be powered off when the Boxee powers on, then the HDMI switch can be powered on. This bug has been around since I bought the first Boxee, and the same switch works flawlessly with a variety of other hardware, including a Motorola HD-DVR, Motorola HD-STB, XBox 360, PS3, Roku 2 XS, Panasonic BD player, and a Sony DVD player, so it is not the switch, it is the Boxee.
- Even after switching to NFS for networking, I still get network re-buffering and [HD audio dropouts](http://jira.boxee.tv/browse/BOXEE-7914) when watching certain high bitrate BD MKV movies.
- Unlike XBMC, there is no separation between TV series and movies in Boxee, this makes it very difficult to find or watch TV shows, and Boxee rarely gets the metadata associations for TV shows right. XBMC does a much better job of treating TV shows as shows, with discrete seasons and episodes.
- The metadata scrapers are incapable of correctly identifying titles from file and directory names that contain a “;” instead of a “:”. In NTFS a “:” is not a legal character for use in file or directory names, so when a show title contains a “:”, I substitute it for a “;” in the filename and directory name. This issue is not unique to Boxee, and I don’t understand why scrapers can’t do common substitutions or removal of punctuation when performing a search.

 Even with all these issues, the Boxee Box still works most of the time for most content.

When the [Iomega TV With Boxee](http://tv.iomega.com/) was announced, one thing that stood out was the 1Gbps network port vs. the 100Mbps port on the D-Link. Theoretically 100Mbps is fast enough for BD content playback, but given the network re-buffering and HD audio dropouts on high bitrate content I was experiencing, I hoped it may help. I could not find official sources of hardware specs for the D-Link or the Iomega, but an [ifixit teardown](http://www.ifixit.com/Teardown/Boxee-Box-Teardown/4109/1) and a [Wikipedia article on Boxee](http://en.wikipedia.org/wiki/Boxee#Hardware_with_Boxee_software_integrated) shows the devices may have similar processor specs, with the Iomega having gigabit networking and analog video output.

The Iomega Boxee is not available in the US, but I around the end of November I pre-ordered an import from [Expansys USA](http://www.expansys-usa.com/iomega-tv-with-boxee-network-media-player-eu-plug-207734/). The box arrived a few days ago, end of December, and I started setting it up by replacing one of my D-Link Boxee’s.

The box comes with very little documentation, as an example, there are no instructions on how to open the remote to insert the batteries. It took me a few minutes to figure out where the battery compartments, yes there are two, were on the remote, and how to open them, i.e. press on the little arrows, apply lots of force, and slide the lids off.  
[![iomtv-remote-battery](/external/de27e6061b5e48ca.png)](/external/56bfeb8f40d91754.png)

The power supply is 12V 2A, 110V to 220V, with EU/UK power plugs supplied, I used a universal adapter to plug it into a US 110V outlet.  
 The box itself does not include WiFi capabilities, but Iomega supplies a WiFi USB dongle with the kit.

The form factor of the Iomega box is much more practical compared to the D-Link, it fits in nicely with the rest of my AV equipment. Iomega does supply a stand to mount the device vertically if you want it that way.  
[![Boxee.Front](/external/a675d69ed476aa1a.jpg)](/external/5bdb2138229e9d1d.jpg) [![Boxee.Back](/external/9da63883094d3c41.jpg)](/external/ca3e28580c4158a4.jpg)

The Iomega remote is a bit larger than the D-Link, but it also includes some handy buttons missing on the D-Link remote.  
[![Boxee.Remote.Front](/external/7a06309c94c9380b.jpg)](/external/fe19fd9323c08694.jpg) [![Boxee.Remote.Back](/external/9131cfde8497f7b3.jpg)](/external/8fcd13ae4cdd4f60.jpg)

The Iomega powered on and displays IO on the screen while booting, unlike D-Link that plays a startup animation, the Iomega box has no startup animation. As with the D-Link, the first thing I had to do was calibrate the screen overscan.

The next step was to login to my Boxee account, and this is where things started going wrong. I could not get the remote to work correctly, it would not respond, or it would enter the wrong characters. The keyboard on the remote has a little button that needs to be pushed to activate the keyboard, once activated, you can enter keys using the keypad. Pressing the button again deactivates the keypad, and you can use the navigation buttons on the front. I tried using the navigation buttons and the on-screen keyboard, the cursor would either not move, or jump way over to the wrong location, or start entering characters when I press navigation buttons. I tried the keyboard, and it would enter a few characters fine, and then just stop working, I could never get the backspace key to work.

I did some general troubleshooting by replacing the batteries, and power cycling the device, but still the same issues. I found a few user reports of similar [troubles with the remote](http://forums.boxee.tv/showthread.php?p=238996). Since my Iomega is an import, there is no chance for local support, but given the general complaints about the remote, I am not going to bother trying to replace it.

The Iomega remote is an IR remote, while the D-Link remote is an RF remote. When I first started using the D-Link RF remote I found it a bit of an inconvenience to switch between my [Harmony One](http://www.logitech.com/en-us/remotes/universal-remotes/devices/6441) universal IR remote, and the dedicated D-Link RF remote, but I must say for fast accurate navigation, the RF remote works great. In fact, I wish there was a standard for RF remotes, so that something like a RF Harmony One can be built, this would alleviate the annoyance and frustration of having to aim at IR devices.

I had a spare [D-Link RF remote with a USB dongle](http://amzn.to/LyqXUv), and I eventually plugged that into the Iomega, it worked fine, and I could login to my account, and configure the Iomega.

As I was configuring the device, I noticed that the Iomega was running firmware version 1.2.1.20452, while the D-Link was running 1.2.2.20482. Manually running an update said that 1.2.1 was the latest firmware for the Iomega. Strangely, the Iomega support site lists a [firmware version 1.3061](https://iomega-na-en.custhelp.com/app/answers/custom_detail/a_id/29313), but the version number format does not follow the typical Boxee a.b.c.d formatting. I tried to install the 1.3061 firmware using the manual USB update procedure, but the firmware install never completes, and a hard power cycle is required to boot back up. So I really don’t know what this 1.3061 firmware is supposed to be or do.

While applying the firmware, I noticed that there is a mouse cursor on the screen, and I noticed that the Iomega IR remote acts like a trackpad, as I slide my finger over the directional buttons, the mouse cursor moves around the screen. I did not try it out, but this may be useful for web browser navigation, if the remote actually works.

US content providers like Hulu, Vudu, and Netflix were not available on the Iomega, or at least I could not find them in any obvious way. I don’t know if this is because of regional targeting differences, or because the Iomega has [analog video output](http://support.boxee.tv/entries/20647293-connectors-and-indicators) and content provider DRM requirements may prohibit such content on this device. The lack of content providers is not a big deal for me, as I only use the Boxee for local content playback. For [Netflix](https://www.netflix.com/) and [Amazon Instant Video](http://www.amazon.com/gp/video/ontv/start) I use a [Roku 2 XS](http://www.roku.com/2xs). Boxee does not offer Amazon Instant Video, and the Roku’s Netflix experience is far superior to the Boxee’s.

The next difference seemed rather weird, the D-Link has HDMI audio passthrough support for DTS-HD and Dolby TrueHD, but the Iomega does not list any HD audio formats. When I tried to play a MKV file with TrueHD and AC3 tracks, the Iomega automatically selected the AC3 track. When I manually selected the TrueHD track, there was no audio.

I configured the Iomega the same way I configured the D-Link, using NFS, I added my music, movies, and TV series, hosted on a Windows server 2008 R2 server, accessed via gigabit Ethernet. Just like the D-Link, it took a while to catalog all the content, and just like the D-Link, the device is less than responsive while cataloging content.

Once the activity light stopped flashing, and the device appeared idle, I started playing some movies that suffer from network re-buffering and audio dropouts on the D-Link. The Iomega played all content perfectly, no re-buffering, and no audio dropouts. Unfortunately this is not really a meaningful test, as the more problematic content contains HD audio tracks, and the Iomega can’t play HD audio.

I will leave the Iomega connected to get some more airtime with it, but unfortunately the lack of HD audio is a deal breaker, not because I need HD audio, but because many of my BD MKV rips only have an HD audio stream. So either the Iomega needs to decode and play HD audio, or it needs to do bitstream passthrough. I doubt this is a hardware limitation, so hopefully a future firmware update adds HD audio passthrough support.


