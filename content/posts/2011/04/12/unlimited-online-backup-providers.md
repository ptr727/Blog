---
title: Unlimited online backup providers becoming extinct
date: '2011-04-13T04:53:00+00:00'
url: /2011/04/12/unlimited-online-backup-providers/
categories:
- backup
- cloud
- storage
tags:
- avg
- backblaze
- carbonite
- crashplan
- elephantdrive
- livekive
- mozy
- safesync
post_id: '116'
---
I just received an email from [ElephantDrive](http://www.elephantdrive.com/) informing me that my legacy unlimited storage account will be terminated in 30 days, and that I must select a new plan.

In July 2009 [ElephantDrive](http://www.elephantdrive.com/) [announced](http://support.elephantdrive.com/entries/211796-why-did-elephantdrive-change-their-plans) that they are no longer offering their $100 per year unlimited storage plan. ElephantDrive is now offering a [$200 per year for 500GB](https://www.elephantdrive.com/welcome/home_plans.aspx) plan.  
In February 2011 [Mozy](http://mozy.com/) [announced](http://mozy.com/support/mozyhome?utm_source=newsletter&utm_medium=email&utm_content=MillinerLaunch-WayOver&utm_campaign=SpecialAnnouncements&ref=36b792db) that they are no longer offering their $55 per year unlimited storage plan. Mozy is now offering a [$120 per year for 125GB](http://mozy.com/home/pricing/) plan.  
In February 2011 [Trend Micro SafeSync](http://us.trendmicro.com/us/products/personal/safe-sync/) announced that they are [bandwidth throttling](http://esupport.trendmicro.com/pages/Frequently-Asked-Questions-FAQ-about-Rate-Limiting-in-Trend-Micro-SafeSync.aspx) large accounts. In March 2011 they announced that they are no longer offering their $35 per year unlimited storage plan. SafeSync is now offering a [$150 per year for 150GB](http://us.trendmicro.com/us/products/personal/safe-sync/) plan.  
Carbonite offers a [$55 per year for unlimited storage](https://buy.carbonite.com/buy/index/4486) plan, but they are [bandwidth throttling](http://carbonite.custhelp.com/app/answers/detail/a_id/1440) accounts over 35GB to 512Kbps and accounts over 200GB to 100Kbps access speeds.  
[AVG LiveKive](http://www.avg.com/us-en/avg-livekive) offers a [$80 per year for unlimited storage](http://www.avg.com/us-en/avg-livekive) plan, but the [terms of service](http://www.avg.com/us-en/livekive-terms) defines unlimited as 500GB.  
[BackBlaze](http://www.backblaze.com/) offers a [$60 per year for unlimited storage](http://www.backblaze.com/) plan.  
[CrashPlan](http://www.crashplan.com/) offers a [$50 per year for unlimited storage](http://www.crashplan.com/consumer/store.vtl) plan.   
Neither [BackBlaze](http://www.backblaze.com/)nor [CrashPlan](http://www.crashplan.com/) supports their unlimited plan on server class machines.

I currently have 2.1TB of data backed up online with [ElephantDrive](http://www.elephantdrive.com/) running on my Windows Server 2008 R2 machine. Needles to say, none of their new plans are affordable for that amount of storage. I either need to significantly trim down what I backup, or I need to find a new unlimited storage provider, that also allows installs on Windows Server.  
For now, I’m uninstalling ElephantDrive.

\[Update\]  
CrashPlan's new v3 software installs and runs fine on Windows Server 2008 R2, and I have switched to using CrashPlan for my backup needs.

Here is an example snippet of the status emails I receive from CrashPlan:  
Source → TargetSelectedFilesBacked  
Up %Last  
ConnectedLast  
BackupVM-STORAGE → CrashPlan Central2.1TB ↑1KB423k 0100.0%2.5 hrs4.3 hrs  


