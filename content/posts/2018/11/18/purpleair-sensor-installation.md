---
title: PurpleAir Sensor Installation
date: '2018-11-19T00:16:37+00:00'
url: /2018/11/18/purpleair-sensor-installation/
categories:
- review
tags:
- purpleair
- weatherunderground
post_id: '1784'
cover:
  alt: Annotation 2018-11-18 160901
  image: /media/2018/11/annotation-2018-11-18-160901.png
---
I've had a [Ambient Weather WS-1400-IP](https://www.ambientweather.com/amws1400ip.html) weather station installed for some time, reporting to [Weather Underground](https://www.wunderground.com/personal-weather-station/dashboard?ID=KCAMANHA8). During the fires of previous years, I considered getting an air quality monitor, but I could never find anything worth the installation effort. During this year's fire season I saw several ads for [PurpleAir](https://www.purpleair.com/), advertising that they collaborate with [Weather Underground](https://www.wunderground.com/cat6/purple-airs-250-air-pollution-monitor-gives-government-equipment-run-money), so I decided to purchase and install a [PA-II](http://www.aqmd.gov/aq-spec/product/purpleair-pa-ii) outdoor sensor.

The [installation instructions](https://www.purpleair.com/install) are sparse, and the device is not really what I would call rugged or weather proof. I would not put money it on it surviving outdoors for longer than a year, specifically because of the use a vanilla Micro-USB power plug that offers no corrosion protection. The unit I received came with a Nest outdoor camera power cable, but unlike the Nest camera that uses a watertight plug, the sensor uses an open USB cable. The instructions do say to point the open USB port downwards, instead I opted to seal it in using clear silicone sealer.

The ideal installation location would have been near my [Rachio](https://www.rachio.com/) water sprinkler controller, where I have a waterproof enclosure with power, but that location is also near the HVAC, instant hot water heater, and dryer vents, so not ideal due to local air pollutants.

I installed the sensor next to my [UniFi AC Mesh AP](https://store.ubnt.com/products/unifi-ac-mesh-ap) outdoor AP, the cables do look a bit messy, and if the sensor survives long enough, I may install an enclosure to clean up the cables.


{{< gallery cols="1" >}}  
{{< figure src="/media/2018/11/20181118%5F220725726%5Fios.jpg" title="20181118\_220725726\_iOS" alt="20181118\_220725726\_iOS" >}}

{{< figure src="/media/2018/11/20181118%5F220654989%5Fios.jpg" title="20181118\_220654989\_iOS" alt="20181118\_220654989\_iOS" >}}

{{< figure src="/media/2018/11/20181118%5F220640643%5Fios.jpg" title="20181118\_220640643\_iOS" alt="20181118\_220640643\_iOS" >}}

{{< figure src="/media/2018/11/20181118%5F220630867%5Fios.jpg" title="20181118\_220630867\_iOS" alt="20181118\_220630867\_iOS" >}}

{{< figure src="/media/2018/11/20181118%5F220623193%5Fios.jpg" title="20181118\_220623193\_iOS" alt="20181118\_220623193\_iOS" >}}  
{{< /gallery >}}  

Configuring the device is reasonably simple, but a mobile app would have been easier. Power up the device, connect to it's WiFi access point, access a web page hosted by the device, configure the local WiFi SSID and password, connect to local WiFi, then register the device with PurpleAir. After all is done, I received a welcome email, and I could see the device on the PurpleAir [map](https://www.purpleair.com/map?622370|622372#11/33.8807/-118.3888).

![Annotation 2018-11-18 160901](/media/2018/11/annotation-2018-11-18-160901.png)

Next up, I have to figure out how to view combined weather and air quality data on Weather Underground, how to get a direct link to my sensor's data (the map link shows an area only), and how to use the [data](https://www.purpleair.com/sensorlist) API (I archive all my data).
