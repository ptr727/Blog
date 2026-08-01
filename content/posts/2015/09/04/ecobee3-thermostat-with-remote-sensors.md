---
title: Ecobee3 Thermostat with Remote Sensors
date: '2015-09-04T18:17:45+00:00'
url: /2015/09/04/ecobee3-thermostat-with-remote-sensors/
categories:
- review
tags:
- ecobee
- nest
post_id: '664'
cover:
  alt: Schedule
  image: /media/2015/09/schedule.png
---
We've had a particularly warm summer, for our very moderate area, and between my wife and my parent's in-law, they were constantly changing the thermostat temperature, leaving nobody particularly happy, and our electricity consumption skyhigh. I needed a better solution, I found one, but it has some quirks.

I was an early adopter of the Nest Generation 1 thermostat, and when we moved to our new house, [Nest](https://nest.com/) was still the best available, and I installed two Nest Generation 2 thermostats, one upstairs, and one downstairs.

Nest used to be an innovator and leader in the home thermostat space, and then two things happened; they were acquired by Google, and competitors like [Ecobee](https://www.ecobee.com/) and [Honeywell](http://lyric.honeywell.com/) released very competitive products. The just released [Nest Generation 3](http://amzn.to/1UpjbSD) thermostat has no new notable features, it is simply thinner, not unlike its competitors.

The one feature I, and many [other users](https://community.nest.com/ideas/1296), asked for was remote temperature sensors. In many homes, like ours, where there are two HVAC units, one for upstairs and one for downstairs, with no room specific dampers or temperature control, the upstairs and downstairs air mixes and causes large temperature differentials between closed rooms and open spaces. Adding to that warm air rises and cold air falls, so in the summer the upstairs pumps cold air downstairs, and in the winter the downstairs pumps warm air upstairs, this again leaves bedrooms too hot or too cold.

Ecobee solved this problem, to a large degree, with the [Ecobee3](http://amzn.to/1fXhI2U) thermostat, that comes with one remote sensing unit, and extra sensors can be purchased at $35 per sensor. The latest version of their thermostat is also [Apple HomeKit](https://developer.apple.com/homekit/) compatible, allowing Siri to control the thermostat.

There are 3rd party integrations that can control the Nest temperature, like [Wally](http://www.wallyhome.com/works-with-nest/) at an additional $299, or [SmartThings](https://community.smartthings.com/t/nest-thermostat-additional-temp-sensors/3282) at an additional $139, but these are integration solutions, not integrated solutions, and makes the Nest solution much more expensive, especially considering the Ecobee3 (with one extra sensor included) and the Nest Gen3 are both $249.

There are alternate solutions like [EcoVent](https://www.ecoventsystems.com/) that controls the individual vents per room, but that adds an additional $499 minimum for two rooms.

The Ecobee3 solution cannot control the temperature in each room, for that you really need a split AC unit per room, but it does allow the temperature sensing logic to take input from any number of rooms. And in my case, I am specifically interested in the temperatures in the bedrooms, not the general open areas.

Replacing the Nest with an Ecobee3 was easy, the Ecobee3 is slightly thinner than the Nest Gen2, and slightly larger, with that extra size used for a multi-color touch display.

[![Size Comparison](/media/2015/09/size-compare.jpg?w=300)](/media/2015/09/size-compare.jpg)

The remote sensors come with stands, wall screw mounts, and wall sticky tape mounts, they are pretty small and unobtrusive.

[![Sensor Size](/media/2015/09/sensor-size.jpg?w=300)](/media/2015/09/sensor-size.jpg)

The WiFi setup was really easy, and the first time I've seen this particular scheme in action, I believe it is called Wireless Accessory Configuration (WAC), not sure, Apple documentation is as always in short supply. Basically it worked like this; install the EB3 app on my iPhone, EB3 told me to connect my phone to the EB3 SSID, my phone asked me if I want to connect the device to WiFi, select yes, and the EB3 was automatically connected to my home WiFi, no passwords, no hassles, easy.

For each thermostat install the EB3 app asked me details about my house, address, size, construction, etc. This was annoying, one house, one set of details, multiple thermostats, why do I need to configure this for every thermostat. The Nest config was always very easy, one set of options per house, multiple thermostats. A call to EB support told me I need to create a group, then add the thermostats to the same group, then select what options I want to share between thermostats in the same group, and this can only be done from the web portal. This was a setup and first experience usability fail.


{{< gallery cols="1" >}}  
{{< figure src="/media/2015/09/group-config.png" title="Group Config" alt="Group Config" >}}

{{< figure src="/media/2015/09/groups.png" title="Groups" alt="Groups" >}}  
{{< /gallery >}}  

The second problem I ran into was the time configuration, the EB3 correctly selected Los Angeles as the time zone, and synced the time, but the displayed time was 3 hours ahead, East Coast time instead of Pacific Time. I fixed this by manually changing the timezone to something other than LA, saving, then changing it back to LA, and the time was correct. I did send EB support an email about this, and they replied that I need to make sure I have the correct time zone selected, right.

[![Time Zone](/media/2015/09/timezone.png?w=300)](/media/2015/09/timezone.png)

Pairing the remote sensors was really easy, stand in front of the EB3 and pull the plastic tab to let the sensor battery make contact, the EB3 detects the sensor, and lets you pair it, and enter a sensor name. The EB3 thermostat UI allowed me to use non-alpha characters, e.g. "Child **'** s Room", note the apostrophe, but when I later renamed the sensors, the mobile app and the web app restricted names to numbers and letters only, a slight inconsistency fail.

[![Sensor Naming](/media/2015/09/sensor-naming.png?w=300)](/media/2015/09/sensor-naming.png)

Configuring the schedule and comfort zones was easy and intuitive. I particularly like the concept of the comfort zones, and reusing them in the schedule, vs. the Nest's more primitive setting of desired temperatures at times of days. This is where I configured the night comfort zones to use only the sensors in the bedrooms, and ignore the temperature at the main thermostat. Made a huge difference in comfort and AC runtime.


{{< gallery cols="1" >}}  
{{< figure src="/media/2015/09/schedule.png" title="Schedule" alt="Schedule" >}}

{{< figure src="/media/2015/09/sensors.png" title="Sensors" alt="Sensors" >}}

{{< figure src="/media/2015/09/zone.png" title="Zone" alt="Zone" >}}  
{{< /gallery >}}  

After a couple days of use I noticed something weird, the AC would turn on, but the thermostats would show the current temperature is still below the set temperature. This happened with both thermostats, and only in the afternoon. The schedule only called for 74F after 8pm during the night time comfort zone, this was around 7pm, when the set temperature was 78F.


{{< gallery cols="1" >}}  
{{< figure src="/media/2015/09/temp-1.jpg" title="Temperature Downstairs" alt="Temperature Downstairs" >}}

{{< figure src="/media/2015/09/time-1.jpg" title="Time Downstairs" alt="Time Downstairs" >}}

{{< figure src="/media/2015/09/temp-2.jpg" title="Temperature Upstairs" alt="Temperature Upstairs" >}}

{{< figure src="/media/2015/09/time-2.jpg" title="Time Upstairs" alt="Time Upstairs" >}}

{{< figure src="/media/2015/09/schedule.png" title="Schedule" alt="Schedule" >}}  
{{< /gallery >}}  

Something is clearly wrong with the scheduler and the schedule. My bet was the scheduler is still using East Coast time (turned out I was wrong), Ecobee phone support was already closed, so I had to wait for the following day.

While I was looking at the System Monitor feature, very neat, I noticed gaps in the data. After a bit of research I found that Ecobee is having [scaling problems](http://www.smarthomehub.net/forums/discussion/599/official-important-ecobee-service-announcement), and their backend cannot handle the load, may be exacerbated by the Apple store kicking out Nest and now selling Ecobee3, or HomeKit integration, or poor planning. It was also weird that Ecobee does not run their own support forums, the Ecobee community supports themselves at the [SmartHomeHub](http://www.smarthomehub.net/forums/categories/ecobee) forums. One intrepid forum user created an availability graph based on his data gaps, clearly shows the recent [problems](http://www.smarthomehub.net/forums/discussion/529/help-disappearing-data-on-ecobee3).


{{< gallery cols="1" >}}  
{{< figure src="/media/2015/09/system-monitor-gaps.png" title="System Monitor Gaps" alt="System Monitor Gaps" >}}

{{< figure src="/media/2015/09/availability.png" title="Availability" alt="Availability" >}}  
{{< /gallery >}}  

I called Ecobee support, and they explained what was going on with the schedule; the thermostat has a feature called [Smart Recovery Mode](https://www.ecobee.com/faq/what-is-the-smart-recovery-heat-cool-function-should-i-leave-these-set-to-the-default-on-setting/), in this mode the AC starts running before a schedule change in an attempt to reach the desired temperature when the schedule starts. And that this prediction takes a week or so to become more accurate, and that it can be impacted by fluctuations in the weather. Ok, makes sense, but usability fail by not making this behavior clear in the status UI.

[![Smart Recovery](/media/2015/09/smart-recovery.png?w=300)](/media/2015/09/smart-recovery.png)

As for the gaps in data, Ecobee support said they are busy migrating data, that this impacts backend performance, and that all systems should be operational in a week, and no data should be lost, slight contradiction to the post on the SmartHomeHub forum, but at least acknowledged.

I am pretty happy with the E3, the remote sensors really do make a big difference in efficiency.

\[Update: [WiFi troubles with the E3](/2016/01/30/ecobee3-wifi-connection-troubles/)\]
