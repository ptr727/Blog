---
title: Unraid vs. Ubuntu SMB Performance
date: '2020-01-18T18:40:05+00:00'
url: /2020/01/18/unraid-vs-ubuntu-smb-performance/
categories:
- performance
- research
tags:
- smb
- unraid
post_id: '1929'
cover:
  alt: UnraidUbuntuW2K19SMB
  image: /media/2020/01/unraidubuntuw2k19smb.png
---
In my [last](/2020/01/16/unraid-smb-performance-v6-7-2-vs-v6-8-1/) round of testing I found that Unraid v6.8 SMB still underperforms compared to Windows Server 2019, but I was wondering if it is a Linux Samba problem, or an Unraid problem.

I installed an Ubuntu Server 18.04.3 LTS VM on Unraid, bridged network, 16GB RAM, 128GB raw disk located on the BTRS cache volume, consisting of 4 x Samsung Pro 860 SSD drives. This is exactly the same configuration I use for the W2K19 test VM. I [installed](https://tutorials.ubuntu.com/tutorial/install-and-configure-samba) Samba on Ubuntu using default options.

I created a SMB share that is backed by the VM disk image, and a second share that is mapped directly to an Unraid share located on the cache volume. For both shares the Ubuntu VM and Samba server will handle SMB network traffic, but one share will write to the Ubuntu EXT4 volume backed by the VM disk image, and the second will write through to the underlying Unraid BTRFS cache volume using [VirtFS](https://wiki.qemu.org/Documentation/9psetup).

I ran a series of tests using my [DiskSpeedTest](https://github.com/ptr727/DiskSpeedTest) utility, and the results are below.

{{< figure align="alignnone" width=672 src="/media/2020/01/unraidubuntuw2k19smb.png" alt="UnraidUbuntuW2K19SMB" caption="UnraidUbuntuW2K19SMB" >}}

{{< figure align="alignnone" width=673 src="/media/2020/01/unraidubuntudirectsmb.png" alt="UnraidUbuntuDirectSMB" caption="UnraidUbuntuDirectSMB" >}}

Note that the VirtFS mapped share exhibit some problems that appear to be caching related. E.g. the file iteration test would create 14000 files, but iterating the just created files would only read 3080.

My conclusion is that the Linux Samba SMB performance is on par with that of Windows Server 2019, and that the performance problems are attributed to the Unraid file write performance. The Windows test used NTFS and Ubuntu used EXT4, so it could be BTRFS and XFS related, but more likely something Unraid does. Maybe the next step could be to test a bare metal Ubuntu SMB on XFS and BTRFS.
