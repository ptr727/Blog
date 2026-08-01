---
title: Zotac ZBOXHD-ID11 First Impressions
date: '2010-05-15T06:30:00+00:00'
url: /2010/05/14/zotac-zboxhd-id11-first-impressions/
categories:
- review
tags:
- boxee
- htpc
- intel
- ion
- minipc
- zbox
- zotac
post_id: '99'
---
Untitled Page

I am sharing my experiences and first impressions of the [Zotac ZBOXHD-ID11-U](http://www.zotacusa.com/zotac-zboxhd-id11-u-intel-atom-d510-1-66-ghz-dual-core-all-in-one-mini-pc.html "Zotac ZBOXHD-ID11-U") mini PC.

In the coming days I will connect the device to my home theater, and review the behavior running [Windows Media Center](http://www.microsoft.com/windows/windows-media-center/get-started/default.aspx "Windows Media Center"), [XBMC](http://xbmc.org/ "XBMC"), and [Media-Portal](http://www.team-mediaportal.com/ "Media-Portal").


 This is first post in a [series of posts](/2010/05/zotac-zbox-mini-pc-zboxhd-id11.html) related to the [Zotac ZBOX ZBOXHD-ID11](http://amzn.to/M2SUnB).


 Summary:   
 \- To enter the BIOS, cold boot and press DEL.   
 \- To select a boot device, cold boot and press F11.   
 \- To enable Aero, run the Windows Experience Index assessment.   
 \- To improve performance, install updated drivers from the hardware vendor site.   
 \- To correct HDMI audio output, install updated drivers from the hardware vendor site.   
 \- To reduce fan noise, change the BIOS temperature thresholds.   
 \- The fan is loud and the box runs hot.

After reading about the new ID11 on several news sites, I was eagerly awaiting its availability.   
 As soon as the ID11 became available, I ordered three units from [NewEgg](http://www.newegg.com/Product/Product.aspx?Item=N82E16856173005 "NewEgg").

I am currently using a two self built HTPC's, one is in a [Lian-Li media center case](/2010/01/intel-dp45sg-and-lian-li-pc-c33b-htpc.html "full size Lian-Li media center case"), and the other is an [AOpen miniPC MP945-VDR](http://usa.aopen.com/products_detail.aspx?Auno=2370 "AOpen miniPC MP945-VDR").   

I am particularly interested in the ID11 because of the small form factor, the HDMI output, and the ability to reliably play 1080p content.





There is a review of the ID11 on [AnandTech](http://www.anandtech.com/show/3702/zotacs-zbox-hdid11-review-next-gen-ion-better-worse-than-ion1 "AnandTech").

 You can watch a video, created by Zotac, of the ID11 on [YouTube](http://www.youtube.com/watch?v=W_FFK5xU3KM "here").


 The first thing I noticed when unpacking was the strange power cable.   

There is a three-pin power plug on the power brick side, and a two-pin power plug on the wall side, with a loose ground wire.

This did not seem safe to me, I contacted Zotac support, and they said they will mail me proper three-pin power cables.


 Below is a picture of the plug:   

[![](http://docs.google.com/File?id=dcmzmbww_107fdmzn6fd_b)](http://docs.google.com/File?id=dcmzmbww_107fdmzn6fd_b)



 \[Update: 18 May 2010\]    
 Zotac support sent me the correct replacement cables free of charge:   
[![](/media/2010/05/power-plug-new2.jpg?w=300)](/media/2010/05/power-plug-new5.jpg)



The ID11 comes with everything included, except for a hard drive and memory.

I installed a [80GB Intel SSD (SSDSA2MH080G2R5](http://www.intel.com/design/flash/nand/mainstream/index.htm "80GB Intel SSD")) hard drive, and a [Kingston 2GB (](http://www.valueram.com/datasheets/default.asp#DDR2 SODIMMs "Kingston 2GB SODIM RAM") [KVR800D2S5/2G](http://www.valueram.com/datasheets/default.asp#DDR2 SODIMMs "Kingston 2GB SODIM RAM")) SODIM RAM module, I ordered the [SSD](http://www.amazon.com/Intel-Mainstream-Retail-Package-SSDSA2MH080G2R5/dp/B002IJA1EG/ref=sr_1_1?ie=UTF8&s=electronics&qid=1273880908&sr=1-1 "SSD") and the [RAM](http://www.amazon.com/Kingston-ValueRAM-Notebook-KVR800D2S5-2G/dp/B00102A066/ref=sr_1_1?ie=UTF8&s=electronics&qid=1273880741&sr=8-1 "RAM") from Amazon.



Below is a picture of the case before the SSD and memory installation:

[![](http://docs.google.com/File?id=dcmzmbww_108c6hv2736_b)](http://docs.google.com/File?id=dcmzmbww_108c6hv2736_b)



Below is a picture of the case after the SSD and memory installation:

[![](http://docs.google.com/File?id=dcmzmbww_109fgn8jtdw_b)](http://docs.google.com/File?id=dcmzmbww_109fgn8jtdw_b)





 I wanted to install from a USB key, but it took me a while to figure out how to boot from the USB key, and how to enter the BIOS.   

On booting there is just a Zotac logo, no BIOS instructions or POST messages.

The instruction manual included in the box makes no mention of how to enter the BIOS.

I tried a variety of keys that normally lets you enter the BIOS; ESC, DEL, F2, F10, F12, and eventually I was able to enter the BIOS.

I changed the BIOS configuration to not show the logo, and on the next boot I could see that F11 lets me choose a boot device, and DEL enters the BIOS setup.

I later read in the Zotac support forum that DEL only works on a cold boot, that explains why it would not work for me when I just did a Ctrl-Alt-Del.

I installed Windows 7 Ultimate x64, and the install completed reasonably fast.

 The default Windows installation included drivers for all devices, and there were no unrecognized or non-functional devices listed in device manager.

Below is a picture of device manager:

[![](http://docs.google.com/File?id=dcmzmbww_110fw8pfmht_b)](http://docs.google.com/File?id=dcmzmbww_110fw8pfmht_b)

After installing Windows I ran Windows Update, the first update pulled down 4 updates totaling about 140MB, after a reboot a second update contained 26 updates totaling about 34MB.   

The Atheros wireless driver, and the NVidia graphics drivers were updated as part of the update, the NVidia driver accounts for about 130MB of the first update.

After all updates were applied I ran the Windows Experience Index assessment, and got a score of 3.4, limited by the processor score.

I noticed that after running the assessment, the UI became Aero enabled.



Below is a picture of the experience index:

[![](http://docs.google.com/File?id=dcmzmbww_111cz7mxkf6_b)](http://docs.google.com/File?id=dcmzmbww_111cz7mxkf6_b)

I noticed that the device manager listed five high definition audio devices.   

The playback devices list shows four HDMI devices, speakers, and a S/PDIF device.

I don't know why there are four HDMI devices when there is only one HDMI port.



Below is a picture of the playback devices:

[![](http://docs.google.com/File?id=dcmzmbww_112cfzqsntg_b)](http://docs.google.com/File?id=dcmzmbww_112cfzqsntg_b)

The Zotac support site [lists downloads](http://www.zotacusa.com/zotac-zboxhd-id11-u-intel-atom-d510-1-66-ghz-dual-core-all-in-one-mini-pc.html "lists several downloads") for the ID11.   

Several of the downloads failed with 503 server too busy errors, after several retries they did download, but the [ZBOXHD-ID11 INF update](http://downloads.zotac.com/mediadrivers/mb/inf_140.zip "ZBOXHD-ID11 INF update") is permanently 404.

Some of the drivers on the Zotac site were older than those installed by Windows.

The packaging did include a driver CD, a cursory inspection showed the drivers to be the same or older than those on the Zotac download site.



Below is a summary of the drivers installed by Windows, available from the Zotac support site, and available from the driver manufacturer site:

**Device Name****Windows****Zotac****Manufacturer** NVidia ION Graphics  8.17.11.9745 [8.17.11.9666](http://downloads.zotac.com/mediadrivers/mb/gt218_764.zip "8.17.11.9666")[8.17.11.9745](http://www.nvidia.com/object/win7_winvista_64bit_197.45_whql.html "8.17.11.9716") NVidia HD Audio  6.1.7600.16385 (Microsoft) [1.0.0.63](http://downloads.zotac.com/mediadrivers/mb/gt218_764.zip "1.0.0.63")[1.0.9.1](http://www.nvidia.com/object/win7_winvista_64bit_197.45_whql.html "1.0.9.1") Realtek HD Audio  6.1.7600.16385 (Microsoft) [2.40 / 6.0.1.6013](http://downloads.zotac.com/mediadrivers/mb/rtl_hda_vista3264.zip "2.40 / 6.0.1.6013")[2.47 / 6.0.1.6101](http://www.realtek.com/downloads/downloadsView.aspx?Langid=1&PNid=14&PFid=24&Level=4&Conn=3&DownTypeID=3&GetDown=false "2.47 / 6.0.1.6101") Realtek RTL8111D Ethernet  7.2.1127.2008 [7.5.730.2009](http://downloads.zotac.com/mediadrivers/mb/lan_8111c.zip "7.5.730.2009")[7.018 / 7.18.322.2010](http://www.realtek.com/downloads/downloadsView.aspx?Langid=1&PNid=13&PFid=5&Level=5&Conn=4&DownTypeID=3&GetDown=false "7.018 / 7.18.322.2010") Atheros AR9285 Wireless  8.0.0.238 [7.7.0.231](http://downloads.zotac.com/mediadrivers/mb/wifi_n_vista.zip "7.7.0.231")[9.0.0.173](http://www.opendrivers.com/driver/2120019/atheros-ar9285-wireless-network-diver-9.0.0.173-windows-7(32-64-bit)-free-download.html "9.0.0.173") \\*  Intel AHCI Storage  6.1.7600.16385 (Microsoft) [8.9.0.1023](http://downloads.zotac.com/mediadrivers/mb/Intel_AHCI.zip "8.9.0.1023")[9.6.0.1014](http://downloadcenter.intel.com/Detail_Desc.aspx?DwnldID=15251&lang=eng "9.6.0.1014")  
 \*Atheros do not make their drivers available for direct download, I used Google [to find an updated driver](http://www.google.com/search?sourceid=chrome&ie=UTF-8&q=atheros+driver+download "to find an updated driver").

Below is a picture of the device manager after the driver updates:   

[![](http://docs.google.com/File?id=dcmzmbww_113cgbjwb5b_b)](http://docs.google.com/File?id=dcmzmbww_113cgbjwb5b_b)



Below is a picture of playback devices after the driver updates:

[![](http://docs.google.com/File?id=dcmzmbww_114d7c3xsgs_b)](http://docs.google.com/File?id=dcmzmbww_114d7c3xsgs_b)


 Below is a picture of the experience index after the driver updates:   

[![](http://docs.google.com/File?id=dcmzmbww_115dzshw532_b)](http://docs.google.com/File?id=dcmzmbww_115dzshw532_b)


 Note the difference in performance after installing updated drivers:   

Graphics: 4.5 to 4.6   
 Hard Disk: 5.9 to 7.7

The ID11 is supposed to be used as a HTPC, and as such it needs to be very quiet.   

At boot the fan is quiet but during normal operation the fan gets louder, and under load the fan gets very loud. The small physical size of the fan probably contributes to the high pitch of the fan noise and makes it more noticeable.



I contacted Zotac support about the noise, and they recommended that I change the BIOS settings as follows:

\[Advanced\]\[PC Health Monitor\]\[CPUFAN TargetTemp Value\] = 50

\[Advanced\]\[PC Health Monitor\]\[CPUFAN Tolerance Value\] = 3



The default value for \[CPUFAN TargetTemp Value\] is 45C.

In the BIOS, with the CPU doing nothing, the temperature is 47C, and the fan speed is 6490RPM.



I changed the value of \[CPUFAN TargetTemp Value\] from 45C to 50C.   
 In the BIOS, with the CPU doing nothing, the temperature is 51C, and the fan speed is 5273RPM.



The fan is quieter, but not quite, and the case is getting hotter.

It seems that the fan is not very effective at cooling, and still does not run as quiet as I would like even at the higher thresholds.



Below is a picture of the PC health monitor page in the BIOS:

[![](http://docs.google.com/File?id=dcmzmbww_120c8rxpdfp_b)](http://docs.google.com/File?id=dcmzmbww_120c8rxpdfp_b)

In order to monitor the fan speed and the CPU/GPU temperature I installed [Lavalys EVEREST Ultimate Edition 5.50.2136](http://www.lavalys.com/ "Lavalys EVEREST 5.50.2136") and [SpeedFan 4.41.b9](http://www.almico.com/speedfan.php "SpeedFan 4.41.b9"), both applications detected the CPU/GPU temperatures, but neither application detected the fan speed.

I also noticed that EVEREST reported the CPU temperatures much higher compared to SpeedFan, the SpeedFan measurements seemed closer to what the BIOS reported, so it may be a problem with EVEREST.

I will contact Zotac and Lavalys support to find out if the hardware is supposed to support fan speed monitoring, and what the correct temperature measurement is supposed to be, will report back later on my findings.



Below is a picture of the GPU and CPU temperatures in EVEREST Ultimate Edition:

[![](http://docs.google.com/File?id=dcmzmbww_117dzhhbqfn_b)](http://docs.google.com/File?id=dcmzmbww_117dzhhbqfn_b)


 Below is a picture of the GPU and CPU temperatures in SpeedFan:   

[![](http://docs.google.com/File?id=dcmzmbww_118dvb99whg_b)](http://docs.google.com/File?id=dcmzmbww_118dvb99whg_b)


 \[Update: 26 May 2010\]   
[CPUID Hardware Monitor](http://www.cpuid.com/softwares/hwmonitor.html) supports the ID11 hardware.   
 The latest [Beta version of EVEREST](http://www.lavalys.com/support/downloads) supports the ID11.


 As I mentioned in the introduction, I bought three ID11's.   

Two worked fine, but the third one had a video corruption problem on the BIOS and boot screens.

I tried various outputs; DVI-D, DVI-I, VGA, and various monitors, same problem.

I filed a RMA with NewEgg, and returned the on ID11 for an exchange.



Below is picture of the screen corruption:

[![](http://docs.google.com/File?id=dcmzmbww_119gwqzfxcn_b)](http://docs.google.com/File?id=dcmzmbww_119gwqzfxcn_b)

So far I have mixed feelings; the weird power plug, the fan noise, the heat, the screen corruption, are all negatives, but the device still shows promise.

In the coming days I will connect the device to my home theater, and compare the behavior while running [Windows Media Center](http://www.microsoft.com/windows/windows-media-center/get-started/default.aspx "Windows Media Center"), [XBMC](http://xbmc.org/ "XBMC"), and [Media-Portal](http://www.team-mediaportal.com/ "Media-Portal").


