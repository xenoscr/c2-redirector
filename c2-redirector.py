import aiohttp, argparse, logging, os, ssl, sys, traceback
from aiohttp import web
from datetime import datetime
from urllib.parse import urlparse

async def forwardRequest(request, useSsl=False):
    rawPath = request.path_qs
    reqHeaders = await parseHeaders(request.headers)
    data = await request.read()
    requestingIP = request.remote
    logging.debug('Redirecting Host: {}'.format(redirectHost))
    logging.debug('Redirecting Path: {}'.format(rawPath))
    logging.debug('Remote host: {}'.format(requestingIP))

    # Create the host values
    destHost = '{}:{}'.format(redirectHost, redirectPort)
    cloakHost = '{}:{}'.format(cloakingHost, cloakingPort)

    if useSsl == True:
        destURL = 'https://{}:{}{}'.format(redirectHost, redirectPort, rawPath)
        cloakURL = 'https://{}:{}{}'.format(cloakingHost, cloakingPort, rawPath)
        if useInsecureSSL:
            sslcontext = False
        else:
            sslcontext = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=args.certificate)
    else:
        destURL = 'http://{}:{}{}'.format(redirectHost, redirectPort, rawPath)
        cloakURL = 'http://{}:{}{}'.format(cloakingHost, cloakingPort, rawPath)
        sslcontext = None
    logging.debug('Forwarding request to remote system.')
    reqHeaders['Host'] = destHost
    async with aiohttp.ClientSession(auto_decompress=False) as session:
        async with session.get(destURL, ssl=sslcontext, headers=reqHeaders, data=data) as response:
            body = await response.read()
            headers = response.headers
            status = response.status
    if status == 200 and not cloakingHost:
            return headers, status, body
    elif cloakingHost:
        logging.debug('C2 Server responded with with {} status, trying the cloaking server.'.format(status))
        reqHeaders['Host'] = cloakHost
        async with aiohttp.ClientSession(auto_decompress=False) as cloakSession:
            async with cloakSession.get(cloakURL, ssl=sslcontext, headers=reqHeaders, data=data) as cloakResponse:
                cloakBody = await cloakResponse.read()
                cloakHeaders = cloakResponse.headers
                cloakStatus = cloakResponse.status
                return cloakHeaders, cloakStatus, cloakBody
    else:
        return headers, status, body

async def parseHeaders(headers):
    returnHeaders = {}
    try:
        for key, value in headers.items():
            returnHeaders.update({key: value})
    except Exception as e:
        logging.error(e)
    return returnHeaders

async def handle_http(request):
    headers, status, body = await forwardRequest(request, useSsl=False)
    response = web.Response(headers=headers, status=status, body=body)

    if "Transfer-Encoding" in headers.keys():
        if headers['Transfer-Encoding'].lower() == "chunked":
            response.enable_chunked_encoding()
    return response
    
async def handle_https(request):
    headers, status, body = await forwardRequest(request, useSsl=True)
    return web.Response(headers=headers, status=status, body=body)
    
# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Log all to console
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Log INFO to file (Apache Combination Log Format is aiohttp's default)
handler = logging.FileHandler('{}-redirection.log'.format(datetime.now().strftime('%Y%m%d%H%M%S')))
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

logging.debug('Console DEBUG logging is on.')

# Parse Arguments
logging.debug('Parsing arguments.')
parser = argparse.ArgumentParser(description= 'Simple HTTP/HTTPS redirection script based on aiohttp module.')
parser.add_argument('-b', '--bind', type=str, help='The IP/FQDN to bind to. If not supplied the default is 0.0.0.0')
parser.add_argument('-l', '--listen', type=str, help='The port the redirector will listen on.')
parser.add_argument('-d', '--destination', type=str, help='The hostname of the server to redirect requests to.')
parser.add_argument('-p', '--port', type=str, help='The port to redirect requests to.')
parser.add_argument('-s', '--secure', type=str, help='Use HTTP (0) or HTTPS (1).')
parser.add_argument('-c', '--certificate', type=str, help='The path of the certificate file, required if "--secure 1".')
parser.add_argument('-k', '--key', type=str, help='The path to the key file, required if "--secure 1".')
parser.add_argument('-i', '--insecure', type=str, help='Force python to accept insecure ssl certificates.')
parser.add_argument('--cloakhost', type=str, help='A host running a web server that will answer instead of the C2 server when 404s are encountered.')
parser.add_argument('--cloakport', type=str, help='The port that the cloak host web server is listening on.')

args = parser.parse_args()
app = web.Application()

if args.insecure:
    useInsecureSSL = True
else:
    useInsecureSSL = False
    
if args.secure:
    if int(args.secure) == 0:
        useHTTPS = False
    elif int(args.secure) == 1:
        useHTTPS = True
    else:
        print('Please specify a valid "--secure" option (i.e. 0 or 1)')
        parser.print_help(sys.stderr)
        raise SystemExit(0)
else:
    useHTTPS = False
    
logging.debug('Insecure SSL: {}'.format(useInsecureSSL))

if args.bind:
    bindTo = args.bind
else:
    bindTo = '0.0.0.0'
    
logging.debug('Binding to: {}'.format(bindTo))

if args.listen:
    if int(args.listen) > 0 and int(args.listen) <= 65535:
        listenPort = int(args.listen)
    else:
        print('Specified listening port is out of range.')
        parser.print_help(sys.stderr)
        raise SystemExit(0)
else:
    print('You must specify a listening port to use.')
    parser.print_help(sys.stderr)
    raise SystemExit(0)

logging.debug('Listening on port: {}'.format(listenPort))

if args.port:
    if int(args.port) > 0 and int(args.port) <= 65535:
        redirectPort = int(args.port)
    else:
        print('Specified port is out of range.')
        parser.print_help(sys.stderr)
        raise SystemExit(0)
else:
    logging.error('You must specify a port to use.')
    parser.print_help(sys.stderr)
    raise SystemExit(0)

logging.debug('Destination port: {}'.format(str(redirectPort)))

if args.cloakhost:
    cloakingHost = args.cloakhost
else:
    cloakingHost = None

logging.debug('Cloaking web server: {}'.format(cloakingHost))

if args.cloakport:
    if int(args.cloakport) > 0 and int(args.cloakport) <= 65535:
        cloakingPort = int(args.cloakport)
    else:
        logging.error('The value specified for the cloakport argument is out of range.')
        parser.print_help(sys.stderr)
        raise SystemExit(0)
else:
    cloakingPort = 80

logging.debug('Cloaking web server port: {}'.format(cloakingPort))

if args.destination:
    redirectHost = args.destination
    logging.debug('Destination host: {}'.format(redirectHost))
    if useHTTPS == False:
        logging.debug('Starting HTTP redirector.')
        app.add_routes([web.route('*', '/{path:.*}', handle_http)])
        web.run_app(app, host=bindTo, port=listenPort, access_log_format='%a - - %t "%r" %s %b "%{Referer}i" "%{User-Agent}i"')
    elif useHTTPS == True:
        if os.path.exists(args.certificate) and os.path.exists(args.key):
            logging.debug('Starting HTTPS redirector.')
            app.add_routes([web.route('*', '/{path:.*}', handle_https)])
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(args.certificate, args.key)
            web.run_app(app, host=bindTo, port=listenPort, ssl_context=ssl_context, access_log_format='%a - - %t "%r" %s %b "%{Referer}i" "%{User-Agent}i"')
        else:
            print('Please make sure the path to the certificate and key are valid')
            parser.print_help(sys.stderr)
            raise SystemExit(0)
    else:
        print('Secure must be an integer with value 0 or 1')
        parser.print_help(sys.stderr)
        raise SystemExit(0)
else:
    print('You must specify a host.')
    parser.print_help(sys.stderr)
    raise SystemExit(0)
