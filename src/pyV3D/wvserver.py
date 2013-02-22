import os
import sys

from tornado import httpserver, web, escape, ioloop, websocket
from tornado.web import RequestHandler, StaticFileHandler

from argparse import ArgumentParser

from pyV3D.pyV3D import WV_Wrapper
from numpy import array, float32, float64, int32, uint8

debug = True

if debug:
    def DEBUG(msg):
       print '<<<' + str(os.getpid()) + '>>> --', msg
else:
    def DEBUG(msg):
        pass

APP_DIR = os.path.dirname(os.path.abspath(__file__))

def get_argument_parser():
    ''' create a parser for command line arguments
    '''
    parser = ArgumentParser(description='launch the test server')
    parser.add_argument('-p', '--port', type=int, dest='port', default=8000,
                        help='port to run server on')
    return parser



# Determining size of buf for websockets:
#    define MAX_MUX_RECURSION 2
#    define LWS_SEND_BUFFER_PRE_PADDING (4 + 10 + (2 * MAX_MUX_RECURSION))
#    define LWS_SEND_BUFFER_POST_PADDING 1
#     unsigned char buf[LWS_SEND_BUFFER_PRE_PADDING + 128 +
#                             LWS_SEND_BUFFER_POST_PADDING]
#
# so -> 4 + 10 + 2*2 + 128 + 1 = 147


class WShandler(websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        self._subprotos = set(kwargs.get('subprotos', []))
        if 'subprotos' in kwargs:
            del kwargs['subprotos']
        super(WShandler, self).__init__(application, request, **kwargs)
    
    def open(self):
        print "WebSocket opened"
        self.create_geom()

    def on_message(self, message):
        print "got message: %s" % message
        self.write_message(u"You said: " + message)

    def on_close(self):
        print "WebSocket closed"

    def select_subprotocol(self, subprotocols):
        print 'asked for subprotocols: %s' % subprotocols
        for proto in subprotocols:
            if proto in self._subprotos:
                return proto
        return None

    def send_binary_data(self, wsi, buf, ibuf):
        print "In send_binary_data"
        print "length", len(buf)
        print "buffer", [buf[i] for i in range(0, ibuf)]
        print ibuf
        #wsi.check()
        #wsi.write_to_file('cube.bin', buf)
        self.write_message(buf, binary=True)

        self.myWV.remove_GPrim(0)
        
        return 0

    def create_geom(self):

        myWV = WV_Wrapper()

        eye    = array([1.0, 0.0, 7.0], dtype=float32)
        center = array([0.0, 0.0, 0.0], dtype=float32)
        up     = array([0.0, 1.0, 0.0], dtype=float32)

        myWV.createContext(0, 30.0, 1.0, 10.0, eye, center, up)

        # box
        # v6----- v5
        # /| /|
        # v1------v0|
        # | | | |
        # | |v7---|-|v4
        # |/ |/
        # v2------v3
        #
        # vertex coords array
        vertices = [
            1, 1, 1, -1, 1, 1, -1,-1, 1, 1,-1, 1, # v0-v1-v2-v3 front
            1, 1, 1, 1,-1, 1, 1,-1,-1, 1, 1,-1, # v0-v3-v4-v5 right
            1, 1, 1, 1, 1,-1, -1, 1,-1, -1, 1, 1, # v0-v5-v6-v1 top
           -1, 1, 1, -1, 1,-1, -1,-1,-1, -1,-1, 1, # v1-v6-v7-v2 left
           -1,-1,-1, 1,-1,-1, 1,-1, 1, -1,-1, 1, # v7-v4-v3-v2 bottom
            1,-1,-1, -1,-1,-1, -1, 1,-1, 1, 1,-1 ] # v4-v7-v6-v5 back

        # normal array
        normals = [
            0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, # v0-v1-v2-v3 front
            1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, # v0-v3-v4-v5 right
            0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, # v0-v5-v6-v1 top
           -1, 0, 0, -1, 0, 0, -1, 0, 0, -1, 0, 0, # v1-v6-v7-v2 left
            0,-1, 0, 0,-1, 0, 0,-1, 0, 0,-1, 0, # v7-v4-v3-v2 bottom
            0, 0,-1, 0, 0,-1, 0, 0,-1, 0, 0,-1 ] # v4-v7-v6-v5 back

        # color array
        colors = [
            0, 0, 255, 0, 0, 255, 0, 0, 255, 0, 0, 255, # v0-v1-v2-v3
            255, 0, 0, 255, 0, 0, 255, 0, 0, 255, 0, 0, # v0-v3-v4-v5
            0, 255, 0, 0, 255, 0, 0, 255, 0, 0, 255, 0, # v0-v5-v6-v1
            255, 255, 0, 255, 255, 0, 255, 255, 0, 255, 255, 0, # v1-v6-v7-v2
            255, 0, 255, 255, 0, 255, 255, 0, 255, 255, 0, 255, # v7-v4-v3-v2
            0, 255, 255, 0, 255, 255, 0, 255, 255, 0, 255, 255] # v4-v7-v6-v5

        # index array
        indices = [
            0, 1, 2, 0, 2, 3, # front
            4, 5, 6, 4, 6, 7, # right
            8, 9,10, 8,10,11, # top
           12,13,14, 12,14,15, # left
           16,17,18, 16,18,19, # bottom
           20,21,22, 20,22,23 ] # back

        vertices = array(vertices, dtype=float64)
        indices = array(indices, dtype=int32)
        colors = array(colors, dtype=uint8)
        normals = array(normals, dtype=float32)

        myWV.add_GPrim_solid("MyBox", vertices, indices, colors, normals,
                             shading=True, orientation=True)

        self.myWV = myWV
        
        buf = 147*' '
        myWV.send_GPrim(self, buf, -1, self.send_binary_data)



# class MainHandler(RequestHandler):
#     def get(self):
#         self.render('index.html')

def main():
    ''' Process command line arguments and run.
    '''
    parser = get_argument_parser()
    options, args = parser.parse_known_args()


    handlers = [
        web.url(r'/', WShandler, { 'subprotos': ["gprim-binary-protocols", "ui-text-protocol"]}),
    ]

    app_settings = {
        'static_path':       APP_DIR,
        #'template_path':     os.path.join(APP_DIR, 'partials'),
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
