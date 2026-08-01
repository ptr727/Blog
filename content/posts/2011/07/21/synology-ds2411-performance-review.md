---
title: Synology DS2411+ Performance Review
date: '2011-07-21T19:43:00+00:00'
url: /2011/07/21/synology-ds2411-performance-review/
categories:
- performance
- power
- review
- storage
tags:
- iscsi
- mpio
- nas
- qnap
- synology
post_id: '121'
---
In my [last post](/2011/07/synology-ds1511-vs-qnap-ts-859-pro.html) I compared the performance of  [Synology DS1511+](http://www.synology.com/us/products/DS1511+/index.php) against the [QNAP TS-859 Pro](http://www.qnap.com/pro_detail_feature.asp?p_id=146). As I finished writing that post, Synology announced the new [Synology DS2411+](http://www.synology.com/us/products/DS2411+/index.php).   
Instead of using a DS1511+ and DX510 extender for 10 disks, the DS2411+ offers 12 disks in a single device. The price difference is also marginal, [DS1511+ is $836](http://amzn.to/KnkD02), the [DX510 is $500](http://amzn.to/Mm0IkU), and the [DS2411+ is $1700](http://amzn.to/JS31rA). That is a difference of only $364, and well worth it for the extra storage space, and the reliability and stability of all drives in one enclosure. I ended up returning my DX510 and DS1511+, and got a DS2411+ instead.

To test the DS2411+, I ran the same performance tests, using the same MPIO setup as I described in my [previous post](/2011/07/synology-ds1511-vs-qnap-ts-859-pro.html). The only slight difference was in the way I configured the [iSCSI](http://en.wikipedia.org/wiki/ISCSI) LUN; the DS1511+ was configured as SHR2, while the DS2411+ was configured as RAID6. Theoretically both are the same when all the disks are the same size, and SHR2 ends up using RAID6 internally.  
iSCSI LUN configuration:  
[![DS2411.iSCSI.LUN](/external/f9ec7f8636ba10fe.png)](/external/29528dce12eb779e.png)

At idle the DS2411+ used 42W power, and under load it used 138W power. The idle power usage is close to the [advertised 39W idle power usage](http://www.synology.com/products/spec.php?product_name=DS2411%2B&lang=us#p_submenu), but quite a bit more than the [advertised 105W power usage under load](http://www.synology.com/products/spec.php?product_name=DS2411%2B&lang=us#p_submenu).

I use [Remote Desktop Manager](http://remotedesktopmanager.com/) to manage all my devices in one convenient application. RDM supports web portals, Remote Desktop, Hyper-V, and many more remote configuration options, all in a single tabbed UI. What I found was that the [Synology DSM](http://www.synology.com/dsm/index.php?lang=enu) has some problems when running in a tabbed IE browser. When I open the log history, I get a script error, and whenever I focus away and back on the browser window, the DSM desktop windows shift all the way to the left. I assume this is a DSM problem related to absolute and relative referencing. I logged a support case, and I hope they can fix it.  
Script error:  
[![DS2411.DSM.Script.Error](/external/01ba6096e8e0590c.png)](/external/0de5c231d559227f.png)

Test results:  

**Device**

**ATTO Read**

**ATTO Write**

**CDM Read**

**CDM Write**

PM810267.153260.839256.674251.850DS2411+244.032165.564149.802156.673DS1511+244.032126.030141.213115.032TS-859 Pro136.17895.152116.01591.097[![Chart](/external/2a57e50d37a6dc8d.png)](/external/eaebbb85ca055898.png)  
DS2411+:  
[![Atto.Synology.MPIO](/external/0efcee7e6899deca.png)](/external/5eed7d1e7dad6d65.png)[![CDM.Synology.MPIO](/external/d9b5e792f71b06ba.png)](/external/b1e7953e1d40c241.png)  
DS1511+  
[![Atto.Synology.MPIO](/external/424f5ecbb366824f.png)](/external/347c74b4742c7fbe.png) [![CDM.Synology.MPIO](/external/b68fb95cc303e646.png)](/external/a01800afaf867024.png)

The DS2411+ [published performance numbers](http://www.synology.com/products/performance.php?lang=enu#tabs-10) are slightly better than the DS1511+ numbers, and my testing confirms that. so far I am really impressed with the DS2411+.


