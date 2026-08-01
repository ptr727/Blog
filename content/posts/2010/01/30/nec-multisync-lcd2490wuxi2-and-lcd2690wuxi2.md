---
title: NEC MultiSync LCD2490WUXi2 and LCD2690WUXi2
date: '2010-01-30T23:00:00+00:00'
url: /2010/01/30/nec-multisync-lcd2490wuxi2-and-lcd2690wuxi2/
categories:
- review
post_id: '97'
---
I recently replaced my DELL monitors with NEC monitors.

The primary reason why I replaced DELL with NEC is color reproduction, I could never quite get the wide gamut DELL's to look right.





I chose the [NEC MultiSync 90](http://www.necdisplay.com/Products/Series/?series=171d9fbb-281e-44d8-be67-14d146e8ada0 "NEC MultiSync 90") series monitors because they have excellent color reproduction, and are reasonably affordable.

The alternative would have been [EIZO ColorEdge](http://www.eizo.com/global/ "EIZO ColorEdge") monitors, but they are significantly more expensive.



Since I had a [hard time calibrating](/2009/06/dell-2408wfp-and-spyder-3-elite.html "hard time calibrating") the wide color gamut DELL monitors in the past, so it was very important that the NEC monitors be correctly calibrated.

As such, I also purchased the monitors with the [NEC SpectraView II](http://www.necdisplay.com/SupportCenter/Monitors/spectraview2/ "NEC SpectraView II") calibration kits.



At my office I use [NEC MultiSync LCD2490WUXi2](http://www.necdisplay.com/Products/Product/?product=29d41c3a-c07c-4dda-a199-13b8823de971 "NEC MultiSync LCD2490WUXi2") monitors, they have very good sRGB color reproduction, ideal for office and web graphics.

At my home office I use [NEC MultiSync LCD2690WUXi2](http://www.necdisplay.com/Products/Product/?product=8899a96d-28dc-484f-a4de-14309a636738 "NEC MultiSync LCD2690WUXi2") monitors, they have very good AdobeRGB color reproduction, ideal for photo graphics.



[![](http://docs.google.com/File?id=dcmzmbww_45gv49p5g3_b)](http://docs.google.com/File?id=dcmzmbww_45gv49p5g3_b "NEC MultiSync LCD2490WUXi2")

[![](http://docs.google.com/File?id=dcmzmbww_46f88c935k_b)](http://docs.google.com/File?id=dcmzmbww_46f88c935k_b "NEC MultiSync LCD2690WUXi2")





As I replaced one of the DELL monitors that was connected via a KVM with the NEC, I immediately noticed a problem.



I was using a [DELL UltraSharp 2405FPW](http://support.dell.com/support/edocs/monitors/2405fpw/en/index.htm "DELL UltraSharp 2405FPW") monitor with a [StarTech StarView SV431DVIUAHR](http://www.startech.com/item/SV431DVIUAHR-4-Port-High-Resolution-USB-DVI-Dual-Link-KVM-Switch-with-Audio.aspx "StarTech StarView SV431DVIUAHR") 4-Port Dual-Link DVI KVM switch.

Although the 2405PFW does not require dual-link, I occasionally used this switch with a [DELL UltraSharp 3007WFP-HC](http://support.dell.com/support/edocs/monitors/3007wfp/en/index.htm "DELL UltraSharp 3007WFP") monitor that does require dual-link.

I have also used this model KVM switch with [DELL UltraSharp 2408WFP](http://www.dell.com/us/en/dfo/peripherals/monitor_2408wfp/pd.aspx?refid=monitor_2408wfp&s=dfo "DELL UltraSharp 2408WFP") monitors wihtout any issues.



I replaced the DELL monitor with the NEC monitor without shutting down my computer.

I just unplugged the DELL from the KVM, and plugged the NEC in, powered it on, and the screen showed fine.



The PC did not detect the new display model, and I assumed this was because the KVM cached the monitor EDID information, so I rebooted.

On shutdown the screen powered off, then on reboot the screen powered on, showed the BIOS screen, then when Windows started loading, the screen powered off again.



I completely power cycled the KVM switch, and tried again, this time the BIOS screen did not even show.

I tried to cold boot with four different machines, a Lenovo T61 notebook, a DELL M4400 notebook, a DELL E4300 notebook, and a custom built PC, all had the same result, the NEC monitor does not power on.



I had three NEC monitors available, tried them all, same problem.

When directly connecting the monitor to the PC, it worked fine.

Using the notebooks, I could boot using the notebook screen, then plugin the KVM to the notebook, and the NEC would power on.



I changed the NEC EDID option to advanced, and the monitor did power on during cold boot.

But, the advanced EDID option makes the monitor appear to be a 1080p/720p display, and the PC cannot set the native 1920x1200 resolution.





Given that the KVM had worked fine with the DELL monitors, and that by enabling the advanced EDID option the monitor worked, I believed the problem to be with the NEC monitors.

I contacted NEC support, they only offer web chat and email, no phone support.

I tried the web chat, but it was closed, so I sent an email, after two days I had not heard a reply.

I tried the web chat again, this time it was open, and after about 10 minutes of waiting, I was connected to an agent.

I described the problem, and as soon as I mentioned KVM, the agent asked if the monitor works when directly connected, on saying yes, I was told that KVM's are not supported.

This sounded like typical not my problem canned response, and I asked where it is officially documented that NEC does not support KVM's, the agent terminated the chat session.

Needless to say, I was less than impressed with the agent's behavior, although theoretically it could have been a network problem and not an attitude problem.

To this day I have not yet received a reply to my support email.





I called StarTech support, unlike NEC they offer phone, email, and web form support.

The agent was very helpful, trying a variety of connection and power on order changes, but to no avail.





I had used IOGEAR KVM's before, and I switched StarTech for dual-link support, something IOGEAR did not offer at that time.

The IOGEAR KVM's are really good value for money, especially when you consider that you get the cables with the IOGEAR units, and with most other KVM manufacturers you have to buy cables separately.

IOGEAR now had the [GCS1204](http://www.iogear.com/product/GCS1204/ "GCS1204") model that did support dual-link.



I ordered a GCS1204, and it worked fine, the monitor powered on without issue.

The only problem with the GCS1204 is that the keyboard keys sometimes get "stuck" and the key will keep on repeatinggggggggg until you press another key.

This seems to be a [known problem](http://www.newegg.com/Product/ProductReview.aspx?Item=N82E16817399034 "known problem") reported by several users.



Although the IOGEAR KVM works and the StarTech does not, I still feel the key issue is with NEC.





In total I have five NEC monitors, one LCD2490WUXi2 connected to the KVM in my office, two LCD2490WUXi2's connected as dual monitor to my office workstation, two LCD2690WUXi2's connected as dual monitor to my home office workstation.

I purchased two of the monitors, model [LCD2690W2-BK-SV](http://www.necdisplay.com/Products/Product/?product=e46df7f2-40d7-4b16-b6ed-9c444e398f11 "LCD2690W2-BK-SV"), with the SpectraView II calibration kits included.

The "-BK" designation means the monitor is black, and the "-SW" designation means the "SVII-PRO-KIT" is included in the box, but the monitor is a [LCD2690WUXi2](http://www.necdisplay.com/Products/Product/?product=8899a96d-28dc-484f-a4de-14309a636738 "LCD2690WUXi2-BK").

I happen to own an [X-Rite i1Display2](http://www.xrite.com/product_overview.aspx?ID=788 "X-Rite i1Display2") sensor, so it was obvious that the NEC sensor is a custom i1Display2 sensor.

The SpectraView documentation states that the sensor is custom calibrated for the wide gamut NEC displays.



[![](http://docs.google.com/File?id=dcmzmbww_47ck7vbfdv_b)](http://docs.google.com/File?id=dcmzmbww_47ck7vbfdv_b "NEC MultiSync LCD2690W2-BK-SV")

[NEC MultiSync LCD2690W2-BK-SV](http://docs.google.com/File?id=dcmzmbww_47ck7vbfdv_b "NEC MultiSync LCD2690W2-BK-SV")[![](http://docs.google.com/File?id=dcmzmbww_48c6fvzwds_b)](http://docs.google.com/File?id=dcmzmbww_48c6fvzwds_b "NEC SVII-PRO-KIT")





The SpectraView software installs a gamma loader application in the Windows startup folder, and on every login, the monitor calibration values are validated, and warns you when calibration is overdue.

With the Lenovo T61 notebook, on every login, the software will tell me that a compatible monitor is not found.

Yet, if I manually run the SpectraView software, or the [NaViSet](http://www.necdisplay.com/SupportCenter/Monitors/Naviset/ "NaViSet") software, it detects the monitor just fine.

Also, if I just rerun the gamma loader in the startup group, it works fine.



[![](http://docs.google.com/File?id=dcmzmbww_49chfznbcp_b)](http://docs.google.com/File?id=dcmzmbww_49chfznbcp_b)



[![](http://docs.google.com/File?id=dcmzmbww_50hsd29x4g_b)](http://docs.google.com/File?id=dcmzmbww_50hsd29x4g_b)



[![](http://docs.google.com/File?id=dcmzmbww_51c4g8ndhm_b)](http://docs.google.com/File?id=dcmzmbww_51c4g8ndhm_b)





I left a comment on the [SpectraView Feedback page](http://www.necdisplay.com/supportcenter/monitors/spectraview2/feedback/ "SpectraView Feedback page") describing the problem, and within a few hours I received an email from a support person asking for more details.

The person suggested the problem is timing related, and that I use a startup manager to delay the loader.

A startup manager seems overkill for something that should probably be addressed in the SpectraView software, and I suggested as such.

We'll see if they address the problem in future versions, but since I rarely logout, I normally just put machine to sleep, this is not a big issue.





The SpectraView calibration software is easy to use, and worked fine on my dual monitor Windows 7 Ultimate x64 workstations.

The calibration results show the difference between the LCD2490WUXi2 and LCD2690WUXi2 color response.



[![](http://docs.google.com/File?id=dcmzmbww_52gcqbsthm_b)](http://docs.google.com/File?id=dcmzmbww_52gcqbsthm_b "NEC MultiSync LCD2490WUXi2")



[![](http://docs.google.com/File?id=dcmzmbww_53gv9z32dv_b)](http://docs.google.com/File?id=dcmzmbww_53gv9z32dv_b "NEC MultiSync LCD2490WUXi2")



[![](http://docs.google.com/File?id=dcmzmbww_545zt23gv_b)](http://docs.google.com/File?id=dcmzmbww_545zt23gv_b "NEC MultiSync LCD2690WUXi2")



[![](http://docs.google.com/File?id=dcmzmbww_55cn2mb8g7_b)](http://docs.google.com/File?id=dcmzmbww_55cn2mb8g7_b "NEC MultiSync LCD2690WUXi2")





I really enjoy these monitors, especially the consistent color reproduction of the dual monitor setups.

The only comments I receive every time somebody visits my desk is how thick these monitors are.

But, as as soon as they see the color reproduction and consistency, they forgive the fat 90's look.




