---
title: Windows 8 Install Hangs Booting From LSI 2308 SAS Controller
date: '2012-08-06T04:29:48+00:00'
url: /2012/08/05/windows-8-install-hangs-booting-from-lsi-2308-sas-controller/
categories:
- problem
tags:
- bios
- driver
- firmware
- lsi
- supermicro
- windows
post_id: '228'
---
I’ve previously posted about [problems installing Windows 8 on SuperMicro machines](/2012/07/19/windows-8-and-server-2012-on-supermicro-results-in-acpi_bios_error-bsod/), and that [SuperMicro released a Beta BIOS](/2012/07/30/supermicro-beta-bios-supports-windows-8-and-server-2012/) that solved the install problems. I’ve since run into two more problems; the install hanging when booting of the LSI 2038 SAS controller, and a BSOD when using a Quadro 5000 video card (more on that in a later post).

I have two SuperWorkstation machines, a [7047A-T](http://www.supermicro.com/products/system/4U/7047/SYS-7047A-T.cfm) using a [X9DAi](http://www.supermicro.com/products/motherboard/Xeon/C600/X9DAi.cfm) motherboard, and a [7047A-73](http://www.supermicro.com/products/system/4U/7047/SYS-7047A-73.cfm) using a [X9DA7](http://www.supermicro.com/products/motherboard/Xeon/C600/X9DA7.cfm) motherboard.

The X9DAi and X9DA7 both use the [Intel C602](http://www.intel.com/content/www/us/en/chipsets/server-chipsets/server-chipset-c600.html) chipset. The X9DAi and X9DA7 both have 2 x SATA3 ports, 4 x SATA2 ports, and 4 x SAS / SATA2 ports. The X9DA7 has an additional [LSI 2308](http://www.lsi.com/products/storagecomponents/Pages/LSISAS2308.aspx) controller with 8 x SAS2 / SATA3 ports.

On the 7047A-T / X9DAi machine, the 8 x hot-swap drive trays are connected to the 2 x SATA3, 2 x SATA2, and 4 x SAS / SATA2 ports.

On the 7047A-73 / X9DA7 machine, the 8 x hot-swap drive trays are connected to the 8 x LSI 2308 ports.

SuperMicro support provided me with Beta BIOS’s for the X9DAi and X9DA7 motherboards, this resolved the [ACPI\_BIOS\_ERROR](http://msdn.microsoft.com/en-us/library/windows/hardware/ff560114(v=vs.85).aspx), and allowed me to install Windows 8 RTM on these machines, or at least get past the BSOD while booting the install media.

I configured both machines with:

- [480GB Intel Series 520 SSD](http://amzn.to/OK2k7c) SATA3 drives
- [ATI FirePro V7900](http://amzn.to/LZehYW) graphic cards
- 32GB Kingston [KVR13LR9D4/8HC](http://amzn.to/QvhfoC) DDR3L memory
- Dual [Intel Xeon E5-2660](http://amzn.to/Qvh3Wo) processors

In the 7047A-T / X9DAi machine, I installed the SSD drive in slot-0 of the hot-swap trays, connected to SATA3 port-0. I installed Windows 8 x64 RTM without issue.

In the 7047A-73 / X9DA7 machine I installed the SSD drive in slot-0 of the hot-swap trays, connected to LSI2308 port-0. I installed Windows 8 x64 RTM, and the install hanged at 0% while copying files.

While in this state, I suspected the problem to be IO related, so I pressed Shift-F10 to open a console window, I ran diskpart, and diskpart hanged.

I downloaded the latest LSI 2308 drivers from the [Supermicro FTP site](ftp://ftp.supermicro.com/driver/SAS/LSI/2308/). I ran the install again, this time I manually loaded the drivers instead of using the in-box drivers, same problem, hang at 0%.

LSI does not make drivers directly available for HBA chips, but the [LSI SAS 9205-8e](http://www.lsi.com/channel/products/storagecomponents/Pages/LSISAS9205-8e.aspx) uses the LSI 2308, and I downloaded the drivers from LSI. They were the same version as the drivers available on the SuperMicro FTP site.

I contacted SuperMicro support, they suggested I install using the SATA3 port while they research the problem. Connecting the SSD drive to SATA3 port-0 installed fine.

I tested the same setup using Windows 7, and although Windows 7 did not include in-box drivers for the LSI 2308, after loading the drivers, Windows 7 installed fine with the SSD connected to LSI2308 port-0.

This probably indicates a Windows 8 compatibility problem with the LSI 2308 driver, or HBA firmware.

LSI HBA’s can be configured to run in Initiator Target (IT) or Integrated RAID (IR) mode. This can be changed by flashing with the appropriate IT or IR firmware. IT firmware is typically preferred where there is no need for hardware RAID and all disks will be in JBOD mode, e.g. for use with [ZFS](http://en.wikipedia.org/wiki/ZFS) or [Storage Spaces](http://technet.microsoft.com/en-us/library/hh831739).

When you flash between IT and IR mode, you need to erase the firmware before re-flashing, i.e. you cannot simply flash one mode on top of another mode. On the SuperMicro motherboards, you also need to perform the flash operation from within the EFI shell, flashing from other environments will fail. You can follow these KB’s to help with the process; [LSI 16266](http://kb.lsi.com/KnowledgebaseArticle16266.aspx), [SuperMicro 14368](http://www.supermicro.com/support/faqs/faq.cfm?faq=14368), and [SuperMicro 14151](http://www.supermicro.ws/support/faqs/faq.cfm?faq=14151). I would not recommend using SuperMicro 14368 method, as it wipes the entire firmware memory, and you will need to manually re-enter the SAS address. It is basically the difference between using “sas2flash -o -e 6” and “sas2flash -o -e 7”, see the SAS2flash reference guide for details.

[![SAS2Flash](/media/2012/08/sas2flash_thumb.png)](/media/2012/08/sas2flash.png)

The X9DA7 motherboard came with firmware version 13.0.0.56 for the LSI 2308, configured in IR mode. I updated the firmware using the firmware from the [SuperMicro FTP site](ftp://ftp.supermicro.com/driver/SAS/LSI/2308/) to 13.0.0.57 in IT mode.

The update process I followed was to boot into the EFI shell while having a USB drive attached containing the firmware update, the drive must contain the firmware, the boot BIOS, and the SAS2Flash.efi tool.

In the EFI shell run the “map” command to list the hardware and see which drive is the USB drive, mount that drive using “mount fs\[drive number\]:”, e.g. “mount fs1:”, then change to the directory to the USB drive using “fs1:”:

`map
mount fs1:
fs1:`

Then wipe the flash “sas2flash -o -e 6”, then program the new firmware and boot code “sas2flash -o -f \[firmware file\] -b \[bootcode file\]”, e.g. “sas2flsh -f 2308IT13.5FW -b mptsas2.rom”, then restart.:

`sas2flash -o -e 6
sas2flsh -f 2308IT13.5FW -b mptsas2.rom
reset`

Same problem, hang at 0%.

I again referred to the LSI site for updated firmware for the LSI 2308, and the [LSI SAS 9205-8e](http://www.lsi.com/channel/products/storagecomponents/Pages/LSISAS9205-8e.aspx) and [LSI SAS 9207-8e](http://www.lsi.com/products/storagecomponents/Pages/LSISAS9207-8e.aspx) includes firmware P14 version 14.0.0.0, a major revision upgrade from version 13.0.0.57 from the SuperMicro site.

The P14 firmware packages does not include the EFI version of SAS2Flash, but a bit of search engine exploration showed it is still included in the [P13 packages](http://www.lsi.com/downloads/Public/Host%20Bus%20Adapters/Host%20Bus%20Adapters%20Common%20Files/SAS_SATA_6G_P13/Installer_P13_for_UEFI.zip).

I am not quite brave enough to flash to this version yet, as a failed flash will require a hardware swap. I’ll continue running this machine with the SSD connected to the SATA3 port.

At this point I am waiting for SuperMicro support to get back to me with a solution, or confirming that I can flash the P14 firmware and see if that resolves the issue.
