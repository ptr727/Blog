---
title: Windows 8 and Server 2012 on SuperMicro results in ACPI_BIOS_ERROR BSOD
date: '2012-07-20T00:59:01+00:00'
url: /2012/07/19/windows-8-and-server-2012-on-supermicro-results-in-acpi_bios_error-bsod/
categories:
- problem
tags:
- bios
- crash
- supermicro
- windows
post_id: '175'
---
I ran out of disk space on my development workstation, all those VM images add up. The machine has four drive bays, and all four have 3TB drives. I can replace the 3TB drives with 4TB drives, but migrating the RAID5 array will be time consuming and risky. I can add an external SAS storage enclosure, but they do not power down when the machine goes to sleep. So I looked at buying a new machine with more drive bays.

I’ve been using [DELL Precision Workstations](http://www.dell.com/us/business/p/precision-desktops) for my development machines for many years, they are fast and very reliable. My current workstation is a [T5500](http://www.dell.com/us/business/p/precision-t5500/fs), and I specifically chose the T5500 over the [T7600](http://www.dell.com/us/business/p/precision-t7600/fs) because of its features to physical size ratio. The T7600 does offer five drive bays over the T5500’s four, but if I’m going to change machines, adding only one more drive is not really worth the cost and effort.

Rather than buying a pre-configured and tested machine, I opted for the more exciting, sometimes rewarding, often frustrating, option of building my own. In order not to spend too much time on the project, I opted to use a chassis and motherboard combo, and just add peripherals. I chose the [SuperMicro SuperWorkstation 7047A-T](http://www.supermicro.com/products/system/4U/7047/SYS-7047A-T.cfm), containing the [X9DAi](http://www.supermicro.com/products/motherboard/Xeon/C600/X9DAi.cfm) motherboard. I specifically picked this model because it has eight hot-swap drive bays, is low noise, has a high efficiency PSU, and supports dual [Intel Xeon E5-2600](http://www.intel.com/content/www/us/en/processors/xeon/xeon-processor-5000-sequence.html) processors.

I used 32GB [Kingston KVR1600D3D4R11SK4/32GI](http://www.kingston.com/dataSheets/KVR1600D3D4R11SK4_32GI.pdf) memory, two [Xeon E5-2660](http://amzn.to/LvYhbX) processors, and an [NVidia Quadro 4000](http://amzn.to/Mbv3AI) graphic card.

I prepared a USB key with Windows 8 x64 Release Preview. Microsoft does provide [a tool to convert ISO images to USB keys](http://www.microsoftstore.com/store/msstore/html/pbPage.Help_Win7_usbdvd_dwnTool), but I’ve been doing this by hand since long before the tool existed, and it is really easy and ultimately quicker to update.

Mount the ISO install image as a virtual drive using [Virtual CloneDrive](http://www.slysoft.com/en/virtual-clonedrive.html). Launch an elevated (right click run as administrator) command prompt, and run:

`diskpart` `list disk
select disk [number]
clean
create partition primary
select partition 1
active
format fs=fat32 quick
assign
exit` `robocopy [virtual cd drive]:\ [usb key drive]:\ /mir`

Once the USB key has been properly formatted, you only have to repeat the robocopy steps for any new builds or bits you want to copy.

I booted from the USB key, black screen with spinning circle animation, blue screen of sad face death, and an immediate reboot.

The machine rebooted so quickly I didn’t get a chance to see what the error was.

I tried Windows Server 2012 RC, same problem. I tried later builds of Windows 8 and Server 2012 (we are part of the Windows 8 Pre-Release Program, I hope I can say that now, at some point I was not even allowed to say that, like the [Fight Club rules](http://www.imdb.com/title/tt0137523/quotes)).

I logged a support case with SuperMicro, and I [posted](http://social.technet.microsoft.com/Forums/en-US/winserver8gen/thread/8c3c3ecf-a9c9-4d36-ac64-6da7915e06c0) on the Microsoft Windows Server support forum. No reply yet from SuperMicro, no useful reply yet from the forum.

I think it is really silly that the default configuration of Windows is set to automatically reboot after a BSOD, even more so for an install situation. BSOD’s are serious, users and administrators need to know something terrible happened, even if they don’t immediately know what the error codes mean or what to do about it. I do know how to change the reboot option from inside windows, but I don’t know how to change it in the installer.

I was looking for a [BCD](http://technet.microsoft.com/en-us/library/cc721886(v=WS.10).aspx) option to disable auto-reboot, and after quite a bit of searching, I found a `BcdOSLoaderBoolean_DisableCrashAutoReboot` WMI BCD option on MSDN. After some more searching I found a `NOCRASHAUTOREBOOT ` BCDEdit option.

That was really unusually difficult to find. Try it yourself, search for “nocrashautoreboot” and [restrict the results to microsoft.com](https://www.google.com/search?q=nocrashautoreboot+site:microsoft.com), there was only one hit on a Microsoft site, in a Word DOC file. Try the search on [the rest of the web](https://www.google.com/search?q=nocrashautoreboot), and you get more hits.

Now that I knew what option to set, the rest was pretty easy. Insert the bootable USB key back in a working machine, open an elevated command prompt, and set the BCD option:

`attrib -r [usb key drive]:\boot\bcd
bcdedit -store [usb key drive]:\boot\bcd -set {default} nocrashautoreboot yes`

Start the install again, wait for the crash, and this time we can see the error is [ACPI\_BIOS\_ERROR](http://msdn.microsoft.com/en-us/library/windows/hardware/ff560114(v=vs.85).aspx):

[![ACPI_BIOS_ERROR](/media/2012/07/acpi_bios_error_thumb.jpg)](/media/2012/07/acpi_bios_error.jpg)

There are many reports on the web about ACPI\_BIOS\_ERROR and Windows 8, most resolved by updating the BIOS, but also several reports of this error with SuperMicro motherboards, and unfortunately it seems without a positive resolution.

To make sure the problem was not peripheral or hardware related, I also installed Windows 7 and Windows Server 2008 R2, both installed and ran ok.

I use a KVM switch, and as I switched back to the machine while it was applying Windows Updates, there was some screen corruption that went away after the reboot. I updated the NVidia driver and the problem has not resurfaced, this may be a driver issue, or it may be a hardware issue:

[![NVIDIA](/media/2012/07/nvidia_thumb.jpg)](/media/2012/07/nvidia.jpg)

I am very disappointed that my brand new machine can only run Windows 7 and not Windows 8. I have yet to hear from SuperMicro support, but I hope they can resolve the problem with a BIOS update before Windows 8 and Windows Server 2012 is released [in August](http://windowsteamblog.com/windows/b/bloggingwindows/archive/2012/07/09/upcoming-windows-milestones-shared-with-partners-at-wpc.aspx).
