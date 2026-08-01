---
title: Amazon Unbox on x64 Vista
date: '2009-06-14T03:41:00+00:00'
url: /2009/06/13/amazon-unbox-on-x64-vista/
categories:
- solution
tags:
- amazon
- windows
- x64
post_id: '89'
---
While shopping on Amazon I noticed that they were offering the Pilot of the [Showtime series Nurse Jackie in HD](http://www.amazon.com/gp/product/B002BEF75G?pf_rd_p=481507571&pf_rd_s=center-2&pf_rd_t=1401&pf_rd_i=1000128561&pf_rd_m=ATVPDKIKX0DER&pf_rd_r=1YPJ8P20JGC64Y7W0F9Y "HBO series Nurse Jackie in HD") for free, so I decided to give it a try.

The install (version 2.0.1.95) went smoothly, and the 1.3GB downloaded also completed pretty quickly, and I watched the show.



Ok, now I wanted to stop the Unbox player service from running and terminate the tray icon application, I have no need to have it running all the time.

I went to \[Settings\]\[Preferences\], and unchecked the \[Run the Amazon Unbox service when Windows starts\] option.

I then right clicked on the tray icon and selected \[Exit\], the tray application launched "Amazon Unbox Config.exe stop" application, requiring UAC elevation, and promptly crashed with the following message:



> An unhandled exception of type 'System.BadImageFormatException' occurred in Unknown Module.  
Additional information: Could not load file or assembly 'ADVWindowsClientAppRoot, Version=2.0.1.95, Culture=neutral, PublicKeyToken=091de1773ddefdbf' or one of its dependencies. An attempt was made to load a program with an incorrect format.



I contacted Amazon support, and they provided this response:



> Hello from Amazon.com.
>
> I sincerely apologize for the trouble you've had using the Unbox Video Player. From your message, I understand you received an error relating to Windows being unable to load the correct file path.
>
> I've researched the issue and suggest that you update the security components of your Microsoft operating system.
>
> Please visit the Microsoft website listed below and follow Microsoft's instructions for updating your security components. Microsoft may require you to use Internet Explorer to access all of the functions of this page and enable Active X controls in your Web browser.
>
> http://drmlicense.one.microsoft.com/Indivsite/en/indivit.asp
>
> If using Microsoft's update does not resolve your playback issue, I recommend uninstalling and reinstalling your .NET Framework.
>
> The Microsoft .NET Framework includes a large library of coded solutions to common programming problems and a virtual machine that manages the execution of programs written specifically for the framework. The .NET Framework is a key Microsoft offering and is intended to be used by most new applications created for the Windows platform.
>
> I hope you found this information useful.



I gave them the benefit of the doubt and tried to update the DRM components, it did not work.



I suspected I know what the problem was, and this problem reminded me of a similar problem with the [Google Email Uploader on Vista x64](/2009/01/google-email-uploader-on-vista-x64.html "Google Email Uploader on Vista x64").

My suspicions were confirmed after I used [CorFlags](http://msdn.microsoft.com/en-us/library/ms164699(VS.80).aspx "CorFlags") to inspect the binaries:



> CorFlags.exe "C:\\Program Files (x86)\\Amazon\\Amazon Unbox Video\\Amazon Unbox Config.exe"  
Microsoft (R) .NET Framework CorFlags Conversion Tool. Version 3.5.21022.8  
Copyright (c) Microsoft Corporation. All rights reserved.
>
> Version : v2.0.50727  
CLR Header: 2.5  
PE : PE32  
CorFlags : 9  
ILONLY : 1  
32BIT : 0  
Signed : 1
>
> CorFlags.exe "C:\\Program Files (x86)\\Amazon\\Amazon Unbox Video\\ADVWindowsClientAppRoot.dll"  
Microsoft (R) .NET Framework CorFlags Conversion Tool. Version 3.5.21022.8  
Copyright (c) Microsoft Corporation. All rights reserved.
>
> Version : v2.0.50727  
CLR Header: 2.5  
PE : PE32  
CorFlags : 11  
ILONLY : 1  
32BIT : 1  
Signed : 1



The output indicated that the EXE file was compiled to run natively on any platform, i.e. x64 on x64 and x86 on x86, but the DLL was compiled to be x86 only.

Thus the EXE runs as x64 and tries to load a x86 binary, not allowed, causing the crash.



The CorFlags output and x64 migration is discussed in this [MSDN blog post](http://blogs.msdn.com/gauravseth/archive/2006/03/07/545104.aspx "MSDN blog post"):

> anycpu: PE = PE32 and 32BIT = 0  
x86: PE = PE32 and 32BIT = 1  
64-bit: PE = PE32+ and 32BIT = 0



To fix the problem I have to change the EXE attributes to only run in 32bit:



> CorFlags.exe "C:\\Program Files (x86)\\Amazon\\Amazon Unbox Video\\Amazon Unbox Config.exe" /32BIT+ /Force



The "Force" flag is required because the binary is Authenticode signed, and after the header change the Authenticode signature is now invalid.

"CorFlags" is parts of the .NET / Platform SDK and can be [downloaded from Microsoft](http://www.microsoft.com/downloads/details.aspx?displaylang=en&FamilyID=e6e1c3df-a74f-4207-8586-711ebe331cdc "downloaded from Microsoft").



After I made the changes to the EXE, I repeated the original steps, and no more crash.



I replied to Amazon with my findings, and I hope they make the necessary, and easy, changes to fully support x64.




