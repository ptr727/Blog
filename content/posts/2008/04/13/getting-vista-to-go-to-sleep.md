---
title: Getting Vista to go to sleep
date: '2008-04-13T20:03:00+00:00'
url: /2008/04/13/getting-vista-to-go-to-sleep/
categories:
- solution
tags:
- ati
- intel
- microsoft
- motherboard
- sp1
- windows
post_id: '79'
---
I noted my troubles with the Intel GMA drivers, the [Intel DG33TL](http://www.intel.com/products/motherboard/DG33TL/index.htm) motherboard, and Vista SP1 blue screen crashing in [my earlier post](/2008/04/intel-dg33tl-motherboard.html).

Since I was running the 15.8 version of the Intel GMA drivers, and [Microsoft KB948343](http://support.microsoft.com/Default.aspx?kbid=948343) indicates that, based on the driver version numbers, these newer drivers should not be affected by SP1, yet the crash details were clearly the same, and no new driver was forthcoming to correct the blue screen crash, I decided to take the GMA drivers out of the picture.

I am currently using an ATI HD 26000 XT card in my HTPC, and this is a great card. I looked for the same model, the one I was using is from [VisionTek](http://www.visiontek.com/products/cards/retail/2600XT_PCIe_512.html), but I found a [Sapphire](http://www.sapphiretech.com/us/products/products_overview.php?gpid=179&grp=3) brand card for significantly less. I am actually happier with the Sapphire compared with the VisionTek, the VisionTek fan was really loud, and since I was using it in my HTPC, I ended up buying a [Zalman VF900-Cu](http://www.zalman.co.kr/ENG/product/Product_Read.asp?idx=144) replacement fan for the VisionTek card. The Sapphire card has no problem with a noisy fan.

I installed the ATI card, installed the drivers, and put the machine to sleep. This is where the GMA drivers would normally crash. This time there was no crash, but the machine also immediately woke up again, I could not get it to stay in sleep mode.

At this point I had had enough of the DG33TL board; it had given me more trouble than I was willing to put up with and I wanted a replacement board. Since I already had the machine open, while replacing the VGA card, I wanted a new board now, which meant instead of ordering online and waiting a few days I had to take a trip to my local Fry’s.

I knew my in store choices would be limited, so I did some research and selected a few models from Asus, Gigabyte, and Intel, with the primary requirement being ICH9 support so that I would not lose the RAID-0 configuration of my drives, and the motherboard swap would not require an OS reinstall. My first choice would have been a [Gigabyte GA-G33-DS3R](http://www.gigabyte.com.tw/Products/Motherboard/Products_Overview.aspx?ProductID=2535), unfortunately, as I suspected, it turns out that of all the options I was hoping for the only board that came close was an [Intel DQ35JO](http://www.intel.com/products/motherboard/DQ35JO/index.htm).

Of the three boards on the shelf, all of them had been returns and were resealed, so this was even more of a risk, but they were marked down a few dollars so that did make me feel better, and I could always return the board.

The DQ35JO is very similar to the DG33TL. The DQ35JO is from the Executive series, and the DG33TL is from the Media series. The DQ35JO has no multichannel audio, but does have TPM and AMT. The component layouts are almost identical.

I replaced the board, powered on, the POST screen came up and then nothing. On reading the Intel support documents they recommended a BIOS reset. I removed the battery, waited a few minutes, replaced the battery and rebooted. This time the POST completed, and I could boot. I assume that since the board had been used, and I just replaced the memory and CPU, that this may have caused the initial boot failure. Before booting into Vista I first booted to my DOS bootable USB key and updated the BIOS to the latest version, then reset the BIOS configuration to defaults, and again made all the required changes, most importantly to restore the RAID drive configuration.

I booted into Vista Ultimate x64, waited a few minutes for the new drivers to load, and eventually the keyboard started working and I could login. The ATI control center application complained that there was no ATI driver installed, so I reinstalled the ATI driver, rebooted, and this time everything seemed fine. Not quite, Windows told me the hardware had changed and I had to reactivate. Activating over the internet failed, and I had to activate over the phone, that worked. I also noticed that Windows Update wasn’t working, the KB article for the error code told me to check the PC time. Since I had reset the BIOS without resetting the time, the time was off by years, on correcting the time WU started working again.

Now for the ultimate test, can the machine go to sleep? I press the sleep button and the machine sleeps, I touch the keyboard and the machine wakes up. I leave the machine idle for an hour, it goes to sleep, I touch the keyboard and the machine wakes up. Success!

There is one thing that is still not 100%, and this seems to be a problem on both the DG33TL and the DQ35JO; the case power light is not always on. E.g. after removing mains power and powering on the case power light will be on and stay on until the first sleep, and then the power light will turn off, and even resuming from sleep or rebooting will not turn the light back on.

Maybe I should have been more patient and ordered the Gigabyte GA-G33-DS3R instead, but for now I am happy.


