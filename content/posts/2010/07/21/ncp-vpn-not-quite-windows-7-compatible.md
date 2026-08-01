---
title: NCP VPN not quite Windows 7 compatible
date: '2010-07-21T23:24:00+00:00'
url: /2010/07/21/ncp-vpn-not-quite-windows-7-compatible/
categories:
- review
- solution
tags:
- ncp
- vpn
- windows
- x64
post_id: '110'
---
I got so frustrated with the [NCP VPN client](http://www.ncp-e.com/en/solutions/vpn-products/ipsec-client.html) software, specifically a recent update, that I decided to let my frustration out by writing about it.

For a long time I used the, IT approved, Cisco VPN client to access our corporate network. And as the OS technology moved along, so did my systems, meaning Vista, Windows 7, and 64-bit. While, for the most part, our IT approved systems remained to be only 32-bit XP. Cisco, for some reason, maybe they are representative of IT organizations as whole, was late to support Vista, was late to support Windows 7, and for the longest time never supported x64.

The only Cisco compatible alternative on Windows 7 x64, was the NCP VPN client. But, at a cost, [$144](http://www.shareit.com/product.html?cart=1&productid=300002618&backlink=http://www.shareit.com/product.html%3Fproductid%3D300004167&cookies=1&showcart=1), per machine, very expensive.

I recently read [that almost 50% of Windows 7 machines are 64-bit](http://windowsteamblog.com/windows/b/bloggingwindows/archive/2010/07/08/64-bit-momentum-surges-with-windows-7.aspx), and I recently read that Cisco [announced VPN client support for x64 on Vista and Windows 7](http://www.cisco.com/en/US/docs/security/vpn_client/cisco_vpn_client/vpn_client5007/release/notes/vpnclient5007.html#wp101224). I am sure this is not a coincidence.

But I digress, this post is not about Cisco, it is about the [NCP VPN client](http://www.ncp-e.com/en/solutions/vpn-products/universal-ipsec-client.html).

Where to start?

The NCP software is intrusive, every time you login it shows a splashscreen, and the splashscreen remains topmost, blocking anything behind it, until it closes, by itself. I contacted NCP support, complaining about the intrusion, and they told me that it is necessary to run their software at login so that they can validate the license. I replied that validating the license need not happen at every login, and certainly should not interfere with my system. They said I could search the internet and find out how other people disabled their software.

This means a few things to me; they do not value usability, they acknowledge there is a problem, yet they do not offer a solution.

Imagine if every application you install on your system decides it is a good idea to show a splashscreen when you login.

Here is the splashscreen that pops up on every login:   
[![NCP.Splash](/external/17a532eabbda55e1.png)](/external/3189bb34b720d0e5.png)

In case you are wondering how to disable NCP from running at startup, they install three user session startup entries under \[HKEY\_LOCAL\_MACHINE\\SOFTWARE\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Run\], delete or rename them

While we’re on the topic of usability, this application’s UI was probably not designed by Windows developers, or certainly not somebody that knows anything about standard Windows user interface design and principles.

In the main UI, shown below, how do you connect, where is the connect button, do you click the red button, no you need to click the gray area next to the red button. They probably though it looks cool.   
[![NCP.UI.1](/external/5e5e7b08ae4854e1.png)](/external/14e292fa67e9fe73.png)

Every time you login the application starts and shows its UI. How would you normally look for options in a windows app; probably \[Options\], or \[Tools\]\[Options\], or \[File\]\[Options\]. No, you need to click on \[View\]\[Autostart\]\[No Autostart\], what does the \[View\] menu have to do with \[Autostart\]?   
[![NCP.UI.7](/external/922ac06d6897bfdf.png)](/external/73f5e53a275bccec.png)

And in case you were wondering, no, disabling autostart does not disable the splashcreen.

So what is it that made me mad enough to write this post?

I received an email that a new version was released, and the software offers a built in check for update mechanism by clicking \[Help\]\[Search for Updates\]:   
[![NCP.KB.vs.MB](/external/386f143d5cd6836d.png)](/external/a4034646f8985f0d.png)

How big is that update? 23.792 kByte, really, 24 kilobyte, or what is a lowercase k in kByte? Or is that really 23,729 KB as in 24 megabyte?   
[![NCP.KB.vs.MB.1](/external/f9d13408b361c5b1.png)](/external/12dcaf1eb7863dc4.png)

Downloaded the update, now let’s apply it:   
[![NCP.Reboot](/external/1dd571cbff8a1287.png)](/external/2be5908edc1e78da.png)

And then the Windows Program Compatibility Assistant pops up:   
[![NCP.AppCompat](/external/5381c7598031f294.png)](/external/266b5fbf27a8eb3c.png)

I contacted support, got an email that said no other users had reported this problem, and they asked if I am an admin on the system, but before I could respond, I got another email that said they reproduced the problem, and that I should download and install the update from the website.

Let’s download the update directly, and install it:   
[![NCP.Update](/external/bfa457b0ac1dd8e7.png)](/external/b4574a68c19eeb16.png)

And then the Windows Program Compatibility Assistant pops up:   
[![NCP.AppCompat.1](/external/9900f082649d4552.png)](/external/5c7e1565a24a0f33.png)

You may think it is a problem with my system, I repeated the same steps on a second system, that is how I captured the screenshots, and I ran [Microsoft Process Monitor](http://technet.microsoft.com/en-us/sysinternals/bb896645.aspx) to record what is happening.

As a developer, that is familiar with writing Windows 7 compatible software, I know what is going on here.

The NCP software installs:   
Three startup items: NcpBudgetGui, NcpPopup, NcpRsuGui   
Three services: ncpclcfg, ncprwsnt, NcpSec   
Two drivers: ncpfilt, ncplelhp

The NCP UI process is called NCPMON.exe, and is launched by explorer, runs non-elevated, at medium IL. It is the NCPMON.exe process that downloads and executes the update.

From the procmon log I can see that NCPMON.exe called CreateProcess() to launch the installer:   
Date & Time:    7/21/2010 10:01:12 AM   
Event Class:    Process   
Operation:    Process Create   
Result:    SUCCESS   
Path:    C:\\Users\\Pieter Viljoen\\AppData\\Local\\Temp\\NCP\_EntryCl\_Win32\_923\_17.exe   
TID:    6952   
Duration:    0.0000000   
PID:    6856   
Command line:    "C:\\Users\\Pieter Viljoen\\AppData\\Local\\Temp\\NCP\_EntryCl\_Win32\_923\_17.exe"

This will not work, the NCP\_EntryCl\_Win32\_923\_17.exe is an installer it has to “Run As Admin” (this is an InstallShield installer, and although it does not contain a [Run As Admin manifest entry](http://msdn.microsoft.com/en-us/library/bb756929.aspx), the Windows Application Compatibility subsystem recognizes InstallShield installers, and automatically runs them with elevation required), this means that when you launch this EXE using ShellExecute(), or using Explorer, you will get a UAC elevation prompt, and if approved, the installer will run elevated, and the install succeed.

There is only one explanation of how NCP could ever have shipped this, their developers and QA test with UAC disabled on their test systems.

What about the appcompat warning after the install?

Microsoft requires that Windows Vista and Windows 7 compatible applications [mark their compatibility in the installer manifest](http://msdn.microsoft.com/en-us/library/dd371711(VS.85).aspx).

By inspecting the resources in the installer EXE, there is a manifest, but there is no compatibility manifest, as such, this error will always show on a Windows 7 system.

I have no explanation for how NCP could allow this to ship, ignorance?

It makes me mad that an ISV advertises Windows 7 compatibility, and ships software like this. It is companies like NCP that gives Windows a bad name, and drives companies like Apple, to enforce rigorous, sometimes draconian, quality and usability standards in order to protect their own brand.


