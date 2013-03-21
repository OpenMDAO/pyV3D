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


class WSViewerHandler(websocket.WebSocketHandler):

    view_handlers = {}

    def initialize(self, view_dir, viewer_classes):
        self.view_dir = view_dir
        self.viewer_classes = viewer_classes

    def _handle_request_exception(self, exc):
        ERROR("Unhandled exception: %s" % str(exc))
        super(WSViewerHandler, self)._handle_request_exception(exc)

    def _execute(self, transforms, *args, **kwargs):
        try:
            self.view_handler = self.geometry_file = None
            if len(args) > 0 and args[0]:
                self.geometry_file = args[0].replace('..', '')
            args = args[1:]
            super(WSViewerHandler, self)._execute(transforms, *args, **kwargs)
        except Exception as err:
            DEBUG("%s" % str(err))

    def open(self):
        try:
            if self._proto == 'pyv3d-bin-1.0':
                klass = None
                if self.geometry_file:
                    self.geometry_file = os.path.join(self.view_dir, self.geometry_file)
                    parts = self.geometry_file.rsplit('.', 1)
                    if len(parts) > 1:
                        try:
                            klass, pkg = self.viewer_classes[parts[1]]
                            if klass is _undefined_:
                                raise RuntimeError("no viewer loaded for file extension '.%s'. Make sure package '%s' has been installed." % (parts[1],pkg))
                        except KeyError:
                            pass
                else:
                    klass = CubeViewHandler

                if klass:
                    self.view_handler = klass(handler=self, fname=self.geometry_file)
                    self.view_handlers[self.geometry_file] = self.view_handler

                if klass is None:
                    self.send_error(404)
                    return

                self.view_handler.open()
        except Exception as err:
            ERROR('Exception: %s' % traceback.format_exc())

    def on_message(self, message):
        if self.view_handler is None:
            self.send_error(404)
            return
        self.view_handler.on_message(message)

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

class WV_ViewHandler(object):
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


class CubeViewHandler(WV_ViewHandler):

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

    class GEMViewHandler(WV_ViewHandler):

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
    GEMViewHandler = _undefined_


class STLViewHandler(WV_ViewHandler):

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

#     class GeoMACHViewHandler(WV_ViewHandler):
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
#     GeoMACHViewHandler = _undefined_


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

    # mapping of file extension (without the '.') to corresponding viewer class and package
    viewer_classes = {
        'csm': (GEMViewHandler, 'pygem_diamond'),
        'stl': (STLViewHandler, 'pyV3D'),
        #'geo': (GeoMACHViewHandler, 'PAM'),
        None: (CubeViewHandler, 'pyV3D'),
    }

    parser = get_argument_parser()
    options, args = parser.parse_known_args()

    if options.debug:
        DEBUG = ERROR

    viewdir = os.path.expanduser(os.path.abspath(options.viewdir))
    if not os.path.isdir(viewdir):
        sys.stderr.write("view directory '%s' does not exist.\n" % viewdir)
        sys.exit(-1)

    handler_data = {
       'view_dir': viewdir,
       'viewer_classes': viewer_classes,
    }

    APP_DIR = os.path.dirname(os.path.abspath(__file__))

    handlers = [
        web.url(r'/',                web.RedirectHandler, {'url': '/index.html', 'permanent': False}),    
        web.url(r'/viewers/(.*)',    WSViewerHandler, handler_data),
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
