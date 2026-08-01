---
title: Synology DS1511+ vs. QNap TS-859 Pro, iSCSI MPIO Performance
date: '2011-07-06T22:50:00+00:00'
url: /2011/07/06/synology-ds1511-vs-qnap-ts-859-pro-iscsi-mpio-performance/
categories:
- performance
- review
- storage
tags:
- iscsi
- mpio
- nas
- qnap
- synology
post_id: '120'
---
Untitled Page I have been very happy with my [QNap TS-859 Pro](http://www.qnap.com/pro_detail_feature.asp?p_id=146) ([Amazon](http://amzn.to/Lpv6Yr)), but I’ve run out of space while archiving my media collection, and I needed to expand the storage capacity. You can read about my experience with the TS-859 Pro [here](/2010/01/data-robotics-drobopro-vs-qnap-ts-859.html), and my experience archiving my media collection [here](/2011/04/archiving-my-cd-dvd-and-bd-collection.html).  
 My primary objective with this project is storage capacity expansion, and my secondary objective is improved performance.

My choices for storage capacity expansion included:  

- Replace the 8 x 2TB drives with 8 x 3TB drives, to give me 6TB of extra storage. The volume expansion would be very time consuming, but my network setup can remain unchanged during the expansion.
- Get a second TS-859 Pro with 8 x 3TB drives, to give me 18TB of extra storage. I would need to add the new device to my network, and somehow rebalance the storage allocation across the two devices, without changing the file sharing paths, probably by using directory mount points.
- Get a [Synology DS1511+](http://www.synology.com/us/products/DS1511+/index.php) ([Amazon](http://amzn.to/LOWKlL)) and a [DX510](http://www.synology.com/us/products/DX510/index.php) ([Amazon](http://amzn.to/M98qwB)) expansion unit with 10 x 3TB drives to replace the QNap, to give me 12TB of extra storage, expandable to 15 x 3TB drives for 36TB of total storage. I will need to copy all data to the new device, then mount the new device in place of the old device.

 I opted for the DS1511+ with one DX510 expansion unit, I can always add a second DX510 and expand the volume later if needed.  
 As far as hard drives go, I’ve been very happy with the [Hitachi Ultrastar A7K2000](http://www.hitachigst.com/internal-drives/enterprise/ultrastar/ultrastar-a7k2000) 2TB drives I use in my workstations and the QNap, so I stayed with the larger [Hitachi Ultrastar 7k3000](http://www.hitachigst.com/internal-drives/enterprise/ultrastar/ultrastar-7k3000) 3TB drives for the Synology expansion.

For improving performance I had a few ideas:  

- The TS-859 Pro is a bit older than the DS1511+, and there are newer and more powerful QNap models available, like the [TS-859 Pro+](http://www.qnap.com/pro_detail_feature.asp?p_id=180) ([Amazon](http://amzn.to/LpvAO6)) with a faster processor, or the [TS-659 Pro II](http://www.qnap.com/pro_detail_feature.asp?p_id=167) ([Amazon](http://amzn.to/LdoEIw)) with a faster processor and SATA3 support, so it not totally fair to compare the TS-859 Pro performance against the newer DS1511+. But, the newer QNap models do not support my capacity needs.
- I use Hyper-V clients and dynamic VHD files located on an iSCSI volume mounted in the host server. I elected this setup because it allowed me great flexibility in creating logical volumes for the VM’s, without actually requiring the space to be allocated. In retrospect this may have been convenient, but it was not performing well in large file transfers between the iSCSI target and the file server Hyper-V client.   
 For my new setup I was going to mount the iSCSI volume as a raw disk in the file server Hyper-V client. This still allowed me to easily move the iSCSI volume between hosts, but the performance will be better than fixed size VHD files, and much better than dynamic VHD files.   
 Here is a [blog post](http://blogs.msdn.com/b/virtual_pc_guy/archive/2010/07/02/hyper-v-amp-iscsi-in-the-parent-or-in-the-virtual-machine.aspx) describing some options for using iSCSI and Hyper-V.
- I used iSCSI thin provisioning, meaning that the logical target has a fixed size, but the physical storage only gets allocated as needed. This is very convenient, but turned out to be slower than instant allocation. The QNap iSCSI implementation is also a file-level iSCSI LUN, meaning that the iSCSI volume is backed by a file on an EXT4 volume.   
 For my new setup I was going to use the Synology block-level iSCSI LUN, meaning that the iSCSI volume is directly mapped to a physical storage volume.
- I use a single LAN port to connect to the iSCSI target, meaning the IO throughput is limited by network bandwidth to 1Gb/s or 125MB/s.   
 For my new setup I wanted to use [802.3ad link aggregation](http://en.wikipedia.org/wiki/Link_aggregation) or [Multi Path IO (MPIO)](http://technet.microsoft.com/en-us/library/cc725907.aspx) to extend the network speed to a theoretical 2Gb/s or 250MB/s. My understanding of link aggregation turned out to be totally wrong, and I ended up using MPIO instead.


 To create a 2Gb/s network link between the server and storage, I [teamed two LAN ports on the Intel server adapter](http://www.intel.com/support/network/sb/cs-009747.htm), I created a bond of the two LAN ports on the Synology, and I created two trunks for those connections on the switch. This gave me a theoretical 2Gb/s pipe between the server and the iSCSI target. But my testing showed no improvement in performance over a single 1Gb/s link. After some research I found that the logical link is 2Gb/s, but that the physical network stream going from one MAC address to another MAC address is still limited by the physical transport speed, i.e. 1Gb/s. This means that the link aggregation setup is very well suited to e.g. connect a server to a switch using a trunk, and allow multiple clients access to the server over the switch, each at full speed, but it has no performance benefit when there is a single source and destination, as is the case with iSCSI. Since link aggregation did not improve the iSCSI performance, I used MPIO instead.

I set up a test environment where I could compare the performance of different network and device configurations using readily available hardware and test tools. Although my testing produced reasonably accurate relative results, due to the differences in environments, it can’t really be used for absolute performance comparisons.

Disk performance test tools:  

- [CrystalDiskMark 3.0.1b](http://crystalmark.info/software/CrystalDiskMark/index-e.html)
- [ATTO Disk Benchmark 2.46](http://majorgeeks.com/ATTO_Disk_Benchmark_d6359.html)

 Server setup:  

- [Windows Server 2008 R2](http://www.microsoft.com/windowsserver2008/en/us/default.aspx) Enterprise SP1.
- [DELL OptiPlex 990](http://www.dell.com/us/en/enterprise/desktops/optiplex-990/pd.aspx?refid=optiplex-990&cs=555&s=biz), 16GB RAM, [Intel Core i7 2600 3.4GHz](http://ark.intel.com/Product.aspx?id=52213), [Samsung PM810](http://www.samsung.com/global/business/semiconductor/products/SSD/downloads/ds_pm810_25_sata_ii_rev10.pdf) SSD.
- [Intel Gigabit ET2 Quad Port Server Adapter](http://ark.intel.com/Product.aspx?id=49187).
- LAN-1 192.168.0.11, LAN-2 192.168.1.12

 Network setup:  

- [HP ProCurve V1810](http://h17007.www1.hp.com/us/en/products/switches/HP_V1810_Switch_Series/index.aspx) switch, Jumbo Frames enabled, Flow Control enabled.
- Jumbo Frames enabled on all adapters.
- CAT6 cables.
- All network adapters connected to the switch.

 QNap setup:  

- [QNap TS-859 Pro](http://www.qnap.com/pro_detail_feature.asp?p_id=146), firmware 3.4.3 Build0520.
- 8 x [Hitachi Ultrastar A7K2000](http://www.hitachigst.com/internal-drives/enterprise/ultrastar/ultrastar-a7k2000) 2TB drives.
- RAID 6.
- 10TB EXT4 volume.
- 10TB iSCSI LUN on EXT4 volume.
- LAN-1 192.168.0.13, LAN-2 192.168.1.14

 Synology setup:  

- [Synology DS1511+](http://www.synology.com/us/products/DS1511+/index.php), firmware 3.1-1748.
- 5 x [Hitachi Ultrastar 7k3000](http://www.hitachigst.com/internal-drives/enterprise/ultrastar/ultrastar-7k3000) 3TB drives.
- [Synology Hybrid RAID](http://forum.synology.com/wiki/index.php/What_is_Synology_Hybrid_RAID%3F) (SHR) 2 drive redundancy.
- 8TB iSCSI LUN on SHR2.
- LAN-1 192.168.0.15, LAN-2 192.168.1.16


 To test the performance using the disk test tools I mounted the [iSCSI](http://en.wikipedia.org/wiki/ISCSI) targets as drives in the server. I am not going to cover details on how to configure iSCSI, you can read the [Synology](http://forum.synology.com/wiki/index.php/How_to_use_the_iSCSI_Target_Service_on_the_Synology_DiskStation) and [QNap](http://www.qnap.com/pro_application.asp?ap_id=135) iSCSI documentation, and more specifically the MPIO documentation for [Windows](http://download.microsoft.com/download/3/0/4/304083f1-11e7-44d9-92b9-2f3cdbf01048/mpio.doc), [Synology](http://forum.synology.com/wiki/index.php/How_to_use_iSCSI_Targets_on_Windows_computers_with_Multipath_I/O) and [QNap](http://www.qnap.com/features/iSCSI_support/iSCSI_targets_with_MCS_and_MPIO.aspx?index=0&ap_id=60&lang=eng).   
 A few notes on setting up iSCSI:  

- The QNap MPIO documentation shows that LAN-1 and LAN-2 are in a trunked configuration. As far as I could tell the best practices documentation from Microsoft, DELL, Synology, and other SAN vendors, say that trunking and MPIO should not be mixed. As such I did not trunk the LAN ports on the QNap.
- I connected all LAN cables to the switch. I could have done direct connections to eliminate the impact of the switch, but this is not how how I will install the setup, and the switch should be sufficiently capable of handling the load and not add any performance degradation.
- Before trying to enable MPIO on Windows Server, first connect one iSCSI target and map the device, then add the MPIO feature. If you do not have a mapped device, the MPIO iSCSI option will be greyed out.
- The server’s iSCSI target configuration explicitly bound the source and destination devices based on the adapters IP address, i.e. server LAN-1 would bind to NAS LAN-1, etc. This ensured that traffic would only be routed to and from the specified adapters.
- I found that the best [MPIO load balance policy](http://technet.microsoft.com/en-us/library/dd851699.aspx) was the Least Queue Depth Option.


 During my testing I encountered a few problems:  

- The DX510 expansion unit would sometimes not power on when the DS1511+ is powered on, or would sometimes fail to initialize the RAID volume, or would sometimes go offline while powered on. I RMA’d the device, and the replacement unit works fine.
- During testing of the DS1511+, the write performance would sometimes degrade by 50% and never recover. The only solution was to reboot the device. Upgrading the the latest 3.1-1748 DSM firmware solved this problem.
- During testing of the DS1511+, when one of the MPIO network links would go down, e.g. I unplug a cable, ghost iSCSI connections would remain open, and the iSCSI processes would consume 50% of the NAS CPU time. The only solution was to reboot the device. Upgrading the the latest 3.1-1748 DSM firmware solved this problem.
- I could not get MPIO to work with the DS1511+, yet no errors were reported. It turns out that LAN-1 and LAN-2 must be on different subnets for MPIO to work.
- Both the QNap and Synology exhibits weird LAN traffic behavior when both LAN-1 and LAN-2 is connected, and the server generates traffic directed to LAN-1 only. The NAS resource monitor would show high traffic volumes on LAN-1 and and LAN-2, even with no traffic directed at LAN-2. I am uncertain why this happens, maybe a reporting issue, maybe a switching issue, but to avoid it influencing the tests, I disconnected LAN-2 while not testing MPIO.


 My test methodology was as follows:  

- Mount either the QNap or Synology iSCSI device, power of the other device while not being tested.
- Connect the iSCSI target using LAN-1 only and unplug LAN-2, or connect using MPIO with LAN-1 and LAN-2 active.
- Run all CDM tests with iterations set at 9, and a 4GB file-set size.
- Run ATTO with the queue depth set to 8, and a 2GB file-set size.
- As a baseline, I also tested the Samsung PM810 SSD drive using ATTO and CDW.


 Test result summary:  

**Device**

**ATTO Read**

**ATTO Write**

**CDM Read**

**CDM Write**

**Total (MB/s)**

 PM810  267.153  260.839  256.674  251.850  1,036.516  DS1511+ MPIO  244.032  126.030  141.213  115.032  626.307  TS-859 Pro MPIO  136.178  95.152  116.015  91.097  438.442  DS1511+  122.294  120.172  89.258  105.618  437.342  TS-859 Pro  119.370  99.864  76.529  89.752  385.515 [![image](/external/9c8ea9e7b3a3298f.png)](/external/ae256086582f1cec.png)

Detailed results:  
 PM810:  
[![Atto.P810](/external/2cc2412c3af12278.png)](/external/fa413874e5ebec5c.png)[![CDM.P810](/external/4b66438ec66b9eb3.png)](/external/93333147c3ea4793.png)  
 DS1511+ MPIO:  
[![Atto.Synology.MPIO](/external/fe33f9f80e310c28.png)](/external/c23b6727adc7e52b.png)[![CDM.Synology.MPIO](/external/823a26f1264e081f.png)](/external/d64a443c3d663bbb.png)  
 TS-859 Pro MPIO:  
[![Atto.Qnap.MPIO](/external/9781b8474bf2480f.png)](/external/cbef8c6c176df2e6.png)[![CDM.Qnap.MPIO](/external/327ac6ccb8742bc8.png)](/external/f94029d7c2c120cf.png)  
 DS1511+:  
[![Atto.Synology](/external/78f1063ef9c407ec.png)](/external/cda64d775d4918aa.png)[![CDM.Synology](/external/b4d1259184930e91.png)](/external/cbe345448673391b.png)  
 TS-859 Pro:  
[![Atto.Qnap](/external/06ece281a84950af.png)](/external/0c7176ac553150b7.png) [![CDM.Qnap](/external/e02bc2d64b670cd9.png)](/external/fcab8688da240ba4.png)

Initially, I was a little concerned about the DX510 being in a separate case connected with an eSATA cable to the main DS1511+. Especially after I had to RMA my first DX510 because of what appeared to be connectivity issues. I was also concerned that there would be a performance difference between the 5 drives in the DS1511+ and the 5 drives in the DX510. Testing showed no performance difference between a 5 drive volume and a 10 drive volume, and the only physically noticeable difference was that the drives in the DX510 ran a few degrees hotter compared to the drives in the DS1511+.

As you can see from the results, the DS1511+ with MPIO performs really very well. Especially the 244MB/s ATTO read performance that gets close to the theoretical maximum of 250MB/s over a 2Gb/s link.

But technology moves quickly, and as I was compiling my test data for this post, Synology released two new NAS units, the [DS3611xs](http://www.synology.com/products/product.php?product_name=DS3611xs&lang=enu) and the [DS2411+](http://www.synology.com/products/product.php?product_name=DS2411%2B&lang=enu). The DS2411+ is very appealing, it is equivalent in performance to the DS1511+, but supports 12 drives in the main enclosure.  
 I may just have to exchange my DS1511+ and DX510 for a DS2411+…

\[Update: 25 July 2011\]  
 I returned the DS1511+ and DX510 in exchange for a DS2411+.  
 Read my performance review [here](/2011/07/synology-ds2411-performance.html).


