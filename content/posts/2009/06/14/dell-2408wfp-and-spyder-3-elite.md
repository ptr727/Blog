---
title: DELL 2408WFP and Spyder 3 Elite
date: '2009-06-14T07:45:00+00:00'
url: /2009/06/14/dell-2408wfp-and-spyder-3-elite/
categories:
- review
tags:
- calibration
- dell
- monitor
- spyder
post_id: '90'
---
I upgraded my vista Ultimate x64 workstation to a dual monitor setup using two 24"[DELL 2408WFP](http://accessories.us.dell.com/sna/products/Monitors/productdetail.aspx?c=us&l=en&s=bsd&cs=04&sku=320-6272 "DELL 2408WFP") displays connected to an [ATI HD4850](http://www.amd.com/us/products/desktop/graphics/ati-radeon-hd-4000/Pages/ati-radeon-hd-4000-series.aspx "ATI HD4850") video card.



I immediately noticed that the colors were unnaturally bright and over-saturated.





I had a similar problem on another workstation with a 30"[DELL 3007WFP-HC](http://accessories.us.dell.com/sna/products/Monitors/productdetail.aspx?c=us&l=en&s=dhs&cs=19&sku=222-7175 "DELL 3007WFP-HC") display. My original 3007WFP was great, until it started making a high pitched noise, and DELL replaced it under warranty, but they replaced it with a 3007WFP-HC model, and the color difference was very noticeably worse than the old monitor.





This is when I found out about what are called "wide gamut" monitors that support displaying an extended color space, and along with it, monitor color calibration.



You can read more about "gamut" on [Wikipedia](http://en.wikipedia.org/wiki/Gamut "Wikipedia"), or a discussion on "wide gamut displays" at [Digital Photography Review](http://forums.dpreview.com/forums/read.asp?forum=1004&message=25060360 "Digital Photography Review") and another at [Overclockers Australia Forums](http://forums.overclockers.com.au/showthread.php?t=723315 "Overclockers Australia Forums").





With these displays the problem is basically that there is a big difference in appearance between an application that is color managed, such as Photoshop, and an application that is not color managed, such as the Windows desktop. The problem is is more noticeable when it comes to web browsers since none of the major browsers support color management.

Here is a [page](http://www.gballard.net/psd/go_live_page_profile/embeddedJPEGprofiles.html "page") to test your browser's color manangement behavior.



When I got the DELL 3007WFP-HC I purchased a [X-Rite i1Display 2](http://www.xrite.com/product_overview.aspx?ID=788 "X-Rite i1Display 2") [calorimeter](http://en.wikipedia.org/wiki/Colorimeter "calorimeter") to calibrate the display, and the results were pretty good.





I tried the 1iDisplay 2 again with the 2408WFP displays, but I was just not happy with the color, and I could not get the two monitors to match. I also sometimes had various problems getting the iMatch software to work correctly when calibrating the secondary display or correctly detecting the calorimeter.





Searching the web I found that many people were having trouble calibrating the 2408WFP monitors, and of those that were happy, several were using the [Datacolor Spyder 3 Elite](http://spyder.datacolor.com/product-mc-s3elite.php "Datacolor Spyder 3 Elite") calorimeter. I ordered a Spyder 3 Elite in the hopes that it would produce better results, or at least be more convenient to use in a dual monitor setup.





Now let me take a moment to talk about my impressions of [Datacolor](http://www.datacolor.com/ "Datacolor").





Their website does not work with the [Google Chrome](http://www.google.com/chrome "Google Chrome") browser, none of the navigation menus work, and I had to use [Microsoft Internet Explorer](http://www.microsoft.com/windows/internet-explorer/default.aspx "Microsoft Internet Explorer") to navigate their site.



The support site navigation is, well, there is no site navigation.



There is no ability to browse documents or downloads by product, all you can do is search.



Once you reach a page through search, there is no navigational link to take you back home, you have to use your browser's history.





I opened a support case with Datacolor to inform them of the Chrome incompatibility, in case they did not know, here is their response:





> Pieter, I just tried to download Google Chrome, but it seems that it is not available for MAC - which is the industry standard. That makes that browser not relevant for the time being if you ask me, as Windows is certainly not the choice of the platform in the visual world; which is where calibration matters.  
That said, our product works very well with both Windows and Mac, and I use it as a professional photographer, along countless others, so do not worry about browsers - this program has nothing to do with browsers and personal feelings/beliefs - it just calibrates your display/printer to icc standards and does it very well.  



So there you have it, according to Datacolor the Mac is the industry standard, and Windows does not matter, nor does their website's accessibility ;)







Things only got worse as I started reading their documentation.



The [product user guide](http://spyder.datacolor.com/downloads/manuals/Spyder3Elite_User_Guide.pdf "product user guide") is a PDF that looks like it was converted from HTML, there are a few random paragraphs that suddenly switch from a very readable white font on gray background to black on gray, e.g. see page 17, this is probably an artifact of the HTML to PDF conversion process.



The [step-by-step](http://spyder.datacolor.com/pdfs/step_by_step_en.pdf "step-by-step") PDF has a better layout but with random German text, e.g. see page 10, and with lots of spelling mistakes, e.g. see page 14 "Place the snsor on teh screen", obviously they never even ran a spell checker through the documents.







I know you think I am nitpicking, but I believe in paying attention to detail when delivering a product, and that sloppy work in one area will reflect sloppiness in all areas.





Ok, back to the calibration.







The Spyder3Elite software that came in the box was version 3.0.4, so I downloaded and installed the later 3.0.7 version software from the Datacolor website.





The installation was easy, and the software launched in the guided wizard mode.



It detected both monitors, allowed me to pick which monitor to calibrate, and as I picked a different monitor the UI automatically centered on that display.



In contrast with iMatch you had to launch the software, then move the window to the monitor you want to calibrate, then start the calibration.





I followed the wizard and calibrated both monitors, the colors looked "ok", not "great", and two monitors were not matched.





After closing the Spyder3Elite calibration software a tray icon remains running and it periodically monitors the ambient light, and also reminds you when the monitor needs to be re-calibrated. This time I am nitpicking, but they could really have picked a better looking tray icon than the blank white square, especially for a graphics company, or maybe since this is Windows and not Mac, the graphics does not really matter, right ;)







While researching calibration of the 2408WFP, I read about Integrated Color Corporation's [ColorEyes Display Pro](http://www.integrated-color.com/cedpro/coloreyesdisplay.html "ColorEyes Display Pro") software, and decided to give that a try.



The software is pretty expensive, but they did have a 10 day trial version available.





The installer installed several drivers that were not [Windows Hardware Quality Labs / Windows Hardware Logo](http://www.microsoft.com/whdc/winlogo/default.mspx "Windows Hardware Quality Labs / Windows Hardware Logo") certified, and Windows required me to accept several bright red warning dialogs during the install.





The software supports multiple calorimeter devices, I picked the Spyder 3 from the list, and performed a calibration.  

The 2408WFP monitor is supposed to support DDC, and the ColorEyes software is supposed to be able to control the monitor alleviating the need to perform manual adjustments, but for some unknown reason this did not work, so I had to make adjustments manually.



Compared to the quick calibration using the Spyder3Elite software, colors did look better, but to be fair at this point I have not done an advanced calibration with the Spyder3Elite software.





When it came time to calibrate the second monitor things did not go so well. The brightness calibration window opened, but after a few seconds it would just close again by itself. When I then tried to close the main window it would not close. I right clicked on the window in the taskbar, selected close, Windows told me the window is not responding, I selected to terminate the application, and my machine completely froze, requiring a hard boot. I assumed those drivers that did not pass Windows Hardware Logo Certification were to blame.



I opened a support case with Integrated Color Corporation to ask about DDC and the hang, and this was their response:



> The driver that comes up unsigned is for the dtp-94. Since the device is no longer in large production, that driver will likely never be signed. However I am sure that is not the issue. These drivers have been used by hundreds of users without an issue on Vista 64. It is more likely that you either have a usb port with a power issue or if you are trying to use ddc the communication is failing. Dell says all their monitors are ddc. However I have been going around and around with them asking for information about how to actually communicate with these monitors. Not only can they not give me any help, I don't think the actually know anything about ddc. No doubt there is some capability in them but Dell can't tell us how to access it. If they were using the standard ddc protocol it would be working. We actually support multiple protocols on Vista 64.  
I would be sure to choose lcd brightness and gains. And if that is not the problem I would try another usb port. If there is a usb hub involved I would avoid that as well. Let me know if that gets you through. If not perhaps we can get on the phone and work on this more easily.





That sounds like a reasonable explanation, and they certainly seem eager to help, I will give the ColorEyes software another go later.



I was interested in knowing if the monitor really did support DDC, so I tried the EnTech Taiwan [softMCCS utility](http://www.entechtaiwan.com/lib/softmccs.shtm "softMCCS utility").

The results confirmed that the monitor did support DDC, and I could control color, brightness, reset, etc. using the utility.

I replied to Integrated Color Corporation with this information, since EnTech provides a SDK, maybe they can use it to really support DDC.



While I was browsing around the EnTech site I found a great utility called [mControl](http://forums.entechtaiwan.com/index.php?topic=6725.0 "mControl") that allows adjustment of the DELL 2408WFP monitor settings:

[![](http://docs.google.com/File?id=dcmzmbww_7dnrmr9fb_b)](http://docs.google.com/File?id=dcmzmbww_7dnrmr9fb_b)



I wanted to try the advanced calibration options using the Spyder3Elite software, and I found several [video tutorials](http://spyder.datacolor.com/learn_videos.php "video tutorials") from Datacolor on how to calibrate dual monitors and how to match the monitors.



I performed the StudioMatch calibration, calibrating both monitors to 6500K, 2.2 Gamma, and 140cd/m², and I set both monitors to the RGB color profile.

Using the mControl software it was very easy to make changes to the monitor settings without needing to use monitor's buttons.



Event at a brightness of 0 the luminance was too high, and I had to lower the RGB values to reach the 140cd/m² mark.

The results were pretty good, both monitors ended up looking very similar, with just a slight difference in brightness between the two.



I tried to validate the results using ColorEyes, but the software would fail with "Sorry, An Error Occurred. kUUERR\_notFound".

I also found that the Spyder3Elite software fails to load the profiles created by ColorEyes.



I repeated the calibration this time using ColorEyes to calibrate both monitors, I used the same target values of 6500K, 2.2 Gamma, and 140cd/m².

This time I had not problems, and the results were about the same, again with one monitor appearing slightly brighter. I am actually beginning to wonder if the difference in observed brightness is really the monitor, or maybe the viewing angle or environment that makes it appear brighter.



The settings for Monitor 1:

Brightness: 24

Contrast: 51

Red: 80

Green: 76

Blue: 75



[![](http://docs.google.com/File?id=dcmzmbww_8nbqzjkd9_b)](http://docs.google.com/File?id=dcmzmbww_8nbqzjkd9_b)



[![](http://docs.google.com/File?id=dcmzmbww_997c27xdv_b)](http://docs.google.com/File?id=dcmzmbww_997c27xdv_b)



The settings for Monitor 2:

Brightness: 26

Contrast: 50

Red: 82

Green: 77

Blue: 75



[![](http://docs.google.com/File?id=dcmzmbww_10drtwrkhb_b)](http://docs.google.com/File?id=dcmzmbww_10drtwrkhb_b)



![](http://docs.google.com/File?id=dcmzmbww_11jbwvgk5v_b)





I went back and forth between Spyder3Elite and ColorEyes Pro, and with the current monitor settings, the visual results are about the same.

I think that if ColorEyes Pro actually performed the DDC adjustments automatically I may consider buying it, but right now I don't think it is worth the additional cost.



\[Update: 17 July 2009\]

I found that my DELL 2408WFP monitors kept loosing their settings when they wake from sleep, and this kept invalidating the calibration results.

Read about the problem and the solution [here](/2009/07/dell-2408wfp-loosing-settings-on-power.html).


