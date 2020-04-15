# c2-redirector

## Short Description
An HTTP(S) redirector using aiohttp

## Long Winded Description
After watching a presentation from [Forty North Security](https://fortynorthsecurity.com) at Wild West Hackin' Fest, San Diego 2020 where they demonstrated using Microsoft Azure's Functions to forward C2 traffic I thought of a way to do the same thing using Python on a system. The result would be a simple to configure redirector that is a bit smarter than forwarding ports with SSH or socat and much more light-weight than setting Apache's mod_rewrite plugin. Forty North Security's example code can be found here:

* [https://github.com/FortyNorthSecurity/FunctionalC2](https://github.com/FortyNorthSecurity/FunctionalC2)

## Improvements
The demonstration code from Forty North Security is a bit limited and is only capable of handling **GET** and **PUT** requests. This code make a few improvements:

* Can handle HTTP & HTTPS
* Can handle any HTTP(S) method (i.e. GET, POST, HEAD)
* Can handle any request path 
* Can handle payloads embedded in C2 response headers

## Requirements
```
aiohttp
```

## Usage
```
usage: c2-redirector.py [-h] [-b BIND] [-l LISTEN] [-d DESTINATION] [-p PORT]
                        [-s SECURE] [-c CERTIFICATE] [-k KEY] [-i INSECURE]

Simple HTTP/HTTPS redirection script based on aiohttp module.

optional arguments:
  -h, --help            show this help message and exit
  -b BIND, --bind BIND  The IP/FQDN to bind to. If not supplied the default is
                        0.0.0.0
  -l LISTEN, --listen LISTEN
                        The port the redirector will listen on.
  -d DESTINATION, --destination DESTINATION
                        The hostname of the server to redirect requests to.
  -p PORT, --port PORT  The port to redirect requests to.
  -s SECURE, --secure SECURE
                        Use HTTP (0) or HTTPS (1).
  -c CERTIFICATE, --certificate CERTIFICATE
                        The path of the certificate file, required if "--
                        secure 1".
  -k KEY, --key KEY     The path to the key file, required if "--secure 1".
  -i INSECURE, --insecure INSECURE
                        Force python to accept insecure ssl certificates.
```

### Example 1: Simple HTTP Redirection
```
c2-redirector.py -l 80 -d 10.10.10.10 -p 80
```

### Example 2: HTTPS Redirection Using Untrusted Certificates
```
c2-redirector.py -l 443 -d 10.10.10.10 -p 443 -c server.crt -k server.key -s 1 -i 0
```

### Example 3: HTTPS Redirection Using Valid Certificates
```
c2-redirector.py -l 443 -d 10.10.10.10 -p 443 -c server.crt -k server.key -s 1
```

### Example 4: Bind to a Specific IP
```
c2-redirector.py -b 20.20.20.20 -l 80 -d 10.10.10.10 -p 80
```
