---
title: Cooling an Overheating MVMe SSD
date: '2021-03-15T15:10:50+00:00'
url: /2021/03/15/cooling-an-overheating-mvme-ssd/
categories:
- backup
- review
- storage
tags:
- asus
- nvme
- samsung
- ssd
post_id: '2312'
cover:
  alt: '2021-03-14'
  image: /media/2021/03/2021-03-14.png
---
The SSD in my Windows 10 system started reporting failures, and as luck would have it, died while I was cloning it to a new drive. I suspect death was caused by overheating, and I addressed that with my new setup.

This Windows 10 system is in a [NCase M1 v5](https://ncases.com/products/m1) SFF case with an [ASUS ROG STRIX Z390-I GAMING](https://rog.asus.com/us/motherboards/rog-strix/rog-strix-z390-i-gaming-model/) mini-ITX motherboard and a [Samsung 970 EVO](https://www.samsung.com/semiconductor/minisite/ssd/product/consumer/970evo/) NVMe M.2 SSD drive. The motherboard has two M.2 slots, one on the front of the motherboard and one on the back. The slot on the front has a heatsink, but I noticed the drive runs hot even under no load. Some googling showed this to be a common problem with the heatsink and M.2 slot being heated by the motherboard chipset, so I moved the SSD to the slot on the back of the motherboard. The SSD still reported +60°C temperatures under load, and I added a passive [heatsink](https://amzn.to/3rMKAB3), and that kept temperatures in the low 50°C's even under load.

Fast forward a year or so to last week, and the system would randomly BSOD, and when rebooting the BIOS would report no disk drive found. If I let things cool for a minute or two, the drive comes back, system boots, with disk read errors reported in the eventlog. I opened the side of the case to inspect the SSD and found the rubber bands holding the heatsink to the SSD broken. I don't know if the rubber bands broke due to excessive heat, or if the excessive heat was caused by the rubber bands breaking, or if the SSD was just failing and overheating.


{{< gallery cols="1" >}}  
{{< figure src="/media/2021/03/img%5F7339.jpg?w=1024" alt="" caption="" >}}  
{{< /gallery >}}  

My plan was to get an actively cooled heatsink, a new SSD, and then clone the old SSD to the new one, before it completely dies.

While searching for heatsinks, I found the [ASUS Hyper M.2 x16 Gen 4 Card](https://amzn.to/2Nj86Xl), that has a massive actively cooled heatsink, and 4 x PCIe 4.0 M.2 NVMe slots. The Z390 based motherboard has only one PCIe Gen3 x16 slot, so I won't get full Gen4 bandwidth, but since I use onboard graphics, that one slot can be used for M.2 drives.

I installed 2 x [Samsung 980 Pro](https://amzn.to/3qNDB9m) PCIe 4.0 NVMe M.2 2TB SSD's in the card. I was initially looking at the [Samsung 970 EVO Plus](https://amzn.to/3bLzE0Q) drives, but the price difference between the 2TB 970 EVO Plus and 2TB 980 Pro was only about $60, so I opted for the 980 Pro's.


{{< gallery cols="3" >}}  
{{< figure src="/media/2021/03/img%5F7336.jpg?w=768" alt="" caption="" >}}  
{{< figure src="/media/2021/03/img%5F7337.jpg?w=768" alt="" caption="" >}}  
{{< figure src="/media/2021/03/img%5F7338.jpg?w=768" alt="" caption="" >}}  
{{< /gallery >}}  

On booting into Windows, only one of the 980 Pro's was listed, a bit of RTFM, and I found that I had to enable "Hyper M.2 x16" in the BIOS, and both drives showed up.


{{< gallery cols="1" >}}  
{{< figure src="/media/2021/03/img%5F7340.jpg?w=1024" alt="" caption="" >}}  
{{< /gallery >}}  

I created a WinPE USB Boot Disk using [Active@ Data Studio](https://www.lsoft.net/data-studio/), booted into WinPE from the USB drive, and used [Active@ Disk Image](https://www.lsoft.net/disk-image/) to clone the old SSD to one of the new 980 Pro's. The process started out running fast, and then slowed to a crawl, and after a few minutes failed due to disk read errors. I noticed the SSD was burning hot, too hot to touch, so I pointed a small fan at the SSD, and I tried again, this time making a backup disk image instead of a direct clone. Although the process completed after many hours, the log showed many read errors. I repeated the process using [AOMEI Partition Assistant Professional](https://www.aomeitech.com/pa/professional.html), hoping for a different result, and after running for a few hours I got another BSOD. On rebooting the BIOS reported a critical disk failure, and the SSD was no longer listed as a boot device, the SSD died.


{{< gallery cols="2" >}}  
{{< figure src="/media/2021/03/img%5F7343.jpg?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2021/03/img%5F7344.jpg?w=1024" alt="" caption="" >}}  
{{< /gallery >}}  

Since my important data is either on OneDrive or on a server with cloud backups, I decided to just reinstall Windows 10 on one of the new 980 Pro's. I used the [Windows Media Creation Tool](https://www.microsoft.com/en-us/software-download/windows10) to create a bootable USB drive, installed, and then got a "Windows cannot install required files 0x8007045D" error. I've used this process many times, but this is the first time I've ever encountered this error. Some googling suggested creating an ISO and using [Rufus](https://rufus.ie/) to create a bootable USB from the ISO. It worked, and the install completed successfully.

Although the BIOS reported a critical drive failure on boot, it did still show the drive was present, just not bootable, and Windows showed the disk in a read-only state, but accessible. [Samsung Magician](https://www.samsung.com/semiconductor/minisite/ssd/download/tools/) showed the disk in critical state, but offered no additional diagnostic details. Since I could access the disk, I created a backup copy of my home directory, using the `robocopy [src] [dst] /mir /xj /r:0 /w:0` options to skip the files with read errors. I was glad I could get some files, as I did not have a copy of my ".ssh" folder containing my private keys for remote SSH access. It would not have been a critical loss, but is something I need to address with my backup strategy.


{{< gallery cols="3" >}}  
{{< figure src="/media/2021/03/2021-03-14-3.png?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2021/03/2021-03-14-2.png?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2021/03/2021-03-14-1.png?w=1024" alt="" caption="" >}}  
{{< /gallery >}}  

I don't know if the SSD failed due to heat, or if the excessive heat was a symptom of the drive failing, but the new 980 Pro's are fast, and with the giant heatsink on the Hyper M.2 x16 card they run cool even under load.


{{< gallery cols="1" >}}  
{{< figure src="/media/2021/03/2021-03-14.png?w=1024" alt="" caption="" >}}  
{{< /gallery >}}  
