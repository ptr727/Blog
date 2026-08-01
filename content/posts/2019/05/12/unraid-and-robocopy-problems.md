---
title: Unraid and Robocopy Problems
date: '2019-05-13T03:12:41+00:00'
url: /2019/05/12/unraid-and-robocopy-problems/
categories:
- problem
- solution
- storage
tags:
- robocopy
- unraid
post_id: '1844'
---
In my [last post](/2019/05/05/moving-from-w2k16-to-unraid/) I described how I converted one of my W2K16 servers to Unraid, and how I am preparing for conversion of the second server.

As I've been copying all my data from W2K16 to Unraid, I discovered some interesting discrepancies between W2K16 SMB and Unraid SMB. I use robocopy to mirror files from one server to the other, and once the first run completes, any subsequent runs should complete without needing to copy any files again (unless they were modified).

First, you have to use the "robocopy.exe /mir \[source\] \[dest\] /mir [/fft](https://docs.microsoft.com/en-us/windows-server/administration/windows-commands/robocopy)" option, for Fat File Times, allowing for 2 seconds of drift in file timestamps.

I found a large number of files that would copy over and over with no changes to the source files. I also found a particular folder that would "magically" show up on Unraid, and cannot be deleted from the Unraid share by robocopy.

After some troubleshooting, I discovered that files with old timestamps, and folder names that end in a dot, do not copy correctly to Unraid.

I looked at the files that would not copy, and I discovered that the file modified timestamps were all set to "1 Jan 1970 00:00". I experimented by changing the modified timestamp to today's date, and the files copied correctly. It seems that if the modified timestamp on the source file is older than 1 Jan 1980, the modified timestamp on Unraid for the same newly created file will always be set as 1 Jan 1980. When then running robocopy again, the source files will always be reported as older, and the file copied again.

Below is an example of a folder of test files with a created date of 1 Jan 1970 UTC, I copy the files using robocopy, and copy them again. The second run of robocopy again copies all the files, instead of reporting them as similar. One can see that the destination timestamp is set to 1 Jan 1980, not 1 Jan 1970 as expected.


{{< gallery cols="2" >}}  
{{< figure src="/media/2019/05/2019-05-12-1.png" title="2019-05-12 (1)" alt="2019-05-12 (1)" >}}

{{< figure src="/media/2019/05/2019-05-12.png" title="2019-05-12" alt="2019-05-12" >}}

{{< figure src="/media/2019/05/2019-05-12-2.png" title="2019-05-12 (2)" alt="2019-05-12 (2)" >}}

{{< figure src="/media/2019/05/2019-05-12-3.png" title="2019-05-12 (3)" alt="2019-05-12 (3)" >}}  
{{< /gallery >}}  

The second set of problem files occur in folder names ending in a dot. Unraid ignores the dots on the end of the folder names, and when another folder exists without dots, the copy operation uses the wrong folder.

Below is an example of a folder that contains two directories, one named "LocalState", and one named "LocalState..". I robocopy the folder contents, and when running robocopy again, it reports an extra folder. That extra folder gets "magically" created in the destination directory, but the "LocalState.." folder is missing.


{{< gallery cols="2" >}}  
{{< figure src="/media/2019/05/2019-05-12-9.png" title="2019-05-12 (9)" alt="2019-05-12 (9)" >}}

{{< figure src="/media/2019/05/2019-05-12-8.png" title="2019-05-12 (8)" alt="2019-05-12 (8)" >}}

{{< figure src="/media/2019/05/2019-05-12-7.png" title="2019-05-12 (7)" alt="2019-05-12 (7)" >}}

{{< figure src="/media/2019/05/2019-05-12-6.png" title="2019-05-12 (6)" alt="2019-05-12 (6)" >}}

{{< figure src="/media/2019/05/2019-05-12-5.png" title="2019-05-12 (5)" alt="2019-05-12 (5)" >}}

{{< figure src="/media/2019/05/2019-05-12-4.png" title="2019-05-12 (4)" alt="2019-05-12 (4)" >}}  
{{< /gallery >}}  

The same robocopy operations to the W2K16 server over SMB works as expected.

From what I researched, the timestamp ranges for [NTFS](https://devblogs.microsoft.com/oldnewthing/20090306-00/?p=18913) is 1 January 1601 to 14 September 30828, [FAT](https://en.wikipedia.org/wiki/File_Allocation_Table) is 1 January 1980 to 31 December 2107, and [EXT4](https://en.wikipedia.org/wiki/Ext4) is 1 January 1970 to 19 January 2106 (2038 + 408). I could not create files with a date earlier than 1 Jan 1980, but I could set file modified timestamps to dates greater than 2106, so I do not know what the Unraid timestamp range is.

Creating and accessing directories with trailing dots requires special care on Windows using the [NT style notation](https://docs.microsoft.com/en-us/windows/desktop/FileIO/naming-a-file), e.g. "[CreateDirectoryW](https://docs.microsoft.com/en-us/windows/desktop/api/fileapi/nf-fileapi-createdirectorya)(L"\\\\\\?\\\C:\\\Users\\\piete\\\Unraid.Badfiles\\\TestDot..", NULL), but robocopy does handle that correctly on W2K16 SMB.

I don't know if the observed behavior is specific to Unraid SMB, or if it would apply to [Samba](https://www.samba.org/) on Linux in general. But, it posed a problem as I wanted to make sure I do indeed have all files correctly backed up.

I decided to write a quick little app to find problem files and folders. The app iterates through all files and folders, it will fix timestamps that are out of range, and report on finding files or folders that end in a dot. I ran it through my files, it fixed the timestamps for me, and I deleted the folders ending in dot by hand. Multiple robocopy runs now complete as expected.
