---
title: Western Digital RE4-GP 2TB Drive Problems
date: '2009-09-22T02:16:00+00:00'
url: /2009/09/21/western-digital-re4-gp-2tb-drive/
categories:
- storage
tags:
- amazon
- areca
- chenbro
- lsi
- nas
- wd
post_id: '93'
---
In my [previous](/2009/06/power-saving-sata-raid-controller.html "previous") [two](/2009/07/power-saving-raid-controller-continued.html "two") posts I described my research into the power saving features of various enterprise class RAID controllers.

In this post I detail the results of my testing of the Western Digital RE4-GP enterprise class "green" drives when used with hardware RAID controllers from Adaptec, Areca, and LSI.



To summarize, the RE4-GP drive fails with a variety of problems, Adaptec, Areca, and LSI acknowledge the problem and lays blame on WD, yet WD insists there are no known problems with the RE4-GP drives.





Test hardware:

\- [Windows Server 2008 R2 x64 Enterprise](http://www.microsoft.com/windowsserver2008/en/us/default.aspx "Windows Server 2008 R2 x64 Enterprise")

\- [Intel S5000PSL motherboard](http://www.intel.com/Products/Server/Motherboards/S5000PSL/S5000PSL-overview.htm "Intel S5000PSL motherboard"), dual Xeon E5450, 32GB RAM, firmware BIOS-98 BMC-65 FRUSDR-48

\- [Adaptec 51245 RAID controller](http://www.adaptec.com/en-US/products/Controllers/Hardware/sas/performance/SAS-51245/ "Adaptec 51245 RAID controller"), firmware 17517, driver 5.2.0.17517

\- [Areca ARC1680ix-12 RAID controller](http://www.areca.com.tw/products/pcietosas1680series.htm "Areca ARC1680ix-16 RAID controller"), firmware 1.47, driver 6.20.00.16\_80819

\- [LSI 8888ELP RAID controller](http://www.lsi.com/storage_home/products_home/internal_raid/megaraid_sas/megaraid_sas_8888elp/ "LSI 8888ELP RAID controller"), firmware 11.0.1-0017 (APP-1.40.62-0665), driver 4.16.0.64

\- [Chenbro CK12803](http://usa.chenbro.com/corporatesite/products_detail.php?sku=73 "Chenbro CK12803") 28-port SAS expander, firmware AA11



Drive setup:

\- Boot drive, 1 x 1TB [WD Caviar Black WD1001FALS](http://www.westerndigital.com/en/products/products.asp?driveid=488 "WD Caviar Black WD1001FALS"), firmware 05.00K05

Simple volume, connected to onboard Intel ICH10R controller running in RAID mode  

\- Data drives, 10 x 2TB [WD RE4-GP WD2002FYPS](http://www.wdc.com/en/products/products.asp?driveid=610 "WD RE4-GP WD2002FYPS") drives, firmware 04.05G04

1 x hot spare, 3 x drive RAID5 4TB, 6 x drive RAID6 8TB, configured as GPT partitions, dynamic disks, and simple volumes  





I started testing the drives as shipped, with no jumpers, running at SATA-II / 3Gb/s speeds.





Adaptec 51245, SATA-II / 3Gb/s:

The Adaptec card has 3 x internal SFF-8087 ports and 1 x external SFF-8088 port, supporting 12 internal drives.

The Adaptec card had immediate problems with the RE4-GP drives, in the ASM utility the drives would randomly drop out and in.

I could not complete testing.



Areca ARC1680ix-16, SATA-II / 3Gb/s:

The Areca card has 3 x internal SFF-8087 ports and 1 x external SFF-8088 port, supporting 12 internal drives.

Unlike the LSI and Adaptec cards that require locally installed management software, the Areca card is completely managed through a web interface from an embedded Ethernet port.

The Areca card allowed the RAID volumes to be created, but during initialization at around 7% the web interface stopped responding, requiring a cold reset.

I could not complete testing.



LSI 8888ELP and Chenbro CK12803, SATA-II / 3Gb/s:

The LSI card has 2 x internal SFF-8087 ports and 2 x external SFF-8088 port, supporting 8 internal drives.

Since I needed to host 10 drives, I used the Chenbro 28 port SAS expander.

The 8888ELP support page only lists the v3 series drivers, while W2K8R2 ships with the v4 series drivers, so I used the latest v4 drivers from the new 6Gb/s LSI cards.

The LSI and Chenbro allowed the volumes to be created, but during initialization 4 drives dropped out, and initialization failed.

I could not complete testing.





I contacted WD, Areca, Adaptec, and LSI support with my findings.





WD support said there is nothing wrong with the RE4-GP, and that they are not aware of any problems with any RAID controllers.

When I insisted that there must be something wrong, they suggested I try to force the drives to SATA-I / 1.5Gb/s speed and see if that helps.

I tested at SATA-I / 1.5Gb/s speed, and achieved some success, but I still insisted that WD acknowledge the problem.

The case was escalated to WD engineering, and I am still waiting for an update.



Adaptec support acknowledged a problem with RE4-GP drives when used with high port count controllers, and that a card hardware fix is being worked on.

I asked if the fix will be firmware or hardware, and was told hardware, and that the card will have to be swapped, but the timeframe is unknown.



Areca support acknowledged a problem between the Intel IOP348 controller and RE4-GP drives, and that Intel and WD are aware of the problem, and that running the drives at SATA-I / 1.5Gb/s speed resolves the problem.

I asked if a fix to run at SATA-II / 3Gb/s speeds will be made available, I was told this will not be possible without hardware changes, and no fix is planned.



LSI support acknowledged a problem with RE4-GP drives, and that they have multiple cases open with WD, and that my best option is to use a different drive, or to contact WD support.

I asked if a fix will become available, they said that it is unlikely that a firmware update would be able to resolve the problem, and that WD would need to provide a fix.





This is rather disappointing, WD advertises the RE4-GP as an enterprise class drive, yet 3/3 of the enterprise class RAID controllers I tested failed with the RE4-GP, and all three vendors blame WD, yet WD insists there is nothing wrong with the RE4-GP.







I continued testing, this time with the SATA-I / 1.5Gb/s jumper set.





Adaptec 51245, SATA-I / 1.5Gb/s:

This time the Adaptec card had no problems seeing the arrays, although some of the drives continue to report link errors.

A much bigger problem was that the controller and battery was overheating, the controller running at 103C / 217F.

In order to continue my testing I had to install an extra chassis fan to provide additional ventilation over the card.

The Adaptec and LSI have passive cooling, where in contrast the Areca has active cooling and only ran at around 51C / 124F.

The Areca and LSI batteries are off-board, and although a bit inconvenient to mount, they did not overheat like the Adaptec.

Initialization completed in 22 hours, compared to 52 hours for Areca and 8 hours for LSI.

The controller supports power management, and drives are spun down when not in use.



3 x Drive RAID5 4TB performance:

[![](http://docs.google.com/File?id=dcmzmbww_18f4mjmshk_b)](http://docs.google.com/File?id=dcmzmbww_18f4mjmshk_b "3 x Drive RAID5 4TB Performance:")



6 x Drive RAID6 8TB Performance:

[![](http://docs.google.com/File?id=dcmzmbww_19f7nks4ft_b)](http://docs.google.com/File?id=dcmzmbww_19f7nks4ft_b "6 x Drive RAID6 8TB Performance:")





Areca ARC1680ix-16, SATA-I / 1.5Gb/s:

This time the Areca card had no problems initializing the arrays.

Initialization completed in 52 hours, much longer compared to 22 hours for Adaptec and 8 hours for LSI.

Areca support said initialization time depends on the drive speed and controller load, and that the RE4-GP drives are known to be slow.

The controller supports power management, and drives are spun down when not in use.



3 x Drive RAID5 4TB performance:

[![](http://docs.google.com/File?id=dcmzmbww_16d8bzhjgn_b)](http://docs.google.com/File?id=dcmzmbww_16d8bzhjgn_b "3 x Drive RAID5 4TB Performance:")



6 x Drive RAID6 8TB Performance:  

[![](http://docs.google.com/File?id=dcmzmbww_17cn95hsc8_b)](http://docs.google.com/File?id=dcmzmbww_17cn95hsc8_b "6 x Drive RAID6 8TB Performance:")





LSI 8888ELP and Chenbro CK12803, SATA-I / 1.5Gb/s:

This time only 2 drives dropped out, one out of each array, and initialization completed after I forced the drives back online.

Initialization completed in 8 hours, much quicker compared to 22 hours for Adaptec and 52 hours for Areca.

The controller only supports power management on unassigned drives, there is no support for spinning down configured but not in use drives.  



3 x Drive RAID5 4TB performance:

[![](http://docs.google.com/File?id=dcmzmbww_20cbjs24gf_b)](http://docs.google.com/File?id=dcmzmbww_20cbjs24gf_b)



6 x Drive RAID6 8TB Performance:

[![](http://docs.google.com/File?id=dcmzmbww_21gqzhbcvg_b)](http://docs.google.com/File?id=dcmzmbww_21gqzhbcvg_b "6 x Drive RAID6 8TB Performance:")







Although all three cards produced results when the RE4-GP drives were forced to SATA-I / 1.5Gb/s speeds, the results still show that the drives are unreliable.



The RE4-GP drive fails with a variety of problems, Adaptec, Areca, and LSI acknowledge the problem and lays blame on WD, yet WD insists there are no known problems with the RE4 drives-GP.



There are alternative low power drives available from Seagate and Hitachi.

I still haven't forgiven Seagate for the endless troubles they caused with ES.2 drives and Intel IOP348 based controllers, and, like WD, also denying any problems with the drives, yet eventually releasing two [firmware updates](http://ask.adaptec.com/scripts/adaptec_tic.cfg/php.exe/enduser/std_adp.php?p_faqid=15324&p_created=1211278235 "firmware update") for the ES.2 drives.

I've always had good service from Hitachi drives, so maybe I'll give the new [Hitachi A7K2000](http://www.hitachigst.com/portal/site/en/products/ultrastar/A7K2000/ "Hitachi A7K2000") drives a run.



One thing is for sure, I will definately be returning the RE4-GP drives.





\[Update: 11 October 2009\]

I [tested](/2009/10/hitachi-a7k2000-and-seagate-barracude.html) the Seagate Barracuda LP and Hitachi Ultrastar 2TB drives.



\[Update: 24 October 2009\]

[3Ware](http://www.3ware.com/) [published a KB (15573) documenting problems with RE4-GP drives](http://3ware.com/KB/article.aspx?id=15573).

3Ware [published a KB (15592) with the new WD firmware for the RE4-GP drives](http://www.3ware.com/kb/article.aspx?id=15592).

Adaptec [published a KB (16913) documenting problems with RE4-GP drives](http://ask.adaptec.com/scripts/adaptec_tic.cfg/php.exe/enduser/std_adp.php?p_faqid=16913&p_created=1253288580&p_sid=VL1iBdLj&p_accessibility=0&p_redirect=&p_lva=14947&p_sp=cF9zcmNoPTEmcF9zb3J0X2J5PWRmbHQ6MSZwX2dyaWRzb3J0PSZwX3Jvd19jbnQ9MSwxJnBfcHJvZHM9MCZwX2NhdHM9MCZwX3B2PSZwX2N2PSZwX3NlYXJjaF90eXBlPWFuc3dlcnMuc2VhcmNoX25sJnBfcGFnZT0xJnBfc2VhcmNoX3RleHQ9MTY5MTM*&p_li=&p_topview=1).

WD support still has not responded to my request for the firmware.


