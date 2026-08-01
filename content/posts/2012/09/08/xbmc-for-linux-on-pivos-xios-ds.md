---
title: XBMC for Linux on Pivos XIOS DS
date: '2012-09-09T02:41:59+00:00'
url: /2012/09/08/xbmc-for-linux-on-pivos-xios-ds/
categories:
- review
tags:
- htpc
- pivos
- xbmc
post_id: '334'
---
Pivos released a [XBMC build for Linux](http://www.pivosforums.com/viewtopic.php?f=11&t=941), and I tried it out.

The [Pivos XIOS DS](http://www.pivosgroup.com/xios.html) is very small (less than 5” x 5” x 1”) HTPC supporting hardware accelerated 1080p video and HD audio playback. The XIOS DS supports [XBMC for Android](http://www.pivosforums.com/viewtopic.php?f=24&t=872), and [XBMC for Linux](http://www.pivosforums.com/viewtopic.php?f=11&t=941), with native hardware acceleration. I reviewed the [Android port of XBMC](/2012/07/22/xbmc-for-android-on-pivos-xios-ds/) in a previous post.

The XIOS DS is available for [$115 at Amazon](http://amzn.to/M4zD8o), placing it, price wise, between the [$98 Roku 2 XS](http://amzn.to/MTVgCf) and the [$178 Boxee Box](http://amzn.to/ORnvBV).

I downloaded the [09/07/12 firmware](http://www.pivosforums.com/XIOS_DS/XBMC/xbmc-XIOS-Linux-090712.zip) release, and installed it using the system update procedure; extract update.img to MicroSD, hold reset button on back of unit, plug in power, release reset button when update screen displays.

[![Firmware.Update.Reset](/media/2012/09/firmware-update-reset_thumb.jpg)](/media/2012/09/firmware-update-reset_.jpg)

[![Firmware.Update.Linux](/media/2012/09/firmware-update-linux_thumb.jpg)](/media/2012/09/firmware-update-linux_.jpg)

XBMC launched immediately on reboot, very similar to the XBMC for Linux [OpenELEC](http://openelec.tv/) experience.

[![XIOS.XBMC](/media/2012/09/xios-xbmc_thumb.jpg)](/media/2012/09/xios-xbmc_.jpg)

[![XIOS.XBMC.1](/media/2012/09/xios-xbmc_-1_thumb.jpg)](/media/2012/09/xios-xbmc_-1.jpg)

[![XBMC.System](/media/2012/09/xbmc-system_thumb.jpg)](/media/2012/09/xbmc-system.jpg)

A quick zoom adjustment and the UI fits on the screen without the need to adjust resolution.

[![XBMC.Zoom](/media/2012/09/xbmc-zoom_thumb.jpg)](/media/2012/09/xbmc-zoom_.jpg)

Unlike the Android version where I had to use a mouse and keyboard, I could use the included IR remote to perform all operations. And unlike the Android version, where I had to create special guest access SMB shares because NFS was not supported, the Linux version supported NFS shares with no problems.

I did encounter the same problem as current OpenELEC builds, where some addons are reported as broken in the repository, but as with OpenELEC, this did not prevent movie and series media from being correctly identified, or played.

I tested a variety of media formats, all in MKV containers, and all played without issue. I did not test DTS, DTS-HD, AC3, and TrueHD passthrough, as this build of XBMC is based on v11 Eden that does not support HD audio (included in the unreleased v12 Frodo), and I had the box directly connected to a television over HDMI, so all audio was downmixed to two channels.

All in all the Linux port of XBMC on the XIOS DS worked much better than the Android port, but as the Android port is classified as Alpha and the Linux port classified as Beta, that is expected.

The XIOS DS running Linux XBMC is not up to Boxee Box standards yet, but it may be a contender.
