import os
import sys
import traceback

from numpy import array, float32, float64, int32, uint8

from tornado import httpserver, web, escape, ioloop, websocket
from tornado.web import RequestHandler, StaticFileHandler

from argparse import ArgumentParser

_undefined_ = object()

def ERROR(*args):
    for arg in args:
        sys.stderr.write(str(arg))
        sys.stderr.write(" ")
    sys.stderr.write('\n')
    sys.stderr.flush()

def DEBUG(*args):
    pass


def get_argument_parser():
    ''' create a parser for command line arguments
    '''
    parser = ArgumentParser(description='launch the test server')
    parser.add_argument('-p', '--port', type=int, dest='port', default=8000,
                        help='port to run server on')
    parser.add_argument("-d","--debug", action="store_true", dest='debug',
                        help="turn on debug mode")
    parser.add_argument('viewdir', nargs='?', default='.',
                        help='pathname of directory containing files to view')
    return parser


def main():
    ''' Process command line arguments and run.
    '''
    global DEBUG

    from pyV3D.handlers import WSHandler, load_subhandlers

    parser = get_argument_parser()
    options, args = parser.parse_known_args()

    if options.debug:
        DEBUG = ERROR

    DEBUG("loading viewer entry points")
    load_subhandlers()

    viewdir = os.path.expanduser(os.path.abspath(options.viewdir))
    if not os.path.isdir(viewdir):
        sys.stderr.write("view directory '%s' does not exist.\n" % viewdir)
        sys.exit(-1)

    handler_data = {
       'view_dir': viewdir,
    }

    APP_DIR = os.path.dirname(os.path.abspath(__file__))

    handlers = [
        web.url(r'/',                web.RedirectHandler, {'url': '/index.html', 'permanent': False}),    
        web.url(r'/viewers/(.*)',    WSHandler, handler_data),
        web.url(r'/(.*)',            web.StaticFileHandler, {'path': os.path.join(APP_DIR,'wvclient')}),
    ]

    app_settings = {
        'static_path':       APP_DIR,
        'debug':             True,
    }
   
    app = web.Application(handlers, **app_settings)

    http_server = httpserver.HTTPServer(app)
    http_server.listen(options.port)

    print 'Serving on port %d' % options.port
    try:
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        DEBUG('interrupt received, shutting down.')


if __name__ == '__main__':
    main()
