---
title: Unraid User-Share vs. Disk-Share SMB Performance
date: '2020-04-25T16:44:42+00:00'
url: /2020/04/25/unraid-user-share-vs-disk-share-smb-performance/
categories:
- performance
tags:
- smb
- unraid
post_id: '1993'
cover:
  alt: UnraidDiskShare
  image: /media/2020/04/unraiddiskshare.png
---
This [is](/2020/02/02/unraid-vs-ubuntu-bare-metal-smb-performance/) [yet](/2020/01/18/unraid-vs-ubuntu-smb-performance/) [another](/2020/01/16/unraid-smb-performance-v6-7-2-vs-v6-8-1/) post on Unraid's poor SMB performance, but I think I narrowed down the cause of the problem to the Unraid FUSE filesystem. I discovered this about 2 months ago, but with COVID-19 and no kids weekend sporting event duties, I have some time to post.

In this round of testing I compared the performance of "User" shares vs. "Disk" shares. An Unraid "User" share is a volume backed by Unraid's [FUSE](https://en.wikipedia.org/wiki/Filesystem_in_Userspace) filesystem, while a "Disk" share is a volume directly backed by the disk's native filesystem.

Per suggestions from Unraid I also tested enabling DirectIO and disabling SMB case sensitivity.

As before, I used my [DiskSpeedTest](https://github.com/ptr727/DiskSpeedTest) utility to automate the testing.

{{< figure src="/media/2020/04/unraiddiskshare.png" alt="" caption="" >}}

The case insensitive SMB and DirectIO options made no discernable difference.

But we can see that the performance of disk shares are near the same performance we get from Ubuntu. This means the performance problem is caused by the Unraid FUSE code affecting all user shares.

One may expect some performance degradation due to the FUSE code needing to perform disk parity operations, but this level of impact is unacceptable compared to other software based RAID systems, and worse is that the test was performed on the SSD cache volume where no parity computation is required.

The Unraid FUSE code is proprietary, so code inspection is not possible, but I suspect the code path is less than optimized. In my experience the performance and quality demands of filesystem code requires extremely competent and diligent developers. Other than the obvious performance degradation, I'll offer two other examples of questionable code behavior: 1) All IO is halted while [waiting](https://forums.unraid.net/bug-reports/stable-releases/smb-disk-io-halts-while-other-disks-spin-up-r918/) for a disk to spin up, even if the disk being spun up has nothing to do with servicing the IO backed by another disk. This could be an overly simplified locking or synchronization model, instead of an IO path based locking model. 2) The cache volume is not backed by parity, but IO performance is still severely degraded. This directly shows the performance degradation caused by code not IO, and could be avoided by direct IO passthrough, or file handle remapping as done in [overlay](https://en.wikipedia.org/wiki/UnionFS) filesystems. But, I'm really just speculating, other than observation I have no substantiation.

I really do like the flexibility of Unraid as an all-in-one storage plus docker plus virtualization host. But the "proprietary" Unraid RAID implementation is showing to be the weakest link, not just in performance but also being [limited](https://www.reddit.com/r/unRAID/comments/5hejks/maximum_drives/) to 28 data + 2 parity drives. I am leaning towards adding my support to the growing number of users that would like to see native [ZFS](https://en.wikipedia.org/wiki/ZFS) [support](https://forums.unraid.net/topic/42429-zfs-filesystem-support/) [in](https://forum.level1techs.com/t/zfs-on-unraid-lets-do-it-bonus-shadowcopy-setup-guide-project/148764) Unraid.

Unfortunately still [no word](https://forums.unraid.net/bug-reports/stable-releases/slow-smb-performance-r566/) from Unraid as to a performance fix.
