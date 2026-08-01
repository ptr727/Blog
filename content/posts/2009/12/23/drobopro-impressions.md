---
title: DroboPro Impressions
date: '2009-12-24T03:49:00+00:00'
url: /2009/12/23/drobopro-impressions/
categories:
- review
- storage
tags:
- drobopro
- iscsi
- nas
post_id: '95'
---
In this post I am describing, and partly reviewing, my experience using a DroboPro over iSCSI.





I have been aware of of the [Drobo](http://www.drobo.com/ "Drobo") storage devices for some time now, but never used one or knew anybody that owned one.  

Recently a coworker's large home RAID system had a controller failure, and after recovering the data, he migrated to a [DroboPro](http://www.drobo.com/products/drobopro/index.php "DroboPro") using [iSCSI](http://en.wikipedia.org/wiki/ISCSI "iSCSI").

After he told me how quite the device is, and how little power it uses, I wanted to try one out myself.



As I always do before purchasing hardware or software, I wanted to visit the community forums to see what owners have to say about their products.

But, to gain access to the [Drobo Forums](http://www.drobospace.com/forums/ "Drobo Forums") you have to register, and to register you need a valid Drobo device serial number, so there really was no way to know what was being discussed before purchasing a device.

This does seem rather weird, makes me wonder if they want to hide something, and searching online I [found several other people](http://www.google.com/search?rlz=1C1GGLS_enUS351US352&sourceid=chrome&ie=UTF-8&q=drobo+forum+requires+serial "found several other people") that had similar feelings about Drobo's forum policy, some saying so more politely than others.



Searching for [DroboPro reviews](http://www.google.com/search?hl=en&safe=off&rlz=1C1GGLS_enUS351US352&q=drobopro+review+experience&aq=f&oq=&aqi= "DroboPro reviews") online, I found mixed results, I found questions being asked about DroboPro and iSCSI, and several very negative Drobo comments, specifically unhappy [Drobo Share](http://www.drobo.com/products/droboshare.php "Drobo Share") owners.

One particular item of interest was the [Drobo Users Community Forum](http://www.drobousers.com/forum/ "Drobo Users Forum"), where the site owner closed the site in response to his dissatisfaction with the device and Data Robotics.



Even with the uncertainty of the device capabilities and stability, I decided to try one out anyway.





When I got the device I was surprised by just how small it is, about the size of a small form factor computer.

I unpacked the device, it comes with USB, FireWire, Ethernet, power cables, a CD and a user guide.

What I found missing was a getting started guide, and I went to the DroboPro support KB site in search of getting started documentation, I found none.

Admittedly, after I already had the device working, and as I was throwing away the packaging, I found the getting started steps printed on a piece of packaging.

I think a simple brochure would have been much more helpful compared to printing it under a part of the pretty packaging, that I discarded as I opened the box.





In order to configure the device you must use a USB connection and the Drobo Dashboard software.

I installed the dashboard, I plugged in the Ethernet cable and USB cables, and powered on.

Nothing, the dashboard software would not see the DroboPro.

Long story short, it turns out that you may have only one cable connected at a time, and since I had Ethernet and USB, the USB did not connect.

Admittedly, the getting started steps on the packaging did say Ethernet OR USB OR FireWire, but I did not literally take this as USB ONLY.



I now have the DroboPro running, and the dashboard sees the device.

There are no drives in the DroboPro, and the status light in the first drive slot is red, this means add a drive.

Strangely, even without a drive in the DroboPro a drive did appear in disk manager, the drive size was reported as a very big negative number, and a 32MB partition of unknown type, weird.





I inserted the first drive ([Hitachi UltraStar A7K2000 2TB](http://www.hitachigst.com/portal/site/en/products/ultrastar/A7K2000/ "Hitachi UltraStar A7K2000 2TB")), the red light flashed for a bit, then turned green, and the second slot turned red.

I inserted the second drive, it turned green, and I continued inserting the remainder of the 8 drives.

While I was inserting the remainder of the drives, the second slot had some problem, I could hear the drive spinning up and down a few times, and then the slot turned red.

I replaced that drive with another, and the slot went back to green.



I went back to disk manager, and the previous 32MB disk was now gone, and instead there was a 2TB RAW drive, again a drive I did not create.

I opened the Drobo Dashboard volume manager, deleted the 2TB volume that was automatically created, and created a new 16TB NTFS volume.

The Drobo Dashboard automatically partitions and formats the volume for you, the supported file systems, on Windows, are FAT32 and NTFS.



While in the settings I changed the device settings to dual disk redundancy.

After applying this change, the device was busy for a few minutes flashing all drive lights, I assume while it was rearranging bits on the disks.





When you create a volume you must specify the partition file system format type.

My understanding is that the [BeyondRAID](http://www.drobo.com/resources/beyondraid.php "BeyondRAID") technology used by Drobo requires understanding of the file system format, this is how they can dynamically move files around, and dynamically adjust the volume size, something that is not possible with traditional block level RAID.



Although the logical volume is reported as 16TB in size, the actual available storage using 8 x 2TB drives is about 11TB.  

The logical volume size reported by the DroboPro to the OS is unrelated to the physical available storage size.

The Drobo documentation says one should create a volume as large as the maximum size you may ever need, and then simply add drives to back that storage as you need the space.



I tested this by creating 2 additional 16TB volumes, three times the physical storage capacity, and the drives showed up fine.

The one caveat is that if you ever format the partition, you must use quick format, regular format will fail.





While on the topic of sizes, the Drobo [mixes](http://en.wikipedia.org/wiki/Gigabyte "mixes") [SI](http://en.wikipedia.org/wiki/SI_prefix "SI") and [IEC](http://en.wikipedia.org/wiki/IEC_60027 "IEC") prefixes, they say TB and GB, but they really mean TiB and GiB.

I even found a post about this on their forum, and the moderator response was that "most people don't know the difference", with this type of indifference the confusion will never be properly addressed.





I wanted to delete the 2 test volumes, and before I did this I wanted to [USB Safely Remove](http://safelyremove.com/ "USB Safely Remove") the volume.

The safely remove failed, telling me that the device is in use, and that the DDService.exe was holding open the handles.

DDService.exe is the Drobo Dashboard Service.



Now was my opportunity to register with [Drobo Forum](http://www.drobospace.com/forums/ "Drobo Forum").

After posting my question, a moderator almost immediately responded saying that I should use the dashboard to power down the device, and that the dashboard will unmount the volume.

I did not want to power down, I just wanted to unmount the volume.

I even found a Drobo [support KB](http://support.datarobotics.com/app/answers/detail/a_id/251 "support KB") saying to use either the dashboard or the normal safely remove procedure.

Several users replied saying they have similar problems with the dashboard service preventing safe removal.



I deleted the two test volumes using the dashboard, it did appear to unmount them, and then reboot.

Still, one would expect the Drobo service to correctly respond to device removal notifications.





I wanted to know why the original drive in bay 2 had failed.

The dashboard does not display any diagnostic information, no drive power state, no SMART state, nothing.

When you right click on the dashboard tray icon there is an option to create a diagnostic report.

At first it seemed like the diagnostic report dialog hanged, then I noticed that DDService.exe crashed.

I restarted the dashboard and the service, and this time the report file was created on the desktop, to my surprised the file was encrypted.

Not allowing me access to any diagnostic information is highly unusual.



I found an old [forum post](http://www.drobousers.com/forum/index.php?topic=16.0 "forum post") on the now closed Drobo Users Community Forum, describing that the data file is a simple XOR.

But since the forum is closed the post was no longer available, fortunately the [google cache](http://74.125.155.132/search?q=cache:XM3JhcPl7Z4J:www.drobousers.com/forum/index.php%3Ftopic%3D16.0+drobo+log+decrypt&cd=1&hl=en&ct=clnk&gl=us "google cache") still has the information.

Unfortunately it turns out that the encryption on newer models have changed.



I opened a support ticket attaching my diagnostic file, and requested the reason for the drive failure, I also asked why the file is encrypted.

I received a reply stating that the drive experienced 2 timeouts, and that is why it was kicked out.

The reason for the encryption is that apparently the log contains details of the [BeyondRAID](http://www.drobo.com/resources/beyondraid.php "BeyondRAID") file movements, and that this is proprietary information.

Ok, I can understand not wanting to give away the secret sauce, but not making any diagnostic information available, and requiring tech support interaction for any questions will become a problem.





I was now ready to switch to iSCSI.

The PDF included on the CD was not much help, but the [KB articles](http://support.datarobotics.com/app/answers/detail/a_id/240/kw/iscsi/r_id/100004 "KB articles") on the Drobo support site was helpful.

The steps calls for; power up with USB only, configure using dashboard, power down using dashboard, disconnect USB, connect Ethernet, power up, dashboard will reconnect after a few minutes.



The steps say that for DroboPro connected to a switch you cannot use automatic IP configuration, and you must use a static IP.  

I could not see why no, so I ignored the steps and used automatic configuration, for whatever reason, it does not work.

I went back to USB, selected a static IP, rebooted, and this time after a few minutes the dashboard connected to the DroboPro, and the drive I had previously created re-appeared.



I assumed that the dashboard is configuring iSCSI targets for me,

I opened the Windows iSCSI Initiator, and as expected the target and device was already configured.





To test the device I started a robocopy of a large set of backup data from my PC to the DroboPro.

At this point I am not testing performance, I will do that later when I have the DroboPro connected to a dedicated Ethernet port.

The copy started, and I left the machine idle while it copied.



On returning later my machine had gone to sleep, and the DroboPro had gone to sleep, just the orange power light was on.

I woke up my machine, and noticed that the robocopy was still in progress, half way through a large file, but not resuming.

I waited, but the DroboPro did not wake up.

Every window I opened and every application I started on my PC would just hang.

In the end I had to reset my machine.



Back to the forum, and as before a moderator responded very quickly.

After a few back and forth questions, the moderator confirmed that it is a known problem with dashboard version 1.6.6 that I was using.

The suggested fix was to simply restart the dashboard and the dashboard service on wake from sleep.

This was not a reasonable solution for disappearing and hanging volumes will lead to data corruption.



I opened a support ticket, and was asked to revert to the older dashboard version 1.5.1.

On uninstalling the 1.6.6 dashboard, I received an error that I must be an administrator, but I am an administrator.

Support told me to disable UAC, and then uninstall.



This is rather surprising, Windows 7 has already shipped and the Drobo software is still not Vista / UAC ready.

On installing dashboard 1.5.1 I found that it is even more Vista unfriendly, the dashboard requires elevation, is added to the startup group, but applications requiring elevation are not allowed to auto start.

Even with the UAC quirks, so far with dashboard 1.5.1 I have not had any hanging problems on resume from sleep.





The dashboard includes an email alert feature.

But after I set it up, and pulled a drive, I did not receive an email alert.

Back to the forum, and a confirmation that the email alert is generated by the dashboard user session process.

This means that no user logged in, no email alert.





I find it rather weird that Drobo implemented [iSCSI](http://www.drobo.com/resources/iscsi.php "iSCSI"), and uses words like "[enterprise ready](http://www.google.com/search?hl=en&safe=off&rlz=1C1GGLS_enUS351US352&q=drobopro+enterprise+site:drobo.com&btnG=Search&aq=f&oq=&aqi= "enterprise ready")", "[enterprise level](http://www.google.com/search?hl=en&safe=off&rlz=1C1GGLS_enUS351US352&q=drobopro+enterprise+site:drobo.com&btnG=Search&aq=f&oq=&aqi= "enterprise level")", and achieved "[VMWare Ready](http://www.drobo.com/vmware/index.php "VMWare Ready")" certification, yet there is not a single enterprise level feature in the product.

And not that I expect enterprise level reliability or performance in a consumer device, but basic functionality that is found in almost all comparable devices.

- iSCSI and IP connectivity, but no web management interface.
- USB for setup requires proximity to a physical machine, no remote management, and no virtual machine provisioning.
- No DHCP support when connected to a LAN.
- No raw volume management, must be a supported file system, must be managed by dashboard app.
- I have to trust DroboPro with my data, but there is no diagnostic or health status.
- I have to trust Data Robotics, but the forum is closed and diagnostic logs are encrypted.
- Email alerts requires a user to be logged in, if I was logged in I would not need an email alert.
- Software that is not fully Vista compatible, even after Windows 7 already shipped.
- Software that shipped with known problems that could cause data corruption.



The [DroboElite](http://www.drobo.com/Products/droboelite.php) is more than double the price of a DroboPro.

The main differences between DroboPro and DroboElite are dual Ethernet ports, multi host access to volumes, and more volumes.

Although I do not have one to test, from what I can gather in documentation and the forum, none of the items above are any different.



As a direct attached USB or FireWire storage device some of the above mentioned items would be irrelevant, but iSCSI, I really expected more.





Next up, I'll move the DroboPro from my workstation to my W2K8R2 server on a dedicated Ethernet port.  

This will give me the ability to do some performance and benchmarking comparison between RAID6 DAS and the DroboPro BeyondRAID iSCSI.



\[Update: 30 January 2010\]

[DroboPro vs. QNAP TS-859 Pro](/2010/01/data-robotics-drobopro-vs-qnap-ts-859.html)


