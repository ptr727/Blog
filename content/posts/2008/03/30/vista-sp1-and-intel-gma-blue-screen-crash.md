---
title: Vista SP1 and Intel GMA blue screen crash
date: '2008-03-31T03:50:00+00:00'
url: /2008/03/30/vista-sp1-and-intel-gma-blue-screen-crash/
categories:
- uncategorized
tags:
- intel
post_id: '71'
---
I previously commented on this problem [here](http://www.insanegenius.com/dg33tl/) and [here](http://www.avsforum.com/avs-vb/showthread.php?t=1008286).  

I participated in the Microsoft Vista SP1 Beta program.

After installing Vista SP1 Beta on my machine with an Intel DG33TL motherboard, and installing version 15.7.3 of the Intel GMA drivers, my machine would blue screen crash when it goes to sleep.

The crash happens in the igdkmd32.sys and igdkmd64.sys drivers, and I could reproduce it on two machines, both with DG33TL motherboards, with Vista x86 and x64.

I reported the problem to Microsoft, and Microsoft responded saying that Intel is aware of the problem, and that updated GMA drivers will be posted before Vista SP1 ships.

Microsoft released Vista SP1, and no updated Intel GMA drivers were available.

Intel released version 15.8 of the GMA drivers, and the SP1 blue screen problem was not resolved.

Microsoft released Vista SP1 to Windows Update, and the GMA driver problem was still not resolved.

Microsoft posted [KB948343](http://support.microsoft.com/Default.aspx?kbid=948343) stating that customers with specific versions of the GMA drivers would not get Vista SP1 via Windows Update until new GMA drivers are released.

To prevent my machines from crashing I am using the “high performance” power profile, i.e. they would never go to sleep.

It has been several months and the Intel has yet to resolve the problem, unbelievable.


