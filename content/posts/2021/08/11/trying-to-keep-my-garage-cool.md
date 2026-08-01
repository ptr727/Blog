---
title: Trying to Keep my Garage Cool
date: '2021-08-11T14:11:19+00:00'
url: /2021/08/11/trying-to-keep-my-garage-cool/
categories:
- homeautomation
tags:
- esphome
- homeassistant
post_id: '2357'
cover:
  alt: IMG_8173
  image: /media/2021/08/img_8173.jpg
---
We live in a moderate climate, and when we built our house my plans were for my home server rack to be installed in the garage and vented through the outside wall to the alley. Unfortunately plans changed, and the instant hot gas water heater had to be moved blocking rack access to outside ventilation. Without cool outside air the servers complain about overheating in the peak of summer, and I either need to power down or keep the garage door open during the day.

I do have a [Panasonic WhisperGreen](https://amzn.to/2VDSRwo) ventilation fan in the garage ceiling, but it is just not cutting it when hot cars are parked in the garage. I've been looking for ready-built solutions, like [louvered extractor fans](https://amzn.to/3jJdK0X), but they would require cutting into stucco walls, that I know are filled with electrical cables coming from the home automation load controller.

As an alternative I decided to build air intake fans mounted to the existing air ventilation slots in the alley door and lower wall. I chose to use [AC Infinity AXIAL S1238](https://amzn.to/3CABqNI) 120x38mm 120V AC fans. I would have liked to use larger fans, but the 120mm fans were a good fit for a 3x1 grid to cover the wall vent, and a 3x2 grid to cover the door vent.

For mounting I considered wood, extruded aluminium (aluminum) or nylon plastic sheeting, but considering the fabrication effort I opted to 3D print the parts using PETG and my [Prusa Mk3S](https://www.prusa3d.com/original-prusa-i3-mk3/) printer. I used [Fusion 360](https://www.autodesk.com/products/fusion-360/overview) to design all the necessary mounting brackets and flanges, and with a few revisions had a perfect fit.


{{< gallery cols="3" >}}  
{{< figure src="/media/2021/08/door-vent-fan-array-v2.png?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2021/08/wall-vent-fan-array-v4.png?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2021/08/edge-flange-v7.png?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2021/08/edge-flange-door-v6.png?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2021/08/edge-connector-v11.png?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2021/08/center-edge-connector-v3.png?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2021/08/corner-flange-v7.png?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2021/08/corner-flange-door-v6.png?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2021/08/center-edge-flange-door-v6.png?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2021/08/center-connector-v14.png?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2021/08/center-connector-no-wings-v2.png?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2021/08/corner-connector-v11.png?w=1024" alt="" caption="" >}}  
{{< /gallery >}}  

I thermostatically control the fans using a [Sonoff TH10](https://amzn.to/37zEWd6) with a Dallas DS18B20 temperature sensor running [ESPHome](https://esphome.io/).

```
climate:

  - platform: thermostat
    name: ${device_name}_thermostat
    id: thermo
    sensor: temp
    # default_mode: COOL
    default_target_temperature_high: ${target_temperature_high}
    cool_action:
      - logger.log: "Thermostat : Cool Action, Turning Relay On."
      - switch.turn_on: relay
    idle_action:
      - logger.log: "Thermostat : Idle Action, Turning Relay Off."
      - switch.turn_off: relay
    visual:
      min_temperature: 20.0
      max_temperature: 40.0
      temperature_step: 0.5
```

My [Home Assistant](https://www.home-assistant.io/) view of my garage sensors:

{{< figure src="/media/2021/08/fireshot-pro-webpage-screenshot-033-overview-home-assistant-home-assistant.home%5F.insanegenius.net%5F.png?w=1024" alt="" caption="" >}}

The finished product:


{{< gallery cols="3" >}}  
{{< figure src="/media/2021/08/img%5F8164.jpg?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2021/08/img%5F8169.jpg?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2021/08/img%5F8165.jpg?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2021/08/img%5F8167.jpg?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2021/08/img%5F8177.jpg?w=768" alt="" caption="" >}}  
{{< figure src="/media/2021/08/img%5F8172.jpg?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2021/08/img%5F8170.jpg?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2021/08/img%5F8171.jpg?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2021/08/img%5F8173.jpg?w=1024" alt="" caption="" >}}  
{{< figure src="/media/2021/08/img%5F8175.jpg?w=768" alt="" caption="" >}}  
{{< figure src="/media/2021/08/img%5F8180.jpg?w=768" alt="" caption="" >}}  
{{< figure src="/media/2021/08/img%5F8181.jpg?w=768" alt="" caption="" >}}  
{{< /gallery >}}  

I find that the vent louvers do restrict the airflow somewhat, but the fans do make an affective difference, when parking hot cars in the garage I no longer have to leave the garage door open.
