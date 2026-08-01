---
title: Storage Spaces Leaves Me Empty
date: '2012-09-22T22:54:46+00:00'
url: /2012/09/22/storage-spaces-leaves-me-empty/
categories:
- review
- storage
tags:
- lsi
- norco
- sansdigital
- supermicro
- synology
- windows
post_id: '352'
---
I was very intrigued when I found out about Storage Spaces and ReFS being introduced in Windows Server 2012 and Windows 8. But now that I’ve spent some time with it, I’m left disappointed, and I will not be trusting my precious data with either of these features, just yet.

Microsoft publicly announced [Storage Spaces](http://blogs.msdn.com/b/b8/archive/2012/01/05/virtualizing-storage-for-scale-resiliency-and-efficiency.aspx) and [ReFS](http://blogs.msdn.com/b/b8/archive/2012/01/16/building-the-next-generation-file-system-for-windows-refs.aspx) in early Windows 8 blog posts. Storage Spaces was of special interest to the Windows Home Server community in light of Microsoft first [dropping support](http://windowsteamblog.com/windows/b/windowshomeserver/archive/2010/11/23/windows-home-server-code-name-vail-update.aspx) for Drive Extender in Windows Home Server 2011, and then completely dropping Windows Home Server, and replacing it with [Windows Server 2012 Essentials](http://blogs.technet.com/b/sbs/). My personal interest was more geared towards expanding my home storage capacity in a cost effective and energy efficient way, without tying myself to proprietary hardware solutions.

I [archive](/2011/04/22/archiving-my-cd-dvd-and-bd-collection/) all my CD’s, DVD’s, and BD discs, and store the media files on a [Synology DS2411+](http://amzn.to/PiiG8o) with 12 x 3TB drives in a RAID6 volume, giving me approximately 27TB of usable storage. Seems like a lot of space, but I’ve run out of space, and I have a backlog of BD discs that need to be archived. In general I have been very happy with [Synology](http://www.synology.com/) (except for an ongoing problem with “ [Local UPS was plugged out](http://forum.synology.com/enu/viewtopic.php?f=19&t=37891)” errors), and they do offer devices capable of more storage, specifically the [RS2212+](http://www.synology.com/products/product.php?product_name=RS2212%2B&lang=us) with the [RX1211](http://www.synology.com/products/rx1211.php?lang=us) expansion unit offering up to 22 combined drive bays. But, at [$2300](http://amzn.to/RT1WIi) plus [$1700](http://amzn.to/Qhwsdg), this is expensive, capped at 22 drives, and further ties me in with Synology. Compare that with [$1400](http://amzn.to/SP4iJD) for a [Norco DS24-E](http://www.norcotek.com/item_detail.php?categoryid=8&modelno=ds-24e) or [$1700](http://amzn.to/QLl1s8) for a [SansDigital ES424X6+BS](http://www.sansdigital.com/elitestor/es424x6plusbs.html) 24 bay 4U storage unit, an inexpensive [LSI OEM branded SAS HBA](http://www.servethehome.com/lsi-sas-2008-raid-controller-hba-information/) from eBay, or a [LSI SAS 9207-8e](http://www.lsi.com/products/storagecomponents/Pages/LSISAS9207-8e.aspx) if you like the real thing, connected to Windows Server 2012, running Storage Spaces and ReFS, and things look promising.

Arguable I am swapping one proprietary technology for another, but with native Windows support, I have many more choices for expansion. One could make the same argument for the use of [ZFS](http://en.wikipedia.org/wiki/ZFS) on [Linux](http://zfsonlinux.org/), and if I was a Linux expert, that may have been my choice, but I’m not.

I tested using a [SuperMicro SuperWorkstation 7047A-73](http://www.supermicro.com/products/system/4U/7047/SYS-7047A-73.cfm), with dual Xeon E5-2660 processors and 32GB RAM. The 7047A-73 uses a [X9DA7](http://www.supermicro.com/products/motherboard/Xeon/C600/X9DA7.cfm) motherboard, that includes a [LSI SAS2308](http://www.lsi.com/products/storagecomponents/Pages/LSISAS2308.aspx) 6Gb/s SAS2 HBA, connected to 8 hot-swap drive bays.

For comparison with a hardware RAID solution I also tested using a [LSI MegaRAID SAS 9286CV-8e](http://www.lsi.com/products/storagecomponents/Pages/MegaRAIDSAS9286CV-8e.aspx) 6Gb/s SAS2 RAID adapter, with the [CacheCade 2.0](http://www.lsi.com/channel/products/storagesw/Pages/MegaRAIDCacheCadeSoftware2-0.aspx) option, and a [Norco DS12-E](http://www.norcotek.com/item_detail.php?categoryid=8&modelno=ds-12e) 12 bay SAS2 2U expander.

For drives I used [Hitachi Deskstar 7K4000](http://www.hgst.com/deskstar-7k4000) 4TB SATA3 desktop drives and [Intel 520 series 480GB](http://amzn.to/OK2k7c) SATA3 SSD drives. I did not test with enterprise class drives, 4TB models are still excessively expensive, and defeats the purpose of cost effective home use storage.

I previously [reported](/2012/08/05/windows-8-install-hangs-booting-from-lsi-2308-sas-controller/) that the Windows Server 2012 and Windows 8 install will hang when trying to install on a SSD connected to the SAS2308. As such I installed Server 2012 Datacenter on an Intel 480GB SSD connected to the onboard SATA3 controller.

Windows automatically installed the drivers for the LSI SAS2308 controller.

I had to manually install the drivers for the C600 chipset RSTe controller, and as [reported](/2012/09/03/dyslexic-intel-rste-driver/) before, the driver works, but suffers from dyslexia.

The SAS2308 controller firmware was updated to the latest released SuperMicro [v13.0.57.0](ftp://ftp.supermicro.com/driver/SAS/LSI/2308/Firmware/IR/).

Since LSI already released v14.0.0.0 firmware for their own SAS2308 based boards like the [SAS 9207-8e](http://www.lsi.com/products/storagecomponents/Pages/LSISAS9207-8e.aspx), I asked SuperMicro support for their v14 version, and they provided me with an as yet unreleased v14.0.0.0 firmware version for test purposes. Doing a binary compare between the LSI version and the SuperMicro version, the differences appear to be limited to descriptive model numbers, and a few one byte differences that are probably configuration or default parameters. It is possible to [cross-flash](http://www.servethehome.com/ibm-m1015-part-1-started-lsi-92208i/) between some LSI and OEM adapters, but since I had a SuperMicro version of the firmware, this was not necessary.

SuperMicro publishes a [v2.0.58.0](ftp://ftp.supermicro.com/driver/SAS/LSI/2308/Driver/Windows/v2.00.58/) LSI driver that lists Windows 8 support, but LSI has not yet released Windows 8 or Server 2012 drivers for their own SAS2308 based products. I contacted LSI support, and their Windows 8 and Server 2012 drivers are scheduled for release in the P15 November 2012 update.

I tested the SuperMicro v14.0.0.0 firmware with the SuperMicro v2.0.58.0 driver, the SuperMicro v14.0.0.0 firmware with the Windows v2.0.55.84 driver, and the SuperMicro v2.0.58.0 driver with the SuperMicro v13.0.57.0 firmware. Any combination that included the SuperMicro v2.0.58.0 driver or the SuperMicro v14.0.0.0 firmware resulted in problems with the drives or controller not responding. The in-box Windows v2.0.55.84 driver and the released SuperMicro v13.0.57.0 firmware was the only stable combination.

Below are some screenshots of the driver versions and errors:

[![LSI.2.0.55.84](/media/2012/09/lsi-2-0-55-84_thumb.png)](/media/2012/09/lsi-2-0-55-84.png)[![LSI.2.0.58.0](/media/2012/09/lsi-2-0-58-0_thumb.png)](/media/2012/09/lsi-2-0-58-0.png)

[![Eventlog.Controller.Error](/media/2012/09/eventlog-controller-error_thumb.png)](/media/2012/09/eventlog-controller-error_.png)[![Eventlog.IO.Retried](/media/2012/09/eventlog-io_-retried_thumb.png)](/media/2012/09/eventlog-io_-retried.png)[![Eventlog.Reset.Device](/media/2012/09/eventlog-reset_-device_thumb.png)](/media/2012/09/eventlog-reset_-device.png)[![Format.Failed](/media/2012/09/format-failed_thumb.png)](/media/2012/09/format-failed.png)

One of the reasons I am not yet prepared to use Storage Spaces or ReFS is because of the complete lack of decent documentation, best practice guides, or deployment recommendations. As an example, the only documentation on SSD journal drive configuration is in TechNet [forum post](http://social.technet.microsoft.com/Forums/en-US/winserver8gen/thread/79ca6d6d-cab7-4ff3-8c17-ec6ce249e641/) from a Microsoft employee, requiring the use of PowerShell, and even then there is no mention of scaling or size ratio requirements. Yes, the actual PowerShell commandlet parameters are [documented](http://technet.microsoft.com/en-us/library/hh848705.aspx) on MSDN, but not the use or the meaning.

PowerShell is very powerful and Server 2012 is completely manageable using PowerShell, but an appeal of Windows has always been the management user interface, especially important for adoption by SMB’s that do not have a dedicated IT staff. With Windows Home Server being replaced by Windows Server 2012 Essentials, the lack of storage management via the UI will require regular users to become PowerShell experts, or maybe Microsoft anticipates that configuration UI’s will be developed by hardware OEM’s deploying [Windows Storage Server 2012](http://www.microsoft.com/en-us/server-cloud/windows-storage-server/default.aspx) or [Windows Server 2012 Essentials](http://www.microsoft.com/en-us/server-cloud/windows-server-essentials/default.aspx) based systems.

My feeling is that Storage Spaces will be one of those technologies that matures and becomes generally usable after one or two releases or service packs post the initial release.

I tested disk performance using [ATTO Disk Benchmark](http://www.attotech.com/products/product.php?sku=Disk_Benchmark) [2.47](http://www.softpedia.com/get/System/Benchmarks/ATTO-Disk-Benchmark.shtml), and [CrystalDiskMark](http://crystalmark.info/software/CrystalDiskMark/index-e.html) [3.01c](http://release.crystaldew.info/redirect.php?product=CrystalDiskMark).

I ran each test twice, back to back, and report the average. I realize two runs are not statistically significant, but with just two runs it took several days to complete the testing in between regular work activities. I opted to only publish the CrystalDiskMark data as the ATTO Disk Benchmark results varied greatly between runs, while the CrystalDiskMark results were consistent.

Consider the values useful for relative comparison under my test conditions, but not useful for absolute comparison with other systems.

Before we get to the results, a word on the tests.

The JBOD tests were performed using the C600 SATA3 controller.  
The Simple, Mirror, Triple, and RAID0 tests were performed using the SAS 2308 SAS2 controller.  
The Parity, RAID5, RAID6, and CacheCade tests were performed using the SAS 9286CV-8e controller.

The Simple test created a simple storage pool.  
The Mirror test created a 2-way mirrored storage pool.  
The Triple test created a 3-way mirrored storage pool.  
The Parity test created a parity storage pool.  
The Journal test created a parity storage pool, with SSD drives used for the journal disks.  
The CacheCade test created RAID sets, with SSD drives used for caching.

As I mentioned earlier, there is next to no documentation on how to use Storage Spaces. In order to use SSD drives as journal drives, I followed information provided in a TechNet [forum post](http://social.technet.microsoft.com/Forums/en-US/winserver8gen/thread/79ca6d6d-cab7-4ff3-8c17-ec6ce249e641/).

Create the parity storage pool using PowerShell or the GUI. Then associate the SSD drives as journal drives with the pool.

`Windows PowerShell
Copyright (C) 2012 Microsoft Corporation. All rights reserved.PS C:\Users\Administrator> Get-PhysicalDisk -CanPool $TrueFriendlyName CanPool OperationalStatus HealthStatus Usage Size
------------ ------- ----------------- ------------ ----- ----
PhysicalDisk4 True OK Healthy Auto-Select 447.13 GB
PhysicalDisk5 True OK Healthy Auto-Select 447.13 GBPS C:\Users\Administrator> $PDToAdd = Get-PhysicalDisk -CanPool $True
PS C:\Users\Administrator>
PS C:\Users\Administrator> Add-PhysicalDisk -StoragePoolFriendlyName "Pool" -PhysicalDisks $PDToAdd -Usage Journal
PS C:\Users\Administrator>
PS C:\Users\Administrator>
PS C:\Users\Administrator> Get-VirtualDiskFriendlyName ResiliencySettingNa OperationalStatus HealthStatus IsManualAttach Size
me
------------ ------------------- ----------------- ------------ -------------- ----
Pool Parity OK Healthy False 18.18 TBPS C:\Users\Administrator> Get-PhysicalDiskFriendlyName CanPool OperationalStatus HealthStatus Usage Size
------------ ------- ----------------- ------------ ----- ----
PhysicalDisk0 False OK Healthy Auto-Select 3.64 TB
PhysicalDisk1 False OK Healthy Auto-Select 3.64 TB
PhysicalDisk2 False OK Healthy Auto-Select 3.64 TB
PhysicalDisk3 False OK Healthy Auto-Select 3.64 TB
PhysicalDisk4 False OK Healthy Journal 446.5 GB
PhysicalDisk5 False OK Healthy Journal 446.5 GB
PhysicalDisk6 False OK Healthy Auto-Select 3.64 TB
PhysicalDisk7 False OK Healthy Auto-Select 3.64 TB
PhysicalDisk8 False OK Healthy Auto-Select 447.13 GB
PhysicalDisk10 False OK Healthy Auto-Select 14.9 GBPS C:\Users\Administrator>`

I initially added the journal drives after the virtual drive was already created, but that would not use the journal drives. I had to delete the virtual drive, recreate it, and then the journal drives kicked in. There must be some way to manage this after virtual drives already exist, but again, no documentation.

In order to test Storage Spaces using the SAS 9286CV-8e RAID controller I had to [switch it to JBOD mode](http://kb.lsi.com/KnowledgebaseArticle16511.aspx) using the commandline MegaCli utility.

`
D:\Install>MegaCli64.exe AdpSetProp EnableJBOD 1 a0Adapter 0: Set JBOD to Enable success.Exit Code: 0x00D:\Install>MegaCli64.exe AdpSetProp EnableJBOD 0 a0Adapter 0: Set JBOD to Disable success.Exit Code: 0x00D:\Install>`

The RAID and CacheCade disk sets were created using the LSI MegaRAID Storage Manager GUI utility.

Below is a summary of the throughput results:

[![ReadWriteKBPS](/media/2012/09/readwritekbps_thumb.png)](/media/2012/09/readwritekbps.png)

[![ReadWriteIOPS](/media/2012/09/readwriteiops_thumb.png)](/media/2012/09/readwriteiops.png)

Not surprisingly the SSD drives had very good scores all around for JBOD, Simple, and RAID0. I only had two drives to test with, but I expect more drives to further improve performance.

The Simple, Mirror, and Triple test results speak for themselves, performance halving, and halving again.

The Parity test shows good read performance, and bad write performance. The write performance approaches that of a single disk.

The Parity with SSD Journal disks shows about the same read performance as without journal disks, and the write performance double that of a single disk.

The RAID0 and Simple throughput results are close, but the RAID0 write IOPS doubling that of the Simple volume.

The RAID5 and RAID6 read performance is close to Parity, but the write performance almost ten fold that of Parity. It appears that the SLI card writes to all drives in parallel, while Storage Spaces parity writes to one drive only.

The CacheCade read and write performance is less than without CacheCade, but the IOPS ten fold higher.

The ReFS performance is about 30% less than the equivalent NTFS performance.

Until Storage Spaces gets thoroughly documented and improves performance, I’m sticking with hardware RAID solutions.
