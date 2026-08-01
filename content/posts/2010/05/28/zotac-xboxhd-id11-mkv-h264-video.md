---
title: Zotac XBOXHD-ID11 MKV H.264 Video Playback Performance
date: '2010-05-29T00:28:00+00:00'
url: /2010/05/28/zotac-xboxhd-id11-mkv-h264-video/
categories:
- review
tags:
- boxee
- coreavc
- ffdshow
- htpc
- mediacenter
- mediaportal
- mkv
- wmp
- xbmc
- zbox
- zotac
post_id: '109'
---
When I started writing about the [ID11](http://www.zotacusa.com/zotac-zboxhd-id11-u-intel-atom-d510-1-66-ghz-dual-core-all-in-one-mini-pc.html), my intent was to document video playback and use as a HTPC, several posts later, and I am finally getting to [MKV](http://en.wikipedia.org/wiki/Mkv) [H.264](http://en.wikipedia.org/wiki/H.264/MPEG-4_AVC) playback configuration and performance.

This is the sixth post in a [series of posts related to the Zotac ZBOX ZBOXHD-ID11](/2010/05/zotac-zbox-mini-pc-zboxhd-id11.html).

Summary:

- The CPU is not powerful enough to render / decode H.264 video, and GPU acceleration via [DXVA](http://en.wikipedia.org/wiki/DXVA) is required, as well as a DXVA capable player.
- The [Microsoft DTV-DVD Video Decoder](http://msdn.microsoft.com/en-us/library/dd390679(VS.85).aspx), included as part of Windows 7 x64, worked perfectly for H.264 playback, and compared to other H.264 decoders had the lowest CPU usage.
- As standalone player, [Media Player Classic Home Cinema](http://mpc-hc.sourceforge.net/), is a perfect choice, it supports MKV, H.264, DXVA, and subtitles without the need of any other software.
- Playback of MKV H.264 in [Windows Media Player](http://www.microsoft.com/windows/windowsmedia/player/default.aspx), [Windows Media Center](http://www.microsoft.com/windows/windows-media-center/), [MediaPortal](http://www.team-mediaportal.com/), or [XBMC](http://xbmc.org/) requires the installation of [Haali Media Splitter](http://haali.su/mkv/), and [ffdshow](http://ffdshow-tryout.sourceforge.net/) audio and video decoders.
- For [AC-3](http://en.wikipedia.org/wiki/Dolby_Digital) / [DTS](http://en.wikipedia.org/wiki/DTS_(sound_system)) pass-through playback via [S/PDIF](http://en.wikipedia.org/wiki/S/PDIF) / [HDMI](http://en.wikipedia.org/wiki/Hdmi), the ffdshow audio decoder is required.

I am not an expert in how these things work, but I have a basic understanding of video playback on Windows platforms, so let’s start with the file format; an MKV file is a [Matroska Media Container](http://www.matroska.org/) file. A MKV file can contain multiple audio-, video-, subtitle-, and other, streams. A MKV file is not a video or audio compression format, it is just a container.

To play the contents of a MKV file, you need a de-multiplexer or splitter, the splitter understands the container format, and produces separate output streams.

The stream output is processed by the stream decoders, typically known as [DirectShow](http://en.wikipedia.org/wiki/DirectShow) filters. The stream filters need to understand the stream contents, e.g. H.264 video, DTS audio, subtitles, etc.

Lastly there are the renderers, the renderer produces the final output such as video display or audio output.

In case of DXVA, the video decoder and the video renderer have a close relationship, the DXVA decoded content can be directly rendered from GPU memory. In comparison, the [CoreCodec](http://corecodec.com/) [CoreAVC](http://corecodec.com/products/coreavc) codec supports GPU hardware acceleration, but it uses the [NVIDIA CUDA](http://www.nvidia.com/object/what_is_cuda_new.html) platform for mathematical processing. The CUDA decoded content needs to be copied to GPU memory, resulting in [higher CPU utilization](https://customers.corecodec.com/knowledgebase/3/What-is-better-CUDA-or-DXVA.html).

An easy way to visualize the stream flow is to use [MONOGRAM GraphStudio](http://blog.monogram.sk/janos/).

I spent quite a bit of time getting the right versions of the right software installed, and on two occasions new versions were released during my testing, and I had to test again. I started by using the [K-Lite Codec Pack](http://www.codecguide.com/). But, I know not everybody installs codec packs, and not everybody uses K-Lite, so I wanted to find the minimum set of components required for playback without the use of a codec pack.

In my testing Windows and CoreCodec CoreAVC were the only commercial products, the remainder are free, and of the free products, only Haali Media Splitter is not open source.

I used the following product versions:

**Product**

**Version**

[Media Player Classic Home Cinema](http://mpc-hc.sourceforge.net/)[1.2.1249 (x64)](http://sourceforge.net/projects/mpc-hc/files/MPC%20HomeCinema%20-%20x64/MPC-HC%20v1.3.1249.0_64%20bits/MPC-HomeCinema.1.3.1249.0.(x64).exe/download)[Haali Media Splitter](http://haali.su/mkv/)[1.10.175.0 (x86, x64)](http://haali.su/mkv/MatroskaSplitter.exe)[ffdshow tryouts](http://ffdshow-tryout.sourceforge.net/)rev 3452 ([x86](http://sourceforge.net/projects/ffdshow-tryout/files/SVN%20builds%20by%20xxl/win32%20generic%20builds/ffdshow_rev3452_20100524.exe/download), [x64](http://sourceforge.net/projects/ffdshow-tryout/files/SVN%20builds%20by%20clsid/64-bit%20builds/ffdshow_rev3452_20100523_clsid_x64.exe/download))[MediaPortal](http://www.team-mediaportal.com/)[1.1.0 RC3 (x86)](http://sourceforge.net/projects/mediaportal/files/MediaPortal%20Setup/MediaPortal%201.1.0%20RC%203/MediaPortalSetup_1.1.0%20RC3.exe/download)[XBMC](http://xbmc.org/) [DSPlayer](http://forum.xbmc.org/showthread.php?t=61355)[rev 30385 (x86)](http://dsplayer.passion-xbmc.org/Dsplayer/XBMCSetup-Rev30385-dx.exe)[CoreCodec CoreAVC](http://corecodec.com/products/coreavc)[2.0 (x86, x64)](https://customers.corecodec.com/cart.php?a=add&pid=1)[Microsoft DTV-DVD Video Decoder](http://msdn.microsoft.com/en-us/library/dd390679(VS.85).aspx)[Windows 7 Ultimate x64](http://www.microsoft.com/windows/windows-7/)[Windows Media Player](http://www.microsoft.com/windows/windowsmedia/player/default.aspx)[Windows 7 Ultimate x64](http://www.microsoft.com/windows/windows-7/)[Windows Media Center](http://www.microsoft.com/windows/windows-media-center/)[Windows 7 Ultimate x64](http://www.microsoft.com/windows/windows-7/)

I tested by letting the system idle, then playing a one minute, 1080p, MKV, H.264, DTS, subtitles, video clip, full screen, on a 1920x1200 display, then back to idle. Where possible the player was set to auto repeat and play for ten minutes, where the player did not support auto-repeat, I manually played the clip three times. While playing, I recorded the CPU utilization using Windows Task Manager, the GPU utilization using [GPU-Z](http://www.techpowerup.com/gpuz/), and the fan speed, CPU and GPU temperature using [CPUID Hardware Monitor Pro](http://www.cpuid.com/softwares/hwmonitor-pro.html).

[Media Player Classic Home Cinema](http://mpc-hc.sourceforge.net/) is simple to use; install it, open the MKV file, and it plays, with subtitles, with MCE remote control support, no additional configuration required. MPC-HC includes all the components required for playback, and does not require any system installed components to function.

From what I read, MPC-HC was the first player to include DXVA accelerated playback. Both DSPlayer and MediaPortal include codecs based on MPC-HC code.

An alternative standalone player, that I did not test, is the [VLC Media Player](http://www.videolan.org/vlc/).

Below are the MPC-HC graphs for fan speed, CPU temperature, and GPU temperature:

[![MPC.CPUFANIN](/external/2306d6b29cb2543c.png)](/external/6215e8ea9fa1f141.png)

[![MPC.CPUTIN](/external/d2b707889bb6d9b7.png)](/external/0fcf7b3d7e5ad14f.png)

[![MPC.GPU.Temp](/external/a8b71c1452b5c2ab.png)](/external/c91df823e853d6c6.png)

Below are the MPC-HC graphs for CPU and GPU utilization:

[![MPC.CPU](/external/11904361ff16d3c5.png)](/external/c544aac68b106548.png)

[![MPC.GPU](/external/fa46471fda0d1ce7.png)](/external/e0a024ea71a7117a.png)

[Windows Media Player](http://www.microsoft.com/windows/windowsmedia/player/default.aspx) is included with the standard Windows installation. WMP uses the system installed DirectShow filers for playback. Even on a x64 system, WMP is still a x86 process, as such, it requires the installation of x86 filters.

In order for WMP to open MKV files, a splitter is required, I used [Haali Media Splitter](http://haali.su/mkv/).

I tested playback with three different video decoders; the [Microsoft DTV-DVD Video Decoder](http://msdn.microsoft.com/en-us/library/dd390679(VS.85).aspx), [CoreCodec CoreAVC](http://corecodec.com/products/coreavc), and [ffdshow tryouts](http://ffdshow-tryout.sourceforge.net/).

I have read that it is possible to get subtitles working with WMP, but even with enabling subtitles in ffdshow, I could not get subtitles to show in WMP. I am sure it is possible, I just didn’t spend the effort to make it work.

When multiple codecs are installed, WMP player uses the preferred codec for playback. The preferred codec can be set using the [Preferred Filter Tweaker for Windows 7](http://www.codecguide.com/windows7_preferred_filter_tweaker.htm), or it may be easier to just install one codec at a time:

[![Win7DSFilterTweaker](/external/a0731785a8fb22fa.png)](/external/20dee913aede70a9.png)

Haali Media Splitter provides an alternative way of forcing video decoding using ffdshow, HMS can change the video output type to a format that is only registered for decoding by ffdshow. This is accomplished by using the \[Use custom media type for H.264\]. This allows you to easily switch between the Windows default (\[No\]), and ffdshow (\[Yes\]):

[![Haali.Custom.Output](/external/08ba707abdb8a844.png)](/external/94d97b7833578701.png)

In order to use hardware acceleration in ffdshow, the ffdshow DXVA codec needs to be configured for H.264 hardware acceleration:

[![ffdshow.Hardware.Acceleration](/external/49b5adea92320e7c.png)](/external/18b9b5d4b9954005.png)

You may also need to change the DirectShow control options in ffdshow to allow the filter to be used in your player’s process space:

[![ffdshow.DirectShow.Control](/external/62f61a44ff65e933.png)](/external/496ff9c113b56264.png)

Below are GraphStudio graphs showing the various codecs in action:

[![Windows.Graph](/external/b01394e9806d1d61.png)](/external/9a3a3c4d26313266.png)

[![CoreAVC.Graph](/external/cd6849bfe158d4aa.png)](/external/684afc218015c567.png)

[![ffdshow.Graph](/external/2572ccc7fb119084.png)](/external/c20ec7fa3b2b68ed.png)

Below are the WMP with Microsoft DTV-DVD Video Decoder graphs for fan speed, CPU and GPU temperature:

[![MediaPlayer.Windows.CPUFANIN0](/external/d3e1cb3698949883.png)](/external/54cbcb2a7144fb0e.png)

[![MediaPlayer.Windows.CPUTIN](/external/93ef613d752e7fe3.png)](/external/8743b22eaf3ed78e.png)

[![MediaPlayer.Windows.GPU.Temp](/external/0715b3d73a5dc7cd.png)](/external/03c8e5979d454a5e.png)

Below are the WMP with Microsoft DTV-DVD Video Decoder graphs for CPU and GPU utilization:

[![MediaPlayer.Windows.CPU](/external/28c4fdf789d3315c.png)](/external/cac454e9e4b1362d.png)

[![MediaPlayer.Windows.GPU](/external/a8c14ed774678cb6.png)](/external/914447adf3168275.png)

Below are the WMP with CoreAVC graphs for fan speed, CPU and GPU temperature:

[![MediaPlayer.CoreAVC.CPUFANIN0](/external/3edf62a10598adac.png)](/external/731dde0d8d9a0947.png)

[![MediaPlayer.CoreAVC.CPUTIN](/external/0797330915ccd2e3.png)](/external/d53daac344268322.png)

[![MediaPlayer.CoreAVC.GPU.Temp](/external/f9098ee2622e80b3.png)](/external/40744c565052422f.png)

Below are the WMP with CoreAVC graphs for CPU and GPU utilization:

[![MediaPlayer.CoreAVC.CPU](/external/28031b2f765d0a0b.png)](/external/83e9a0dc2c71488a.png)

[![MediaPlayer.CoreAVC.GPU](/external/a19c6c8704e718f0.png)](/external/5c28421f7fed8acc.png)

Below are the WMP with ffdshow DXVA graphs for fan speed, CPU and GPU temperature:

[![MediaPlayer.ffdshow.CPUFANIN0](/external/b19fff9f9bccd0ad.png)](/external/7fafb54885003c1d.png)

[![MediaPlayer.ffdshow.CPUTIN](/external/205370f703221e08.png)](/external/525cf258da94b047.png)

[![MediaPlayer.ffdshow.GPU.Temp](/external/05997d0804a4e1cc.png)](/external/012780e57b2fc504.png)

Below are the WMP with ffdshow DXVA graphs for CPU and GPU utilization:

[![MediaPlayer.ffdshow.CPU](/external/89f81ae189e0c69f.png)](/external/0197cac21b87bbd5.png)

[![MediaPlayer.ffdshow.GPU](/external/fca7f179ec89bd47.png)](/external/50f59c5ca85db101.png)

[Windows Media Center](http://www.microsoft.com/windows/windows-media-center/) is included with the Premier and Ultimate editions of Windows. MCE does not use DirectShow for playback, instead it uses [Windows Media Foundation](http://en.wikipedia.org/wiki/Media_Foundation). In order to use DirectShow filters in MCE, either the media type is not natively supported by WMF but is supported by DS, or the WMF media type is disabled using e.g. [Preferred Filter Tweaker for Windows 7](http://www.codecguide.com/windows7_preferred_filter_tweaker.htm). MCE runs as a x64 process on a x64 system, as such, it requires the installation of x64 filters.

As with WMP, MCE also requires the [Haali Media Splitter](http://haali.su/mkv/) to open MKV files. And to use ffdshow instead of the default WMF decoders, set the HMS \[Use custom media type for H.264\] option to \[Yes\].

I tested playback with two different video decoders; the [Microsoft DTV-DVD Video Decoder](http://msdn.microsoft.com/en-us/library/dd390679(VS.85).aspx), and [ffdshow tryouts](http://ffdshow-tryout.sourceforge.net/).

I have read that it is possible to get subtitles working with MCE, but even with enabling subtitles in ffdshow, I could not get subtitles to show in WMP. I also tried the [Media Control](http://damienbt.free.fr/) plugin that is supposed to enable remote control support for ffdshow subtitles, but I could not get it to work. As with WMP, I am sure it is possible, I just didn’t spend the effort to make it work.

I could not find a way to loop playback in MCE, or in MediaPortal, or in XBMC, so instead I manually played the video three times in a row. The resulting fan speed, CPU and GPU temperature graphs are not very interesting, so I am only including the CPU and GPU utilization graphs.

Below are the MCE with Microsoft DTV-DVD Video Decoder graphs for CPU and GPU utilization:

[![MediaCenter.Windows.CPU](/external/b7c6b85ac64a9c04.png)](/external/1eb7f5bc9a39f266.png)

[![MediaCenter.Windows.GPU](/external/6db034d18abe9d7f.png)](/external/2e64051b839ca3b5.png)

Below are the MCE with ffdshow DXVA graphs for CPU and GPU utilization:

[![MediaCenter.ffdshow.CPU](/external/68d24de592ffcefb.png)](/external/daec58261bb0e705.png)

[![MediaCenter.ffdshow.GPU](/external/59c6379fe9c9a185.png)](/external/cc7debaff3f34c43.png)

[MediaPortal](http://www.team-mediaportal.com/) is a Home Theater PC frontend, similar to Windows Media Center, but open source. Like WMP, MP uses DirectShow for playback, but unlike WMP, or MCE, MP allows for explicit filter configuration, including which filters to use for which media types:

[![MediaPortal.Codec](/external/4cf0a8a95c3a9e49.png)](/external/c41341554aa94759.png)

I tested playback with two different video decoders; the [Microsoft DTV-DVD Video Decoder](http://msdn.microsoft.com/en-us/library/dd390679(VS.85).aspx), and [ffdshow tryouts](http://ffdshow-tryout.sourceforge.net/).

Below are the MP with Microsoft DTV-DVD Video Decoder graphs for CPU and GPU utilization:

[![MediaPortal.Windows.CPU](/external/d4e791439c3eacfe.png)](/external/8b21e0d0dadc83ef.png)

[![MediaPortal.Windows.GPU](/external/e38972d183ec8709.png)](/external/33aeacc6a891cf3f.png)

Below are the MP with ffdshow DXVA graphs for CPU and GPU utilization:

[![MediaPortal.ffdshow.CPU](/external/819540bffc706dc2.png)](/external/39179b4e681a8e94.png)

[![MediaPortal.ffdshow.GPU](/external/c9979eb47803dcbc.png)](/external/6979f1c6ddc39f28.png)

[XBMC](http://xbmc.org/) is a Home Theater PC frontend, similar to Windows Media Center, but like MediaPortal, it is open source. Unlike MediaPortal, that just supports Windows, XBMC also supports Mac, Linux, and XBox. XBMC has its roots in the XBox, but XBox support has just been suspended. In order to support DXVA on Windows, a Windows only DirectShow port of XBMC was created called [DSPlayer](http://forum.xbmc.org/showthread.php?t=61355).

In order to switch between codecs used in XBMC DSPlayer, you have to edit a configuration file. Details of the process can be found [here](http://wiki.xbmc.org/?title=HOW-TO:_Using_DSPlayer).

I read that DXVA2 support will be natively supported in future XBMC builds. The DSPlayer build of XBMC is much newer than the latest released XBMC. This build of XBMC included native support for DXVA2 without the need to use DSPlayer. The DXVA2 option is in the system menu. I did notice that the first few seconds of playback produced screen artifacts, hopefully this will be corrected when this functionality is released.

I tested playback with three different video decoders; built in DXVA2, DSPlayer MPC codec, and DSPlayer [ffdshow tryouts](http://ffdshow-tryout.sourceforge.net/).

Below are the XBMC with DXVA2 graphs for CPU and GPU utilization:

[![XBMC.DVDPlayer.CPU](/external/a616adc9e25701f1.png)](/external/bf95c1967a8195f0.png)

[![XBMC.DVDPlayer.GPU](/external/679ed94b9f241c82.png)](/external/30b825245c2355a6.png)

Below are the XBMC DSPlayer MPC graphs for CPU and GPU utilization:

[![XBMC.DSPlayer.MPC.CPU](/external/e59778db97bf36cd.png)](/external/02b65508927a4fed.png)

[![XBMC.DSPlayer.MPC.GPU](/external/2c7c315c5b096195.png)](/external/7b907b810b13e078.png)

Below are the XBMC DSPlayer ffdshow DXVA graphs for CPU and GPU utilization:

[![XBMC.DSPlayer.ffdshow.CPU](/external/1385b55325802410.png)](/external/1ff977f94cbbd0e4.png)

[![XBMC.DSPlayer.ffdshow.GPU](/external/31d3909d9c5045d2.png)](/external/93c5b65f3de82abb.png)

Playback load summary:

**Configuration**

**Fan Speed**

**CPU Temp**

**GPU Temp**

**CPU Load**

**GPU Load**

MPC-HC2700RPM62C84CLowHighWMP, DTV-DVD2400RPM59C78CVery LowLowWMP, CoreAVC1800RPM54C86CMediumMediumWMP, ffdshow2400RPM59C78CLowMediumMCE, DTV-DVDVery LowMediumMCE, ffdshowLowMediumMP, DTV-DVDLowLowMP, ffdshowLowMediumXBMC, DXVA2Very LowMediumXBMC, MPCLowMediumXBMC, ffdshowLowMedium

Conclusion:

If all you need is video playback, you can’t go wrong with [Media Player Classic Home Cinema](http://mpc-hc.sourceforge.net/).

All other configurations require [Haali Media Splitter](http://haali.su/mkv/) and [ffdshow](http://ffdshow-tryout.sourceforge.net/).

If you want to use Windows Media Center or Windows Media Player with subtitles, you will need to do some more research.

If you run Windows and want a MCE alternative that is easily configurable, use [MediaPortal](http://www.team-mediaportal.com/).

If you need Mac or Linux support use [XBMC](http://xbmc.org/), or if don’t mind configuration files and bleeding-edge code on Windows, use [DSPlayer](http://forum.xbmc.org/showthread.php?t=61355).

As long as your player of choice supports DXVA, the ID11 has no problem playing 1080p MKV H.264 content.


