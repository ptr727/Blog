---
title: Broken Symbol Proxy
date: '2009-04-09T23:24:00+00:00'
url: /2009/04/09/broken-symbol-proxy/
categories:
- uncategorized
tags:
- symproxy
- windbg
post_id: '84'
---
This post is about [Microsoft Debugging Tools for Windows](http://www.microsoft.com/whdc/DevTools/Debugging/default.mspx), symbol servers, and [symbol proxy servers](http://msdn.microsoft.com/en-us/library/cc901417.aspx).

You can read my posts about this problem on the [Microsoft WinDbg group](http://groups.google.com/group/microsoft.public.windbg/browse_thread/thread/8d4d4628cbd580b8/c95bd267da162ff4), and on the [Google Chromium group](http://groups.google.com/group/chromium-dev/browse_thread/thread/1f109398e848bb6d).

We run several symbol servers, and a single symbol proxy server that provides transparent access to all our symbols servers, as well as the Microsoft symbol servers.

I was debugging a Google Chrome crash, and was looking for symbols for Chrome. I was pleasantly surprised to find out that both Mozilla and Google have public debug symbol servers [for Firefox](https://developer.mozilla.org/en/Using_the_Mozilla_symbol_server) and [for Chrome](http://dev.chromium.org/developers/how-tos/debugging). I added the Mozilla and Google symbol servers to our symbol proxy server list.

The problem was that the symbols for Firefox or Chrome did not download as expected, but when pointing directly to the Firefox or Chrome symbol servers the symbols would download correctly.

This worked:

symchk.exe “chrome.exe” /v /s "srv\*c:\\symbols\*http://build.chromium.org/buildbot/symsrv"

This failed:

symchk.exe “chrome.exe” /v /s "srv\*c:\\symbols\*http://our.symbol.server/symbols"

I captured network stack traces of the direct request and the proxy server request.

Direct request:

HTTP - Hyper Text Transfer Protocol

HTTP Command: GET

URI: /buildbot/symsrv/chrome\_exe.pdb/A931F873616F40A4972373FAD37D562D1/chrome\_exe.pdb

HTTP Version: HTTP/1.1

Accept-Encoding: gzip

User-Agent: Microsoft-Symbol-Server/6.11.0001.402

Host: build.chromium.org

Connection: Keep-Alive

Cache-Control: no-cache

Proxy server request:

HTTP - Hyper Text Transfer Protocol

HTTP Command: GET

URI: /buildbot/symsrv/chrome\_exe.pdb/a931f873616f40a4972373fad37d562d1/chrome\_exe.pdb

HTTP Version: HTTP/1.1

User-Agent: Microsoft-Symbol-Server/6.11.0001.402

Host: build.chromium.org

Connection: Keep-Alive

Cache-Control: no-cache

Pragma: no-cache

The problem turns out to be that the symbol proxy uses an all lowercase URI to access the symbol servers. This works with the Microsoft symbol server because they run IIS, and IIS is case insensitive. But, Mozilla and Google run case sensitive Linux based web servers, and when the symbol proxy changes the case of the request, the symbols are not found

We were running symproxy.dll version 6.8.4.0, and the latest release was 6.11.1.404. I upgraded the binaries to the latest version, hoping the problem would go away, instead the problem got worse. Now we were also unable to download symbols from the Microsoft’s own symbol server.

Reading the MSDN documentation for [SymSetOptions()](http://msdn.microsoft.com/en-us/library/ms681366(VS.85).aspx), I noticed two options that could affect the observed behavior; SYMOPT\_CASE\_INSENSITIVE, and SYMOPT\_FAVOR\_COMPRESSED.

I wanted to modify the symbol options while the symbol proxy was running, so I created an ISAPI filter DLL that will run in the same process space as the symbol proxy, allowing me to modify the symbol options. IIS calls [GetFilterVersion()](http://msdn.microsoft.com/en-us/library/ms525465.aspx) to initialize the filter, during this call I called SymSetOptions() and set SYMOPT\_CASE\_INSENSITIVE and SYMOPT\_FAVOR\_COMPRESSED.

Calling SymSetOptions() had no effect, and I quickly realized that I am on the wrong track.

SymSetOptions() is implemented by dbghelp.dll, while symproxy.dll does not load dbghelp.dll.

A bit of investigation revealed that symproxy.dll loads symsrv.dll using LoadLibrary(), and uses only two exports; SymbolServerSetOptions() and SymbolServerByIndex().

I found documentation for [SymbolServerSetOptions()](http://msdn.microsoft.com/en-us/library/ms680676(VS.85).aspx), but nothing for SymbolServerByIndex(). But dbghelp.h did include the function prototypes for both functions.

I changed my strategy, and decided to write a shim to sit between IIS and symproxy.dll, and another shim to sit between symproxy.dll and symsrv.dll. This approach would allow me to see all the values passing between the DLLs.

I modified my ISAPI filter to also export SymbolServerSetOptions() and SymbolServerByIndex(). My DLL now effectively contained exports similar to symproxy.dll and symsrv.dll. The implementation of the exported functions called through to the real symproxy.dll and the real symsrv.dll.

Since symproxy.dll loaded symsrv.dll using LoadLibrary(“symsrv.dll”) I had to name my DLL SymSrv.dll. To avoid DLL name confusion I renamed the original symproxy.dll to symproxy.orig.dll, and symsrv.dll to symsrv.orig.dll. My shim DLL was named SymSrv.dll, and implemented the symproxy.dll and symsrv.dll exports.

IIS -> SymSrv.dll -> symproxy.orig.dll

symproxy.orig.dll -> SymSrv.dll -> symsrv.orig.dll

I observed that symproxy.dll responds to the ISAPI GetFilterVersion() call and sets pVer->dwFlags to:

// pVer->dwFlags 0x00081203

// SF\_NOTIFY\_ORDER\_HIGH 0x00080000

// SF\_NOTIFY\_URL\_MAP 0x00001000

// SF\_NOTIFY\_LOG 0x00000200

// SF\_NOTIFY\_NONSECURE\_PORT 0x00000002

// SF\_NOTIFY\_SECURE\_PORT 0x00000001

I observed that the symproxy.dll sets the following options when calling SymbolServerSetOptions():

// SSRVOPT\_UNATTENDED 0x00000020

// SSRVOPT\_SERVICE 0x00100000

// SSRVOPT\_CALLBACK 0x00000001

// SSRVOPT\_TRACE 0x00000400

// SSRVOPT\_PROXY 0x00001000

I observed that the parameters being passed in to SymbolServerByIndex() are the symbol server, the file name, and an identifier. I also observed that the file name and identifier are present in the URL, but that by the time symproxy.dll calls SymbolServerByIndex() the parameters have all been made lowercase.

The requested URL would look something like:

“/symbols/ch/chrome\_exe.pdb/A931F873616F40A4972373FAD37D562D1/chrome\_exe.pdb”

The physical path would look something like:

“C:\\inetpub\\Symbols\\chrome\_exe.pdb\\A931F873616F40A4972373FAD37D562D1\\chrome\_exe.pdb”

The parameters passed to SymbolServerByIndex() would look something like:

“c:\\inetpub\\symbols\*http://build.chromium.org/buildbot/symsrv”

“chrome\_exe.pdb”

“a931f873616f40a4972373fad37d562d1”

Since I had access to the original path request, and I could intercept the call to SymbolServerByIndex(), I wrote code to replace the file name and identifier with the original cased versions.

See the [source code](https://docs.google.com/uc?id=0B_YiDruAPkKzNzMzN2I3ODktOWM0OS00NmJjLThjYTEtZDhiOWVhNzY1NmMx&export=download&hl=en) for details.

This fixed the case problem and I was now able to retrieve symbols from the Mozilla and Firefox symbol servers.

This did not however solve the problem with the Microsoft symbol servers.

This worked:

symchk.exe “notepad.exe” /v /s "srv\*c:\\symbols\* http://msdl.microsoft.com/download/symbols"

This failed:

symchk.exe “notepad.exe” /v /s "srv\*c:\\symbols\*http://our.symbol.server/symbols"

I captured network stack traces of the direct request and the proxy server request.

Direct request:

HTTP - Hyper Text Transfer Protocol

HTTP Command: GET

URI: /download/symbols/notepad.pdb/DA66AEF719A14FF9902CB3D8EDB248E71/notepad.pdb

HTTP Version: HTTP/1.1

Accept-Encoding: gzip

User-Agent: Microsoft-Symbol-Server/6.11.0001.402

Host: msdl.microsoft.com

Connection: Keep-Alive

Cache-Control: no-cache

HTTP - Hyper Text Transfer Protocol

HTTP Command: GET

URI: /download/symbols/notepad.pdb/DA66AEF719A14FF9902CB3D8EDB248E71/notepad.pd\_

HTTP Version: HTTP/1.1

Accept-Encoding: gzip

User-Agent: Microsoft-Symbol-Server/6.11.0001.402

Host: msdl.microsoft.com

Connection: Keep-Alive

Cache-Control: no-cache

Proxy server request:

HTTP - Hyper Text Transfer Protocol

HTTP Command: GET

URI: /download/symbols/notepad.pdb/da66aef719a14ff9902cb3d8edb248e71/notepad.pdb

HTTP Version: HTTP/1.1

User-Agent: Microsoft-Symbol-Server/6.11.0001.402

Host: msdl.microsoft.com

Connection: Keep-Alive

Cache-Control: no-cache

Pragma: no-cache

The problem turns out to be that the symbols on the Microsoft symbol server are compressed, and that the client would ask for the PDB file, get a 404, then ask for the compressed PD\_ file, while the proxy would only ask for the PDB file, get a 404, and do nothing.

By reverting symproxy.dll and symsrv.dll back to version 6.8.0.4, the symbol proxy worked again, first asking for the PDB, then asking for PD\_, then decompressing the PD\_ to PDB, and serving the PDB to the client.

While looking at the meaning of the various options passed to SymbolServerSetOptions() I recalled that the MSDN documentation stated that the SSRVOPT\_SERVICE option had been deprecated. I took a chance and modified my code to prevent the SSRVOPT\_SERVICE option from being set.

The result was that the symbol proxy now correctly retrieved compressed symbols.

I now have a working symbol proxy that fixes the problems experienced with case sensitive web servers and compressed symbols.

The [source code is available here](https://docs.google.com/uc?id=0B_YiDruAPkKzNzMzN2I3ODktOWM0OS00NmJjLThjYTEtZDhiOWVhNzY1NmMx&export=download&hl=en), normal disclaimers apply, use at your own risk.

Installation instructions:

\- Rename the original symproxy.dll to symproxy.orig.dll

\- Rename the original symsrv.dll to symsrv.orig.dll

\- Compile the code for your platform and copy SymSrv.dll to the same location as symproxy.orig.dll

\- The ISAPI registration will now point to the new SymSrv.dll file

Testing the code:

\- The simplest way to test is to run IIS in debug mode

\- To run IIS in debug mode you must run VC elevated

\- Set the debug target to “C:\\Windows\\System32\\inetsrv\\w3wp.exe /debug”

\- Change the ISAPI registration to point to your build output SymSrv.dll

\- Make sure that the WWW service is not running

\- Start the debugger, this will start IIS, access the symbol server, this will load the ISAPI DLL

My solution is pretty much a hack, and since I do not have documentation for SymbolServerByIndex(), I assume there may be some use cases where my code will break.

Microsoft has acknowledged the problem, and said they will fix the two problems in the next Debugging Tools for Windows release.

Maybe one day Microsoft will make all their utilities open source allowing the community to fix problems instead of working around them.

25 May 2020:

I recovered the project from backups, download [SymProxyOptions](/media/2020/05/symproxyoptions.zip "SymProxyOptions").
