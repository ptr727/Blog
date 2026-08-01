---
title: DxO Optics Pro and Adobe Lightroom on Vista x64
date: '2009-02-11T23:15:00+00:00'
url: /2009/02/11/dxo-optics-pro-and-adobe-lightroom-on-vista-x64/
categories:
- solution
tags:
- dxo
- lightroom
- x64
post_id: '83'
---
I bought my first SLR camera, a Canon EOS 20D, and my first wide angle lens, a Canon EF-S 10-22, several years ago. Amongst the many articles and reviews I read, online and in magazines, I came across a product called [DxO Optics Pro](http://www.dxo.com/us/photo/dxo_optics_pro), a product that would supposedly correct, amongst other things, lens distortion. This seemed like the perfect tool to help me with my wide angle pictures that looked very “fishy eyed”. And since DxO, then version 4, was receiving good reviews, I decided to trial the product. In those days the DxO licensing model was to pay per camera body and per lens module, not a cheap investment, but I really liked the results and so I purchased the product.



Not too long after I purchased DxO, they changed their licensing model, and instead of paying per module, they came up with a Standard and an Elite product, with the distinction being the camera bodies that are supported. The Elite version typically supports more high end cameras, I am sure there is no technical difference in the calibration techniques, this just seemed like a way to get more money from professionals that own high end cameras.



In the mean time I switched to using [Adobe Lightroom](http://www.adobe.com/products/photoshoplightroom/) version 1, and DxO fell in disuse. Every now and again I did come across an article or forum post with less than flattering reports of the poor product quality in DxO version 4.5, and very poor quality in version 5. The other thing I read, and confirmed with DxO tech support, is that DxO did not support x64 editions of Vista, and since I had switched to Vista Ultimate x64 edition, this would be a problem.



I switched from taking mostly JPG images to mostly RAW images, and manual correction in LR became very time consuming, so I was again interested in DxO. By now I was using LR 2.2 x64 edition, and by now DxO 5.3.2 did support Vista x64 editions. I purchased an upgrade for DxO, I bought the more expensive Elite edition, since I have dreams of one day owning a 5D Mark II.



In standalone mode DxO 5.3.2 worked great, but the integration with LR was not so great. The problem is that [DxO does not support integration with the x64 edition of LR](http://forum.dxo.com/showthread.php?t=2265), when calling DxO from x64 LR nothing happens. The DxO installer is also not fully x64 compatible, it creates a start menu shortcut to the “DxO Download Manager v5”, but it sets the path to “C:\\Program Files\\DxO Labs\\DxO Download Manager v5\\DxODownloadManager.exe” instead of “C:\\Program Files (x86)\\DxO Labs\\DxO Download Manager v5\\DxODownloadManager.exe”, obviously a hardcoded path instead of dynamically discovered path.



Before I get to DxO, I think Adobe should have supported in-process DLL based plugins in LR, just like they do with Photoshop. For whatever reason this type of suggestion seems to make Adobe very uncomfortable, and [they go to great lengths to defend their position](http://blogs.adobe.com/jnack/2008/08/the_lightroom_v.html), reads more like marketing firefighting, and say why the LUA based scripting and external process launching is so much better than plugins, at least when compared to Apple Aperture. I am a software developer, there is no way that anybody can convince me that a scripting language or launching an external process is better, or as good, as a native DLL based plugin with a rich integration API.



So how does DxO integrate with LR in light of the lacking plugin model? When you edit an image using an external editor, LR launches the editor with the image path specified on the commandline. LR provides three options for what file is passed to the external editor; the original file, a copy of the original file, or a copy of the LR processed version of the file. The problem is that when the file is a RAW file, LR only allows a copy of the LR processed version of the file to be passed, and this processed file is useless to a RAW editor.



DxO, being a RAW file processor, obviously needs access to the original RAW file, and they go about it in a clever, but cumbersome way. LR allows for configuration of the file type and file name of the new file it generates, and DxO exploits this file naming scheme to infer the original filename. E.g. the original RAW file is called Test.CR2, LR creates a copy of this file and names it Test-Edit.TIF, DxO infers the original filename is Test.CR2, opens Test.CR2 as the input file, and uses Test-Edit.TIF as the output file.



DxO can run in one of two modes; “plugin-in” mode (their spelling, not mine) or normal mode. When launched by LR, DxO runs in plugin mode. In plugin mode DxO only allows processing of the images passed in on the commandline, and the output processing automatically replaces those same input files.



Since DxO does not have a way of explicitly launching in plugin mode, they infer the mode by interpreting how they are being launched. DxO looks at their parent process, and if the parent process is called Lightroom.exe, and the Lightroom.exe has version information that looks like LR, then DxO automatically enters plugin mode.



So why does DxO not work when launched from the x64 edition of LR? When launching DxO from x64 LR the DxO process starts and immediately terminates without showing any UI. It appears that DxO fails to determine information about the parent process when the parent process is a x64 process. I am speculating, but this is probably related to the technique that DxO is using to determine information about the parent process. Typically one would use the PS API or ToolHelp API’s, along with NtQueryInformationProcess(), but when mixing x86 and x64 process types, they do not provide consistent information, and extra handling is required by using IsWow64Process(). A more portable, but less reliable, alternative is to use WMI. DxO is not a native application, it is written in .NET, presumable C#, but it apparently still suffers from some x64 related problem.



So how do we solve the problem? You can install both the x64 and the x86 editions of LR on your x64 system, and when you want to work with DxO you can use the x86 edition of LR. This however is not very convenient. My solution was to create a x86 proxy process that looks like LR, is discoverable by DxO, and convinces DxO to enter plugin mode. LR is then configured to launch the proxy process instead of DxO, the proxy process launches DxO and passes the same commandline parameters as passed by LR to DxO, waits for DxO to terminate, and returns the exit code to LR.



Instead of inferring the mode of operation by looking at attributes of the parent process, it would have been much simpler, and it would have avoided the x64 problem, if DxO had a stub executable that always launched in plugin mode. And, it would have been even better if LR supported DLL based plugins with programmatic access to image information instead of inferring it. But, DxO would then have had to write a native x64 DLL, and if they can’t even write WoW64 compatible x86 code, I don’t know if that would have been a solution.



So how did I figure this out?



At this point I have to remind you that I have absolutely no connection with DxO, nor insight into the coding of DxO, nor did I reverse engineer or disassemble DxO, my analysis and solution is purely based on observing LR and DxO behaviors by using [Microsoft Process Monitor](http://technet.microsoft.com/en-us/sysinternals/bb896645.aspx).



I compared the behavior of DxO on a x86 system with the behavior on a x64 system, and I noticed that on the x86 system the DxO process opens the LR executable file on disk. Looking at the call stack I noticed that DxO calls the.NET runtime calls the GetFileVersionInfoW() API. On the x64 system DxO never attempts to open the LR executable. I installed the x86 version of LR on the x64 system, and noticed a similar behavior to the x86 system.



I created a C++ project in Visual Studio 2008, and wrote code to take the input commandline parameters and call the DxO executable with the same parameters as passed in by LR. I built a x86 binary, renamed the output file Lightroom.exe, and when I run “Lightroom.exe c:\\test\\test-edit.tif”, DxO would open in plugin mode, but would not load the original test.cr2 file. I added version information to the proxy project, and matched the version information contents to that of the real LR binary. Repeating the test, DxO now believes that it was called by LR and it opens in plugin mode and it finds the correct RAW file.



The source and binary file is available [here](https://docs.google.com/uc?id=0B_YiDruAPkKzNzUyNzBiMGItNGZkMi00ODkyLTk5YTEtNGVhNDg4ZmNiYzc1&export=download&hl=en).

Please remember that I provide no warranty at all, I did minimal testing, so use at your own risk.



To install simply extract, rename DxOProxy.exe to Lightroom.exe, and change the LR configuration to point to the proxy Lightroom.exe instead of the DxO binary.



In closing, and in light of my previous post related to my trouble with the [Google Email Uploader on x64](/2009/01/google-email-uploader-on-vista-x64.html); with all the available programming documentation, and free compilers, and free virtualization testing environments, why is it so difficult for some ISV’s to produce quality and compatible software?


