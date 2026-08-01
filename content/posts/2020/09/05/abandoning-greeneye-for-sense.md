---
title: Abandoning GreenEye for Sense
date: '2020-09-05T23:30:28+00:00'
url: /2020/09/05/abandoning-greeneye-for-sense/
categories:
- power
- review
tags:
- greeneye
- sense
post_id: '2154'
cover:
  alt: IMG_6706
  image: /media/2020/09/img_6706.jpg
---
I planned whole a house energy monitoring setup when we built our house. But in all these years I never completed the [Brultech GreenEye](https://www.brultech.com/greeneye/) installation, I officially called that plan abandoned, and instead installed [Sense](https://amzn.to/3h4IWEG) energy monitors.

First a bit of a history, skip to the end if you're not interested in my procrastination journey.

I installed my first energy monitor, circa 2009, a [The Energy Detective TED-5000](http://www.theenergydetective.com/) connected to [Google PowerMeter](https://en.wikipedia.org/wiki/Google_PowerMeter).

![](/media/2018/08/ted-dashboard.png)

![](/media/2018/08/ted-graphing.png)![](/media/2018/08/5000cimage_2.jpg)

Although our power utility ([SCE](https://www.sce.com/)) had installed [smart meters](https://www.sce.com/wps/portal/home/customer-service/my-account/smart-meters/), it took them several years, circa 2012, to enable [Home Area Networks](https://www.sce.com/wps/portal/home/residential/rebates-savings/hanlogin/) (HAN). I installed an [EnergyHub](http://www.energyhub.com/) [Home Base](http://www.energyhub.com/blog/energyhub-system-now-available-for-purchase), that turned out to be too unreliable due to the too long distance for ZigBee from the meter to our condo. I ordered the starter kit, that also included an energy monitoring power strip, but the power strip was unusable due to the excessive loud high frequency noise it generated.

![](/media/2018/08/energyhub_powerstrip_web.jpg)![](/media/2018/08/homebase-front.png)

![](/media/2018/08/sce_smartmeter.jpg)

We started construction on our new house, circa 2012, and I made provision for power, water, and gas consumption monitoring. My research showed several potential candidates for whole house energy monitoring, and I narrowed it down to the following products; [Smart Energy Groups](https://smartenergygroups.com/) [SEGMeter](http://shop.smartenergygroups.com/store/show/segmeter_v25), [Open Energy Monitor](https://openenergymonitor.org/) [emonTx](https://openenergymonitor.com/emontx-v3-electricity-monitoring-transmitter/), and [Brultech](http://www.brultech.com/) [Green Eye Energy Monitor](http://www.brultech.com/greeneye/).

![](/media/2018/08/fully_loaded_more_side.jpg)

![](/media/2018/08/0259f9ed4a48dc5db5d79abacb44a434.jpg)

![](/media/2018/08/gem_nocover.png)

I opted for the Green Eye Energy Monitor (GEM); it was a commercial product, with an active user community, that supported 4 pulse sensors (for gas and water) and 32 current sensors, and ethernet connectivity (or RS232 or ZigBee or WiFi).

Our house has 400A service, with two 200A subpanels, and each panel has 42 breakers. Since the GEM only supported 32 circuits, I installed two GEM units, in recessed utility cabinets, near each panel, and ran a conduit between the electrical panel and the utility cabinet. This is where the long delay started; the electrician was reluctant to install the current transformers, the city inspector had no idea if it was allowed by code, and I did not want to cause undue delays or wasted installation effort, so I simply left the GEM's disconnected, and closed the panels in order to pass inspection.

![](/media/2018/08/20180811_172657174_ios.jpg)![](/media/2018/08/20180811_172632361_ios.jpg)

![](/media/2018/08/20180811_172609507_ios.jpg)

Another problem was the city utility water and gas meters, where I was not allowed to attach any type of device, not even an optical sensor, to the meters. The water meter was by the street, so even if I wanted to, I could not easily monitor it. I had to install my own dry contact pulse output gas and water meters inline with the utility meters, and to pass code, my meters had to be the same model as the utility installed meters, making it expensive. The water meter is a [Neptune T-10](https://www.neptunetg.com/products/watermeters/residential/t10/) 1½” Direct Read with a Tricon/S. The gas meter is an [Elster American Meter AC630](https://www.elster-americanmeter.com/en/product-details/88/en/AC-630) with a Digital Pulser.

![](/media/2020/08/img_6638.jpg)

![](/media/2018/08/20180811_180521052_ios.jpg)

After we moved in, I endeavoured to install the current transformers, but I found the wire leads were [too short](https://www.brultech.com/community/viewtopic.php?f=29&t=507) to go from the electrical panel to the GEM's. The leads are about 5' in length, but the total required length between my electrical panels and utility panels is about 11' at the furthest point. I really don't understand if the short leads is a cost saving measure, or if there is not demand for longer leads. Either way, I would be happy to pay more for longer wires vs. having to extend 2 x 48 x 2 = 192 wires by hand, and looking at the [forum](https://www.brultech.com/community/), I'm not the only person with this problem. This effort further delayed the installation.

I eventually decided to run multi-pair CAT3 cables between the panels, connect the CAT3 and current sensor leads with terminal blocks, and safeguard the terminal blocks in plastic enclosures. I was concerned about the cable thickness, and if I'd be able to pull the cable through the connecting conduit, so I ordered various types of 12-, 25-, and 50-pair CAT3 cable samples. In retrospect, fitting all the leads in one 1" conduit may have been a problem even if the CT leads were long enough.

While I waited for the CAT3 cable samples, I started setting up one of the GEM's with a pair of CT's for testing. The software configuration turned out to be frustratingly confusing, with the instructions and screenshots in the manuals not matching the current version of the tools, and documented configuration settings no longer being accurate. It took trial and error, and back and forth with support, to get the GEM updated and configured.

The firmware updates were particularly frustrating, e.g. the baud rate needs to be lowered else the update fails, why does the tool not lower the baud rate by itself, or the update added support for a password, and instead of setting the password to a known value, I have to do a complex password reset by means of button pushes timed with flashing LED's.

The UX of the tools are indicative of engineers writing tools for themselves vs. their customers.

![](/media/2018/08/2018-08-19.png)

![](/media/2018/08/2018-08-19-1.png)

Once I had the GEM updated, and it was producing measurement data, I wanted to configure it to directly post data to the [Open Energy Monitor](https://openenergymonitor.org/) [emonCMS](https://emoncms.org/) service. The [configuration](http://www.brultech.com/community/viewtopic.php?t=1577) steps did not work, and neither the GEM nor the cloud hosted emonCMS provided any means of debugging or troubleshooting help.

I resorted to troubleshooting the HTTP traffic, comparing my observations with the emonCMS [API](https://emoncms.org/site/api#input) documentation. I use a [Ubiquity UniFi Security Gateway](https://www.ubnt.com/unifi-routing/unifi-security-gateway-pro-4/), and with a bit of [SSH](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html) and [tcpdump](http://www.tcpdump.org/) magic, I could observe router traffic from [WireShark](https://www.wireshark.org/) running on my Windows 10 workstation.

```
plink.exe -ssh admin@192.168.1.1 -pw secret "sudo tcpdump -ni eth0 -s 0 -w - not port 22" | "C:\Program Files\Wireshark\Wireshark.exe" -k -i -
```

When I took the first captures I was confused by the many errors and partial traffic, a bit of head scratching, and I realized I have to disable hardware offload on the router, and the streams cleared up. Once I filtered out the HTTP traffic, the problem was clear, the GEM was creating an incorrectly formed HTTP GET request. The config UI calls for a URL, but the code prepends HTTP://, so the edit field needs to be a FQDN only.

![](/media/2018/08/packet.png)

![](/media/2018/08/data.png)

![](/media/2018/08/httphttp.png)

![](/media/2018/08/hardwareoffload.png)

![](/media/2018/08/badrequest.png)

I received my multi-pair CAT3 samples, and more so than ever it looked like a lot of effort to get all the current sensors hooked up, time passed, always easy to do nothing.

I abandoned the idea of using emonCMS, and since I adopted [Home Assistant](https://www.home-assistant.io/) (HA) for my home automation needs, I wanted to connect my GEM's to HA. Fortunately there was a GEM [integration](https://www.home-assistant.io/integrations/greeneye_monitor/) for HA, but I could not get it to work reliably when using multiple GEM units. I did some troubleshooting by writing a GEM network [test tool](https://github.com/ptr727/GEM-Echo-Server), and it became clear that reliable operation requires both the GEM [firmware](https://www.brultech.com/software/files/checksn/3/1) and the [WIZ110SR](https://www.wiznet.io/product-item/wiz110sr/) TCP to Serial bridge [firmware](https://www.wiznet.io/product-item/wiz110sr/) to be up to date, and specifically configured. With a stable hardware platform, the author of the GEM HA integration assisted and rewrote the code to support multiple GEM units.

![](/media/2020/09/annotation-2020-09-05-133711.png)

![](/media/2020/09/annotation-2020-09-05-133649.png)![](/media/2020/09/annotation-2020-09-05-133622.png)

By now I had abandoned the idea of wiring all those GEM current sensors, and I was looking for alternatives.

If I could build today, I may go for a panel-integrated solution from [Leviton](https://www.leviton.com/en/products/residential/load-centers), [Eaton](https://www.eaton.com/us/en-us/markets/innovation-stories/energy-management-circuit-breaker.html), or [ABB](https://electrification.us.abb.com/products/panelboards/series-ii-branch-circuit-monitoring). I do anticipate US home building code for energy efficiency eventually catching up to European high standards, e.g. watch [Grand Designs](https://www.channel4.com/programmes/grand-designs) on [Netflix](https://www.netflix.com/title/80160755), and I anticipate home energy management systems of the future will look more like commercial building energy management systems of today, but readily available and affordable.

On the open source front, the general availability of integrated power metering devices, like the [ATM90E32AS](https://www.microchip.com/wwwproducts/en/atm90e32as), have made devices cheaper and more capable, and the [CircuitSetup Expandable 6 Channel ESP32 Energy Meter](https://github.com/CircuitSetup/Expandable-6-Channel-ESP32-Energy-Meter) is one of my favorite designs.

I run a [Fluke VR1710](https://www.fluke.com/en-us/product/electrical-testing/power-quality/vr1710) power quality monitor at my house, and I really would like to see more open source power quality monitoring projects. The only active open source power quality monitoring project I am aware of, is the [Open Power Quality Project](https://openpowerquality.org/) from the University of Hawaii. Their hardware [project](https://github.com/openpowerquality/opq/tree/master/box) uses an [AMC1100](https://www.ti.com/product/AMC1100) isolation transformer with a [AD7684](https://www.analog.com/en/products/ad7684.html) ADC for signal analysis.

I decided to forego the installation complexity of per-circuit monitoring, and opted to install two [Sense](https://sense.com/) energy monitors, one [with solar](https://amzn.to/354T9i2) monitoring, and one [without](https://amzn.to/3h4IWEG). Like the [Phyn Plus](/2020/08/24/phyn-plus-smart-water-assistant-early-impressions/) does for water, the Sense uses [machine learning](https://blog.sense.com/articles/training-sense/) to identify individual electrical loads by means of signal analysis. I've been aware of Sense for a number of years, and a detractor had always been the lack of 400A circuit support.

My home uses a 400A split circuit, with the 400A feed split into two 200A breaker panels. Sense only recently added support for [400A circuits](https://help.sense.com/hc/en-us/articles/360048974514-Installing-Sense-with-400A-Split-Service), but they use the solar port for the second 200A circuit. This still won't work for me, as I have solar and 400A, so I either need support for three sets of current sensors, or a current sensor that is rated for 400A. Like many other users with a similar configuration I opted to install two Sense units, one with Solar for one panel, and one without solar for the other panel. The downside is that you need two separate Sense accounts. Some users do report installing the 200A rated current clamp around the 400A feed, but this requires the electrical supplier to agree to the installation, and open the restricted supply side panel, and the clamp to fit around the wires, and general usage to not exceed 200A to avoid clipping.

The Sense device requires a 240V double breaker to monitor each of the 120V legs. My one panel had space for a double breaker, my other panel was already full, and required the use of a quad breaker. My panels are Murray brand, acquired by Siemens, so for convenience I bought two Siemens [Q22020CT](https://amzn.to/3budPRE) triple circuit breakers. To my surprise it did not fit, and I learned the hard way about [Rejection Clips and Circuit Total Limitation (CTL)](https://en.wikipedia.org/wiki/Circuit_total_limitation). Long story short, some panels allow double breakers on one circuit, others don't, and some panels allow doubles on some locations only, limiting the total number of circuits per panel. The Q22020CT has rejection clips, while the model without rejection clips is Q22020NC, and is apparently no longer being manufactured. My local electrical supplier offered an easy solution, use two double breakers with a connecting breaker clip.

![](/media/2020/09/img_6665.jpg)

![](/media/2020/09/img_6668.jpg)

![](/media/2020/09/img_6675.jpg)

I picked one of the hottest days of the year to install the two Sense units, I know, not 'sens'ible, but I did it early morning and it took me less than an hour to install both panels. I installed the antennas of both units in the wall of the recessed panels, the upstairs panel is near an access point and has good signal, while the downstairs panel currently has poor signal. During onboarding, the Sense app reported the WiFi signal as low, but speed as sufficient, so I may add another [AUP-AC-M](https://amzn.to/3i4DD9o) access point in the garage if the Sense reports ongoing signal issues.

While the panels were open I double checked all the breakers, and I was surprised, and concerned, to find that several high current breakers, like the electrical oven, AC compressors, and solar inverter, had loose connections. Several of the loose screws were on multi-strand wire, so I don't know if they were never properly torqued, torqued too tight cutting strands, or loosened over time.

![](/media/2020/09/img_6692.jpg)

![](/media/2020/09/img_6693.jpg)![](/media/2020/09/img_6695.jpg)

![](/media/2020/09/img_6703.jpg)

![](/media/2020/09/img_6706.jpg)

![](/media/2020/09/img_6705.jpg)

It is really unfortunate that I need to run two Sense accounts, it is not just inconvenient, but it also means that the network based device discovery may not work, as the same network is seen by both devices, but equipment is only connected to one of the monitored panels. I do hope that Sense will either support combining of multiple Sense devices under a single account, or release a new device with support for three current sensors (solar + 200A + 200A).

Update: I followed advice from the Sense community forum; I confirmed my total load has never exceeded 200A / 24KW, and installed the CT's on the 400A supply side, alleviating the need for a 2nd Sense unit. I drilled a hole between the user and utility side, installed a rubber grommet, and ran the primary CT's to the utility side. Secondary CT's are still on solar, and I uninstalled the 2nd Sense unit. So far so good.

I am still in the process of converting the gas and water meter pulse counters from the GEM's to an [ESP32](https://amzn.to/3jOfAMw) with [ESPHome](https://esphome.io/), and I'll report on that later.

It has only been a few hours of runtime, and my Sense units are still learning, so I'm eager to see what they discover.

![](/media/2020/09/img_6710.png)

![](/media/2020/09/img_6711.png)
