import aiohttp, argparse, logging, os, ssl, sys
from aiohttp import web
from datetime import datetime
from urllib.parse import urlparse

async def forwardRequest(request, useSsl=False):
    rawPath = request.path_qs
    headers = request.headers
    data = await request.read()
    logging.debug('Redirecting Path: {}'.format(rawPath))
    logging.debug('Redirecting Headers: {}'.format(headers))
    # logging.debug('Body: {}'.format(data))
    if useSsl == True:
        destURL = 'https://{}:{}{}'.format(redirectHost, redirectPort, rawPath)
        if useInsecureSSL:
            sslcontext = False
        else:
            sslcontext = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=args.certificate)
    else:
        destURL = 'http://{}:{}{}'.format(redirectHost, redirectPort, rawPath)
        sslcontext = None
    async with aiohttp.ClientSession() as session:
        async with session.get(destURL, ssl=sslcontext, headers=headers, data=data) as response:
            body = await response.read()
            headers = response.headers
            status = response.status
            return headers, status, body

async def handle_http(request):
    headers, status, body = await forwardRequest(request, useSsl=False)
    return web.Response(headers=headers, status=status, body=body)
    
async def handle_https(request):
    headers, status, body = await forwardRequest(request, useSsl=True)
    return web.Response(headers=headers, status=status, body=body)
    
# Setup logging
logLvl = logging.DEBUG
logging.basicConfig(filename='{}-redirection.log'.format(datetime.now().strftime('%Y%m%d%H%M%S')), level=logLvl, format='%(asctime)s - %(levelname)s: %(message)s')
logging.debug('Debugging logging is on.')

# Parse Arguments
logging.debug('Parsing arguments.')
parser = argparse.ArgumentParser(description= 'Simple HTTP/HTTPS redirection script based on aiohttp module.')
parser.add_argument('-l', '--listen', type=str, help='The port the redirector will listen on.')
parser.add_argument('-d', '--destination', type=str, help='The hostname of the server to redirect requests to.')
parser.add_argument('-p', '--port', type=str, help='The port to redirect requests to.')
parser.add_argument('-s', '--secure', type=str, help='Use HTTP (0) or HTTPS (1).')
parser.add_argument('-c', '--certificate', type=str, help='The path of the certificate file, required if "--secure 1".')
parser.add_argument('-k', '--key', type=str, help='The path to the key file, required if "--secure 1".')
parser.add_argument('-i', '--insecure', type=str, help='Force python to accept insecure ssl certificates.')

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
    
if args.port:
    if int(args.port) > 0 and int(args.port) <= 65535:
        redirectPort = int(args.port)
    else:
        print('Specified port is out of range.')
        parser.print_help(sys.stderr)
        raise SystemExit(0)
else:
    print('You must specify a port to use.')
    parser.print_help(sys.stderr)
    raise SystemExit(0)

if args.destination:
    redirectHost = args.destination
    if useHTTPS == False:
        app.add_routes([web.route('*', '/{path:.*}', handle_http)])
        web.run_app(app, host='0.0.0.0', port=listenPort)
    elif useHTTPS == True:
        if os.path.exists(args.certificate) and os.path.exists(args.key):
            app.add_routes([web.route('*', '/{path:.*}', handle_https)])
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(args.certificate, args.key)
            web.run_app(app, host='0.0.0.0', port=listenPort, ssl_context=ssl_context)
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
