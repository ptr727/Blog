---
title: Printing from the network
date: '2008-03-31T06:15:00+00:00'
url: /2008/03/30/printing-from-network/
categories:
- solution
post_id: '72'
---
I have made various attempts at sharing my printer over my home network. The criteria for sharing are simple; the printer must be available over the network and I must be able to print from Windows and Mac machines.
In practice this turned out to be a little more difficult.

The simplest solution would have been a network enabled printer, but I had no luck in finding an affordable consumer grade home printer that can directly connect to the network.

My first implementation was to connect a Canon i960 to my Windows XP machine using USB, and then sharing the printer. This had a few problems; my machine had to be on all the time, the Windows XP x64 Canon i960 driver crashed when connected to a network shared printer, and the Canon i960 Mac driver could not print to a network shared printer.

The Canon i960 had given me good service, but I was now looking for a better photo printer. I decided to upgrade a few systems at the same time; I upgraded to Vista, I bought a HP D7360 Photosmart printer, and I bought a Belkin [F5L009](http://www.belkin.com/support/product/?lid=en&pid=F5L009&scid=1) network USB hub.

The F5L009 is a USB hub that you connect to your network, and then by installing a USB driver on any computer on the network, the USB devices connected to the hub appear to be directly connected to your machine.

At this time I was running Windows Server 2003 R2 x64 as my home server, and since the server was on all the time, I wanted to share the printer from the server. I installed the USB hub driver on the server, and I installed the printer driver. It turns out that the hub software only connects the hub as long as you are logged in, as soon as you log out the printer disconnects. This is in my opinion a fatal flaw in the F5L009 implementation.
I resorted to installing the F5L009 driver on all my client machines, a less than ideal solution.

I recently noticed that HP released the [D7460](http://www.shopping.hp.com/webapp/shopping/product_detail.do?landing=photography&storeName=storefronts&category=printer&catLevel=2&product_code=CC247A%23B1H) printer, basically the same as the D7360 except it has native network printing support, great. With a $25 HP online store discount I paid less for the D7460 than what I paid for the D7360.

Since the D7460 is a network printer any machine can directly print to the printer, but sharing the printer from my server has the advantage of a much simplified installation for client machines, and greater manageability.

I had recently upgraded my server to Windows Server 2008 x64, but I thought no problem, the D7460 comes with Vista x64 drivers, so installing the driver on W2K8 x64 should not be a problem. It turns out the driver installer does an OS check and does not allow the driver to be installed on W2K8.

I proceeded to install the driver on my Vista x64 machine, the install utility found the network printer, and automatically installed the driver. On investigation I found that the installer had simply configured a custom printer port to print to TCP port 9001 on the printer. I also found that the printer has a web based management portal that showed status information and allowed the network properties such as device name to be changed.

I changed the printer network device name, made sure that the entry showed up on the DNS server, added a new printer port in W2K8 pointing to the printer, and when asked for the driver pointed to the driver directory, and everything worked fine.

I wanted to add the x86 drivers to the print server so that clients can automatically get the printer driver without neding access the the driver media, but when I tried to add the drivers I got a message asking for the x86 print processor file from the install media. I tried to add the x86 drivers to the server from an x86 Vista machine, but the option to add additional drivers was grayed out. After searching I found users with [similar](http://www.experts-exchange.com/Hardware/Peripherals/Printers_Scanners/HP/Q_23167078.html) problems, and [KB927832](http://support.microsoft.com/kb/927832) describing a solution for Vista. I could not get the solution to work.
I ended up remotely installing the x86 drivers from W2K8 x86 running in VMWare, not very elegant but it worked.

I now have an elegant network printing solution.


