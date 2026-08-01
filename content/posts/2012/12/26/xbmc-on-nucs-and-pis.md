---
title: XBMC on NUC&rsquo;s and Pi&rsquo;s
date: '2012-12-26T22:44:44+00:00'
url: /2012/12/26/xbmc-on-nucs-and-pis/
categories:
- review
tags:
- intel
- pivos
- raspberry-pi
- xbmc
- zotac
post_id: '395'
---
I’m still looking for the perfect [XBMC](http://xbmc.org/) hardware; must be small, silent, low power, low heat, 1080p, HD audio, and play anything I throw at it without a hiccup. The number of options are increasing, but no clear winner.

I previously tested a [XIOS DS](http://www.amazon.com/gp/product/B0088IGPM8/ref=as_li_ss_tl?ie=UTF8&tag=pievilsblo-20&linkCode=as2&camp=1789&creative=390957&creativeASIN=B0088IGPM8) running [XBMC on Android](/2012/07/22/xbmc-for-android-on-pivos-xios-ds/), and [XBMC on Linux](/2012/09/08/xbmc-for-linux-on-pivos-xios-ds/). At that time the builds were pretty unstable. I retested the latest Linux builds, that also include XBMC 12 Frodo RC2.

I tested using the [121512 release](http://www.pivosforums.com/viewtopic.php?f=11&t=941), after rebooting, I just saw a black screen. I could see that the AVR had negotiated HDMI audio, but the screen remained black. Reading the [forum thread](http://www.pivosforums.com/viewtopic.php?f=25&t=2008) there were many reports of similar problems, same symptoms, leave the system up, and after 15 minutes XBMC loaded. The [bug](https://github.com/Pivosgroup/buildroot-linux-kernel/commit/efe8412048e0ea16f3d0d81ff1183cbb546084f6) has been identified, but not yet fixed in official firmware. I used a [community build](http://www.pivosforums.com/viewtopic.php?f=25&t=1987) that included the fix, and the system booted normally.

I noticed that there are now [two hardware variants](http://www.pivosforums.com/viewtopic.php?f=12&t=2071) of the DS, a M1 version, that I have, and a new M3 version, that [apparently](http://www.j1nx.nl/xbmc-amlogic-8726-m-pivos-xios-an-initial-investigation/) includes a faster processor and more memory, and is currently only shipped in the EU and UK. This seems to be consistent with the [AMLogic AML8726-M](http://www.amlogic.com/product02.htm) SoC device containing an ARM Cortex-A9 and a Mali-400 graphic processor.

The playback results were rather disappointing, no HD audio pass-through, high bitrate content would stutter, and I would get frequent network re-buffering. This device still shows promise, but not in its current state.

I tested [XBMC](http://wiki.xbmc.org/index.php?title=Raspberry_Pi) on a [Raspberry Pi](http://www.raspberrypi.org/). The Pi devices are pretty cheap at $35, but the units at this price have very long lead times. Instead I opted to buy an in-stock [Model B Revision 2](http://www.amazon.com/gp/product/B009SQQF9C/ref=as_li_ss_tl?ie=UTF8&tag=pievilsblo-20&linkCode=as2&camp=1789&creative=390957&creativeASIN=B009SQQF9C) unit from Amazon, and also [a case](http://www.amazon.com/gp/product/B008TDBIDI/ref=as_li_ss_tl?ie=UTF8&tag=pievilsblo-20&linkCode=as2&camp=1789&creative=390957&creativeASIN=B008TDBIDI).

The Pi Model B Revision 2 uses the [Broadcom BCM2835](http://www.broadcom.com/products/BCM2835) SoC device containing an [ARM1176JZ-F](http://www.arm.com/products/processors/classic/arm11/arm1176.php) with [VideoCore IV](http://www.broadcom.com/products/Cellular/Mobile-Multimedia-Processors/BCM2763) graphic processor.

Deploying XBMC to a Pi is rather more involved compared to the DS, and I opted to use the [Raspbmc](http://www.raspbmc.com/) distribution that includes easy to use [tools for Windows](http://www.raspbmc.com/wiki/user/windows-installation/). The deployment tool creates a bootable SD card, that then retrieves and installs the latest builds over the internet, similar to many Linux network boot disk installers.

The playback results were rather disappointing, no HD audio support, high bitrate content would stutter, and I would get very frequent network re-buffering.

Similar to openELEC that provides a XBMC plugin for OS configuration, Raspbmc configuration in XBMC is done using the Raspbmc plugin. When I first clicked the plugin I thought it did nothing, and after several more remote clicks it suddenly displayed and did whatever my remote clicks did, causing a restart. The plugin provides lots of configuration options, including switching of XBMC versions, downloading and running nightly builds, and advanced configuration, but really it is super slow to load up.

XBMC on the DS supported HD audio passthrough, but Raspbmc did not include HD audio support. The plugin allowed me to enable the XBMC AudioEngine, with a warning that it may not work. After restarting XBMC with AE enabled, there were options for HD audio, but AE did not detect the HDMI audio output device and only offered audio output over analog or SPDIF.

[MPEG2](http://www.raspberrypi.com/mpeg-2-license-key/) and [VC-1](http://www.raspberrypi.com/vc-1-license-key/) codecs have to be purchased for the Pi, but as my test results were disappointing, I did not bother purchasing the codecs.

I tested one of the new [Intel Next Unit of Computing](https://www-ssl.intel.com/content/www/us/en/motherboards/desktop-motherboards/next-unit-computing-introduction.html?) devices, specifically the [DC3217IYE](http://www.amazon.com/gp/product/B0093LINVK/ref=as_li_ss_tl?ie=UTF8&tag=pievilsblo-20&linkCode=as2&camp=1789&creative=390957&creativeASIN=B0093LINVK). The device is barebones, and I used Kingston [KVR16S11K2/16](http://www.amazon.com/gp/product/B008TYIEVQ/ref=as_li_ss_tl?ie=UTF8&tag=pievilsblo-20&linkCode=as2&camp=1789&creative=390957&creativeASIN=B008TYIEVQ) 16GB memory and a Kingston [SMS100S2/64G](http://www.amazon.com/gp/product/B0062CHMZG/ref=as_li_ss_tl?ie=UTF8&tag=pievilsblo-20&linkCode=as2&camp=1789&creative=390957&creativeASIN=B0062CHMZG) 64GB mSATA card. Oh, and you need your own power cable, I happened to have a spare [Monoprice 7687](http://www.monoprice.com/products/product.asp?c_id=102&cp_id=10228&cs_id=1022806&p_id=7687&seq=1&format=2) 3-prong power cable lying around that fit the PSU.

I don’t know what to make of it, but Intel included a gadget in the box, that plays the Intel jingle every time you open the box. I’m inclined to think that they could have included a power cable instead of the jingle gadget, but my kids do enjoy playing with the box, so it may have some marketing value.

Here are a few unboxing pictures:  
[![IMG_1384_DxO](/media/2012/12/img_1384_dxo_thumb.jpg)](/media/2012/12/img_1384_dxo.jpg)[![IMG_1385_DxO](/media/2012/12/img_1385_dxo_thumb.jpg)](/media/2012/12/img_1385_dxo.jpg)[![IMG_1386_DxO](/media/2012/12/img_1386_dxo_thumb.jpg)](/media/2012/12/img_1386_dxo.jpg)[![IMG_1388_DxO](/media/2012/12/img_1388_dxo_thumb.jpg)](/media/2012/12/img_1388_dxo.jpg)[![IMG_1389_DxO](/media/2012/12/img_1389_dxo_thumb.jpg)](/media/2012/12/img_1389_dxo.jpg)[![IMG_1390_DxO](/media/2012/12/img_1390_dxo_thumb.jpg)](/media/2012/12/img_1390_dxo.jpg)[![IMG_1391_DxO](/media/2012/12/img_1391_dxo_thumb.jpg)](/media/2012/12/img_1391_dxo.jpg)[![IMG_1392_DxO](/media/2012/12/img_1392_dxo_thumb.jpg)](/media/2012/12/img_1392_dxo.jpg)[![IMG_1393_DxO](/media/2012/12/img_1393_dxo_thumb.jpg)](/media/2012/12/img_1393_dxo.jpg)[![IMG_1394_DxO](/media/2012/12/img_1394_dxo_thumb.jpg)](/media/2012/12/img_1394_dxo.jpg)[![IMG_1395_DxO](/media/2012/12/img_1395_dxo_thumb.jpg)](/media/2012/12/img_1395_dxo.jpg)[![IMG_1396_DxO](/media/2012/12/img_1396_dxo_thumb.jpg)](/media/2012/12/img_1396_dxo.jpg)[![IMG_1397_DxO](/media/2012/12/img_1397_dxo_thumb.jpg)](/media/2012/12/img_1397_dxo.jpg)[![IMG_1398_DxO](/media/2012/12/img_1398_dxo_thumb.jpg)](/media/2012/12/img_1398_dxo.jpg)[![IMG_1399_DxO](/media/2012/12/img_1399_dxo_thumb.jpg)](/media/2012/12/img_1399_dxo.jpg)

I installed openELEC v3 Beta 6, that includes XBMC 12 Frodo RC2.

Most things worked fine, audio output device was automatically detected and set to HDMI, but HD audio passthrough did not work, and several videos showed artifacts during playback, even worse, some videos caused lots of artifacts and caused the device to hang. I assume the video issue is a problem with the Intel HD graphics driver being picked up by openELEC.

I am using a D-Link DSM-22 RF remote (I wish I can find more for sale), and I found that the key presses were erratic, after moving the RF dongle from a rear USB port to the front USB port, everything worked fine. I assume there is some interference near the back of the unit.

Physical size wise the NUC compares well against a [Zotac ZBox Nano XS AD11 Plus](http://www.zotacusa.com/zbox-nano-xs-ad11-plus.html), but price wise the NUC is more expensive once memory and flash storage is added.

The Nano XS is a Fusion based device, which means it will never get HD audio passthrough (AMD drivers lack HD audio support on Linux), so if openELEC and Intel can resolve the video corruption on the NUC, and XBMC can resolve the HD passthrough problem with my setup, the NUC would be a good contender.

I am still running openELEC on my [Zotac ZBOX ID84](http://www.zotacusa.com/zbox-id84-plus.html) system with a NVidia GeForce GT520M GPU. This GPU supports HD audio passthrough, but as with my other devices, it does not work on my setup. The problem appears to be related to how XBMC AudioEngine targets audio, and that instead of sending the audio to the AVR, it sends it to the television, but this is speculation on my part. I logged a ticket with [openELEC](https://github.com/OpenELEC/OpenELEC.tv/issues/1618) and [XBMC](http://trac.xbmc.org/ticket/13793), and there is a forum thread at [openELEC](http://openelec.tv/forum/68-audio/55638-openelec-version-2952-yamaha-amp-no-hd-audio-over-hdmi) with other Yamaha and Onkyo AVR users reporting similar problems, but nobody from openELEC or XBMC has yet responded :(

Here is a comparison of device sizes, top is Raspberry Pi, then XIOS DS, then ZBOX AD11, then Intel NUC, and ZBOX ID84 at the bottom:  
[![PV_20121226_5060_DxO](/media/2012/12/pv_20121226_5060_dxo_thumb.jpg)](/media/2012/12/pv_20121226_5060_dxo.jpg)[![PV_20121226_5061_DxO](/media/2012/12/pv_20121226_5061_dxo_thumb.jpg)](/media/2012/12/pv_20121226_5061_dxo.jpg)

My quest continues.
