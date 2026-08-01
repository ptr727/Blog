---
title: Windows 8 Install Crash With NVidia Quadro 5000
date: '2012-08-06T08:45:13+00:00'
url: /2012/08/06/windows-8-install-crash-with-nvidia-quadro-5000/
categories:
- problem
tags:
- crash
- nvidia
- pny
- quadro
- supermicro
- windows
post_id: '230'
---
I got Windows 8 RTM installed on my two SuperMicro SuperWorkstation machines, with a [bit of trouble](/2012/08/05/windows-8-install-hangs-booting-from-lsi-2308-sas-controller/) along the way, but nothing I could not work around. But, I ran into a problem with NVidia Quadro 5000 cards causing a [VIDEO\_TDR\_FAILURE](http://msdn.microsoft.com/en-us/library/windows/hardware/ff557263(v=VS.85).aspx) BSOD during the Windows 8 install process.

I was running my two workstations with [ATI FirePro V7900](http://amzn.to/LZehYW) graphic cards, but I decided I wanted a bit more rendering horsepower. I wanted a card that had a good balance between modern architecture, great 2D performance, good 3D performance, OpenCL or CUDA support, and reasonable power consumption. I found the [Tom’s Hardware Workstation Graphics 2012](http://www.tomshardware.com/charts/workstation-graphics-2012/benchmarks,139.html) benchmark site to be a very informative, and I decided that the [NVidia Quadro 5000](http://amzn.to/RrHg9L) was a very good choice.

I replaced my FirePro V7900 with the Quadro 5000, and started the Windows 8 x64 RTM install. All went well, until the first reboot during the install, and the machine would blue screen crash with a [VIDEO\_TDR\_FAILURE](http://msdn.microsoft.com/en-us/library/windows/hardware/ff557263(v=VS.85).aspx). During the install process the hardware is identified, the appropriate drivers extracted, and on the reboot those drivers are started. It appears that soon after the NVidia driver loads, that it crashes.

The [Timeout Detection and Recovery (TDR)](http://msdn.microsoft.com/en-us/library/windows/hardware/ff570087(v=vs.85).aspx) feature was added to Windows Vista, and was a way for the OS to recover from a renderer failure without the need to restart the machine. Typically the user will [see a notification](http://msdn.microsoft.com/en-us/library/windows/hardware/ff569917(v=vs.85).aspx) that the graphic subsystem was restarted, but in cases where the restart fails, a [VIDEO\_TDR\_FAILURE](http://msdn.microsoft.com/en-us/library/windows/hardware/ff557263(v=VS.85).aspx) blue screen crash is generated.

The web is full of reports of NVidia VIDEO\_TDR\_FAILURE crashes, and solutions typically involve replacing the hardware or updating drivers. In my case I had two new machines, and two new graphic cards, and a brand new operating system, and both cards on both machines crashed.

I contacted SuperMicro support, and responsive as they always are, said they would investigate.

I also contacted PNY support, as PNY is the manufacturer of the NVidia Quadro 5000, here is their reply.

> Again, I am sorry, but we do not list Windows 8 (yet) as being compatible with the Quadro 5000, or any other Quadro or Geforce card we manufacture. Until it is publically and commercially available, we cannot provide support for Windows 8. Windows 8 is not available to the end user yet, and it is in testing, as is the Nvidia driver. If you find issues, you must report them to Microsoft in order to improve compatibility in the final release. There is obviously a compatibility problem with Windows 8 and the Quadro 5000 right now (according to your testing of TWO cards), and unfortunately there is nothing we can do to fix it while in is not available to the public. My best advice is to try it again when it is officially released sometime in 2013.

Not very helpful at all, and their concept of Windows 8 release timing, and their responsibility, is way out there.

The real problem here is that it is the in-box NVidia drivers that are crashing, not drivers I install later. And as it is the in-box graphic drivers that crash, there is no (easy) way to update the drivers used by the Windows 8 install media.

I had previously used a Quadro 4000 card on the same machines, and they installed without incident, so it appears to be something unique the Quadro 5000 cards.

At this time I am waiting for SuperMicro to get back to me with suggestions, as I have little hope of hearing anything useful from PNY.
