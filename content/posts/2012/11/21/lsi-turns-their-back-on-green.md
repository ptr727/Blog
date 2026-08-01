---
title: LSI turns their back on Green
date: '2012-11-21T23:02:00+00:00'
url: /2012/11/21/lsi-turns-their-back-on-green/
categories:
- power
- problem
- review
- storage
tags:
- adaptec
- lsi
- raid
- windows
post_id: '357'
---
I previously blogged [here](/2009/06/12/power-saving-sata-raid-controller/) and [here](/2009/07/17/power-saving-raid-controller-continued/) on my research into finding a power saving RAID controllers.

I have been using [LSI MegaRAID SAS 9280-4i4e](http://www.lsi.com/products/storagecomponents/Pages/MegaRAIDSAS9280-4i4e.aspx) controllers in my Windows 7 workstations and [LSI MegaRAID SAS 9280-8e](http://www.lsi.com/products/storagecomponents/Pages/MegaRAIDSAS9280-8e.aspx) controllers Windows Server 2008 R2 servers. These controllers work great, my workstations go to sleep and wake up, and in workstations and servers drives spin down when not in use.

I am testing a new set of workstation and server systems running Windows 8 and Server 2012, and using the “2nd generation” PCIe 3.0 based [LSI RAID controllers](http://www.lsi.com/products/storagecomponents/Pages/6GBSATA_SASRAIDCards.aspx). I’m using [LSI MegaRAID SAS 9271-8i](http://www.lsi.com/products/storagecomponents/Pages/MegaRAIDSAS9271-8i.aspx) with [CacheVault](http://store.lsi.com/store.cfm/CacheVault/CacheVault/LSI00297/) and [LSI MegaRAID SAS 9286CV-8eCC](http://www.lsi.com/products/storagecomponents/Pages/MegaRAIDSAS9286CV-8eCC.aspx) controllers.

I am unable to get any of the configured drives to spin down on either of the controllers, nor in Windows 8 or Windows Server 2012.

LSI has not yet published any Windows 8 or Server 2012 drivers on their support site. In September 2012, after the public release of Windows Server 2012, LSI support told me drivers would ship in November, and now they tell me drivers will ship in December. All is not lost as the 9271 and 9286 cards are detected by the default in-box drivers, and appear to be functional.

I had hoped the no spin-down problem was a driver issue, and that it would be corrected by updated drivers, but that appears to be wishful thinking.

I contacted LSI support about the drive spin-down issue, and was referred to this August 2011 [KB 16563](http://kb.lsi.com/KnowledgebaseArticle16563.aspx), pointing to [KB 16385](http://kb.lsi.com/KnowledgebaseArticle16385.aspx) stating:

> newer versions of firmware no longer support DS3; the newest version of firmware to support DS3 was 12.12.0-0045\_SAS\_2108\_FW\_Image\_APP-2.120.33-1197

When I objected to the removal, support replied with this canned quote:

> In some cases, when Dimmer Switch with DS3 spins down the volume, the volume cannot spin up in time when I/O access is requested by the operating system.  This can cause the volume to go offline, requiring a reboot to access the volume again.

LSI basically turned their back on green by disabling drive spin-down on all new controllers and new firmware versions.

I have not had any issues with this functionality on my systems, and spinning down unused drives to save power and reduce heat is a basic operational requirement. Maybe there are issues with some systems, but at least give me the choice of enabling it in my environment.

A little bit of searching shows I am not alone in my complaint, see [here](http://www.servethehome.com/lsi-sas-2108-megaraid-power-save-active-drives/#comment-22499) and [here](http://hardforum.com/showthread.php?t=1723677).

And from Intel a November 2012 [KB 033877](http://www.intel.com/support/motherboards/server/sb/CS-033877.htm) that they have disabled drive power save on all their RAID controllers, maybe not that surprising given that Intel uses rebranded LSI controllers.

After a series of overheating batteries and S3 failures, I have long ago given up on [Adaptec](http://www.adaptec.com/) RAID controllers, but this situation with [LSI](http://www.lsi.com/) is making me take another look at them.

Adaptec is advertising [Intelligent Power Management](http://www.adaptec.com/en-us/_common/ipm/) as a feature of their controllers, I ordered a [7805Q](http://www.adaptec.com/en-us/products/series/7q/) controller, and will report my findings in a future post.
