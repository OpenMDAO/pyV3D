import os
import sys

from tornado import httpserver, web, escape, ioloop
from tornado.web import RequestHandler, StaticFileHandler


def get_argument_parser():
    ''' create a parser for command line arguments
    '''
    parser = ArgumentParser(description='launch the test server')
    parser.add_argument('-p', '--port', type=int, dest='port', default=8000,
                        help='port to run server on')
    return parser

class MainHandler(RequestHandler):

    def get(self):
        self.render('index.html')

def main():
    ''' Process command line arguments and run.
    '''
    parser = get_argument_parser()
    options, args = parser.parse_known_args()


     handlers = [
        # web.url(r'/', MainHandler),
        # web.url(r'/js/(.*)', web.StaticFileHandler, {'path': os.path.join(APP_DIR,'js')}),
        # web.url(r'/lib/(.*)', web.StaticFileHandler, {'path': os.path.join(APP_DIR,'lib')}),
        # web.url(r'/css/(.*)', web.StaticFileHandler, {'path': os.path.join(APP_DIR,'css')}),
        # web.url(r'/img/(.*)', web.StaticFileHandler, {'path': os.path.join(APP_DIR,'img')}),
        # web.url(r'/partials/(.*)', web.StaticFileHandler, {'path': os.path.join(APP_DIR,'partials')}),
        # web.url(r'/hosts/(.*)', CommitHandler),
        # web.url(r'/tests', CommitsHandler),
        # web.url(r'/results/(.*)/(.*)', TestHandler)
    ]

    app_settings = {
        'static_path':       APP_DIR,
        'template_path':     os.path.join(APP_DIR, 'partials'),
        'debug':             True,
    }
   
    app = web.Application(handlers, **app_settings)

    http_server = httpserver.HTTPServer(app)
    http_server.listen(options.port)

    DEBUG('Serving on port %d' % options.port)
    try:
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        DEBUG('interrupt received, shutting down.')


if __name__ == '__main__':
    main()
