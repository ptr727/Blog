---
title: Dyslexic Intel RSTe Driver
date: '2012-09-03T16:45:04+00:00'
url: /2012/09/03/dyslexic-intel-rste-driver/
categories:
- problem
tags:
- intel
- supermicro
- windows
post_id: '263'
---
I encounter [one problem after another](/tag/supermicro/) running Windows 8 and Server 2012 on the dual Xeon E5 [Intel C600](http://www.intel.com/content/www/us/en/chipsets/server-chipsets/server-chipset-c600.html) chipset based SuperMicro [7047A-T](http://www.supermicro.com/products/system/4U/7047/SYS-7047A-T.cfm) and [7047A-73](http://www.supermicro.com/products/system/4U/7047/SYS-7047A-73.cfm) SuperWorkstation machines. I will say that this is really not representative of my Windows 8 experience in general, as all other machines I installed on worked fine with the in-box drivers.

The C602 includes the Intel Storage Controller Unit (SCU) SATA / SAS controller. Windows 8 and Server 2012 do not include in-box drivers for the SCU. The SCU drivers are part of the Intel [Rapid Storage Technology Enterprise](http://www.intel.com/p/en_US/support/highlights/chpsts/rste) (RSTe) driver set. Note that the RSTe and RST drivers are different and not compatible with one another. When you install the full RSTe package, it includes SCU drivers for the SCU RAID controller, AHCI drivers for the SATA controller, and the Windows RST management application.

A clean install of Windows 8 will use the in-box drivers for the SATA controller. In the image below you can see the [Intel 520 Series 480GB SSD](http://amzn.to/OK2k7c) drive show up with the correct model number:

[![Device.Manager.Win8](/media/2012/09/device-manager-win8_thumb.png)](/media/2012/09/device-manager-win8_.png)

After installing RSTe ([3.2.0.1132](ftp://ftp.supermicro.com/driver/SCU/Intel_PCH_SCU_Romley/Windows/3.2.0.1132/), [3.2.0.1134](http://downloadcenter.intel.com/Detail_Desc.aspx?ProductID=3449&DwnldID=21752&lang=eng&iid=dc_rss)), the 4TB Hitachi drives attached to the SCU show up, but the model numbers of the drives, including the SSD drive attached to the SATA port, are now messed up:

[![Device.Manager.RSTe](/media/2012/09/device-manager-rste_thumb.png)](/media/2012/09/device-manager-rste_.png)

The drive hardware identifiers are correct, but the friendly name is not:

[![Intel.SSD.Hardware](/media/2012/09/intel-ssd_-hardware_thumb.png)](/media/2012/09/intel-ssd_-hardware.png)[![Intel.SSD.Friendly](/media/2012/09/intel-ssd_-friendly_thumb.png)](/media/2012/09/intel-ssd_-friendly.png)

It appears that the text BYTE’s are WORD swapped, i.e. ABCD becomes BADC.

The driver is also not functional, attempting to create a storage spaces pool using the Hitachi drives hangs forever, with no drive activity, requiring a hard power cycle:

[![Storage.Pool](/media/2012/09/storage-pool_thumb.png)](/media/2012/09/storage-pool_.png)

And lastly, the [Intel SSD Toolbox](http://www.intel.com/support/go/ssdtoolbox/index.htm) [3.0.3](http://downloadcenter.intel.com/Detail_Desc.aspx?agr=Y&DwnldID=18455) is not compatible with Windows 8:

[![SSD.Toolbox](/media/2012/09/ssd-toolbox_thumb.png)](/media/2012/09/ssd-toolbox.png)

The clock is ticking for Windows Server 2012 (4 September, 1 day left) and Windows 8 (26 October, 7 weeks left) general availability, I can only hope compatible drivers, firmware, and utilities are forthcoming.

_\[Update: 4 September 2012\]_
SuperMicro [posted updated RSTe drivers](ftp://ftp.supermicro.com/driver/SCU/Intel_PCH_SCU_Romley/Management/3.5.0.1101/) (package v3.5.0.1101, driver v3.5.0.1096). This driver set resolves the hang during storage space creation, but the drive names are still messed up.
