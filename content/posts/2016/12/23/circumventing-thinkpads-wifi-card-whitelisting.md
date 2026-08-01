---
title: Circumventing ThinkPad's WiFi Card Whitelisting
date: '2016-12-23T20:10:45+00:00'
url: /2016/12/23/circumventing-thinkpads-wifi-card-whitelisting/
categories:
- problem
- solution
tags:
- intel
- thinkpad
- wifi
post_id: '1065'
---
What started as a simple Mini PCI Express WiFi card swap on a ThinkPad T61 notebook, turned into deploying a custom BIOS in order to get the card to work.

I love ThinkPad notebooks, they are workhorses that keep on going and going. I always keep my older models around for testing, and one of my old T61's had an [Intel 4965AGN](http://www.thinkwiki.org/wiki/Intel_PRO/Wireless_4965AGN_Mini-PCI_Express_Adapter) card, that worked fine with Windows 10, until the release of the Anniversary / [Redstone 1](https://en.wikipedia.org/wiki/Windows_10_version_history) update. After the RS1 update, WiFi would either fail to connect, or randomly drop out. The 4965AGN card is not supported by Intel on Win10, and the internet is full of problem reports of Win10 and 4965AGN cards.

Ok, no problem, I'll just get a cheap, reasonably new, with support for Win10, Mini PCIe WiFi card, and swap the card. I got an [Intel 3160](http://amzn.to/2inYrJM) dual band 802.11AC card and [mounting bracket](http://amzn.to/2h9WBev) for about $20. The 3160 is a [circa 2013](http://www.intel.com/content/www/us/en/wireless-products/wireless-product-selection-guide.html) card with Win10 support. I installed the card, booted, and got a BIOS error 1802: Unauthorized network card is plugged in.

This lead me to the discovery of ThinkPad [hardware whitelisting](http://www.thinkwiki.org/wiki/Problem_with_unauthorized_MiniPCI_network_card), where the BIOS only allows specific cards to be used, which lead me to [Middleton's BIOS](http://www.thinkwiki.org/wiki/Middleton%27s_BIOS), a custom T61 BIOS, that removes the hardware whitelisting, and enables SATA-2 support. I found working download links to the v2.29-1.08 Middleton BIOS [here](http://ali.dj/blog/sata-ii-support-for-lenovo-thinkpad-t61-x61-r61).

The BIOS update is packaged as a Win7 x86 executable or DOS bootable ISO image. As I'm running Win10 x64, and I could not find any CD-R discs around, I used [Rufus](https://rufus.akeo.ie/) to create a bootable DOS USB key, and I extracted the ISO contents using [7-Zip](http://www.7-zip.org/) to a directory on the USB key. The ISO is created using a bootable 1.44MB DOS floppy image, and AUTOEXEC.BAT launches "FLASH2.EXE /U", I created a batch file that does the same.

I removed the WiFi card, booted from USB, ran the flash, and got an error 1, complaining that flashing over the LAN is disabled. Ok, I enabled flashing the BIOS over the LAN in the BIOS, and rebooted.

I ran the update again, and this time I got error 99, complaining that BitLocker is enabled, and to temporarily disable BitLocker. I did not have BitLocker enabled, so I removed the hard drive and tried again, same error. Must be something in the BIOS, I disabled the security chip in the BIOS, tried again, and the update starts, but a minute or so later the screen goes crazy with INVALID OPCODE messages.

Hmm, maybe the updater does not like the FreeDOS boot image used by Rufus. Ok, let me create a MS-DOS USB key, uhh, on Win10, that turned out to be near impossible. Win10 does not include MS-DOS files, Rufus does not support custom locations for MS-DOS files, nor does it support getting them from floppy or CD images (readily available for [download](http://www.allbootdisks.com/)), the HP USB Disk utility complains my USB drive is locked, and writing raw images to USB result in a FAT12 disk structure that is too small to use. I say near impossible because I gave up, and instead went looking for an existing MS-DOS USB key I had made a long time ago. I am sure with a bit more persistence I could have found a way to create MS-DOS bootable USB keys on Win10, but that is an exercise of another day.

Trying again with a MS-DOS USB key, and voilà, BIOS flashed, and WiFi working.

I am annoyed that I had to go to this much trouble to get the new WiFi card working, but the best part of the exercise turns out to be the SATA-2 speed increase. This machine had a SSD drive, that I always found to be slow, but with the SATA-2 speed bump in Middleton's BIOS, the machine is noticeably snappier.

A couple hours later, my curiosity got the better of me, and I made my [own version](https://github.com/ptr727/rufus/commit/0ac0b5cfe2c03df15d56ae94b7e7e518c8f37213) of [Rufus](https://github.com/pbatard/rufus) that will allow formatting of MS-DOS USB drives on Win10. In the process I [engaged](https://github.com/pbatard/rufus/issues/870) in an interesting discussion with the author of Rufus. I say interesting, but it was rather frustrating, Microsoft removed the MS-DOS files from Win10, and Rufus refuses to add support for sourcing of MS-DOS files from a user specified location, citing legal reasons, and my reluctance to first report the issue to FreeDOS. Anyway, can code, have compiler, if have time, will solve problem.
