---
title: Recovering the Firmware on a Supermicro BPN-SAS3-846EL1 Backplane
date: '2020-02-02T21:26:32+00:00'
url: /2020/02/02/recovering-the-firmware-on-a-supermicro-bpn-sas3-846el1-backplane/
categories:
- problem
- solution
- storage
tags:
- firmware
- lsi
- sas
- supermicro
post_id: '1935'
cover:
  alt: IMG_5934
  image: /media/2020/01/img_5934.jpg
---
In a [previous](/2020/01/10/unraid-repeat-parity-errors-on-reboot/) adventure I replaced an Adaptec HBA with a LSI SAS3 HBA, and the chassis drive bay LED's stopped working. I suspect the LSI card does not play nice with the SGPIO sideband controller, and I decided to replace the chassis with one similar to my SC846 chassis, where the LSI card and drive bay LED's do work fine.

What should have been a simple replacement turned into quite a recovery operation.

Since I now had SAS3 HBA's in both my servers, I really wanted to get SAS3 backplanes, but I did not want to pay SAS3 chassis prices. I found a refurbished [SuperChassis 846E16-R1200B](https://www.supermicro.com/en/products/chassis/4U/846/SC846E16-R1200B) chassis and two refurbished [Supermicro BPN-SAS3-846EL1](https://www.supermicro.com/manuals/other/BPN-SAS3-846EL.pdf) backplanes on eBay. The one SAS3 backplane would replace the SAS2 backplane in my existing SC846, and the second SAS3 backplane would replace the SAS2 backplane in the newly purchased SC846. The combination of the 24 bay 4U chassis with a SAS2 backplane and a replacement SAS3 backplane is much cheaper compared to any native SAS3 chassis I could find.

I do understand that using SATA3 drives on a SAS3 backplane will not perform like SAS3 drives, but with multipath the aggregate throughput can still outperform SAS2.

I received my chassis and my backplanes. The chassis was clean but a bit dinged in one corner, and the expanders were clean, but the metal frames showing a little rust. I had no idea how old the firmware on the backplanes were, so I contacted Supermicro support to ask for the current firmware. After asking for my serial numbers, Supermicro sent me the latest firmware for my hardware. The firmware update instructions were included in the "ReleaseNote.txt" file that came with the firmware.

I removed the motherboard from the old chassis and installed it in the new SC846. I removed the SAS2 backplane, and installed the SAS3 backplane in its place. The power cable layout on the SAS3 backplane is a bit different, and I had to use a few molex power [splitters](https://amzn.to/3beMRgu) to extend the power cables to reach the power plugs on the SAS3 backplane. The [standard](https://store.supermicro.com/4u-5u-rail-kit-mcp-290-00057-0n.html) rails are too long to fit in my [rack](https://www.middleatlantic.com/products/racks-enclosures/slide-out-racks/wr-series-roll-out-rotating-rack/wr-24-32.aspx), and the [short](https://store.supermicro.com/2u-5u-rail-kit-mcp-290-00058-0n.html) rails are too short for the chassis, so as I again used short outer rails and standard inner rails.


{{< gallery cols="3" >}}  
{{< figure src="/media/2020/01/img%5F5893.jpg?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2020/01/img%5F5894.jpg?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2020/01/img%5F5895.jpg?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2020/01/img%5F5896.jpg?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2020/01/img%5F5897.jpg?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2020/01/img%5F5898.jpg?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2020/01/img%5F5899.jpg?w=768" alt="" caption="" >}}  
![](/media/2020/02/img_5973.jpg?w=1024)  
![](/media/2020/02/img_5980.jpg?w=768)  
{{< /gallery >}}  

I powered the machine up through remote IPMI KVM, all looked good, and I booted into my Ubuntu Server USB stick so I could SSH into the box, and update the firmware.

The instructions from "ReleaseNote.txt" say:

```
How to Flash Firmware
-------------------------
Under Linux/Windows Environment to use CLIXTL (ver.6.00)
1. use "CLIXTL -l" to show SAS addresses
1. use "CLIXTL -f all  -d " to update firmware
1. use "CLIXTL -f 3  -d  -r" to update MFG and reset expander

example:
CLIXTL -l
CLIXTL -f all -t 500304800000007F -d SAS3-EXPFW_66.16.11.00.fw
CLIXTL -f 3 -t 500304800000007F -d BPN-SAS3-846EL-PRI_16_11.bin -r
```

The existing firmware on the expanders were v66.06.01.02 and MFG v06.02, while the new firmware was v66.16.11.00 and MFG v16.11.

```
Firmware Update History
-------------------------
1. migrate expander firmware to phase 16
1. enhance TMP, VOL, FAN, and PWS status in SES pages
1. present version information of current running firmware
1. Dynamic SES page element presentation
1. move BMC IP to SCSI network inquiry
1. support I2C R/W as slave to let BMC to identify platforms
1. redundant side has sensor information
1. firmware rewrite and optimization
```

I did the following:

```
$ sudo ./CLIXTL -i -t 5003048001B24DBF
================================================================================
COMMAND-LINE INTERFACE XTOOL
version 6.10.C
Supermicro Computer ,Inc.
================================================================================
UNIT SPECIFIC INFORMATION:
SAS ADDRESS - 5003048001B24DBF
ENCLOSURE ID - 5003048001B24DBF
ENCLOSURE INFORMATION:
PLATFORM NAME - SMC846ELSAS3P
SERIAL NUMBER -
VENDOR ID - LSI
PRODUCT ID - SAS3x40
VERSION INFORMATION:
FLASH REGION 0 - 66.06.01.02
FLASH REGION 1 - 66.06.01.02
FLASH REGION 2 - 66.06.01.02
FLASH REGION 3 - 06.02
DEVICE INFORMATION:
DEVICE NAME - /dev/sg0
BMC IP - NULL

$ sudo ./CLIXTL -f all -t 5003048001B24DBF -d SAS3-EXPFW_66.16.11.00.fw
================================================================================
COMMAND-LINE INTERFACE XTOOL
version 6.10.C
Supermicro Computer ,Inc.
================================================================================
Firmware Region 0 - Finished
Firmware Region 1 - Finished
Firmware Region 2 - Finished
Please reset expander to activate

pieter@ubuntuusb:~/SAS3$ sudo ./CLIXTL -f 3 -t 5003048001B24DBF -d BPN-SAS3-846EL-PRI_16_11.bin -r
================================================================================
COMMAND-LINE INTERFACE XTOOL
version 6.10.C
Supermicro Computer ,Inc.
================================================================================
Error, incompatible file type or directory
```

And the expander dropped and never came back up.

```
$ sudo ./CLIXTL -l
================================================================================
COMMAND-LINE INTERFACE XTOOL
version 6.10.C
Supermicro Computer ,Inc.
================================================================================
Error, no enclosure has been found
```

I can hear the comments now, why risk updating the firmware if it is not broken, true, but I didn't know if it would work, and I'd rather start fresh. Do also note that I did the update on my secondary server, my primary server is still running unmodified, so no interruption of home service or work experiments.

I still had the second SAS3 backplane, so I replace the "bricked" one, leaving the firmware as is, and brought my Unraid server back up, all appeared fine. At least I had two working servers, giving me time to try and recover the backplane.

I sent Supermicro support an email asking for help, but since it was weekend I had to wait, so I did my own research. I found a forum [post](https://hardforum.com/threads/did-i-brick-one-of-my-bpn-sas2-846el1-backplanes.1929384/#post-1043477103) of a user that recovered a "bricked" SAS2 expander via the factory serial port, and I decided to give it a try.


{{< gallery cols="3" >}}  
{{< figure src="/media/2020/01/annotation-2020-01-22-192504.png" alt="" caption="" >}}  
{{< figure src="/media/2020/01/img%5F5932.jpg" alt="" caption="" >}}  
{{< figure src="/media/2020/01/img%5F5933.jpg" alt="" caption="" >}}  
{{< figure src="/media/2020/01/img%5F5934.jpg" alt="" caption="" >}}  
{{< /gallery >}}  

I used my Arduino programming FTDI USB RS232 [adapter](https://amzn.to/3aAz83i), and the pin connections for PRI-SDB / 8 are:

```
PRI-SDB : 1 : TX  -> RS232 : RX
PRI-SDB : 2 : GND -> RS232 : GND
PRI-SDB : 3 : RX  -> RS232 : TX
```

The current [XTools](https://www.supermicro.com/wftp/utility/ExpanderXtools_Lite/) v6.10.C CLI does not include COM support, at least none that I could find in the documentation or CLI help, so I used the older v1.4 version.

```
>g3Xflash.exe -s com4 get avail
********************************************************************************
g3Xflash
LSI SAS Expander Flash Utility
Version: 2.0.0.0
Copyright (c) 2013 LSI Corporation. All rights reserved.
********************************************************************************
Initializing Interface.....
Expander: Unknown (SAS_3X_40)
1) Unknown (SAS_3X_40) (00000000:00000000)
```

Good sign, the COM port worked, and the expander hardware was detected, but did not have an address.

I flashed the firmware and the MFG data:

```
>g3Xflash.exe -s com4 down fw SAS3-EXPFW_66.16.11.00.fw 0
********************************************************************************
g3Xflash
LSI SAS Expander Flash Utility
Version: 2.0.0.0
Copyright (c) 2013 LSI Corporation. All rights reserved.
********************************************************************************
Initializing Interface..
Expander: Unknown (SAS_3X_40)
Expander Validation: Passed
Checksum: Passed
Target Firmware Region: 00
Current Version: 255.255.255.255
Replacement Version: 66.16.11.00
Image Validation: Passed
Pre-Validation of image is successful.
Are you sure to download file to expander?(y/n):y
Downloading File...........................................................................Download Complete.
Post-validating........................................................Post-Validation of image is successful.
Download Successful.

>g3Xflash.exe -s com4 down mfg BPN-SAS3-846EL-PRI_16_11.bin 3
********************************************************************************
g3Xflash
LSI SAS Expander Flash Utility
Version: 2.0.0.0
Copyright (c) 2013 LSI Corporation. All rights reserved.
********************************************************************************
Initializing Interface.....
Expander: Unknown (SAS_3X_40)
Image Validation: Passed
Checksum: Passed
Reading MFG version from flash...Unable to retrieve version.
Replacement Version: 10.0b
Pre-Validation of image is successful.
Are you sure to download file to expander?(y/n):y
Downloading File............................Download Complete.
Post-validating.........Post-Validation of image is successful.
Download Successful.
```

I reset the expander, the LED's now did a test pattern that they did not do before, and things looked good:

```
>g3Xflash.exe -s com4 reset exp
********************************************************************************
g3Xflash
LSI SAS Expander Flash Utility
Version: 2.0.0.0
Copyright (c) 2013 LSI Corporation. All rights reserved.
********************************************************************************
Initializing Interface....................
Expander: SC846-P (SAS_3X_40)
Are you sure you want to reset Expander?(y/n):y
Expander reset successful.

>g3Xflash.exe -s com4 get avail
********************************************************************************
g3Xflash
LSI SAS Expander Flash Utility
Version: 2.0.0.0
Copyright (c) 2013 LSI Corporation. All rights reserved.
********************************************************************************
Initializing Interface..
INFO: Bootstrap is not present on board.
Downloading the Bootstrap
................................................................Download Bootstrap Complete.
..................
Expander: SC846-P (SAS_3X_40)
1) SC846-P (SAS_3X_40) (50030480:0000007F)

>g3Xflash.exe -s com4 get exp

********************************************************************************
g3Xflash
LSI SAS Expander Flash Utility
Version: 2.0.0.0
Copyright (c) 2013 LSI Corporation. All rights reserved.
********************************************************************************
Initializing Interface....................
Expander: SC846-P (SAS_3X_40)
Reading the expander information................
Expander: SC846-P (SAS_3X_40) C1
SAS Address: 50030480:0000007F
Enclosure Logical Id: 50030480:0000007F
Component Identifier: 0x0232
Component Revision: 0x03

>g3Xflash.exe -s com4 get ver 0
********************************************************************************
g3Xflash
LSI SAS Expander Flash Utility
Version: 2.0.0.0
Copyright (c) 2013 LSI Corporation. All rights reserved.
********************************************************************************
Initializing Interface....................
Expander: SC846-P (SAS_3X_40)
Firmware Region Version: 66.16.11.00
```

Everything looked good, except the SAS address defaulted to 50030480:0000007F.

The firmware "ReleaseNote.txt" file states that the v6.00 CLIXTL tool can change the SAS address, but the only version on the Supermicro site is the  v6.10.C version, that does not support changing the SAS address.

```
How to modify SAS address
-------------------------
Under Linux/Windows Environment to use CLIXTL (ver.6.00)
1. use "CLIXTL -l" to show SAS addresses
1. use "CLIXTL -s  -t  -r" to change SAS address and reset expander

example:
CLIXTL -l
CLIXTL -s 500304801234567F -t 500304800000007F -r
```

The v1.4 GUI does support changing the SAS address. It appears that the GUI dynamically creates a MFG image (I could see a BIN file get created in the directory), but after it changed the address, the backplane was back to a borked state, and I had to repeat the recovery process.


{{< gallery cols="3" >}}  
{{< figure src="/media/2020/01/2020-01-20-2.png" alt="" caption="" >}}  
{{< figure src="/media/2020/01/2020-01-20.png" alt="" caption="" >}}  
{{< /gallery >}}  

By the next week I heard back from Supermicro, and they confirmed the instructions from the "ReleaseNote.txt" file were wrong, and I should use the instructions from the "Command-line Xtool 6.10.C.pdf" file.

```
Wrong, will bork the MFG data:
CLIXTL -f 3 -t 5003048001B24DBF -d BPN-SAS3-846EL-PRI_16_11.bin -r

Right:
CLIXTL -c -t 5003048001B24DBF -d BPN-SAS3-846EL-PRI_16_11.bin

Better, update firmware and MFG and retain settings:
CLIXTL -a usc -t 5003048001B24DBF -d ~/
```

I used the all in one update method on the server that was running the original firmware backplane, and it updated without issue:

```
# ./CLIXTL -a usc -t 500304800914683F -d ~/CLIXTL6.10.C_Linux/
================================================================================
COMMAND-LINE INTERFACE XTOOL
version 6.10.C
Supermicro Computer ,Inc.
================================================================================
Firmware Region 0 - Finished
Firmware Region 1 - Finished
Firmware Region 2 - Finished
MFG page Region 3 - Finished
New configuration is uploaded successfully
Please reset expander to activate

[Reboot]

# ./CLIXTL -i -t 500304800914683F
================================================================================
COMMAND-LINE INTERFACE XTOOL
version 6.10.C
Supermicro Computer ,Inc.
================================================================================
UNIT SPECIFIC INFORMATION:
SAS ADDRESS - 500304800914683F
ENCLOSURE ID - 500304800914683F
ENCLOSURE INFORMATION:
PLATFORM NAME - SMC846ELSAS3P
SERIAL NUMBER -
VENDOR ID - LSI
PRODUCT ID - SAS3x40
VERSION INFORMATION:
FLASH REGION 0 - 66.16.11.00
FLASH REGION 1 - 66.16.11.00
FLASH REGION 2 - 66.16.11.00
FLASH REGION 3 - 16.11
DEVICE INFORMATION:
DEVICE NAME - /dev/sg11
BMC IP - NULL
```

I now had one perfectly updated backplane preserving all the original MFG data, and one backplane with default MFG data. I wanted to apply the MFG data from the good backplane to the default values backplane.

I downloaded the firmware and manufacturing data from the good backplane using the v1.4 tools (not supported in current CLIXTL):

```
./g3Xflash -i get avail
./g3Xflash -y -i 500304800914683F up fw up_fw_loader_0.fw 0
./g3Xflash -y -i 500304800914683F up fw up_fw_loader_1.fw 1
./g3Xflash -y -i 500304800914683F up fw up_fw_loader_2.fw 2
./g3Xflash -y -i 500304800914683F up mfg up_mfg_loader.bin 3
```

The downloaded files are larger and are padded with 0xFF or 0x00. I trimmed the MFG file to the right size, and modified the SAS address in two places:

{{< figure src="/media/2020/01/2020-01-22-3.png" alt="2020-01-22 (3)" caption="2020-01-22 (3)" >}}

I tried to uploaded the modified MFG data:

```
>g3Xflash.exe -y -s com4 down mfg BPN-SAS3-846EL-PRI_16_11.bin 3
********************************************************************************
g3Xflash
LSI SAS Expander Flash Utility
Version: 2.0.0.0
Copyright (c) 2013 LSI Corporation. All rights reserved.
********************************************************************************
Initializing Interface.....
Expander: Unknown (SAS_3X_40)
Image Validation: Passed
Checksum: Failed
```

But the tool complains that the checksum failed. From the file diff we can see that there is more than just the SAS address that change, I assume some sort of checksum calculation that goes with the data.

The v1.4 g3xFlash CLI help does reference XML options for converting between binary and XML MFG formats, but no instructions on how to use it. Like the serial recovery procedure these tools are probably for internal use only, and I could find no public references.

```
>g3Xflash.exe -h
********************************************************************************
    g3Xflash
    LSI SAS Expander Flash Utility
    Version: 2.0.0.0
    Copyright (c) 2013 LSI Corporation.  All rights reserved.
********************************************************************************
SYNTAX:
    g3Xflash OPTIONS INTERFACE COMMAND
OPTIONS:
...
COMMAND:
...
        up mfg
...
            In case of mfg upload using XML file, command syntax changes
            as below. XML file needs to be specified at two places.
            e.g.
            "g3Xflash -x   up mfg  3"
```

Supermicro support confirmed the current tools cannot change the SAS address, they would not supply the older version of the tools, and recommended I send the backplane in for service, or allow them to remotely SSH to the machine and they will change it for me. A bit disappointing that something so simple is made so complicated, and really way too much trouble.

Since I only had one expander in the chassis, there would be no issues using a default SAS address, and I decided to leave it as is. I replaced the other SAS2 backplane with the recovered SAS3 backplane, and the expander and all drives were back online.

![](/media/2020/02/ikvm_capture_1.jpg?w=720)

If anybody knows how to update the SAS address, or has a copy of the v6.00 CLIXTL tools that supposedly can change the address, please do let me know.
