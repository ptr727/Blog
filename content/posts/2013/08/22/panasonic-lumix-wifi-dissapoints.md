---
title: Panasonic Lumix WiFi Dissapoints
date: '2013-08-22T21:38:27+00:00'
url: /2013/08/22/panasonic-lumix-wifi-dissapoints/
categories:
- review
tags:
- lumix
- wifi
post_id: '396'
---
I've been a long time fan of [Panasonic Lumix](http://panasonic.net/avc/lumix/index.html) digital cameras, and I tend to update them every couple of years. My current cameras are the [DMC-ZS20](http://shop.panasonic.com/shop/model/DMC-ZS20K) for travel, and the [DMZ-ZS7](http://shop.panasonic.com/shop/model/DMC-ZS7K) for pocket use.

My workflow typically entails taking lots of pictures, and then using a [Transcend USB3 card reader](http://www.amazon.com/gp/product/B0056TYRMW/ref=as_li_ss_tl?ie=UTF8&camp=1789&creative=390957&creativeASIN=B0056TYRMW&linkCode=as2&tag=pievilsblo-20) and [ImageIngester Pro](http://basepath.com/site/detail-ImageIngester.php) to copy and rename them to my PC, and finally import them into Adobe Photoshop Lightroom. This is a tedious process, but with the release of the Lumix WiFi capable handheld cameras, an opportunity to make my life simpler by uploading directly using WiFi.

I bought the WiFi enabled [DMC-ZS30](http://www.amazon.com/gp/product/B00B3YSW5W/ref=as_li_ss_tl?ie=UTF8&camp=1789&creative=390957&creativeASIN=B00B3YSW5W&linkCode=as2&tag=pievilsblo-20) to replace my DMC-Z20, and a [DMC-TS5](http://www.amazon.com/gp/product/B00ATE7ULY/ref=as_li_ss_tl?ie=UTF8&camp=1789&creative=390957&creativeASIN=B00ATE7ULY&linkCode=as2&tag=pievilsblo-20) to replace my DMC-ZS7. The TS5 is not really an upgrade to the ZS7, but it is waterproof, shockproof, and kids-proof.

The cameras were typical great Lumix quality, but my interest was the WiFi capability.

The camera offers several modes of connecting, I setup the PC WiFi connected option. During the setup process you have to select the access point SSID, in my case I have a couple roaming enabled access points around me, and the camera showed multiple access points with the same SSID. I've seen this behavior in some devices that bind to a specific access point, and these devices would refuse to roam, requiring a new setup for every single access point.

It did not really matter as the camera would not connect, it would ask for my password, but fail to connect. My camera was running firmware 1.0, and there was a [v1.2 available](http://panasonic.jp/support/global/cs/dsc/download/TZ40_TZ41_ZS30/index.html), I upgraded, and the WiFi connection succeeded. The firmware notes say nothing about WiFi connectivity, but for whatever reason it helped.

First big frustration; every time anything in the connection setup flow fails, you have to re-enter the WiFi password, the login username, and the password, very painful when using a navigation only keyboard, and long complicated passwords. It would have been much more convenient to configure WiFi in one place, save the WiFi connection, and then configure transfer profiles, or at least always remember the previously entered values.

PC connectivity requires a SMB network share and a named host, i.e. no support for any protocol other than SMB, and no support for entering servers by IP address.

I could not get the camera to connect to my server, looking at the security logs, I could see that the connection was using "WORKGROUP" as the domain, and using the DOMAIN portion of  \[DOMAIN\\UserName\] specification as part of the literal username. The camera has no provisioning for changing the workgroup or domain, and I had to resort to creating a machine local account in order to connect. Once I had my local account created, and again re-entered all information, I could finally connect.

I took some pictures, pressed the WiFi button, navigated to the profiles, and uploaded the pictures, it took forever, around 90s per 5MB average picture, or around 400Kbps. Using my USB3 card reader the same pictures all transferred in a few seconds. Yes, USB3 is much faster than WiFi 802.11n, but 400 kilo bits per second is super slow, not near the capability of the WiFi network.

I also tried the [Panasonic Lumix Club](http://lumixclub.panasonic.net/) Cloud Sync service, what a joke. You setup the account from the camera, it reports your a username in the form of aaaa-bbbb-cccc-dddd, then you enter your own password, but when you try to login at the website, that you need to find using google, you need to use aaaabbbbccccdddd. I only discovered this through trial and error.

On logging in, you need to supply an email address, and then validate the email address, by clicking a link emailed to you. On clicking the link, it takes you to the service page, and it displays an error message, any action more errors. If you manually login again, you are in.

From there nothing works. From what I can tell from FAQ's, you are supposed to be able to create a drop that allows you to pull the data from the cloud to your PC. But when you go to configure the devices and services, none of the links work.

What Panasonic should have done is build a very simple get connected flow, many small complicated devices today use a USB connection and an app, PC or mobile, to get the device provisioned, there are many other novel ways of simplifying this process, e.g. QR codes, BT, P2P, SD card data file, etc. Not supporting FTP, or IP addresses, or domain credentials, or workgroup configurations would be forgiven if connecting was easy, and transfer speed was at WiFi capacity, sadly, it is not.

From my perspective the WiFi capability on these cameras are a waste of good silicon and battery power.
