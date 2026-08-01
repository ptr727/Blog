---
title: MR16 12V Halogen to LED retrofit
date: '2015-08-02T21:25:14+00:00'
url: /2015/08/02/mr16-12v-halogen-to-led-retrofit/
categories:
- research
- review
tags:
- hatch
- led
- lutron
- mr16
- soraa
- torchstar
- transformer
- vantage
post_id: '622'
cover:
  alt: Magnetic_Min_Torchstar
  image: /media/2015/08/magnetic_min_torchstar.png
---
\[7 years later, see update at end of post\]

This post is about my research into finding suitable MR16 LED's for replacing the 50W recessed halogen lights in our house. In summary, I've found "ok" bulbs, not great bulbs, and you can read about the details below.

Our house is about 3 years old, new construction, and one of the many decisions we made during planning was recessed halogen vs. recessed LED lighting. At the time my calculations showed the additional cost for LED lights would only be recovered in electricity cost savings after about 12 years, not worth the cost at the time. Another problem was the optical quality of the products, the near halogen optical quality LED products were ridiculously expensive, and the mainstream LED's were of poor optical quality, and had poor dimmability.

Given the situation we opted for recessed [Elco](http://amzn.to/1JfyeIw) MR16 low voltage 12V AC magnetic transformer halogens, and planned on retrofitting them with LED's as the technology improved and costs came down.

Now, 3 years later; our electricity cost is way higher than originally estimated, we installed [solar](http://www.sunrun.com/rf/referral-costco/) that gave us a 50% reduction in cost, some of the recessed [reflectors](http://amzn.to/1FxuZEL) are showing signs of heat damage from the halogen bulbs, and 12V MR16 LED's have entered the mainstream.


{{< gallery cols="1" >}}  
{{< figure src="/media/2015/06/reflectors-1.jpg" title="Reflectors-1" alt="Reflectors-1" >}}

{{< figure src="/media/2015/06/reflectors-2.jpg" title="Reflectors-2" alt="Reflectors-2" >}}  
{{< /gallery >}}  

I've been looking for MR16 LED's for some time now, same problem as 3 years ago, dimmable good optical quality bulbs are very expensive, ~$20 per, while eBay and Amazon sourced Chinese manufactured no-name brands are ~$4.

During my research I've made a few important observations:

- US electrical code requires the use of GU10 bi-pin twist-lock lamp bases for new construction, and GU10 will eventually replace all E26 style screw in bases. In the past months I found that there is a much wider supply of 110V [GU10](https://en.wikipedia.org/wiki/Multifaceted_reflector) base MR16 dimmable LED bulbs compared to [GU5.3](https://en.wikipedia.org/wiki/Multifaceted_reflector) 12V bulbs. This is especially true for the no-name brand Chinese suppliers on eBay. I am assuming that the electronic circuitry used is similar to that used in the widely available regular E26 / A21 110V dimmable LED bulbs, and that the only difference is the MR16 housing construction. Keeping in mind that most installed AC [dimmers](http://amzn.to/1LqtiRN) are forward phase, and support a large variety of load types, while an LED is a constant current device that typically uses pulse width modulation for dimming. Thus a line voltage forward phase dimmer to pulse width modulated LED driver circuit is non-trivial, adding a 12V AC transformer in the mix, and supporting both 12V AC and 12V DC loads further complicates the circuitry, especially when dimming is required.
- Just like there is an expanding variety of dimmable GU10 [line voltage](http://amzn.to/1BIkJi0) MR16's, there is an equal growing number of line voltage dimmable [retrofit](http://amzn.to/1dcQ2Wh) LED housings, that are near the cost of a MR16 bulb. These housings replace the old recessed can with an integrated AC LED driver and LED bulb array.
- Today, as was the case 3 years ago, commercial and residential LED recessed lights separate the enclosure from the LED driver, allowing for different color and brightness LED's to be used, and to optimize the electronic circuitry for the type of dimmer being used. The prices are much lower compared to 3 years ago, but still high comparing a [$40](http://amzn.to/1J1a3dY) halogen enclosure to a similar style [$150](http://amzn.to/1dcM8g5) LED enclosure. It is possible to replace the entire enclosure, but it is a big job requiring ripping out ceiling drywall.
- 12V MR16's can be powered by 12V AC electromagnetic transformers or electronic low voltage drivers. ELV drivers offer much higher efficiencies, but require compatible dimmers, and sometimes dimmers specifically designed for ELV drivers. Halogens are almost always powered by electromagnetic transformers due to the reduced cost and complexity. It is possible to replace the electromagnetic transformers in the enclosure with an ELV transformer, I've seen the electrician replace a blown transformer, he had to bring in the "small hand guy" from his crew and even then it took a lot of blind finger fiddling.
- I use a [Vantage Controls InFusion](http://www.vantagecontrols.com/solutions/lighting-automation/infusion-system.aspx) home automation lighting control system in my house. The system supports line-voltage forward phase and reverse phase dimmer modules, 0-10V control, and PWM control [LED dimming](http://www.vantagecontrols.com/solutions/lighting-automation/led-lighting.aspx). All loads in my installation are dimmed using forward phase dimmers. The recommended LED control setup is to use the 0-10V or PWM circuits, i.e. the dimming control and power lines are separate. The [0-10V / PWM](http://dealer.vantagecontrols.com/products/details.php?category=a0M800000049qPcEAI&id=01tC00000039IhXIAU) control modules are about the same cost per line as AC [dimmer](http://dealer.vantagecontrols.com/products/details.php?category=a0M800000049qfSEAQ&id=01tC00000038yCqIAI) modules, but the real cost is again in LED driver circuitry.

So what are my realistic choices:

- The best quality option is to replace the halogen housings and line voltage control circuitry with native PWM control and native LED drivers. But, same as during construction, this is not a cost effective solution.
- I can remove the transformers and convert the enclosure to line voltage, and use GU10 type MR16's. But, tricky to remove the transformer, and the safety and legal state of the enclosure would be unknown after being converted to a line voltage receptacle.
- I can remove the transformers and convert the enclosure to line voltage as above, but instead of using MR16 form factor bulbs, I can replace the insert with LED retrofit inserts.
- I can replace the electromagnetic transformers with ELV's to improve efficiency and dimmability. But again, a tricky job with marginal cost savings, and I still end up using 12V LED MR16's.
- I've opted to replace the halogen bulbs with LED's on an as needed basis, i.e. when I need to replace a burnt trim, or blown bulb, I will replace the entire zone of lights with the same model of LED's. My hope is that there will be ongoing improvements in product quality and performance, and ongoing reduction in costs as availability goes mainstream.

Here then is my review, more an exploration, greatly skewed by my subjective opinion vs. scientific fact, of the products I could find and test.

I initially tested the bulbs by replacing the halogens in my office, but this quickly became cumbersome, so instead I created a test bed for evaluation, trying to simulate the various dimmer and transformer types available.

I bought the the following items to match what I use in my house:

- I bought an [Elco Lighting EL1499ICA 4" Low Voltage Airtight Housing](http://amzn.to/1Gk9ysb) on eBay, this is exactly what I have in my house, and I removed the magnetic transformer for testing.
- A [Lutron DV-603P Diva](http://amzn.to/1DhKx5x) dimmer, the kids and guest rooms have regular light switches, not automated, and use these dimmers.

Here are some pictures of the Elco enclosure, this will give you an idea of how to go about swapping the transformer, and how tight a squeeze it is:


{{< gallery cols="1" >}}  
{{< figure src="/media/2015/06/elco-1.jpg" title="Elco-1" alt="Elco-1" >}}

{{< figure src="/media/2015/06/elco-2.jpg" title="Elco-2" alt="Elco-2" >}}

{{< figure src="/media/2015/06/elco-6.jpg" title="Elco-6" alt="Elco-6" >}}

{{< figure src="/media/2015/06/elco-5.jpg" title="Elco-5" alt="Elco-5" >}}

{{< figure src="/media/2015/06/elco-3.jpg" title="Elco-3" alt="Elco-3" >}}

{{< figure src="/media/2015/06/elco-4.jpg" title="Elco-4" alt="Elco-4" >}}

{{< figure src="/media/2015/06/elco-7.jpg" title="Elco-7" alt="Elco-7" >}}  
{{< /gallery >}}  

The DV-603P is a vanilly halogen and incandescent dimmer, it works just fine with the magnetic transformer and halogen bulbs in my house, but the MR16 LED manufacturer's compatibility guide require the use of specific low voltage magnetic or electronic low voltage dimmers. So I also bought:

- A [Lutron DVELV-303P](http://amzn.to/1JY7aZx) electronic low voltage dimmer.
- A [Lutron DVLV-603P](http://amzn.to/1LX8sbD) magnetic low voltage dimmer.

I considered a more elaborate [test setup](http://www.ledbenchmark.com/faq/How-Do-We-Test.html), but I don't have access to the required equipment, and the measurements would be interesting from a scientific perspective, not so much a subjective perspective. So I opted for a simpler test setup, attached to a piece of hobby board, capturing waveforms using my [Rigol DS4022](http://www.rigolna.com/products/digital-oscilloscopes/ds4000/ds4022/) scope and a [Rigol RP1050D](http://www.rigolna.com/products/accessories/rp1050d/) high voltage differential probe and the UltraScope software.


{{< gallery cols="1" >}}  
{{< figure src="/media/2015/06/bench-1.jpg" title="Bench-1" alt="Bench-1" >}}

{{< figure src="/media/2015/06/bench-2.jpg" title="Bench-2" alt="Bench-2" >}}

{{< figure src="/media/2015/06/bench-3.jpg" title="Bench-3" alt="Bench-3" >}}  
{{< /gallery >}}  

For transformers, I used the magnetic transformer from the Elco enclosure, and I bought three ELV's from eBay, two from a known brand, and one unknown brand:

- [HATCH RS12-60M-LED](http://www.hatchlighting.com/media/productPDF/RS_LED_Drivers_8.pdf), $20 on eBay.
- [HATCH RL12-60A](http://www.hatchlighting.com/media/productPDF/RL-60-75_5.pdf), $6 on eBay.
- Advance Lite TC60W, $3 on eBay, I could not find any documentation on this product or brand.


{{< gallery cols="1" >}}  
{{< figure src="/media/2015/06/transformers-1.jpg" title="Transformers-1" alt="Transformers-1" >}}

{{< figure src="/media/2015/06/transformers-4.jpg" title="Transformers-4" alt="Transformers-4" >}}

{{< figure src="/media/2015/06/transformers-3.jpg" title="Transformers-3" alt="Transformers-3" >}}

{{< figure src="/media/2015/06/transformers-2.jpg" title="Transformers-2" alt="Transformers-2" >}}  
{{< /gallery >}}  

For bulbs, I bought a variety of models from Amazon, eBay, and 1000bulbs:

- [Sylvania 58327](http://assets.sylvania.com/assets/documents/hal_pib2.36e21a03-4ab5-42a4-9d6c-4a092930aad8.pdf): 50W Halogen MR16, 3000K, 35 Degree, 1450 CBCP.  
These are the halogen bulbs I currently use, about $2.20 per bulb.
- [Torchstar TS010](http://www.torchstar.us/4w-dimmable-mr16-led-bulb-spotlight.html): Dimmable, 12V 4W MR16 LED, 6000K Daylight, 50 Watt Equivalent, 330 Lumen, 60 Degree Beam Angle.  
I ordered a 10-pack from [Amazon,](http://amzn.to/1Ib9Czh) the price worked out at about $5.50 per bulb. The packaging is generic, with a black marker dot indicating this to be a "pure white" variant. The bulb itself contains no markings, other than a small Torchstar sticker on the base. The bulb color is very blueish, like that of a daylight compact fluorescent bulb. I found the color to be very displeasing and distracting in my office environment, it made my color calibrated monitor screen appear yellow.
- [Torchstar TS010](http://www.torchstar.us/4w-dimmable-mr16-led-bulb-spotlight.html): Dimmable, 12V 4W MR16 LED, 3200K Warm White, 50 Watt Equivalent, 330 Lumen, 60 Degree Beam Angle  
I ordered a 10-pack from [Amazon,](http://amzn.to/1Ib9Czh) the price worked out to about $5.70 per bulb. Like the daylight version, the packaging is generic, with a black marker dot indicating this to be a "warm white" variant. The bulb itself contains no markings, other than a small Torchstar sticker on the base. The bulb color is pleasing, pretty close to the halogen.
- [Soraa Brilliant 00965](http://www.soraa.com/public/docs/Spec-Sheets-GU5.3-US/3.0/Soraa%20SM16%209W.pdf): Dimmable, 12V 9W MR16 LED, 75 Watt Equivalent, 3000K, CRI 80, CBCP 1540, 590 Lumen  
I ordered the bulbs from [1000bulbs](https://www.1000bulbs.com/product/116685/LED-00965.html), the price is about $28 per bulb. The color is pleasing but it appears to be ever so slightly bluer, more noticeable when dimmed. This bulb is bright, at 75W equivalent, almost too bright for my office as one of the bulbs is right above my head.  
[Soraa](http://www.soraa.com/) specializes in high color quality products, and this model is from the older Brilliant Series, while I was really looking for the new [Vivid Series](http://www.soraa.com/products/specs-GU5.3-US) bulbs, like the [00943](http://www.soraa.com/public/docs/Spec-Sheets-GU5.3-US/3.0/Soraa%20SM16%207W.pdf), but it seems these bulbs are not yet available. I hope to find and test some when they do become available. At the price point of near $30 they are definitely specialty use, but I am interested in the supposed dimmability improvements.
- [Soraa Outdoor 00107](https://www.1000bulbs.com/pdf/soraa-00107-specsheet.pdf): Dimmable, 12V 9.8W MR16 LED, 2700K  
This is a 36W equivalent LED for outdoor use, I bought them for about $24 more than a year ago, the line has since been discontinued.
- [Soraa Premium 2 00249](http://www.soraa.com/public/docs/Spec-Sheets-GU5.3-US/SS-Premium-2-12W-3000K.pdf): Dimmable, 12V 11.5W MR16 LED, 3000K  
I bought these more than a year ago for about $34 each,  the line has since been discontinued.
- Architectural LED MR16-DIM-12V: 2700K 45deg  
I received samples of these MR16 LED's from my electrician, I could not find any info on them.
- [eBay Dimmable CREE LED COB MR16](http://www.ebay.com/itm/171813686721?_trksid=p2057872.m2749.l2649&var=470751037458&ssPageName=STRK%3AMEBIDX%3AIT): 6W MR16  
I bought a batch of 10 warm white and 10 daylight 6W bulbs, and a 9W and a 12W. The 6W bulbs are about $3 per bulb. These bulbs worked surprisingly well and the color was good. Note that the 9W and 12W variants are longer than standard MR16's.


{{< gallery cols="1" >}}  
{{< figure src="/media/2015/06/mr16-1.jpg" title="MR16-1" alt="MR16-1" >}}

{{< figure src="/media/2015/06/mr16-2.jpg" title="MR16-2" alt="MR16-2" >}}

{{< figure src="/media/2015/06/mr16-11.jpg" title="MR16-11" alt="MR16-11" >}}

{{< figure src="/media/2015/06/mr16-10.jpg" title="MR16-10" alt="MR16-10" >}}

{{< figure src="/media/2015/06/mr16-4.jpg" title="MR16-4" alt="MR16-4" >}}

{{< figure src="/media/2015/06/mr16-3.jpg" title="MR16-3" alt="MR16-3" >}}

{{< figure src="/media/2015/06/mr16-5.jpg" title="MR16-5" alt="MR16-5" >}}

{{< figure src="/media/2015/06/mr16-6.jpg" title="MR16-6" alt="MR16-6" >}}

{{< figure src="/media/2015/06/mr16-7.jpg" title="MR16-7" alt="MR16-7" >}}

{{< figure src="/media/2015/06/mr16-8.jpg" title="MR16-8" alt="MR16-8" >}}

{{< figure src="/media/2015/06/mr16-9.jpg" title="MR16-9" alt="MR16-9" >}}  
{{< /gallery >}}  

I tested the transformer response by monitoring the high voltage AC input and low voltage AC output sides using the oscilloscope. I controlled the ELV transformers using the ELV dimmer and the magnetic transformer using the magnetic dimmer. I attached a 12ohm resistor for a purely resistive load, the halogen bulb, and the Torchstar LED bulb. I captured oscilloscope screenshots at full, half, and lowest dimming settings.

Here are the results for the magnetic transformer:


{{< gallery cols="1" >}}  
{{< figure src="/media/2015/08/magnetic%5Fmin%5Fresistor.png" title="Magnetic\_Min\_Resistor" alt="Magnetic\_Min\_Resistor" >}}

{{< figure src="/media/2015/08/magnetic%5Fmed%5Fresistor.png" title="Magnetic\_Med\_Resistor" alt="Magnetic\_Med\_Resistor" >}}

{{< figure src="/media/2015/08/magnetic%5Fmax%5Fresistor.png" title="Magnetic\_Max\_Resistor" alt="Magnetic\_Max\_Resistor" >}}

{{< figure src="/media/2015/08/magnetic%5Fmin%5Fhalogen.png" title="Magnetic\_Min\_Halogen" alt="Magnetic\_Min\_Halogen" >}}

{{< figure src="/media/2015/08/magnetic%5Fmed%5Fhalogen.png" title="Magnetic\_Med\_Halogen" alt="Magnetic\_Med\_Halogen" >}}

{{< figure src="/media/2015/08/magnetic%5Fmax%5Fhalogen.png" title="Magnetic\_Max\_Halogen" alt="Magnetic\_Max\_Halogen" >}}

{{< figure src="/media/2015/08/magnetic%5Fmin%5Ftorchstar.png" title="Magnetic\_Min\_Torchstar" alt="Magnetic\_Min\_Torchstar" >}}

{{< figure src="/media/2015/08/magnetic%5Fmed%5Ftorchstar.png" title="Magnetic\_Med\_Torchstar" alt="Magnetic\_Med\_Torchstar" >}}

{{< figure src="/media/2015/08/magnetic%5Fmax%5Ftorchstar.png" title="Magnetic\_Max\_Torchstar" alt="Magnetic\_Max\_Torchstar" >}}  
{{< /gallery >}}  

Here are the results for the HATCH RS12-60M-LED ELV transformer:


{{< gallery cols="1" >}}  
{{< figure src="/media/2015/08/elv%5Fmin%5Fresistor.png" title="ELV\_Min\_Resistor" alt="ELV\_Min\_Resistor" >}}

{{< figure src="/media/2015/08/elv%5Fmed%5Fresistor.png" title="ELV\_Med\_Resistor" alt="ELV\_Med\_Resistor" >}}

{{< figure src="/media/2015/08/elv%5Fmax%5Fresistor.png" title="ELV\_Max\_Resistor" alt="ELV\_Max\_Resistor" >}}

{{< figure src="/media/2015/08/elv%5Fmin%5Fhalogen.png" title="ELV\_Min\_Halogen" alt="ELV\_Min\_Halogen" >}}

{{< figure src="/media/2015/08/elv%5Fmed%5Fhalogen.png" title="ELV\_Med\_Halogen" alt="ELV\_Med\_Halogen" >}}

{{< figure src="/media/2015/08/elv%5Fmax%5Fhalogen.png" title="ELV\_Max\_Halogen" alt="ELV\_Max\_Halogen" >}}

{{< figure src="/media/2015/08/elv%5Fmin%5Ftorchstar.png" title="ELV\_Min\_Torchstar" alt="ELV\_Min\_Torchstar" >}}

{{< figure src="/media/2015/08/elv%5Fmed%5Ftorchstar.png" title="ELV\_Med\_Torchstar" alt="ELV\_Med\_Torchstar" >}}

{{< figure src="/media/2015/08/elv%5Fmax%5Ftorchstar.png" title="ELV\_Max\_Torchstar" alt="ELV\_Max\_Torchstar" >}}  
{{< /gallery >}}  

Here are the results for the HATCH RL12-60A ELV transformer:


{{< gallery cols="1" >}}  
{{< figure src="/media/2015/08/elv1%5Fmin%5Fhalogen.png" title="ELV1\_Min\_Halogen" alt="ELV1\_Min\_Halogen" >}}

{{< figure src="/media/2015/08/elv1%5Fmed%5Fhalogen.png" title="ELV1\_Med\_Halogen" alt="ELV1\_Med\_Halogen" >}}

{{< figure src="/media/2015/08/elv1%5Fmax%5Fhalogen.png" title="ELV1\_Max\_Halogen" alt="ELV1\_Max\_Halogen" >}}

{{< figure src="/media/2015/08/elv1%5Fmin%5Ftorchstar.png" title="ELV1\_Min\_Torchstar" alt="ELV1\_Min\_Torchstar" >}}

{{< figure src="/media/2015/08/elv1%5Fmed%5Ftorchstar.png" title="ELV1\_Med\_Torchstar" alt="ELV1\_Med\_Torchstar" >}}

{{< figure src="/media/2015/08/elv1%5Fmax%5Ftorchstar.png" title="ELV1\_Max\_Torchstar" alt="ELV1\_Max\_Torchstar" >}}  
{{< /gallery >}}  

Here are the results for the Advance Lite TC60W ELV transformer:


{{< gallery cols="1" >}}  
{{< figure src="/media/2015/08/elv2%5Fmin%5Fhalogen.png" title="ELV2\_Min\_Halogen" alt="ELV2\_Min\_Halogen" >}}

{{< figure src="/media/2015/08/elv2%5Fmed%5Fhalogen.png" title="ELV2\_Med\_Halogen" alt="ELV2\_Med\_Halogen" >}}

{{< figure src="/media/2015/08/elv2%5Fmax%5Fhalogen.png" title="ELV2\_Max\_Halogen" alt="ELV2\_Max\_Halogen" >}}

{{< figure src="/media/2015/08/elv2%5Fmin%5Ftorchstar.png" title="ELV2\_Min\_Torchstar" alt="ELV2\_Min\_Torchstar" >}}

{{< figure src="/media/2015/08/elv2%5Fmed%5Ftorchstar.png" title="ELV2\_Med\_Torchstar" alt="ELV2\_Med\_Torchstar" >}}

{{< figure src="/media/2015/08/elv2%5Fmax%5Ftorchstar.png" title="ELV2\_Max\_Torchstar" alt="ELV2\_Max\_Torchstar" >}}  
{{< /gallery >}}  

Looking at the results we can see that the response waveforms for the halogen bulb is, not surprisingly, near that of the resistor. We can see that the magnetic transformer and LED load has all sorts of inductive goodness going on. And we can see that the RL12-60W and TC60W ELV transformers are not nearly as well behaved as the RS12-60M-LED ELV that is specifically designed for LED loads.

I then proceeded to test the dimmability of the various LED bulbs, I summarize my subjective findings below:

Halogen:

Magnetic: Good dimming range  
RS12-60M-LED: Good dimming range, slight transformer buzzing  
RL12-60A: Good dimming range  
TC60W: Good dimming range

Torchstar:

Magnetic: Good dimming range, flicker at low end  
RS12-60M-LED: Limited dimming range, no flicker, slight transformer buzzing  
RL12-60A: Good dimming range, continuous flicker  
TC60W: Good dimming range, flicker at low end

Soraa Premium 2:

Magnetic: Good dimming range, flicker at low end, very loud transformer buzzing  
RS12-60M-LED: Good dimming range, flicker at low end, slight transformer buzzing

Soraa Brilliant:

Magnetic: Good dimming range, flicker at low end, slight transformer buzzing  
RS12-60M-LED: Good dimming range, slight transformer buzzing

eBay CREE COB:

Magnetic: Good dimming range, switches off before end of dim range  
RS12-60M-LED: Good dimming range, slight transformer buzzing

I was surprised that the cheap $3 eBay CREE COB MR16 LED bulbs worked as well as they did. Only downside is they switch off at around 20% when using the magnetic transformer, but dim down well. I don't know if they really contain [CREE COB LED's](http://www.cree.com/LED-Components-and-Modules/Landing-pages/CXA), but the COB array arrangement of LED's provide an even light source.

The [Torchstar](http://amzn.to/1Ib9Czh) bulbs have a slight flicker at the low end, but dims down all the way, a bit more expensive compared to the eBay bulbs, but US based Torchstar support may be worth the extra 1$ per bulb.

The RS12-60M-LED ELV transformer performed well with halogen and LED loads, but the buzzing sound with or without load was a disappointment. I tested with two units, both buzz. I contacted the manufacturer to find out if this is normal, or if the units I bought on eBay are faulty.

I have yet to find a MR16 LED that can be driven by a magnetic transformer that performs like halogens, my search continues.

7 years later...

I was looking for replacement baffles as many were discoloring from heat, and my attempts at spray painting with heat resistant paint was not very successful.

One day I was shown a build.com ad on Facebook, assuming due to my search history, a win, for an [Elco EL140CT5](https://elcolighting.com/products/4-led-bi-pin-retrofit-insert-reflector-trims) retrofit insert that is CA Title 24 compliant, sold by [Build.com](https://www.build.com/elco-el140ct5/s1762241?uid=4160681) or [Amazon](https://amzn.to/3h1mimL) for about $33. Not cheap, but about the same price as just a replacement metal baffle, that now needs to be special ordered.

The retrofit replaces the entire baffle and lamp, using the old lamp connector, and has an adjustable color switch 2700K-5000K. They were easy to install, and they look great. I used 3000K for most of the house, and 4000K for bathrooms, closets, and work rooms. It cost me a pretty sum, but I replaced every single bulb (where I could reach without needing to get scaffolding built e.g. above the staircase).


{{< gallery cols="1" >}}  
{{< figure src="/media/2022/12/image.png?w=513" alt="" caption="" >}}

{{< figure src="/media/2022/12/image-1.png?w=589" alt="" caption="" >}}  
{{< /gallery >}}  

The dimming linearity is quite different to halogens, but I can compensate in my Vantage Infusion light controller, just haven't gotten around to doing it yet.

+2 Years later, and I also replaced all the kitchen CFL's with retrofit LED's, using [Elco ECF41540W 4" 4000K LED CFL Retrofit Inserts](https://www.elcolighting.com/products/4-led-cfl-retrofit-insert). The LED replacement inserts are $30, and a CFL bulb (that recently got really expensive) is $18, and the CFL's need at least yearly replacement, so 2 year return is not bad.

{{< figure src="https://www.elcolighting.com/sites/default/files/ECF41527W.png" alt="" caption="" >}}
