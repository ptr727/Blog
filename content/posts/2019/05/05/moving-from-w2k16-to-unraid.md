---
title: Moving from W2K16 to Unraid
date: '2019-05-06T01:34:42+00:00'
url: /2019/05/05/moving-from-w2k16-to-unraid/
categories:
- review
- storage
tags:
- adaptec
- freenas
- hyper-v
- supermicro
- unraid
post_id: '1825'
cover:
  alt: FireShot Capture 007 - unraid_Apps - unraid.home.insanegenius.net
  image: /media/2019/05/fireshot-capture-007-unraid_apps-unraid.home_.insanegenius.net_.png
---
I have been happy with [my server rack](/2014/10/08/rack-that-server/) running my [UniFi](https://unifi-sdn.ui.com/) network equipment and two Windows Server 2016 (W2K16) instances. I use the servers for [archiving my media collection](/2011/04/22/archiving-my-cd-dvd-and-bd-collection/) and running Hyper-V for all sorts of home projects and work related experiments. But, time moves on, one can never have enough storage, and technology changes. So I set about a path that lead to me replacing my W2K16 servers with [Unraid](https://unraid.net/).

I currently use Adaptec [7805Q](https://storage.microsemi.com/en-us/support/raid/sas_raid/sas-7805q/) and [81605ZQ](https://storage.microsemi.com/en-us/support/raid/sas_raid/asr-81605zq/) RAID cards, with a mixture of SSD for caching, SSD RAID1 for boot and VM images, and HDD RAID6 for the large media storage array. The setup has been solid, and although I've had both SSD and HDD failures, the hot spares kicked in, and I replaced the failed drives with new hot spares, no data lost.

For my large RAID6 media array I used lots of HGST 4TB Ultrastar (enterprise) and Deskstar (consumer) drives, but I am out of open slots in my 24-bay 4U case, so adding more storage has become a problem. I can replace the 4TB drives with larger drives, but in order to expand the RAID6 volume without loosing data, I need to replace all disks in the array, one-by-one, rebuilding parity in between every drive upgrade, and then expand the volume. This will be very expensive, take a very long time, and risk the data during during every drive rebuild.

I have been looking for more flexible provisioning solutions, including [Unraid](https://unraid.net/), [FreeNAS](https://freenas.org/), [OpenMediaVault](https://www.openmediavault.org/), [Storage Spaces](https://docs.microsoft.com/en-us/windows-server/storage/storage-spaces/overview), and [Storage Spaces Direct](https://docs.microsoft.com/en-us/windows-server/storage/storage-spaces/storage-spaces-direct-overview). I am not just looking for dynamic storage, I also want a system that can run VM's, and Docker containers, I want it to work with consumer and or small business hardware, and I do not want to spend all my time messing around in a CLI.

I have tried Storage Spaces with [limited success](/2012/09/22/storage-spaces-leaves-me-empty/), but that was a long time ago. Storage Spaces Direct offers significant improvements, but with more stringent enterprise hardware requirements, that would make it too costly and complicated for my home use.

[FreeNAS](https://freenas.org/) offers the best storage capabilities, but I found the VM and Docker ecosystem to be an afterthought and still lacking.

[OpenMediaVault](https://www.openmediavault.org/) (OMV) is a relative newcomer, the web front-end is modern, think of OMV as Facebook and FreeNAS and Unraid as MySpace, with growing support for VM's and Docker. Compared to FreeNAS and Unraid the OMV community is still very small, and I was reluctant to entrust my data to it.

[Unraid](https://unraid.net/) offered a good balance between storage, VM, and Docker, with a large support community. Unlike FreeNAS and OMV, Unraid is not free, but the [price](https://unraid.net/pricing) is low enough.

An ideal solution would have been the storage flexibility offered by FreeNAS, the docker and VM app ecosystem offered by Unraid, and the UI of OMV. Since that does not exist, I opted to go with Unraid.

Picking a replacement OS was one problem, but moving the existing systems to run on it, without loosing data or workloads, quite another. I decided to convert the two servers one at a time, so I moved all the Hyper-V workloads from Server-2 with the 8-bay chassis, to Server-1 with the 24-bay chassis. This left Server-1 unused, and I could go about converting it to Unraid. I not only had to install Unraid, I also had to provision enough storage in the 8-bay chassis to hold all the data from the 24-bay chassis, so that I could then move the data on Server-1 to Server-2, convert Server-1 to Unraid, and move the data back to Server-1. And I had to do this without risking the data, and without an extended outage.

To get all the data from Server-1 to fit on Server-2, I pruned the near 60TB set down to around 40TB. You know how it works, no matter how much storage you have it will always be filled. I purchased 4 x [12TB Seagate IronWolf ST12000VN0007](https://amzn.to/2Wr6WIm) drives, and combined with 2 x 4TB HGST drives, gave me around 44TB of of usable storage space, enough to copy all the important data from Server-1 to Server-2.

While I was at it, I decided to upgrade the IPMI firmware, motherboard BIOS, and RAID controller firmware. I knew it is possible to upgrade the SuperMicro BIOS through IPMI, but you have to [buy](https://store.supermicro.com/out-of-band-sft-oob-lic.html?utm=osite) a per-motherboard locked Out-of-Band feature key from SuperMicro to enable this, something I had never bothered doing. While looking for a way to buy a code online, I found an [interesting post](https://peterkleissner.com/2018/05/27/reverse-engineering-supermicro-ipmi/) describing a method of creating my own activation keys, and it worked.

IPMI updated, motherboard BIOS updated, RAID firmware updated, I set about converting the Adaptec RAID controller from RAID to HBA mode. Unlike the LSI controllers that need to be re-flashed with IR or IT firmware to change modes, the Adaptec controller allows this configuration via the controller BIOS. In order to change modes, all drives have to be uninitialized, but there were two drives that I could not uninitialize. After some troubleshooting I discovered that it is not possible to delete MaxCache arrays from the BIOS. I had to boot using the [Adaptec bootUSB Utility](https://storage.microsemi.com/en-us/support/infocenter/release-2013-4/index.jsp?topic=/maxview_ug.xml/Topics/Running_maxView_from_a_Bootable_USB_Image.html), that is a Linux bootable image that runs the MaxView storage controller GUI. MaxCache volumes deleted, I could convert to HBA mode.


{{< gallery cols="1" >}}  
{{< figure src="/media/2019/05/ikvm%5Fcapture-2.jpg" title="iKVM\_capture (2)" alt="iKVM\_capture (2)" >}}

{{< figure src="/media/2019/05/ikvm%5Fcapture-3.jpg" title="iKVM\_capture (3)" alt="iKVM\_capture (3)" >}}

{{< figure src="/media/2019/05/ikvm%5Fcapture-1.jpg" title="iKVM\_capture (1)" alt="iKVM\_capture (1)" >}}

{{< figure src="/media/2019/05/ikvm%5Fcapture.jpg" title="iKVM\_capture" alt="iKVM\_capture" >}}

{{< figure src="/media/2019/05/ikvm%5Fcapture-4.jpg" title="iKVM\_capture (4)" alt="iKVM\_capture (4)" >}}  
{{< /gallery >}}  

With the controller in HBA mode, I set about installing Unraid, well, it is not really installing in the classic sense, Unraid runs from a USB drive, and all drives in the system are used for storage. There are lots of info online on installing and configuring Unraid, but I found very good info on the [Spaceinvader One Youtube channel](https://www.youtube.com/channel/UCZDfnUn74N0WeAPvMqTOrtA). I have seen some reports of issues with USB drives, but I had no problems using a [SanDisk Cruzer Fit](https://amzn.to/2DUwjLA) drive.

It took a couple iterations before I was happy with the setup, and here are a few important things I learned:

- Unraid does not support SSD drives as data drives, see the install [docs](https://lime-technology.com/wp/getting-started/); " _Do not assign an SSD as a data/parity device. While unRAID won’t stop you from doing this, SSDs are only supported for use as cache devices due TRIM/discard and how it impacts parity protection. Using SSDs as data/parity devices is unsupported and may result in data loss at this time._" This is one area where FreeNAS and OMV offer much better redundancy solutions using e.g. [ZFS](https://en.wikipedia.org/wiki/ZFS) over Unraid's [parity solution](https://wiki.unraid.net/Parity), or many other commercial solutions that have for many years been using SSD's in drive arrays.
- Unraid's caching solution using SSD drives and [BTRFS](https://en.wikipedia.org/wiki/Btrfs) works just ok. Unlike e.g. Adaptec MaxCache that seamlessly caches block storage regardless of the file system, the Unraid cache works at the file level. While this does create flexibility in deciding which files from which shares should be using the cache, it greatly complicates matters when running out of space on the cache. When a file is created on the cache, and the file is then enlarged to the point it no longer fits in the available space, the file operation will permanently fail. E.g. copying a large file to a cached share, and the file is larger that the available space, the copy will proceed until the cache runs out of space, and then fail, repeat and get the same. To avoid this, one has to set the minimum free space setting to a value larger than the largest file that would ever be created on the cache, for large files, this is very wasteful. Imagine a thin provisioned VM image, it can grow until no space, and then fail, until manually moved to a different drive.
- The cache re-balancing and file moving algorithm is very rudimentary, the operation is schedule per time period, and will move files from the cache to regular storage. There is no support for flushing the cache in real-time as it runs out of space, there is no high water or low water mechanisms, no LRU or MRU file access logic. I installed the [Mover Tuning](https://forums.unraid.net/topic/70783-plugin-mover-tuning/) plugin that allows balancing the cache based on consumed space, better, but still not good enough.
- Exhausting the cache space while copying files to Unraid is painfully slow. I used robocopy to copy files from W2K16 to a share on Unraid that had caching set to "preferred", meaning use the cache if it has space, and as soon as the cache ran out of space, the copy operation slowed down to a crawl. As soon as the cache ran out of space, new files were supposed to be written to HDD, but my experience showed that something was not working, and I had to disable the cache and then copy the files. The whole SSD and caching thing is a big disappointment.
- Building parity while copying files is very slow. Copying files using robocopy while the parity was building resulted in about 200Mbps throughput, very slow. I cancelled the parity operation, disabled the parity drive, and copied with no parity protection in place, and got near the expected 1Gbps throughput. I will re-enable parity building after all data is copied across.
- Performing typical disk based operations like add-, remove-, or replace- a drive, is very cumbersome. The [wiki](https://wiki.unraid.net/Replacing_a_Data_Drive) tries to explain, but it is still very confusing. I really expected much easier ways of doing typical disk based operations, especially when almost all operations result in the parity becoming invalid, leaving the system exposed to failure.
- It is really easy to use Docker, with containers directly from [Docker Hub](https://hub.docker.com/), or from the [Community Applications](https://forums.unraid.net/topic/38582-plug-in-community-applications/) plugin that acts like an app store.
- It is reasonably easy to create VM's, one has to manually install the [LibVirt](https://libvirt.org/) KVM/QEMU drivers in Windows OS's, but it is made easy with the automatic mounting of the LibVirt driver ISO.
- I could not get any Ubuntu Desktop VM's working, they would all hang during install. I had no problems with Ubuntu Server installs. I am sure there is a solution, I just did not try looking yet as I only needed Ubuntu Server.
- VM runtime management is lacking, there is no support for snapshots or backups. One can install the [Virt-Manager](https://forums.unraid.net/topic/77603-virt-manager-intel-gpu-tools-and-more-dockers/) container to help, but it is still rather rudimentary compared to offerings from VMWare, Hyper-V, and VirtualBox.
- In order to get things working I had to install several community plugins, I would have expected this functionality to be included in the base installation. Given how active the plugin authors are in the community, I wonder if not including said functionality by default may be intentional?
- Drive power saving works very well, and drives are spun down when not in use. I will have to revisit the file and folder to drive distribution, as common access patterns to common files should be constrained to the same physical drive.
- The [community forum](https://forums.unraid.net/) is very active and very helpful.


{{< gallery cols="1" >}}  
{{< figure src="/media/2019/05/fireshot-capture-009-unraid%5Fmain-unraid.home%5F.insanegenius.net%5F.png" title="FireShot Capture 009 - unraid\_Main - unraid.home.insanegenius.net" alt="FireShot Capture 009 - unraid\_Main - unraid.home.insanegenius.net" >}}

{{< figure src="/media/2019/05/fireshot-capture-008-unraid%5Fdashboard-unraid.home%5F.insanegenius.net%5F.png" title="FireShot Capture 008 - unraid\_Dashboard - unraid.home.insanegenius.net" alt="FireShot Capture 008 - unraid\_Dashboard - unraid.home.insanegenius.net" >}}

{{< figure src="/media/2019/05/fireshot-capture-006-unraid%5Fvms-unraid.home%5F.insanegenius.net%5F.png" title="FireShot Capture 006 - unraid\_VMs - unraid.home.insanegenius.net" alt="FireShot Capture 006 - unraid\_VMs - unraid.home.insanegenius.net" >}}

{{< figure src="/media/2019/05/fireshot-capture-005-unraid%5Fdocker-unraid.home%5F.insanegenius.net%5F.png" title="FireShot Capture 005 - unraid\_Docker - unraid.home.insanegenius.net" alt="FireShot Capture 005 - unraid\_Docker - unraid.home.insanegenius.net" >}}

{{< figure src="/media/2019/05/fireshot-capture-004-unraid%5Fplugins-unraid.home%5F.insanegenius.net%5F.png" title="FireShot Capture 004 - unraid\_Plugins - unraid.home.insanegenius.net" alt="FireShot Capture 004 - unraid\_Plugins - unraid.home.insanegenius.net" >}}

{{< figure src="/media/2019/05/fireshot-capture-007-unraid%5Fapps-unraid.home%5F.insanegenius.net%5F.png" title="FireShot Capture 007 - unraid\_Apps - unraid.home.insanegenius.net" alt="FireShot Capture 007 - unraid\_Apps - unraid.home.insanegenius.net" >}}

{{< figure src="/media/2019/05/fireshot-capture-002-unraid%5Faddvm-unraid.home%5F.insanegenius.net%5F.png" title="FireShot Capture 002 - unraid\_AddVM - unraid.home.insanegenius.net" alt="FireShot Capture 002 - unraid\_AddVM - unraid.home.insanegenius.net" >}}

{{< figure src="/media/2019/05/fireshot-capture-003-unraid-netdata-dashboard-192.168.1.98.png" title="FireShot Capture 003 - unraid netdata dashboard - 192.168.1.98" alt="FireShot Capture 003 - unraid netdata dashboard - 192.168.1.98" >}}  
{{< /gallery >}}  

I still have a few days of file copying left, and I will keep my W2K16 server operational until I am confident in the integrity and performance of Unraid. When I'm ready, I'll convert the second server to Unraid, and then re-balance the storage, VM, and Docker workloads between the two servers.
