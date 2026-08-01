---
title: XBMC for Android on Pivos XIOS DS
date: '2012-07-22T20:36:07+00:00'
url: /2012/07/22/xbmc-for-android-on-pivos-xios-ds/
categories:
- review
tags:
- android
- htpc
- pivos
- xbmc
post_id: '201'
---
In my [ongoing quest](/tag/htpc/) to find the perfect Home Theater PC platform, I was excited to read that [XBMC had been ported to Android](http://xbmc.org/theuni/2012/07/13/xbmc-for-android/). This opens possibilities for XBMC on low cost, low power, low noise, small form factor hardware, with hardware accelerated media playback.

The XBMC Android development was done on a [Pivox XIOS DS](http://www.pivosgroup.com/#!vstc0=xios) device, and I ordered one from [Amazon](http://amzn.to/M4zD8o). At $115 it is not exactly low cost, especially compared to mature platforms like the [Roku 2 XS](http://amzn.to/MTVgCf) for $98 or [Boxee Box](http://amzn.to/ORnvBV) for $180.

The XIOS DS is really small, here is a picture showing the size of a [Roku 2 XS](http://www.roku.com/roku-products) compared to a [XIOS DS](http://www.pivosgroup.com/#!vstc0=xios) compared to a [Zotac ZBOX Nano XS AD11](http://www.zotacusa.com/zbox-nano-xs-ad11-plus.html), compared to a [Pulse Eight Pulse Box](http://www.pulse-eight.com/store/products/107-pulsebox-xbmc-based-home-theatre-pc.aspx):

[![Size.Compare](/media/2012/07/size-compare_thumb.jpg)](/media/2012/07/size-compare.jpg)

“Piovs” vs. “Pivos”; while unpacking the box I found this little gem printed on the box, one would think that spelling your company name correctly on the packaging is important:

[![Pivos.Box.Back](/media/2012/07/pivos-box_-back_thumb.jpg)](/media/2012/07/pivos-box_-back_.jpg)

If you’re interested in an a full unboxing, [look here](http://www.avsforum.com/t/1414297/pivos-xios-ds-media-play-the-semiofficial-thread).

I installed the box, powered it up, and it takes about 90s to power up, much longer compared to the Roku, Boxee or [OpenElec](http://openelec.tv/).

Navigation using the included IR remote is a bit clunky, the UI has no indication of where the current focus is, and the Ok button sometimes needs to be pressed twice. I can’t really fault Android for this as the UI is intended for tablet use, not for remote use, but it is something that needs work. Here is a screenshot of the opening page:

[![Main.Screen](/media/2012/07/main-screen_thumb.jpg)](/media/2012/07/main-screen.jpg)

By default LAN and WiFi are both disable, if you click the down button, the settings icon will be active, and you can press the Ok button, once or a few times, and then enable the LAN card.

The box comes installed with [Android Gingerbread 2.3.4](http://developer.android.com/about/versions/android-2.3.4.html). The auto update functionality reports everything is up-to-date, but you can get the firmware and app updates from the [Pivos forum](http://www.pivosforums.com/viewtopic.php?f=11&t=669). I updated the firmware and apps, instructions are on the forum, here is a summary; download the firmware and apps RAR files, extract the contents to a microSD card, insert the microSD card in the box, navigate to \[Privacy\]\[Update System\] and select update:

[![Firmware.Update](/media/2012/07/firmware-update_thumb.jpg)](/media/2012/07/firmware-update.jpg)

After several minutes the new launch screen will be up:

[![Boot.After.Firmware](/media/2012/07/boot-after_-firmware_thumb.jpg)](/media/2012/07/boot-after_-firmware.jpg)

This screen is even less remote friendly. It took me several tries to figure out that I need to press the left and right buttons to see the different desktops, this would be equivalent to swiping left and right on the screen. After pressing the right button you will see a desktop with the settings icon:

[![Settings.After.Firmware](/media/2012/07/settings-after_-firmware_thumb.jpg)](/media/2012/07/settings-after_-firmware.jpg)

The updated version is [Android Ice Cream Sandwich 4.0.3](http://developer.android.com/about/versions/android-4.0.3.html).

I again needed to enable the LAN port, and set the correct time zone. Again the remote vs. touch had me struggling to enable the LAN port, you need to select network, then Ok, then right, and then up, and then Ok to enable the LAN port, highlighted below:

[![Ethernet.After.Firmware](/media/2012/07/ethernet-after_-firmware_thumb.jpg)](/media/2012/07/ethernet-after_-firmware.jpg)

I had the box up, and updated, I wanted to install XBMC, and I discovered that the announcement for XBMC on Android support did not include the availability of official binary packages, just source code, [and build instructions](http://wiki.xbmc.org/index.php?title=XBMC_for_Android_specific_FAQ).

I was not really up for setting up a build environment myself, and knowing the community, I started looking for unofficial builds, and I found one at the [Miniand Tech forums for the MK802](https://www.miniand.com/forums/forums/1/topics/136), but I did not want to install it until I could find confirmation if it would work on the DS. This morning I noticed a [new thread on the Pivos forum](http://www.pivosforums.com/viewtopic.php?f=24&t=811) containing a pre-release APK file for the DS.

I downloaded the APK file to the microSD card, and I needed to get to the file browser to install it. I gave up on fiddling with the remote, and I attached a USB mouse, from here on I clicked the apps icon, top right on main page, launched the file browser, opened the APK file, and installed XBMC:

[![Pivos.XBMC](/media/2012/07/pivos-xbmc_thumb.jpg)](/media/2012/07/pivos-xbmc_.jpg)

Once up and running, I wanted to add some network media, and this turned out to be a challenge, as NFS is not supported, yet SMB is. I normally allow anonymous/root NFS read-only access to my media files, all media players are happy with this. I do allow SMB access using a domain username and password, and most players are happy with this, just more typing. But, I was unable to enter any symbol characters, the standard XBMC remote control data entry box would not enable the symbol buttons. I tried a USB keyboard, but the “\_” character resulted in a “-“ character, and the UI would not close, unless you hit the Ok button on the remote several times. Next I tried setting up a XP VM image with the guest account enabled to allow anonymous SMB network access, and just browsing to the share, that also didn’t work, as I was prompted for a username and password. I created a test account on the XP image, using a simple username and password, and that allowed me to access to the folder. The remember credentials option did not work, every time I access the folder I have to re-enter the credentials. I’m sure NFS support will be added, and these issues resolved over time.

I used the series of [bird test videos](http://www.avsforum.com/t/1181902/official-codec-container-test-videos) to test network playback, I have MKV files ranging from 20mbps to 110mbps. I haven’t yet found a player that can play the 110mbps video without dropping frames. Unfortunately the OSD for XBMC on Android does not show frame statistics, but by visual observation stuttering started around the 38Mbps mark. Note that these MKV files only contains a video stream, no audio or other streams.

I was disappointed as I couldn’t get any of my AVC/H264/DTS/AC3/AAC based movie files to play. Since the video only files played ok, I assume it is due to the audio stream types, or a configuration option, but I’m not sure.

The platform is promising, but in its current Alpha state it still needs lots of work, both in terms of remote control based Android navigation, and XBMC on Android stability. I will definitely try again once a more stable version is released for direct deployment via the appstore.
