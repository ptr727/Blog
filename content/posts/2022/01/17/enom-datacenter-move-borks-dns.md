---
title: eNom Datacenter Move Borks DNS
date: '2022-01-17T19:52:26+00:00'
url: /2022/01/17/enom-datacenter-move-borks-dns/
categories:
- problem
tags:
- cloudflare
- dns
- enom
post_id: '2478'
cover:
  alt: '2022-01-17'
  image: /media/2022/01/2022-01-17.png
---
[eNom](https://www.enom.com/) really [borked](https://enomstatus.com/) their datacenter move resulting in two days and counting of no DNS.

I first noticed the issue Saturday (15 Jan 2022) night when my inbox remained clean for several hours, yes, I am one of those people that like to keep email organized and the inbox clean. A bit of head scratching and googling led me to a reddit [post](https://www.reddit.com/r/sysadmin/comments/s4ucsk/enom_dns_down_anything_on_nameservicescom_etc/) laying blame on the [Enom Data Center Migration](https://enomstatus.com/incidents/3k436lhwz878) [gone wrong](https://twitter.com/enomsupport/status/1483062015862054915).


{{< gallery cols="1" >}}  
{{< figure src="/media/2022/01/2022-01-17-1.png?w=959" alt="" caption="" >}}

{{< figure src="/media/2022/01/2022-01-17-2.png?w=958" alt="" caption="" >}}

{{< figure src="/media/2022/01/2022-01-17-3.png?w=958" alt="" caption="" >}}  
{{< /gallery >}}  

I registered my first domain in 2000 over a dialup modem. Over time I've registered several more domains with several registrars (based on regional or TLD requirements of the day). In 2006 I consolidated all my registrations with eNom, in 2011 eNom transferred my account to BulkRegister, and in 2020 BulkRegister transferred my account to [Hover](https://www.hover.com/). So, today I am a Hover customer, and Hover is an eNom reseller, using eNom DNS services.

My primary concern was getting [Google Workspaces](https://workspace.google.com/) email working again, no MX records, no email. I manage a few workspaces that are used for friends and family custom email, grandfathered in from the [Free Google Apps](https://support.google.com/a/answer/2855120?product_name=UnuFlow&hl=en&visit_id=637780444003600937-4274051864&rd=1&src=supportwidget0&hl=en#) days. The Hover portal was still working, and I do use [CloudFlare](https://www.cloudflare.com/) for some DNS services, so I tried changing the DNS servers on Hover from eNom to CloudFlare, but it failed with "Nameservers for \[domain\] cannot be registered". There was not much more to be done, so I waited.

Next day (16 Jan 2022) was more of the same, more [complaints](https://www.bleepingcomputer.com/news/security/enom-data-center-migration-mistakenly-knocks-sites-offline/), more [maintenance](https://enomstatus.com/), still can't change DNS. I tried transferring the domain, but I couldn't because I can't get an email with the transfer key, as I can't get email due to no MX records. Per canned advice from [@enomsupport](https://twitter.com/enomsupport) I sent an email to help@enom.com, from my gmail account, to this day never received a reply. Hover chat support said, sorry, need to wait for eNom.

Today (17 Jan 2022) I tried changing DNS at Hover again, no error, and although the web UI still reports the old eNom DNS servers, DNS did switch to CloudFlare. I re-registered the MX records at Google Workspaces domain management, and a couple minutes later email started flowing in.

I am busy switching DNS for all domains to CloudFlare, and as soon as possible I'll be transferring my domains away from eNom, or anybody associated with eNom.

So what have I learned?

- Never use eNom or any of their affiliates again. This is not the type of failure where an organization gets a second chance. Planning and executing a migration plan of this nature requires competent people, clearly they failed.
- Do not use the same company for domain registration and DNS services.
- Do not use an email address for service communication that is managed by that service.
- Keep restorable and portable file [backups](https://support.cloudflare.com/hc/en-us/articles/200168856-Importing-and-exporting-DNS-records) of DNS registrations. It is taking me a long time to recreate all the DNS entries by hand.
