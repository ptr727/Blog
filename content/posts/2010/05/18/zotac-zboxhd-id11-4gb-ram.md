---
title: Zotac ZBOXHD-ID11 4GB RAM
date: '2010-05-19T02:46:00+00:00'
url: /2010/05/18/zotac-zboxhd-id11-4gb-ram/
categories:
- review
tags:
- amazon
- boxee
- codec
- coreavc
- crash
- htpc
- intel
- ion
- minipc
- zbox
- zotac
post_id: '102'
---
In this post I describe my experience while upgrading the BIOS, in order to support 4GB of memory.

This is the third post in a [series of posts related to the Zotac ZBOX ZBOXHD-ID11](/2010/05/zotac-zbox-mini-pc-zboxhd-id11.html).

Summary:   
\- 4GB is supported after upgrading the BIOS.   
\- BIOS has to be updated using less than 4GB, else ID11 fails to post.


\[Update: 20 May 2010\]   
After writing this post, the machine started bluescreen / BSOD crashing.   
Mostly MEMORY\_MANAGEMENT / 0x0000001A errors, with occasional 0x000000BE and 0x0000003B crashes.   
When I initially installed the 4GB RAM, I ran [memtest](http://www.memtest.org/) for one cycle, and the RAM tested fine. I just reran memtest, and it is reporting that the memory as bad.   
I replaced the memory with a new stick, I ran memtest overnight, and everything seems back to normal.   
I hope it was just a bad stick, and not the ID11 that killed the memory.


When I ordered my ID11, I also ordered a [4GB Kingston SODIM RAM](http://www.ec.kingston.com/ecom/configurator_new/partsinfo.asp?root=&LinkBack=&ktcpartno=KVR800D2S6/4G) stick.   
When I received the ID11, the specs said 2GB only, and after contacting Zotac support, and posting in their [support forum](http://www.zotacusa.com/forum/topic/2791-id11-can-it-use-4gb-memory/), they confirmed that 4GB is not supported.   
I reverted to using a [2GB Kingston SODIM RAM](http://www.ec.kingston.com/ecom/configurator_new/partsinfo.asp?root=&LinkBack=&ktcpartno=KVR800D2S5/2G) stick.

I was pleasantly surprised when Zotac [announced a BIOS update](http://www.zotacusa.com/downloads/?cat=223) that added 4GB support.

The BIOS changes are described as follows:   
Version 05/11/10   
.Added support on 4GB memory modules   
.Added CMOS selection on Logo LED

I [downloaded](http://downloads.zotac.com/mediadrivers/mb/bios/pa140.zip) the BIOS update, extracted the contents, and tried running the AFUWIN AMI BIOS update utility. After a warning message appeared telling me to not run other apps and not to power down, on clicking ok, nothing happened. I tried again this time running AFUWIN.exe as administrator, still nothing.

I went to the [AMI](http://www.ami.com/) site, and [downloaded](http://www.ami.com/support/downloadagreement.cfm?DLFile=support/downloads/amiflash.zip&InpDrvID=90) their latest Windows BIOS update utility. Since I was running Windows 7 Ultimate x64, I ran AFUWINx64.exe, this binary automatically UAC prompted for elevated access, and presented this warning:   
[![](/media/2010/05/ami-warn5.png?w=300)](/media/2010/05/ami-warn5.png)

I opened the A140PA19.rom file, and the information tab showed the following:   
[![](/media/2010/05/ami-information1.png?w=300)](/media/2010/05/ami-information1.png)

I started the flash, and got this warning:   
[![](/media/2010/05/ami-warn-11.png?w=300)](/media/2010/05/ami-warn-11.png)

I accepted, and the flash completed:   
[![](/media/2010/05/ami-done1.png?w=300)](/media/2010/05/ami-done1.png)

I rebooted, and the POST screen showed a CMOS Checksum Bad error:   
[![](/media/2010/05/2010-05-1815-32-351.jpg?w=300)](/media/2010/05/2010-05-1815-32-351.jpg)

I pressed F1 to enter setup, and I made the following changes:   
\[Exit\] \[Load Optimal Defaults\]   
\[Advanced\] \[PC Health Monitor\] \[CPUFAN TargetTemp Value\] = 50   
\[Advanced\] \[IDE Configuration\] \[Configure SATA as\] = AHCI   
\[Advanced\] \[PCIPnP\] \[Plug & Play OS\] = Yes

The two BIOS changes are visible under these sections:   
\[Chipset\] \[North Bridge Configuration\] “PCI MMIO Allocation: 4GB to 3072MB”   
\[Chipset\] \[South Bridge Configuration\] \[LOGO LED indicator:\]

I rebooted, and everything worked fine.

Next I powered down, and replaced the 2GB RAM with 4GB RAM.

On reboot the following changes were visible on the POST screen and in the BIOS:   
[![](/media/2010/05/2010-05-1818-13-351.jpg?w=300)](/media/2010/05/2010-05-1818-13-351.jpg)

[![](/media/2010/05/2010-05-1818-12-351.jpg?w=300)](/media/2010/05/2010-05-1818-12-351.jpg)

Booting into Windows, the following 4GB related changes were visible:   
[![](/media/2010/05/properties-4gb1.png?w=300)](/media/2010/05/properties-4gb1.png)  
[![](/media/2010/05/task-manager-4gb1.png?w=300)](/media/2010/05/task-manager-4gb1.png)

So far everything appears to work fine.   
One of these days I will really get to testing media playback performance.

By the way.   
In my [first impressions post](/2010/05/zotac-zboxhd-id11-first-impressions.html) I reported that the ID11 came with the wrong power cable. Zotac support sent me the correct replacement cables free of charge:   
[![](/media/2010/05/power-plug-new4.jpg?w=300)](/media/2010/05/power-plug-new4.jpg)


