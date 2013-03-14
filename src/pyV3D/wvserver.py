import os
import sys
import traceback

from numpy import array, float32, float64, int32, uint8

from tornado import httpserver, web, escape, ioloop, websocket
from tornado.web import RequestHandler, StaticFileHandler

from argparse import ArgumentParser

from pyV3D.pyV3D import WV_Wrapper, WV_ON, WV_SHADING, WV_ORIENTATION

#sample_file = os.path.join(os.path.dirname(__file__), "test", "sample.csm")
#sample_file = os.path.join(os.path.dirname(__file__), "test", "box1.csm")

def ERROR(*args):
    for arg in args:
        sys.stderr.write(str(arg))
        sys.stderr.write(" ")
    sys.stderr.write('\n')
    sys.stderr.flush()

def DEBUG(*args):
    pass

APP_DIR = os.path.dirname(os.path.abspath(__file__))

def get_argument_parser():
    ''' create a parser for command line arguments
    '''
    parser = ArgumentParser(description='launch the test server')
    parser.add_argument('-p', '--port', type=int, dest='port', default=8000,
                        help='port to run server on')
    parser.add_argument("-d","--debug", action="store_true", dest='debug',
                        help="turn on debug mode")
    parser.add_argument('geometry_file', nargs='?',
                        help='pathname of geometry file to view')
    return parser


class BaseWSHandler(websocket.WebSocketHandler):
    def _handle_request_exception(self, exc):
        ERROR("Unhandled exception: %s" % str(exc))
        super(BaseWSHandler, self)._handle_request_exception(exc)


class WSTextHandler(BaseWSHandler):

    def open(self):
        DEBUG("text WebSocket opened")

    def on_close(self):
        DEBUG("text WebSocket closed")


class WSBinaryHandler(BaseWSHandler):
    def initialize(self):
        self.wv = WV_Wrapper()
        self.buf = self.wv.get_bufflen()*'\0'

    def open(self):
        DEBUG("binary WebSocket opened")
        try:
            self.create_geom()
            self.send_geometry(first=True)
        except Exception as err:
            ERROR('Exception: %s' % traceback.format_exc())

    def on_message(self, message):
        DEBUG("binary ws got message: %s" % message)

    def on_close(self):
        DEBUG("binary WebSocket closed")

    def send_binary_data(self, wsi, buf, ibuf):
        try:
            self.write_message(buf, binary=True)
        except Exception as err:
            ERROR("Exception in send_binary_data:", err)
            return -1
        return 0

    def send_geometry(self, first=False):
        self.wv.prepare_for_sends()

        if first:
            self.wv.send_GPrim(self, self.buf,  1, self.send_binary_data)  # send init packet
            self.wv.send_GPrim(self, self.buf, -1, self.send_binary_data)  # send initial suite of GPrims
        else:  #FIXME: add updating of GPRims here...
            pass

        self.wv.finish_sends()


class SimpleWSTextHandler(WSTextHandler):
    pass

class SimpleWSBinaryHandler(WSBinaryHandler):

    def create_geom(self):

        eye    = array([0.0, 0.0, 7.0], dtype=float32)
        center = array([0.0, 0.0, 0.0], dtype=float32)
        up     = array([0.0, 1.0, 0.0], dtype=float32)
        fov   = 30.0
        zNear = 1.0
        zFar  = 10.0

        bias = 0
        self.wv.createContext(bias, fov, zNear, zFar, eye, center, up)
        self.wv.createBox("Box$1", WV_ON|WV_SHADING|WV_ORIENTATION, [0.,0.,0.])


# create handlers for pygem geometry only if pygem_diamond package is installed
try:
    from pygem_diamond import gem
    from pygem_diamond.pygem import GEMParametricGeometry

    class GEMWSTextHandler(WSTextHandler):
        def on_message(self, message):
            pass
            #if message.startswith('identify;'):
            #    self.write_message('identify:wvserver')
            # elif message.startswith('getPmtrs;'):
            #     pass
            # elif message.startswith('setPmtr'):
            #     pass
            # elif message.startswith('getBrchs;'):
            #     pass
            # elif message.startswith('toglBrch;'):
            #     pass
            # elif message.startswith('build;'):
            #     pass
            # elif message.startswith('save'):
            #     pass


    class GEMWSBinaryHandler(WSBinaryHandler):
        def initialize(self, options):
            try:
                super(GEMWSBinaryHandler, self).initialize()
                self.geometry_file = options.geometry_file
            except Exception as err:
                ERROR('Exception: %s' % traceback.format_exc())

        def create_geom(self):
            DEBUG("create_geom")
            eye    = array([0.0, 0.0, 7.0], dtype=float32)
            center = array([0.0, 0.0, 0.0], dtype=float32)
            up     = array([0.0, 1.0, 0.0], dtype=float32)
            fov   = 30.0
            zNear = 1.0
            zFar  = 10.0

            bias  = 1
            self.wv.createContext(bias, fov, zNear, zFar, eye, center, up)

            self.my_param_geom = GEMParametricGeometry()
            self.my_param_geom.model_file = os.path.expanduser(os.path.abspath(self.geometry_file))
            geom = self.my_param_geom.get_geometry()
            if geom is None:
                raise RuntimeError("can't get Geometry object")
            geom.get_visualization_data(self.wv, angle=15., relSide=.02, relSag=.001)

except ImportError:
    GEMWSBinaryHandler = None
    GEMWSTextHandler = None

from pyV3D.pyV3D import STLGeometryObject

class STLWSTextHandler(WSTextHandler):
    pass

class STLWSBinaryHandler(WSBinaryHandler):
        def initialize(self, options):
            try:
                super(STLWSBinaryHandler, self).initialize()
                self.geometry_file = options.geometry_file
            except Exception as err:
                ERROR('Exception: %s' % traceback.format_exc())

        def create_geom(self):
            DEBUG("create_geom")
            eye    = array([0.0, 0.0, 7.0], dtype=float32)
            center = array([0.0, 0.0, 0.0], dtype=float32)
            up     = array([0.0, 1.0, 0.0], dtype=float32)
            fov   = 30.0
            zNear = 1.0
            zFar  = 10.0

            bias  = 1
            self.wv.createContext(bias, fov, zNear, zFar, eye, center, up)

            self.model_file = os.path.expanduser(os.path.abspath(self.geometry_file))
            geom = STLGeometryObject(self.model_file)
            geom.get_visualization_data(self.wv, angle=15., 
                                        relSide=.02, relSag=.001)

def main():
    ''' Process command line arguments and run.
    '''
    global DEBUG

    textargs = {}
    binargs = {}

    parser = get_argument_parser()
    options, args = parser.parse_known_args()

    if options.debug:
        DEBUG = ERROR

    if options.geometry_file is None: # just draw the cube
        print 'No geometry file given, serving simple cube...'
        binaryhandler = SimpleWSBinaryHandler
        texthandler = SimpleWSTextHandler
    elif options.geometry_file.lower().endswith('.csm'):
        if GEMWSBinaryHandler is None:
            raise RuntimeError("viewing opencsm files requires the pygem_diamond package")
        else:
            binaryhandler = GEMWSBinaryHandler
            binargs = { 'options': options }
            texthandler = GEMWSTextHandler
    elif options.geometry_file.lower().endswith('.stl'):
        if STLWSBinaryHandler is None:
            raise RuntimeError("something is messed up. Contact Bret Naylor.")
        else:
            binaryhandler = STLWSBinaryHandler
            binargs = { 'options': options }
            texthandler = STLWSTextHandler
    else:
        raise RuntimeError("don't know how to read geometry file '%s'. unsupported format" % 
                           os.path.basename(options.geometry_file))

    handlers = [
        web.url(r'/',                web.RedirectHandler, {'url': '/index.html', 'permanent': False}),    
        web.url(r'/ws/text',         texthandler,   textargs),
        web.url(r'/ws/binary',       binaryhandler, binargs),
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
