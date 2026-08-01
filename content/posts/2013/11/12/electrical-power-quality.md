---
title: Electrical Power Quality
date: '2013-11-13T00:49:25+00:00'
url: /2013/11/12/electrical-power-quality/
categories:
- power
- problem
tags:
- fluke
- sce
post_id: '473'
---
Earlier this year we moved a couple miles from Redondo Beach to Manhattan Beach, bigger house, better school district.
As far as the house and area is concerned, it is definitely an upgrade, but not so for the utilities.

Monthly utilities are a lot more expensive, not so much the per unit fees, but the base service fees, not just a couple $, but three of four times what we paid in Redondo Beach. Now, if it came with better offerings, or better service, or higher quality, ok, but the opposite.
Water quality is worse, specifically hardness, MB [supplies](http://www.citymb.info/city-officials/public-works/utilities-division/water-systems/source-of-supply) its own water, RB gets water from [LADWP](https://www.ladwp.com/ladwp/faces/ladwp/aboutus/a-water/a-w-sourcesofsupply/), and that unsightly water tower that no longer serves any practical purpose, with efforts to demolish it always being thwarted.
As a new resident trash collection makes me pay almost thirty $ extra per month for an extra trash can, while grandfathered-in residents keep extras for free. Now, I know it is unfair to judge a service by their employee's actions, or is it, but the trash collection guy is a jerk, if a little dust and having to get out of the truck is going to get you agitated, you are in the wrong business, especially when compared with the pack of trash collection men in RB that were always friendly and willing to give a hand.
But, I really digress, I want to discuss electrical power quality problems.

In the six plus years we lived in RB, I think we had one scheduled power outage, and maybe two short unplanned outages. Since moving to MB earlier this year, we've had two scheduled outages, one lasting an entire day, and several unscheduled outages.
The power is unreliable, SCE knows it, the city knows it, there are some plans addressing it, see [here](http://www.easyreadernews.com/72017/manhattan-beach-south-bay-officials-stand-behind-muratsuchis-utility-outage-bill/) [here](http://manhattanbeach.patch.com/groups/business-news/p/sces-onoff-again-planned-power-outage-demystified) [here](http://www.southbaycities.org/sites/default/files/board_directors/meeting/10-12%20Reliability,%20Outages,%20CSA_SBCCOG%20report.pdf) [here](http://tbrnews.com/news/manhattan_beach/city-officials-upset-edison-has-left-residents-in-the-dark/article_aa98db7e-ce14-11e2-9a52-0019bb2963f4.html).

My concern is not really power being on or off, it is power being on but of poor quality; an electronic equipment killer.

When we moved in, the first signs of electrical problems were flickering lights. At first I thought it was a problem with the [Vantage](http://www.vantagecontrols.com/) light control system, but even lights directly on utility power flickered. As soon as I hooked up UPS's to my servers and the signal distribution system, the UPS's started complaining about power quality. Occasionally during the day I would get a notification from the UPS's that it detected a distorted input, and every night the UPS's would complain about low input voltage.
It may be coincidental, but I've also had two [astronomical clock light timers](http://www.amazon.com/gp/product/B003AIKQZ8/ref=as_li_ss_tl?ie=UTF8&camp=1789&creative=390957&creativeASIN=B003AIKQZ8&linkCode=as2&tag=pievilsblo-20) fail at the same time, the casings were scorched in what appears to be signs of electrical damage.

UPS Event Log:
[![APC Event Log](/media/2013/11/apc-log.png)](/media/2013/11/apc-log.png)

In order to quantify the problem, I used a [Fluke VR1710 Voltage Quality Recorder](http://www.amazon.com/gp/product/B002006LQA/ref=as_li_ss_tl?ie=UTF8&camp=1789&creative=390957&creativeASIN=B002006LQA&linkCode=as2&tag=pievilsblo-20). The device plugs into a mains outlet, and records events, and a USB port is used to configure the device, and download recorded data.

As I am not a power quality expert, I referred to [Wikipedia](http://en.wikipedia.org/wiki/Power_quality) to and [Power Quality In Electrical Systems](http://www.powerqualityworld.com/) for information and reference material. To further simplify the analysis, I opted to compare my office power with my home power, this allowed me to easily visualize the quality differences, granted, I am assuming my office power is good.

I configured the VR1710 to take measurements every 10s, and to record exceptional events, about 10 days worth of data. I set the dip threshold to 106V, the swell threshold to 127V, and the transient sensitivity to 5V.

VR1710 Settings:
[![VR1710 Settings](/media/2013/11/settings.png)](/media/2013/11/settings.png)

Below are reports detailing the recorded events, click graphs to view full resolution:

Home Voltage:
[![Home - Voltage](/media/2013/11/home-voltage.png?w=584)](/media/2013/11/home-voltage.png)

There is a clear pattern of voltage drops below 102V every evening, these drops are also observed in the UPS logs showing low voltage warnings around 7:30PM every evening.

Office Voltage:
[![Office - Voltage](/media/2013/11/office-voltage.png?w=584)](/media/2013/11/office-voltage.png)

The office voltage is very stable.

Home Flicker:
[![Home - Flicker](/media/2013/11/home-flicker.png?w=584)](/media/2013/11/home-flicker.png)

According to [Wikipedia](http://en.wikipedia.org/wiki/Power-line_flicker) and [PQW](http://www.powerqualityworld.com/2011/09/voltage-fluctuations-flicker.html) short term flicker (Pst) is noticeable at values exceeding 1.0, and long term flicker (Plt) is noticeable at values exceeding 0.65. These results would explain why we observe lights flickering.

Office Flicker:
[![Office - Flicker](/media/2013/11/office-flicker.png?w=584)](/media/2013/11/office-flicker.png)

Office flicker values are well within acceptable ranges.

Home Statistics:
[![Home - Statistics](/media/2013/11/home-statistics.png?w=584)](/media/2013/11/home-statistics.png)

From this distribution we can see the wide spread in voltages, well below the 120V theoretical norm. This chart does not show it, but the 95% distribution is 115.5V, and the 5% distribution is 106.1V.

Office Statistics:
[![Office - Statistics](/media/2013/11/office-statistics.png?w=584)](/media/2013/11/office-statistics.png)

The office voltage distribution is nicely clustered around 119V, with the 95% distribution at 119.6V, and the 5% distribution at 117.4V.

Home Dips And Swells:
[![Home - Dips Swells](/media/2013/11/home-dips-swells.png?w=584)](/media/2013/11/home-dips-swells.png)

ITIC and CBEMA are standards for acceptable power quality, see [here](http://www.powerqualityworld.com/2011/04/itic-power-acceptability-curve.html) for a detailed description.
To describe the graph, I quote from the Fluke Power Log software manual:
_Dips and swells are shown on a CBEMA (Computer Business Equipment Manufacturers Association) and ITIC (Information Technology Industry Council) plot classification table according to EN50160. On the CBEMA (blue) and ITIC (red), curve markers are plotted for each dip and swell. The height on the vertical axis shows the severity of the dip or swell relative to the nominal voltage. The horizontal position shows the duration of the dip or swell. These curves show an ac input voltage envelope which typically can be tolerated (no interruption in function) by most Information Technology Equipment (ITE)._

Based on the graph we can see a large number of events exceeding the acceptable ranges. Since there were no dips at the office, there is no graph for the office.

Home Transients:
[![Home - Transients](/media/2013/11/home-transients.png?w=584)](/media/2013/11/home-transients.png)

I only show the transients graph for home, as the wave forms all look different, and the only difference between home and office is 87 events were recorded at home while 10 events were recorded at the office for the same approximate time duration. See [PQW](http://www.powerqualityworld.com/2011/05/transients-power-quality-basics.html) for an explanation of transients.

We can clearly see that the power quality at my house is significantly worse compared to the power at my office.

I am speculating, but I wonder if the old transformer across the road can supply sufficient power, given that it used to supply power to three small very old houses on four lots, demolished to make room for four new larger houses?

I just opened a support ticket with [SCE](https://www.sce.com/), let's hope they can do something about the problem.
