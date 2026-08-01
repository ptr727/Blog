---
title: Unraid in production, a bit rough around the edges, and terrible SMB performance
date: '2019-06-11T02:51:12+00:00'
url: /2019/06/10/unraid-in-production-a-bit-rough-around-the-edges-and-terrible-smb-performance/
categories:
- performance
- problem
tags:
- smb
- unraid
- w2k19
post_id: '1859'
cover:
  alt: RW.2
  image: /media/2019/06/rw.2.png
---
In my [last](/2019/05/05/moving-from-w2k16-to-unraid/) [two](/2019/05/12/unraid-and-robocopy-problems/) posts I described how I migrated from W2K16 and hardware RAID6 to Unraid. Now that I've had two Unraid servers in production for a while, I'll describe some of the good and not so good I experienced.

Running Docker on Unraid is magnitudes easier compared to getting Docker to work on Windows. Docker allowed me to move all but one of my workloads from VM's to containers, simplifying updates, reducing the memory footprint, and improving performance.

For my IP security camera NVR software I did switch from [Milestone XProtect Express](https://www.milestonesys.com/solutions/platform/video-management-software/xprotect-express/) running on a W2K16 VM, to [DW Spectrum](https://digital-watchdog.com/productdetail/DW-Spectrum-IPVMS/) running on an Ubuntu Server VM. DW Spectrum is the US brand name for the [Nx Witness](https://www.networkoptix.com/nx-witness/) product, and the DW Spectrum branded product is sold in the US. I chose to switch to Nx Witness, no DW Spectrum, from XProtect because Nx Witness is lighter in resource consumption, easier to deploy, easier to update, has perpetual licenses, includes native remote viewing, and an official Docker release is [forthcoming](https://support.networkoptix.com/hc/en-us/community/posts/360028480674-Docker-Container).

I have been a long time user of CrashPlan, and I [switched](/2017/08/22/crashplan-throws-in-the-towel-for-home-users/) to CrashPlan Pro when they stopped offering a consumer product. I tested [CrashPlan Pro](https://hub.docker.com/r/jlesage/crashplan-pro/) and [Duplicati](https://hub.docker.com/r/linuxserver/duplicati/) containers on Unraid, with Duplicati backing up to [Backblaze B2](https://www.backblaze.com/blog/duplicati-backups-cloud-storage/). Duplicati is the clear winner, backups were very fast, and completed in about 3 days. Where after 5 days I stopped CrashPlan, when it estimated another 18 days to complete the same backup operation, and it showed the familiar out of memory error. My B2 storage cost will be a few $ higher compared to a single seat license for CrashPlan Pro, but the Duplicati plus B2 functionality and speed is superior.

![2019-06-08 (10)](/media/2019/06/2019-06-08-10.png)

When the Unraid 6.7.0 release went public, I immediately updated, but soon realized my mistake, when several plugins stopped working. It took several weeks before plugin updates were released that restored full functionality. It is worth mentioning, again, that I find it strange that Unraid without community provided plugins is really not that usable, but the functionality still remains in community provided plugins, not in Unraid. Next time I will wait a few weeks for the dust to settle in the plugin community before updating.

Storage and disk management is reasonably easy, and much more flexible compared to hardware RAID management. But adding and removing disks is still mostly a manual process, and doing it without invalidating parity is very cumbersome and time consuming. At several times I gave up on the convoluted steps required to [add](https://wiki.unraid.net/Add_One_or_More_New_Data_Drives) or [remove](https://wiki.unraid.net/Shrink_array) disks without invalidating parity, and just reconfigured the array and then rebuilt parity, hoping nothing goes wrong during the parity rebuild. This is in my opinion a serious shortcoming, maybe not in technology, but in lack of an easy to use and reliable workflow to help retain redundant protection at all times.

In order to temporarily make enough storage space in my secondary server, I removed all the SSD cache drives and replaced them with [12TB Seagate IronWolf](https://amzn.to/2Wr6WIm) drives. I did move all the data that used to be on the cache to regular storage, including the docker appdata folder. This should not be a big deal, but I immediately started getting SQLite DB corruption errors in apps like Plex, that store data in SQLite on the appdata share. After some troubleshooting I found many people [complaining](https://www.reddit.com/r/unRAID/comments/bwxcof/670_needs_attention_theres_issues_impacting_a_lot/) about this issue, that seems to have been exasperated by the recent Unraid 6.7.0 update. Apparently this is a known problem with the Fuse filesystem used by Unraid. Fuse dynamically spans shares and folders across disks, but apparently breaks file and file-region locking [required](https://www.sqlite.org/lockingv3.html) by SQLite. The recommended workaround is to put all files that require locking to work on the cache, or on a single disk, effectively bypassing Fuse. If it is Fuse that breaks file locking behavior, I find it troubling that this is not considered a critical bug.

I am quite familiar with VM snapshot management using Hyper-V and VMWare, it is a staple of VM management. In Unraid I am using a Docker based [Virt-Manager](https://hub.docker.com/r/djaydev/docker-virt-manager), which seems far less flexible, but more importantly, fails to take snapshots of UEFI based VM's. Apparently this is a [known](https://www.redhat.com/archives/virt-tools-list/2017-September/msg00008.html) shortcoming. I have not looked very hard for alternatives, but this seems to be a serious functional gap compared to Hyper-V or VMWare's snapshot capabilities.

![2019-06-05 (2)](/media/2019/06/2019-06-05-2.png)

As I started using the SMB file shares, now hosted on Unraid, in my regular day to day activities, I noticed that under some conditions the write speed becomes extremely slow, often dropping to around 2MB/s. This seems to happen when there are other file read operations in progress, and even a few KB/s of reads can drastically reduce the array SMB write performance. Interestingly the issue does not appear to affect my use of rsync between Unraid servers, but only SMB. I did find at least one other recent [report](https://forums.unraid.net/topic/80256-670-slow-smb-download-throughput/) of similar slowdowns, where only SMB is affected.

Since the problem appeared to be specific to Unraid SMB, and not general network performance, I compared the Unraid SMB performance with Windows SMB in a W2K19 VM running on the same Unraid system. By running W2K19 as a VM on the same Unraid system, the difference in performance will be mostly the SMB stack, not hardware or network.

On Unraid I created a share that is backed by the SSD cache array, that same SSD cache array holds the W2K19 VM disk image, so the storage subsystems are similar. I ran a similar test against an Unraid share backed by disk instead of cache.


{{< gallery cols="1" >}}  
{{< figure src="/media/2019/06/2019-06-08-8.png" title="2019-06-08 (8)" alt="2019-06-08 (8)" >}}

{{< figure src="/media/2019/06/2019-06-08-9.png" title="2019-06-08 (9)" alt="2019-06-08 (9)" >}}  
{{< /gallery >}}  

I found a few references ([1](https://blogs.technet.microsoft.com/josebda/2014/10/13/diskspd-powershell-and-storage-performance-measuring-iops-throughput-and-latency-for-both-local-disks-and-smb-file-shares/), [2](https://www.altaro.com/hyper-v/storage-performance-baseline-diskspd/)) to SMB benchmarking using [DiskSpd](https://github.com/microsoft/diskspd), and I used them as a basis for the test options I used. Start by creating a 64GB test file on all test shares, we reuse the file and it saves a lot of time to not recreate it every time. Note, we get a warning when creating the file on Unraid, due to [SetFileValidData()](https://docs.microsoft.com/en-us/windows/desktop/api/fileapi/nf-fileapi-setfilevaliddata) not being [supported](https://github.com/microsoft/diskspd/search?q=SetFileValidData&unscoped_q=SetFileValidData) by Unraid's SMB implementation, but that should not be an issue.

```
>diskspd.exe -c64G \\storage\testcache\testfile64g.dat
WARNING: Could not set valid file size (error code: 50); trying a slower method of filling the file (this does not affect performance, just makes the test preparation longer)

>diskspd.exe -c64G \\storage\testmnt\testfile64g.dat
WARNING: Could not set valid file size (error code: 50); trying a slower method of filling the file (this does not affect performance, just makes the test preparation longer)

>diskspd.exe -c64G \\WIN-EKJ8HU9E5QC\TestW2K19\testfile64g.dat
```

I ran several tests similar to the following commandlines:

```
>diskspd -w50 -b512K -F2 -r -o8 -W60 -d120 -Srw -Rtext \\storage\testcache\testfile64g.dat > d:\diskspd_unraid_cache.txt
>diskspd -w50 -b512K -F2 -r -o8 -W60 -d120 -Srw -Rtext \\storage\testmnt\testfile64g.dat > d:\diskspd_unraid_mnt.txt
>diskspd -w50 -b512K -F2 -r -o8 -W60 -d120 -Srw -Rtext \\WIN-EKJ8HU9E5QC\TestW2K19\testfile64g.dat > d:\diskspd_w2k19.txt
```

For a full explanation of the commandline arguments see [here](https://github.com/microsoft/diskspd/wiki/Command-line-and-parameters). The test will do 50% read and 50% write, block sizes varied from 4KB to 2048KB, 2 threads, 8 outstanding IO operations, random aligned IO, warm up for 60s, run for 120s, disable local caching for remote filesystems.

![W2K19.1](/media/2019/06/w2k19.1.png)![W2K19.3](/media/2019/06/w2k19.3.png)![Cache.1](/media/2019/06/cache.1.png)![Cache.3](/media/2019/06/cache.3.png)![Mount.1](/media/2019/06/mount.1.png)![Mount.3](/media/2019/06/mount.3.png)

From the results we can see that the Unraid SMB performance for this test is pretty poor. I redid the tests, this time doing independent read and write tests, and instead of various block sizes, I just did a 512KB block size test (I got lazy).

![RW.1](/media/2019/06/rw.1.png)![RW.2](/media/2019/06/rw.2.png)

No matter how we look at it, the Unraid SMB write performance is still really bad.

I wanted to validate the synthetic tests results with a real world test, so I collected a folder containing around 65.2GB of fairly large files, on SSD, and copied the files up and down using robocopy from my Win10 system. I chose the size of files to be about double the size of the memory on the Unraid system, such that the impact of caching can be minimized. I made sure to use a RAW VM disk to eliminate any performance impact of growing a QCOW2 image file.

```
>robocopy d:\temp\out \\storage\testmnt\in /mir /fft > d:\robo_pc_mnt.txt
>robocopy d:\temp\out \\storage\testcache\in /mir /fft > d:\robo_pc_cache.txt
>robocopy d:\temp\out \\WIN-EKJ8HU9E5QC\TestW2K19\in /mir > d:\robo_pc_w2k19.txt

>robocopy \\storage\testmnt\in d:\temp\in /mir /fft > d:\robo_mnt_pc.txt
>robocopy \\storage\testcache\in d:\temp\in /mir /fft > d:\robo_cache_pc.txt
>robocopy \\WIN-EKJ8HU9E5QC\TestW2K19\in d:\temp\in /mir > d:\robo_w2k19_pc.txt
```

During the robocopy to Unraid I notice that sporadically the Unraid web UI, and web browsing in general, becomes very slow. This never happens while copying to W2K19. I can't explain this, I see no errors reported in my Win10 client eventlog or resource monitor, I see no unusual errors on the network switches, and no errors in Unraid. I suspect whatever is impacting SMB performance is affecting network performance in general, but without data I am really just speculating.

The robocopy read results are pretty even, but again shows inferior Unraid SMB write performance. Do note that the W2K19 VM is still not as fast as my previous W2K16 RAID6 setup where I could consistently saturate the 1Gbps link for read and writes, on the same hardware and using the same disk.

![Robocopy.1.png](/media/2019/06/robocopy.1.png)![Robocopy.2](/media/2019/06/robocopy.2.png)

It is very disappointing to discover the poor SMB performance, I [reported](https://forums.unraid.net/bug-reports/stable-releases/slow-smb-performance-r566/) my findings to the Unraid support forum, and I hope they can do something to improve performance, or maybe invalidate my findings.
