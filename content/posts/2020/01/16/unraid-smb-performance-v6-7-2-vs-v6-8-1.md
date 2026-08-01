---
title: 'Unraid SMB Performance: v6.7.2 vs. v6.8.1'
date: '2020-01-16T19:07:49+00:00'
url: /2020/01/16/unraid-smb-performance-v6-7-2-vs-v6-8-1/
categories:
- performance
- storage
tags:
- smb
- unraid
post_id: '1909'
cover:
  alt: Sum_Of_MBPS_and_BlockSize
  image: /media/2020/01/sum_of_mbps_and_blocksize.png
---
I previously [wrote](/2019/06/10/unraid-in-production-a-bit-rough-around-the-edges-and-terrible-smb-performance/) about the poor SMB performance I experienced in Unraid v6.7.2. Unraid v6.8 supposedly addressed SMB performance issues for concurrent read and write operations, and after waiting for the first bugfix release of v6.8, I re-tested using v6.8.1.

In my last test I used a combination of batch files and copy and paste, this time I wrote a [tool](https://github.com/ptr727/DiskSpeedTest) to make repeat testing easy. I am not going to describe the usage here, see the instructions at the [GitHub](https://github.com/ptr727/DiskSpeedTest) repository. There are new [reports](https://forums.unraid.net/bug-reports/stable-releases/680-smb-ver-4113-significant-performance-decrease-when-opening-files-in-folders-with-1000-files-in-them-r789/) in v6.8 of poor SMB performance when a folders contains large numbers of files, so I added a test to try and simulate that behavior, by creating a large number of files, then reading each file, then deleting each file.

I configured my Unraid server with two test SMB shares, one pointing to the cache, and one pointing to a single spinning disk. The cache consists of 4 x 1TB Samsung Pro 860 drives in a BTRFS volume, and the spinning disk is a Seagate IronWolf 12TB disk formatted XFS protected by a single similar model parity disk. The third share is backed by a Windows Server 2019 VM running on the cache disk.

I upgraded the server from v6.7.2 to v6.8.1, verified operation, and then restored it back to v6.7.2. I ran the first set of tests with v6.7.2, upgraded to v6.8.1, and re-ran the same set of tests. Both tests used exactly the same hardware configuration and environment, and were run back to back.

Here are results in graph form:

{{< figure align="alignnone" width=480 src="/media/2020/01/sum%5Fof%5Fmbps.png" alt="Sum\_Of\_MBPS" caption="Sum\_Of\_MBPS" >}}

{{< figure align="alignnone" width=480 src="/media/2020/01/sum%5Fof%5Fmbps%5Fand%5Fblocksize.png" alt="Sum\_Of\_MBPS\_and\_BlockSize" caption="Sum\_Of\_MBPS\_and\_BlockSize" >}}

{{< figure align="alignnone" width=480 src="/media/2020/01/mbps%5F1mb.png" alt="MBPS\_1MB" caption="MBPS\_1MB" >}}

{{< figure align="alignnone" width=473 src="/media/2020/01/mbps%5F1mb%5Fnow2k19.png" alt="MBPS\_1MB\_NoW2K19" caption="MBPS\_1MB\_NoW2K19" >}}

{{< figure align="alignnone" width=480 src="/media/2020/01/iterationtime.png" alt="IterationTime" caption="IterationTime" >}}

What did we learn?

- Windows Server 2019 SMB performance is still far superior compared to Unraid.
  - I don't know if the Linux SMB implementation is just that much slower compared to Windows, or if the performance degradation is attributed to Unraid.
  - TODO: Test SMB performance between a Linux VM and Windows VM.
- The cache performance in v6.8.1 is worse compared to v6.7.2.
- No noticeable SMB performance improvement in v6.8.1.
