import aiohttp, logging, ssl
from aiohttp import web
from datetime import datetime
from urllib.parse import urlparse

async def forwardRequest(request):
    rawPath = request.path_qs
    headers = request.headers
    data = await request.read()
    logging.debug('Redirecting Path: {}'.format(rawPath))
    logging.debug('Redirecting Headers: {}'.format(headers))
    # logging.debug('Body: {}'.format(data))
    sslcontext = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile='domain_srv.crt')
    destURL = 'http://127.0.0.1:8000{}'.format(rawPath)
    async with aiohttp.ClientSession() as session:
        async with session.get(destURL, ssl=sslcontext, headers=headers, data=data) as response:
            body = await response.read()
            headers = response.headers
            status = response.status
            return headers, status, body

async def handle_all(request):
    headers, status, body = await forwardRequest(request)
    return web.Response(headers=headers, status=status, body=body)
    
# Setup logging
logLvl = logging.DEBUG
logging.basicConfig(filename='{}-redirection.log'.format(datetime.now().strftime('%Y%m%d%H%M%S')), level=logLvl, format='%(asctime)s - %(levelname)s: %(message)s')
logging.debug('Debugging logging is on.')

# Parse Arguments
logging.debug('Parsing arguments.')

app = web.Application()
app.add_routes([web.route('*', '/{path:.*}', handle_all)])

ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain('domain_srv.crt', 'domain_srv.key')
web.run_app(app, host='127.0.0.1', port=8888, ssl_context=ssl_context)
    
