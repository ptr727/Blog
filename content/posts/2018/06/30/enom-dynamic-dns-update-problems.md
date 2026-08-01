---
title: eNom Dynamic DNS Update Problems
date: '2018-06-30T16:57:07+00:00'
url: /2018/06/30/enom-dynamic-dns-update-problems/
categories:
- problem
- solution
tags:
- dns
- enom
post_id: '1753'
---
_Update: On 27 July 2018 eNom support notified me by email that the issue is resolved. I tested it, and all is back to normal with DNS-O-Matic._

Sometime between 12 May 2018 and 24 May 2018 the [eNom dynamic DNS](https://help.enom.com/hc/en-us/articles/115002224432-Dynamic-DNS-FAQs) update mechanism stopped working.

I use the very convenient [DNS-O-Matic](https://www.dnsomatic.com/) dynamic DNS update service to update my OpenDNS account, and several host records at eNom, pointing them to my home IP address.

I was first alerted to the problem by a DNS-O-Matic status failure email, but as I was about to get on a plane for a business trip, I ignored the issue, hoping it was temporary.

```
eNom response for 'foo.bar.net':
--------------------
;URL Interface
;Machine is SJL0VWAPI03
;Encoding Type is utf-8
Command=SETDNSHOST
APIType=API.NET
Language=eng
ErrCount=1
Err1=Domain name not found
ResponseCount=1
ResponseNumber1=316153
ResponseString1=Validation error; not found; domain name(s)
MinPeriod=1
MaxPeriod=10
Server=sjl0vwapi03
Site=eNom
IsLockable=
IsRealTimeTLD=
TimeDifference=+0.00
ExecTime=0.053
Done=true
TrackingKey=5d09a343-b2d6-44e2-8d70-0ad9bcabcb8d
RequestDateTime=6/21/2018 6:11:11 PM
--------------------
```

Here is the update history from DNS-O-Matic:

```
47.44.1.123, Jun 29, 2018 4:58 pm, ERROR
47.44.1.123, Jun 29, 2018 4:53 pm, ERROR
47.44.1.123, Jun 21, 2018 6:11 pm, ERROR
47.44.1.123, May 24, 2018 6:10 pm, ERROR
47.44.1.124, May 12, 2018 8:56 am, OK
47.44.1.124, May 4, 2018 2:48 pm, OK
47.44.1.124, May 3, 2018 1:42 pm, OK
47.44.1.124, Apr 1, 2018 12:39 pm, OK
47.44.1.124, Apr 1, 2018 9:58 am, OK
47.44.1.124, Mar 24, 2018 5:06 pm, OK
```

As of yesterday, I could not find any other reports of similar issues on google, and the [eNom status page](https://enomstatus.com/) showed no problems.

I use a [Ubiquity UniFi Security Gateway Pro](https://www.ubnt.com/unifi-routing/unifi-security-gateway-pro-4/) as home router, and I have the dynamic DNS service in the UniFi controller configured to point to DNS-O-Matic, but it offered no additional hints as to the cause of the problem.

![DNS](/media/2018/06/dns.png)

I contacted eNom support over chat, and they informed me they know there is an issue, and they said I should use the following format for the update:

```
http://dynamic.name-services.com/interface.asp?Command=SetDNSHost&UID=%1&PW=%2&Zone=%3&DomainPassword=%4

%1 = Is username in Enom
%2 = Is password
%3 = Is my host and domain
%4 = Is my domain access password
```

This was interesting, I had looked at several eNom update scripts, even the eNom [sample code](https://www.enom.com/download/updateip.cpp), and they all used a different command format. I looked up the [SetDNSHost](https://www.enom.com/api/API%20topics/api_SetDNSHost.htm) documentation, and sure enough, it looks like eNom changed the API.

Old format:

```
https://dynamic.name-services.com/interface.asp?Command=SetDNSHost&HostName=[host]&Zone=[domain]&DomainPassword=[password]&Address=[IP]
```

New format:

```
https://dynamic.name-services.com/interface.asp?Command=SetDNSHost&UID=[LoginName]&PW=[LoginPassword]&Zone=[FQDN]&DomainPassword=[Password]&Address=[IP]
```

eNom changed the meaning of the "Zone" parameter to be the fully qualified domain name, and they required the addition of the account username and password.

I tried the old format in my browser, and I got the same "Domain name not found" error. As I tried the URL, I noticed that HTTPS failed with a certificate mismatch. The certificate for https://dynamic.name-services.com points to reseller.enom.com.


{{< gallery cols="1" >}}  
{{< figure src="/media/2018/06/ssl.png" title="SSL" alt="SSL" >}}

{{< figure src="/media/2018/06/cert.png" title="Cert" alt="Cert" >}}  
{{< /gallery >}}  

Broken SSL, and including my account username and password was not an acceptable option, additionally I use 2FA on my account, so I had doubts that my password would even work. I tried the command as described in the documentation, but I omitted my account password, and it worked.

```
https://dynamic.name-services.com/interface.asp?Command=SetDNSHost&UID=[LoginName]&Zone=[FQDN]&DomainPassword=[Password]&Address=[IP]
```

I still find it very weird that this has been broken for so long, and that I could not find other reports of the problem on google, are people not using eNom or eNom resellers with dynamic DNS?

I also find it disappointing that the status page is not reflecting this problem, and that the SSL domain does not match, one would expect more from a domain company.

Until eNom fixes the problem, or until DNS-O-Matic updates support for the new API format, I created a PowerShell script to update my domains, maybe it is useful for others with the same problem.

```
$UserName = 'eNom account username'
$HostNames = @('www', 'name1', 'name2', 'etc')
$DomainName = 'yourdomain.com'
$Password = 'Domain change password'

$url = 'http://myip.dnsomatic.com'
$webclient = New-Object System.Net.WebClient
$result = $webclient.DownloadString($url)
Write-Host $result
$IPAddress = $result.ToString()
$webclient.Dispose()

# Ignore SSL error caused by dynamic.name-services.com SSL certificate pointing to a different domain
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}
$webclient = New-Object System.Net.WebClient
foreach ($hostname in $HostNames)
{
    # https://dynamic.name-services.com/interface.asp?Command=SetDNSHost&HostName=[host]&Zone=[domain]&DomainPassword=[password]&Address=[IP]
    # https://dynamic.name-services.com/interface.asp?Command=SetDNSHost&UID=[LoginName]&Zone=[FQDN]&DomainPassword=[Password]&Address=[IP]
    $url = "https://dynamic.name-services.com/interface.asp?Command=SetDNSHost&UID=$UserName&Zone=$hostname.$DomainName&DomainPassword=$Password&Address=$IPAddress"
    Write-Host $url
    $result = $webclient.DownloadString($url);
    Write-Host $result
}
$webclient.Dispose()
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = $null
```
