---
title: Power Saving SATA RAID Controller
date: '2009-06-12T19:37:00+00:00'
url: /2009/06/12/power-saving-sata-raid-controller/
categories:
- power
- review
- storage
tags:
- 3ware
- adaptec
- nas
- raid
- sata
- seagate
- wd
post_id: '88'
---
I've been a longtime user of Adaptec SATA RAID cards ([3805](http://www.adaptec.com/en-US/products/Controllers/Hardware/sas/value/SAS-3805/), [5805](http://www.adaptec.com/en-US/products/Controllers/Hardware/sas/performance/SAS-5805/), [51245](http://www.adaptec.com/en-US/products/Controllers/Hardware/sas/performance/SAS-51245/)), but over the years I've become more energy saving conscious, and the Adaptec controllers did not support Windows power management.



My workstations are normally running in the "Balanced" power mode so that they will go to sleep after an hour, but sometimes I need to run computationally intensive tasks that leaves the machines running 24/7.



During these periods the disks don't need to be on and I want the disks to spin down, like they would had they been directly connected and not in a RAID configuration.



I was building a new system with 4 drives in RAID10, and I decided to the try a 3Ware / AMCC SATA [9690SA-4I](http://www.3ware.com/products/sas-9690SA.asp) RAID controller. Their sales support confirmed that the card does support native Windows power management.



I also ordered a battery backup unit with the card, and my first impressions of installing the battery backup unit was less than impressive. The BBU comes with 4 plastic screws with pillars, but the 9690SA card only had one mounting hole. After inserting the BBU in the IDC header I had to pull it back out and adjust it so that it would align properly.



After running the card for a few hours I started getting battery overheating warnings. The BBU comes with an extension cable, and I had to use the extension cable and mount the battery away from the controller board. After making this adjustment the BBU seemed to operate at normal temperature.



Getting back to installation, the 3Ware BIOS utility is very rudimentary (compared to Adaptec), I later found out that the 3Ware Disk Manager 2 (3DM2) utility is not much better. The BIOS only allowed you to create one boot volume, and the rest of the disk space was automatically allocated. The BIOS also only supports INT13 booting from the boot volume.



I installed Vista Ultimate x64 on the boot volume, and used the other of the volume for data. I also installed the 3DM2 management utility, and the client tray alerting application. The client utility does not work on Vista because it requires elevation, and elevation s not allowed for auto start items. The 3DM2 utility is a web server and you connect using your web browser.



At first the lack of management functionality did not bother me, I did not need it, and the drives seemed to perform fine. After a month or so I noticed that I was getting more and more controller reset messages in the eventlog. I contacted 3Ware support, and they told me they see CRC errors and that the fanout cable was probably bad. I replaced the cable, but the problems persisted.



The CRC errors reminded me of problems I had with Seagate ES2 drives on other systems, and I updated the firmware in the 4 500 GB Seagate drives I was using. No change, same problem.



I needed more disk space anyway, so I decided to upgrade the 500GB Seagate drives to 1TB WD Caviar Black drives. The normal procedure would be to remove the drives one by one, insert the new drive, wait for the array to rebuild, and when all drives have been replaced, to expand the volume.



A 3Ware KB article confirmed this operation, but, there was no support for volume expansion, what?



In order to expand the volume I would need to boot from DOS, Windows is not supported, run a utility to collect data, send the data to 3Ware, and they would create a custom expansion script for me that I then need to run against the volume to rewrite the META data. They highly recommend that I backup the data before proceeding.



I know the Adaptec Storage Manager (ASM) utility does support volume expansion, I've used it, it's easy, it's a right click in the GUI.



I never got to the point of actually trying the expansion procedure. After swapping the last drive I ran a verify, and one of the mirror units would not go past 22%. Support told me to try various things, disable scheduling, enable scheduling, stop the verify, restart the verify. When they eventually told me it seems there are some timeouts, and that the cause was Native Command Queuing (NCQ) and a bad BBU, I decided I had enough.



The new Adaptec 5-series cards do support [power management](http://www.adaptec.com/en-us/_common/ipm/?hpBan=IPMHEROswf-US&utm_source=hp&utm_medium=banner&utm_campaign=IPMHERO-US), but unlike the 9690SA card they do not support native Windows power management, and requires power savings to be enabled through the ASM utility.



I ordered an Adaptec [5445](http://www.adaptec.com/en-US/products/Controllers/Hardware/sas/performance/SAS-5445/) card, booted my system with the 9690SA still in place from WinPE, made an image backups using Symantec Ghost Solution Suite (SGSS), installed the 5445 card, created new RAID10 volumes, booted from WinPE, restored the images using Ghost, and Vista booted just fine.



From past experience I knew that when changing RAID controllers I had to make sure that the Adaptec driver would be ready after swapping the hardware, else the boot will fail. So before I swapped the cards and made the Ghost backup, I used regedit and changed the start type of the "arcsas" driver from disabled to boot. I know that SGSS does have support for driver injection used for bare metal restore, but since the Adaptec driver comes standard with Vista, I just had to enable it.



It has only been a few days, but the system is running stable with no errors. Based purely on boot times, I do think the WD WD1001FALS Caviar Black drives are faster than the Seagate ST3500320AS Barracuda drives I used before.



Let's hope things stay this way.



\[Updated: 17 July 2009\]

The Adaptec was not that power friendly after all.

Read the [continued post](/2009/07/power-saving-raid-controller-continued.html).


