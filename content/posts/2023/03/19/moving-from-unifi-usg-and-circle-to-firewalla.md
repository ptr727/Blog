---
title: Moving from UniFi-USG and Circle to Firewalla
date: '2023-03-19T15:56:14+00:00'
url: /2023/03/19/moving-from-unifi-usg-and-circle-to-firewalla/
categories:
- network
- performance
- review
tags:
- circle
- firewalla
- parentalcontrol
- unifi
post_id: '2666'
cover:
  alt: image-11
  image: /media/2023/03/image-11.png
---
I replaced my aging [UniFi Security Gateway Pro](https://store.ui.com/products/unifi-security-gateway-pro) and slow [Circle Home Plus](https://meetcircle.com/products/circle-home-plus-parental-controls) with a [Firewalla Gold Plus](https://firewalla.com/products/firewalla-gold-plus), giving me gigabit speed firewall and parental controls in a single easy to use and actively developed device.

Why Firewalla? We have 1Gbps internet, and I want a feature rich firewall that can operate at line speed. We do configure Apple, Google, Microsoft, Amazon, Netflix, Hulu, Disney, etc. (homogeneous control remains lacking) child account restrictions, but I also want content control and visibility for any network connected devices. Firewalla is at the intersection of high speed and visibility and parental controls.

First a bit of history on parental controls; when our kids were young I used [OurPact](https://ourpact.com/) on their iPad's, as they got older and started using other devices, I switched to using [Circle](https://meetcircle.com/). OurPact uses Mobile Device Management (MDM) to control almost all aspects of the device, and it was really very good, but at the time iOS only, and the kids started using Chromebooks for school and Windows laptops for gaming. I switched from OurPact to Circle, a home network router, that works with any home network connected device, and a VPN profile for mobile devices. A big problem with Circle is slow network performance, for filtered content Circle often gets less than 30Mbps and with high latency. My kids were constantly complaining that I made them use "the slow network", and any connectivity issue or game lag was blamed on the Circle, often with cause.

Before I get to the Firewalla, I'll describe how I installed and configured the Circle such that it was only used for some network devices, leaving the majority of my network untouched. Circle has only one ethernet port, and uses [ARP spoofing](https://en.wikipedia.org/wiki/ARP_spoofing) to become the network gateway. To keep the Circle and its ARP spoofing isolated from my primary network, I created a new VLAN network and new WiFi SSID to use as a parental control enabled network. I plugged the Circle LAN port into a switch with the switch port configured to the parental control VLAN, and I changed the kids devices to connect to the parental control WiFi.

[![](/media/2022/11/screenshot-2022-11-14-085346.png)](/media/2022/11/screenshot-2022-11-14-085346.png?w=1024)

[![](/media/2022/11/screenshot-2022-11-14-085935.png)](/media/2022/11/screenshot-2022-11-14-085935.png?w=1024)

[![](/media/2022/11/screenshot-2022-11-14-090143.png)](/media/2022/11/screenshot-2022-11-14-090143.png?w=1024)

My network consists exclusively of [Ubiquity](https://www.ui.com/) UniFi managed equipment, and switching from the USG-Pro-4 router to the Firewalla Gold Plus router was not trivial. It is unfortunate that Ubiquity never invested in nor supported 3rd party content control integration with their routers, it is just part of the very typical Ubiquity love hate relationship.

I wanted to configure the Firewalla without replacing my USG router, and without disrupting my network. I created a 10.0.0.1/8 private class A network, that would look like a NAT'ing ISP, and associated this network with a switch port. I unboxed the Firewalla, and followed the [installation guide](https://help.firewalla.com/hc/en-us/articles/360046669734-Firewalla-Gold-Installation-Guide), using my "ISP network" for the WAN port, and a laptop connected to the Firewalla LAN port.

[![](/media/2023/03/image.png)](/media/2023/03/image.png?w=1024)

[![](/media/2023/03/image-1.png)](/media/2023/03/image-1.png?w=1011)

The Firewalla onboarding requires the use of a mobile app, and Bluetooth for discovery, and scanning a QR code on the device for authentication. Onboarding was very easy using the mobile app, but is unfortunately that the mobile app is the only way to configure the Firewalla. I understand product managers views of a mobile first world, but configuring a firewall is not like texting, and I would much prefer using web based configuration, where I can see and edit lots of information on a large screen using a keyboard. There is a [web portal](https://help.firewalla.com/hc/en-us/articles/360052779253-The-Firewalla-Web-Interface) showing lots of information, but configuration is currently very limited. An [MSP web interface](https://help.firewalla.com/hc/en-us/articles/4409866753427-Firewalla-Managed-Security-Portal-Introduction) is in the works, and I hope it would allow for more web based configurability.

It was easy, even on the phone, to configure my networks and VLAN's to match my USG configuration.

[![](/media/2023/03/img_3712.png)](/media/2023/03/img_3712.png?w=472)

[![](/media/2023/03/img_3713.png)](/media/2023/03/img_3713.png?w=472)

[![](/media/2023/03/img_3714.png)](/media/2023/03/img_3714.png?w=472)

[![](/media/2023/03/img_3715.png)](/media/2023/03/img_3715.png?w=472)

Adding DNS entries was not so simple. Firewalla has great [DNS support](https://help.firewalla.com/hc/en-us/articles/4570608120979-Firewalla-DNS-Services-Introduction), including [DNS over HTTPS (DoH)](https://help.firewalla.com/hc/en-us/articles/360038449734-DNS-over-HTTPS) and [Unbound](https://help.firewalla.com/hc/en-us/articles/4556423309587-DNS-Service-Unbound-), but only a simple phone UI for A records. I use [Ansible](https://www.ansible.com/) to configure my home lab, including lots of A and CNAME records via a UniFi configuration file, so I needed a manual alternative, or until I add Firewalla configuration support to my Ansible deployment. Firewalla runs Ubuntu and the device [can be accessed](https://help.firewalla.com/hc/en-us/articles/360007345553-Fun-Things-To-Do-with-Firewalla) via SSH, and SSH can be accessed via [VSCode](https://code.visualstudio.com/docs/remote/ssh), alleviating the need for cumbersome CLI editing of config files. Per the [docs](https://help.firewalla.com/hc/en-us/articles/360056024294) DNS entries would typically go in `~/.firewalla/config/dnsmasq_local/`, but on closer inspection the mobile app added entries show up in `~/.firewalla/config/dnsmasq/policy_15.conf`. I was reluctant to mix configurations, and opted to use the file based method for A and CNAME records. (See later for an update, turns out CNAME's did not work and I had to convert them to A records.)

[![](/media/2023/03/img_3718-2.png)](/media/2023/03/img_3718-2.png?w=472)

[![](/media/2023/03/2023-03-18-2.png)](/media/2023/03/2023-03-18-2.png?w=1024)[![](/media/2023/03/2023-03-18-3.png)](/media/2023/03/2023-03-18-3.png?w=1024)[![](/media/2023/03/2023-03-18-5.png)](/media/2023/03/2023-03-18-5.png?w=1024)

Now that Firewalla was mostly configured, it was time to prepare for removing the USG from the network, but keeping the AP and switch configurations. I could not find any good references for doing this, with many reports of problems along the way. I made a configuration backup, removed all DHCP reservations, and deleted the `config.gateway.json` file. Firewalla has not yet released a [rackmount kit](https://www.reddit.com/r/firewalla/comments/114vahr/feedback_needed_firewalla_gold_rack_mounting_kit/), so for now I just placed it in my server rack on a shelf, like I did with the old Circle. I swapped the LAN and WAN cables from USG to the Firewalla, and waited...

[![](/media/2023/03/img_3722.jpg)](/media/2023/03/img_3722.jpg)

[![](/media/2023/03/img_3723.jpg)](/media/2023/03/img_3723.jpg)

My phone started beeping furiously with Firewalla new device discovered notifications, and logging back into the web portal I could see new devices being discovered. I had to change my phone's notification settings and the Firewalla alarm configuration to stop the constant alerts.

[![](/media/2023/03/image-2.png)](/media/2023/03/image-2.png?w=620)

[![](/media/2023/03/img_3724.png)](/media/2023/03/img_3724.png?w=472)

Most things seemed to at least have internet connectivity, but we'll see how things go when DHCP clients start renewing, and how existing clients with old DHCP issued IP's would conflict with new DHCP assignments.

I quickly noticed that CNAME's were not working, while it looks like A names were correctly resolving. I was pretty sure this did work when I tested standalone, so my testing was either using the upstream DNS server, or something changed after the power cycle. The DNS page showed that both DoH and Unbound was enabled, and I'm sure that is not supposed to be [allowed](https://help.firewalla.com/hc/en-us/articles/4570608120979-Firewalla-DNS-Services-Introduction#:~:text=these%20services%20are%20mutually%20exclusive) for the same targets, " _these services are mutually exclusive_"? I disabled DoH, but it did not seem to make a difference, CNAME resolution was still not working. Looking closer at the dnsmasq and unbound docs, CNAME resolution only works for externally resolvable records, so I converted all my CNAME records to A records, restarted the `firerouter_dns` service, and now names resolved as expected.

Going back to UniFi, it was not happy, it showed that most of the switches failed adoption, but the AP's were ok. I removed the USG from the configuration, changed all the networks to no DHCP and 3rd party gateway (I should probably have done this earlier), and restarted the UniFi docker container, still failed to adopt. I noticed some of the switches reported a 192.168.8.x address, so I tried power cycling a switch, and it came back online. I did not feel like walking around power cycling all switches, so I'm going to wait and see if they come back up by themselves, maybe when DHCP refreshes, and by the next morning all devices reported online.

[![](/media/2023/03/image-5.png)](/media/2023/03/image-5.png?w=586)

[![](/media/2023/03/image-3.png)](/media/2023/03/image-3.png?w=620)[![](/media/2023/03/image-4.png)](/media/2023/03/image-4.png?w=620)[![](/media/2023/03/image-7.png)](/media/2023/03/image-7.png?w=620)

With the USG I updated my dynamic DNS IP using [DNS-O-Matic](https://www.dnsomatic.com/), that in turn changed a [CloudFlare](https://www.cloudflare.com/) A record. Firewalla provides built in dynamic DNS support, and I simplified my public DNS configuration by changing from an A record to a CNAME pointing to `xxx.d.firewalla.org`. Port forwarding is configured under the NAT settings, and I just need SSL forwarded to my [Taefik](https://traefik.io/) proxy that takes care of the rest.

[![](/media/2023/03/img_3726.png)](/media/2023/03/img_3726.png?w=472)

[![](/media/2023/03/image-6.png)](/media/2023/03/image-6.png?w=472)

I use a captive portal WiFi guest network, hosted by the UniFi controller, and I had to open access from the guest VLAN network to the UniFi controller. The network intercept is implemented on the AP's and on the USG, but with Firewalla ethernet based captive portal no longer works, while WiFi still does. Native captive portal support would be preferred.

![](/media/2023/03/img_3727.png)

![](/media/2023/03/image-10.png)

As DHCP renewed on my machine, I noticed that name resolution using only the hostname, not the FQDN was failing. I.e. `ping foo` fails, ping `foo.bar.net` succeeds. On inspection I found that DHCP was not setting the DNS suffix. Firewalla seems to use a [different](https://help.firewalla.com/hc/en-us/articles/1500002445242-Difference-between-Search-Domain-Local-Domain) configuration for local domain vs. domain suffix, where I'd expect a per network configuration, regardless, the DHCP configured DNS search suffix seems to be missing.

[![](/media/2023/03/image-9.png)](/media/2023/03/image-9.png?w=620)

[![](/media/2023/03/image-8.png)](/media/2023/03/image-8.png?w=620)

[![](/media/2023/03/screenshot-2023-03-19-075444.png)](/media/2023/03/screenshot-2023-03-19-075444.png?w=657)

As far as parental controls go, the biggest gaps are lack of time based management (that I'm using much less as the kids got older, and I get great usage reports from Microsoft Family), and a single button to stop the internet, that does wonders if kids need a bit of motivation to get something done. There is a [Social Hour](https://help.firewalla.com/hc/en-us/articles/360008214094-Activity-and-Parental-Control#:~:text=Social%20Hour%20temporarily%20blocks%20social,enjoy%20some%20family%20social%20time.) setting, but it only blocks social networking activity, not quite effective at stopping game play.

Performance wise I can't tell a difference between the network with family controls enabled, and the one without.

[![](/media/2023/03/2023-03-19.png)](/media/2023/03/2023-03-19.png?w=416)

It's been about a day since installation, so too early for a conclusion, but here are some initial thoughts:

- I miss the all-in-one management view I got from UniFi, I now need to use two tools for network configuration.
- Initial setup on the phone was easy, but I'd expect to be able to use the phone or web for configuration, especially for bulk configuration tasks, e.g. nobody wants to enter many DNS entries from a phone.
- Native support for captive portals are missing, but my WiFi captive portal still works via UniFi, just not for LAN access as enforcement is now only in the AP's, not on the router.
- Having SSH access and the ability to directly configure services is powerful, but also concerning when the docs [say](https://help.firewalla.com/hc/en-us/articles/360056024294#:~:text=This%20is%20not%20officially%20supported%20and%20is%20not%20guaranteed%20to%20work%20long%20term.) " _not officially supported and is not guaranteed to work long term_".
- The web dashboard is very informative, giving insights into what is happening on the network.
- I'd prefer a rackmount form factor, will buy one when it becomes available.
- I miss a single "stop the internet" button for parental controls.
- Performance is great for normal and family networks.
- I'll open a support case for DoH and Unbound being on at the same time for the same targets, and for DHCP missing the DNS search suffix, will report back when I hear from Firewalla support.

**\[Update 1 on DHCP DNS search suffix issue on Win11\]**

- I noticed my Ubuntu laptop did get the correct DNS suffix, while none of my Win11 machines did.
- I did some testing using the [dhcptest](https://github.com/CyberShadow/dhcptest) utility, and option 119 is passed through, and although the text is not decoded (119 decoding is not implemented, and I [could not get](https://github.com/CyberShadow/dhcptest/issues/28) my change to compile in Windows), converting to ASCII looks correct.
- Looks like the [intended](https://github.com/systemd/systemd/issues/13903) [behavior](https://learn.microsoft.com/en-us/windows-server/networking/technologies/dhcp/what-s-new-in-dhcp) is to use option 119 if set and ignore 15 if 15 and 119 is set.
- Verified behavior in Windows Server 2022 that shows the domain as not set but DNS search suffix as set.
- Some more searching I found that apparently option 119 is broken in Win11, was supposed to be [fixed](https://support.microsoft.com/en-us/topic/april-25-2022-kb5012643-os-build-22000-652-preview-expired-43a75ee7-d857-4943-a2b9-f961538bd2b0#:~:text=Dynamic%20Host%20Configuration%20Protocol%20(DHCP)%20option%20119), but is still [broken](https://learn.microsoft.com/en-us/answers/questions/779236/windows-11-vs-windows-10-reciving-dns-suffix-searc?page=2&orderby=Helpful&comment=answer-1186490#newest-answer-comment).
- This leads me to believe that the USG may have used DHCP option 15 (domain name), or option 15 and option 119 (DNS search), but not just option 119.

[![](/media/2023/03/screenshot-2023-03-19-143337.png)](/media/2023/03/screenshot-2023-03-19-143337.png?w=620)

[![](/media/2023/03/image-12.png)](/media/2023/03/image-12.png?w=620)

[![](/media/2023/03/image-13.png)](/media/2023/03/image-13.png?w=620)

**\[Update 2 on DHCP DNS search suffix issue on Win11\]**

- Firewalla support suggested that I could change the dnsmasq DHCP config from tag from 119 to 15. I instead opted to add 15, thus hoping to keep the desired 119 behavior.
- DHCP is configured per adapter in e.g. `.router/config/dhcp/conf/br0.conf`, and I added a domain name tag to the list of tags `dhcp-option=tag:br0,15,home.insanegenius.net`
- Testing shows that the domain is now correctly set on Win11, and dhcptest confirms that both tag 15 and 119 is set.
- I will revert the change when Win11 updates to correctly support DHCP option 119.

[![](/media/2023/03/image-16.png)](/media/2023/03/image-16.png?w=620)

[![](/media/2023/03/image-17.png)](/media/2023/03/image-17.png?w=620)

[![](/media/2023/03/image-18.png)](/media/2023/03/image-18.png?w=620)

[![](/media/2023/03/image-19.png)](/media/2023/03/image-19.png?w=620)
