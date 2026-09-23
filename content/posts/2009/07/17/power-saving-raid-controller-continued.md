---
title: Power Saving RAID Controller (Continued)
date: '2009-07-18T00:20:00+00:00'
url: /2009/07/17/power-saving-raid-controller-continued/
categories:
- power
- review
- storage
tags:
- adaptec
- amazon
- lsi
- nas
- raid
- sata
- sleep
- wd
post_id: '92'
---
This post continues from my [last post](/2009/06/power-saving-sata-raid-controller.html "last post") on power saving RAID controllers.





It turns out the Adaptec 5 series controller are not that workstation friendly.





I was testing with Western Digital drives; 1TB Caviar Black WD1001FALS, 2TB Caviar Green WD20EADS, and 1TB RE3 WD1002FBYS.

I also wanted to test with the new 2TB RE4-GP WD2002FYPS drives, but they are on backorder.



I found that the Caviar Black WD1001FALS and Caviar Green WD20EADS drives were just dropping out of the array for no apparent reason, yet they were still listed in ASM as if nothing was wrong.

I also noticed that over time ASM listed medium errors and aborted command errors for these drives.



In comparison the RE3 WD1002FBYS drives worked perfectly.



A little searching pointed me to a feature of WD drives called Time Limited Error Recovery (TLER).

You can read more about TLER [here](http://www.hardforum.com/showthread.php?s=150abd4f7c6ef7d75ea7b0d752190329&t=1285254 "here"), or [here](http://en.wikipedia.org/wiki/Time-Limited_Error_Recovery "here"), or [here](http://wdc.custhelp.com/cgi-bin/wdc.cfg/php/enduser/std_adp.php?p_faqid=1397&p_sid=1fPqzI-i&p_lva=1478&p_accessibility=0&p_redirect=&p_sp=cF9zcmNoPTEmcF9zb3J0X2J5PSZwX2dyaWRzb3J0PSZwX3Jvd19jbnQ9OCZwX3Byb2RzPTAmcF9jYXRzPTAmcF9wdj0mcF9jdj0mcF9zZWFyY2hfdHlwZT1hbnN3ZXJzLnNlYXJjaF9mbmwmcF9wYWdlPTEmcF9zZWFyY2hfdGV4dD1UTEVS&p_li= "here").



Basically the enterprise class drives have TLER enabled, and the consumer drives not, so when the RAID controller issues a command and the drive does not respond in a reasonable amount of time, the controller drops the drive out of the array.



The same drives worked perfectly in single drive, RAID-0, and RAID-1 configurations with an Intel ICH10R RAID controller, granted, the Intel chipset controller is not in the same performance league.





The Adaptec 5805 and 5445 controllers I tested did let the drives spin down, but the controller is not S3 sleep friendly.



Every time my system resumes from S3 sleep ASM would complain "The battery-backup cache device needs a new battery: controller 1.", and when I look in ASM it tells me the battery is fine.



Whenever the system enters S3 sleep the controller does not spin down any of the drives, this means that all the drives in external enclosures, or on external power, will keep on spinning while the machine is sleeping.

This defeats the purpose of power saving and sleep.



The embedded Intel ICH10R RAID controller did correctly spin down all drives before entering sleep.



Since installing the ASM utility my system is taking a noticably longer time to shutdown.

Vista provides a convenient, although not always accurate, way to see what is impacting system performance in terms of even timing, and ASM was identified as adding 16s to every shutown.



Under \[Computer Management\]\[Event Viewer\]\[Applications and Services Logs\]\[Microsoft\]\[Windows\]\[Diagnostics-Performance\]\[Operational\], I see this for every shutdown event:

This service caused a delay in the system shutdown process:

File Name:AdaptecStorageManagerAgent

Friendly Name:

Version:

Total Time:20002ms

Degradation Time:16002ms

Incident Time (UTC):6/11/2009 3:15:57 AM





It really seems that Adaptec did not design or test the 5 series controllers for use in Workstations, this is unfortunate, for performance wise the 5 series cards really are great.





\[Update: 22 August 2009\]

I received several WD RE4-GP / WD2002FYPS drives.

I tested with W2K8R2 booted from a WD RE3 / WD1002FBYS drive connected to an Intel ICH10R controller on an Intel S5000PSL server board.

I tested 8 drives in RAID6 connected to a LSI 8888ELP controller, worked perfectly.

I connected the same 8 drives to an Adaptec 51245 controller, at boot only 2 out of 8 drives were recognized.

After booting, ASM showed all 8 drives, but they were continuously dropping out and back in.

I received confirmation of similar failures with the RE4 drives and Adaptec 5 series cards from a blog reader.

Adaptec support told him to temporarily run the drives at 1.5Gb/s, apparently this does work, I did not test it myself, clearly this is not a long term solution, nor acceptable.

I am still waiting to hear back from Adaptec and WD support.



\[Update: 30 August 2009\]

I received a reply from Adaptec support, and the news is not good, there is a hardware compatibility problem between the WD RE4-GP /WD2002FYPS drives.

"I am afraid currently these drives are not supported with this model of controller. This is due to a compatibility issue with the onboard expander on the 51245 card. We are working on a hardware solution to this problem, but I am currently not able to say in what timeframe this will come."



\[Update: 31 August 2009\]

I asked support if a firmware update will fix the issue, or if a hardware change will be required.

"Correct, a hardware solution, this would mean the card would need to be swapped, not a firmeware update. I can't tell you for sure when the solution would come as its difficult to predict the amount of time required to certify the solution but my estimate would be around the end of September."



\[Update: 6 September 2009\]

I experienced similar timeouts testing an Areca ARC-1680 controller.

Areca support was very forthcoming with the problem and the solution.

"this issue had been found few weeks ago and problem had been reported to WD and Intel which are vendors for hard drive and processor on controller. because the problem is physical layer issue which Areca have no ability to fix it.

but both Intel and WD have no fix available for this issue, the only solution is recommend customer change to SATA150 mode.

and they had closed this issue by this solution.

so i do not think a fix for SATA300 mode may available, sorry for the inconvenience."



That explains why the problem happens with the Areca and Adaptec controllers, but not the LSI, both use the Intel IOP348 processor.


