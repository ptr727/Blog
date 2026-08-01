---
title: Windows 8 VIDEO_TDR_FAILURE Madness
date: '2012-08-23T22:09:49+00:00'
url: /2012/08/23/windows-8-video_tdr_failure-madness/
categories:
- problem
- solution
tags:
- ati
- bios
- crash
- nvidia
- supermicro
- windbg
- windows
post_id: '249'
---
I finally figured out why I kept on getting VIDEO\_TDR\_FAILURE BSOD’s when installing Windows 8 on my SuperMicro workstations. It turns out that the problem goes away when I use a PCIe slot associated with CPU #1, instead of a slot associated with CPU #2.

Some history on my adventures with [Windows 8](http://windows.microsoft.com/en-US/windows/home) and [SuperMicro SuperWorkstations](http://www.supermicro.com/products/nfo/superworkstation.cfm):  
I got [ACPI\_BIOS\_ERROR BSOD](/2012/07/19/windows-8-and-server-2012-on-supermicro-results-in-acpi_bios_error-bsod/)’s while installing Windows 8, SuperMicro [provided a Beta BIOS](/2012/07/30/supermicro-beta-bios-supports-windows-8-and-server-2012/) that resolved the problem.  
The Windows 8 [install hangs](/2012/08/05/windows-8-install-hangs-booting-from-lsi-2308-sas-controller/) if installing to a SSD drive on a [LSI 2308](http://www.lsi.com/products/storagecomponents/Pages/LSISAS2308.aspx) SAS controller, that issue is still unresolved, but can be worked around by connecting the SSD to the Intel SATA controller.  
I got [VIDEO\_TDR\_ERROR BSOD](/2012/08/06/windows-8-install-crash-with-nvidia-quadro-5000/)’s while installing Windows 8 with a NVidia Quadro 5000 graphic card, same with an ATI FirePro V7900 or a NVidia GeForce GTX 680 or an ATI HD 7970. And this post is about resolving that problem.

SuperMicro released v1.0a [BIOS updates](http://www.supermicro.com/support/bios/) for the [X9DAi](http://www.supermicro.com/products/motherboard/Xeon/C600/X9DAi.cfm) and [X9DA7](http://www.supermicro.com/products/motherboard/Xeon/C600/X9DA7.cfm) motherboards used in the [7470A-T](http://www.supermicro.com/products/system/4U/7047/SYS-7047A-T.cfm) and [7470A-73](http://www.supermicro.com/products/system/4U/7047/SYS-7047A-73.cfm) SuperWorkstations. I was hoping this will resolve the [VIDEO\_TDR\_FAILURE](http://msdn.microsoft.com/en-us/library/windows/hardware/ff557263(v=VS.85).aspx) BSOD’s, but no.

The X9DA7 BIOS updated without issue, but the X9DAi update reported an error at the end of the update process; “Error when sending Enable Message to ME”.

I contacted SuperMicro support, and they asked me to make sure that there is no jumper on JPME1. There is no mention of JPME1 in the motherboard [manual](http://www.supermicro.com/manuals/motherboard/C606_602/MNL-1275.pdf), but it is located next to JIPMB1, next to PCIe slot #1. The header had a jumper on pins 2 and 3, where the same header on the X9DA7 motherboard had a jumper between 1 and 2. I removed the jumper, and the BIOS update succeeded.

[![JPME1](/media/2012/08/jpme1_thumb.png)](/media/2012/08/jpme1.png)

Unlike the [ACPI\_BIOS\_ERROR](http://msdn.microsoft.com/en-us/library/windows/hardware/ff560114(v=vs.85).aspx) BSOD that happens during the WinPE phase of the install, the [VIDEO\_TDR\_FAILURE](http://msdn.microsoft.com/en-us/library/windows/hardware/ff557263(v=VS.85).aspx) BSOD happens on the first boot after the install, during the hardware detection and driver install phase. This means that the [technique I used to kernel debug the initial boot phase](/2012/07/20/debugging-windows-8-install-bsod/) will not work, as the second boot is using the BCD already deployed to the target hard drive. I had to modify the BCD of the already installed image, prior to the install continuing after the reboot.

I tested many permutations of graphic cards and configurations, and it quickly became very annoying to have to type my Win8 product key every single time I boot and install. To avoid this I created configuration files in the sources directory on the install media, and this bypassed the key question. You can read more about the meaning of the file contents [here](http://technet.microsoft.com/en-us/library/hh824952.aspx):

EI.cfg:

`[EditionID]
Professional
[Channel]
Retail
[VL]
0`

PID.txt:

`[PID]
Value=XXXXX-XXXXX-XXXXX-XXXXX-XXXXX`

To modify the BCD of the installed image, and be able to easily repeat the second phase of install testing, I installed a second hard drive, and deployed WinPE to the second drive. By using F11 during boot to choose the boot drive, I could select booting from the second drive at any time.

I have a variety WinPE v3 (Win7) based utility images, and I updated them to use WinPE v4 (Win8). In the process I lost the boot menu, and the first image in the menu automatically started booting. After some trial and error, I found the bootmenupolicy BCD option, and when set to legacy mode, the old style menu is back:

`bcdedit /set {default} bootmenupolicy legacy`

I installed Win8 on the primary drive, and during the reboot, instead of booting to the installed Win8 drive, I used F11 and booted to my secondary WinPE drive. From WinPE I modified the boot BCD to enable kernel debugging over the network:

`bcdedit -store c:\boot\bcd /set {default} nocrashautoreboot yes
bcdedit -store c:\boot\bcd /set {default} debugtype net
bcdedit -store c:\boot\bcd /set {default} hostip 3232235876
bcdedit -store c:\boot\bcd /set {default} port 50000
bcdedit -store c:\boot\bcd /set {default} key my.secret.debug.key
bcdedit -store c:\boot\bcd /debug {default} yes`

This is equivalent to:

`bcdedit /dbgsettings net host:192.168.1.100 port:50000 key:my.secret.debug.key`

But unlike the [dbgsettings](http://msdn.microsoft.com/en-us/library/windows/hardware/ff542187(v=vs.85).aspx) command, this allows me to specify a BCD store. Also note that the IP address is stored as a single numeric value instead of the dotted IP format.

While still in WinPE, I captured the state of the primary Win8 drive by making a drive image using Symantec Ghost, the [real Ghost](http://en.wikipedia.org/wiki/Ghost_(software)), currently sold as [Symantec Ghost Solution Suite](http://www.symantec.com/ghost-solution-suite), not the same named but volume snapshot based [Norton Ghost](http://us.norton.com/ghost/) or [Symantec System Recovery](http://www.symantec.com/system-recovery-desktop-edition). By saving a drive image, I can easily change hardware or configurations, test the install starting at the second phase, reboot to the secondary WinPE drive using F11, restore the entire drive image, and try again, while leaving the kernel debug options intact.

I tested with following hardware configurations in various permutations:

- Workstation: [SuperMicro 7047A-T](http://www.supermicro.com/products/system/4U/7047/SYS-7047A-T.cfm)
- Workstation: [SuperMicro 7047A-73](http://www.supermicro.com/products/system/4U/7047/SYS-7047A-73.cfm)
- Processor: Dual [Intel Xeon E5-2660](http://amzn.to/Qvh3Wo)
- Memory: [Kingston DDR3 32GB KVR1600D3D4R11SK4/32GI](http://www.kingston.com/dataSheets/KVR1600D3D4R11SK4_32GI.pdf)
- Memory: [Kingston DDR3L 32GB KVR13LR9D4/8HC](http://amzn.to/QvhfoC)
- Graphic card: [NVidia Quadro 5000](http://amzn.to/RrHg9L)
- Graphic card: [NVidia Quadro 4000](http://amzn.to/Q6lGGc)
- Graphic card: [NVidia GeForce GTX 680](http://amzn.to/PF9fyJ)
- Graphic card: [ATI FirePro V7900](http://amzn.to/LZehYW)
- Graphic card: [ATI Radeon HD 7970](http://amzn.to/SsswX7)
- Hard drive: [Intel 330 Series 60GB SSD SSDSC2CT060A3K5](http://amzn.to/Pf88FD)
- Hard drive: [Intel 520 Series 480GB SSD SSDSC2CW480A3K5](http://amzn.to/OK2k7c)

With the kernel debugger attached, I captured the following crash details in WinDbg for NVidia based cards:

``VIDEO_TDR_FAILURE (116)
Attempt to reset the display driver and recover from timeout failed.
Arguments:
Arg1: fffffa80211cd010, Optional pointer to internal TDR recovery context (TDR_RECOVERY_CONTEXT).
Arg2: fffff8800782d0d8, The pointer into responsible device driver module (e.g. owner tag).
Arg3: 0000000000000000, Optional error code (NTSTATUS) of the last failed operation.
Arg4: 0000000000000002, Optional internal context dependent data.Debugging Details:
------------------FAULTING_IP:
nvlddmkm+1ae0d8
fffff880`0782d0d8 4055 push rbpDEFAULT_BUCKET_ID: GRAPHICS_DRIVER_TDR_FAULTBUGCHECK_STR: 0x116PROCESS_NAME: SystemCURRENT_IRQL: 0STACK_TEXT:
fffff880`12c76078 fffff801`66fef0ea : 00000000`00000000 00000000`00000116 fffff880`12c761e0 fffff801`66f734b8 : nt!DbgBreakPointWithStatus
fffff880`12c76080 fffff801`66fee742 : 00000000`00000003 fffff880`12c761e0 fffff801`66f73e90 00000000`00000116 : nt!KiBugCheckDebugBreak+0x12
fffff880`12c760e0 fffff801`66ef4144 : fffffa80`2094b100 fffff880`021ee9c0 fffffa80`1f54e400 00000000`00000000 : nt!KeBugCheck2+0x79f
fffff880`12c76800 fffff880`04b33dcb : 00000000`00000116 fffffa80`211cd010 fffff880`0782d0d8 00000000`00000000 : nt!KeBugCheckEx+0x104
fffff880`12c76840 fffff880`04b32518 : fffff880`0782d0d8 fffffa80`211cd010 fffff880`12c76949 00000000`000000c7 : dxgkrnl!TdrBugcheckOnTimeout+0xef
fffff880`12c76880 fffff880`04a1e608 : fffffa80`211cd010 fffff880`12c76949 00000000`00000000 00000000`00000002 : dxgkrnl!TdrIsRecoveryRequired+0x168
fffff880`12c768b0 fffff880`04a4d539 : 00000000`00000000 fffff780`00000320 00000000`00000000 fffffa80`1f54e400 : dxgmms1!VidSchiReportHwHang+0x438
fffff880`12c769b0 fffff880`04a4ba49 : fffffa80`00000002 fffffa80`1f54e400 fffffa80`1f54e840 fffffa80`1f54e840 : dxgmms1!VidSchiCheckHwProgress+0xe5
fffff880`12c76a00 fffff880`04a16fe5 : ffffffff`ff676980 00000000`00000001 fffff880`12c76b69 fffffa80`1f54e400 : dxgmms1!VidSchiWaitForSchedulerEvents+0x20d
fffff880`12c76aa0 fffff880`04a4b646 : 00000000`00000000 00000000`0000000f fffffa80`1f54e400 fffffa80`1f54e400 : dxgmms1!VidSchiScheduleCommandToRun+0x289
fffff880`12c76bd0 fffff801`66e9b521 : fffffa80`1f5abb00 fffffa80`1f54e400 fffff880`03b01140 00000000`06a21e1e : dxgmms1!VidSchiWorkerThread+0xca
fffff880`12c76c10 fffff801`66ed9dd6 : fffff880`03af5180 fffffa80`1f5abb00 fffff880`03b01140 fffffa80`19aac040 : nt!PspSystemThreadStartup+0x59
fffff880`12c76c60 00000000`00000000 : fffff880`12c77000 fffff880`12c71000 00000000`00000000 00000000`00000000 : nt!KiStartSystemThread+0x16STACK_COMMAND: .bugcheck ; kbFOLLOWUP_IP:
nvlddmkm+1ae0d8
fffff880`0782d0d8 4055 push rbpSYMBOL_NAME: nvlddmkm+1ae0d8FOLLOWUP_NAME: MachineOwnerMODULE_NAME: nvlddmkmIMAGE_NAME: nvlddmkm.sysDEBUG_FLR_IMAGE_TIMESTAMP: 4fdf93d7FAILURE_BUCKET_ID: 0x116_IMAGE_nvlddmkm.sysBUCKET_ID: 0x116_IMAGE_nvlddmkm.sys ``

With the kernel debugger attached, I captured the following crash details in WinDbg for ATI based cards:

``VIDEO_TDR_FAILURE (116)
Attempt to reset the display driver and recover from timeout failed.
Arguments:
Arg1: fffffa801ed114d0, Optional pointer to internal TDR recovery context (TDR_RECOVERY_CONTEXT).
Arg2: fffff8800725cefc, The pointer into responsible device driver module (e.g. owner tag).
Arg3: 0000000000000000, Optional error code (NTSTATUS) of the last failed operation.
Arg4: 000000000000000d, Optional internal context dependent data.Debugging Details:
------------------FAULTING_IP:
atikmpag+8efc
fffff880`0725cefc 4055 push rbpDEFAULT_BUCKET_ID: GRAPHICS_DRIVER_TDR_FAULTBUGCHECK_STR: 0x116PROCESS_NAME: SystemCURRENT_IRQL: 0STACK_TEXT:
fffff880`06fa9ee8 fffff803`e6ff20ea : 00000000`00000000 00000000`00000116 fffff880`06faa050 fffff803`e6f764b8 : nt!DbgBreakPointWithStatus
fffff880`06fa9ef0 fffff803`e6ff1742 : 00000000`00000003 fffff880`06faa050 fffff803`e6f76e90 00000000`00000116 : nt!KiBugCheckDebugBreak+0x12
fffff880`06fa9f50 fffff803`e6ef7144 : fffffa80`1e2df4e0 fffff880`020b99c0 fffffa80`1d31f010 00000000`00000000 : nt!KeBugCheck2+0x79f
fffff880`06faa670 fffff880`04d31dcb : 00000000`00000116 fffffa80`1ed114d0 fffff880`0725cefc 00000000`00000000 : nt!KeBugCheckEx+0x104
fffff880`06faa6b0 fffff880`04d30548 : fffff880`0725cefc fffffa80`1ed114d0 fffff880`06faa7b9 00000000`00000180 : dxgkrnl!TdrBugcheckOnTimeout+0xef
fffff880`06faa6f0 fffff880`04c11608 : fffffa80`1ed114d0 fffff880`06faa7b9 00000000`0000000f fffffa80`1d31f8f8 : dxgkrnl!TdrIsRecoveryRequired+0x198
fffff880`06faa720 fffff880`04c459f9 : 00000000`00000001 fffff880`06faa8a0 fffff880`06faa920 00000000`00000000 : dxgmms1!VidSchiReportHwHang+0x438
fffff880`06faa820 fffff880`04c3ff72 : fffffa80`1d31f010 fffff780`00000320 fffffa80`1d31f770 fffffa80`1d31f010 : dxgmms1!VidSchWaitForCompletionEvent+0x411
fffff880`06faa8e0 fffff880`04c4206c : fffffa80`1d31f010 fffffa80`1d31f450 fffffa80`1d31f450 00000000`00000000 : dxgmms1!VidSchiWaitForEmptyHwQueue+0x9a
fffff880`06faa9d0 fffff880`04c3ea85 : 00000000`00000000 fffffa80`1d31f010 fffffa80`1d31f450 00000000`00000000 : dxgmms1!VidSchiSuspend+0x74
fffff880`06faaa00 fffff880`04c09fe5 : ffffffff`ff676980 00000000`00000001 fffff880`06faab69 fffffa80`1d31f010 : dxgmms1!VidSchiWaitForSchedulerEvents+0x249
fffff880`06faaaa0 fffff880`04c3e646 : 00000000`00000000 fffffa80`1d585660 fffffa80`1d44d7f0 fffffa80`1d31f010 : dxgmms1!VidSchiScheduleCommandToRun+0x289
fffff880`06faabd0 fffff803`e6e9e521 : fffffa80`1d6b9b00 fffffa80`1d31f010 fffff880`03932140 00000000`04d91ecb : dxgmms1!VidSchiWorkerThread+0xca
fffff880`06faac10 fffff803`e6edcdd6 : fffff880`03926180 fffffa80`1d6b9b00 fffff880`03932140 fffffa80`19ac7500 : nt!PspSystemThreadStartup+0x59
fffff880`06faac60 00000000`00000000 : fffff880`06fab000 fffff880`06fa5000 00000000`00000000 00000000`00000000 : nt!KiStartSystemThread+0x16STACK_COMMAND: .bugcheck ; kbFOLLOWUP_IP:
atikmpag+8efc
fffff880`0725cefc 4055 push rbpSYMBOL_NAME: atikmpag+8efcFOLLOWUP_NAME: MachineOwnerMODULE_NAME: atikmpagIMAGE_NAME: atikmpag.sysDEBUG_FLR_IMAGE_TIMESTAMP: 4fdf9279FAILURE_BUCKET_ID: 0x116_IMAGE_atikmpag.sysBUCKET_ID: 0x116_IMAGE_atikmpag.sys ``

This was not really helping me much, and I decided to repeat the tests but use the [checked build](http://msdn.microsoft.com/en-us/library/windows/hardware/ff543457(v=vs.85).aspx) of Windows 8 to help troubleshoot.

With the kernel debugger attached, I captured the following ASSERT during the boot:

``Windows 8 Kernel Version 9200 MP (1 procs) Checked x64
Built by: 9200.16384.amd64chk.win8_rtm.120725-1247
Machine Name:
Kernel base = 0xfffff802`0e01d000 PsLoadedModuleList = 0xfffff802`0e760ac0
System Uptime: 0 days 0:00:06.228 (checked kernels begin at 49 days)
Assertion: The BIOS has reported inconsistent resources (_CRS). Please upgrade your BIOS.
ACPI!PnpBiosGetDeviceResourceList+0x15e:
fffff880`012c3c2a cd2c int 2Ch
...
Unknown bugcheck code (0)
Unknown bugcheck description
Arguments:
Arg1: 0000000000000000
Arg2: 0000000000000000
Arg3: 0000000000000000
Arg4: 0000000000000000Debugging Details:
------------------PROCESS_NAME: SystemFAULTING_IP:
ACPI!PnpBiosGetDeviceResourceList+15e
fffff880`012c3c2a cd2c int 2ChERROR_CODE: (NTSTATUS) 0xc0000420 - An assertion failure has occurred.EXCEPTION_CODE: (NTSTATUS) 0xc0000420 - An assertion failure has occurred.DEFAULT_BUCKET_ID: WIN8_DRIVER_FAULTBUGCHECK_STR: 0x0CURRENT_IRQL: 0LOCK_ADDRESS: fffff8020e7c5d60 -- (!locks fffff8020e7c5d60)Resource @ nt!PiEngineLock (0xfffff8020e7c5d60) Exclusively owned
Threads: fffffa8019a36040-01<*>
1 total locks, 1 locks currently heldPNP_TRIAGE:
Lock address : 0xfffff8020e7c5d60
Thread Count : 1
Thread address: 0xfffffa8019a36040
Thread wait : 0x105eccd4LAST_CONTROL_TRANSFER: from fffff880012b736f to fffff880012c3c2aSTACK_TEXT:
fffff880`009b4b30 fffff880`012b736f : fffffa80`23a9e900 fffff880`012a7e01 fffff880`009b4c08 fffff880`012a7e70 : ACPI!PnpBiosGetDeviceResourceList+0x15e
fffff880`009b4bd0 fffff880`0125acba : fffffa80`23a9e900 fffffa80`19ac54c0 fffff880`012a7e70 fffffa80`1f477010 : ACPI!ACPIBusIrpQueryResourceRequirements+0x8b
fffff880`009b4c50 fffff802`0e91b6a4 : fffffa80`23a9e900 fffffa80`19ac54c0 fffff880`009b4db0 fffffa80`23a9e900 : ACPI!ACPIDispatchIrp+0x2a6
fffff880`009b4cf0 fffff802`0e91cd1b : fffffa80`23a9e900 fffff880`009b4db0 00000001`c00000bb 00000000`00000000 : nt!IopSynchronousCall+0x10c
fffff880`009b4d80 fffff802`0e915bdb : fffffa80`23a9e900 fffff880`009b4e50 fffffa80`23a4f850 00000000`0000001e : nt!PpIrpQueryResourceRequirements+0x5f
fffff880`009b4e10 fffff802`0e91748d : fffffa80`23a9b8e0 00000000`00000000 ffffffff`80000218 fffffa80`23a9b8e0 : nt!PiQueryResourceRequirements+0x47
fffff880`009b4ea0 fffff802`0e91a1f2 : fffffa80`23a9b8e0 fffffa80`23a9b8e0 00000000`00000001 00000000`00000000 : nt!PiProcessNewDeviceNode+0x159d
fffff880`009b5070 fffff802`0e08feb5 : fffffa80`19adcd20 00000000`00000000 fffff880`009b5358 00000000`00000000 : nt!PipProcessDevNodeTree+0x1fe
fffff880`009b5310 fffff802`0e08fb59 : 00000000`00000000 00000000`00000000 00000000`00000000 fffffa80`37e19cc0 : nt!PnpDeviceActionWorker+0x345
fffff880`009b53d0 fffff802`0ed4010d : 00000000`00000000 fffff8a0`00000007 fffff8a0`00f08c00 00000000`00000000 : nt!PnpRequestDeviceAction+0x2ed
fffff880`009b5420 fffff802`0ed3b39d : fffff802`0d536800 fffff802`0e7c83c0 00000000`00000006 fffff802`0d536800 : nt!IopInitializeBootDrivers+0x905
fffff880`009b5650 fffff802`0ed2deb5 : fffff802`0d536800 00000000`00000000 fffff802`0d536800 fffff802`0d51ebf0 : nt!IoInitSystem+0xb5d
fffff880`009b59b0 fffff802`0e82d013 : fffff802`0d536800 fffffa80`19a36040 00000000`00000000 fffffa80`19ab3040 : nt!Phase1InitializationDiscard+0x1899
fffff880`009b5bc0 fffff802`0e1b289e : fffff802`0d536800 fffff802`0d536800 00000000`00000000 00000000`00000000 : nt!Phase1Initialization+0x13
fffff880`009b5bf0 fffff802`0e24ef96 : fffff802`0e82d000 fffff802`0d536800 fffff802`0e6c6180 00000000`f8ffffff : nt!PspSystemThreadStartup+0x1a2
fffff880`009b5c60 00000000`00000000 : fffff880`009b6000 fffff880`009b0000 00000000`00000000 00000000`00000000 : nt!KiStartSystemThread+0x16STACK_COMMAND: kbFOLLOWUP_IP:
ACPI!PnpBiosGetDeviceResourceList+15e
fffff880`012c3c2a cd2c int 2ChSYMBOL_STACK_INDEX: 0SYMBOL_NAME: ACPI!PnpBiosGetDeviceResourceList+15eFOLLOWUP_NAME: MachineOwnerMODULE_NAME: ACPIIMAGE_NAME: ACPI.sysDEBUG_FLR_IMAGE_TIMESTAMP: 50109dd0BUCKET_ID_FUNC_OFFSET: 15eFAILURE_BUCKET_ID: 0x0_ACPI!PnpBiosGetDeviceResourceListBUCKET_ID: 0x0_ACPI!PnpBiosGetDeviceResourceList ``

This is interesting, the kernel ASSERT’s on a problem reported by the BIOS.

I contacted SuperMicro support, they said they will investigate the BIOS failure, and they suggested I try to use PCIe slot #3 instead of slot #5. The motherboard [manual](http://www.supermicro.com/manuals/motherboard/C606_602/MNL-1275.pdf) mentions that slots #1, #2, and #3 are to be used if CPU #1 is installed, and slots #4, #5, and #6 to be used only if CPU #2 is installed.

[![PCIe](/media/2012/08/pcie_thumb.png)](/media/2012/08/pcie.png)

I have both processors installed, so not using the more conveniently located slot #5 never came to mind. I moved the graphic card to CPU #1 slot #3, and voila, install succeeded and Windows 8 was up and running!

I repeated the checked build test with the graphic card in slot #3, and the same BIOS ASSERT error was reported, so the BIOS ASSERT seems to be unrelated to the ACPI\_TDR\_FAILURE error.

This was a very frustrating problem, and I still don’t understand the root cause, but I am happy to be able to finally switch both workstations to Windows 8.
