---
title: Intel DG33TL motherboard
date: '2008-04-02T04:13:00+00:00'
url: /2008/04/01/intel-dg33tl-motherboard/
categories:
- review
tags:
- intel
post_id: '77'
---
This article was originally posted [here](http://www.insanegenius.com/dg33tl/).

### Introduction:



After my bad experience with the Abit F-I90HD motherboards, read about it  
[here](http://www.blogger.com/f-i90hd/), I purchased two Intel DG33TL motherboards.

Although these boards do not have HDMI onboard, they do have HDCP compliant DVI,  
and by adding an ADD2 HDMI board you get HDMI and audio over HDMI.





### The Good:




- Onboard HDCP compliant DVI.

- Intel ADD2 HDMI card support.

- Vista installed very fast and with no problems.

- The driver DVD that came with the board installs all devices that is not  
installed by Vista.

It even lets you set your username and password and will automatically  
reboot and continue the installation after every driver.




### The Bad:




- The DVD installs the 5.x version audio driver, works fine, yet the Intel  
website lists the latest driver as 6.x.

However the 6.x driver fails to install, reporting that the hardware is not  
supported.

Intel support says the 6.x driver installed fine on their test system, and  
they recommended I wait for a new driver to be released, or I exchange the  
boards.

I find it hard to believe Intel support, and I believe the website is  
incorrectly listing the 6.x driver as compatible with this board.

- Intel Desktop Utilities sporadically reports 0.000V warning messages,  
and lists one source for a voltage reading as unknown.

Intel support told me that Desktop Utilities is not supported on the 3x  
series boards, yet the DVD that came with the board installs Desktop  
Utilities, and the Desktop Utilities download page lists support for the 3x  
series boards.

After pointing this out to Intel support, they recommended I reinstall the  
BIOS and the Desktop Utilities, made no difference.

A new 0262 version BIOS was released that lists some corrections with the  
Media Engine, but this made no difference.

Waiting for Intel support to respond, or for a new version of Desktop  
Utilities.

- I purchased the  
[  
Prolink PV-CH7315](http://www.prolink.com.tw/style/content/CN-08-2cp2/product_detail.asp?lang=2&customer_id=1470&name_id=36165&rid=17885&id=82053) ADD2 card, but connecting the HDMI does indicate that  
there is a HDMI signal, but no picture on the television.

The Intel GMA control application does list three outputs, monitor,  
television, and digital television, only monitor / VGA works.

- The Intel 15.7.3 and 15.8 igdkmd32.sys and igdkmd64.sys GMA drivers and Vista SP1 are incompatible,  
the machine blue screen crashes when going to sleep.

I tested this with Vista Ultimate x86 being upgraded to SP1, and a clean  
install of Vista Ultimate x64 with integrated SP1.

I notified Microsoft of the issue during the Vista SP1 Beta, was told Intel  
would fix it before SP1 ships, yet the problem still exists even after SP1  
shipped and after the 15.8 GMA drivers shipped. The issue now appears to be  
documented in  
[this KB  
article](http://support.microsoft.com/Default.aspx?kbid=948343).






### The Outcome:




- I have been contacted by several readers that experience similar issues,  
I urge you to contact Intel support and notify Intel of the problems.

- After several exchanges with Intel support I am still waiting for a new  
version of Desktop Utilities to solve the 0.000V alerts.

- Intel removed the 6.x audio driver from the download site, and updated  
the 5.x driver, seems the 6.x driver was not supposed to be on the site.

- I have not been able to get HDMI working with the Prolink card.

- Waiting for new GMA drivers that do not bluescreen with Vista SP1, the  
issue is now documented in  
[this KB  
article](http://support.microsoft.com/Default.aspx?kbid=948343).






### Links:




- [Pieter Viljoen's homepage](http://www.insanegenius.com/).

-   
[Intel DG33TL  
motherboard](http://www.intel.com/products/motherboard/DG33TL/index.htm).

-   
[  
Prolink PV-CH7315 ADD2 card](http://www.prolink.com.tw/style/content/CN-08-2cp2/product_detail.asp?lang=2&customer_id=1470&name_id=36165&rid=17885&id=82053).

-   
[Abit F-I90HD motherboard experience](http://www.blogger.com/f-i90hd/).

-   
["G965 with Prolink HDMI ADD2" post on AVSForum.](http://www.avsforum.com/avs-vb/showthread.php?t=782711)





