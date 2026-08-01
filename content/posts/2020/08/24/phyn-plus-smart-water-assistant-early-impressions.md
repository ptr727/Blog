---
title: Phyn Plus Smart Water Assistant - Early Impressions
date: '2020-08-25T04:03:13+00:00'
url: /2020/08/24/phyn-plus-smart-water-assistant-early-impressions/
categories:
- review
tags:
- water
post_id: '2116'
cover:
  alt: IMG_6641
  image: /media/2020/08/img_6641.jpg
---
[Phyn Plus](https://www.phyn.com/plus-smart-water-assistant/) is a "smart water assistant", a device that monitors water usage, and can automatically shut off the water supply when a leak is detected.

I am familiar with whole house water monitoring and leak detection devices, like the widely available and advertised [Moen Flo Smart Water Shutoff](https://meetflo.com/product/smart-water-shutoff), but until very recently I've never even heard of [Phyn](https://www.phyn.com/). I was introduced to Phyn by a tech savvy friend that bought one at [Costco](https://www.costco.com/phyn-plus-smart-water-monitor-with-whole-home-leak-detection-and-auto-shutoff.product.100490249.html), installed it at his house, and he had only good things to say about it.

What made Phyn interesting to me was that Phyn is to water what [Sense](https://sense.com/) is to electricity. Phyn uses machine learning to [analyze](https://www.phyn.com/technology/) water flow and pressure measurements to automatically identify individual water consuming devices, just like Sense uses machine learning and current and voltage measurements to [identify](https://blog.sense.com/articles/training-sense/) individual electrical appliances.

From what I [read](https://www.prnewswire.com/news-releases/phyn-announces-12m-additional-investment-from-joint-venture-partners-belkin-international-and-uponor-300847074.html) Phyn is a joint venture between [Belkin](https://www.belkin.com/us/p/P-PHNSWA01/) and [Uponor](https://www.uponor-usa.com/en), and the flow sensor is manufactured by [Badger Meter](https://www.badgermeter.com/). Like any cool gadget from an unknown entity, there is always a chance that the device may not live long, or even if the device keeps working, the cloud service may go offline, but when I recently had to do maintenance to my instant hot water heater and plumbing, I took the plunge and had one installed while the plumbing was being fixed. My local Costco store does not stock them, but as of writing Costco [online](https://www.costco.com/phyn-plus-smart-water-monitor-with-whole-home-leak-detection-and-auto-shutoff.product.100490249.html) sells them cheaper compared to [Amazon](https://amzn.to/2Qoa1HO) or Phyn direct.

When I initially read about the Moen Flo and other such devices, none supported supply lines larger than 3/4", and since my supply line from the city is 1 1/2" copper, I was reluctant to install a flow restrictive device. Phyn Plus [supports](https://www.phyn.com/media/phyn-installation.pdf) "up to" 1 1/4" and Moen Flo supports "up to" 1 1/2" supply lines. With Phyn yet to release their [XL](https://www.phyn.com/phyn-xl-15/) product line that will support 1 1/2" and 2" lines. My home water supply from the city is 1 1/2", but after tapping the fire sprinklers and irrigation system, it is reduced to 1" feeding the water filter and conditioners. The actual internal diameter of the Phyn Plus is only around 5/8", so quite a stretch to claim support for "up to" 1 1/4" lines.

My outdoor plumbing will require significant rerouting to allow monitoring of the home and irrigation system, while leaving the fire sprinklers directly connected, so I opted to install right before the water filters and conditioners, monitoring the inside of the house only. The Phyn Plus is supplied with 1" female NPS to 3/4" male NPT [adapters](https://www.supplyhouse.com/Bluefin-WMC075-3-4-Male-NPT-x-1-NPSM-Water-Meter-Coupling-Lead-Free), but instead of further reducing the flow with a 3/4" connector to my 1" plumbing, I opted to use 1" NPS to 1" CTS John Guest [adapters](https://amzn.to/3gp9wIb) to minimize flow reduction.

![](/media/2020/08/img_6637.jpg)

![](/media/2020/08/img_6620.jpg)

Physical installation was straightforward, I had the plumber install Phyn in-line before the water filter while they were rerouting plumbing to fix the instant hot water heater. If you are reasonably adept at pipe plumbing, self-installation should be easy. I have noticed reduced water flow when multiple showers are used at the same time, but using a single shower seems about the same. Your experience may differ, as I may or may not have removed the flow restrictors required by CA code from our shower heads.

![](/media/2020/08/img_6628.jpg)

![](/media/2020/08/img_6640.jpg)

![](/media/2020/08/img_6641.jpg)

Configuring the mobile app on iOS was easy, following a typical pattern of create account (no support for 3rd party auth), connect phone to the device WiFi access point, then configure WiFi settings, and the device connects to home WiFi. After completing information asking about my home and the installed fixtures and appliances, and performing a device firmware upgrade, I was prompted to perform a plumbing check. I did an "extended" plumbing check that took about 15 minutes, during which time the Phyn cut the water supply, and monitored pressure downstream, looking for a drop in pressure signifying a possible leak, no problems detected.

During water use the app presents water use events and tries to match the event with the configured fixtures and appliances. For every event you have the ability to override the automatic classification, and this is what Phyn uses for training. The app was reasonably successful at identifying fixtures and toilets, but not so successful at identifying the washing machine, showers, or tubs. The docs do state that Phyn needs more than a thousand events before accuracy improves, and I've yet to reach that milestone after less than a week of use.

During use I did encounter two alerts, both alerts were high flow rate events, both when running multiple showers at the same time. On alert the app pops a notification and asked me to classify the event as an issue or not, and if not an issue, what fixture was in use. The app does not offer the ability to specify when multiple fixtures were in use, so I had to select "a" shower. I do suspect there is a bug in the app, as the alert history shows a slow flow event, quite the opposite of what happened.

![](/media/2020/08/img_6636.png)

![](/media/2020/08/img_6635.png)

![](/media/2020/08/img_6634.png)

![](/media/2020/08/img_6633.png)

![](/media/2020/08/img_6631.png)

![](/media/2020/08/img_6639.png)

I was very disappointed to learn that there is no ability to download water usage data, no data access REST API, and no web portal. I know in a mobile first world web portals may be an afterthought for interactivity, but I much prefer a big screen and easy reading when looking at data, something very difficult to do on a little phone screen. Per Phyn support there are no plans for data download, no API access, and no consumer web portal.

I integrate everything I can measure at my house into [Home Assistant](https://www.home-assistant.io/), and if I'd known there was no way for me to access my own data, I may not have installed Phyn. But, it is too soon to say if I'd be uninstalling it simply because it keeps my data hostage.

_Update - 20 January 2025_:  
I discovered a [Phyn integration for Home Assistant](https://github.com/jordanruthe/homeassistant-phyn) does exist. Looks like it was created around January 2023, after I had long given up on using Phyn in HA. Do note that the original integration, the one currently found in HACS, appears to be abandoned, but the form I linked is currently being maintained.
