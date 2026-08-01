---
title: Self Signed BitFury Drivers
date: '2014-04-17T01:45:16+00:00'
url: /2014/04/16/self-signed-bitfury-drivers/
categories:
- solution
tags:
- bitcoin
post_id: '566'
---
Almost two years ago I pre-ordered some [bitcoin](https://bitcoin.org/en/) mining hardware from [Butterfly Labs](http://www.butterflylabs.com/), what a waste. After countless delays, more than a year late, they finally shipped the hardware, and given the low probability of ever recovering the money through mining, I immediately sold the hardware on eBay, for a little profit.

In the mean time USB stick miners became available, outperforming GPU mining, and easy to setup and run. I've had a couple of ASICMiner Block Erupter's running under my desk for some time, in the early days I saw some fractions of coins coming in, but in recent months they are so under-powered against the current hash-rates that they do little more than blink lights.

There is a resurgence in [USB stick mining hardware](https://bitcointalk.org/index.php?topic=464496), specifically the Bitfury type devices, many based on the [NanoFury](https://github.com/nanofury/NanoFury) open source project that provided software, design, and PCB schematics.

I got myself a [Red Fury](https://bitcointalk.org/index.php?topic=321551), an [Nano Fury II](https://bitcointalk.org/index.php?topic=526925), and a [Hex Fury](https://bitcointalk.org/index.php?topic=523063). Compared to the 300MH/s of my little Block Erupters, these run at 2GH/s, 4GH/s, and 11GH/s respectively. There is still no way to ever make a profit in mining (at this scale), but I was really interested in seeing how these newer generation devices worked, especially since the publication of the NanoFury open source project, where in theory I could build my own.

So what does this have to do with self signed drivers, well, my mining tool of choice is [CGMiner](https://github.com/ckolivas/cgminer), but CGMiner currently only runs Nano Fury II's at half speed, requiring the use of [BFGMiner](https://github.com/luke-jr/bfgminer) to go full speed. But unlike CGMiner that accesses all USB devices via [Zadig](http://zadig.akeo.ie/) installed WinUSB drivers, BFGMiner requires native Windows drivers, and neither the Red Fury nor the Hex Fury drivers are signed, so no installation on Windows 8 x64 (without disabling driver signing on every boot).

Looking at the INF files, all these devices do is register the USB hardware id as a generic null modem USB to COM bridge device, so no binaries required, just a signed CAT file.

After a bit of searching I found that I was not alone in my frustration, and I [found](https://bitcointalk.org/index.php?topic=367981) a self-signed Red Fury driver. But, the Hex Fury used a different hardware id, and most people used CGMiner, so no need for a signed native driver as Zadig took care of that for us. So, I created my own signing script and signed my own drivers, install ok, BFGMiner happy.

If you just want signed drivers, get a copy of self-signed "Bitfury BF1" and "bi•fury" drivers [here](/media/2014/04/bitfury.zip).

If you are interested in signing your own drivers, read on.

I tested on Windows 8.1 Update 1 x64:

Install the Windows 8.1 [SDK](http://msdn.microsoft.com/en-us/windows/desktop/bg162891.aspx) and [WDK](http://msdn.microsoft.com/en-us/windows/hardware/gg454513.aspx).
Get the original "[Bitfury BF1](http://cryptoware.co.uk/pages/red-fury)" and "[bi•fury](http://cryptostore.io/?page_id=550)" INF files.
The bf1.inf file is saved in \*NIX format (CR), convert it to Windows format (CRLF).
Create a self signed certificate:

```

makecert.exe -r -pe -ss PrivateCertStore -sr localMachine -n "CN=BitFury Test Signing Certificate" "C:\BitFury\BitFuryTest.cer"

```

[![Self Signed Certificate](/media/2014/04/selfsign-3.png)](/media/2014/04/selfsign-3.png)

Prepare the INF files, and create CAT files:

```

stampinf.exe -n -f "C:\BitFury\bf1.inf" -d * -v * -c "bf1.cat"
stampinf.exe -n -f "C:\BitFury\bifury_c4C.inf" -d * -v * -c "bifury_c4C.cat"
inf2cat.exe /v /driver:C:\BitFury\ /os:7_x86,7_x64,8_x86,8_x64

```

Sign the CAT files:

```

signtool.exe sign /v /s PrivateCertStore /n "BitFury Test Signing Certificate" /t http://timestamp.verisign.com/scripts/timestamp.dll "C:\BitFury\bf1.cat"
signtool.exe sign /v /s PrivateCertStore /n "BitFury Test Signing Certificate" /t http://timestamp.verisign.com/scripts/timestamp.dll "C:\BitFury\bifury_c4C.cat"

```

To use the drivers, you have to import the signing certificate into the local certificate store. As this is basically a self-signed CAT file, there are no trusted root certificates in the system that signed the signing certificate, and we need to add the signing certificate to the root and the trusted certificate stores.

```

certmgr.exe -add -c "C:\BitFury\BitFuryTest.cer" -s -r localMachine root
certmgr.exe -add -c "C:\BitFury\BitFuryTest.cer" -s -r localMachine trustedpublisher

```

Alternatively you can run "certlm.msc", and import the certificate file into the "Trusted Root Certification Authorities" and the "Trusted Publishers" hives.

[![SelfSign.2](/media/2014/04/selfsign-2.png?w=584)](/media/2014/04/selfsign-2.png)[![SelfSign.1](/media/2014/04/selfsign-1.png?w=584)](/media/2014/04/selfsign-1.png)

Last thing left to do is to use your newly signed drivers when selecting the custom driver from device manager.

[![SelfSign.4](/media/2014/04/selfsign-4.png)](/media/2014/04/selfsign-4.png)[Here](/media/2014/04/bitfury.zip) is a package with signed drivers, and scripts to help you sign your own INF files, and import the certificate. It should work on Windows 7 and Windows 8 x86 and x64. Your mileage may vary, use at your own risk :)
