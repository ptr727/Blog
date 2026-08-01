---
title: UPS Battery Replacement Turns Into Unrecoverable Firmware Update
date: '2016-10-15T02:09:32+00:00'
url: /2016/10/14/ups-battery-replacement-turns-into-unrecoverable-firmware-update/
categories:
- power
- problem
tags:
- apc
post_id: '920'
cover:
  alt: apc-3
  image: /media/2016/10/apc-3.png
---
As the saying goes, if it is not broken do not fix it, especially when it comes to firmware.

I have a couple [APC Smart-UPS](http://www.apc.com/smartups/)'s at my house, same as the models I like to use at the office. I use the [SMT750](http://amzn.to/2eq5PHJ) models with [AP9631](http://amzn.to/2e8ppnk) [Network Monitoring Cards](http://www.apc.com/shop/us/en/categories/power/uninterruptible-power-supply-ups-/ups-management/ups-network-management-cards/_/N-1x4urig). The problem started when we had a short power outage, and the UPS that powers the home network switch, cell repeater, alarm internet connection, and PoE IP cameras, unexpectedly died. A battery replacement led to the opportunity to do a UPS firmware update, which led to an unrecoverable firmware update.

It started when I woke up one morning and it was obvious the power had been out, first indicator is the kitchen appliances have blinking clocks, second are the numerous power failure email notifications, and the emails that stood out were from the alarm system that says it lost power and internet connectivity. The alarm has it's own backup battery, the network switches and FiOS internet have their own battery backups, and the outage was only about 4 minutes.  So how is it that the UPS died, killing the switch, disconnecting the internet, especially when the outage was only 4 minutes, and typical runtimes on the UPS should be about an hour?

Here is the UPS outage log produced by the NMC card:

\[code gutter="false"\]10/11/2016 06:53:05 Device UPS: A discharged battery condition no longer exists. 0x0108
10/11/2016 06:12:27 Device UPS: The battery power is too low to support the load; if power fails, the UPS will be shut down immediately. 0x0107
10/11/2016 06:12:24 Device UPS: Restored the local network management interface-to-UPS communication. 0x0101
10/11/2016 06:12:12 System Network service started. IPv6 address FE80::2C0:B7FF:FE98:9BAF assigned by link-local autoconfiguration. 0x0007
10/11/2016 06:12:10 Device Environment: Restored the local network management interface-to-integrated Environmental Monitor (Universal I/O at Port 1) communication. 0x0344
10/11/2016 06:12:09 System Network service started. System IP is 192.168.1.11 from manually configured settings. 0x0007
10/11/2016 06:12:02 System Network Interface coldstarted. 0x0001
10/11/2016 05:45:36 Device UPS: A low battery condition no longer exists. 0x0110
10/11/2016 05:45:36 Device UPS: The battery power is too low to support the load; if power fails, the UPS will be shut down immediately. 0x0107
10/11/2016 05:45:35 Device UPS: The output power is turned off. 0x0114
10/11/2016 05:45:35 Device UPS: The graceful shutdown period has ended. 0x014F
10/11/2016 05:45:35 Device UPS: No longer on battery power. 0x010A
10/11/2016 05:45:35 Device UPS: Main outlet group, UPS Outlets, has been commanded to shutdown with on delay. 0x0174
10/11/2016 05:45:35 Device UPS: The power for the main outlet group, UPS Outlets, is now turned off. 0x0135
10/11/2016 05:45:18 Device UPS: The battery power is too low to continue to support the load; the UPS will shut down if input power does not return to normal soon. 0x010F
10/11/2016 05:41:36 Device UPS: On battery power in response to rapid change of input. 0x0109\[/code\]

I could see from the log that the UPS battery power ran out within 4 minutes, 05:41:36 on battery, 05:45:18 battery too low, 05:45:35 output turned off. The UPS status page was equally puzzling, load was at 9.7%, yet reported runtime was only 5 minutes, impossible.

Here is the status screenshot:

![apc-1](/media/2016/10/apc-1.png)

I ran a manual battery test, the test passed, but from the log it was clear the battery failed. I have bi-weekly scheduled battery tests for all UPS's, never received a failure report. So what is the point of a battery test if the test comes back no problem yet it is clear to me from the logs that the battery failed?

Here is the log:
\[code gutter="false"\]10/11/2016 18:07:06 Device UPS: A low battery condition no longer exists. 0x0110
10/11/2016 18:07:06 Device UPS: The battery power is too low to support the load; if power fails, the UPS will be shut down immediately. 0x0107
10/11/2016 18:07:05 Device UPS: Self-Test passed. 0x0105
10/11/2016 18:06:59 Device UPS: A discharged battery condition no longer exists. 0x0108
10/11/2016 18:06:59 Device UPS: The battery power is too low to continue to support the load; the UPS will shut down if input power does not return to normal soon. 0x010F
10/11/2016 18:06:58 Device UPS: Self-Test started by management device. 0x0137
10/11/2016 18:06:56 Device UPS: The battery power is too low to support the load; if power fails, the UPS will be shut down immediately. 0x0107\[/code\]
I asked for advice on the [APC forum](http://forums.apc.com/spaces/5/smart-ups-symmetra-lx-rm/forums/general/13112/very-low-runtime-on-low-load-ups-compared-to-similar-model-with-high-load), no reply yet, and I ordered a replacement [RBC48](http://amzn.to/2dQQywl) battery. I received the battery, installed it, and the reported runtime is back to normal, 1 hour 48 minutes.

Here is a status screenshot with the new battery:

![apc-2](/media/2016/10/apc-2.png)

Here is where I should have stopped and called it a day, but no. I knew that the UPS's were on old firmware, and I decided to use this opportunity to update the firmware. I'd normally let firmware be, unless I have a good reason to update, but I convinced myself that the new firmware readme had some fixes that may help with the false pass on the battery test:
\[code gutter="false"\]Release Notes (UPS09.3):
========================
2\. Improved self-test logging for PCBE / NMC.
11\. Repaired an occasional math error in the battery replacement date algorithm that resulted in incorrect dates.\[/code\]
I update the UPS, where I just replaced the battery, [instructions](http://www.schneider-electric.us/en/faqs/FA170679/) are pretty simple. Only hassle is I have to bypass the network equipment to be mains powered so I can turn the UPS outputs off while updating the firmware, while maintaining network connectivity.

I did the same for my office UPS, PC and office switch on mains power, and when I power down the output, I made sure to not notify [PowerChute Network Shutdown](http://www.apc.com/shop/us/en/categories/power/ups/ups-management/powerchute-network-shutdown/_/N-auzzn7) (PCNS) clients, as my PC had the PowerChute client installed to receive power state via the network. I start the firmware update over the network, and a few seconds later I get a Windows message that shutdown had been initiated by PCNS, what? I sit there in frustration, nothing to do but watch my PC shutdown while it is still delivering the firmware update.

On rebooting my PC, NMC comes up, but reports the UPS has stopped communicating. I pull AC power from the UPS, no change, I also pull the batteries, and when I plug the batteries and mains back on, beeeeeeeeeep. NMC now reports no UPS found, the UPS LCD panel reports all is fine. And still beeeeeeeeeep, and no way to stop the beeeeeeeeeep.

Here is the NMC status page:

![apc-3](/media/2016/10/apc-3.png)

I try to do [Firmware Upgrade Wizard](ftp://178.165.81.38/firmware/APC/FA164737_EN_US_31.0.pdf) update via USB, plug a USB cable in, PC sees UPS, reports critical condition, but the upgrade wizard reports no UPS found on USB.

Here is the wizard error page:

![apc-4](/media/2016/10/apc-4.png)

So, here I am, stuck with a bricked UPS, lesson learned, actually two lessons learned; do not trust scheduled battery tests, and leave working firmware be!
