---
title: Trend Micro SafeSync, neat, but unreliable
date: '2010-12-31T22:17:00+00:00'
url: /2010/12/31/trend-micro-safesync-neat-but-unreliable/
categories:
- backup
- cloud
- review
tags:
- crash
- dropbox
- safesync
- trendmicro
post_id: '112'
---
I wanted to write about [Trend Micro SafeSync](http://us.trendmicro.com/us/products/personal/safe-sync/), but it reminded me of my [Streamload](http://en.wikipedia.org/wiki/Streamload) experience, and I ended up writing [this](/2010/12/will-your-online-backup-or-sync-and.html) instead. This time I am really going to write about SafeSync.

SafeSync is another online backup and sync and share application. Actually, they offer both online storage through a mapped drive, and syncing folders online, this makes it unique compared to many existing offerings.

I have used almost all online backup and sync and share type applications out there, my favorite remains [DropBox](http://www.dropbox.com/). SafeSync used to be [Humyo](http://en.wikipedia.org/wiki/Humyo), before being acquired by Trend. I have used Humyo when they were in Beta, it was just ok, but between then and now their product seem to have come a long way.

Of all the online backup and sync and share applications, a few things remain constant;   
Free is unsustainable, somebody has to pay for the staff, the bandwidth, the disks, and the infrastructure. These vendors are running on venture capital, waiting for acquisition, for paid customers, for indirect monetization, or failure.   
Unlimited storage is unfeasible, the increased home bandwidth capacity makes it easy to upload Terabytes of data, and we are back at the cost factor.   
Usability and coolness is critical, especially usability on mobile devices, and coolness on web frontends.   
Reliability is critical, and this brings me back to SafeSync.

SafeSync offers many things common to many other backup or sync and share providers, but three things stood out; they offer unlimited storage, they offer data access using WebDAV, and the web frontend allows convenient access to pictures and music.

The product is offered as a yearly service, listed as $59.99 on the Trend eStore, or $35.95 on the Trend US product page, weird. Regardless, when you add the product to the cart, the cost is $35.95.

I installed the software on three systems, two running Windows 7 Ultimate x64, and one running Windows Server 2008 R2. The install creates a new drive that is mapped to the online storage, and a user session application that can be used to sync a local folder to the online storage.

Here are some screenshots:   
[![SafeSync.Config.Folders](/external/7a1d3f4e06439834.png)](/external/7c2a1af966937893.png)  
[![SafeSync.Config.Connection](/external/268628bf232ab13d.png)](/external/8cff859749334196.png)  
[![SafeSync.Status](/external/98235426b88ea166.png)](/external/b36dd6311012f985.png)

The web frontend really reminds me of Streamload:   
[![SafeSync.Online](/external/45991e594b4c6641.png)](/external/aa03c29848de548e.png)

A very neat feature is WebDAV access to the storage. This means that you can access the data using any WebDAV client, and there is no need to install the SafeSync client software. Here is a [Trend KB](http://support.antivirus.co.uk/trendmicro/kbresolution.jsp?hmid=52790&serviceId=37&applicationId=265#_Is_it_possible) for details, basically you connect to “dav.trendmicro.safesync.com” using your SafeSync credentials.

You can use the built in Windows WebDAV client to access the storage, but you have to make a registry change, else you will get a "the folder you entered does not appear to be be valid" error. After you make the change reboot, or just restart the WebClient service. See this [Microsoft KB](http://support.microsoft.com/kb/2123563) for details:   
\[HKEY\_LOCAL\_MACHINE\\SYSTEM\\CurrentControlSet\\services\\WebClient\\Parameters\]   
"BasicAuthLevel"=dword:00000002

Open explorer and map a network drive to “\\\dav.trendmicro.safesync.com”:   
[![WebDAV.Windows](/external/c6828d686298df8b.png)](/external/42f4db7bc0ee0460.png)

Here are some explorer screenshots of a mapped drive using SafeSync, Windows, and [WebDrive](http://www.webdrive.com/products/webdrive/winindex.html):   
[![SafeSync.Cross](/external/eee10f3e4bc8235f.png)](/external/4f7907474a301c7b.png)  
[![Windows.Cross](/external/2e48fa96402a46f7.png)](/external/0a0e8db33571fd3d.png)  
[![WebDrive.Cross](/external/1f4ede9f9fc4a11e.png)](/external/045bf94def0b653b.png)

So this all sounds great, well, not so great, the client application has serious stability issues.

On two machines, every time I logout of Windows, Windows reports that SafeSync is not responding, after a minute or so, Windows eventually logs out.   
On one machine, every time I logout, Windows paints the logging out screen, and never completes, requiring a power cycle.

SafeSync interferes with applications that are accessing files in a shared folder. It appears that SafeSync notices a file modification, then opens the file, and does not allow other applications access to the file. As an example, I create backups of my CD collection using [dbPoweramp](http://www.dbpoweramp.com/), and I shared the output folder in SafeSync. While dbPoweramp is still using the files, SafeSync opens the file and dbPoweramp fails. This is not a problem with dbPoweramp, and other sync applications, like DropBox, work just fine in the same situation.   
[![dBPoweramp.Error.Writing](/external/0f10c13980dede96.png)](/external/6b280149315843db.png)

Adobe PhotoShop CS4 x64 crashes every time I open an image that is located in a shared folder. The crash is caused by the SafeSync explorer shell extension.   
FAULTING\_IP:   
HrfsShellExtension!DllUnregisterServer+202ef

If a sync is in progress, and the machine goes to sleep, then later wakes up, SafeSync does not reconnect, instead it reports that the server is unavailable. In order to resolve this you have to logout and log back in.

I added a folder to sync, this folder was very large, the status window indicated it would take several days to complete, I wanted to remove the mapping. On clicking the remove button, I received this funny error message, “Unexpected and unknown error, it is possible a logical error”. The only way to stop the sync was to uninstall.   
[![SafeSync.Logical.Error](/external/3a25fab79c71dfb2.png)](/external/98d84413bf424b21.png)

SafeSync crashed while uninstalling.   
[![SafeSync.Uninstall.Crash](/external/93fbe5b1f238fb8c.png)](/external/dd3e8d585e376e55.png)

Lastly, the website does not display any file extensions.

I have not quite given up on the service, just the client software, it is simply too buggy. I am still using the online storage through a [WebDrive](http://www.webdrive.com/products/webdrive/winindex.html) mapped drive.   
But, I still do not believe that unlimited storage is a sustainable business practice, and I would not be surprised if SafeSync limits storage, dramatically increases pricing, or is terminated.


