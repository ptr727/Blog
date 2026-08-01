---
title: DELL 2408WFP loosing settings on power cycle
date: '2009-07-05T21:39:00+00:00'
url: /2009/07/05/dell-2408wfp-loosing-settings-on-power-cycle/
categories:
- problem
- solution
post_id: '91'
---
In my [last post](/2009/06/dell-2408wfp-and-spyder-3-elite.html "last post") I discussed the calibration of my DELL 2408WFP monitors.

After calibration, and changing the monitor settings, the monitors looked pretty good, but I later found that the monitor colors looked all weird again.

It turns out that the monitors reverted to their default settings, invalidating the calibration.

It seems to me that as soon as my PC goes to sleep, or the monitors go into power saving mode, or powers off, that on turning back on they revert to default settings.

I found a relatively simple solution using [EnTech mControl](http://forums.entechtaiwan.com/index.php?topic=6725.0 "EnTech mControl"), not completely automated but close.

mControl allows you to save the current monitor settings to a profile, and allows you to restore those settings.

Here are the steps:

1. Install and run mControl.
1. Set mControl to automatically load when you login. Right click on the mControl tray icon and enable auto-load. This will add an entry in the startup program group.
1. Calibrate your monitor, adjusting the monitor settings using mControl.
1. Save your monitor profile. Open a command prompt, change to the mControl directory ("C:\\Program Files (x86)\\mControl\\"), and run "mControl.exe /saveprofile Calibrate". This will save the current monitor settings to a profile called "Calibrate". You can use any profile name, I just used "Calibrate" as an example.
1. Edit the mControl startup item so that it automatically restores the monitor profile when mControl starts. Right click the mControl entry in your startup programs group, and edit the commandline to include the "/restoreprofile Calibrate" option. E.g. ""C:\\Program Files (x86)\\mControl\\mControl.exe" /restoreprofile Calibrate"

Every time you login mControl will start and restore the monitor settings.

If you change the monitor settings, simply run "mControl /saveprofile Calibrate" again to save the updated settings.

Unfortunately this only works when you login, but if the monitors power down while you are logged in, e.g. sleep, you have to manually restore the settings.

I solved this by creating a text script file called "Monitor.Restore.Profile.cmd" on my desktop, and putting the restore command in the file, ""C:\\Program Files (x86)\\mControl\\mControl.exe" /restoreprofile Calibrate".

Now whenever the monitor settings need to be fixed, I just run this script and the settings are restored.

This seems to be a problem with the DELL 2408WFP monitors, and I would like to know if this is specific my to my setup, or if this happens to other people, leave me a comment and let me know.

\[Update: 17 July 2009\]

EnTech has [enhanced mControl](http://forums.entechtaiwan.com/index.php?topic=7014.0) to support profiles right in the UI, including an "Autoexec" profile that will automatically restore the monitor settings on login and wake from sleep.

It works great.


