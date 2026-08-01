---
title: Unraid repeat parity errors on reboot
date: '2020-01-11T01:52:30+00:00'
url: /2020/01/10/unraid-repeat-parity-errors-on-reboot/
categories:
- problem
- storage
tags:
- adaptec
- lsi
- unraid
post_id: '1882'
cover:
  alt: IMG_5864
  image: /media/2020/01/img_5864.jpg
---
This post started with a quick experiment, but after hardware incompatibilities forced me to swap SSD drives, and subsequently losing a data volume, it turned into a much bigger effort.

My two Unraid servers have been running nonstop without any issues for many months, last I looked the uptime on v6.7.2 was around 240 days. We recently experienced an extended power failure, and I noticed 5 parity errors, on both servers, after the servers were restarted.

```
Jan 1 06:09:23 Server-1 kernel: md: recovery thread: PQ corrected, sector=1962934168
Jan 1 06:09:23 Server-1 kernel: md: recovery thread: PQ corrected, sector=1962934176
Jan 1 06:09:23 Server-1 kernel: md: recovery thread: PQ corrected, sector=1962934184
Jan 1 06:09:23 Server-1 kernel: md: recovery thread: PQ corrected, sector=1962934192
Jan 1 06:09:23 Server-1 kernel: md: recovery thread: PQ corrected, sector=1962934200

Jan 1 04:42:39 Server-2 kernel: md: recovery thread: P corrected, sector=1962934168
Jan 1 04:42:39 Server-2 kernel: md: recovery thread: P corrected, sector=1962934176
Jan 1 04:42:39 Server-2 kernel: md: recovery thread: P corrected, sector=1962934184
Jan 1 04:42:39 Server-2 kernel: md: recovery thread: P corrected, sector=1962934192
Jan 1 04:42:39 Server-2 kernel: md: recovery thread: P corrected, sector=1962934200
```

I initially suspected that a dirty shutdown caused the corruption, but my entire rack is on a large UPS, and the servers are configured, and tested, to cleanly shutdown in case of a low battery condition. Unfortunately Unraid does not persist logs across reboots, so it was impossible to verify the shutdown behavior via logs. Unraid logs to memory and not to the USB flash drive to prevent flash wear, but I think this needs to be at least configurable, as no logs means troubleshooting after an unexpected reboot is near impossible. Yes, I know I can enable the Unraid syslog server, and I can redirect syslog to write to the flash drive, but syslog is not as reliable or complete as native logging, especially during a shutdown scenario, but more importantly, syslog was not enabled, so no shutdown logs.

I could not entirely rule out a dirty shutdown, but I could test a clean reboot scenario. I restarted from within Unraid, ran a parity check, same exact 5 parity errors were back, ran a parity check again, and clean. It takes more than a day to run a single parity check, so this is a cumbersome and time consuming exercise. It is  very suspicious that it is exactly the same 5 sectors, every time.

```
Jan  3 10:03:07 Server-2 kernel: md: recovery thread: P corrected, sector=1962934168
Jan  3 10:03:07 Server-2 kernel: md: recovery thread: P corrected, sector=1962934176
Jan  3 10:03:07 Server-2 kernel: md: recovery thread: P corrected, sector=1962934184
Jan  3 10:03:07 Server-2 kernel: md: recovery thread: P corrected, sector=1962934192
Jan  3 10:03:07 Server-2 kernel: md: recovery thread: P corrected, sector=1962934200
```

I searched the Unraid forums, and I found that there are other reports of similar repeat parity errors. In [some](https://forums.unraid.net/topic/56262-resolved-5-errors-after-every-parity-check/) instances attributed to a Marvel chipset, or a Supermicro AOC-SASLP-MV8 controller, or the SASLP2 driver. My systems use Adaptec RAID cards, [7805Q](https://amzn.to/37ypFai) SAS2 and [81605ZQ](https://amzn.to/2FosaQe) SAS3, in HBA mode, so no Marvel chipset and no SASLP2 driver, but the same symptoms.

An all too common forum reply to storage problems is to switch to a LSI HBA, and I got the same reply when I [reported](https://forums.unraid.net/topic/86793-errors-during-parity-check-after-clean-restart) the parity problem with my Adaptec hardware.

I was sceptical, causation vs. correlation. As example, take the SQLite corruption bug introduced in v6.7 and for the longest time it was blamed on hardware or 3rd party apps, but it eventually turns out to be an Unraid [bug](https://forums.unraid.net/bug-reports/prereleases/sqlite-data-corruption-testing-r664/).

Arguing my case on a community support forum is not productive, and I just want the parity problem resolved, so I decided to switch to LSI HBA cards. I really do have a love hate relationship with community support, especially when I pay for a product, like Unraid or Plex Pass, but have no avenue to dedicated support.

I am no stranger to LSI cards, and the problems flashing from IR to IT mode firmware, so I got my LSI cards preflashed with the latest IT mode firmware at the [Art of Server](https://www.artofserver.com/) eBay [store](https://www.ebay.com/str/theartofserver). My systems are wired with miniSAS HD SFF-8643 cables, and the only cards offered with miniSAS HD ports were [LSI SAS9340-8i ServeRAID M1215](https://www.ebay.com/itm/LSI-SAS9340-8i-ServeRAID-M1215-12Gbps-SAS-HBA-P16-IT-mode-for-ZFS-FreeNAS-unRAID/163040642059) cards. I know the RAID hardware is overkill when using IT mode, and maybe I should have gone for vanilla [LSI SAS 9300-8i](https://amzn.to/36u0aXF) cards, especially when the the Unraid community was quick to [comment](https://forums.unraid.net/topic/86793-errors-during-parity-check-after-clean-restart/?tab=comments#comment-806878) that a 9340 is not a "true" HBA.

I replaced the 7805Q with the SAS9340 in Server-2, and noticed that none of my SSD drives showed up in the LSI BIOS utility, only the spinning disks showed up. I put the 7805Q card back, and all the drives, including the SSD drives, showed up in the Adaptec BIOS utility. I replaced the 81605ZQ with the SAS9340 in Server-1, and this time some of the SSD's showed up. None of my Samsung EVO 840 SSD's showed up, but the Samsung Pro 850 and Pro 860 SSD's did show up. I again replaced the 7805Q in Server-2 with the SAS9340, but this time I added a Samsung Pro 850, and it did show up.


{{< gallery cols="1" >}}  
{{< figure src="/media/2020/01/img%5F5864.jpg" title="IMG\_5864" alt="IMG\_5864" >}}

{{< figure src="/media/2020/01/img%5F5865.jpg" title="IMG\_5865" alt="IMG\_5865" >}}

{{< figure src="/media/2020/01/img%5F5866.jpg" title="IMG\_5866" alt="IMG\_5866" >}}

{{< figure src="/media/2020/01/img%5F5873.jpg" title="IMG\_5873" alt="IMG\_5873" >}}  
{{< /gallery >}}  

The problem seemed to be limited to my Samsung EVO drives. I reached out to Art of Server for help, and although he was very responsive, he had not seen or heard of this problem. I looked at the LSI hardware [compatibility](https://techdocs.broadcom.com/content/broadcom/techdocs/us/en/ca-enterprise-software/other/HBA_93xx_12Gb_s_SAS_Storage_Adapter_Drive_Compatibility_Report_Selection_Guide/v23688813/v26850575.html#v26850575) list, and the EVO drives were listed. Some more searching, and I found a LSI KB [article](https://www.broadcom.com/support/knowledgebase/1211161496937/trim-and-sgunmap-support-for-lsi-hbas-and-raid-controllers) mentioning TRIM support not being supported on Samsung Pro 850 drives. It seems that the LSI HBA's need TRIM to support DRAT (Deterministic Read After TRIM) / (Data Set Management TRIM supported (limit 8 blocks)), and RZAT (Deterministic read ZEROs after TRIM). The [Wikipedia](https://en.wikipedia.org/wiki/Trim_(computing)) article on TRIM mentions specific drives for faulty TRIM implementations, including the Samsung 840 and 850 (without specifying Pro or EVO), and the Linux [kernel](https://github.com/torvalds/linux/blob/master/drivers/ata/libata-core.c) has special handling for Samsung 840 and 850 drives.

```
	/* devices that don't properly handle queued TRIM commands */
	{ "Micron_M500IT_*",		"MU01",	ATA_HORKAGE_NO_NCQ_TRIM |
						ATA_HORKAGE_ZERO_AFTER_TRIM, },
	{ "Micron_M500_*",		NULL,	ATA_HORKAGE_NO_NCQ_TRIM |
						ATA_HORKAGE_ZERO_AFTER_TRIM, },
	{ "Crucial_CT*M500*",		NULL,	ATA_HORKAGE_NO_NCQ_TRIM |
						ATA_HORKAGE_ZERO_AFTER_TRIM, },
	{ "Micron_M5[15]0_*",		"MU01",	ATA_HORKAGE_NO_NCQ_TRIM |
						ATA_HORKAGE_ZERO_AFTER_TRIM, },
	{ "Crucial_CT*M550*",		"MU01",	ATA_HORKAGE_NO_NCQ_TRIM |
						ATA_HORKAGE_ZERO_AFTER_TRIM, },
	{ "Crucial_CT*MX100*",		"MU01",	ATA_HORKAGE_NO_NCQ_TRIM |
						ATA_HORKAGE_ZERO_AFTER_TRIM, },
	{ "Samsung SSD 840*",		NULL,	ATA_HORKAGE_NO_NCQ_TRIM |
						ATA_HORKAGE_ZERO_AFTER_TRIM, },
	{ "Samsung SSD 850*",		NULL,	ATA_HORKAGE_NO_NCQ_TRIM |
						ATA_HORKAGE_ZERO_AFTER_TRIM, },
	{ "FCCT*M500*",			NULL,	ATA_HORKAGE_NO_NCQ_TRIM |
						ATA_HORKAGE_ZERO_AFTER_TRIM, },
```

This is all still circumstantial, as it does not explain why the LSI controller would not mount the 840 EVO drives, but will mount the 850 Pro drive, when both are listed as problematic, and both are included on the LSI hardware compatibility list. I do not have EVO 850's to test with, so I can not confirm if the problem is limited to EVO 840's.

I still had the original parity problem to deal with, and to verify that a LSI HBA will resolve the problem, so I needed a working Unraid with LSI HBA system. Server-1 had two EVO 840's, a 850 Pro, and a 860 Pro for the BTRFS cache volume. I pulled a Pro 850 and a Pro 860 drive from another system, and proceeded to replace the two EVO 840's. Per the Unraid [FAQ](https://forums.unraid.net/topic/46802-faq-for-unraid-v6/?tab=comments#comment-480419), I should be able to replace the drives one at a time, waiting for the BTRFS volume to rebuild. I replaced the first disk, it took about a day to rebuild, I replaced the second disk using the same procedure, but something went wrong, and my cache volume would not mount, and reported being corrupt.

```
Jan  6 07:25:41 Server-1 kernel: BTRFS info (device sdf1): allowing degraded mounts
Jan  6 07:25:41 Server-1 kernel: BTRFS info (device sdf1): disk space caching is enabled
Jan  6 07:25:41 Server-1 kernel: BTRFS info (device sdf1): has skinny extents
Jan  6 07:25:41 Server-1 kernel: BTRFS warning (device sdf1): devid 4 uuid 94867179-94ed-4580-ace4-f026694623f6 is missing
Jan  6 07:25:41 Server-1 kernel: BTRFS error (device sdf1): failed to verify dev extents against chunks: -5
Jan  6 07:25:41 Server-1 root: mount: /mnt/cache: wrong fs type, bad option, bad superblock on /dev/sdr1, missing codepage or helper program, or other error.
Jan  6 07:25:41 Server-1 emhttpd: shcmd (7033): exit status: 32
Jan  6 07:25:41 Server-1 emhttpd: /mnt/cache mount error: No file system
Jan  6 07:25:41 Server-1 emhttpd: shcmd (7034): umount /mnt/cache
Jan  6 07:25:41 Server-1 kernel: BTRFS error (device sdf1): open_ctree failed
Jan  6 07:25:41 Server-1 root: umount: /mnt/cache: not mounted.
Jan  6 07:25:41 Server-1 emhttpd: shcmd (7034): exit status: 32
Jan  6 07:25:41 Server-1 emhttpd: shcmd (7035): rmdir /mnt/cache
```

In retrospect I should have known something was wrong when Unraid reported the array being stopped, but I still saw lots of disk activity on the SSD drive bay lights. I suspect the BTRFS rebuild was still ongoing, or mounted, even if Unraid reported the array being stopped. No problem, I thought, I make daily data backups to [Backblaze](https://www.backblaze.com/b2/cloud-storage.html) B2 using [Duplicacy](https://duplicacy.com/), and weekly Unraid (appdata and docker) backups, that are then backed up to B2. I recreated the cache volume, and got the server started again, but my Unraid data backups were missing.

It was an oversight and configuration mistake: I configured my backup share to be cached, I ran daily backups of the backup share to B2 at 2am, and weekly Unraid backups to the backup share on Mondays at 3am. The last B2 backup was Monday morning at 2am, the last Unraid backup was Monday morning at 3am. When the cache died all data on the cache was lost, including the last Unraid backup, that never made it to B2. My last recoverable Unraid backup on B2 was a week old.

So a few key learnings: do not use the cache for backup storage, schedule offsite backups to run after onsite backups, and if the lights are still blinking don't pull the disk.

Once I had all the drives installed, I tested for TRIM support.

Samsung Pro 860, supports DRAT and RZAT:

```
root@Server-1:/mnt# hdparm -I /dev/sdf | grep TRIM
* Data Set Management TRIM supported (limit 8 blocks)
* Deterministic read ZEROs after TRIM
```

Samsung Pro 850, supports DRAT:

```
root@Server-2:~# hdparm -I /dev/sdf | grep TRIM
* Data Set Management TRIM supported (limit 8 blocks)
```

Samsung EVO 840, supports DRAT, but does not work with the LSI HBA:

```
root@Server-2:~# hdparm -I /dev/sdc | grep TRIM
* Data Set Management TRIM supported (limit 8 blocks)
```

The BTRFS volume consisting 4 x Pro 860 drives reported trimming what looks like all disks, 3.2 TiB:

```
root@Server-1:~# fstrim -v /mnt/cache
/mnt/cache: 3.2 TiB (3489240088576 bytes) trimmed
```

The BTRFS volume consisting of 2 x Pro 860 + 2 x Pro 850 drives reported trimming what looks like only 2 disks, 1.8 TiB:

```
root@Server-2:~# fstrim -v /mnt/cache
/mnt/cache: 1.8 TiB (1946586398720 bytes) trimmed
```

In summary, Samsung EVO 840 no good, Samsung Pro 850 avoid, [Samsung Pro 860](https://amzn.to/36FJUTs) is ok.

Server-2 uses SFF-8643 to SATA breakout cables with sideband [SGPIO](https://en.wikipedia.org/wiki/SGPIO) connectors, controlling the drive bay lights. With the Adaptec controller the drive bay lights worked fine, but with the LSI the lights do not appear to work. I am really tempted to replace the chassis with a SAS expander, alleviating the need for the breakout cables, but that is a project for another day.

After I recreated the cache volume, reinstalled the Duplicacy web container and tried to restore my now week old backup file. I could not get the web UI to restore the 240GB backup file, either the session timed out or the network connection was dropped. I reverted to using the CLI, and with a few retries, eventually restored the file. It was [disappointing](https://forum.duplicacy.com/t/how-to-view-restore-progress-in-web-ui/3025/5) to learn that the web UI must remain open during the restore, and that the CLI does not automatically retry on network failures. Fortunately Duplicacy will do block-based restores and can resume restoring large files.

```
2020/01/06 07:59:01 Created restore session 1o8nqw
2020/01/06 07:59:01 Running /home/duplicacy/.duplicacy-web/bin/duplicacy_linux_x64_2.3.0 [-log restore -r 101 -storage B2-Backup -overwrite -stats --]
2020/01/06 07:59:01 Set current working directory to /cache/localhost/restore
2020/01/06 09:37:35 Deleted listing session jnji7l
2020/01/06 09:37:41 Invalid session
2020/01/06 12:07:57 Stopping the restore operation in session 1o8nqw
2020/01/06 12:07:57 Failed to restore files for backup B2-Backup-Backup revision 101 in the storage B2-Backup: Duplicacy was aborted
2020/01/06 12:07:57 closing log file restore-20200106-075901.log
2020/01/06 12:08:17 Deleted restore session 1o8nqw
```

```
Downloaded chunk 34683 size 13140565, 15.05MB/s 01:20:44 70.1%
Failed to download the chunk
1ff9d2c082d06226b0d81019338d048bf5a4428827a3fc0d3f6f337d66fd7fa9: read tcp 192.168.1.113:49858->206.190.215.16:443: wsarecv: An existing connection was forcibly closed by the remote host.
...
Downloaded chunk 49473 size 2706939, 13.52MB/s 00:00:01 100.0%
Downloaded Unraid/2019-12-30@03.00/CA_backup.tar.gz (255834283004)
Restored C:\Users\piete\Downloads\Duplicacy to revision 101
Files: 1 total, 243982.58M bytes
Downloaded 1 file, 243982.58M bytes, 14795 chunks
Total running time: 01:30:23
```

I did lose my [DW-Spectrum](https://digital-watchdog.com/productdetail/DW-Spectrum-IPVMS/) IPVMS running on an Ubuntu Server VM. I've known that I don't have a VM backup solution, but the video footage is on the storage server not in the VM, video backups go to B2, and it is reasonably easy to recreate the VM. I am still [working](https://hub.docker.com/r/ptr727/dwspectrum-lsio) on a DW-Spectrum docker solution for Unraid, but as of today the VMS does [not](https://support.networkoptix.com/hc/en-us/requests/19037) recognize Unraid mapped storage volumes.

After all this trouble, I could finally test a parity check after reboot with the LSI HBA.  With the system up I ran a parity check, all clear, rebooted, ran the parity check again, and ... no errors. I performed this operation on both servers, no problems.

I was really sceptical that the LSI would work where the Adaptec failed, and this does not rule out Unraid as the cause, but it does show that Unraid with the LSI HBA does not have the dirty parity on reboot problem.
