---
title: ESP32 Water and Gas Utility Meter
date: '2021-08-10T03:27:27+00:00'
url: /2021/08/09/esp32-water-and-gas-utility-meter/
categories:
- homeautomation
- power
tags:
- esphome
- homeassistant
post_id: '2340'
cover:
  alt: IMG_8178_1
  image: /media/2021/08/img_8178_1.jpg
---
The [recent](https://www.home-assistant.io/blog/2021/08/04/home-energy-management/) release of Home Assistant's energy dashboard inspired me to restore my gas and water utility meter monitors. I lost the measurements when I [removed](/2020/09/05/abandoning-greeneye-for-sense/) my Brultech GreenEye energy meters in favor of [Sense](https://amzn.to/3jIGAhQ) energy monitors.

To recap, my local city and utilities do not allow any connections in any form to their utility meters, but I am allowed to install my own meters downstream, as long as the meter models are approved for local use, i.e. the exact same model as used by the local utilities. I installed the same model water and gas meters as used by the utilities but with dry-contact metering.

I already have a couple ESP32/8266 devices in my home, so I built a ESP32 based counter integrated with HA using [ESPHome](https://esphome.io/). I used a [ESP32-DevKitC-32UE](https://www.espressif.com/en/products/devkits/esp32-devkitc) variant of the ESP32, because that's what I had on hand, with a transparent waterproof [case](https://amzn.to/37tb3e7) with two grommets, an external antenna, and solder-protoboard. Really any [ESP32-WROOM-32](https://amzn.to/3xzzBNl) and case and protoboard should work. I used a 5V [PSU](https://amzn.to/3lIPSxc) with a switch, cutting the MicroUSB plug off and feeding it through the grommet into the case. I fed the shielded twisted pair wire from the meters through the other grommet. I connected power and sensor wires using spring terminal [blocks](https://amzn.to/3iwHRcI), and added an LED. No other components are needed, the reed switches are pulled high by the ESP32, and pulled to ground when closed.

Below are pictures of the finished case and the utility meters:


{{< gallery cols="4" >}}  
{{< figure src="/media/2018/08/20180811_180521052_ios.jpg?w=1024" alt="" caption="" >}}

{{< figure src="/media/2020/08/img_6638.jpg?w=768" alt="" caption="" >}}

{{< figure src="/media/2021/08/img_8178_1.jpg?w=400" alt="" caption="" >}}

{{< figure src="/media/2021/08/img_8178.jpg?w=569" alt="" caption="" >}}
{{< /gallery >}}  

The ESPHome code uses the [pulse\_meter](https://esphome.io/components/sensor/pulse_meter.html) sensor, with the total sensor being measured by the HA [utility\_meter](https://www.home-assistant.io/integrations/utility_meter/) integration. The sensor produces flow rate measurements and incrementing absolute consumption, and it is the consumption, not flow rate, that is needed for the utility meter integration.

ESPHome (5 Nov 2022 updated to support gas and water device classes now supported in HA):

```
sensor:
  - platform: pulse_meter
    pin:
      number: GPIO32
      mode: INPUT_PULLUP
    internal_filter_mode: PULSE
    internal_filter: 100ms
    timeout: 60s
    unit_of_measurement: 'gal/min'
    accuracy_decimals: 3
    name: ${device_name}_water_meter
    icon: 'mdi:water'
    filters:
      - multiply: 10
    total:
      name: ${device_name}_water_meter_total
      icon: 'mdi:water'
      device_class: 'water'
      id: water_total
      unit_of_measurement: 'gal'
      accuracy_decimals: 3
      filters:
      - multiply: 10
  - platform: pulse_meter
    pin:
      number: GPIO33
      mode: INPUT_PULLUP
    internal_filter_mode: PULSE
    internal_filter: 100ms
    timeout: 60s
    unit_of_measurement: 'ft³/min'
    accuracy_decimals: 3
    name: ${device_name}_gas_meter
    icon: 'mdi:fire'
    filters:
      - multiply: 10
    total:
      name: ${device_name}_gas_meter_total
      icon: 'mdi:fire'
      device_class: 'gas'
      id: gas_total
      unit_of_measurement: 'ft³'
      accuracy_decimals: 3
      filters:
      - multiply: 10
  - platform: template
    name: ${device_name}_water_meter_total_m3
    icon: 'mdi:water'
    device_class: 'water'
    state_class: 'total_increasing'
    accuracy_decimals: 3
    unit_of_measurement: 'm³'
    # Convert gal to m³
    lambda: |-
      return id(water_total).state / 264.2;
  - platform: template
    name: ${device_name}_gas_meter_total_m3
    icon: 'mdi:fire'
    device_class: 'gas'
    state_class: 'total_increasing'
    accuracy_decimals: 3
    unit_of_measurement: 'm³'
    # Convert ft³ to m³
    lambda: |-
      return id(gas_total).state / 35.315;
```

Home Assistant:

```
utility_meter:
  daily_water_total:
    source: sensor.utility_pulse_counter_water_meter_total
    cycle: daily
  daily_water_total_m3:
    source: sensor.utility_pulse_counter_water_meter_total_m3
    cycle: daily
  monthly_water_total:
    source: sensor.utility_pulse_counter_water_meter_total
    cycle: monthly
  monthly_water_total_m3:
    source: sensor.utility_pulse_counter_water_meter_total_m3
    cycle: monthly
  daily_gas_total:
    source: sensor.utility_pulse_counter_gas_meter_total
    cycle: daily
  daily_gas_total_m3:
    source: sensor.utility_pulse_counter_gas_meter_total_m3
    cycle: daily
  monthly_gas_total:
    source: sensor.utility_pulse_counter_gas_meter_total
    cycle: monthly
  monthly_gas_total_m3:
    source: sensor.utility_pulse_counter_gas_meter_total_m3
    cycle: monthly
```

HA Dashboard:

{{< figure src="/media/2021/08/ha.png?w=687" alt="" caption="" >}}

The HA energy dashboard currently only tracks power, but I hope other measurements would be added over time. (5 Nov 2022 now with Gas and Water)

{{< figure src="/media/2022/11/screenshot-2022-11-05-180920.png?w=1024" alt="" caption="" >}}

\[Updated on 5 November 2022 with [Home Assistant 2022.11](https://www.home-assistant.io/blog/2022/11/02/release-202211/) support for Water and Gas energy consumption monitoring\]
