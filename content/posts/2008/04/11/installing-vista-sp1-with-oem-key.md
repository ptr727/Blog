---
title: Installing Vista SP1 with an OEM key
date: '2008-04-12T01:45:00+00:00'
url: /2008/04/11/installing-vista-sp1-with-oem-key/
categories:
- uncategorized
tags:
- microsoft
- windows
post_id: '78'
---
I received my new Lenovo ThinkPad T61 notebook, pre-installed with Vista Ultimate, but also with 3rd party software I did not care for.

I wanted a clean Vista install, and that is exactly why I made sure to order the recovery media with the notebook, thinking that this will include an OS install DVD. It turns out that the recovery media is six CDs, I don’t know why not a DVD, regardless, the recovery media does not include a Vista install DVD.

I called Lenovo support asking how to obtain a Vista DVD that will accept the OEM key, and was told that Vista install DVDs are not available, and that I should use the recovery CDs or the recovery partition.

I decided to give the recovery partition a try; boot, press F11, select restore, do a custom restore, unselect all the 3rd party software, start the install process.

The machine rebooted several times, eventually returning to the same state as when I first booted. There was no 3rd party software on the system, only the Lenovo ThinkPad software was installed.

This was much better than the out of the box version, but still not as clean as I’d like it to be.

I did some research and found several [articles](http://forum.notebookreview.com/showthread.php?t=144783) explaining elaborate procedures on how to install Vista using a normal Vista DVD and an OEM key.

Since I had read that Vista SP1 had made some licensing changes, I decided to experiment using a Vista x86 with instegrated SP1 DVD I downloaded from MSDN.

I was not sure if I would need the actual key used on my system, as explained by the [article](http://forum.notebookreview.com/showthread.php?t=144783), which is different to the key on the OEM sticker, so to be safe I used [Magical Jelly Bean Keyfinder](http://www.magicaljellybean.com/keyfinder/) to make a note of my current key. This key was indeed different than the key on the OEM sticker.

I booted from the Vista with integrated SP1 DVD, formatted the partition, it was interesting that the 6GB recovery partition does not show up in Vista, I did not enter a key, and started the installation.

After the installation completed I changed the product key using the key I had previously retrieved from the system. After a few seconds Windows reported that there was a problem with the key.

This is when I noticed something interesting, the activation window appearance changed, and the temporary key that was displayed changed to indicate xxx-OEM-xxx. It seems that Windows automatically switched to OEM mode.

Next I tried the key on the sticker, and after a few seconds Windows was activated.

I was intrigued by the automatic mode change, but I did not want to repeat the whole procedure just to find out if I could have used the OEM key in the first place.

If you try this procedure using Vista with integrated SP1, be sure to first try the key on the OEM sticker, you may not need the initial key retrieval step at all.


