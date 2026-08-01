---
title: Rotation confuses face recognition
date: '2011-12-14T00:44:00+00:00'
url: /2011/12/13/rotation-confuses-face-recognition/
categories:
- uncategorized
tags:
- facerecognition
- fastpictureviewer
- lightroom
- live
- microsoft
- windows
post_id: '122'
---
I have around fifty thousand digital photos in my library, and it has become impractical to browse through them looking for some event, or some place, or some person. So other than archiving, there really is no value in collecting photos if you can’t go back and find the ones you are looking for.

A few years ago I switched to using [Image Ingester Pro](http://imageingester.com/ii-info.php) and [Adobe Photoshop Lightroom](http://www.adobe.com/products/photoshoplightroom/) to import and catalog my photos. Now one of the first things I do after importing photos, is to add keywords describing the event, the place, and the people. But, I still have tens of thousands of photos that have no keywords, and there is no easy or automated way to add keywords to these photos. One thing that can be automated is adding people keywords to photos based on automated face recognition.

Unlike free [Windows Live Photo Gallery](http://explore.live.com/windows-live-photo-gallery), or free [Google Picasa](http://picasa.google.com/), or free [Apple iPhoto](http://www.apple.com/ilife/iphoto/), none of Adobe’s products offer face recognition, something often discussed and complained about in [Adobe forums](http://forums.adobe.com/thread/358718). Professional photographers may argue that face recognition is a gimmick, and I agree that for professional workflows it may not be required, but at less than $300, Photoshop Lightroom is an ideal tool for use by amateur and family photographers, and I think face recognition is a must have feature.

Although Lightroom does not directly offer face recognition, there are convoluted ways to add people keywords to Lightroom using Google Picasa and [Jeffrey Friedl’s Picasa Face-Recognition Import plugin](http://regex.info/blog/lightroom-goodies/picasa-face-import). The process requires you to add all your photos to Adobe Lightroom and Google Picasa, then use Picasa to detect faces, and assign them to contacts, then use Jeffrey’s import plugin to add the Picasa people as keywords to photos in Lightroom.

Picasa is not the most friendly app to work with, it may alter photo metadata without your intent, adding support for new RAW formats takes a long time, there are lots of bugs related to managing people and duplicate contacts happens all the time. The Picasa to Lightroom conversion experience is not something I am prepared to deal with on an ongoing basis, unfortunately I am also not aware of any other ways of automatically tagging people in pictures in Lightroom.

The next best thing would be to use an application that does support face recognition in addition to Lightroom, even if the two tools do not integrate or share metadata. Since I was already quite familiar with Picasa, and I have a Mac but don’t use it as a primary machine, that left me with Windows Live Photo Gallery (WLPG).

Unlike Picasa that uses its own built in image rendering technology, WLPG uses [Windows Imaging Component](http://msdn.microsoft.com/en-us/library/windows/desktop/ee719654(v=vs.85).aspx) (WIC) technology to render and interpret image metadata. The downside is that you need to install RAW image WIC codecs in order for WLPG to display RAW images, the upside is that you can install a WIC codec instead of waiting for the app to natively support the RAW format. As an example, the Panasonic DMC-LX5 was released July 2010, Picasa added support for DMC-LX5 RW2 files in Picasa 3.9, released December 2011, 17 months after the camera’s release.

WIC does have its drawbacks, some camera manufacturers do not release WIC codecs at all, and some big name manufacturers, like Canon and Nikon, are stuck in the dark ages with no x64 codec support. At this time I am aware of two alternate suppliers of RAW WIC codecs, Axel Rietschin's [FastPictureViewer Codec Pack](http://www.fastpictureviewer.com/codecs/), and [Microsoft’s Camera Codec Pack](http://www.microsoft.com/download/en/details.aspx?id=26829). Microsoft’s Camera Codec Pack is free, but offers limited camera support, and as we’ll see later, limited Explorer and WLPG integration support. FastPictureViewer Codec Pack (FPVCP) costs $14.95, is frequently updated, supports almost all camera’s and formats under the sun, integrates with Explorer and WLPG, and is what I use.

With FPVCP installed, WLPG was easy to use, the contact and names feature integrated nicely with Windows Live contacts, without any of the weirdness of the equivalent functionality I found with Picasa. Once faces were tagged, a semi automated process requiring manual verification, it was easy to find photos I was looking for, e.g. I could say show me all photos in December 2010, with me, my wife, and our daughter in the picture.

So this finally brings me to the actual problem I wanted to write about. I noticed that WLPG would get confused when tagging faces in some portrait rotated pictures. When you view the image standalone, the faces are correctly recognized, and the bounding rectangles are correctly drawn over the image. But, the thumbnails are completely wrong, taken from a different part of the image. It seems like the thumbnails are taken from the landscape coordinates view of the image, not portrait coordinates of the image.  
See the following pictures as an example, note how the thumbnails in the portrait view image are taken from the wrong part of the image:   
[![WLPG.Face.JPG.Landscape](/external/9d120ec5958fdec2.png)](/external/83b4c7e79e0e4c7f.png) [![WLPG.FPVCodecPack.Face.JPG.Portrait](/external/508ddb7412593617.png)](/external/f9b4c8dec34ab49e.png)

I reported the problem in the [WLPG support forum](http://windowslivehelp.com/thread.aspx?threadid=505fa6b0-5b41-45cf-9d7d-5613409a0604), and after some back and forth, I provided sample pictures where I could reproduce the problem, but I was told that they were unable to reproduce the problem using the same pictures. As I was not crazy, and I had seen this behavior on two different machines, I wanted to create steps to reproduce the problem.

The sample images were taken of a magazine page taped to a door, using a Canon 5D Mark II, a Panasonic DMC-LX5, a Panasonic DMC-ZS7, and an iPhone 4. I took 5 pictures with each camera in each mode; face centered, face top-left, face top-right, face bottom-left, and face bottom-right. I did this in landscape mode, portrait mode, JPG mode, and RAW mode.

I fired up a clean Windows 7 Ultimate x64 SP1 VM, installed WLPG v15.4.3538.513, and Picasa v3.9, and I dropped my collection of sample images on the machine.

As I viewed the images in Explorer, I immediately noticed a difference between my machine and the test machine, the test machine Explorer view did not display the JPG images using the correct rotation, while my machine did. This is when I remembered that I have FastPictureViewer Codec Pack installed on all my machines, and that this may have something to do with the face rotation problem.

See the following pictures of the Explorer view with and without FPVCP, note how the FPVCP version displays the CR2 thumbnails and displays the JPG files in the right rotation:   
[![Explorer.5DMk2](/external/16d26094cafef432.png)](/external/284611e4774a7efe.png) [![Explorer.5DMk2.FPVCodecPack](/external/4059baee72e45682.png)](/external/64b2b4ab7510d111.png)

Testing Windows Live Photo Gallery showed that as with Explorer, it also does not display the images using the correct rotation. This was a real big disappointment for I can’t believe that a photo application with all the bells and whistles of WLPG neglects to correctly rotate images.

See the following pictures of WLPG with and without the FPVCP, note how the FPVCP version displays the CR2 thumbnails and displays the JPG files in the right rotation:   
[![WLPG](/external/a8dc5df6bbc6af79.png)](/external/20f4ed20e3eb389b.png) [![WLPG.FPVCodecPack](/external/50111170ffcb0132.png)](/external/9a57e6acb269522d.png)

Since WLPG did not correct the rotation on portrait images, it was unable to recognize any faces in these images. So when Microsoft said they can’t reproduce the problem, they neglected to mention that the portrait images did not render correctly nor detect any pictures at all.

See the following pictures of WLPG with and without the FPVCP, note how the FPVCP version displays the JPG files in the right rotation, but WLPG uses the wrong image coordinates:   
[![WLPG.Face.JPG.Portrait](/external/ed734829a0a4d48e.png)](/external/ca64f5681f0135dc.png) [![WLPG.FPVCodecPack.Face.JPG.Portrait](/external/21627c5270b8920b.png)](/external/6174325e7acd5c27.png)

Interestingly enough, RAW images in both landscape and portrait detected the faces correctly:   
[![WLPG.FPVCodecPack.Face.RAW.Landscape](/external/b503371090baeeff.png)](/external/53add356088c81cd.png) [![WLPG.FPVCodecPack.Face.RAW.Portrait](/external/5e7e6e560c4d86b1.png)](/external/5aabdd966189e27b.png)

I repeated the tests using Microsoft’s Camera Codec Pack (MCCP).

Notice how MCCP does not correct the rotation of JPG images in Explorer, nor does it render the CR2 file thumbnails in Explorer, vs. FPVCP that does both:   
[![Explorer.5DMk2.MSFTCodecPack](/external/ad1c39cf5f553175.png)](/external/d0e1af6e53499dc2.png) [![Explorer.5DMk2.FPVCodecPack](/external/86b3a8d2c878d7a0.png)](/external/d2857c9010fba65a.png)

Notice how MCCP does not correct the rotation of JPG images in WLPG, nor does it render the CR2 file thumbnails in WLPG, vs. FPVCP that does both:   
[![WLPG.MSFTCodecPack](/external/1ac90ee8afcc02ec.png)](/external/2a0ec5be8a0c3c08.png) [![WLPG.FPVCodecPack](/external/ec5944e49c580131.png)](/external/ea9ec6398798f428.png)

I will reply to the Windows Live Photo Gallery support thread with this information, and I will also open a support ticket with FastPictureViewer, let’s see what happens.

\[Update : 28 December 2011\]  
I received an email from from [Ardfry Imaging](http://www.ardfry.com/), informing me that they were shipping a x64 DNG codec before FPV existed, and they they are still offering a variety of codecs.  


