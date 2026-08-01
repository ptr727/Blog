---
title: Zotac ZBOXHD-ID11 Fan Speed and Noise
date: '2010-05-19T00:38:00+00:00'
url: /2010/05/18/zotac-zboxhd-id11-fan-speed-and-noise/
categories:
- review
tags:
- boxee
- fan
- htpc
- noise
- zbox
- zotac
post_id: '100'
---
In my previous post I discussed [my initial impressions of the Zotac ZBOXHD-ID11](/2010/05/zotac-zboxhd-id11-first-impressions.html).   
In this post I continue my review, focusing on fan speed and noise.   

This is second post in a [series of posts related to the Zotac ZBOX ZBOXHD-ID11](/2010/05/zotac-zbox-mini-pc-zboxhd-id11.html).


Summary:   
\- High fan speed and noise while under load.   
\- Fan never returns to silent operation after load is removed.   
\- Need DXVA capable player for video playback.   

\[Update: 26 May 2010\]   
I [tested the Beta BIOS](/2010/05/zotac-zboxhd-id11-beta-bios-reduces-fan.html), and produced significantly better results. Effectively the new BIOS runs the CPU at 65C vs. 50C, as such you may be able to achieve the same results with the current BIOS by simply changing the CPU temperature threshold to 65C.

Last time I tried [Lavalys EVEREST](http://www.lavalys.com/) and [SpeedFan](http://www.almico.com/speedfan.php) to measure the CPU/GPU temperature and fan speed, but neither application was able to detect the fan, and both applications produced questionable results for the CPU temperature.   
A [Media-Portal forum](http://forum.team-mediaportal.com/barebones-commercial-htpcs-352/zotac-zbox-hd-id11-81693/index3.html) reader responded, and said I should try [CPUID Hardware Monitor](http://www.cpuid.com/hwmonitor.php), which I did, and it works. Actually, I used [CPUID Hardware Monitor Pro](http://www.cpuid.com/hwmonitorpro.php), this way I can capture values over time, and easily produce graphs.

Below is a picture of the hardware detected as a Winbond W83627DHG:   
![](/external/4e47ba5384521179.png)  
My test methodology is to measure from power on, idle, under load, and back to idle.

I let the ID11 reach room temperature (73F / 23C), I cold booted, and after logging in, immediately started Hardware Monitor Pro (HWMP). I let the ID11 sit idle for a few minutes. The fan remained very slow and very quiet, almost impossible to hear.   
The idle fan speed is around 180RPM.

Next I launched EVEREST system stability test, this placed the CPU under load, I ran this for a few minutes. Almost immediately the fan speed increased, and became very loud.   
The high fan speed is around 5300RPM.   
The case reached a temperature of 112F / 44C.

After stopping the system stability test, I let the system idle for a few minutes. The fan speed reduced, but never returned to the initial very low speed. At this speed the fan is audible, about the same noise level as a spinning hard drive.   
The return to idle fan speed is around 1400RPM.

Below are graphs showing CPU, GPU, and fan speed over time during the stability test:   
![](/external/de6265b71ed0cd91.png)  
![](/external/a2797158972334b6.png)  
![](/external/f08ea9ffcce2345a.png)

I expected the fan to go back to the initial very low speed, but it didn’t. I was not sure if I should let the system idle for longer, so I repeated the test.

But, instead of using EVEREST, I used [XBMC 9.11](http://xbmc.org/download/) using all default options.   
I chose to play a 39GB DTS H264 MKV file, this file is a very high bit rate Blu-Ray rip, and I know that my netbook stutters when playing this file, while my workstation has no problems playing it.

Immediately after starting playback the fan speed increased, and became very loud, same as during the stability test.   
The high fan speed is around 5300RPM.   
The case reached a temperature of 108F / 42C.

As before, the fan never went back to super quiet, even after sitting idle for a very long time.   
The return to idle fan speed is around 2000RPM.

This behavior may be a BIOS problem, or it may be the thermal characteristics of the ID11.

Below are graphs showing CPU, GPU, and fan speed over time during movie playback:   
![](/external/d846daa9fb005c94.png)  
![](/external/7c7d2c8ca28c936b.png)  
![](/external/bb35b565f71256a2.png)

Although I was not focusing on video performance, it was clear that the video stuttered, and this was confirmed by looking at the on screen playback statistics. There was a very high frame drop count, and the frame rate was around 13fps, far from the 24fps target.

Below are two OSD captures, one from the ID11, and one from my [DELL Core i7 XPS 9000](http://www.dell.com/us/en/home/desktops/desktop-studio-xps-9000/pd.aspx?refid=desktop-studio-xps-9000&cs=19&s=dhs) workstation:   
![](/external/e2e89fa476af650b.png)  
![](/external/8ada2e7cd345c95d.png)

The default XBMC does not work on the ID11. A little bit of searching revealed that the internal decoders used by XBMC do not support GPU acceleration, and instead relies on the CPU to the rendering.   
There is a Windows specific port of XBMC using DirectShow codecs that do support [DirectX Video Hardware Acceleration (DXVA)](http://en.wikipedia.org/wiki/DirectX_Video_Acceleration), called [DSPlayer](http://forum.xbmc.org/showthread.php?t=61355).

When I do a more elaborate video performance test I will use only DXVA capable players.


