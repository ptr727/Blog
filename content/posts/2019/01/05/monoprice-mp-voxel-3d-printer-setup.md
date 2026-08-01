---
title: Monoprice MP Voxel 3D Printer Setup
date: '2019-01-05T19:07:03+00:00'
url: /2019/01/05/monoprice-mp-voxel-3d-printer-setup/
categories:
- review
tags:
- 3dprint
- flashforge
- monoprice
- polarcloud
- voxel
post_id: '1795'
cover:
  alt: voxel
  image: /media/2019/01/voxel.png
---
_\[Update\]_ _After using the printer for about two weeks, I returned it to Monoprice for a refund. I would suggest you stay away and look elsewhere, or wait until Monoprice addresses the serious issues; Polar Cloud disconnects while printing, IO timeout error breaks camera function, and the deal breaker is hangs during printing, with the touch screen unresponsive and the extruder and print bed heater still on._

I've been looking for a new 3D printer to use at home, and I just installed and configured my new [Monoprice Voxel 3D Printer](https://www.monoprice.com/product?p_id=33820).

I bought my first 3D printer, a [Makerbot Replicator 2](https://www.makerbot.com/), for our office new-tech lab in 2012. It was a shared printer, hard to maintain, and eventually printed to death.

A few months ago I found the [HobbyKing Turnigy Mini Fabrikator V2](https://hobbyking.com/en_us/mini-fabrikator-v2-3d-printer-us-plug.html) on sale at a great price. It sat unopened, until a few weeks ago, when I wanted to use it to print Christmas ornaments for the kids to decorate. What a disappointment, difficult to configure, flimsy construction, and during the first print the filament guide adapter broke away from the print head, impossible to fix without ordering replacement parts, I just trashed it.

In search of a replacement, I decided to look for something the kids could use with minimal (wishful thinking at this age) help from me. That meant an enclosed printer and iPad capable software. A semi-helpful [Reddit post](https://www.reddit.com/r/3Dprinting/comments/a2krm9/purchase_advice_megathread_what_to_buy_who_to_buy/) made it clear to me that the best printers, and best value for money printers, are not really kid friendly, but it did point me in the right direction. To [Polar Cloud](https://polar3d.com/), and to [FlashForge](http://www.flashforge.com/), and eventually the [Monoprice Voxel](https://www.monoprice.com/product?p_id=33820), that is a cheaper Monoprice branded [FlashForge Adventurer 3](http://www.flashforge.com/3d-printer/adventurer-3/).


{{< gallery cols="1" >}}  
{{< figure src="/media/2019/01/voxel.png" title="voxel" alt="voxel" >}}

{{< figure src="/media/2019/01/makerbot%5Freplicator2%5Fmain%5F0.png" title="makerbot\_replicator2\_main\_0" alt="makerbot\_replicator2\_main\_0" >}}

{{< figure src="/media/2019/01/fabrikator.png" title="fabrikator" alt="fabrikator" >}}

{{< figure src="/media/2019/01/adventurer.png" title="adventurer" alt="adventurer" >}}  
{{< /gallery >}}  

Unboxing and setting up was easy, and in a few minutes I printed the sample cube that is included on the 8GB internal memory. The unit is quiet while printing, but the continuous high pitched fan noise is annoying.


{{< gallery cols="1" >}}  
{{< figure src="/media/2019/01/20190105%5F001612746%5Fios.jpg" title="20190105\_001612746\_ios" alt="20190105\_001612746\_ios" >}}

{{< figure src="/media/2019/01/20190105%5F001722196%5Fios.jpg" title="20190105\_001722196\_ios" alt="20190105\_001722196\_ios" >}}

{{< figure src="/media/2019/01/20190105%5F001730856%5Fios.jpg" title="20190105\_001730856\_ios" alt="20190105\_001730856\_ios" >}}

{{< figure src="/media/2019/01/20190105%5F002233767%5Fios.jpg" title="20190105\_002233767\_ios" alt="20190105\_002233767\_ios" >}}

{{< figure src="/media/2019/01/20190105%5F002401718%5Fios.jpg" title="20190105\_002401718\_ios" alt="20190105\_002401718\_ios" >}}

{{< figure src="/media/2019/01/20190105%5F003331814%5Fios.jpg" title="20190105\_003331814\_ios" alt="20190105\_003331814\_ios" >}}

{{< figure src="/media/2019/01/20190105%5F003813828%5Fios.jpg" title="20190105\_003813828\_ios" alt="20190105\_003813828\_ios" >}}

{{< figure src="/media/2019/01/20190105%5F150706047%5Fios.jpg" title="20190105\_150706047\_ios" alt="20190105\_150706047\_ios" >}}  
{{< /gallery >}}  

Next I configured WiFi and connected to Polar Cloud, this is where things started going wrong. The manual that is included in the box is not complete, and I found an [updated manual](https://downloads.monoprice.com/files/manuals/33820_Manual_181025.pdf) and [instructional video](https://monopricesupport.kayako.com/article/262-mp-voxel-3d-printer-introduction-setup) on the Monoprice site. The steps to connect to WiFi is easy, but I found that using the touch screen was very difficult. The WiFi password is hidden with asterisks, and the touch screen has a tendency to not respond, or to pick multiple characters, or the wrong character. Since I could not see the password, it took several frustrating tries to get the right password entered. This experience could easily be improved by simply not hiding the password, or allowing configuration and control via mobile app.

The Monoprice site lists the FlashPrint software as version 3.23.2, while the version on the [FlashForge](http://www.flashforge.com/support-center/flashprint-support/#) site is 3.25.1, so naturally I installed the latest software from FlashForge. Mistake, I cloud not select the Voxel as printer, and it turns out that "FlashPrint-MP" is for Monoprice printers, and "FlashPrint" is for FlashForge printers. So back to installing [FlashPrint-MP 3.23.2](https://downloads.monoprice.com/files/software/33820_Software_Win64_v3.23.2_181120.zip). The software is typical modeling and slicing, and allowed me to connect to the printer over the network.


{{< gallery cols="2" >}}  
{{< figure src="/media/2019/01/annotation-2019-01-05-092019.png" title="annotation 2019-01-05 092019" alt="annotation 2019-01-05 092019" >}}

{{< figure src="/media/2019/01/2019-01-05.png" title="2019-01-05" alt="2019-01-05" >}}  
{{< /gallery >}}  

I followed the [instructions](https://www.youtube.com/watch?v=vtxg0rr71UM) to connect the Voxel to Polar Cloud, but I kept getting an error about my printer MAC address already belonging to a different user. I found a [KB article](https://polar3d.freshdesk.com/support/solutions/articles/9000154751--printer-already-exists-with-the-mac-and-it-is-not-owned-by-the-supplied-account-) that instructed me to hard reset the printer, and I dreaded having to reenter my WiFi password. The article mentioned that this problem will be addressed in a future firmware update, so I tried that first. I could not find any downloadable firmware, but I found that updating from the printer pulled new firmware over the internet. After a reboot, no more error, and I was connected to Polar Cloud.

I encountered some IO timeout errors being displayed on the printer, I thought it was related to Polar Cloud, but I later encountered them during normal operation navigating the camera configuration menus. I suspect it is related the camera, since I lost the camera view on Polar Cloud as soon as I got this error. I hope this gets fixed in a firmware update.

My first cloud print after the firmware update did not go so well, the head scratched the print plate. I did find other users (Amazon reviews) complaining of the same scratching problem, I suspect the firmware update may have reset the calibration. After re-leveling, cloud prints worked fine again, but this should never have happened.


{{< gallery cols="1" >}}  
{{< figure src="/media/2019/01/20190105%5F025724484%5Fios.jpg" title="20190105\_025724484\_ios" alt="20190105\_025724484\_ios" >}}

{{< figure src="/media/2019/01/20190105%5F030958782%5Fios.jpg" title="20190105\_030958782\_ios" alt="20190105\_030958782\_ios" >}}

{{< figure src="/media/2019/01/20190105%5F041921727%5Fios.jpg" title="20190105\_041921727\_ios" alt="20190105\_041921727\_ios" >}}

{{< figure src="/media/2019/01/20190105%5F042806476%5Fios.jpg" title="20190105\_042806476\_ios" alt="20190105\_042806476\_ios" >}}

{{< figure src="/media/2019/01/20190105%5F180310557%5Fios.jpg" title="20190105\_180310557\_ios" alt="20190105\_180310557\_ios" >}}  
{{< /gallery >}}  

Printing from Polar Cloud is super simple, select a community model, upload your own model, and print. Job is sliced per selected options, and sent to the printer, it is a nice touch to have the printer camera images be displayed on the website while printing. I did notice that the time estimate displayed on the printer keeps changing, e.g. Polar Cloud listed the time remaining as 2 hours 26 minutes, Voxel 2 minutes ... 11 minutes ... 45 minutes. I suspect the job is spooled such that the printer only knows what is left in the buffer vs. the complete job.


{{< gallery cols="1" >}}  
{{< figure src="/media/2019/01/annotation-2019-01-05-094932.png" title="annotation 2019-01-05 094932" alt="annotation 2019-01-05 094932" >}}

{{< figure src="/media/2019/01/annotation-2019-01-05-094902.png" title="annotation 2019-01-05 094902" alt="annotation 2019-01-05 094902" >}}

{{< figure src="/media/2019/01/annotation-2019-01-05-100630.png" title="annotation 2019-01-05 100630" alt="annotation 2019-01-05 100630" >}}  
{{< /gallery >}}  

In closing, so far, I think it is a great printer for the money, and I hope future firmware updates improves the experience.

Bad:

- Instructions are incomplete and all over the place.
- Poor touchscreen experience, difficult to press, double press, wrong press.
- Difficult WiFi setup, password is hidden, and combined with wrong key presses results in frustration.
- Scratched build plate, re-leveling seems to be required after a firmware update.
- Out of the box Polar Cloud would not connect due to duplicate MAC address, requires firmware update to fix.
- Sporadic IO timeout errors, suspect related to camera.
- High pitched fan noise (I may try to mod this by replacing the fan or adding sound dampening material).
- Hangs during printing, with the extruder and build plate heaters still on, and touchscreen unresponsive.

Good:

- Low price
- Enclosed
- Easy to use
- Cloud print

For others setting up this printer, I would recommend the following steps:

1. Ignore the manual in the box, [download](https://downloads.monoprice.com/files/manuals/33820_Manual_181025.pdf) the manual from Monoprice.
1. [Connect](https://monopricesupport.kayako.com/article/262-mp-voxel-3d-printer-introduction-setup) to WiFi, I suggest using the eraser part of a pencil to touch the screen while entering the password, this helps prevent typing mistakes.
1. Update the firmware from the tools menu.
1. Re-level the build plate.
1. [Connect](https://www.youtube.com/watch?v=vtxg0rr71UM) to Polar Cloud.
1. Print, do not print until after re-leveling.

Next steps for me is to find suitable software for the kids to use for modeling on their iPads.
