---
title: Microsoft Expression Media / iView Media Pro to Adobe Photoshop Lightroom converter
date: '2008-04-02T04:08:00+00:00'
url: /2008/04/01/microsoft-expression-media-iview-media-pro-to-adobe-photoshop-lightroom-converter/
categories:
- solution
tags:
- expressionmedia
- iview
- lightroom
- microsoft
post_id: '76'
---
This article was originally posted [here](http://www.insanegenius.com/expressionmedia/).

### Introduction:


Because of severe performance problems I experienced with both iView Media Pro and Microsoft Expression Media, I decided to switch to Adobe Lightroom.

Unfortunately Lightroom does not understand catalog sets nor does it understand people tags, so the transition is not that simple.

After I could not find a simple, or even complicated solution, I decided to write my own conversion application.

This application will convert hierarchical catalog sets into keywords, and will add people tags to keywords.

I considered directly converting to Lightroom's native SQLite database format, but the reverse engineering effort did not seem justified.

### Disclaimer:


I am providing this utility and the source code as is, no warranties are provided, use at your own risk.

Backup all your data, validate the conversion results, do not discard your backups.

### Source:


I wrote the utility in C++ using Visual Studio 2005 SP1.

I tested on Vista Ultimate x86.

I tested with Microsoft Expression Media 1.0.8104.0, and iView Media Pro 3.1.3.42E6.

The code utilizes the COM API's exposed by Expression Media and Media Pro.

Unfortunately neither application's COM API's work reliably, I can only hope that the quality of future versions will improve.

See the source code comments for problems I encountered.

### Usage:




1. Download the archive and extract the contents to your folder of choice.

The archive contains the source, and two binaries, one for Expression Media  
and one for Media Pro.

The binaries are compiled to use either the Expression Media or the Media Pro COM type libraries.

1. Run Expression Media or Media Pro, and open the catalog you want to convert.

Make sure that only one catalog is open.

Make sure you have a backup of your catalog and of all your media files.

1. Open a command prompt and change the directory to where you extracted the files.

Run: ExpressionMediaExport.exe \[Full path to the catalog file you opened in  
Expression Media or Media Pro enclosed in double quotes\]

E.g. \[ExpressionMediaExport.exe "c:\\media\\catalog.ivc"\]

The utility will convert catalog sets to keywords, and will convert people to  
keywords.

You can close the command prompt.

1. The catalog sets will be converted so that each catalog node is a keyword and  
the keywords are assigned to all items in that catalog.

E.g. if you have "Travel" and "Travel\\Someplace", the keywords will be  
"{Root}{Travel}", and {Root}{Travel}{Someplace}".

1. People are added to keywords.

E.g. if you have "John Doe" as a person tag, then "John Doe" will be added to  
keywords.

1. Sync the updated information to the media files.

In Expression Media or Media Pro \[Edit\]\[Select All\], \[Action Sync  
Annotations\]\[Export annotations to original files\].

1. Import the images into Adobe Lightroom.

Use the category keywords to create new collections.

Select all images containing a category keyword e.g. "{Root}{Travel}", create a  
new collection called "Travel", and add all selected images to the collection, do  
the same for child collections.

### Known Problems:




- If you are using Expression Media, you first have to fix the COM registration  
that is not correctly set during installation.

On Vista \[Start\]\[All Programs\]\[Accessories\]\[right click the Command Prompt icon  
and select Run as administrator\].

On XP \[Start\]\[Programs\]\[Accessories\]\[Command Prompt\]

Change directory to the Expression Media folder: \[cd "C:\\Program  
Files\\Microsoft Expression\\Media 1.0"\]

Register the Expression Media COM interfaces: \[media.exe /regserver\]

You can close the command prompt.

- If you encounter failures writing keywords to media items, try adding  
keywords to all items that fail using the main application.
- If you get an error "Active catalog does not match requested catalog", it means the catalog you specified on the commandline did not match the default catalog. The problem is that the Open() API always fails, and I have to use the Attach() API to connect the active catalog, and for integrity reasons I make sure the catalog on the commandline is the same as the active catalog that will be modified.

- Complain to Microsoft that the COM API's are not fully functional.

### Download:



#### Version 1.0.1.1: [ExpressionMediaExport.1.0.1.1.zip](https://docs.google.com/open?id=0B_YiDruAPkKzZmNlNzdiZjAtYTZhZi00MDc1LWEwMjgtNDc3ZWJkODViOTEw)




- Added people to keyword export.



#### Version 1.0.0.2: [ExpressionMediaExport.1.0.0.2.zip](https://docs.google.com/uc?id=0B_YiDruAPkKzYjA2MDAxNTgtZWI5YS00YTBjLWJiYjgtYTkwMjkwYzdlMWYx&export=download&hl=en)




- First release.

### Links:




- [Pieter Viljoen's homepage](http://www.insanegenius.com/).

- ["Converting Catalog Sets and Keywords from iView to Lightroom"  
post on The DAM Forum](http://thedambook.com/smf/index.php?topic=1631.0).




