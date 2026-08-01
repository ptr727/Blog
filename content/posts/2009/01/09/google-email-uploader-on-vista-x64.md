---
title: Google Email Uploader on Vista x64
date: '2009-01-10T04:17:00+00:00'
url: /2009/01/09/google-email-uploader-on-vista-x64/
categories:
- solution
tags:
- gmail
- google
- microsoft
- windows
- x64
post_id: '82'
---
I am currently importing a few thousand email messages from Outlook 2007 to my email account hosted on Google Apps. Google provides an [Email Uploader](http://mail.google.com/mail/help/email_uploader.html) utility, and it is easy to use, but getting it to work with Outlook 2007 on Vista x64 was less than trivial.

The utility installed fine on my Vista x64 system, but it found no mailboxes to import. A little [research](http://groups.google.com/group/google-email-uploader/browse_thread/thread/2f486b85c1096440) showed that several other people using Vista x64 and Outlook 2007 have exactly the same problem.

Since Google kindly publishes the [source](http://code.google.com/p/google-email-uploader/) for the tool, I decided to have a look. Turns out it was a relatively simple fix to get it to work.

The main application is a C# .NET application, with the build properties for the target set to "Any CPU". This means that on a x86 / WIN32 system it will be a 32bit process and on x64 / WIN64 system it will be a 64bit process.

The problem is that the application also uses two mixed mode DLLs, and these DLLs are compiled for x86 / WIN32. When running the main EXE on Vista x64, the process is a 64bit process, and that fails to load the 32bit DLLs. The fix was simple, change the build target from "Any CPU" to "x86".

I also had to fix a couple other small things in order to get the "Release" build to compile correctly. The DLLs are written in C++, but for some reason the developers used .MH and .MCC extensions instead of the standard .H and .CPP extensions. The "Debug" build had set custom build properties for .MCC files, and associated the files with the C++ compiler. Once I did the same for the "Release" build, the project compiled.

The last change was to set the Outlook import DLL linker options to delay load MAPI32.DLL.

You can download the binaries from [here](https://docs.google.com/uc?id=0B_YiDruAPkKzNzIyNzRiYjYtNTcxZS00MzRkLWE1MzMtMGE1N2FhZWNjMmFl&export=download&hl=en), simply extract and run.  
Please remember that I provide no warranty at all, I did minimal testing, so use at your own risk.

I hope Google makes these easy changes to the main source branch so future official versions also support Outlook 2007 on Vista x64.


