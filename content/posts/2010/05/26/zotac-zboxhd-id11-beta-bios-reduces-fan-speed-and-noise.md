---
title: Zotac ZBOXHD-ID11 Beta BIOS Reduces Fan Speed and Noise
date: '2010-05-26T21:18:00+00:00'
url: /2010/05/26/zotac-zboxhd-id11-beta-bios-reduces-fan-speed-and-noise/
categories:
- review
tags:
- bios
- boxee
- fan
- htpc
- intel
- ion
- minipc
- noise
- temperature
- zbox
- zotac
post_id: '106'
---
In a [previous post](/2010/05/zotac-zboxhd-id11-fan-speed-and-noise.html) I measured the fan speed and noise under load, and I found it to be unacceptably high.   
Zotac support notified me that a new Beta BIOS is available that address the issue.   
In this post I measure the difference between the release BIOS and the Beta BIOS.

This is the fourth post in a [series of posts related to the Zotac ZBOX ZBOXHD-ID11](/2010/05/zotac-zbox-mini-pc-zboxhd-id11.html).

Summary:

- The Beta BIOS reduces the fan speed and noise significantly.
- The default BIOS values need some adjustment to get acceptable results.
- Similar results may be possible with the current BIOS by setting the target temperature to 65C.

The Beta BIOS was first announced on the [global Zotac site](http://www.zotac.com/index.php?lang=un), it only later appeared on the [US site](http://www.zotacusa.com/). I would recommend that ID11 owners look for [updates on the global site](http://www.zotac.com/index.php?option=com_docman&task=cat_view&gid=223&Itemid=100032&lang=un) instead of the US site.   
The Beta BIOS is available for download from [here](http://downloads.zotac.com/mediadrivers/mb/bios/pa140beta.zip).

As with the [4GB BIOS update](/2010/05/zotac-zboxhd-id11-4gb-ram.html), the update tools included in the Zip file do not work on Windows 7 x64. I [downloaded](http://www.ami.com/support/downloadagreement.cfm?DLFile=support/downloads/amiflash.zip&InpDrvID=90) the latest BIOS update tools from the AMI site, and used the AFUWinx64.exe application to update the BIOS.

Below are two screenshots of the BIOS, first the Beta BIOS, then the current BIOS:   
[![Beta.BIOS.PCHealth](/external/3240c088a346e983.jpg)](/external/47d416e4617d5c9b.jpg)

[![Health.Monitor](/external/6360485800d920ec.jpg)](/external/9a14a8e6400f29bb.jpg)

The new \[CPUFAN Mode\] Setting is called \[SMART Mode\].   
Several of the parameters changed, and the fan ratio settings are no longer 0-255, but a percentage value.

I changed the BIOS values to:   
\[Smart FAN start Temperature\] = 50C   
\[CPUFAN Tolerance Value\] = 2C   
\[CPUFAN Lowest Value\] = 30%   
\[CPUFAN Maximum Value\] = 100%   
\[CPUFAN Step Value\] = 4%

I ran a series of tests to determine what the minimum fan speed is in relation to the \[CPUFAN Lowest Value\] setting:   
20% = No value reported by BIOS.   
30% = 1000RPM   
40% = 1800RPM   
50% = 2500RPM

At 20% the BIOS did not report a fan speed. Visual inspection showed the fan was spinning, but very slow. I think too slow for such a small fan, so I set the value to 30%.

At idle the CPU runs at or just below 50C, so I set the \[Smart FAN start Temperature\] to 50C.

I left the \[CPUFAN Tolerance Value\] and the \[CPUFAN Step Value\] values at the BIOS defaults of 2C and 4%.

I placed the system under load with the \[CPUFAN Maximum Value\] value at 90% and 100%, but in both cases the maximum fan speed never exceeded 3300RPM, so it appears as if the 90% throttling value was not reached in my tests. To be on the safe side I set the \[CPUFAN Maximum Value\] at 100%.

Although the latest Beta version of Lavalys EVEREST now correctly detects the Winbond controller, it still does not report accurate readings. So in order to measure values under load, I used [CPUID Hardware Monitor Pro](http://www.cpuid.com/softwares/hwmonitor-pro.html) to measure, and [Great Internet Mersenne Prime Search (GIMPS)](http://www.mersenne.org/) to place the system under load.

As in my [previous test](/2010/05/zotac-zboxhd-id11-fan-speed-and-noise.html), I let the system sit idle, placed it under load, then back to idle, while I recorded the fan speed and temperatures.

Below are two graphs showing fan speed under load, first the Beta BIOS, then the current BIOS:   
[![CPUFANIN0.Beta.Stability](/external/21c8403f1ab76c73.png)](/external/0458cbe3c742e195.png)

[![CPUFANIN0.Stability](/external/18acf1b0c5bc4392.png)](/external/ac32f68dd6673058.png)

Comparing the graphs, the Beta BIOS maximum fans speed is around 2400RPM, while the current BIOS maximum fan speed is around 5300RPM. The Beta BIOS made a significant improvement in reducing fan speed and noise.

Below are two graphs showing CPU temperature under load, first the Beta BIOS, then the current BIOS:   
[![CPUTIN.Beta.Stability](/external/95aa5e630c988301.png)](/external/219b9a895c92f36f.png)

[![CPUTIN.Stability](/external/bbb833a01d8120b8.png)](/external/395d80b93384176d.png)

Comparing the graphs, the Beta BIOS lets the CPU temperature reach around 65C, while the current BIOS limits the CPU temperature to around 50C. In the Beta BIOS the \[Smart FAN start Temperature\] is set to 50C, and in the current BIOS the \[CPUFAN TargetTemp Value\] was set to 50C. The 50C \[CPUFAN TargetTemp Value\] was the value recommended by Zotac support. I wonder if the value was set to 65C if the fan would have been comparable to the Beta BIOS?


