---
title: SuperMicro Beta BIOS supports Windows 8 and Server 2012
date: '2012-07-30T20:15:32+00:00'
url: /2012/07/30/supermicro-beta-bios-supports-windows-8-and-server-2012/
categories:
- problem
- review
- solution
tags:
- ati
- bios
- firepro
- nvidia
- quadro
- supermicro
- windows
post_id: '207'
---
In a [previous post](/2012/07/19/windows-8-and-server-2012-on-supermicro-results-in-acpi_bios_error-bsod/) I reported that my [SuperMicro SuperWorkstation 7047A-T](http://www.supermicro.com/products/system/4U/7047/SYS-7047A-T.cfm) failed to install Windows 8 or Windows Server 2012 due to a [ACPI\_BIOS\_ERROR](http://msdn.microsoft.com/en-us/library/windows/hardware/ff560114(v=vs.85).aspx). I contacted SuperMicro support, and I was informed that new BIOS releases are on their way that will support Windows 8 and Server 2012.

This morning I received an email from SuperMicro, with a new Beta BIOS for the [X9DAi motherboard](http://www.supermicro.com/products/motherboard/Xeon/C600/X9DAi.cfm) used in the 7047A-T. The new BIOS allowed me to install Windows 8 and Server 2012.

I used a DOS bootable USB key, and installed the new BIOS.

The 7047A-T has USB ports on the back and on the front of the case. The ports on the front are all USB3, and it is not possible to boot from these ports, at least I have not yet found a configuration that allows booting from USB3 ports. I tried using USB2 keys and, my newest [Kingston DataTraveler HyperX 3.0](http://amzn.to/MXjv4Y) super fast USB3 keys, the BIOS does not list any boot devices in these USB3 ports. To boot from USB you have to plug the USB key in one of the rear USB2 ports.

The new BIOS version is “1.0 beta”, compilation date “7/23/2012”. The BIOS screen looks like the more modern AMI EFI BIOS’s I’ve seen in other devices, i.e. the thin font instead of the classic console font.

[![BIOS.Beta](/media/2012/07/bios-beta_thumb.jpg)](/media/2012/07/bios-beta_.jpg)

I performed a “Restore Optimized Defaults”, and then went through the options to see what has changed and what is new.

The \[Advanced\] \[Chipset Configuration\] \[North Bridge\] \[IOH Configuration\] now sets all PCIe busses to GEN3, the old BIOS defaulted to GEN2.

The \[Advanced\] \[SATA Configuration\] now enabled hot plug on all ports, the old BIOS defaulted to hot plug disabled.

The \[Advanced\] \[Boot Feature\] ads a new power configuration item called “EuP”. This seems to be related to [EU Directive 2005/32/EC](http://europa.eu/legislation_summaries/other/l32037_en.htm):

> EU Directive 2005/32/EC enacted by the European Union member countries dictates that after January 1, 2010, no computer or other energy using product (EuP) sold in the member countries may dissipate more than 1 Watt in the standby (S5) state.

I measured the power utilization, and the machine uses 2W when powered off, 140W at idle in Windows 8 desktop, and 7W while sleeping.

I updated my Windows 8 USB key to the latest build (I have access to), booted from the USB key, and installed Windows 8 without any major issues.

I had swapped the [NVidia Quadro 4000](http://amzn.to/Q6lGGc) for a faster [ATI FirePro V7900](http://amzn.to/LZehYW). The v1.0 BIOS worked fine with the Quadro 4000, but after installing the V7900, the screen powered on and Windows 7 started booting before I had a chance to see the BIOS screen. After installing the new Beta BIOS, the V7900 works as expected and I can see the BIOS screen during POST.

This is a note for ATI; please make sure your VGA driver install UI fits on a 640x480 display. When I swapped the Quadro 4000 for the V7900, and rebooted into Windows 7, I booted into a 640x480 16 color screen. Imagine my frustration trying to guess which button has focus when you can only see the top half of the ATI driver installer.

Windows 8 automatically installed drivers for the V7900.

The only driver Windows 8 did not automatically install is the C600 chipset SAS driver. I installed the [Intel Rapid Storage Technology Enterprise](http://www.intel.com/p/en_US/support/highlights/chpsts/rste) (RSTe) drivers, and that solved that problem.

While running Windows 7 on this machine, and running the Windows Experience Index Assessment, the test would always crash. The same test in Windows 8 completed successfully.

[![Win8.EI](/media/2012/07/win8-ei_thumb.png)](/media/2012/07/win8-ei_.png)

I found the 2D and 3D results to be disappointing, and I tried to replace the “ATI FirePro V (FireGL V) Graphics Adapter (Microsoft Corporation - WDDM v1.20)” driver with the [ATI Windows 8 Consumer Preview](http://support.amd.com/us/kbarticles/Pages/Windows8ConsumerPreviewDrivers.aspx) driver. Although the release notes indicate that the V7900 is supported, the driver installation failed with an unsupported hardware error. I’ll have to wait for newer Windows 8 drivers from ATI to see if the test scores improve.

I’m quite happy that I can use my new machines with Windows 8.

I just wish SuperMicro solved the BIOS incompatibility problems long ago, after all, it has been almost two years since the Windows 8 pre-release program started, and almost a year since the release of the public developer preview.
