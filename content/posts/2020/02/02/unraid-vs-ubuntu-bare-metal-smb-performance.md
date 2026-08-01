---
title: Unraid vs. Ubuntu Bare Metal SMB Performance
date: '2020-02-03T04:14:07+00:00'
url: /2020/02/02/unraid-vs-ubuntu-bare-metal-smb-performance/
categories:
- performance
- problem
tags:
- smb
- ubuntu
- unraid
post_id: '1986'
cover:
  alt: UnraidUbuntuBareMetal
  image: /media/2020/02/unraidubuntubaremetal.png
---
In my last [test](/2020/01/18/unraid-vs-ubuntu-smb-performance/) I compared Unraid SMB performance with an Ubuntu VM running on Unraid, and Ubuntu outperformed Unraid. I was wondering if the VM disk image synthetically improved performance, maybe IO caching, so this time I tested Ubuntu on the same hardware that runs Unraid.

I configured the system to boot from either the Unraid USB stick, or an Ubuntu Server USB stick. In both cases the hardware was exactly the same, and the SMB share was on the same 4 x 1TB Samsung 860 Pro SSD BTRFS volume. I mounted the BTRS volume using the same mount options that Unraid uses. The Ubuntu Samba server used default options, the only change I made was to register the share.

```
Samba Config:
[cstshare]
comment = Samba on Ubuntu
path = /mnt/cache/CacheSpeedTest
read only = no
browsable = yes

BTRFS Mount:
mount -t btrfs -o noatime,nodiratime -U 89d1ad3a-83f3-4086-9006-5f0931370d36 /mnt/cache
```

I ran the same [tests](https://github.com/ptr727/DiskSpeedTest) as before, and the results again showed that the Unraid SMB ReadWrite and Write performance is much worse compared to Ubuntu. It was interesting to note that the Ubuntu ReadWrite performance was higher than the theoretical 1Gbps limit at 1MB and 2MB block sizes. I re-tested twice and got the same results, my assumption is that the DiskSpd options to disable local and remote caching were not effective.

{{< figure src="/media/2020/02/unraidubuntubaremetal.png?w=672" alt="" caption="" >}}

I have now tested Unraid vs. W2K19 VM, Ubuntu VM, and now Ubuntu Bare Metal, and Unraid ReadWrite and Write performance is always abysmal.

I have again [reported](https://forums.unraid.net/bug-reports/stable-releases/slow-smb-performance-r566/?tab=comments#comment-8466) my findings in the Unraid SMB performance issue thread, and we continue to wait for a fix.
