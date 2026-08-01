---
title: Ecobee3 WiFi Connection Troubles
date: '2016-01-30T17:39:45+00:00'
url: /2016/01/30/ecobee3-wifi-connection-troubles/
categories:
- research
- review
tags:
- ecobee
- ubiquity
- xclaim
post_id: '722'
---
In a previous [post](/2015/09/04/ecobee3-thermostat-with-remote-sensors/) I wrote about my transition from [Nest](http://amzn.to/1UpjbSD) to [Ecobee3](http://amzn.to/1fXhI2U) thermostats, and how the biggest benefit of the E3 was the use of remote sensors.

After several months of use, winter and summer, I find the remote sensors really do work very well, and our bedrooms remain at the desired temperature, while the areas around the thermostats can be warmer or colder.

But, the E3 is not perfect, there are two recurring problems; the remote sensors would report offline, and the units would lose network connectivity.

I've received sensor offline alerts a couple of times, typically happens early mornings, maybe interference, don't know, the sensors never move from where they are placed.

Every time a I get a sensors offline report, the sensor already restored connectivity. This behavior is very annoying, I will get two emails a minute apart, and the E3 UI will have an alert saying sensor offline, I click ok, and then immediately an alert saying sensor online.

![E3.Sensor.Email](/media/2016/01/e3-sensor-email.png)

I expect the E3 to have some sort of grace period before it deems a problem so important that it needs to notify me. As is, it is just an annoyance as there is no remediation action to take.

The second problem is the E3 loses network connectivity, this is a real problem, as the units remain offline until power cycled, and to power cycle the E3 has to be removed from the wall bracket, i.e. there is no reboot menu option.

I reported this problem to Ecobee support in October, and on the [SmartHomeHub](http://www.smarthomehub.net/forums/discussion/662/wifi-disconnect-requiring-power-cycle-to-restore-connectivity) community forum. Yes, it is a bit pathetic that Ecobee does not have their own support community forum. Ecobee had me reserve static IP's in the DHCP server, setup a dedicated 2.4GHz SSID, still disconnects. By December the problem was still happening, and Ecobee support escalated the problem to their development team, it is two months later, and still no updates from Ecobee support on the problem.

![E3.Log](/media/2016/01/e3-log.jpg?w=285)

Through my own research and experimentation I suspect the problem to be that the E3 is unable to handle a WiFi channel change, and unable to roam between access points. There are some conditions that trigger the problem that I cannot explain.

I have multiple access points in my house, same SSID, different channels, 2.4GHz and 5GHz bands. I tested with [Ubiquity UniFi AC](http://amzn.to/1VxyQeK) and with [Ruckus/Xclaim Xi-3](http://amzn.to/1OX9ANo). And in case you're wondering, no other devices in my house have any problems with WiFi, even with dynamic channel selection.

I can make the E3 fail by either changing the AP channel, or by making it roam to a different AP, also changing channels. If I configure the AP's to use auto channel selection, then the E3 will fail as soon as the AP chooses to change channels (UniFi does this on startup, Xclaim does this [dynamically](https://www.ruckuswireless.com/technology/channelfly)). If I manually change the AP channel, the E3 will fail. If I take one AP offline, the E3 will fail to roam to a different AP (on a different channel).

Even with my AP's configured with static non-overlapping channels, the E3 would still sometimes fail, requiring a power cycle. I do not know why this would happen, as signal strength by the E3's are perfect.

On the plus side, the E3 units remember the schedule, and even when offline, they continue to operate.

Bottom line is E3 WiFi is not reliable, and E3 support/dev is not responsive.
