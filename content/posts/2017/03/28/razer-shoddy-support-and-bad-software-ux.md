---
title: Razer Shoddy Support and Bad Software UX
date: '2017-03-28T19:07:28+00:00'
url: /2017/03/28/razer-shoddy-support-and-bad-software-ux/
categories:
- problem
- review
tags:
- nec
- razer
post_id: '1251'
cover:
  alt: Synapse.3
  image: /media/2017/03/synapse-3.png
---
This post is just me venting my frustration at [Razer's](https://www.razerzone.com/) poor software user experience, and their shoddy support practices. I'm writing this after I just had to go and find a working mouse, so I could click a button on a dialog that had no keyboard navigation support.

I've been using Razer keyboards and mice for some time, love them, their software not so much. I had to replace an aging ThinkPad, and the newly released [Razer Blade Stealth](https://www.razerzone.com/gaming-systems/razer-blade-stealth) looked like a great candidate, small and fast, reasonably priced, should be perfect, well, not so much.

I keep my monitors color calibrated, and I cringe whenever I see side-by-side monitors that clearly don't match, or when somebody creates graphic content (yes you graphic artists using MacBooks to create content for PC software without proper color profiles) that looks like shades of vomit on a projector or a cheap screen, but I digress. My monitor of choice is [NEC](http://www.necdisplay.com/) and their native [SpectraView](http://www.necdisplay.com/spectra-view-II) color calibration software. Unfortunately, the Blade with its lower end Intel graphics processor, and HDMI port, does not support [DDC/CI](https://en.wikipedia.org/wiki/Display_Data_Channel), so no ability to color calibrate my monitor. My main monitor is a [NEC MultiSync EA275UHD](http://amzn.to/2mMJjMJ) 4K monitor, and the internal Intel graphics processor is frustratingly slow on this high resolution display. And, the HDMI connectivity would drop out whenever the monitor went into power saving mode. Why not use a more standard mini-DisplayPort connector, would not solve the speed problem, but at least would have resolved the connection reliability and allowed for proper color calibration.

To solve the problem, I decided to get a [Razer Core](https://www.razerzone.com/gaming-systems/razer-blade-stealth#ultrabook-desktop) with an [EVGA GeForce GTX 1070](http://amzn.to/2nIMZ1w) graphics adapter. The Core is an external USB and network dock, with a PSU and PCIe connector for a graphics card, all connected to the notebook by Thunderbolt 3 over a, too short, USB-C cable. I connected my monitor to the GTX 1070 DisplayPort connector, connectivity was fine, I could color calibrate my monitor, and the display performance with the GTX 1070 was fast, great. By the way, [JayzTwoCents](https://www.youtube.com/channel/UCkWQ0gDrqOCarmUKmppD7GQ) has a great [video](https://www.youtube.com/watch?v=QR5f1MwfugA) on the performance of external graphic cards.

But, my USB devices connected to the dock kept on dropping out. I found several threads on the Razer support forum complaining about [the same](https://insider.razerzone.com/index.php?threads/core-keeps-disconnecting.15013/) [USB problems](https://insider.razerzone.com/index.php?threads/razer-core-mouse-and-keyboard-via-usb-problem.14223/), and the threads are promptly closed with a contact support message. I contacted Razer support and they told me they are working on the problem, and closed my ticket. I contacted them again stating that closing my ticket did not resolve the problem, and they said my choice is RMA the device, with no known solution, or wait, and then they closed my ticket again. To this day this issue has not been resolved, and I have to connect my USB devices directly the notebook, defeating the purpose of a dock. They did publish a [FAQ](http://www.razersupport.com/gaming-systems/razer-core/) advising users to not use 2.4GHz WiFi, but to stick with 5GHz due to interference issues, so much for their hardware testing.

Now, let's talk about their [Razer Synapse](https://www.razerzone.com/synapse/) software, the real topic of this post. The software is used to configure all the Razer devices, and sync the device preferences across computers with a cloud account, neat idea. The color scheme and custom drawn controls of this software matches their edgy "brand", but their choice of thin grey font on a dark background fails in my usability book when used in a brightly lit office space.

![Synapse.1](/media/2017/03/synapse-1.png)

Whenever Windows 10 updates, the stupid Synapse software pops up while the install is still going, if you say yes, install now, then as expected the install fails due to Windows still installing. I logged the issue with Razer support, and they told me it is behaving as designed, really, designed to fail.

![Synapse.2](/media/2017/03/synapse-2.png)

So, today the Synapse software, again, prompts me to update, a frequent occurrence, and my mouse dies during the update, presumably because they updated the mouse driver, but this time I am prompted with a reboot required dialog. Dead mouse, no problem, have keyboard, tab over, wait, no keyboard navigation on the stupid owner drawn custom control dialog, no way to interact with the dialog without a mouse, just fail.

![Synapse.3](/media/2017/03/synapse-3.png)

Moral of the story, UX is important people, and I should just stick with ThinkPad or Microsoft Surface Book hardware, costs more, but never disappoints.
