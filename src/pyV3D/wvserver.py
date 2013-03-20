import os
import sys
import traceback

from numpy import array, float32, float64, int32, uint8
#import msgpack

from tornado import httpserver, web, escape, ioloop, websocket
from tornado.web import RequestHandler, StaticFileHandler

from argparse import ArgumentParser

from pyV3D.pyV3D import WV_Wrapper, WV_ON, WV_SHADING, WV_ORIENTATION, STLGeometryObject

_undefined_ = object()

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
    parser.add_argument('viewdir', nargs='?', default='.',
                        help='pathname of directory containing files to view')
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

    def on_message(self, message):
        DEBUG("text Websocket received message: %s" % message)


class WSBinaryHandler(BaseWSHandler):

    def _execute(self, transforms, *args, **kwargs):
        try:
            self.view_server = self.geometry_file = None
            if len(args) > 0 and args[0]:
                self.geometry_file = args[0].replace('..', '')
            args = args[1:]
            super(WSBinaryHandler, self)._execute(transforms, *args, **kwargs)
        except Exception as err:
            DEBUG("%s" % str(err))

    def open(self):
        global VIEWERS, _viewdir
        try:
            if self._proto is None:
                DEBUG("no proto")
                return

            DEBUG("_proto = %s" % self._proto)
            if '-txt-' in self._proto:
                DEBUG("skipping due to proto")
                return

            klass = None
            if self.geometry_file:
                self.geometry_file = os.path.join(_viewdir, self.geometry_file)
                parts = self.geometry_file.rsplit('.', 1)
                if len(parts) > 1:
                    ext = '.'+parts[1]
                    try:
                        klass, pkg = VIEWERS[parts[1]]
                    except KeyError:
                        pass
                else:
                    ext = 'None'
            else:
                klass = CubeViewServer

            if klass is _undefined_:
                raise RuntimeError("no viewer loaded for file extension '%s'. Most likely, package '%s' failed to load" % (ext,pkg))
            if klass:
                self.view_server = klass(handler=self, fname=self.geometry_file)
        except Exception as err:
            DEBUG("%s" % str(err))

        if klass is None:
            self.send_error(404)
            return
        try:
            self.view_server.open()
        except Exception as err:
            ERROR('Exception: %s' % traceback.format_exc())

    def on_message(self, message):
        if self.view_server is None:
            self.send_error(404)
            return
        self.view_server.on_message(message)

    def on_close(self):
        DEBUG("binary WebSocket closed")

    def select_subprotocol(self, subprotocols):
        try:
            protocols = ['pyv3d-bin-1.0', 'pyv3d-txt-1.0']
            for p in protocols:
                if p in subprotocols:
                    self._proto = p
                    DEBUG("matched subproto %s" % p)
                    return p
            DEBUG("returning None for subproto choices: %s" % subprotocols)
        except Exception as err:
            DEBUG("%s" % err)
        self._proto = None
        return None

class WV_ViewServer(object):
    def __init__(self, handler, fname=None):
        self.wv = WV_Wrapper()
        self.buf = self.wv.get_bufflen()*'\0'
        self.handler = handler  # need this to send the msgs
        self.geometry_file = fname

    def send_binary_data(self, wsi, buf, ibuf):
        try:
            #dat = msgpack.packb(buf, encoding=None)
            #self.handler.write_message(dat, binary=True)
            self.handler.write_message(buf, binary=True)
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

    def on_message(self, message):
        DEBUG("binary ws got message: %s" % [ord(c) for c in message])

    def on_close(self):
        DEBUG("binary WebSocket closed")

    def open(self):
        DEBUG("binary WebSocket opened. addr=%d" % id(self))
        DEBUG("fname = %s" % self.geometry_file)
        try:
            self.create_geom()
            self.send_geometry(first=True)
        except Exception as err:
            ERROR('Exception: %s' % traceback.format_exc())


class CubeViewServer(WV_ViewServer):

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


# create view server for pygem geometry only if pygem_diamond package is installed
try:
    from pygem_diamond import gem
    from pygem_diamond.pygem import GEMParametricGeometry

    class GEMViewServer(WV_ViewServer):

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
    GEMViewServer = _undefined_


class STLViewServer(WV_ViewServer):

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

# try:
#     from PAM.configurations.pyv3d import GeoMACHParametricGeometry

#     class GeoMACHWSTextHandler(WSTextHandler):
#         def on_message(self, message):
#             pass

#     class GeoMACHWSBinaryHandler(WSBinaryHandler):
#         def initialize(self, options):
#             try:
#                 super(GeoMACHWSBinaryHandler, self).initialize()
#                 self.modpath = options.geometry_file
#             except Exception as err:
#                 ERROR('Exception: %s' % traceback.format_exc())

#         def create_geom(self):
#             DEBUG("create_geom")
#             eye    = array([0.0, 0.0, 7.0], dtype=float32)
#             center = array([0.0, 0.0, 0.0], dtype=float32)
#             up     = array([0.0, 1.0, 0.0], dtype=float32)
#             fov   = 30.0
#             zNear = 1.0
#             zFar  = 10.0

#             bias  = 1
#             self.wv.createContext(bias, fov, zNear, zFar, eye, center, up)

#             self.my_param_geom = GeoMACHParametricGeometry(self.modpath)
#             geom = self.my_param_geom.get_geometry()
#             if geom is None:
#                 raise RuntimeError("can't get Geometry object")
#             geom.get_visualization_data(self.wv)
# except ImportError:
#     GeoMACHViewServer = _undefined_


# mapping of file extension (without the '.') to corresponding viewer class and package
VIEWERS = {
    'csm': (GEMViewServer, 'pygem_diamond'),
    'stl': (STLViewServer, 'pyV3D'),
    #'geo': (GeoMACHViewServer, 'PAM'),
    None: (CubeViewServer, 'pyV3D'),
}  

_viewdir = '.'

def main():
    ''' Process command line arguments and run.
    '''
    global DEBUG, _viewdir

    textargs = {}
    binargs = {}

    parser = get_argument_parser()
    options, args = parser.parse_known_args()

    if options.debug:
        DEBUG = ERROR

    _viewdir = os.path.expanduser(os.path.abspath(options.viewdir))
    if not os.path.isdir(_viewdir):
        sys.stderr.write("view directory '%s' does not exist.\n" % _viewdir)
        sys.exit(-1)

    handlers = [
        web.url(r'/',                web.RedirectHandler, {'url': '/index.html', 'permanent': False}),    
        #web.url(r'/ws/text',         WSTextHandler),
        #web.url(r'/ws/binary/(.*)',  WSBinaryHandler),
        web.url(r'/viewers/(.*)',    WSBinaryHandler),
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
