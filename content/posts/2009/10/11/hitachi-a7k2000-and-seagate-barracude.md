---
title: Hitachi Ultrastar and Seagate Barracude LP 2TB drives
date: '2009-10-11T22:54:00+00:00'
url: /2009/10/11/hitachi-a7k2000-and-seagate-barracude/
categories:
- review
- storage
tags:
- amazon
- areca
- chenbro
- hitachi
- lsi
- nas
- seagate
- wd
post_id: '94'
---
In my [previous post](/2009/09/western-digital-re4-gp-2tb-drive.html "previous post") I talked about Western Digital RE4-GP 2TB drive problems.



In this post I present my test results for 2TB drives from Seagate and Hitachi.

The test setup is the same as for the RE4-GP testing, except that I only tested 4 drives from each manufacturer.



Unlike the enterprise class WD RE4-GP and Hitachi Ultrastar A7K2000 drives, the Seagate Barracuda LP drive is a desktop drive.

The equivalent should have been a Seagate Constellation ES drive, but as far as I know the 2TB drives are not yet available.





To summarize:

The Hitachi A7K2000 drives performed without issue on all three controllers, the Seagate Barracuda LP drive failed to work with the Adaptec controller.

The Hitachi Ultrastar A7K2000 outperformed the Seagate Barracuda LP drive, but this was not really a surprise given the drive specs.

The Areca ARC1680 controller produced the best and most reliable results, the Adaptec was close, but given the overheating problem, it is not reliable unless additional cooling is added.





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

\- Data drives, 4 x 2TB [Hitachi Ultrastar A7K2000 HUA722020ALA330](http://www.hgst.com/portal/site/en/products/ultrastar/A7K2000/ "Hitachi A7K2000 HUA722020ALA330") drives, firmware JKAOA20N

1 x hot spare, 3 x drive RAID5 4TB, configured as GPT partitions, dynamic disks, and simple volumes

\- Data drives, 4 x 2TB [Seagate Barracuda LP ST32000542AS](http://www.seagate.com/www/en-us/products/desktops/barracuda_hard_drives/barracuda_lp/ "Seagate Barracuda LP ST32000542AS") drives, firmware CC32

1 x hot spare, 3 x drive RAID5 4TB, configured as GPT partitions, dynamic disks, and simple volumes







I tested the drives as shipped, with no jumpers, running at SATA-II / 3Gb/s speeds.





Adaptec 51245, SATA-II / 3Gb/s:

As in my previous test I had to use an extra fan to keep the Adaptec card from overheating.

The Hitachi drives had no problems.

The Hitachi drives completed initialization in 16 hours.

The Seagate drives would not show up on the system, I tried different ports, resets, cable swaps, no go.



Adaptec, RAID5, Hitachi:

[![](http://docs.google.com/File?id=dcmzmbww_23hhrp6hc2_b)](http://docs.google.com/File?id=dcmzmbww_23hhrp6hc2_b)



Adaptec, RAID5, WD:

[![](http://docs.google.com/File?id=dcmzmbww_24gjf8gtcr_b)](http://docs.google.com/File?id=dcmzmbww_24gjf8gtcr_b)







Areca ARC1680ix-12, SATA-II / 3Gb/s:

The Areca had not problems with the Hitachi or Seagate drives.

The Hitachi drives completed initialization in 40 hours.

The Seagate drives completed initialization in 49 hours.

The array initialization time of the Areca is significantly longer compared to Adaptec or LSI.



Areca, RAID5, Hitachi:

[![](http://docs.google.com/File?id=dcmzmbww_25dj3jfcck_b)](http://docs.google.com/File?id=dcmzmbww_25dj3jfcck_b)



Areaca, RAID5, Seagate:

[![](http://docs.google.com/File?id=dcmzmbww_26ghxs8ddp_b)](http://docs.google.com/File?id=dcmzmbww_26ghxs8ddp_b)



Areca, RAID5, WD:

[![](http://docs.google.com/File?id=dcmzmbww_27fqhnwgfh_b)](http://docs.google.com/File?id=dcmzmbww_27fqhnwgfh_b)







LSI 8888ELP and Chenbro CK12803, SATA-II / 3Gb/s:

The Hitachi drives reported a few "Invalid field in CDB" errors with, but it did not appear to affect the operation of the array.

The Hitachi drives completed initialization in 4 hours.

The Seagate drives reported lots of "Invalid field in CDB" and "Power on, reset, or bus device reset occurred" errors, but it did not appear to affect the operation of the array.

The Seagate drives made clicking sounds when they powered on, and occasionally during normal operation.

The Seagate drives completed initialization in 4 hours.



LSI, RAID5, Hitachi:

[![](http://docs.google.com/File?id=dcmzmbww_28ctr9nsg8_b)](http://docs.google.com/File?id=dcmzmbww_28ctr9nsg8_b)



LSI, RAID5, Seagate:

[![](http://docs.google.com/File?id=dcmzmbww_29qggsx6wc_b)](http://docs.google.com/File?id=dcmzmbww_29qggsx6wc_b)



LSI, RAID5, WD:

[![](http://docs.google.com/File?id=dcmzmbww_30fn8qzmd9_b)](http://docs.google.com/File?id=dcmzmbww_30fn8qzmd9_b)







The Hitachi A7K2000 drives performed without issue on all three controllers, the Seagate Barracuda LP drive failed to work with the Adaptec controller.

The Hitachi A7K2000 outperformed the Seagate Barracuda LP drive, but this was not really a surprise given the drive specs.

The Areca ARC1680 controller produced the best and most reliable results, the Adaptec was close, but given the overheating problem, it is not reliable unless additional cooling is added.



I will be scaling my test up from 4 to 12 Hitachi drives, using the Areca controller, and I will expand the Areca cache from 512MB to 2GB.


