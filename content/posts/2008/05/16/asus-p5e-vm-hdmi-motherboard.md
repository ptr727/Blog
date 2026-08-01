---
title: Asus P5E-VM HDMI motherboard
date: '2008-05-16T23:31:00+00:00'
url: /2008/05/16/asus-p5e-vm-hdmi-motherboard/
categories:
- review
tags:
- asus
post_id: '80'
---
In the ongoing saga to get a motherboard that works well with Vista SP1 going to sleep, I have yet again switched motherboards.

As previously posted I’ve tried an [Intel DG33TL](/2008/04/intel-dg33tl-motherboard.html) board, and an [Intel DQ35JO](/2008/04/getting-vista-to-go-to-sleep.html), and I am now using an [Asus P5E-VM HDMI](http://www.asus.com/products.aspx?l1=3&l2=11&l3=584&l4=0&model=1912&modelmenu=1) board.

I was happy with the Intel DQ35JO, but this did not last very long. A few days after posting I found my machine with garbage characters on the screen, requiring a cold boot. Intel support was of little help, but a few days later I updated the firmware on my ThinkPad T61, and I read that one of the fixes in the firmware was to fix garbage characters on the screen when sleeping on resuming from sleep caused by the AMT feature. The DQ35JO board also has AMT, so maybe that was the same problem.

Not wanting to have more trouble I returned the Intel DQ35JO board to Fry’s, and I ordered an Asus P5E-VM HDMI board from Amazon. There are three variants of the P5E-VM board; the SE, DO, and HDMI, but only the HDMI variant was immediately available on Amazon. I would not be using the HDMI output since I was going to use the ATI HD 2600 XT card, but it does not hurt to have onboard HDMI available.

Installing the board was simple, the RAID still worked, and Vista Ultimate x64 booted without issues. The only missing driver was for the Realtek audio. I tried the driver from the Asus site but that failed to install, rather disappointing. Asus support told me to use the driver from the Realtek site, and that worked fine.

I again noticed that the power LED was intermittently not working, this being the third board with this problem, I was now convinced it was a problem with the actual LED. I contact Antec support, and a few days later I received a new power LED free of charge. I installed it, and problem solved.

Asus provides several utilities to monitor and adjust the performance of their boards, i.e. AI Suite and PC Probe II. I’ll spare you the details but these utilities are of very poor quality, failing to install, failing to uninstall, crashing on start, crashing on sleep, crashing on resume from sleep, and worse when uninstalled they still leave crap behind. I had to delete two tasks from the task scheduler, delete several files and folders, and manually delete several COM objects from the registry. Avoid these tools.

One feature I really like about the Asus board is the BIOS upgrade feature. Just copy the firmware to a USB key, plug the USB key in, boot, enter the BIOS, select the upgrade option, pick the file, and upgrade, so simple.

This time round I waited a few weeks before posting, and I am very happy with the Asus P5E-VM board.


