---
title: Delete, Are You Sure, Yes, Oh Oh
date: '2011-01-04T04:44:00+00:00'
url: /2011/01/03/delete-are-you-sure-yes-oh-oh/
categories:
- storage
post_id: '114'
---
I just had one of those moments where the blood drains from your head as you contemplate what you did.

I was in Disk Management Console, messing around with new drives I was testing, and I wanted to delete the volumes. Right Click, Delete, Are you sure, your data will be lost, and without thinking twice, I clicked yes.   
Then the blood drained from my head as I realized what I just did; instead of deleting the test volume, I just deleted my main 5TB data volume!

This is 5TB GPT partition backed by RAID5 on 4 x 2TB drives. The RAID thing makes it even worse, what is the point of RAID if I manually delete the partition and destroy the data myself?

Luck was on my side though, just yesterday I ran a backup, so I could recover most of the data, but all my VM images will be gone, they are too big to backup.

I know partition recovery is possible, I’ve done it in DOS a few times, but that was DOS and a long time ago. I also know it is possible using direct disk editing, I know an admin who had to recover a volume on a SAN he accidentally deleted, but that was done with the help of EMC support. I was looking for an easier solution.

A Google search for partition recovery software showed a variety of options, some free, some paid. I found only one product that could recover GPT partitions, [Active@ Partition Recovery](http://www.partition-recovery.com/).

I ran the trial software, and it found no drives. I found it strange that it did not UAC elevate, so I ran it again, this time as admin. It showed all my drives, I selected the drive with the missing volume, clicked quick scan, and it found a recoverable partition. Clicking on recover prompted me to enter a serial number, so I purchased a copy, entered my serial, clicked recover again, and waited. The UI reported that it saved a copy of the partition table, but it showed no progress of actually recovering the volume. I waited a bit more, opened explorer, and there was my drive back, fully recovered.

So [Active@ Partition Recovery](http://www.partition-recovery.com/) is not perfect, it needs some usability enhancements, but it works great. If you have experience with other partition recovery software supporting GPT, let me know in the comments.


