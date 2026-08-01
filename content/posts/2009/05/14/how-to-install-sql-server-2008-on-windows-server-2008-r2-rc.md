---
title: How to install SQL Server 2008 on Windows Server 2008 R2 RC
date: '2009-05-14T20:44:00+00:00'
url: /2009/05/14/how-to-install-sql-server-2008-on-windows-server-2008-r2-rc/
categories:
- uncategorized
tags:
- microsoft
- sqlserver
- windows
post_id: '87'
---
I was trying to install SQL Server 2008 on Windows Server 2008 R2 RC.

But, when I launch SETUP.EXE, Windows warns me that SQL Server is not compatible with Windows Server.  
If I ignore the warning, the install proceeds but then fails to install .NET 3.5.

After a little searching and experimentation I found a way to install without any problems:  
1\. Create a slipstreamed SQL Server 2008 SP1 install, follow the instructions [here](http://blogs.msdn.com/petersad/archive/2009/02/25/sql-server-2008-creating-a-merged-slisptream-drop.aspx).  
I set my my PCUSOURCE=".\\PCU" and that worked fine.  
2\. Add .NET 3.5 by going to server manager and adding the .NET 3.5.1 feature.  
3\. Install by running SETUP.EXE.

I hope this helps somebody.


