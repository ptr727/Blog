---
title: Razer BSOD When Driver Verifier is Enabled
date: '2017-04-26T05:13:57+00:00'
url: /2017/04/25/razer-bsod-when-driver-verifier-is-enabled/
categories:
- problem
- review
tags:
- razer
post_id: '1522'
cover:
  alt: 20170416_201259779_iOS
  image: /media/2017/04/20170416_201259779_ios.jpg
---
Not too long ago I complained about [Razer's poor UX and Support](/2017/03/28/razer-shoddy-support-and-bad-software-ux/), this time it is a BSOD in one of their drivers, and forever crashing [Razer Stargazer](https://www.razerzone.com/gaming-broadcaster/razer-stargazer) camera software.

I've been looking for a Windows Hello capable webcam, and the Razer Stargazer, based on [Intel RealSense](http://www.intel.com/content/www/us/en/architecture-and-technology/realsense-overview.html) technology, looked promising. The device is all metal and tactical looking, but the software experience is so buggy, install this, install that, then crash after crash after crash. I ended up returning it for a refund, and got a [Logitech BRIO](http://amzn.to/2pjE9I8) instead, the BRIO is cheaper, and works great.

A couple days ago I was greeted with a BSOD on one of my test machines, a crash in the RZUDD.SYS "Razer Rzudd Engine" driver, part of the Razer Synapse software. What makes this interesting, is that the issue seems to be triggered by having [Driver Verifier](https://msdn.microsoft.com/en-us/windows/hardware/drivers/devtest/driver-verifier) enabled.

![20170416_201259779_iOS](/media/2017/04/20170416_201259779_ios.jpg)

One may be tempted to say do not enable Driver Verifier, but, the point of driver verifier is to help detect bugs in drivers, and is a basic requirement for driver certification. Per the WinDbg analysis, this appears to be a memory corruption bug. After some searching, I found that the Driver Verifier BSOD has been reported by [other users](https://insider.razerzone.com/index.php?threads/rzudd-sys-causing-bsod.14500/), with no acknowledgement, and no fix forthcoming. I contacted Razer support, and not surprisingly, they suggested uninstall and reinstall. I tried the [community forums](https://insider.razerzone.com/index.php?threads/rzudd-sys-bsod-when-driver-verifier-is-enabled.22256/), and I was just pointed back to support.

\[code\]
FAULTING\_IP:
rzudd+28c80
...
DEFAULT\_BUCKET\_ID: CODE\_CORRUPTION
...
PROCESS\_NAME: RzSynapse.exe
...
STACK\_TEXT:
nt!KeBugCheckEx
nt!MiSystemFault+0x12e69c
nt!MmAccessFault+0xae6
nt!KiPageFault+0x132
rzudd+0x28c80
rzudd+0x218d4
rzudd+0x7a9f
Wdf01000!FxIoQueue::DispatchRequestToDriver+0x1bf \[minkernel\\wdf\\framework\\shared\\irphandlers\\io\\fxioqueue.cpp @ 3325\]
Wdf01000!FxIoQueue::DispatchEvents+0x3bf \[minkernel\\wdf\\framework\\shared\\irphandlers\\io\\fxioqueue.cpp @ 3125\]
Wdf01000!FxPkgIo::DispatchStep1+0x53e \[minkernel\\wdf\\framework\\shared\\irphandlers\\io\\fxpkgio.cpp @ 324\]
Wdf01000!FxDevice::DispatchWithLock+0x5a5 \[minkernel\\wdf\\framework\\shared\\core\\fxdevice.cpp @ 1430\]
nt!IovCallDriver+0x245
...
FAILURE\_BUCKET\_ID: MEMORY\_CORRUPTION\_LARGE
\[/code\]

I am done with Razer, exciting promises for technology on paper, great looking hardware, terrible support, terrible software.
