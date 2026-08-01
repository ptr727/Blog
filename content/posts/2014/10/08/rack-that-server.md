---
title: Rack that server
date: '2014-10-09T00:24:34+00:00'
url: /2014/10/08/rack-that-server/
categories:
- review
- storage
tags:
- adaptec
- hitachi
- samsung
- supermicro
post_id: '576'
cover:
  alt: After
  image: /media/2014/10/after.jpg
---
It's been a year and a half since we moved into the new house, and I finally have the servers racked in the garage. Looks pretty nice compared to my old setups.

My old setup was as follows:
Two DELL OptiPlex 990 small form factor machines with Windows Server 2008 R2 as Hyper-V servers. One server ran the important 24/7 VM's, the other was used for testing and test VM's. The 24/7 VM's included a W2K8R2 domain controller and a W2K12 file server.
For storage I used a [Synology DS2411+](http://www.amazon.com/gp/product/B0057LA7KU/ref=as_li_tl?ie=UTF8&camp=1789&creative=390957&creativeASIN=B0057LA7KU&linkCode=as2&tag=pievilsblo-20&linkId=7QPTMJCWPCQX5SR3) NAS, with 12 x 3TB Hitachi Ultrastar drives, configured in RAID6, and served via iSCSI. The the iSCSI drive was mounted in the Hyper-V host, and configured as a 30TB passthrough disk for the file server VM, that served files over SMB and NFS.
These servers stood on a wooden storage rack in the garage, and at the new house they were temporarily housed under the desk in my office.

One of my primary objectives was to move the server equipment to the garage in an enclosed server rack, with enough space for expansion and away from dust. A garage is not really dust free and does get hot in the summer, not an ideal location for a server rack, but better than finding precious space inside the house. To keep dust to a minimum I epoxy coated the floor and installed foam air filters in the wall and door air inlet vents. To keep things cool, especially after parking two hot cars, I installed an extractor fan. I had planned on connecting it to a [thermostat](http://www.amazon.com/gp/product/B00368D6JA/ref=as_li_tl?ie=UTF8&camp=1789&creative=390957&creativeASIN=B00368D6JA&linkCode=as2&tag=pievilsblo-20&linkId=I223TIC4HPRAWJLQ), but opted to use a [Panasonic WhisperGreen](http://www.amazon.com/gp/product/B004UHUCVG/ref=as_li_tl?ie=UTF8&camp=1789&creative=390957&creativeASIN=B004UHUCVG&linkCode=as2&tag=pievilsblo-20&linkId=MWME5CRGRQJHRYG2) extractor fan rated for 24/7 operation, and I just leave it on all the time. We have ongoing construction next door, and the biggest source of dust are the gaps around the garage door. I've considered applying sticky foam strips next to the garage door edges, but have not done so yet.

In retrospect, preparing the garage concrete surface by hand, and applying the [Epoxy Coat](http://www.amazon.com/gp/product/B00C7VX2V4/ref=as_li_tl?ie=UTF8&camp=1789&creative=390957&creativeASIN=B00C7VX2V4&linkCode=as2&tag=pievilsblo-20&linkId=YAKWMNU7RZM3EPSK) kit by myself, is not something I would recommend for a novice. If you can, pay a pro to do it for you, or at least get a friend to help, and rent a diamond floor abrasion machine.

I did half the garage at a time, moving everything to one side, preparing the surface by hand, letting it dry, applying the epoxy and flakes, letting it dry, and then repeating the process for the other side. I decided the 7" roller that came with the kit was too small, and I bought a 12" roller, big mistake, as soon as I started rolling the epoxy there was lint everywhere. From the time you start applying the epoxy you have 20 minutes working time, no time to go buy the proper type of lint free roller. I did not make the same mistake twice, and used the kit roller for the second half, no lint. With the experience gained from the first half it was much easier the second time round, and the color flake application was also much more even compared to the first half.

To conserve space in the garage I used a Middle Atlantic [WR-24-32](http://www.middleatlantic.com/products/racks-enclosures/slide-out-racks/wr-series-roll-out-rotating-rack/wr-24-32.aspx) WR Series Roll Out Rotating Rack. The roll out and rotate design allowed me to mount the rack right against the wall and against other equipment, as it does not require rear or side panel access. I also used a low noise [MW-4QFT-FC](http://www.middleatlantic.com/products/racks-enclosures/tops/mw-series-top-options/mw-4qft-fc.aspx) thermostatically controlled integrated extractor fan top to keep things cool, and a [WRPFD-24](http://www.middleatlantic.com/products/racks-enclosures/front-doors/pfd-series-plexi-front-doors/wrpfd-24.aspx) plexiglass front door to make it look nice.

The entire interior cage rolls out on heavy duty castors, and the bottom assembly rotates on ball bearings. The bottom of the enclosure is open in the center with steel plate tracks for the castors, and must be mounted down on a sturdy and level surface. My garage floor is not level and slopes towards the door, and consequently a fully loaded rack wants to roll out the door, and all the servers keep sliding out of the rails.

I had to level the enclosure by placing spacers under the front section, and then bolting it down on the concrete floor. This leaves the enclosure and the rails inside the enclosure level, but as soon as I pull the rack out on the floor, the chassis slide out and the entire rack wants to roll out the door. I had to build a removable wood platform with spacers to provide a level runway surface in front of the rack, that way I can pull the rack out on a level surface, and store the runway when not in use.

The WR-24-32 is 24U high, and accommodates equipment up to 26" in length, quite a bit shorter than most standard racks. The interior rack assembly pillar bars are about 23" apart, with equipment extending past the pillar ends. This turned out to be more of a challenge than the 26" equipment length constraint. When the rack is in its outside rotated position, the 23" pillars just clears the enclosure, but the 26" equipment sticking out past the pillars do not, and prevents the rack from rotating. This requires brute force to lift the castors, and a very heavy loaded rack, over the rail edge and pull the enclosure out all the way before the rack would rotate freely.

Another problem with the 23" pillar spacing is the minimum adjustable distance for the 4U Supermicro chassis rails is about 25", and they would not fit between the pillars. I had to order a shorter set of adjustable rails, and use the chassis side of the original rails to match the chassis mounting holes, and the rack side of the rails to clear the pillars, fortunately they fit perfectly into each other, but not on the rack. The WR-24-32 has tapped 10-32 screw holes in all locations, i.e. no square holes anywhere, which meant I had to use my Dremel to cut the quick mount tabs from the rails in order to screw them on instead of hanging them on.

Rather than using another NAS based storage solution I opted for direct attached storage, so I was looking for a 24-bay chassis, less than 26" in length, with low noise fans. I opted for a Supermicro 4U 24-bay SuperChassis [846BE16-R920B](http://www.supermicro.com/products/chassis/4U/846/SC846BE16-R920.cfm) for the main file server, and a 4U 8-bay SuperChassis [745BTQ-R1K28B-SQ](http://www.supermicro.com/products/chassis/4U/745/SC745BTQ-R1K28-SQ.cfm) for the utility server. It was the SC846's included rails that were too long to fit between the posts, and I replaced them with a MCP-290-00058-0N short rail set.

I used Supermicro [X10SLM+-F](http://www.supermicro.com/products/motherboard/xeon/c220/x10slm_-f.cfm) Xeon boards with Intel [Xeon E3-1270 v3](http://ark.intel.com/products/75056/Intel-Xeon-Processor-E3-1270-v3-8M-Cache-3_50-GHz) processors for both systems. Low power and low heat was a higher priority than performance, and the E3 v3 processors were a good balance. I've had good experiences with the X9 series SM boards, but I have mixed feelings about the X10 boards. Kingston dropped support for these boards due to memory chip incompatibilities, and SM certified memory for this board is very expensive, and I had endless troubles getting the boards to work with an [Adaptec 7805Q](http://www.adaptec.com/en-us/products/series/7q/) controller. The 7805Q controller would simply fail to start, and after being bounced around between SM and Adaptec support, SM eventually provided me with a special [BIOS](http://www.supermicro.com/support/faqs/faq.cfm?faq=18859) build, that is yet to be publicly updated, that resolved the problem. I had no such problems with the newer [81605ZQ](http://www.adaptec.com/en-us/products/series/8q/) controller I used in the 24-bay chassis.

For the 24-bay system storage, I used 2 x [Samsung 840 Pro 512GB](http://www.amazon.com/gp/product/B009NB8WRU/ref=as_li_tl?ie=UTF8&camp=1789&creative=390957&creativeASIN=B009NB8WRU&linkCode=as2&tag=pievilsblo-20&linkId=NNTGV3LACDC4NIM7) SSD drives in RAID1 for booting the OS and for MaxCache, 4 x [Samsung 840 EVO 1TB](http://www.amazon.com/gp/product/B00E3W16OU/ref=as_li_tl?ie=UTF8&camp=1789&creative=390957&creativeASIN=B00E3W16OU&linkCode=as2&tag=pievilsblo-20&linkId=HZEDPSSGHSVH24T7) SSD drives in RAID5 to host VM's, 16 x [Hitachi 4TB Coolspin](http://www.amazon.com/gp/product/B005SZ8NE2/ref=as_li_tl?ie=UTF8&camp=1789&creative=390957&creativeASIN=B005SZ8NE2&linkCode=as2&tag=pievilsblo-20&linkId=5SHR3KDWUBZFKLKP) drives plus 2 x hot spares in RAID6 for main storage. The 56TB RAID6 volume is mounted as a passthrough disk to the file server VM. To save power and reduce heat I host all the VM's on the SSD array, and opted to use the consumer grade Hitachi Coolspin drives over the more expensive but reliable Ultrastar drives. The 8-bay system has a similar configuration, less the large RAID6 data array.

The SM boards are very easy to manage using the integrated IPMI KVM functionality. Other than configuring the BIOS and IPMI IP settings on the first boot, I rarely have to use the rack mounted KVM console. Each server runs W2K12R2 with the Hyper-V role. I am no longer running a domain controller, the complexity outweighed the benefit, especially with the introduction of Microsoft online accounts used in Windows 8. The main VM is a W2K12R2 storage file server VM, with the RAID6 disk in passthrough, serving data over SMB and NFS. My other VM's include a system running [Milestone XProtect](http://www.milestonesys.com/) IP security camera network video recorder, a [MSSQL](http://www.microsoft.com/en-us/server-cloud/products/sql-server/) and [MySQL](http://www.mysql.com/) DB VM, a [Spiceworks](http://www.spiceworks.com/) VM, a [Splunk](http://www.splunk.com/) VM, a [UniFi Controller](http://www.ubnt.com/enterprise/) VM, and several work related VM's.

I had Verizon switch my internet connection from Coax to Ethernet, and I now run a [Ubiquity EdgeRouter Pro](http://www.ubnt.com/edgemax/edgerouter-pro/). I did run a MiktroTik Routerboard [CCR1009-8G-1S-1S+](http://routerboard.com/CCR1009-8G-1S-1Splus) for a while, and it is a very nice box, but as I also switched out my EnGenius [EAP600](http://www.engeniustech.com/business-networking/indoor-access-points-client-bridges/16598-eap600-new) access points to Ubiquity [UniFi AC](http://www.ubnt.com/unifi/unifi-ap-ac/) units, and I replaced the problematic TRENDNet [TPE-1020WS](http://www.trendnet.com/support/supportdetail.asp?prod=190_TPE-1020WS) POE+ switches with Ubiquity ToughSwitch [TS-8-Pro](http://www.ubnt.com/accessories/toughswitch/) POE units, I preferred to stick to one brand in the hopes of better interoperability. Be weary of the ToughSwitch units though, seems that under certain conditions mixing 100Mbps and 1Gbps ports have serious performance [problems](http://community.ubnt.com/t5/ToughSwitch/The-new-and-improved-low-throughput-thread/td-p/904008). I am still on the fence about the UniFi AC units, they are really easy to manage via the UniFi controller, but some devices, like my Nest thermostats, are having problems staying connected. Not sure if it is a problem with access points or the Nest's, as there are many people [blaming](https://community.nest.com/message/25610) this problem on a Nest firmware update.

I used an APC [Smart-UPS](http://www.apc.com/products/resource/include/techspec_index.cfm?base_sku=SMX1500RM2UNC&xtmc=SMX1500RM2UNC&xtcr=1) X 1500VA Rack/Tower LCD 120V with Network Card for clean and reliable power, and an ITWatchDogs [SuperGoose II](http://www.itwatchdogs.com/climate-monitor-supergoose-ii-p11.html) Climate Monitor for environmental monitoring and alerting.

After building and configuring everything, I copied all 30TB of data from the DS2411+ to the new server using robocopy with the multithreaded option, took about 5 days to copy. I continued using the old systems for two weeks while I let the new systems settle in, in case anything breaks. I then re-synced the data using robocopy, moved the VM's over, and pointed clients to the new systems.

VM's are noticeably more response, presumable due to being backed by SSD. I can now have multiple XBMC systems simultaneously watch movies while I copy data to storage without any playback stuttering, something that used to be an issue on the old iSCSI system.

The best part is really the way the storage cabinet looks :)

This is the temporary server home under my office desk:
[![Before](/media/2014/10/before.jpg?w=300)](/media/2014/10/before.jpg)

Finished product:
[![After](/media/2014/10/after.jpg?w=140)](/media/2014/10/after.jpg)

The "runway" I constructed to create a level surface:
[![Runway](/media/2014/10/runway.jpg?w=225)](/media/2014/10/runway.jpg)

Pulled out all the way, notice the cage is clear, but the equipment won't clear:
[![Out](/media/2014/10/out.jpg?w=226)](/media/2014/10/out.jpg)

To clear the equipment the castors have to be pulled over the edge:
[![Cleared](/media/2014/10/cleared.jpg?w=225)](/media/2014/10/cleared.jpg)

Rotated view:
[![Rotated](/media/2014/10/rotated.jpg?w=184)](/media/2014/10/rotated.jpg)

The rarely used KVM drawer:
[![KVM](/media/2014/10/kvm.jpg?w=226)](/media/2014/10/kvm.jpg)

Extractor fans:
[![Fans](/media/2014/10/fans.jpg?w=300)](/media/2014/10/fans.jpg)

Night mode:
[![Night](/media/2014/10/night.jpg?w=176)](/media/2014/10/night.jpg)
